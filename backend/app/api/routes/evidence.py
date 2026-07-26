import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.core.security import SupabaseUser
from app.models.models import Activity, LearningEvent, MetricEvent, NodeMastery, Roadmap, RoadmapNode
from app.schemas.evidence import (
    EvidenceEventOut,
    EvidenceSummaryOut,
    ManualEvidenceIn,
    NodeMasteryOut,
    NodeMasteryOut,
    RecomputeOut,
    LeetCodeSolveIn,
    LeetCodeBackfillIn
)
from app.models.models import Problem, ProblemConcept
from app.services import evidence
from app.services.metrics import record_metric_event
from app.services.evidence_weights import WEIGHTS_VERSION

router = APIRouter()


async def _assert_node_visible(db: AsyncSession, user_id: uuid.UUID, node_id: uuid.UUID) -> RoadmapNode:
    """A node is usable if its roadmap is the official catalog (user_id NULL)
    or a personal roadmap owned by this user — same visibility rule as
    GET /api/roadmaps/ (roadmaps._resolve_roadmap)."""
    row = (
        await db.execute(
            select(RoadmapNode, Roadmap.user_id.label("roadmap_owner_id"))
            .join(Roadmap, RoadmapNode.roadmap_id == Roadmap.id)
            .where(RoadmapNode.id == node_id)
        )
    ).first()
    if row is None or (row.roadmap_owner_id is not None and row.roadmap_owner_id != user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")
    return row.RoadmapNode


@router.post("/manual", status_code=status.HTTP_204_NO_CONTENT)
async def log_manual_evidence(
    body: ManualEvidenceIn,
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Producer B (SPEC-career-coach-phase1 §6.2) — TIME_BLOCK/T4_claimed,
    always w=0. Proves the schema is producer-agnostic and seeds Balance data
    for phase 2; moves no mastery on its own."""
    user_id = uuid.UUID(current_user.id)
    await _assert_node_visible(db, user_id, body.node_id)

    await evidence.record_event(
        db, user_id,
        event_type="TIME_BLOCK",
        trust_tier="T4_claimed",
        source="manual",
        node_id=body.node_id,
        duration_min=body.minutes,
        payload={"note": body.note} if body.note else {},
    )
    await db.commit()


@router.get("/nodes", response_model=List[NodeMasteryOut])
async def list_node_mastery(
    roadmap_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    user_id = uuid.UUID(current_user.id)
    now = datetime.utcnow()

    stmt = (
        select(NodeMastery, RoadmapNode.title)
        .join(RoadmapNode, NodeMastery.node_id == RoadmapNode.id)
        .where(NodeMastery.user_id == user_id)
    )
    if roadmap_id is not None:
        stmt = stmt.where(RoadmapNode.roadmap_id == roadmap_id)
    rows = (await db.execute(stmt)).all()
    if not rows:
        return []

    node_ids = [row.NodeMastery.node_id for row in rows]
    activities_by_node = {
        a.node_id: a
        for a in (
            await db.execute(
                select(Activity).where(Activity.user_id == user_id, Activity.node_id.in_(node_ids))
            )
        ).scalars().all()
    }

    out = []
    for row in rows:
        nm = row.NodeMastery
        events = (
            await db.execute(
                select(LearningEvent).where(
                    LearningEvent.user_id == user_id,
                    LearningEvent.node_id == nm.node_id,
                    LearningEvent.deleted_at.is_(None),
                )
            )
        ).scalars().all()
        has_unassisted_pass = any(
            e.outcome == "pass" and e.assistance == "none" and e.trust_tier in ("T1_verified_external", "T2_verified_internal")
            for e in events
        )
        distinct_tiers = len({e.trust_tier for e in events})

        r = evidence.retrievability_for(activities_by_node.get(nm.node_id), now)
        m = evidence.displayed_mastery(nm.m_learned, r)
        out.append(NodeMasteryOut(
            node_id=nm.node_id,
            title=row.title,
            m_learned=nm.m_learned,
            r=r,
            m=m,
            state=evidence.node_state(m, has_unassisted_pass),
            confidence=evidence.confidence(nm.evidence_count, nm.last_event_at, distinct_tiers, now),
            evidence_count=nm.evidence_count,
            last_event_at=nm.last_event_at,
        ))
    return out


@router.get("/nodes/{node_id}/events", response_model=List[EvidenceEventOut])
async def get_node_events(
    node_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """The "why is this number what it is" surface (spec §7/§13): every event
    for this node with its own weight and the running mastery right after it."""
    user_id = uuid.UUID(current_user.id)
    await _assert_node_visible(db, user_id, node_id)

    events = (
        await db.execute(
            select(LearningEvent).where(LearningEvent.user_id == user_id, LearningEvent.node_id == node_id)
        )
    ).scalars().all()

    return [
        EvidenceEventOut(
            id=event.id,
            occurred_at=event.occurred_at,
            event_type=event.event_type,
            trust_tier=event.trust_tier,
            source=event.source,
            outcome=event.outcome,
            difficulty=event.difficulty,
            assistance=event.assistance,
            grade=event.grade,
            duration_min=event.duration_min,
            weight=weight,
            m_learned_after=m_learned_after,
            deleted_at=event.deleted_at,
        )
        for event, weight, m_learned_after in evidence.fold_events_trace(events)
    ]


@router.get("/summary", response_model=EvidenceSummaryOut)
async def get_evidence_summary(
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    user_id = uuid.UUID(current_user.id)

    live_events_stmt = select(LearningEvent).where(
        LearningEvent.user_id == user_id, LearningEvent.deleted_at.is_(None)
    )
    live_events = (await db.execute(live_events_stmt)).scalars().all()

    by_tier: dict[str, int] = {}
    by_type: dict[str, int] = {}
    for e in live_events:
        by_tier[e.trust_tier] = by_tier.get(e.trust_tier, 0) + 1
        by_type[e.event_type] = by_type.get(e.event_type, 0) + 1

    unmapped_events = (
        await db.execute(
            select(func.count()).select_from(MetricEvent).where(
                MetricEvent.user_id == user_id, MetricEvent.event_type == "evidence_unmapped"
            )
        )
    ).scalar_one()

    nodes_with_evidence = (
        await db.execute(
            select(func.count()).select_from(NodeMastery).where(
                NodeMastery.user_id == user_id, NodeMastery.evidence_count > 0
            )
        )
    ).scalar_one()

    return EvidenceSummaryOut(
        total_events=len(live_events),
        by_tier=by_tier,
        by_type=by_type,
        unmapped_events=unmapped_events,
        nodes_with_evidence=nodes_with_evidence,
        weights_version=WEIGHTS_VERSION,
    )


@router.post("/recompute", response_model=RecomputeOut)
async def recompute_all(
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Full replay for the calling user. Idempotent."""
    user_id = uuid.UUID(current_user.id)
    nodes_recomputed = await evidence.recompute_user(db, user_id)
    await db.commit()
    return RecomputeOut(nodes_recomputed=nodes_recomputed)


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Soft-delete (design doc §14) + recompute the affected node."""
    user_id = uuid.UUID(current_user.id)
    event = (
        await db.execute(
            select(LearningEvent).where(LearningEvent.id == event_id, LearningEvent.user_id == user_id)
        )
    ).scalars().first()
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    event.deleted_at = datetime.utcnow()
    db.add(event)
    if event.node_id is not None:
        await evidence.recompute_node(db, user_id, event.node_id)
    await db.commit()


@router.post("/leetcode/solve", status_code=status.HTTP_204_NO_CONTENT)
async def log_leetcode_solve(
    body: LeetCodeSolveIn,
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Producer C (LeetCode Extension) — EXTERNAL_SOLVE/T1_verified_external."""
    user_id = uuid.UUID(current_user.id)
    
    # 1. Lookup problem
    stmt = select(Problem).where(Problem.slug == body.problem_slug)
    problem = (await db.execute(stmt)).scalars().first()
    if not problem:
        # We don't have this problem in our catalog, log as unmapped
        await record_metric_event(
            db, user_id,
            event_type="evidence_unmapped",
            payload={"problem_slug": body.problem_slug, "duration_min": body.duration_min, "source": "leetcode"}
        )
        await db.commit()
        return

    # 2. Lookup primary concept mapping
    stmt = select(ProblemConcept).where(ProblemConcept.problem_id == problem.id, ProblemConcept.role == "primary")
    pc = (await db.execute(stmt)).scalars().first()
    
    if not pc:
        # Problem exists but has no primary mapping
        await record_metric_event(
            db, user_id,
            event_type="evidence_unmapped",
            payload={"problem_slug": body.problem_slug, "problem_id": str(problem.id), "duration_min": body.duration_min, "source": "leetcode"}
        )
        await db.commit()
        return
        
    # 3. Log the event
    occurred_at = body.occurred_at or datetime.utcnow()
    # Normalize naive-UTC
    if occurred_at.tzinfo is not None:
        from datetime import timezone
        occurred_at = occurred_at.astimezone(timezone.utc).replace(tzinfo=None)
        
    # Difficulty comes from OUR catalog, never from the client - the extension cannot be
    # trusted to report it and the weight table is keyed on (difficulty, assistance).
    difficulty = problem.difficulty

    # Assistance is derived from the reflection. When the user skipped it we must NOT
    # assume a clean solve: `assistance="none"` is the most generous row in the weight
    # table (0.25-0.35), so defaulting to it silently inflates every unreflected solve.
    # Fall back to evidence_weights._DEFAULT_ASSISTANCE ("llm_assisted", 0.06) instead -
    # understate, never overstate (Design law, ARCHITECTURE-learning-system.md §0).
    if body.needed_hint is True:
        assistance = "hint"
    elif body.needed_hint is False:
        assistance = "none"
    else:
        assistance = "llm_assisted"

    await evidence.record_event(
        db, user_id,
        event_type="PROBLEM_SOLVED",
        trust_tier="T1_verified_external",
        source="leetcode",
        node_id=pc.node_id,
        duration_min=body.duration_min,
        difficulty=difficulty,
        outcome="pass",
        assistance=assistance,
        entity_id=problem.id, # idempotency key: one logged solve per problem
        occurred_at=occurred_at,
        payload={
            "problem_slug": body.problem_slug,
            "submission_id": body.submission_id,
            "confidence": body.confidence,
            "needed_hint": body.needed_hint,
            "mistake": body.mistake,
            "reflected": body.needed_hint is not None or body.confidence is not None,
        },
    )
    await db.commit()


@router.post("/leetcode/backfill", status_code=status.HTTP_204_NO_CONTENT)
async def log_leetcode_backfill(
    body: LeetCodeBackfillIn,
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Bulk import of historic solves from the LeetCode extension."""
    user_id = uuid.UUID(current_user.id)
    
    if not body.solved_slugs:
        return
        
    # Difficulty comes from OUR catalog for the same reason it does in /solve:
    # the weight table is keyed on (difficulty, assistance), and omitting it
    # silently folds every backfilled solve at _DEFAULT_DIFFICULTY.
    stmt = select(Problem.id, Problem.slug, Problem.difficulty).where(Problem.slug.in_(body.solved_slugs))
    problems = (await db.execute(stmt)).all()
    problem_ids = [p.id for p in problems]
    slug_map = {p.id: p.slug for p in problems}
    difficulty_map = {p.id: p.difficulty for p in problems}
    
    if not problem_ids:
        return
        
    # Find all primary concepts for these problems
    stmt = select(ProblemConcept.problem_id, ProblemConcept.node_id).where(
        ProblemConcept.problem_id.in_(problem_ids), 
        ProblemConcept.role == "primary"
    )
    mappings = (await db.execute(stmt)).all()
    
    now = datetime.utcnow()
    for mapping in mappings:
        problem_slug = slug_map[mapping.problem_id]
        
        await evidence.record_event(
            db, user_id,
            event_type="PROBLEM_SOLVED",
            trust_tier="T1_verified_external",
            source="leetcode",
            node_id=mapping.node_id,
            outcome="pass",
            difficulty=difficulty_map[mapping.problem_id],
            # NOT "none". A historic solve carries even less information than a
            # live unreflected one — we have no idea whether it was hint-free —
            # and "none" is the most generous row in the weight table, so it
            # would inflate mastery for every problem the user ever touched at
            # import time. Same understate-never-overstate default /solve uses
            # (evidence_weights._DEFAULT_ASSISTANCE).
            assistance="llm_assisted",
            entity_id=mapping.problem_id,
            occurred_at=now,
            payload={"problem_slug": problem_slug, "backfilled": True}
        )
        
    await db.commit()
