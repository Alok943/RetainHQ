from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct, cast, Date, text
import statistics
import uuid
from datetime import datetime, timedelta

from app.api.deps import get_db, get_current_user
from app.core.security import SupabaseUser
from app.models.models import Review, Activity
from app.schemas.dashboard import (
    DashboardStats, HeatmapResponse, ReviewMetrics,
    SourceRetentionResponse, SourceRetentionRow,
    CalibrationResponse,
    MemoryStrengthResponse, StrengthBucket,
    NodeAccuracyResponse,
    TimeOfDayResponse, TimeOfDayBucket,
    FocusArea, FocusAreasResponse,
)
from app.services.scheduler import REVIEW_SESSION_CAP
from app.services.learner_stats import REVIEW_METRICS_MIN, get_review_metrics as _get_review_metrics, get_heatmap as _get_heatmap, get_node_accuracy as _get_node_accuracy

router = APIRouter()

# Same "don't show noise" floor, sized per-endpoint to what makes the specific
# aggregate meaningful.
SOURCE_RETENTION_MIN = 3    # completed reviews, PER source group

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


FOCUS_WINDOW_DAYS = 14
FOCUS_LIMIT = 5


@router.get("/focus-areas", response_model=FocusAreasResponse)
async def get_focus_areas(
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Topics the user got WRONG recently — powers Home's 'Key areas to focus'.

    Signal = the user's own `recalled == False` on completed reviews (the honest,
    authoritative miss signal; the AI verdict only supplies the feedback line).
    Grouped per card (activity), most-missed first, capped so the section is a
    nudge and never a wall of shame. Empty list = the section doesn't render.
    """
    user_id = uuid.UUID(current_user.id)
    since = datetime.utcnow() - timedelta(days=FOCUS_WINDOW_DAYS)

    stmt = (
        select(
            Review.activity_id,
            Review.completed_at,
            Review.ai_feedback,
            Activity.topic,
        )
        .join(Activity, Review.activity_id == Activity.id)
        .where(
            Review.user_id == user_id,
            Review.status == "completed",
            Review.recalled == False,  # noqa: E712 — SQLAlchemy needs the comparison
            Review.completed_at >= since,
        )
        .order_by(Review.completed_at.desc())
    )
    rows = (await db.execute(stmt)).all()

    # Aggregate per activity in Python (bounded: one user's 14-day misses).
    by_activity: dict = {}
    for row in rows:
        entry = by_activity.setdefault(
            row.activity_id,
            {"topic": row.topic, "misses": 0, "last": row.completed_at, "feedback": None},
        )
        entry["misses"] += 1
        # rows arrive newest-first, so first non-empty feedback is the latest one
        if entry["feedback"] is None and row.ai_feedback:
            entry["feedback"] = row.ai_feedback

    # Most-missed first; ties broken by recency (newest miss first).
    ranked = sorted(
        by_activity.items(),
        key=lambda kv: (-kv[1]["misses"], -kv[1]["last"].timestamp()),
    )[:FOCUS_LIMIT]

    return FocusAreasResponse(
        areas=[
            FocusArea(
                activity_id=str(aid),
                topic=e["topic"],
                misses=e["misses"],
                last_missed_at=e["last"],
                feedback=e["feedback"],
            )
            for aid, e in ranked
        ]
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
    return await _get_review_metrics(db, user_id, None)


@router.get("/heatmap", response_model=HeatmapResponse)
async def get_heatmap(
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    user_id = uuid.UUID(current_user.id)
    return await _get_heatmap(db, user_id, None)


@router.get("/source-retention", response_model=SourceRetentionResponse)
async def get_source_retention(
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Recall rate grouped by Activity.source_type. Fills the Analytics page's
    'Retention by Source' banner. Each group needs its own SOURCE_RETENTION_MIN
    completed reviews to be shown — a source with 1 review isn't a rate."""
    user_id = uuid.UUID(current_user.id)
    # Built once, reused in both select() and group_by() — two SEPARATE
    # func.coalesce(...) calls compile to textually-distinct bound-parameter
    # expressions ($1 vs $2, same value), which Postgres's GROUP BY validity
    # check does NOT treat as equivalent (unlike SQLite, which let this slide —
    # caught testing against a real Postgres DB, not the SQLite test harness).
    source_type_expr = func.coalesce(Activity.source_type, "other").label("source_type")
    stmt = (
        select(
            source_type_expr,
            func.count(Review.id).label("completed"),
            func.count(Review.id).filter(Review.recalled == True).label("recalled"),
        )
        .select_from(Review)
        .join(Activity, Review.activity_id == Activity.id)
        .where(Review.user_id == user_id, Review.status == "completed")
        .group_by(source_type_expr)
    )
    rows = (await db.execute(stmt)).all()
    sources = [
        SourceRetentionRow(
            source_type=row.source_type,
            completed=row.completed,
            recalled=row.recalled or 0,
            recall_rate=round((row.recalled or 0) / row.completed, 3),
        )
        for row in rows
        if row.completed >= SOURCE_RETENTION_MIN
    ]
    return SourceRetentionResponse(enough_data=len(sources) > 0, sources=sources)


