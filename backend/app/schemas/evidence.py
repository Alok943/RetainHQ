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


class LeetCodeBackfillIn(BaseModel):
    solved_slugs: list[str]
