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
    daily_minutes: int = 60
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


# --- Phase 3: Scheduler & Today screen (SPEC-career-coach-phase3.md §4) ------

class PlanItemOut(BaseModel):
    kind: str                                  # 'review' | 'study' | 'balance'
    review_id: Optional[uuid.UUID] = None
    node_id: Optional[uuid.UUID] = None
    label: str
    reason: str
    est_share: float


class TodayPlanOut(BaseModel):
    items: list[PlanItemOut]
    balance: dict[str, float]
    overflow: bool
    tree_complete: bool
    daily_minutes: int


class GoalPatchIn(BaseModel):
    """daily_minutes only, deliberately unconstrained here — the route clamps
    to 30-240 server-side rather than 422ing on an overshoot (§6)."""
    daily_minutes: int


class TodayFeedbackIn(BaseModel):
    item_ref: str
    action: str  # 'done' | 'skipped'


# --- Attached roadmaps (IMPLEMENTATION-career-attached-roadmaps.md) ----------

class AvailableRoadmapOut(BaseModel):
    id: uuid.UUID
    slug: Optional[str] = None
    title: str
    node_count: int
    source: str  # 'inbuilt' | 'mine'


class AvailableRoadmapsOut(BaseModel):
    inbuilt: list[AvailableRoadmapOut]
    mine: list[AvailableRoadmapOut]


class AttachRoadmapIn(BaseModel):
    """One-click attach: roadmap_id is the only required field. `subject` and
    `default_priority` are derived from the roadmap when omitted, so the UI can
    be a single button rather than a form."""
    roadmap_id: uuid.UUID
    subject: Optional[str] = None
    default_priority: Optional[int] = None


class AttachedRoadmapOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    roadmap_id: uuid.UUID
    slug: Optional[str] = None
    title: str
    subject: str
    default_priority: int
    node_count: int
    nodes_added: int = 0