@router.get("/calibration", response_model=CalibrationResponse)
async def get_calibration(
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """How often the AI grader's verdict agrees with the user's own self-rating,
    on reviews the grader actually graded (ai_recalled IS NOT NULL)."""
    user_id = uuid.UUID(current_user.id)
    stmt = (
        select(
            func.count(Review.id).label("graded"),
            func.count(Review.id).filter(Review.recalled == Review.ai_recalled).label("agree"),
            func.count(Review.id)
            .filter(Review.recalled == True, Review.ai_recalled == False)
            .label("overconfident"),
            func.count(Review.id)
            .filter(Review.recalled == False, Review.ai_recalled == True)
            .label("underconfident"),
        )
        .where(Review.user_id == user_id, Review.ai_recalled.is_not(None))
    )
    r = (await db.execute(stmt)).one()
    graded = r.graded or 0
    if graded < REVIEW_METRICS_MIN:
        return CalibrationResponse(enough_data=False, graded=graded)
    return CalibrationResponse(
        enough_data=True,
        graded=graded,
        agreement_rate=round((r.agree or 0) / graded, 3),
        overconfident_rate=round((r.overconfident or 0) / graded, 3),
        underconfident_rate=round((r.underconfident or 0) / graded, 3),
    )


_STRENGTH_BUCKETS = [("<1d", 0, 1), ("1-7d", 1, 7), ("7-30d", 7, 30), ("30-90d", 30, 90), (">90d", 90, None)]


@router.get("/memory-strength", response_model=MemoryStrengthResponse)
async def get_memory_strength(
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Distribution of FSRS stability (days-to-target-decay) across all topics
    that have been through at least one review. Median computed in Python —
    no portable cross-dialect SQL median, and this is a small in-memory list."""
    user_id = uuid.UUID(current_user.id)
    stmt = select(Activity.stability).where(Activity.user_id == user_id, Activity.stability.is_not(None))
    values = [row[0] for row in (await db.execute(stmt)).all()]
    count = len(values)
    if count < REVIEW_METRICS_MIN:
        return MemoryStrengthResponse(enough_data=False, count=count)

    buckets = []
    for label, lo, hi in _STRENGTH_BUCKETS:
        n = sum(1 for v in values if v >= lo and (hi is None or v < hi))
        buckets.append(StrengthBucket(label=label, count=n))

    return MemoryStrengthResponse(
        enough_data=True,
        count=count,
        median_stability_days=round(statistics.median(values), 1),
        buckets=buckets,
    )


@router.get("/node-accuracy", response_model=NodeAccuracyResponse)
async def get_node_accuracy(
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Weakest nodes from Tests-section history — the highest miss+wrong rate,
    among nodes with at least NODE_ACCURACY_MIN question results."""
    user_id = uuid.UUID(current_user.id)
    return await _get_node_accuracy(db, user_id, None)


# Postgres-only (extract(hour from ...)) — frontend shifts UTC→local via
# getTimezoneOffset() rather than the server guessing a timezone.
_TIME_OF_DAY_SQL = text("""
    select
        extract(hour from completed_at)::int as hour_utc,
        count(*) as cnt,
        count(*) filter (where recalled = true) as recalled_cnt,
        avg(duration_ms) as avg_duration
    from reviews
    where user_id = :user_id and status = 'completed'
    group by extract(hour from completed_at)
    order by hour_utc
""")


@router.get("/time-of-day", response_model=TimeOfDayResponse)
async def get_time_of_day(
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Completed-review volume/recall/duration by hour of day (UTC)."""
    user_id = uuid.UUID(current_user.id)
    rows = (await db.execute(_TIME_OF_DAY_SQL, {"user_id": user_id})).all()
    total = sum(row.cnt for row in rows)
    if total < REVIEW_METRICS_MIN:
        return TimeOfDayResponse(enough_data=False)
    buckets = [
        TimeOfDayBucket(
            hour_utc=row.hour_utc,
            count=row.cnt,
            recall_rate=round((row.recalled_cnt or 0) / row.cnt, 3) if row.cnt else None,
            avg_duration_ms=round(row.avg_duration, 0) if row.avg_duration is not None else None,
        )
        for row in rows
    ]
    return TimeOfDayResponse(enough_data=True, buckets=buckets)
