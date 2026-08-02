import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ManualEvidenceIn(BaseModel):
    node_id: uuid.UUID
    minutes: int = Field(gt=0, le=600)
    note: Optional[str] = Field(default=None, max_length=2000)


class NodeMasteryOut(BaseModel):
    node_id: uuid.UUID
    title: str
    m_learned: float
    r: float
    m: float
    state: str
    confidence: str
    evidence_count: int
    last_event_at: Optional[datetime] = None


class EvidenceEventOut(BaseModel):
    id: uuid.UUID
    occurred_at: datetime
    event_type: str
    trust_tier: str
    source: str
    outcome: Optional[str] = None
    difficulty: Optional[str] = None
    assistance: Optional[str] = None
    grade: Optional[float] = None
    duration_min: int
    weight: float
    m_learned_after: float
    deleted_at: Optional[datetime] = None


class EvidenceSummaryOut(BaseModel):
    total_events: int
    by_tier: dict[str, int]
    by_type: dict[str, int]
    unmapped_events: int
    nodes_with_evidence: int
    weights_version: str


class RecomputeOut(BaseModel):
    nodes_recomputed: int


class LeetCodeSolveIn(BaseModel):
    problem_slug: str
    occurred_at: Optional[datetime] = None
    duration_min: int = Field(default=0)
    # LeetCode's own submission id. Recorded for provenance/audit. NOT the idempotency
    # key - that stays problem-scoped so re-solving the same problem cannot farm mastery.
    submission_id: Optional[str] = None

    # Reflection (SPEC-leetcode-retention.md §4.1). All optional and skippable: the solve
    # is a fact and is logged with or without these. Absent reflection is scored with the
    # CONSERVATIVE defaults in evidence_weights.py - mastery may understate, never overstate.
    confidence: Optional[int] = Field(default=None, ge=1, le=5)
    needed_hint: Optional[bool] = None
    mistake: Optional[str] = Field(default=None, max_length=500)


class NeetCodeSolveIn(LeetCodeSolveIn):
    """Identical producer contract to LeetCodeSolveIn (Producer C — verified-external
    solve, reflection optional) — a different `source` string, not a different shape.
    Kept as its own class rather than reusing LeetCodeSolveIn directly so the route
    signature/OpenAPI docs read as what they are, not as a LeetCode-specific type."""


class LeetCodeBackfillIn(BaseModel):
    solved_slugs: list[str]
    # slug -> when it was actually solved. Optional and defaulting to empty so
    # an older extension build keeps working unchanged; any slug missing from
    # the map still falls back to import time.
    #
    # Worth carrying rather than stamping everything `now`: the companion now
    # imports a *window* (e.g. Python solves from the last 60 days), and
    # collapsing two months of work onto the import date would make the evidence
    # log claim it all happened in one afternoon — the same overstating this
    # module refuses when it defaults `assistance` to "llm_assisted".
    solved_at: dict[str, datetime] = Field(default_factory=dict)


class NeetCodeBackfillIn(BaseModel):
    """NeetCode's `getCompletedProblems`, normalised by the extension.

    Deliberately NOT shaped like LeetCodeBackfillIn, because the data isn't
    comparable:

    `leetcode_slugs`, not NeetCode ones — that endpoint returns LeetCode URLs
    (`https://leetcode.com/problems/valid-palindrome/`), since NeetCode links out
    to LeetCode to solve. The extension extracts the slug, so this resolves
    against the LeetCode catalog directly and needs no alias lookup.

    ONE `occurred_at` for the whole batch, not a per-slug map. NeetCode exposes
    no per-problem completion date anywhere — `getUserStreakData` gives daily
    activity COUNTS but never says which problem — so a per-slug map would be
    fabricated precision. The extension sends the user's EARLIEST recorded
    activity date instead: that understates recency (more decay, review comes
    sooner) rather than claiming today, which is the direction this codebase
    errs in deliberately.
    """
    leetcode_slugs: list[str]
    occurred_at: Optional[datetime] = None
