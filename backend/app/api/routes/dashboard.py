from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import uuid
from datetime import datetime, timedelta

from app.api.deps import get_db, get_current_user
from app.core.security import SupabaseUser
from app.models.models import Review, Activity
from app.schemas.dashboard import DashboardStats

router = APIRouter()

@router.get("/", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user)
):
    user_id = uuid.UUID(current_user.id)
    now = datetime.utcnow()
    
    # 1. Calculate due count
    due_stmt = select(func.count(Review.id)).where(
        Review.user_id == user_id,
        Review.status == "due",
        Review.scheduled_for <= now
    )
    due_result = await db.execute(due_stmt)
    due_count = due_result.scalar_one() or 0
    
    # 2. Calculate consistency window (over last 7 days)
    seven_days_ago = now - timedelta(days=7)
    
    # Get days with logged activities
    activities_stmt = select(Activity.created_at).where(
        Activity.user_id == user_id,
        Activity.created_at >= seven_days_ago
    )
    activities_result = await db.execute(activities_stmt)
    active_days_activities = {d.date() for (d,) in activities_result.all()}
    
    # Get days with completed reviews
    reviews_stmt = select(Review.completed_at).where(
        Review.user_id == user_id,
        Review.status == "completed",
        Review.completed_at >= seven_days_ago
    )
    reviews_result = await db.execute(reviews_stmt)
    active_days_reviews = {d.date() for (d,) in reviews_result.all() if d is not None}
    
    # Union of both sets of dates
    active_dates = active_days_activities.union(active_days_reviews)
    consistency_window = len(active_dates)
    
    # Count total activities today + total reviews completed today
    today_start = datetime(now.year, now.month, now.day)
    
    today_act_stmt = select(func.count(Activity.id)).where(
        Activity.user_id == user_id,
        Activity.created_at >= today_start
    )
    today_act_res = await db.execute(today_act_stmt)
    today_activities = today_act_res.scalar_one() or 0
    
    today_rev_stmt = select(func.count(Review.id)).where(
        Review.user_id == user_id,
        Review.status == "completed",
        Review.completed_at >= today_start
    )
    today_rev_res = await db.execute(today_rev_stmt)
    today_reviews = today_rev_res.scalar_one() or 0
    
    daily_progress = today_activities + today_reviews

    # 4. Lifetime totals (real, cheap counts — safe for launch)
    total_act_stmt = select(func.count(Activity.id)).where(Activity.user_id == user_id)
    total_activities = (await db.execute(total_act_stmt)).scalar_one() or 0

    total_done_stmt = select(func.count(Review.id)).where(
        Review.user_id == user_id,
        Review.status == "completed",
    )
    total_reviews_completed = (await db.execute(total_done_stmt)).scalar_one() or 0

    return DashboardStats(
        due_count=due_count,
        consistency_window=consistency_window,
        daily_progress=daily_progress,
        total_activities=total_activities,
        total_reviews_completed=total_reviews_completed,
    )
