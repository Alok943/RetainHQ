"""
LLM recall grader — EXPERIMENT (frozen per the design doc: §5/§6, ships post-validation).

One model call. Grades a user's FREE-RECALL answer against the stored `key_memory`
(the rubric) and returns an objective verdict + short feedback. This is the
machine version of the `recalled` signal we already capture by self-report —
the gap between the two is the calibration metric.

Design constraints baked in here (do not "improve" away):
  - ONE call, not multi-agent.
  - Grade against the PROVIDED reference answer, not the model's world knowledge.
  - Strict JSON out, validated with Pydantic.
  - Small/fast model by default (latency is existential for an SRS).
  - The verdict is a PROPOSAL — the UI must always allow a one-tap user override.

Not wired into the live review endpoint. Call it as a non-blocking step AFTER
reveal once the launch loop is validated.
"""
from typing import Literal, Optional, List
from pydantic import BaseModel, ValidationError

from app.core.config import settings
from app.services import llm


# --------------------------------------------------------------------------- #
# Every grader call goes through services/llm.py, which picks the provider from
# settings.GRADER_MODEL's id. This function is now just the error translation —
# the rest of this module raises GraderError and knows nothing about providers.
#
# `reasoning`: honoured on Groq's gpt-oss (hidden reasoning tokens count against
# max_tokens, so generation passes "low" to stay fast and GRADING passes "medium"
# — at "low" it rubber-stamps answers that merely use the right words). On a
# Gemini id the model manages its own thinking budget and the argument is a
# documented no-op, so the strictness of grading rides on the model itself. Kept
# at the call sites regardless: it is the standing statement of which calls need
# real judgment, and it becomes live again the moment GRADER_MODEL routes to Groq.
# --------------------------------------------------------------------------- #
async def _grader_json(system_prompt: str, user_msg: str, max_tokens: int = 700, reasoning: str = "low") -> str:
    try:
        return await llm.call_json(
            model=settings.GRADER_MODEL,
            system_prompt=system_prompt,
            user_msg=user_msg,
            max_tokens=max_tokens,
            reasoning=reasoning,
        )
    except llm.LLMError as e:
        raise GraderError(str(e)) from e


def is_configured() -> bool:
    """Whether the grader's selected model has its provider key set."""
    return llm.is_configured(settings.GRADER_MODEL)


class RelatedSubtopic(BaseModel):
    """A highly-related subtopic worth learning next — a SUGGESTION, never a quiz.

    This is the answer to the "no un-captured gotcha trivia" problem: rather than
    testing the user on material they never logged, we surface adjacent topics as
    an invitation to capture them next. Title + one short explainer line.
    """
    title: str
    explainer: str  # one short line; what it is / why it's worth knowing


class GraderVerdict(BaseModel):
    verdict: Literal["correct", "partial", "incorrect"]
    recalled: bool          # objective: did they reconstruct the key idea?
    feedback: str           # one short sentence, shown after reveal
    revision_note: str      # 2-4 crisp points of what to remember, grounded in the reference
    related_subtopics: List[RelatedSubtopic] = []  # 1-2 adjacent topics to explore next


