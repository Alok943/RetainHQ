from pydantic import BaseModel

class DashboardStats(BaseModel):
    due_count: int
    consistency_window: int
    daily_progress: int # items done today (activities logged + reviews completed)
    total_activities: int = 0          # lifetime activities logged
    total_reviews_completed: int = 0   # lifetime reviews completed
