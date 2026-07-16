import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# --------------------------------------------------------------------------- #
# Roster / lifecycle
# --------------------------------------------------------------------------- #

class ClassroomCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    school_name: Optional[str] = Field(default=None, max_length=200)


class ClassroomPatch(BaseModel):
    """All fields optional — PATCH applies only what's provided. `archived`
    toggles archived_at (True sets it to now, False clears it); `regenerate_join_code`
    overwrites join_code with a freshly generated one (invalidating the old code)."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    school_name: Optional[str] = Field(default=None, max_length=200)
    archived: Optional[bool] = None
    regenerate_join_code: Optional[bool] = None


class ClassroomOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    school_name: Optional[str] = None
    join_code: str
    archived_at: Optional[datetime] = None
    created_at: datetime


class TeachingClassroomOut(ClassroomOut):
    member_count: int = 0


class EnrolledClassroomOut(BaseModel):
    """Student's view of a classroom they belong to — no teacher identity."""
    id: uuid.UUID
    name: str
    school_name: Optional[str] = None
    display_name: str  # the caller's own roll-call name in this class
    joined_at: datetime


class MyClassroomsOut(BaseModel):
    teaching: List[TeachingClassroomOut] = []
    enrolled: List[EnrolledClassroomOut] = []


class JoinRequest(BaseModel):
    code: str = Field(min_length=1, max_length=16)
    display_name: str = Field(min_length=1, max_length=120)


class JoinResponse(BaseModel):
    """Drives the /join/{code} consent screen — the exact fields a member of
    this class exposes to the teacher (spec §5)."""
    classroom_id: uuid.UUID
    classroom_name: str
    school_name: Optional[str] = None
    member_id: uuid.UUID
    display_name: str
    teacher_sees: List[str] = [
        "display_name (as you enter it here)",
        "activity timing (when you log/review)",
        "review counts and outcomes",
        "computed mastery per topic (from test scores and reviews)",
        "test scores and per-question outcomes",
        "your streak",
    ]
    teacher_never_sees: List[str] = [
        "your private notes / key memories / mistake text",
        "your free-recall answer text",
        "AI feedback text",
        "your email or Google identity",
        "anything from roadmaps not assigned to this class",
    ]


class MemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    student_user_id: uuid.UUID
    display_name: str
    joined_at: datetime


class MemberRename(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)


class ClassroomRoadmapsIn(BaseModel):
    roadmap_ids: List[uuid.UUID] = Field(default_factory=list, max_length=50)


class ClassroomRoadmapsOut(BaseModel):
    roadmap_ids: List[uuid.UUID] = []


class RoadmapOptionOut(BaseModel):
    id: uuid.UUID
    title: str


class ClassroomRoadmapsDetailOut(BaseModel):
    """GET counterpart to the PUT above — currently assigned roadmap_ids plus
    the full catalog of assignable (school-audience, catalog-only) roadmaps,
    so the frontend's assignment control never has to guess at options."""
    roadmap_ids: List[uuid.UUID] = []
    available: List[RoadmapOptionOut] = []


# --------------------------------------------------------------------------- #
# Class analytics (teacher-owner only)
# --------------------------------------------------------------------------- #

class RoadmapCoverageRow(BaseModel):
    roadmap_id: uuid.UUID
    title: str
    coverage_pct: int  # % of members with any activity/test signal on this roadmap


class ClassroomOverviewOut(BaseModel):
    member_count: int
    active_last_7d: int
    reviews_completed_7d: int
    class_recall_rate_7d: Optional[float] = None
    enough_data_for_recall_rate: bool = False
    at_risk_count: int
    roadmap_coverage: List[RoadmapCoverageRow] = []


class GapMapCellCounts(BaseModel):
    untouched: int = 0
    weak: int = 0
    developing: int = 0
    strong: int = 0


class GapMapNodeOut(BaseModel):
    node_id: uuid.UUID
    title: str
    phase: str
    section: str
    status: str  # class_cell_status: insufficient_data | untouched | weak | developing | strong
    counts: GapMapCellCounts
    weak_students: List[uuid.UUID] = []  # member ids
    root_cause_node_id: Optional[uuid.UUID] = None


class GapMapOut(BaseModel):
    roadmap_id: uuid.UUID
    nodes: List[GapMapNodeOut] = []


class RosterRowOut(BaseModel):
    member_id: uuid.UUID
    display_name: str
    last_active_at: Optional[datetime] = None
    reviews_completed_7d: int = 0
    recall_rate: Optional[float] = None
    current_streak: int = 0
    weak_node_count: int = 0
    overdue_count: int = 0
    at_risk: bool = False
    at_risk_reasons: List[str] = []


class RosterOut(BaseModel):
    students: List[RosterRowOut] = []


class StudentNodeMasteryOut(BaseModel):
    node_id: uuid.UUID
    title: str
    phase: str
    section: str
    status: str  # untouched | weak | developing | strong


class WeeklyRecallBucket(BaseModel):
    week_start: str  # ISO "YYYY-MM-DD", Monday of that week (UTC)
    count: int
    recalled: int
    recall_rate: Optional[float] = None


class StudentDetailOut(BaseModel):
    member_id: uuid.UUID
    display_name: str
    joined_at: datetime
    review_metrics: dict  # ReviewMetrics.model_dump() — reuses services/learner_stats.py shape
    node_accuracy: dict   # NodeAccuracyResponse.model_dump()
    node_mastery: List[StudentNodeMasteryOut] = []
    weekly_recall_trend: List[WeeklyRecallBucket] = []  # last 8 weeks
