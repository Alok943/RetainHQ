"""Suite-specific checking logic.

`check_grader` calls the real production grader (app.services.grader) — never
a copy of its prompt. `check_mcq_items` / `check_answerable` use a judge call
through the same `app.services.llm.call_json` path production code will use,
on `settings.GRADER_MODEL` (documented self-bias; a second-model judge is a
later item, not added here). `check_leetcode_statements` is a no-op pass
until Step 7 wires a real generator — see its docstring.

Each check_<suite> function returns a plain dict (no bespoke report class —
run.py renders it straight to markdown):
    {
        "suite": str,
        "total_cases": int,
        "metrics": {name: float, ...},
        "thresholds": {name: "<= x" | ">= x", ...},
        "passed": bool,
        "case_results": [ {...per-case fields...}, ... ],
        "notes": [str, ...],       # optional, e.g. skip reasons
        "skipped": bool,           # optional — a skip never fails the run
    }
"""
import asyncio
from typing import List

from pydantic import BaseModel, ValidationError

from app.core.config import settings
from app.services import grader as grader_service
from app.services import llm

from evals.schemas import AnswerableCase, GraderCase, LeetcodeStatementCase, MCQItemCase


# --------------------------------------------------------------------------- #
# grader
# --------------------------------------------------------------------------- #

async def check_grader(cases: List[GraderCase]) -> dict:
    incorrect_cases = [c for c in cases if c.expected == "incorrect"]
    correct_cases = [c for c in cases if c.expected == "correct"]

    case_results = []
    false_accepts = 0
    false_rejects = 0
    exact_matches = 0
    errors = 0

    for c in cases:
        try:
            verdict = await grader_service.grade_recall(
                topic=c.question, key_memory=c.reference_answer, user_answer=c.user_answer
            )
        except grader_service.GraderError as e:
            errors += 1
            case_results.append({"id": c.id, "category": c.category, "error": str(e)})
            continue

        is_false_accept = c.expected == "incorrect" and verdict.recalled
        is_false_reject = c.expected == "correct" and not verdict.recalled
        if is_false_accept:
            false_accepts += 1
        if is_false_reject:
            false_rejects += 1
        if verdict.verdict == c.expected:
            exact_matches += 1

        case_results.append({
            "id": c.id,
            "category": c.category,
            "expected": c.expected,
            "actual_verdict": verdict.verdict,
            "actual_recalled": verdict.recalled,
            "false_accept": is_false_accept,
            "false_reject": is_false_reject,
        })

    false_accept_rate = false_accepts / len(incorrect_cases) if incorrect_cases else 0.0
    false_reject_rate = false_rejects / len(correct_cases) if correct_cases else 0.0
    exact_match_rate = exact_matches / len(cases) if cases else 0.0
    passed = false_accept_rate <= 0.03 and false_reject_rate <= 0.15 and errors == 0

    return {
        "suite": "grader",
        "total_cases": len(cases),
        "metrics": {
            "false_accept_rate": false_accept_rate,
            "false_reject_rate": false_reject_rate,
            "exact_match_rate": exact_match_rate,
            "errors": errors,
        },
        "thresholds": {
            "false_accept_rate": "<= 0.03",
            "false_reject_rate": "<= 0.15",
        },
        "passed": passed,
        "case_results": case_results,
    }


# --------------------------------------------------------------------------- #
# mcq_items
# --------------------------------------------------------------------------- #

class _MCQJudgeVerdict(BaseModel):
    valid: bool
    reason: str


_MCQ_JUDGE_SYSTEM_PROMPT = (
    "You are a strict QA reviewer for multiple-choice quiz items used in a spaced-repetition "
    "app. Given a QUESTION and its OPTIONS (one marked CORRECT, the rest distractors, each with "
    "a `why`), judge whether the item is sound:\n"
    "1. The option marked CORRECT must actually be the correct answer to the question.\n"
    "2. No distractor may also be a defensible correct answer.\n"
    "3. Each option's `why` must be factually accurate and must agree with which option is correct "
    "(a distractor's `why` must correctly explain why IT is wrong, not restate the right answer).\n"
    'Respond ONLY as JSON: {"valid": true|false, "reason": "one short sentence"}'
)


async def _judge_mcq_item(case: MCQItemCase) -> _MCQJudgeVerdict:
    options_block = "\n".join(
        f"{i + 1}. [{'CORRECT' if o.correct else 'distractor'}] {o.text} — why: {o.why}"
        for i, o in enumerate(case.options)
    )
    user_msg = f"QUESTION: {case.question}\n\nOPTIONS:\n{options_block}"
    raw = await llm.call_json(
        model=settings.GRADER_MODEL,
        system_prompt=_MCQ_JUDGE_SYSTEM_PROMPT,
        user_msg=user_msg,
        max_tokens=300,
        schema=_MCQJudgeVerdict,
    )
    return _MCQJudgeVerdict.model_validate_json(raw)


def _mcq_structural_failures(case: MCQItemCase) -> List[str]:
    failures = []
    if len(case.options) != 4:
        failures.append(f"expected exactly 4 options, found {len(case.options)}")
    correct_opts = [o for o in case.options if o.correct]
    if len(correct_opts) != 1:
        failures.append(f"expected exactly 1 correct option, found {len(correct_opts)}")
    if any(not o.why.strip() for o in case.options):
        failures.append("every option needs a non-empty `why`")
    if case.references_data and not case.context:
        failures.append("question references data but has no `context`")
    return failures


