"""
Aggregate-query bodies shared between the self-serve /api/dashboard/* endpoints
and the teacher drill-down (SPEC-teacher-dashboard.md §4.3 "Refactor, don't
duplicate"). Each function takes (db, user_id, roadmap_scope): roadmap_scope
is None for the self-serve path (unscoped — identical to the pre-refactor
behavior) or a list of roadmap ids when a teacher views one student's stats
scoped to the classroom's assigned roadmaps. One implementation, two
authorization callers.
"""
import uuid
from datetime import datetime, timedelta

from sqlalchemy import select, func, cast, Date, text, bindparam
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PG_UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Review, Activity
from app.schemas.dashboard import (
    HeatmapDay, HeatmapResponse, ReviewMetrics, RatingCounts,
    NodeAccuracyResponse, NodeAccuracyRow,
)

# Below this many completed reviews, the retention metrics are statistical noise —
# we tell the user to keep reviewing instead of showing a misleading number.
REVIEW_METRICS_MIN = 5

# Same "don't show noise" floor, sized per-endpoint to what makes the specific
# aggregate meaningful.
NODE_ACCURACY_MIN = 2       # test-question results, PER node
NODE_ACCURACY_TOP_N = 8


async def get_review_metrics(
    db: AsyncSession, user_id: uuid.UUID, roadmap_scope: list[uuid.UUID] | None
) -> ReviewMetrics:
    """Real retention metrics from completed-review history:
      - recall_rate: objective recalled / completed
      - retention_score (0-100) + band: recalled reviews weighted by felt difficulty
        (easy=100, medium=70, hard=40), misses count as 0
      - compliance_rate: completed / (completed + currently-overdue)
    """
    now = datetime.utcnow()

    # One round-trip: completed count, recalled count, rating mix, and the
    # recalled-by-rating breakdown needed for the weighted retention score.
    stmt = select(
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
    where = [Review.user_id == user_id]
    # Unscoped self-serve path stays exactly as before (no join); a teacher
    # drill-down joins Activity in only to add the roadmap-scope filter.
    if roadmap_scope is not None:
        stmt = stmt.select_from(Review).join(Activity, Review.activity_id == Activity.id)
        where.append(Activity.roadmap_id.in_(roadmap_scope))
    stmt = stmt.where(*where)
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


async def get_heatmap(
    db: AsyncSession, user_id: uuid.UUID, roadmap_scope: list[uuid.UUID] | None
) -> HeatmapResponse:
    now = datetime.utcnow()
    window_start = now - timedelta(days=365)

    # Single round-trip: per-day count + recalled count for the last 365 days.
    # func.count(...).filter(...) is the same FILTER-clause aggregate style used
    # everywhere else in this module.
    stmt = select(
        cast(Review.completed_at, Date).label("day"),
        func.count(Review.id).label("count"),
        func.count(Review.id).filter(Review.recalled == True).label("recalled"),
    )
    where = [
        Review.user_id == user_id,
        Review.status == "completed",
        Review.completed_at >= window_start,
    ]
    if roadmap_scope is not None:
        stmt = stmt.select_from(Review).join(Activity, Review.activity_id == Activity.id)
        where.append(Activity.roadmap_id.in_(roadmap_scope))
    stmt = (
        stmt.where(*where)
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


# Postgres-only (jsonb_array_elements) — same untestable-on-SQLite boundary as
# reminders.py's auth.users join; conftest.py documents this convention.
# roadmap_scope is bound as a Postgres uuid[] and short-circuited via
# "is null or" so the unscoped self-serve call passes no effective filter.
_NODE_ACCURACY_SQL = text("""
    select
        elem->>'node_title' as node_title,
        count(*) filter (where elem->>'outcome' = 'got') as got,
        count(*) filter (where elem->>'outcome' = 'missed') as missed,
        count(*) filter (where elem->>'outcome' = 'wrong') as wrong,
        count(*) as total
    from test_attempts ta, jsonb_array_elements(ta.results) as elem
    where ta.user_id = :user_id
      and (:roadmap_scope is null or ta.roadmap_id = any(:roadmap_scope))
    group by elem->>'node_title'
    having count(*) >= :min_results
    order by (count(*) filter (where elem->>'outcome' != 'got'))::float / count(*) desc
    limit :top_n
""").bindparams(bindparam("roadmap_scope", type_=ARRAY(PG_UUID)))


async def get_node_accuracy(
    db: AsyncSession, user_id: uuid.UUID, roadmap_scope: list[uuid.UUID] | None
) -> NodeAccuracyResponse:
    """Weakest nodes from Tests-section history — the highest miss+wrong rate,
    among nodes with at least NODE_ACCURACY_MIN question results."""
    rows = (
        await db.execute(
            _NODE_ACCURACY_SQL,
            {
                "user_id": user_id,
                "roadmap_scope": list(roadmap_scope) if roadmap_scope is not None else None,
                "min_results": NODE_ACCURACY_MIN,
                "top_n": NODE_ACCURACY_TOP_N,
            },
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