_SYSTEM_PROMPT = (
    "You grade a student's from-memory recall answer against a REFERENCE answer.\n"
    "Rules:\n"
    "1. The REFERENCE answer is ground truth. Judge ONLY whether the student's answer "
    "captures its key idea(s) — ignore your own outside knowledge.\n"
    "2. Be lenient on WORDING and phrasing, but strict on CORRECTNESS. If the answer asserts "
    "something FALSE or muddled — even when it uses the right keywords — it is NOT 'correct'. "
    "Grade what the student actually SAID, not the right answer you can infer they were reaching for.\n"
    "3. Do NOT charitably rewrite a flawed answer into the correct one. If something is wrong or "
    "imprecise, your feedback must name the SPECIFIC error and give the correction.\n"
    "4. 'correct' = key idea fully and accurately captured; 'partial' = some of it, or right idea "
    "with a real inaccuracy; 'incorrect' = missing or wrong.\n"
    "5. 'recalled' is true only for correct or solid-partial with no serious conceptual error.\n"
    "6. feedback: ONE honest sentence. If they nailed it, say so briefly; if they got something wrong, "
    "name the exact mistake and the fix. Do NOT give blanket praise when the answer has an error.\n"
    "7. revision_note: 2-4 short bullet lines (each prefixed with '- ') of the most crucial "
    "points to remember for this topic. Ground it in the REFERENCE answer; you may add a "
    "directly-related point ONLY if you are highly confident it is correct. Keep it concise "
    "and factual — never invent specifics you are unsure about.\n"
    "8. related_subtopics: 1-2 subtopics under this TOPIC that are highly related and worth "
    "learning next. These are SUGGESTIONS, not part of the grade — do not penalize the "
    "student for not mentioning them. Each has a 'title' and a one-line 'explainer'. Pick "
    "genuinely adjacent, high-leverage topics; if nothing strong comes to mind, return [].\n"
    'Respond ONLY as JSON: {"verdict": "correct|partial|incorrect", "recalled": true|false, '
    '"feedback": "...", "revision_note": "- point one\\n- point two", '
    '"related_subtopics": [{"title": "...", "explainer": "..."}]}'
)


class GraderError(RuntimeError):
    pass


async def grade_recall(topic: str, key_memory: str, user_answer: str) -> GraderVerdict:
    """Grade a single recall attempt. Raises GraderError if not configured."""
    if not is_configured():
        raise GraderError("No provider key set for GRADER_MODEL — grader is disabled.")

    # Skip the call entirely if the user committed "I don't know" / left it blank.
    if not user_answer or not user_answer.strip():
        return GraderVerdict(
            verdict="incorrect",
            recalled=False,
            feedback="No answer given — review the key memory and try again next time.",
            revision_note=key_memory.strip() or "Review the key memory for this topic.",
        )

    user_msg = (
        f"TOPIC: {topic}\n\n"
        f"REFERENCE ANSWER:\n{key_memory}\n\n"
        f"STUDENT ANSWER (from memory):\n{user_answer.strip()}"
    )

    raw = await _grader_json(_SYSTEM_PROMPT, user_msg, max_tokens=1100, reasoning="medium")
    try:
        return GraderVerdict.model_validate_json(raw)
    except ValidationError as e:
        raise GraderError(f"Grader returned malformed JSON: {e}") from e


# =========================================================================== #
# QUESTION MODE — gated behind GRADER_ENABLED, same as the grader.
#
# The LLM turns a card into targeted short-answer questions and grades the
# answers, probing the forgettable EDGES instead of letting the learner skate
# by with a two-line summary.
#
# Design guardrails (deliberate — do not "improve" away):
#   - Open-ended short answer, never multiple choice (recognition is weaker
#     retrieval than recall).
#   - Two calls per fresh set (generate, then grade the whole set) — not one
#     per question; generation further amortizes via QuestionSet persistence.
# =========================================================================== #


class QuestionItemGrade(BaseModel):
    question: str
    correct: bool
    note: str  # one short sentence on what was right/missing


class QuestionSetGrade(BaseModel):
    recalled: bool        # objective: did they reconstruct the key idea overall?
    feedback: str         # one short, encouraging summary sentence
    items: List[QuestionItemGrade]
    related_subtopics: List[RelatedSubtopic] = []  # 1-2 adjacent topics to explore next


