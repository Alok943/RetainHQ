from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct, cast, Date
import uuid
from datetime import datetime, timedelta

from app.api.deps import get_db, get_current_user
from app.core.security import SupabaseUser
from app.models.models import Review, Activity
from app.schemas.dashboard import (
    DashboardStats, HeatmapDay, HeatmapResponse, ReviewMetrics, RatingCounts,
)
from app.services.scheduler import REVIEW_SESSION_CAP

router = APIRouter()

# Below this many completed reviews, the retention metrics are statistical noise —
# we tell the user to keep reviewing instead of showing a misleading number.
REVIEW_METRICS_MIN = 5

@router.get("/", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user)
):
    user_id = uuid.UUID(current_user.id)
    now = datetime.utcnow()
    seven_days_ago = now - timedelta(days=7)
    today_start = datetime(now.year, now.month, now.day)

    # One round-trip over activities: all-time total, today's count, and the set of
    # distinct active dates in the last 7 days (for the consistency window).
    act_stmt = (
        select(
            func.count(Activity.id).label("total"),
            func.count(Activity.id).filter(Activity.created_at >= today_start).label("today"),
            func.array_agg(distinct(cast(Activity.created_at, Date)))
            .filter(Activity.created_at >= seven_days_ago)
            .label("active_dates"),
        )
        .where(Activity.user_id == user_id)
    )
    act = (await db.execute(act_stmt)).one()

    # One round-trip over reviews: due now, all-time completed, today's completed,
    # and distinct completed-dates in the last 7 days.
    rev_stmt = (
        select(
            func.count(Review.id)
            .filter(Review.status == "due", Review.scheduled_for <= now)
            .label("due"),
            func.count(Review.id)
            .filter(Review.status == "completed")
            .label("total_completed"),
            func.count(Review.id)
            .filter(Review.status == "completed", Review.completed_at >= today_start)
            .label("today"),
            func.array_agg(distinct(cast(Review.completed_at, Date)))
            .filter(Review.status == "completed", Review.completed_at >= seven_days_ago)
            .label("active_dates"),
            func.min(Review.scheduled_for)
            .filter(Review.status == "due", Review.scheduled_for > now)
            .label("next_review"),
        )
        .where(Review.user_id == user_id)
    )
    rev = (await db.execute(rev_stmt)).one()

    # array_agg(...) FILTER returns NULL (not []) when nothing matches.
    act_dates = set(act.active_dates or [])
    rev_dates = set(rev.active_dates or [])
    consistency_window = len(act_dates | rev_dates)
    daily_progress = (act.today or 0) + (rev.today or 0)

    # Cap the surfaced due count to one session's worth — it must match the
    # bounded queue from /reviews/due so Home never shows a scary backlog number
    # the user can't actually clear in one sitting (the "23 due" death spiral).
    return DashboardStats(
        due_count=min(rev.due or 0, REVIEW_SESSION_CAP),
        consistency_window=consistency_window,
        daily_progress=daily_progress,
        total_activities=act.total or 0,
        total_reviews_completed=rev.total_completed or 0,
        next_review_at=rev.next_review,
    )


