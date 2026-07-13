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
    DashboardStats, HeatmapDay, HeatmapResponse, ReviewMetrics, RatingCounts,
    SourceRetentionResponse, SourceRetentionRow,
    CalibrationResponse,
    MemoryStrengthResponse, StrengthBucket,
    NodeAccuracyResponse, NodeAccuracyRow,
    TimeOfDayResponse, TimeOfDayBucket,
)
from app.services.scheduler import REVIEW_SESSION_CAP

router = APIRouter()

# Below this many completed reviews, the retention metrics are statistical noise —
# we tell the user to keep reviewing instead of showing a misleading number.
REVIEW_METRICS_MIN = 5

# Same "don't show noise" floor, sized per-endpoint to what makes the specific
# aggregate meaningful.
SOURCE_RETENTION_MIN = 3    # completed reviews, PER source group
NODE_ACCURACY_MIN = 2       # test-question results, PER node

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


NODE_ACCURACY_TOP_N = 8

# Postgres-only (jsonb_array_elements) — same untestable-on-SQLite boundary as
# reminders.py's auth.users join; conftest.py documents this convention.
_NODE_ACCURACY_SQL = text("""
    select
        elem->>'node_title' as node_title,
        count(*) filter (where elem->>'outcome' = 'got') as got,
        count(*) filter (where elem->>'outcome' = 'missed') as missed,
        count(*) filter (where elem->>'outcome' = 'wrong') as wrong,
        count(*) as total
    from test_attempts ta, jsonb_array_elements(ta.results) as elem
    where ta.user_id = :user_id
    group by elem->>'node_title'
    having count(*) >= :min_results
    order by (count(*) filter (where elem->>'outcome' != 'got'))::float / count(*) desc
    limit :top_n
""")


@router.get("/node-accuracy", response_model=NodeAccuracyResponse)
async def get_node_accuracy(
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Weakest nodes from Tests-section history — the highest miss+wrong rate,
    among nodes with at least NODE_ACCURACY_MIN question results."""
    user_id = uuid.UUID(current_user.id)
    rows = (
        await db.execute(
            _NODE_ACCURACY_SQL,
            {"user_id": user_id, "min_results": NODE_ACCURACY_MIN, "top_n": NODE_ACCURACY_TOP_N},
        )
    ).all()
    if not rows:
        return NodeAccuracyResponse(enough_data=False)
    weakest = [
        NodeAccuracyRow(
            node_title=row.node_title,
            got=row.got, missed=row.missed, wrong=row.wrong, total=row.total,
            accuracy=round(row.got / row.total, 3),
        )
        for row in rows
    ]
    return NodeAccuracyResponse(enough_data=True, weakest=weakest)


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
