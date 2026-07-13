from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
import uuid
from app.api.deps import get_db, get_current_user
from app.core.security import SupabaseUser
from app.core.config import settings
from app.models.models import Activity
from app.schemas.activity import (
    ActivityCreate, ActivityResponse, ActivityListItem,
    KeyPointsRequest, KeyPointsResponse,
)
from app.services.scheduler import initial_review_for_activity
from app.services.grader import suggest_key_points, GraderError
from app.services import analytics

router = APIRouter()

@router.get("/", response_model=List[ActivityListItem])
async def list_activities(
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user)
):
    """All of the current user's captured activities, newest first (Knowledge Vault)."""
    user_id = uuid.UUID(current_user.id)
    stmt = (
        select(Activity)
        .where(Activity.user_id == user_id)
        .order_by(Activity.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/suggest-key-points", response_model=KeyPointsResponse)
async def suggest_key_points_endpoint(
    body: KeyPointsRequest,
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Capture aid (gated): suggest the core sub-points under a topic so a stuck
    learner can KEEP the ones they actually studied. Recognition, not a grade —
    never auto-applied. No DB access; pre-submit, so it hangs off activities, not
    a review id. 404 when disabled → UI hides the feature; 503 on LLM failure."""
    if not settings.GRADER_ENABLED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Disabled")
    if not body.topic.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Topic required")
    try:
        result = await suggest_key_points(body.topic, body.draft)
    except GraderError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    return KeyPointsResponse(points=result.points)


async def _find_lesson_card(
    db: AsyncSession, user_id: uuid.UUID, node_id: uuid.UUID
) -> Optional[Activity]:
    """The user's existing card for this lesson node, if any. Oldest-first so a
    pre-index duplicate pair resolves deterministically instead of erroring."""
    return (
        await db.execute(
            select(Activity)
            .where(Activity.user_id == user_id, Activity.node_id == node_id)
            .order_by(Activity.created_at)
            .limit(1)
        )
    ).scalars().first()


def _existing_card_response(existing: Activity) -> ActivityResponse:
    return ActivityResponse(
        id=existing.id, user_id=existing.user_id, track_id=existing.track_id,
        roadmap_id=existing.roadmap_id, topic=existing.topic, notes=existing.notes,
        difficulty=existing.difficulty, needed_hint=existing.needed_hint,
        key_memory=existing.key_memory, mistake=existing.mistake,
        created_at=existing.created_at, reviews_scheduled=0, review_due_now=False,
    )


@router.post("/", response_model=ActivityResponse)
async def log_activity(
    activity_in: ActivityCreate,
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user)
):
    user_id = uuid.UUID(current_user.id)

    # Lesson-cards are idempotent: one card per (user, node). If this lesson is
    # already in the user's reviews, return that card rather than duplicating it
    # (the "Add to reviews" button can be tapped more than once). The DB-level
    # guard is the uq_activities_user_node partial unique index; this SELECT is
    # just the fast path.
    if activity_in.source_type == "lesson" and activity_in.node_id is not None:
        existing = await _find_lesson_card(db, user_id, activity_in.node_id)
        if existing:
            return _existing_card_response(existing)

    # Is this the user's first-ever activity? If so it gets a one-time demo review
    # due now (instant proof of the recall loop); every later activity's first
    # review waits until tomorrow. Count before inserting so we don't count this one.
    existing_count = (
        await db.execute(
            select(func.count()).select_from(Activity).where(Activity.user_id == user_id)
        )
    ).scalar_one()
    is_first = existing_count == 0

    # Create the activity
    activity = Activity(
        user_id=user_id,
        topic=activity_in.topic,
        notes=activity_in.notes,
        difficulty=activity_in.difficulty,
        needed_hint=activity_in.needed_hint,
        key_memory=activity_in.key_memory,
        mistake=activity_in.mistake,
        source_type=activity_in.source_type,
        roadmap_id=activity_in.roadmap_id,
        node_id=activity_in.node_id,
    )
    db.add(activity)

    # Flush to generate activity.id without committing the transaction. For
    # lesson cards the uq_activities_user_node index closes the SELECT-then-INSERT
    # race: if a concurrent tap won, return their card instead of erroring.
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        if activity_in.source_type == "lesson" and activity_in.node_id is not None:
            existing = await _find_lesson_card(db, user_id, activity_in.node_id)
            if existing:
                return _existing_card_response(existing)
        raise
    await db.refresh(activity)

    # Every activity enters the SM-2 rotation: initialize its memory state and
    # schedule the first review (tomorrow, or now for the first-ever demo card).
    # Subsequent reviews are scheduled on completion (see reviews.complete_review).
    first_review = initial_review_for_activity(activity, immediate=is_first)
    db.add(first_review)

    await db.commit()
    await db.refresh(activity)

    # Server-truth: a card entered the FSRS rotation. `immediate` first cards are
    # the activation demo; every other is a normal +1d schedule.
    analytics.capture(
        user_id,
        "review_scheduled",
        {"first_review": True, "immediate": is_first, "source_type": activity.source_type},
    )

    # Build response schema manually to include the custom review count
    return ActivityResponse(
        id=activity.id,
        user_id=activity.user_id,
        track_id=activity.track_id,
        roadmap_id=activity.roadmap_id,
        topic=activity.topic,
        notes=activity.notes,
        difficulty=activity.difficulty,
        needed_hint=activity.needed_hint,
        key_memory=activity.key_memory,
        mistake=activity.mistake,
        created_at=activity.created_at,
        reviews_scheduled=1,
        review_due_now=is_first,
    )
