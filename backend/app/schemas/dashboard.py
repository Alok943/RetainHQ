from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class DashboardStats(BaseModel):
    due_count: int
    consistency_window: int
    daily_progress: int # items done today (activities logged + reviews completed)
    total_activities: int = 0          # lifetime activities logged
    total_reviews_completed: int = 0   # lifetime reviews completed
    next_review_at: Optional[datetime] = None  # soonest future-scheduled review (when nothing is due now)


class HeatmapDay(BaseModel):
    date: str          # ISO "YYYY-MM-DD"
    count: int         # completed reviews that day
    recalled: int      # how many had recalled == True


class HeatmapResponse(BaseModel):
    days: List[HeatmapDay]
    current_streak: int
    longest_streak: int
    total_reviews: int
    active_days: int
