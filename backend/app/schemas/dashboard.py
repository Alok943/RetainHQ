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


class RatingCounts(BaseModel):
    easy: int = 0
    medium: int = 0
    hard: int = 0


class ReviewMetrics(BaseModel):
    """User-facing retention metrics, computed from completed-review history.

    `enough_data` gates the UI: below a small threshold we surface an honest
    "keep reviewing" state instead of a noisy, misleading number from 1-2 reviews.
    """
    reviews_completed: int
    enough_data: bool
    recall_rate: Optional[float] = None       # 0-1: objective recalled / completed
    retention_score: Optional[int] = None     # 0-100: recalled reviews weighted by felt difficulty
    retention_band: Optional[str] = None       # Weak | Developing | Strong | Mastered
    compliance_rate: Optional[float] = None   # 0-1: completed / (completed + currently-overdue)
    rating_counts: RatingCounts = RatingCounts()


# --- HANDOFF-sentry-push-analytics.md C3: aggregation endpoints -------------- #

class SourceRetentionRow(BaseModel):
    source_type: str  # 'other' for NULL
    completed: int
    recalled: int
    recall_rate: float


class SourceRetentionResponse(BaseModel):
    enough_data: bool  # True iff at least one source cleared its own floor
    sources: List[SourceRetentionRow] = []


class CalibrationResponse(BaseModel):
    enough_data: bool
    graded: int = 0             # reviews with an ai_recalled verdict
    agreement_rate: Optional[float] = None      # ai_recalled == recalled
    overconfident_rate: Optional[float] = None  # user said recalled, AI disagreed
    underconfident_rate: Optional[float] = None # user said missed, AI thought they had it


class StrengthBucket(BaseModel):
    label: str   # '<1d' | '1-7d' | '7-30d' | '30-90d' | '>90d'
    count: int


class MemoryStrengthResponse(BaseModel):
    enough_data: bool
    count: int = 0
    median_stability_days: Optional[float] = None
    buckets: List[StrengthBucket] = []


class NodeAccuracyRow(BaseModel):
    node_title: str
    got: int
    missed: int
    wrong: int
    total: int
    accuracy: float  # got / total


class NodeAccuracyResponse(BaseModel):
    enough_data: bool
    weakest: List[NodeAccuracyRow] = []


class TimeOfDayBucket(BaseModel):
    hour_utc: int  # 0-23
    count: int
    recall_rate: Optional[float] = None
    avg_duration_ms: Optional[float] = None


class TimeOfDayResponse(BaseModel):
    enough_data: bool
    buckets: List[TimeOfDayBucket] = []
