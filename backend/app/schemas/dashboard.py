from pydantic import BaseModel

class DashboardStats(BaseModel):
    due_count: int
    consistency_window: int
    daily_progress: int # For a potential progress bar or something similar