@router.get("/review-metrics", response_model=ReviewMetrics)
async def get_review_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Real retention metrics from completed-review history:
      - recall_rate: objective recalled / completed
      - retention_score (0-100) + band: recalled reviews weighted by felt difficulty
        (easy=100, medium=70, hard=40), misses count as 0
      - compliance_rate: completed / (completed + currently-overdue)
    """
    user_id = uuid.UUID(current_user.id)
    now = datetime.utcnow()

    # One round-trip: completed count, recalled count, rating mix, and the
    # recalled-by-rating breakdown needed for the weighted retention score.
    stmt = (
        select(
            func.count(Review.id).filter(Review.status == "completed").label("completed"),
            func.count(Review.id).filter(Review.status == "completed", Review.recalled == True).label("recalled"),
            func.count(Review.id).filter(Review.status == "completed", Review.rating == "easy").label("easy"),
            func.count(Review.id).filter(Review.status == "completed", Review.rating == "medium").label("medium"),
            func.count(Review.id).filter(Review.status == "completed", Review.rating == "hard").label("hard"),
            func.count(Review.id).filter(Review.status == "completed", Review.recalled == True, Review.rating == "easy").label("r_easy"),
            func.count(Review.id).filter(Review.status == "completed", Review.recalled == True, Review.rating == "medium").label("r_medium"),
            func.count(Review.id).filter(Review.status == "completed", Review.recalled == True, Review.rating == "hard").label("r_hard"),
            func.count(Review.id).filter(Review.status == "due", Review.scheduled_for < now).label("overdue"),
        )
        .where(Review.user_id == user_id)
    )
    r = (await db.execute(stmt)).one()

    completed = r.completed or 0
    if completed < REVIEW_METRICS_MIN:
        return ReviewMetrics(reviews_completed=completed, enough_data=False)

    recalled = r.recalled or 0
    recall_rate = recalled / completed

    # Weighted retention: recalled reviews score by felt difficulty; misses = 0.
    score_sum = (r.r_easy or 0) * 100 + (r.r_medium or 0) * 70 + (r.r_hard or 0) * 40
    retention_score = round(score_sum / completed)
    if retention_score >= 90:
        band = "Mastered"
    elif retention_score >= 75:
        band = "Strong"
    elif retention_score >= 50:
        band = "Developing"
    else:
        band = "Weak"

    overdue = r.overdue or 0
    compliance_rate = completed / (completed + overdue) if (completed + overdue) else None

    return ReviewMetrics(
        reviews_completed=completed,
        enough_data=True,
        recall_rate=round(recall_rate, 3),
        retention_score=retention_score,
        retention_band=band,
        compliance_rate=round(compliance_rate, 3) if compliance_rate is not None else None,
        rating_counts=RatingCounts(easy=r.easy or 0, medium=r.medium or 0, hard=r.hard or 0),
    )


@router.get("/heatmap", response_model=HeatmapResponse)
async def get_heatmap(
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    user_id = uuid.UUID(current_user.id)
    now = datetime.utcnow()
    window_start = now - timedelta(days=365)

    # Single round-trip: per-day count + recalled count for the last 365 days.
    # func.count(...).filter(...) is the same FILTER-clause aggregate style used
    # everywhere else in this module.
    stmt = (
        select(
            cast(Review.completed_at, Date).label("day"),
            func.count(Review.id).label("count"),
            func.count(Review.id).filter(Review.recalled == True).label("recalled"),
        )
        .where(
            Review.user_id == user_id,
            Review.status == "completed",
            Review.completed_at >= window_start,
        )
        .group_by(cast(Review.completed_at, Date))
        .order_by(cast(Review.completed_at, Date))
    )
    rows = (await db.execute(stmt)).all()

    # Build the days list and collect the set of active date objects for streak math.
    days: list[HeatmapDay] = []
    active_dates: set = set()
    total_reviews = 0

    for row in rows:
        days.append(HeatmapDay(
            date=row.day.isoformat(),
            count=row.count,
            recalled=row.recalled,
        ))
        active_dates.add(row.day)
        total_reviews += row.count

    # Streak computation in Python — clean and correct.
    # Anchor: today if today is active, else yesterday if yesterday is active,
    # else current_streak = 0.
    from datetime import date as date_type
    today = now.date()
    yesterday = today - timedelta(days=1)

    if today in active_dates:
        anchor = today
    elif yesterday in active_dates:
        anchor = yesterday
    else:
        anchor = None

    current_streak = 0
    if anchor is not None:
        cursor = anchor
        while cursor in active_dates:
            current_streak += 1
            cursor -= timedelta(days=1)

    # Longest streak: walk all active dates in sorted order.
    longest_streak = 0
    if active_dates:
        sorted_dates = sorted(active_dates)
        run = 1
        for i in range(1, len(sorted_dates)):
            if (sorted_dates[i] - sorted_dates[i - 1]).days == 1:
                run += 1
            else:
                longest_streak = max(longest_streak, run)
                run = 1
        longest_streak = max(longest_streak, run)

    return HeatmapResponse(
        days=days,
        current_streak=current_streak,
        longest_streak=longest_streak,
        total_reviews=total_reviews,
        active_days=len(active_dates),
    )
