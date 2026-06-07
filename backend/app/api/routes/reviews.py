from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import uuid
from datetime import datetime
from typing import List

from app.api.deps import get_db, get_current_user
from app.core.security import SupabaseUser
from app.models.models import Review, Activity
from app.schemas.review import ReviewResponse, ReviewComplete
from app.services.scheduler import quality_from_outcome, apply_sm2

router = APIRouter()

@router.get("/due", response_model=List[ReviewResponse])
async def get_due_reviews(
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user)
):
    user_id = uuid.UUID(current_user.id)
    now = datetime.utcnow()
    
    # Crucial: selectinload is required for AsyncSession to avoid MissingGreenlet error
    stmt = (
        select(Review)
        .where(
            Review.user_id == user_id,
            Review.status == "due",
            Review.scheduled_for <= now
        )
        .options(selectinload(Review.activity))
        .order_by(Review.scheduled_for.asc())
    )
    
    result = await db.execute(stmt)
    reviews = result.scalars().all()
    return reviews

@router.post("/{review_id}/complete", response_model=ReviewResponse)
async def complete_review(
    review_id: uuid.UUID,
    review_in: ReviewComplete,
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user)
):
    user_id = uuid.UUID(current_user.id)
    
    # IDOR protection: Must fetch by BOTH review_id and user_id
    stmt = (
        select(Review)
        .where(Review.id == review_id, Review.user_id == user_id)
        .options(selectinload(Review.activity))
    )
    result = await db.execute(stmt)
    review = result.scalars().first()
    
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
        
    if review.status == "completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Review already completed")
        
    now = datetime.utcnow()
    review.status = "completed"
    review.completed_at = now
    review.rating = review_in.rating
    review.recalled = review_in.recalled

    # Advance the activity's SM-2 state from this outcome and schedule the next
    # review. activity is eager-loaded above, so this is safe on the async session.
    quality = quality_from_outcome(review_in.rating, review_in.recalled)
    review.quality = quality  # persist the grade for later analytics
    next_review = apply_sm2(review.activity, quality, now)
    db.add(next_review)

    await db.commit()
    await db.refresh(review)

    return review
