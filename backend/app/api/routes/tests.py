from collections import defaultdict
from datetime import datetime
from typing import List

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.core.security import SupabaseUser
from app.core.config import settings
from app.models.models import Roadmap, RoadmapNode, Activity, Review, TestAttempt
from app.schemas.test import (
    NodeWeight,
    WeightsResponse,
    GradeFillupRequest,
    GradeFillupResponse,
    SubmitAttemptRequest,
    SubmitAttemptResponse,
)
from app.services.scheduler import apply_fsrs, RATING_AGAIN
from app.services.test_scoring import score_attempt
from app.services.grader import grade_fillup, GraderError

router = APIRouter()

# How many of the user's most recent attempts on this roadmap feed the /weights
# accuracy aggregate. Small and in-Python (no node_mastery table) — see
# SPEC-test-runtime.md for why this is fine at pilot scale.
_RECENT_ATTEMPTS_FOR_WEIGHTS = 10


async def _get_roadmap_or_404(db: AsyncSession, roadmap_slug: str) -> Roadmap:
    roadmap = (
        await db.execute(select(Roadmap).where(Roadmap.slug == roadmap_slug))
    ).scalars().first()
    if not roadmap:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roadmap not found")
    return roadmap


@router.get("/weights", response_model=WeightsResponse)
async def get_weights(
    roadmap_slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Per-node due/accuracy signal so the client can weight its session sample
    toward nodes that are due/overdue or recently missed. Content (the question
    bank) stays client-side; this is the one piece of user-state the client
    can't compute on its own."""
    user_id = uuid.UUID(current_user.id)
    roadmap = await _get_roadmap_or_404(db, roadmap_slug)
    now = datetime.utcnow()

    # Node title -> due/overdue state, from any Activity the user has for this roadmap.
    stmt = (
        select(RoadmapNode.title, Activity.next_review_at)
        .outerjoin(
            Activity,
            (Activity.node_id == RoadmapNode.id) & (Activity.user_id == user_id),
        )
        .where(RoadmapNode.roadmap_id == roadmap.id)
    )
    rows = (await db.execute(stmt)).all()

    due_by_title: dict[str, tuple[bool, int]] = {}
    for title, next_review_at in rows:
        if next_review_at is not None and next_review_at <= now:
            overdue_days = max(0, (now - next_review_at).days)
            due_by_title[title] = (True, overdue_days)
        else:
            due_by_title[title] = (False, 0)

    # Recent accuracy per node, aggregated in Python from the last N attempts.
    recent = (
        await db.execute(
            select(TestAttempt.results)
            .where(TestAttempt.user_id == user_id, TestAttempt.roadmap_id == roadmap.id)
            .order_by(TestAttempt.created_at.desc())
            .limit(_RECENT_ATTEMPTS_FOR_WEIGHTS)
        )
    ).scalars().all()

    got_count: dict[str, int] = defaultdict(int)
    total_count: dict[str, int] = defaultdict(int)
    for results in recent:
        for r in results or []:
            title = r.get("node_title")
            if not title:
                continue
            total_count[title] += 1
            if r.get("outcome") == "got":
                got_count[title] += 1

    nodes = []
    for title, (due, overdue_days) in due_by_title.items():
        attempts = total_count.get(title, 0)
        accuracy = (got_count.get(title, 0) / attempts) if attempts else None
        nodes.append(NodeWeight(
            node_title=title, due=due, overdue_days=overdue_days,
            accuracy_recent=accuracy, attempts_recent=attempts,
        ))

    return WeightsResponse(nodes=nodes)


@router.post("/grade-fillup", response_model=GradeFillupResponse)
async def grade_fillup_question(
    body: GradeFillupRequest,
    current_user: SupabaseUser = Depends(get_current_user),
):
    """The one LLM call in the Tests system: grade a fill-up answer against the
    bank's reference answer. If disabled/unavailable, the frontend falls back to
    showing the reference answer and letting the student self-mark."""
    if not settings.GRADER_ENABLED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grader is disabled")
    try:
        verdict = await grade_fillup(
            question=body.question,
            reference_answer=body.reference_answer,
            student_answer=body.student_answer,
        )
    except GraderError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Grader unavailable: {e}")
    return GradeFillupResponse(verdict=verdict.verdict, feedback=verdict.feedback)


@router.post("/attempts", response_model=SubmitAttemptResponse)
async def submit_attempt(
    body: SubmitAttemptRequest,
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Persist a completed Test session, score it, and run the FSRS bridge.

    FSRS bridge (SPEC-test-runtime.md — do not "improve" without re-reading it):
    tests NEVER create new Activities and NEVER accelerate on success. Only
    'wrong'/'missed' outcomes touch FSRS, and only for nodes that already have
    an Activity with a currently-open Review — 'Add to reviews' stays the one
    explicit entry point into spaced repetition.
    """
    user_id = uuid.UUID(current_user.id)
    roadmap = await _get_roadmap_or_404(db, body.roadmap_slug)
    now = datetime.utcnow()

    score, max_score = score_attempt(body.results)

    attempt = TestAttempt(
        user_id=user_id,
        roadmap_id=roadmap.id,
        phase=body.phase,
        score=score,
        max_score=max_score,
        results=[r.model_dump() for r in body.results],
    )
    db.add(attempt)

    # One reschedule attempt per unique node that was wrong/missed this session.
    rescheduled: List[str] = []
    weak_titles = {r.node_title for r in body.results if r.outcome in ("wrong", "missed")}
    if weak_titles:
        node_rows = (
            await db.execute(
                select(RoadmapNode.id, RoadmapNode.title)
                .where(RoadmapNode.roadmap_id == roadmap.id, RoadmapNode.title.in_(weak_titles))
            )
        ).all()
        node_id_by_title = {title: nid for nid, title in node_rows}

        for title in weak_titles:
            node_id = node_id_by_title.get(title)
            if node_id is None:
                continue
            activity = (
                await db.execute(
                    select(Activity).where(Activity.user_id == user_id, Activity.node_id == node_id)
                )
            ).scalars().first()
            if activity is None:
                continue  # no card in rotation for this node — a test never creates one

            open_review = (
                await db.execute(
                    select(Review).where(Review.activity_id == activity.id, Review.status == "due")
                )
            ).scalars().first()
            if open_review is None:
                continue  # nothing currently scheduled to pull forward

            open_review.status = "superseded"
            db.add(open_review)
            next_review = apply_fsrs(activity, RATING_AGAIN, now)
            db.add(activity)
            db.add(next_review)
            rescheduled.append(title)

    await db.commit()
    await db.refresh(attempt)

    return SubmitAttemptResponse(
        id=attempt.id, score=score, max_score=max_score, rescheduled_nodes=rescheduled,
    )
