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
from typing import Literal, Optional
from pydantic import BaseModel, ValidationError

from app.core.config import settings


class GraderVerdict(BaseModel):
    verdict: Literal["correct", "partial", "incorrect"]
    recalled: bool          # objective: did they reconstruct the key idea?
    feedback: str           # one short sentence, shown after reveal
    revision_note: str      # 2-4 crisp points of what to remember, grounded in the reference


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
    'Respond ONLY as JSON: {"verdict": "correct|partial|incorrect", "recalled": true|false, '
    '"feedback": "...", "revision_note": "- point one\\n- point two"}'
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

    # Lazy import so the app runs fine without the `groq` package installed.
    try:
        from groq import AsyncGroq
    except ImportError as e:
        raise GraderError("The 'groq' package is not installed (pip install groq).") from e

    client = AsyncGroq(api_key=settings.GROQ_API_KEY)

    user_msg = (
        f"TOPIC: {topic}\n\n"
        f"REFERENCE ANSWER:\n{key_memory}\n\n"
        f"STUDENT ANSWER (from memory):\n{user_answer.strip()}"
    )

    try:
        resp = await client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=400,  # room for the revision_note in addition to verdict/feedback
        )
        raw = resp.choices[0].message.content
        return GraderVerdict.model_validate_json(raw)
    except ValidationError as e:
        raise GraderError(f"Grader returned malformed JSON: {e}") from e
    except Exception as e:  # network / API / rate-limit
        raise GraderError(f"Grader call failed: {e}") from e