# =========================================================================== #
# QUESTION SET GENERATION — persisted, reusable sets ({question, reference_answer}).
#
# Two grounding modes, decided by whether the card is linked to a roadmap node:
#   - TOPIC-grounded (node-linked, e.g. syllabus roadmaps): the node's title +
#     description is the contract — standard textbook knowledge of THAT topic is
#     fair game (an exam doesn't care what the student happened to write down),
#     but never leak into adjacent topics: those are separate cards with their
#     own schedule. key_memory, if present, biases toward what they studied.
#   - KEY-MEMORY-grounded (free-form logs): unchanged trust model — questions
#     answerable solely from what the user captured; no gotcha trivia.
#
# Every question carries a REFERENCE_ANSWER written at generation time. That's
# what makes persistence + strict grading possible without a user rubric: the
# grader judges against the stored reference, not the model's live knowledge.
# Reference answers are stored server-side and never sent to the client.
#
# depth (user's explicit choice at review time):
#   'main' = 2-3 questions: the definition and the why.
#   'deep' = 4-5 questions: adds apply/derive/compare/edge-case probes.
# =========================================================================== #


class QuestionItem(BaseModel):
    question: str
    reference_answer: str


class GeneratedQuestionItems(BaseModel):
    questions: List[QuestionItem]


_QGEN_SET_SYSTEM_PROMPT = (
    "You write short active-recall questions WITH reference answers for a spaced-repetition "
    "review of one topic.\n"
    "Grounding rules:\n"
    "1. If the input has a SYLLABUS TOPIC block, that topic (title + description) is the "
    "contract: use standard, commonly-taught textbook knowledge of exactly that topic. "
    "Stay STRICTLY inside it — never quiz neighboring topics, prerequisites, or follow-ups. "
    "If a KEY MEMORY is also given, prefer probing what the student captured, then fill "
    "with the topic's core facets.\n"
    "2. If the input has ONLY a KEY MEMORY block, every question must be answerable SOLELY "
    "from that note — nothing not stated or directly implied by it. No outside trivia.\n"
    "3. If a PROBLEM CONTEXT is given, NEVER restate, quote, or paraphrase the problem statement. "
    "The title is a label, not content to quiz on. If a LANGUAGE is given, language questions must be about "
    "semantics and complexity, never syntax lookup (e.g. if the answer is a one-line docs lookup, it is not a question). "
    "Only emit a language question when the language is explicitly provided.\n"
    "3b. If the PROBLEM CONTEXT contains THE STUDENT'S APPROACH, it overrides the canonical "
    "solution as the subject of every implementation, complexity, and edge-case question. Quiz "
    "the code they actually wrote — the listed WHAT THEIR CODE DOES facts are ground truth about "
    "it. Do NOT ask about a data structure, variable, or optimization the facts do not mention: "
    "if the facts say they compared two dictionaries, asking about a fixed count array or a match "
    "counter is asking about someone else's solution. The one legitimate way to raise a technique "
    "they did not use is an explicit comparison ('you did X — what would Y buy you here?'), and "
    "that counts as the transfer question, not the implementation one.\n"
    "Question rules:\n"
    "4. DEPTH=main → 2-3 questions covering the core: the definition/statement and the why. "
    "If PROBLEM CONTEXT is present: 1 concept (why the pattern works) + 1 trigger (what signals this pattern) + 1 implementation (in the card's language, if provided, else complexity).\n"
    "DEPTH=deep → 4-5 questions: the core PLUS apply/derive/compare/edge-case probes. "
    "If PROBLEM CONTEXT is present: core PLUS 1 complexity/transfer (about alternative approaches) + 1 edge case/discriminating question.\n"
    "5. Each question is ONE sentence, open-ended short-answer — never yes/no, never "
    "multiple choice. Force specific retrieval ('Why does X…', 'What happens when Y…'), "
    "no generic padding.\n"
    "6. Probe DIFFERENT facets — no two questions testing the same fact reworded.\n"
    "7. Each reference_answer is 1-3 sentences: the complete, correct expected answer. It is "
    "the grading ground truth, so it must be self-contained and factually precise — never "
    "invent specifics you are unsure about.\n"
    'Respond ONLY as JSON: {"questions": [{"question": "...", "reference_answer": "..."}]}'
)


