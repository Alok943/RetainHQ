import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.services.career_tree import CareerTreeDraft


class CareerTemplateOut(BaseModel):
    role_key: str
    title: str
    version: str
    node_count: int


class TreeGenerateIn(BaseModel):
    role_key: str
    goal_title: str
    target_date: Optional[date] = None
    diagnostic_results: Optional[list[dict]] = None
    free_text: Optional[str] = Field(default=None, max_length=2000)


class CareerGoalIn(BaseModel):
    role_key: str
    title: str
    target_date: Optional[date] = None


class CareerGoalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role_key: str
    title: str
    target_date: Optional[date] = None
    roadmap_id: Optional[uuid.UUID] = None
    template_version: Optional[str] = None
    sprint_node_id: Optional[uuid.UUID] = None
    sprint_until: Optional[date] = None
    status: str
    created_at: datetime
    updated_at: datetime


class SprintIn(BaseModel):
    node_id: uuid.UUID
    sprint_until: date


class DiagnosticProbeOut(BaseModel):
    stable_key: str
    node_title: str
    probe: str


class DiagnosticAnswerIn(BaseModel):
    stable_key: str
    answer: str


class DiagnosticResultOut(BaseModel):
    stable_key: str
    verdict: str  # 'correct' | 'partial' | 'incorrect'
    recalled: bool
    grade: float = Field(ge=0.0, le=1.0)
    feedback: str


class DiagnosticResultIn(BaseModel):
    """What the client threads from /diagnostic/submit's response into
    /tree/commit — grade + recalled only. entity_id is NOT carried over: the
    commit endpoint re-derives it deterministically from (goal_id, stable_key)
    via uuid5, so resubmitting the same goal's diagnostic is naturally a
    dedupe no-op rather than a double-counted learning_event."""
    stable_key: str
    grade: float = Field(ge=0.0, le=1.0)
    recalled: bool


class TreeCommitIn(CareerTreeDraft):
    """The (possibly user-edited) draft tree, plus the diagnostic results held
    since /diagnostic/submit — both replayed into the DB in the same
    transaction (§4: "held in the draft, replay on commit")."""
    diagnostic_results: Optional[list[DiagnosticResultIn]] = None


class SuggestedNodeOut(BaseModel):
    node_id: uuid.UUID
    stable_key: str
    title: str
    confidence: float
    tier: str  # 'auto' (>=0.75) | 'triage' (0.55-0.75) — see topic_mapping.py


class UnmappedActivityOut(BaseModel):
    activity_id: uuid.UUID
    topic: str
    skipped_count: int
    suggested_node: Optional[SuggestedNodeOut] = None


class AssignNodeIn(BaseModel):
    node_id: uuid.UUID


class AssignNodeOut(BaseModel):
    activity_id: uuid.UUID
    node_id: uuid.UUID
    events_written: int


class NodePatchIn(BaseModel):
    title: Optional[str] = None
    priority: Optional[int] = Field(default=None, ge=1, le=5)
    est_effort_min: Optional[int] = Field(default=None, gt=0)


class NodeOut(BaseModel):
    node_id: uuid.UUID
    stable_key: str
    title: str
    priority: int
    est_effort_min: int
    user_edited: bool
