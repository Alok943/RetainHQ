"""Evidence weight table (Career Coach design doc §9; SPEC-career-coach-phase1
§3-4). Pure config + the `w()` interface — no DB access, no I/O. This is the
single source of truth for the enumerations the DB CHECK-constrains and the
API validates against.

`w()` takes a duck-typed event (any object exposing the attributes below) so
this module has zero dependency on the ORM. `EventInput` is the plain
dataclass stand-in used until `LearningEvent` (SPEC §2.1) lands; once it does,
real rows satisfy the same shape and need no adapter.
"""
import logging
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger(__name__)

EVENT_TYPES = (
    "RECALL_GRADED", "PROBLEM_SOLVED", "ARTIFACT_BUILT",
    "CONCEPT_EXPLAINED", "CONTENT_CONSUMED", "TIME_BLOCK",
)
TRUST_TIERS = ("T1_verified_external", "T2_verified_internal", "T3_observed", "T4_claimed")
SOURCES = (
    "leetcode", "retainhq_review", "retainhq_coach", "github",
    "manual", "companion_desktop", "companion_android",
)

WEIGHTS_VERSION = "v0"

# §4.2 rule 2 — T3 (and CONTENT_CONSUMED regardless of tier) can't push a node
# past this, though it can never drag an already-higher node back down.
T3_EXPOSURE_CAP = 0.35
CAPPED_EVENT_TYPES = frozenset({"CONTENT_CONSUMED"})
CAPPED_TRUST_TIERS = frozenset({"T3_observed"})

# Conservative defaults for missing fields (§4 gap list) — mastery may
# understate, it must never overstate.
_DEFAULT_DIFFICULTY = "medium"
_DEFAULT_ASSISTANCE = "llm_assisted"

_FAIL_MIN_DURATION_MIN = 15
_FAIL_WEIGHT = 0.03

# (difficulty, assistance) -> weight, outcome == "pass". Transcribed from the
# parent doc's §9 table with the §4 gaps filled to their documented values.
_PROBLEM_SOLVED_PASS_WEIGHTS = {
    ("hard", "none"): 0.35,
    ("hard", "hint"): 0.21,
    ("hard", "llm_assisted"): 0.08,
    ("hard", "solution_seen"): 0.08,
    ("medium", "none"): 0.25,
    ("medium", "hint"): 0.15,
    ("medium", "llm_assisted"): 0.06,
    ("medium", "solution_seen"): 0.06,
    ("easy", "none"): 0.10,
    ("easy", "hint"): 0.04,
    ("easy", "llm_assisted"): 0.04,
    ("easy", "solution_seen"): 0.04,
}

RECALL_GRADED_WEIGHT = 0.20
CONCEPT_EXPLAINED_WEIGHT = 0.18
ARTIFACT_BUILT_WEIGHT = 0.30
CONTENT_CONSUMED_WEIGHT = 0.04
TIME_BLOCK_WEIGHT = 0.0


@dataclass
class EventInput:
    """Minimal shape `w()` / `fold_events()` need from an event. Satisfied by
    this plain dataclass now and by the real `LearningEvent` SQLModel once it
    lands (step 3) — same attribute names, no adapter needed."""
    event_type: str
    trust_tier: str
    outcome: Optional[str] = None
    difficulty: Optional[str] = None
    assistance: Optional[str] = None
    duration_min: int = 0
    grade: Optional[float] = None
    occurred_at: Optional[Any] = None
    id: Optional[Any] = None
    deleted_at: Optional[Any] = None


def is_capped(event: Any) -> bool:
    """True if this event's contribution to m_learned is subject to the T3
    exposure cap (§4.2 rule 2) — regardless of what w() returns for it."""
    return event.trust_tier in CAPPED_TRUST_TIERS or event.event_type in CAPPED_EVENT_TYPES


def apply_event_weight(m_learned_before: float, weight: float, capped: bool) -> float:
    """One fold step (parent §9 update rule): m ← m + w(1 − m), clamped to
    [0, 1], then the T3 cap. `max(m_learned_before, cap)` is deliberate — a
    capped event must never drag an already-higher node back down."""
    m_learned_after = m_learned_before + weight * (1 - m_learned_before)
    m_learned_after = min(max(m_learned_after, 0.0), 1.0)
    if capped and m_learned_after > T3_EXPOSURE_CAP:
        m_learned_after = max(m_learned_before, T3_EXPOSURE_CAP)
    return m_learned_after


def w(event: Any, node_state: Any = None, user_history: Optional[dict] = None) -> float:
    """Evidence weight for one event. v1 = table lookup + modifiers;
    `node_state` and `user_history` are unused but present so contextual/
    learned weights can land later without touching any caller."""
    if event.trust_tier == "T4_claimed":
        return 0.0

    event_type = event.event_type
    if event_type == "PROBLEM_SOLVED":
        return _problem_solved_weight(event)
    if event_type == "RECALL_GRADED":
        return _graded_weight(event, RECALL_GRADED_WEIGHT)
    if event_type == "CONCEPT_EXPLAINED":
        return _graded_weight(event, CONCEPT_EXPLAINED_WEIGHT)
    if event_type == "ARTIFACT_BUILT":
        return ARTIFACT_BUILT_WEIGHT
    if event_type == "CONTENT_CONSUMED":
        return CONTENT_CONSUMED_WEIGHT
    if event_type == "TIME_BLOCK":
        return TIME_BLOCK_WEIGHT
    return 0.0


def _problem_solved_weight(event: Any) -> float:
    if event.outcome == "fail":
        return _FAIL_WEIGHT if (event.duration_min or 0) >= _FAIL_MIN_DURATION_MIN else 0.0

    difficulty = event.difficulty or _DEFAULT_DIFFICULTY
    assistance = event.assistance or _DEFAULT_ASSISTANCE
    pass_weight = _PROBLEM_SOLVED_PASS_WEIGHTS.get((difficulty, assistance))
    if pass_weight is None:
        pass_weight = _PROBLEM_SOLVED_PASS_WEIGHTS[(_DEFAULT_DIFFICULTY, _DEFAULT_ASSISTANCE)]

    if event.outcome == "partial":
        return pass_weight / 2

    if event.outcome != "pass":
        logger.warning("PROBLEM_SOLVED event with missing/unknown outcome=%r treated as no evidence", event.outcome)
        return 0.0

    return pass_weight


def _graded_weight(event: Any, multiplier: float) -> float:
    if event.grade is None:
        logger.warning("%s event with grade=None treated as no evidence (producer bug)", event.event_type)
        return 0.0
    return multiplier * event.grade
