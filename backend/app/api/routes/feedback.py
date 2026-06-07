from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.core.security import SupabaseUser
from app.models.models import Feedback
from app.schemas.feedback import FeedbackCreate, FeedbackOut

router = APIRouter()

@router.post("/", response_model=FeedbackOut)
async def create_feedback(
    feedback_in: FeedbackCreate,
    current_user: SupabaseUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    feedback = Feedback(
        user_id=current_user.id,
        message=feedback_in.message
    )
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)
    return feedback