async def generate_question_items(
    topic: str,
    depth: str = "main",
    key_memory: Optional[str] = None,
    node_title: Optional[str] = None,
    node_description: Optional[str] = None,
    unit: Optional[str] = None,
    mistake: Optional[str] = None,
    problem_context: Optional[dict] = None,
) -> List[QuestionItem]:
    """Generate a persistable question set ({question, reference_answer} items).

    Pass node_* for topic-grounded generation (roadmap-linked cards); otherwise
    key_memory is required and is the sole ground truth. Raises GraderError.
    """
    depth = depth if depth in ("main", "deep") else "main"
    parts = [f"DEPTH: {depth}"]
    if node_title:
        topic_block = f"SYLLABUS TOPIC: {node_title}"
        if node_description:
            topic_block += f"\nWHAT TO RECALL: {node_description}"
        if unit:
            topic_block += f"\nUNIT: {unit}"
        parts.append(topic_block)
        if key_memory and key_memory.strip():
            parts.append(f"KEY MEMORY (what the student captured):\n{key_memory.strip()}")
    else:
        if not key_memory or not key_memory.strip():
            raise GraderError("No grounding available — need a key memory or a linked topic.")
        parts.append(f"TOPIC: {topic}\n\nKEY MEMORY:\n{key_memory.strip()}")
    if mistake and mistake.strip():
        parts.append(f"A MISTAKE THE STUDENT PREVIOUSLY MADE (good to probe):\n{mistake.strip()}")
        
    if problem_context:
        ctx = "PROBLEM CONTEXT:\n"
        ctx += f"Problem: {problem_context.get('problem_title', 'Unknown')}\n"
        if problem_context.get('primary_node_title'):
            ctx += f"Primary Concept: {problem_context['primary_node_title']}\n"
        alt = problem_context.get('alternative_node_titles')
        if alt:
            ctx += f"Alternative Concepts: {', '.join(alt)}\n"
        if problem_context.get('language'):
            ctx += f"Language: {problem_context['language']}\n"
        # The student's own implementation, when they shared it. This is the block
        # that stops the model defaulting to the textbook solution — without it,
        # "Sliding window (fixed)" + a problem title is all it has, so it invents
        # the canonical count-array version and quizzes code the user never wrote.
        approach_title = problem_context.get('user_approach_title')
        approach_facts = problem_context.get('user_approach_facts') or []
        if approach_title or approach_facts:
            ctx += "\nTHE STUDENT'S APPROACH (what they actually wrote — quiz THIS):\n"
            if approach_title:
                ctx += f"Approach taken: {approach_title}\n"
            if approach_facts:
                ctx += "WHAT THEIR CODE DOES:\n"
                ctx += "".join(f"- {f}\n" for f in approach_facts)
        parts.append(ctx)

    raw = await _grader_json(_QGEN_SET_SYSTEM_PROMPT, "\n\n".join(parts), max_tokens=1200)
    try:
        result = GeneratedQuestionItems.model_validate_json(raw)
    except ValidationError as e:
        raise GraderError(f"Question generator returned malformed JSON: {e}") from e

    cap = 5 if depth == "deep" else 3
    items = [
        QuestionItem(question=q.question.strip(), reference_answer=q.reference_answer.strip())
        for q in result.questions
        if q.question.strip() and q.reference_answer.strip()
    ][:cap]
    if not items:
        raise GraderError("Question generator returned no usable questions.")
    return items


