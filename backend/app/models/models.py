import uuid
from datetime import datetime, date
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import UniqueConstraint

class Roadmap(SQLModel, table=True):
    __tablename__ = "roadmaps"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    nodes: List["RoadmapNode"] = Relationship(back_populates="roadmap")

class RoadmapNode(SQLModel, table=True):
    __tablename__ = "roadmap_nodes"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    roadmap_id: uuid.UUID = Field(foreign_key="roadmaps.id", ondelete="CASCADE")
    phase: str
    section: str
    title: str
    tier: Optional[str] = None
    order_index: int = Field(default=0)
    description: Optional[str] = None
    # Self-reference: subtopics are child nodes (parent_id -> a top-level node)
    parent_id: Optional[uuid.UUID] = Field(default=None, foreign_key="roadmap_nodes.id", ondelete="CASCADE")

    roadmap: Optional[Roadmap] = Relationship(back_populates="nodes")
    progress: List["UserProgress"] = Relationship(back_populates="node")

class UserProgress(SQLModel, table=True):
    __tablename__ = "user_progress"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID
    node_id: uuid.UUID = Field(foreign_key="roadmap_nodes.id", ondelete="CASCADE")
    status: str = Field(default="not_started")
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    node: Optional[RoadmapNode] = Relationship(back_populates="progress")

class Track(SQLModel, table=True):
    __tablename__ = "tracks"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    activities: List["Activity"] = Relationship(back_populates="track")

class Activity(SQLModel, table=True):
    __tablename__ = "activities"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID
    track_id: Optional[uuid.UUID] = Field(default=None, foreign_key="tracks.id")
    # Optional link to the roadmap this capture belongs to (roadmap-level, not node).
    # Powers the Log form's roadmap picker + future "captures by roadmap" views.
    roadmap_id: Optional[uuid.UUID] = Field(default=None, foreign_key="roadmaps.id")
    topic: str
    notes: Optional[str] = None
    difficulty: int = Field(ge=1, le=5)
    needed_hint: bool = Field(default=False)
    key_memory: str
    mistake: Optional[str] = None
    source_type: Optional[str] = None  # e.g. problem/lecture/video/book/article/course/project/other
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # SM-2 memory state (one activity = one card). Updated on each review completion.
    # repetitions starts at 0 (only the Day-0 baseline scheduled, not yet recalled).
    ease_factor: float = Field(default=2.5)
    repetitions: int = Field(default=0)
    interval_days: int = Field(default=0)
    last_reviewed_at: Optional[datetime] = None  # set on each review completion
    next_review_at: Optional[datetime] = None    # mirrors the open due review (cheap dashboard queries)

    track: Optional[Track] = Relationship(back_populates="activities")
    reviews: List["Review"] = Relationship(back_populates="activity")

class Review(SQLModel, table=True):
    __tablename__ = "reviews"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID
    activity_id: uuid.UUID = Field(foreign_key="activities.id", ondelete="CASCADE")
    status: str = Field(default="due") # 'due', 'completed'
    scheduled_for: datetime
    completed_at: Optional[datetime] = None
    rating: Optional[str] = None # 'easy', 'medium', 'hard' (subjective: how hard it felt)
    recalled: Optional[bool] = None # objective: did they reconstruct it? (got-it / missed-it)
    quality: Optional[int] = None # SM-2 quality grade (0-5) derived from rating+recalled; persisted for analytics
    # LLM recall grader output (proposal only — user's rating/recalled stay authoritative).
    # Stored to compute the calibration metric: self-reported `recalled` vs machine `ai_recalled`.
    ai_verdict: Optional[str] = None   # 'correct' | 'partial' | 'incorrect'
    ai_recalled: Optional[bool] = None # machine judgement of whether they reconstructed the key idea
    ai_feedback: Optional[str] = None  # one short sentence shown after reveal
    created_at: datetime = Field(default_factory=datetime.utcnow)

    activity: Optional[Activity] = Relationship(back_populates="reviews")

class Feedback(SQLModel, table=True):
    __tablename__ = "feedbacks"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID
    message: str
    status: str = Field(default="new") # new, reviewed, resolved
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ReminderLog(SQLModel, table=True):
    """At-most-once-per-day ledger for due-review reminder emails. The unique
    (user_id, sent_on) constraint is the idempotency guard — a second run on the
    same day can't double-send (the INSERT conflicts)."""
    __tablename__ = "reminder_log"
    __table_args__ = (UniqueConstraint("user_id", "sent_on", name="uq_reminder_user_day"),)
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID
    sent_on: date  # UTC date the reminder was sent
    due_count: int = Field(default=0)  # how many were due at send time (for later analysis)
    created_at: datetime = Field(default_factory=datetime.utcnow)
