from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict, Field
import uuid

VALID_SOURCES = Literal["problem", "lecture", "video", "book", "article", "course", "project", "lesson", "other"]

class ActivityCreate(BaseModel):
    topic: str = Field(max_length=300)
    notes: Optional[str] = Field(default=None, max_length=5000)
    difficulty: int = Field(ge=1, le=5)
    needed_hint: bool
    # Capped at 500 chars (~6 lines): a Key Memory is ONE testable claim, not a
    # paragraph dump (a wall of text makes recall feel like failure). Also bounds
    # what we send to the LLM. Only validates new logs — existing rows untouched.
    key_memory: str = Field(max_length=500)
    mistake: Optional[str] = Field(default=None, max_length=2000)
    source_type: Optional[VALID_SOURCES] = None
    roadmap_id: Optional[uuid.UUID] = None  # optional link to the roadmap it belongs to
    node_id: Optional[uuid.UUID] = None  # lesson-level link (roadmap_nodes.id) for "Add to reviews"


class KeyPointsRequest(BaseModel):
    """Ask the LLM to suggest the core sub-points under a topic (capture aid)."""
    topic: str = Field(max_length=300)
    draft: Optional[str] = Field(default=None, max_length=500)


class KeyPointsResponse(BaseModel):
    points: list[str]  # 3-5 short recognition prompts; the user keeps what they learned

class ActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    track_id: Optional[uuid.UUID] = None
    roadmap_id: Optional[uuid.UUID] = None
    topic: str
    notes: Optional[str] = None
    difficulty: int
    needed_hint: bool
    key_memory: str
    mistake: Optional[str] = None
    created_at: datetime
    reviews_scheduled: int = 0
    # True only for a user's first-ever activity, which gets a demo review due
    # now; the UI uses this to send them straight into that review. Later
    # activities schedule their first review for tomorrow (review_due_now=False).
    review_due_now: bool = False

class ActivityListItem(BaseModel):
    """A single captured activity for the Knowledge Vault (browse view)."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    topic: str
    key_memory: str
    notes: Optional[str] = None
    difficulty: int
    needed_hint: bool
    mistake: Optional[str] = None
    source_type: Optional[str] = None
    roadmap_id: Optional[uuid.UUID] = None
    created_at: datetime
    repetitions: int
    next_review_at: Optional[datetime] = None
    last_reviewed_at: Optional[datetime] = None