_QGRADE_SYSTEM_PROMPT = (
    "You grade a student's short answers to recall questions. The KEY MEMORY is the "
    "general ground truth, but if a specific REFERENCE ANSWER is provided for a question, "
    "judge the student's answer against THAT reference answer primarily, ignoring outside "
    "knowledge.\n"
    "Rules:\n"
    "1. Be lenient on WORDING but strict on CORRECTNESS. Grade what the student actually "
    "WROTE, not the correct answer you can infer they meant. An answer is 'correct' ONLY if "
    "what it states is true and on-point. If it contains a false or muddled claim — even with "
    "the right keywords present — mark it false (correct: false).\n"
    "2. Do NOT charitably rewrite a flawed answer into the right one. If an answer is wrong or "
    "imprecise, the 'note' must name the SPECIFIC error and give the correction in one sentence.\n"
    "3. 'recalled' (overall) is true only if the student got the MAJORITY right AND made no "
    "serious conceptual error.\n"
    "4. Each item's 'note': if correct, one sentence on what was right; if wrong, name the exact "
    "mistake and correct it — do not paper over it.\n"
    "5. 'feedback' is ONE honest summary sentence: encouraging when earned, but it must mention the "
    "main gap if they got something wrong. No blanket praise over an incorrect answer.\n"
    "6. related_subtopics: 1-2 subtopics under this TOPIC that are highly related and worth "
    "learning next. These are SUGGESTIONS, NOT graded — never penalize the student for not "
    "knowing them. Each has a 'title' and a one-line 'explainer'. Pick genuinely adjacent, "
    "high-leverage topics; if nothing strong comes to mind, return [].\n"
    'Respond ONLY as JSON: {"recalled": true|false, "feedback": "...", "items": '
    '[{"question": "...", "correct": true|false, "note": "..."}], '
    '"related_subtopics": [{"title": "...", "explainer": "..."}]}'
)


# =========================================================================== #
# CAPTURE ASSIST (PROTOTYPE — gated behind GRADER_ENABLED).
#
# Runs at LOG time, not review time. When a user is stuck summarizing what they
# learned, this suggests the core sub-points under the topic so they can KEEP the
# ones they actually studied — recognition is far easier than blank-page recall.
#
# Design guardrails (deliberate):
#   - It is a SUGGESTION the user curates, never auto-applied to the field. The
#     endpoint just returns a list; the UI lets the user pick/edit. This is the
#     answer to "I can't articulate it" WITHOUT making them capture (and later be
#     quizzed on) material they never actually learned.
#   - Surface the core, commonly-taught points — not obscure trivia.
# =========================================================================== #


class KeyPointSuggestions(BaseModel):
    points: List[str]  # 3-5 short recognition prompts


_KEYPOINTS_SYSTEM_PROMPT = (
    "You help a learner CAPTURE what they just studied — you are NOT testing them.\n"
    "Given a TOPIC (and maybe a rough DRAFT note), list the 3-5 most important "
    "sub-points or subtopics that typically fall under this topic.\n"
    "Rules:\n"
    "1. These are RECOGNITION PROMPTS: the learner keeps the ones they actually "
    "learned and ignores the rest. List the CORE, commonly-taught points — not "
    "obscure trivia or edge cases.\n"
    "2. Each point is ONE short line: a concrete fact or idea, self-contained, not "
    "a vague heading. Plain language, no preamble, no numbering.\n"
    "3. Stay tightly on the TOPIC. Build on the DRAFT if given; you may include core "
    "points the draft missed, but do not contradict it.\n"
    'Respond ONLY as JSON: {"points": ["...", "..."]}'
)


async def suggest_key_points(topic: str, draft: Optional[str] = None) -> KeyPointSuggestions:
    """Suggest the core sub-points under a topic to help a stuck learner capture.

    A capture AID, not a grader — the user curates which to keep. Raises GraderError
    if not configured or on a malformed/empty response.
    """
    extra = f"\n\nTHEIR DRAFT SO FAR:\n{draft.strip()}" if draft and draft.strip() else ""
    user_msg = f"TOPIC: {topic.strip()}{extra}"

    raw = await _grader_json(_KEYPOINTS_SYSTEM_PROMPT, user_msg, max_tokens=600)
    try:
        result = KeyPointSuggestions.model_validate_json(raw)
    except ValidationError as e:
        raise GraderError(f"Key-point suggester returned malformed JSON: {e}") from e
    result.points = [p.strip() for p in result.points if p and p.strip()][:5]
    if not result.points:
        raise GraderError("Key-point suggester returned no usable points.")
    return result


