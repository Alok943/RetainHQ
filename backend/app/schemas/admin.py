from datetime import date
from typing import Optional, List
from pydantic import BaseModel


class FunnelSummary(BaseModel):
    signups: int
    logged_activity: int
    completed_review: int
    returned_later_day: int
    pct_activated: float
    pct_reviewed: float
    pct_retained: float


class FunnelUser(BaseModel):
    email: Optional[str] = None
    signed_up: Optional[date] = None
    activities: int
    reviews_done: int
    last_active: Optional[date] = None


class SourceCount(BaseModel):
    source_type: str
    activities: int


class AdminFunnel(BaseModel):
    summary: FunnelSummary
    users: List[FunnelUser]
    by_source: List[SourceCount]

from datetime import datetime
import uuid

class AdminFeedbackOut(BaseModel):
    id: uuid.UUID
    email: Optional[str] = None
    message: str
    status: str
    created_at: datetime
