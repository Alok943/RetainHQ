"""
LLM recall grader — EXPERIMENT (frozen per the design doc: §5/§6, ships post-validation).

One Groq call. Grades a user's FREE-RECALL answer against the stored `key_memory`
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


# --------------------------------------------------------------------------- #
# Helper: a single configured AsyncGroq call returning the raw JSON string.
# Centralizes the client construction + error wrapping shared by every grader
# function so each one is just a prompt + a Pydantic model.
# --------------------------------------------------------------------------- #
async def _groq_json(system_prompt: str, user_msg: str, max_tokens: int = 700) -> str:
    if not settings.GROQ_API_KEY:
        raise GraderError("GROQ_API_KEY is not set — grader is disabled.")
    try:
        from groq import AsyncGroq
    except ImportError as e:
        raise GraderError("The 'groq' package is not installed (pip install groq).") from e

    # gpt-oss is a REASONING model: its hidden reasoning tokens count against
    # max_tokens (and add latency). Pin reasoning to "low" so a simple grade/gen
    # task doesn't burn the budget or truncate the JSON. The flag is gpt-oss-only;
    # sending it to a llama model would 400, so gate it on the model name. We rely
    # on json_object (not the json_schema strict mode, which gpt-oss ignores).
    extra = {}
    if settings.GROQ_MODEL.startswith("openai/gpt-oss"):
        extra["reasoning_effort"] = "low"

    client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    try:
        resp = await client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=max_tokens,
            **extra,
        )
        return resp.choices[0].message.content
    except Exception as e:  # network / API / rate-limit
        raise GraderError(f"Grader call failed: {e}") from e


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
    "2. Be lenient on wording, phrasing, and minor detail; strict on the core concept.\n"
    "3. 'correct' = key idea fully captured; 'partial' = some of it; 'incorrect' = missing or wrong.\n"
    "4. 'recalled' is true for correct or solid-partial, false otherwise.\n"
    "5. feedback: ONE short, encouraging sentence naming what they missed (if anything).\n"
    "6. revision_note: 2-4 short bullet lines (each prefixed with '- ') of the most crucial "
    "points to remember for this topic. Ground it in the REFERENCE answer; you may add a "
    "directly-related point ONLY if you are highly confident it is correct. Keep it concise "
    "and factual — never invent specifics you are unsure about.\n"
    "7. related_subtopics: 1-2 subtopics under this TOPIC that are highly related and worth "
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
    if not settings.GROQ_API_KEY:
        raise GraderError("GROQ_API_KEY is not set — grader is disabled.")

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

    raw = await _groq_json(_SYSTEM_PROMPT, user_msg, max_tokens=700)
    try:
        return GraderVerdict.model_validate_json(raw)
    except ValidationError as e:
        raise GraderError(f"Grader returned malformed JSON: {e}") from e


# =========================================================================== #
# QUESTION MODE (PROTOTYPE — gated behind GRADER_ENABLED, same as the grader).
#
# Instead of one open "describe the topic" prompt, the LLM turns the stored
# key_memory into 2-3 targeted short-answer questions and grades the answers.
# This probes the forgettable EDGES of what the user captured rather than
# letting them skate by with a two-line summary.
#
# Design guardrails (deliberate — do not "improve" away):
#   - Questions must be answerable SOLELY from the key_memory. We never quiz
#     un-captured trivia; an unfair "gotcha" failure is exactly the kind of
#     friction that breeds review fatigue. Probe edges, don't ambush.
#   - key_memory remains the single ground truth for grading (same as the free
#     recall grader) — we do not invent or persist a separate answer key.
#   - Open-ended short answer, never multiple choice (recognition is weaker
#     retrieval than recall).
#   - Two calls total (generate, then grade the whole set) — not one per Q.
# =========================================================================== #


class GeneratedQuestions(BaseModel):
    questions: List[str]  # 2-3 short-answer questions, each answerable from key_memory


class QuestionItemGrade(BaseModel):
    question: str
    correct: bool
    note: str  # one short sentence on what was right/missing


class QuestionSetGrade(BaseModel):
    recalled: bool        # objective: did they reconstruct the key idea overall?
    feedback: str         # one short, encouraging summary sentence
    items: List[QuestionItemGrade]
    related_subtopics: List[RelatedSubtopic] = []  # 1-2 adjacent topics to explore next


_QGEN_SYSTEM_PROMPT = (
    "You write short active-recall questions from a student's own KEY MEMORY note.\n"
    "Rules:\n"
    "1. Produce 2-3 questions, each answerable SOLELY from the KEY MEMORY. Never ask "
    "about anything not stated or directly implied by it — no outside trivia, no "
    "'gotcha' questions on material the student did not capture.\n"
    "2. Probe DIFFERENT facets/edges of the note (a definition, a why, a distinction, "
    "an application) so the set tests real understanding, not one fact restated.\n"
    "3. Each question is ONE sentence, open-ended short-answer — NOT yes/no and NOT "
    "multiple choice.\n"
    "4. Keep them plain and direct; no preamble.\n"
    'Respond ONLY as JSON: {"questions": ["...", "..."]}'
)


async def generate_questions(
    topic: str, key_memory: str, notes: Optional[str] = None, mistake: Optional[str] = None
) -> GeneratedQuestions:
    """Generate grounded short-answer questions from the stored key_memory."""
    extra = ""
    if notes:
        extra += f"\n\nADDITIONAL NOTES (context only):\n{notes}"
    if mistake:
        extra += f"\n\nA MISTAKE THE STUDENT PREVIOUSLY MADE (good to probe):\n{mistake}"
    user_msg = f"TOPIC: {topic}\n\nKEY MEMORY:\n{key_memory}{extra}"

    raw = await _groq_json(_QGEN_SYSTEM_PROMPT, user_msg, max_tokens=400)
    try:
        result = GeneratedQuestions.model_validate_json(raw)
    except ValidationError as e:
        raise GraderError(f"Question generator returned malformed JSON: {e}") from e
    # Trim to a sane bound; an empty set means we fall back to free recall.
    result.questions = [q.strip() for q in result.questions if q and q.strip()][:3]
    if not result.questions:
        raise GraderError("Question generator returned no usable questions.")
    return result


_QGRADE_SYSTEM_PROMPT = (
    "You grade a student's short answers to recall questions. The KEY MEMORY is the "
    "ground truth — judge each answer ONLY against it, ignoring your own outside "
    "knowledge.\n"
    "Rules:\n"
    "1. Be lenient on wording, strict on the core idea. 'correct' means the answer "
    "captures the key point the question is after.\n"
    "2. 'recalled' (overall) is true if the student got the MAJORITY of questions right "
    "and missed nothing critical.\n"
    "3. Each item's 'note' is ONE short sentence on what was right or missing.\n"
    "4. 'feedback' is ONE short, encouraging summary sentence.\n"
    "5. related_subtopics: 1-2 subtopics under this TOPIC that are highly related and worth "
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

    raw = await _groq_json(_KEYPOINTS_SYSTEM_PROMPT, user_msg, max_tokens=600)
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
        lines.append(f"Q{i}: {q}\nA{i}: {a}")
    qa_block = "\n\n".join(lines)
    user_msg = (
        f"TOPIC: {topic}\n\nKEY MEMORY (ground truth):\n{key_memory}\n\n"
        f"STUDENT'S ANSWERS:\n{qa_block}"
    )

    raw = await _groq_json(_QGRADE_SYSTEM_PROMPT, user_msg, max_tokens=900)
    try:
        return QuestionSetGrade.model_validate_json(raw)
    except ValidationError as e:
        raise GraderError(f"Question grader returned malformed JSON: {e}") from e
