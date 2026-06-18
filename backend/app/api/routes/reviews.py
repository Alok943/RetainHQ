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
    ReviewQuestionsResponse,
    ReviewGradeQuestionsRequest,
    ReviewGradeQuestionsResponse,
)
from app.services.scheduler import quality_from_outcome, apply_sm2, REVIEW_SESSION_CAP
from app.services.grader import (
    grade_recall,
    generate_questions,
    grade_question_set,
    GraderError,
)

router = APIRouter()

@router.get("/due", response_model=List[ReviewResponse])
async def get_due_reviews(
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user)
):
    user_id = uuid.UUID(current_user.id)
    now = datetime.utcnow()
    
    # Crucial: selectinload is required for AsyncSession to avoid MissingGreenlet error.
    # Cap the session (oldest-first) so a long-overdue backlog surfaces as a bounded,
    # finishable set — the rest stay 'due' and roll forward to the next session.
    stmt = (
        select(Review)
        .where(
            Review.user_id == user_id,
            Review.status == "due",
            Review.scheduled_for <= now
        )
        .options(selectinload(Review.activity))
        .order_by(Review.scheduled_for.asc())
        .limit(REVIEW_SESSION_CAP)
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
        related_subtopics=[
            {"title": s.title, "explainer": s.explainer} for s in verdict.related_subtopics
        ],
    )


async def _load_open_review(db: AsyncSession, review_id: uuid.UUID, user_id: uuid.UUID) -> Review:
    """Fetch a still-due review owned by the user, with its activity eager-loaded.

    Raises 404 if not found / not owned / already completed (shared by question mode).
    """
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
    return review


@router.post("/{review_id}/questions", response_model=ReviewQuestionsResponse)
async def get_review_questions(
    review_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Question mode (PROTOTYPE, gated on GRADER_ENABLED): generate 2-3 short-answer
    questions from the activity's key_memory. Advisory layer over free recall — the
    frontend falls back to the single free-recall box if this 404s (disabled) or 503s.
    """
    if not settings.GRADER_ENABLED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question mode is disabled")

    user_id = uuid.UUID(current_user.id)
    review = await _load_open_review(db, review_id, user_id)

    try:
        generated = await generate_questions(
            topic=review.activity.topic,
            key_memory=review.activity.key_memory,
            notes=review.activity.notes,
            mistake=review.activity.mistake,
        )
    except GraderError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Question generation unavailable: {e}",
        )

    return ReviewQuestionsResponse(questions=generated.questions)


@router.post("/{review_id}/grade-questions", response_model=ReviewGradeQuestionsResponse)
async def grade_review_questions(
    review_id: uuid.UUID,
    body: ReviewGradeQuestionsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Grade the question-mode answers against the key_memory (one LLM call). Advisory:
    persists the verdict on the review (reusing the ai_* columns) but the user's own
    rating/recalled sent to /complete remain authoritative.
    """
    if not settings.GRADER_ENABLED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question mode is disabled")

    user_id = uuid.UUID(current_user.id)
    review = await _load_open_review(db, review_id, user_id)

    try:
        graded = await grade_question_set(
            topic=review.activity.topic,
            key_memory=review.activity.key_memory,
            qa_pairs=[{"question": qa.question, "answer": qa.answer} for qa in body.answers],
        )
    except GraderError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Question grader unavailable: {e}",
        )

    # Persist as the review's AI proposal (same columns as free-recall grading).
    review.ai_verdict = "correct" if graded.recalled else "incorrect"
    review.ai_recalled = graded.recalled
    review.ai_feedback = graded.feedback
    db.add(review)
    await db.commit()

    return ReviewGradeQuestionsResponse(
        recalled=graded.recalled,
        feedback=graded.feedback,
        items=[
            {"question": it.question, "correct": it.correct, "note": it.note}
            for it in graded.items
        ],
        related_subtopics=[
            {"title": s.title, "explainer": s.explainer} for s in graded.related_subtopics
        ],
    )
