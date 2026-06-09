from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict, Field
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
    # LLM grader output (proposal); user's rating/recalled stay authoritative.
    ai_verdict: Optional[str] = None
    ai_recalled: Optional[bool] = None
    ai_feedback: Optional[str] = None
    created_at: datetime

    activity: ActivityResponse

class ReviewComplete(BaseModel):
    # Subjective signal: how hard it felt. Constrained to the documented scale.
    rating: Literal["easy", "medium", "hard"]
    # Objective signal: did they actually reconstruct the answer? (got-it / missed-it)
    recalled: Optional[bool] = None

class ReviewGradeRequest(BaseModel):
    # The user's free-recall attempt. Capped to bound LLM cost/latency.
    answer: str = Field(default="", max_length=4000)

class ReviewGradeResponse(BaseModel):
    verdict: Literal["correct", "partial", "incorrect"]
    recalled: bool
    feedback: str
