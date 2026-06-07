from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
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
    # Cap at 20 to avoid flooding the UI after a long break (overdue backlog).
    stmt = (
        select(Review)
        .where(
            Review.user_id == user_id,
            Review.status == "due",
            Review.scheduled_for <= now
        )
        .options(selectinload(Review.activity))
        .order_by(Review.scheduled_for.asc())
        .limit(20)
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
    now = datetime.utcnow()
    quality = quality_from_outcome(review_in.rating, review_in.recalled)

    # Atomic: only transition due→completed once. Prevents double-completion race
    # where two concurrent requests both schedule a next review.
    atomic_stmt = (
        update(Review)
        .where(
            Review.id == review_id,
            Review.user_id == user_id,
            Review.status == "due",
        )
        .values(
            status="completed",
            completed_at=now,
            rating=review_in.rating,
            recalled=review_in.recalled,
            quality=quality,
        )
    )
    result = await db.execute(atomic_stmt)

    if result.rowcount == 0:
        # Either not found, wrong user, or already completed
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Review not found or already completed",
        )

    # Re-fetch with activity loaded for SM-2 advancement
    stmt = (
        select(Review)
        .where(Review.id == review_id)
        .options(selectinload(Review.activity))
    )
    review = (await db.execute(stmt)).scalars().first()

    # Advance the activity's SM-2 state and schedule next review
    next_review = apply_sm2(review.activity, quality, now)
    db.add(next_review)

    await db.commit()
    await db.refresh(review)

    return review
