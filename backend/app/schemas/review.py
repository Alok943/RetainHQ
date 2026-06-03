from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict
import uuid
from .activity import ActivityResponse

class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    activity_id: uuid.UUID
    status: str
    scheduled_for: datetime
    completed_at: Optional[datetime] = None
    rating: Optional[str] = None
    recalled: Optional[bool] = None
    created_at: datetime

    activity: ActivityResponse

class ReviewComplete(BaseModel):
    # Subjective signal: how hard it felt. Constrained to the documented scale.
    rating: Literal["easy", "medium", "hard"]
    # Objective signal: did they actually reconstruct the answer? (got-it / missed-it)
    recalled: Optional[bool] = None