async def check_mcq_items(cases: List[MCQItemCase]) -> dict:
    case_results = []
    structural_failure_count = 0

    for c in cases:
        failures = _mcq_structural_failures(c)
        if failures:
            structural_failure_count += 1
        case_results.append({"id": c.id, "structural_failures": failures})

    structural_pass_rate = (
        1 - structural_failure_count / len(cases) if cases else 1.0
    )

    judged = await asyncio.gather(*[_judge_mcq_item(c) for c in cases])
    judged_defects = 0
    for result, verdict in zip(case_results, judged):
        result["judged_valid"] = verdict.valid
        result["judged_reason"] = verdict.reason
        if not verdict.valid:
            judged_defects += 1
    judged_defect_rate = judged_defects / len(cases) if cases else 0.0

    passed = structural_pass_rate == 1.0 and judged_defect_rate <= 0.05

    return {
        "suite": "mcq_items",
        "total_cases": len(cases),
        "metrics": {
            "structural_pass_rate": structural_pass_rate,
            "judged_defect_rate": judged_defect_rate,
        },
        "thresholds": {
            "structural_pass_rate": "== 1.0",
            "judged_defect_rate": "<= 0.05",
        },
        "passed": passed,
        "case_results": case_results,
    }


# --------------------------------------------------------------------------- #
# answerable
# --------------------------------------------------------------------------- #

class _AnswerableJudgeVerdict(BaseModel):
    answerable: bool
    reason: str


_ANSWERABLE_JUDGE_SYSTEM_PROMPT = (
    "You judge whether a spaced-repetition review question is answerable by a learner who has "
    "ONLY the QUESTION text and its CONTEXT (if any) in front of them — the original lesson is "
    "closed. The ANSWER is given to you for reference only, never shown to the learner.\n"
    "A question is answerable if a learner who once studied this topic could reason their way to "
    "the answer from the question + context alone, without needing to recall an external fact, "
    "diagram, or prior statement that isn't present here. It is NOT answerable if it references "
    "something ('these two lines', 'the diagram above', 'as shown earlier') that isn't actually "
    "included in the context.\n"
    'Respond ONLY as JSON: {"answerable": true|false, "reason": "one short sentence"}'
)


async def _judge_answerable(case: AnswerableCase) -> _AnswerableJudgeVerdict:
    ctx_block = f"\n\nCONTEXT: {case.context}" if case.context else ""
    user_msg = (
        f"QUESTION: {case.question}{ctx_block}\n\n"
        f"ANSWER (reference only, not shown to the learner): {case.answer}"
    )
    raw = await llm.call_json(
        model=settings.GRADER_MODEL,
        system_prompt=_ANSWERABLE_JUDGE_SYSTEM_PROMPT,
        user_msg=user_msg,
        max_tokens=200,
        schema=_AnswerableJudgeVerdict,
    )
    return _AnswerableJudgeVerdict.model_validate_json(raw)


async def check_answerable(cases: List[AnswerableCase]) -> dict:
    judged = await asyncio.gather(*[_judge_answerable(c) for c in cases])
    yes_count = sum(1 for v in judged if v.answerable)
    yes_rate = yes_count / len(cases) if cases else 0.0

    case_results = [
        {
            "id": c.id,
            "expected_answerable": c.expected_answerable,
            "judged_answerable": v.answerable,
            "judged_reason": v.reason,
        }
        for c, v in zip(cases, judged)
    ]

    passed = yes_rate >= 0.90

    return {
        "suite": "answerable",
        "total_cases": len(cases),
        "metrics": {"yes_rate": yes_rate},
        "thresholds": {"yes_rate": ">= 0.90"},
        "passed": passed,
        "case_results": case_results,
    }


# --------------------------------------------------------------------------- #
# leetcode_statements
# --------------------------------------------------------------------------- #

async def check_leetcode_statements(cases: List[LeetcodeStatementCase]) -> dict:
    """No generator exists yet (Step 7 of the implementation doc builds
    `problem_statements` + the generation service). Rather than fail the whole
    run or fabricate a check, this reports the dataset as ready and skips —
    the moment Step 7 lands, wire the real generator call in here and this
    suite starts grading for real."""
    try:
        from app.services import leetcode_statements as ls_service  # noqa: F401
    except ImportError:
        return {
            "suite": "leetcode_statements",
            "total_cases": len(cases),
            "metrics": {},
            "thresholds": {"judged_accuracy": ">= 0.95"},
            "passed": True,
            "skipped": True,
            "case_results": [],
            "notes": [
                "app.services.leetcode_statements does not exist yet (Step 7 of "
                "IMPLEMENTATION-quiz-capture-v2.md). Dataset is seeded and ready "
                f"({len(cases)} cases) — wire the real generator call into "
                "check_leetcode_statements once it's built.",
            ],
        }
    raise NotImplementedError(
        "app.services.leetcode_statements now exists — implement the real "
        "generate-and-judge check in check_leetcode_statements instead of this stub."
    )
