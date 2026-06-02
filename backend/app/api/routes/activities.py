from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from app.api.deps import get_db, get_current_user
from app.core.security import SupabaseUser
from app.models.models import Activity
from app.schemas.activity import ActivityCreate, ActivityResponse
from app.services.scheduler import schedule_reviews_for_activity

router = APIRouter()

@router.post("/", response_model=ActivityResponse)
async def log_activity(
    activity_in: ActivityCreate,
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user)
):
    user_id = uuid.UUID(current_user.id)
    
    # Create the activity
    activity = Activity(
        user_id=user_id,
        topic=activity_in.topic,
        notes=activity_in.notes,
        difficulty=activity_in.difficulty,
        needed_hint=activity_in.needed_hint,
        key_memory=activity_in.key_memory,
        mistake=activity_in.mistake
    )
    db.add(activity)
    
    # Flush to generate activity.id without committing the transaction
    await db.flush()
    await db.refresh(activity)
    
    # Schedule reviews based on difficulty/hint
    reviews = schedule_reviews_for_activity(activity)
    if reviews:
        db.add_all(reviews)
        
    await db.commit()
    await db.refresh(activity)
    
    # Build response schema manually to include the custom review count
    return ActivityResponse(
        id=activity.id,
        user_id=activity.user_id,
        track_id=activity.track_id,
        topic=activity.topic,
        notes=activity.notes,
        difficulty=activity.difficulty,
        needed_hint=activity.needed_hint,
        key_memory=activity.key_memory,
        mistake=activity.mistake,
        created_at=activity.created_at,
        reviews_scheduled=len(reviews)
    )
