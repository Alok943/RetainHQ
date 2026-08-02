"""Infer WHICH approach a user actually implemented, from their own solution code.

The problem this solves
-----------------------
Question generation (services/grader.py) is grounded in the *catalog's* view of a
problem: the `role='primary'` roadmap node's title + description, the problem
title, and the language. That is enough to name the pattern and nothing more, so
when the model is asked for an implementation question it fills the gap with the
canonical textbook solution. A user who solved #567 with two dicts and a full
`fs1 == wins2` comparison per slide gets quizzed on the 26-length count array and
the `matches` counter — same concept, different code, every specific detail wrong.

This module closes that gap with one call at LOG time (not review time — the
result is stored, so it is amortized over every future review of the card).

Two hard constraints, both inherited
------------------------------------
1. **Closed vocabulary.** The model NEVER names a concept. It picks one of the
   nodes already mapped to this problem in `problem_concepts` (primary /
   supporting / alternative), or `"other"`. Free-form concept emission is what
   SPEC-leetcode-retention.md §2 exists to prevent, and a model told to always
   produce an answer will always produce one.
2. **Inference is not evidence.** The result never touches `Activity.node_id`
   and never writes a `learning_event`. It reframes questions; that is all.
   (SPEC-leetcode-retention.md §3.2.-1; IMPLEMENTATION-leetcode-log-capture.md §1.)

Failure is always soft. No key, no candidates, a timeout, a hallucinated id, a
malformed response — every one of them returns `None` and the card falls back to
exactly today's catalog-grounded behaviour. Capture must never fail because an
optional enrichment did.
"""
import uuid
from typing import Literal, Optional

from pydantic import BaseModel

from app.core.config import settings
from app.services import llm

APPROACH_PROMPT_VERSION = "v1"

# The model may only ever return one of the supplied node ids, or this.
_NO_MATCH = "other"


class InferredApproach(BaseModel):
    """What the user's code actually does, in the closed vocabulary."""

    node_id: Optional[uuid.UUID] = None  # None == 'other' / unresolvable
    node_title: Optional[str] = None
    confidence_band: Literal["high", "medium", "low"] = "low"
    # 2-4 short, concrete, checkable observations about THIS code. These are the
    # payload — they are what lets the question generator ask about the code the
    # user wrote ("you compare two dicts each slide") instead of the code the
    # textbook would have written.
    facts: list[str] = []
    reason: str = ""

    def to_summary(self) -> dict:
        """The JSONB blob persisted on `activities.approach_summary`."""
        return {
            "facts": self.facts,
            "reason": self.reason,
            "node_title": self.node_title,
            "model": settings.APPROACH_MODEL,
            "version": APPROACH_PROMPT_VERSION,
        }


class _RawResult(BaseModel):
    """The model's response shape. `selected` is a string so a hallucinated
    value is caught by us rather than by a Pydantic UUID parse error."""

    selected: str
    confidence_band: Literal["high", "medium", "low"]
    facts: list[str]
    reason: str


_SYSTEM_RULES = """\
You are given a student's own solution to a coding problem, and a CLOSED LIST of
candidate concepts. Identify which candidate the code actually implements, and
state concrete facts about how they implemented it.

Rules:
1. `selected` MUST be one of the given Node IDs verbatim, or the string "other".
   Never invent a concept, never return a title, never return a concept that is
   not in the list. If the code implements something genuinely outside the list,
   return "other" — that is a correct answer, not a failure.
2. Judge the CODE, not the problem. If the candidate list says the canonical
   approach is X but this code clearly does Y, and Y is in the list, answer Y.
3. `facts`: 2-4 short statements about what THIS code specifically does, each
   one checkable against the source. Prefer the decisions that have consequences:
   the data structure chosen, what is recomputed per iteration and what it costs,
   how state is maintained or invalidated, which edge case the early return
   handles. Name real identifiers from the code where it helps.
   Do NOT restate the problem. Do NOT praise or criticize. Do NOT suggest fixes.
4. `confidence_band`:
   - "high"   — the code unambiguously implements the selected concept.
   - "medium" — it is the best fit but the code is partial, unusual, or blends two.
   - "low"    — you are guessing, or you returned "other".
5. `reason`: one sentence naming the specific evidence in the code.
"""




async def infer_approach(
    code: str,
    language: Optional[str],
    problem_title: str,
    candidates: list[dict],
) -> Optional[InferredApproach]:
    """Resolve `code` onto one of `candidates`.

    `candidates` are dicts of {node_id, title, description, role} drawn from
    `problem_concepts` for this problem — the closed set for this call.

    Returns None whenever the inference could not be made, for ANY reason. The
    caller treats None as "no approach known" and loses nothing it had before.
    """
    if not code or not code.strip():
        return None
    if not candidates:
        # Nothing legal to choose from. Inventing a vocabulary here is precisely
        # the failure mode §2 bans, so we decline instead.
        return None
    if not llm.is_configured(settings.APPROACH_MODEL):
        return None

    valid: dict[str, dict] = {str(c["node_id"]): c for c in candidates}

    candidates_text = ""
    for c in candidates:
        candidates_text += (
            f"Node ID: {c['node_id']}\n"
            f"Title: {c['title']}\n"
            f"Description: {c.get('description') or ''}\n"
            f"Catalog role for this problem: {c.get('role') or 'unknown'}\n\n"
        )

    user_msg = (
        f"# Problem\n{problem_title}\n\n"
        f"# Candidate concepts (choose exactly one Node ID, or \"other\")\n"
        f"{candidates_text}"
        f"# The student's solution"
        f"{f' ({language})' if language else ''}\n"
        f"```\n{code.strip()}\n```\n"
    )

    try:
        raw_json = await llm.call_json(
            model=settings.APPROACH_MODEL,
            system_prompt=_SYSTEM_RULES,
            user_msg=user_msg,
            max_tokens=800,
            schema=_RawResult,
        )
        raw = _RawResult.model_validate_json(raw_json)
    except Exception:
        # Network, timeout, quota, SDK missing, malformed JSON — all the same to
        # the caller. Capture is not allowed to fail over an optional enrichment.
        return None

    facts = [f.strip() for f in (raw.facts or []) if f and f.strip()][:4]

    if raw.selected == _NO_MATCH:
        # An honest "none of these". The facts are still useful — they describe
        # real code — so keep them and let the questions stay catalog-grounded.
        return InferredApproach(
            node_id=None, node_title=None, confidence_band="low",
            facts=facts, reason=raw.reason.strip(),
        )

    match = valid.get(raw.selected)
    if match is None:
        # Hallucinated an id. Same handling as llm_classifier.py: drop the
        # selection, never trust the band that came with it.
        return InferredApproach(
            node_id=None, node_title=None, confidence_band="low",
            facts=facts,
            reason=f"System override: model returned unknown node {raw.selected}",
        )

    return InferredApproach(
        node_id=uuid.UUID(str(match["node_id"])),
        node_title=match["title"],
        confidence_band=raw.confidence_band,
        facts=facts,
        reason=raw.reason.strip(),
    )
