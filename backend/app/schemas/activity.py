from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
import uuid

class ActivityCreate(BaseModel):
    topic: str
    notes: Optional[str] = None
    difficulty: int
    needed_hint: bool
    key_memory: str
    mistake: Optional[str] = None
    source_type: Optional[str] = None

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
