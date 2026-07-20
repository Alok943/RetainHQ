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
