import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
import random
import uuid
from datetime import datetime
from typing import List, Optional

from app.api.deps import get_db, get_current_user
from app.core.security import SupabaseUser
from app.core.config import settings
from app.models.models import Review, Activity, RoadmapNode, Roadmap, QuestionSet, Problem, ProblemConcept
from app.schemas.review import (
    ReviewResponse,
    ReviewComplete,
    ReviewGradeRequest,
    ReviewGradeResponse,
    ReviewQuestionsRequest,
    ReviewQuestionsResponse,
    ReviewGradeQuestionsRequest,
    ReviewGradeQuestionsResponse,
)
from app.services.scheduler import (
    quality_from_outcome,
    fsrs_rating_from_outcome,
    apply_fsrs,
    current_retrievability,
    REVIEW_SESSION_CAP,
    DUE_QUEUE_FETCH_CAP,
)
from app.services.grader import (
    grade_recall,
    generate_question_items,
    grade_question_set,
    GraderError,
)
from app.services import analytics, evidence, metrics, recall_answer_key
from app.services.topic_key import resolve_topic_keys

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/due", response_model=List[ReviewResponse])
async def get_due_reviews(
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user)
):
    user_id = uuid.UUID(current_user.id)
    now = datetime.utcnow()

    # Crucial: selectinload is required for AsyncSession to avoid MissingGreenlet error.
    # Ranking is by each card's CURRENT retrievability (docs/IMPLEMENTATION-quiz-
    # capture-v2.md Step 5.1), an FSRS decay computation SQL can't order by — so
    # the final cap to REVIEW_SESSION_CAP happens in Python, not SQL. The SQL
    # LIMIT here is only an outer safety bound (DUE_QUEUE_FETCH_CAP) so a huge
    # backlog still can't force an unbounded fetch; ties within that bound keep
    # the old oldest-scheduled-first order.
    stmt = (
        select(Review, Roadmap.slug.label("roadmap_slug"), RoadmapNode.title.label("node_title"))
        .join(Activity, Review.activity_id == Activity.id)
        .outerjoin(RoadmapNode, Activity.node_id == RoadmapNode.id)
        .outerjoin(Roadmap, RoadmapNode.roadmap_id == Roadmap.id)
        .where(
            Review.user_id == user_id,
            Review.status == "due",
            Review.scheduled_for <= now
        )
        .options(selectinload(Review.activity))
        .order_by(Review.scheduled_for.asc())
        .limit(DUE_QUEUE_FETCH_CAP)
    )

    result = await db.execute(stmt)
    rows = result.all()

    # Lowest retrievability = most at risk of being forgotten = surfaces first.
    # Tie-break on scheduled_for so cards with equal retrievability (e.g.
    # several brand-new cards, all 0.0) still sort deterministically instead
    # of in whatever order Postgres happened to return them.
    rows.sort(key=lambda row: (current_retrievability(row.Review.activity, now), row.Review.scheduled_for))
    rows = rows[:REVIEW_SESSION_CAP]

    # Rotation hint: the most recent COMPLETED review's question_served per
    # activity, so the client can avoid repeating the same item this session.
    activity_ids = [row.Review.activity_id for row in rows]
    last_served_by_activity: dict = {}
    if activity_ids:
        served_rows = (
            await db.execute(
                select(Review.activity_id, Review.question_served)
                .where(
                    Review.activity_id.in_(activity_ids),
                    Review.status == "completed",
                    Review.question_served.is_not(None),
                )
                .order_by(Review.completed_at.desc())
            )
        ).all()
        for r in served_rows:
            last_served_by_activity.setdefault(r.activity_id, r.question_served)

    # Batched: every activity needing the embedding fallback is embedded in
    # ONE call (services/topic_key.py), not one blocking call per card.
    topics_by_activity = await resolve_topic_keys(db, [row.Review.activity for row in rows])

    reviews = []
    for row in rows:
        # Review (SQLModel, table=True) has no roadmap_slug/node_title fields —
        # attach them on the response schema instead of the ORM row.
        review = ReviewResponse.model_validate(row.Review)
        review.roadmap_slug = row.roadmap_slug
        review.node_title = row.node_title
        review.last_question_served = last_served_by_activity.get(row.Review.activity_id)
        topic = topics_by_activity[row.Review.activity_id]
        review.topic_key = topic.key
        review.topic_label = topic.label
        reviews.append(review)

    # topic_key resolution may have written the embedding-fallback derived
    # cache onto some activities (services/topic_key.py) — commit that once
    # for the whole batch rather than per-card.
    await db.commit()

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

    rating = review_in.rating
    recalled = review_in.recalled

    # Server-side MCQ verification (docs/IMPLEMENTATION-quiz-capture-v2.md
    # Step 5.3): "never trust a client `correct: true`". Only lesson-sourced
    # MCQs can be verified today — services/recall_answer_key.py is synced from
    # content/roadmaps, the backend's only view into which option is correct.
    # A manual/QuestionSet MCQ (Step 6) or a missing/stale manifest entry falls
    # back to trusting the client, same as every other path today — this must
    # never fail a completion, only skip the extra check.
    if review_in.question_format == "mcq" and review_in.question_source == "lesson" and review_in.question_served:
        entry = recall_answer_key.lookup(review_in.question_served)
        if entry is not None:
            server_correct = (
                review_in.selected_option_index is not None
                and review_in.selected_option_index == entry["correct_index"]
            )
            recalled = server_correct
            rating = "medium" if server_correct and not review_in.hint_used else "hard"

    # quality (0-5) is persisted for analytics continuity; the FSRS grade (1-4)
    # drives scheduling. Both derive from the same (rating, recalled) signals —
    # server-verified above when applicable, the client's own otherwise.
    quality = quality_from_outcome(rating, recalled)
    fsrs_rating = fsrs_rating_from_outcome(rating, recalled)

    # A client-measured timer is trust-but-verify: clamp to a plausible single-
    # card range (30 min ceiling) rather than reject the completion outright —
    # a garbage/absent value just means no duration metric for this card.
    duration_ms = review_in.duration_ms
    if duration_ms is not None and not (0 < duration_ms <= 1_800_000):
        duration_ms = None
    think_ms = review_in.think_ms
    if think_ms is not None and not (0 < think_ms <= 1_800_000):
        think_ms = None

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
            rating=rating,
            recalled=recalled,
            quality=quality,
            duration_ms=duration_ms,
            mode=review_in.mode,
            question_format=review_in.question_format,
            question_tier=review_in.question_tier,
            question_source=review_in.question_source,
            question_served=review_in.question_served,
            hint_used=review_in.hint_used,
            think_ms=think_ms,
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

    # Advance the activity's FSRS state and schedule next review
    next_review = apply_fsrs(review.activity, fsrs_rating, now)
    db.add(next_review)

    await db.commit()
    await db.refresh(review)

    # Evidence spine (SPEC-career-coach-phase1 §6.1/§6.3) — failure-isolated:
    # a bug in this brand-new, low-traffic feature must never break the
    # review loop that already committed above. Most existing activities have
    # node_id=NULL (only lesson-created cards set it) — never guess a node,
    # just count the miss so phase 2 can see how large the gap actually is.
    #
    # The attempt is wrapped in a SAVEPOINT (db.begin_nested()), not a bare
    # try/except around db.rollback(): a plain session.rollback() expires
    # every object already loaded on `db` — including `review.activity`,
    # eager-loaded above via selectinload — and the next unguarded attribute
    # access (analytics.capture()'s review.activity.interval_days, just below)
    # would then try to lazy-load on a sync attribute access outside any
    # await, crashing with MissingGreenlet. A savepoint rollback undoes only
    # this block's own work and leaves the rest of the session untouched.
    if review.activity.node_id is not None:
        try:
            async with db.begin_nested():
                grade = evidence.recall_grade(recalled, rating, review.quality)
                if grade is not None:
                    await evidence.record_event(
                        db, user_id,
                        event_type="RECALL_GRADED",
                        trust_tier="T2_verified_internal",
                        source="retainhq_review",
                        node_id=review.activity.node_id,
                        grade=grade,
                        outcome="pass" if recalled else "fail",
                        duration_min=round(duration_ms / 60000) if duration_ms else 0,
                        entity_id=review.id,
                        payload={
                            "rating": rating,
                            "recalled": recalled,
                            "quality": review.quality,
                            "ai_verdict": review.ai_verdict,
                        },
                    )
            await db.commit()
        except Exception:
            logger.exception("evidence record_event failed for review %s", review.id)
    else:
        try:
            async with db.begin_nested():
                await metrics.record_metric_event(
                    db, user_id,
                    event_type="evidence_unmapped",
                    payload={"reason": "no_node_id", "activity_id": str(review.activity_id)},
                )
            await db.commit()
        except Exception:
            logger.exception("evidence_unmapped metric failed for review %s", review.id)

    # Server-truth: the spaced-repetition loop advanced this card. `interval_days`
    # is the new spacing — a rising interval across a cohort means memory is sticking.
    analytics.capture(
        user_id,
        "review_scheduled",
        {
            "first_review": False,
            "rating": rating,
            "recalled": recalled,
            "interval_days": review.activity.interval_days,
        },
    )

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
    body: ReviewQuestionsRequest | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Question mode (gated on GRADER_ENABLED): serve a persisted question set for
    this card, shuffled. A set is generated once and reused for QUESTION_SET_REUSE
    sessions before a fresh one is made — LLM cost amortizes, questions stay stable
    while the memory forms, and the random order stops sequence-memorization.

    Grounding: node-linked cards get TOPIC-grounded questions (title + description
    is the contract; key_memory only biases); free-form cards keep the
    key_memory-as-sole-truth model. Frontend falls back to the single free-recall
    box if this 404s (disabled) or 503s.
    """
    if not settings.GRADER_ENABLED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question mode is disabled")

    user_id = uuid.UUID(current_user.id)
    review = await _load_open_review(db, review_id, user_id)
    activity = review.activity
    depth = body.depth if body else "main"

    # Reuse: newest set for this card + depth that hasn't exhausted its sessions.
    qset = (
        await db.execute(
            select(QuestionSet)
            .where(
                QuestionSet.activity_id == activity.id,
                QuestionSet.user_id == user_id,
                QuestionSet.depth == depth,
                QuestionSet.times_used < settings.QUESTION_SET_REUSE,
            )
            .order_by(QuestionSet.created_at.desc())
        )
    ).scalars().first()

    if not qset:
        node_title = node_description = unit = None
        if activity.node_id:
            node = (
                await db.execute(select(RoadmapNode).where(RoadmapNode.id == activity.node_id))
            ).scalars().first()
            if node:
                node_title, node_description, unit = node.title, node.description, node.section
                
        problem_context = None
        if getattr(activity, 'problem_id', None):
            problem = (await db.execute(select(Problem).where(Problem.id == activity.problem_id))).scalars().first()
            if problem:
                rows = (
                    await db.execute(
                        select(ProblemConcept.role, RoadmapNode.title)
                        .join(RoadmapNode, RoadmapNode.id == ProblemConcept.node_id)
                        .where(ProblemConcept.problem_id == activity.problem_id)
                    )
                ).all()
                primary_node_title = next((r.title for r in rows if r.role == "primary"), None)
                alt_node_titles = [r.title for r in rows if r.role == "alternative"]

                # What the user actually wrote, inferred once at log time from
                # their pasted solution (services/approach_inference.py). Absent
                # for every card logged without code — then this block is empty
                # and generation behaves exactly as it did before.
                summary = getattr(activity, 'approach_summary', None) or {}
                approach_title = summary.get("node_title")
                approach_facts = summary.get("facts") or []

                problem_context = {
                    "problem_title": problem.title,
                    "primary_node_title": primary_node_title,
                    "alternative_node_titles": alt_node_titles,
                    "language": getattr(activity, 'language', None),
                    "user_approach_title": approach_title,
                    "user_approach_facts": approach_facts,
                }

                # Re-ground the SYLLABUS TOPIC on the approach the user took, but
                # ONLY on a high-confidence read. Rule 1 of the prompt makes the
                # topic block a hard boundary ("never quiz neighboring topics"),
                # so leaving it on the catalog primary while the facts describe a
                # different approach hands the model two contradictory contracts.
                # Medium/low bands keep the catalog primary as the topic and let
                # the facts sharpen the implementation questions only — the
                # asymmetry is deliberate: a wrong topic swap costs a whole
                # question set, a wrong fact costs one question.
                if getattr(activity, 'approach_confidence', None) == "high" and getattr(activity, 'approach_node_id', None):
                    approach_node = (
                        await db.execute(
                            select(RoadmapNode).where(RoadmapNode.id == activity.approach_node_id)
                        )
                    ).scalars().first()
                    if approach_node:
                        node_title, node_description = approach_node.title, approach_node.description
                        unit = approach_node.section

        try:
            items = await generate_question_items(
                topic=activity.topic,
                depth=depth,
                key_memory=activity.key_memory,
                node_title=node_title,
                node_description=node_description,
                unit=unit,
                mistake=activity.mistake,
                problem_context=problem_context,
            )
        except GraderError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Question generation unavailable: {e}",
            )
        qset = QuestionSet(
            user_id=user_id,
            activity_id=activity.id,
            depth=depth,
            items=[{"question": i.question, "reference_answer": i.reference_answer} for i in items],
        )
        db.add(qset)

    # Serving counts as a use; shuffle so the order never becomes the cue.
    qset.times_used += 1
    db.add(qset)
    await db.commit()

    shuffled = random.sample(list(qset.items), len(qset.items))
    return ReviewQuestionsResponse(questions=[i["question"] for i in shuffled], depth=depth)


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

    # Attach stored reference answers (never sent to the client) so grading judges
    # against the answer key written at generation time. Client-provided
    # reference_answer (lesson recall questions ship their own) takes priority.
    ref_by_question: dict[str, str] = {}
    recent_sets = (
        await db.execute(
            select(QuestionSet)
            .where(
                QuestionSet.activity_id == review.activity_id,
                QuestionSet.user_id == user_id,
            )
            .order_by(QuestionSet.created_at.desc())
            .limit(4)
        )
    ).scalars().all()
    for qs in reversed(recent_sets):  # newest last → newest wins on collisions
        for item in qs.items or []:
            q, ref = (item.get("question") or "").strip(), (item.get("reference_answer") or "").strip()
            if q and ref:
                ref_by_question[q] = ref

    try:
        graded = await grade_question_set(
            topic=review.activity.topic,
            key_memory=review.activity.key_memory,
            qa_pairs=[
                {
                    "question": qa.question,
                    "answer": qa.answer,
                    "reference_answer": qa.reference_answer or ref_by_question.get(qa.question.strip()),
                }
                for qa in body.answers
            ],
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