async def grade_question_set(
    topic: str, key_memory: str, qa_pairs: List[dict]
) -> QuestionSetGrade:
    """Grade a set of {question, answer} pairs against the key_memory in one call."""
    lines = []
    for i, pair in enumerate(qa_pairs, 1):
        q = (pair.get("question") or "").strip()
        a = (pair.get("answer") or "").strip() or "(no answer)"
        ref = (pair.get("reference_answer") or "").strip()
        ref_block = f"\nREFERENCE ANSWER for Q{i}: {ref}" if ref else ""
        lines.append(f"Q{i}: {q}{ref_block}\nA{i}: {a}")
    qa_block = "\n\n".join(lines)
    user_msg = (
        f"TOPIC: {topic}\n\nKEY MEMORY (ground truth):\n{key_memory}\n\n"
        f"STUDENT'S ANSWERS:\n{qa_block}"
    )

    raw = await _grader_json(_QGRADE_SYSTEM_PROMPT, user_msg, max_tokens=1300, reasoning="medium")
    try:
        return QuestionSetGrade.model_validate_json(raw)
    except ValidationError as e:
        raise GraderError(f"Question grader returned malformed JSON: {e}") from e


# =========================================================================== #
# TEST-SECTION FILLUP GRADING (SPEC-test-runtime.md). The ONE LLM call in the
# whole Tests system — everything else (numeric/mcq/code/query) grades
# deterministically client-side. This grades against a CURATED bank answer
# (the question's `answer` field), not a user-written key_memory, so the
# reference is always complete and unambiguous — same trust model as
# grade_recall, just a different (and more reliable) source of ground truth.
# =========================================================================== #

class FillupVerdict(BaseModel):
    verdict: Literal["correct", "partial", "incorrect"]
    feedback: str  # one short sentence


_FILLUP_SYSTEM_PROMPT = (
    "You grade a student's fill-in-the-blank test answer against a REFERENCE answer "
    "written by a curriculum author.\n"
    "Rules:\n"
    "1. The REFERENCE answer is ground truth. Judge ONLY whether the student's answer "
    "captures its key idea — ignore outside knowledge.\n"
    "2. Be lenient on WORDING, strict on CORRECTNESS. A right answer in different words is "
    "'correct'; a partially-right or vague answer is 'partial'; a wrong or missing answer is "
    "'incorrect'.\n"
    "3. feedback: ONE short sentence. If wrong, name the specific gap or error — do not just "
    "say 'incorrect'.\n"
    'Respond ONLY as JSON: {"verdict": "correct|partial|incorrect", "feedback": "..."}'
)


async def grade_fillup(question: str, reference_answer: str, student_answer: str) -> FillupVerdict:
    """Grade a single Test-section fill-up answer. Raises GraderError if not configured."""
    if not is_configured():
        raise GraderError("No provider key set for GRADER_MODEL — grader is disabled.")

    if not student_answer or not student_answer.strip():
        return FillupVerdict(verdict="incorrect", feedback="No answer given.")

    user_msg = (
        f"QUESTION: {question}\n\n"
        f"REFERENCE ANSWER:\n{reference_answer}\n\n"
        f"STUDENT ANSWER:\n{student_answer.strip()}"
    )

    raw = await _grader_json(_FILLUP_SYSTEM_PROMPT, user_msg, max_tokens=300, reasoning="low")
    try:
        return FillupVerdict.model_validate_json(raw)
    except ValidationError as e:
        raise GraderError(f"Fillup grader returned malformed JSON: {e}") from e
