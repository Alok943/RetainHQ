from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
import uuid
from datetime import datetime
from typing import List

from app.api.deps import get_db, get_current_user
from app.core.security import SupabaseUser
from app.core.config import settings
from app.models.models import Review, Activity
from app.schemas.review import (
    ReviewResponse,
    ReviewComplete,
    ReviewGradeRequest,
    ReviewGradeResponse,
)
from app.services.scheduler import quality_from_outcome, apply_sm2
from app.services.grader import grade_recall, GraderError

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


@router.post("/{review_id}/grade", response_model=ReviewGradeResponse)
async def grade_review(
    review_id: uuid.UUID,
    body: ReviewGradeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Grade a free-recall attempt with the LLM grader (non-blocking proposal).

    The verdict is advisory only — it pre-fills the suggested outcome in the UI but
    the user's own rating/recalled (sent to /complete) remain authoritative. We persist
    the AI verdict on the review to compute the self-report-vs-machine calibration metric.
    """
    if not settings.GRADER_ENABLED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grader is disabled")

    user_id = uuid.UUID(current_user.id)

    # Ownership + still-open check; eager-load the activity for topic/key_memory.
    stmt = (
        select(Review)
        .where(
            Review.id == review_id,
            Review.user_id == user_id,
            Review.status == "due",
        )
        .options(selectinload(Review.activity))
    )
    review = (await db.execute(stmt)).scalars().first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found or already completed",
        )

    try:
        verdict = await grade_recall(
            topic=review.activity.topic,
            key_memory=review.activity.key_memory,
            user_answer=body.answer,
        )
    except GraderError as e:
        # Never block the loop on a grader failure — the UI falls back to manual rating.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Grader unavailable: {e}",
        )

    # Persist the proposal (review stays 'due'; user still completes it manually).
    review.ai_verdict = verdict.verdict
    review.ai_recalled = verdict.recalled
    review.ai_feedback = verdict.feedback
    db.add(review)
    await db.commit()

    return ReviewGradeResponse(
        verdict=verdict.verdict,
        recalled=verdict.recalled,
        feedback=verdict.feedback,
        revision_note=verdict.revision_note,
    )
