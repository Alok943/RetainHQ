from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict, Field
import uuid

VALID_SOURCES = Literal["problem", "lecture", "video", "book", "article", "course", "project", "other"]

class ActivityCreate(BaseModel):
    topic: str = Field(max_length=300)
    notes: Optional[str] = Field(default=None, max_length=5000)
    difficulty: int = Field(ge=1, le=5)
    needed_hint: bool
    key_memory: str = Field(max_length=2000)
    mistake: Optional[str] = Field(default=None, max_length=2000)
    source_type: Optional[VALID_SOURCES] = None

class ActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    track_id: Optional[uuid.UUID] = None
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
    created_at: datetime
    repetitions: int
    next_review_at: Optional[datetime] = None
    last_reviewed_at: Optional[datetime] = None
