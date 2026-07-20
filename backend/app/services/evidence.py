"""Career Coach evidence engine (SPEC-career-coach-phase1 §5). `fold_events`
is pure and DB-free — it's the correctness oracle that the DB-backed
`record_event`/`recompute_node` (step 4 of the build order) must agree with
exactly (Design law 2: mastery is a derived cache, always rebuildable from
`learning_events` alone).
"""
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import LearningEvent, NodeMastery
from app.services.evidence_weights import WEIGHTS_VERSION, apply_event_weight, is_capped, w
from app.services.scheduler import _retrievability


@dataclass
class NodeMasteryResult:
    m_learned: float = 0.0
    evidence_count: int = 0
    last_event_at: Optional[datetime] = None
    exposure_capped: bool = False


def recall_grade(recalled: Optional[bool], rating: str, quality: Optional[int]) -> Optional[float]:
    """RECALL_GRADED grade (§6.1) — the objective `recalled` signal wins when
    present; `quality` (always populated by quality_from_outcome, itself
    falling back to the felt `rating`) is the fallback for older clients that
    never sent `recalled`. Shared by Producer A (routes/reviews.py) and the
    phase-2 topic-mapping backfill (services/topic_mapping.py) — one grade
    rule, not two copies that can drift."""
    if recalled is False:
        return 0.0
    if recalled is True:
        return {"easy": 1.0, "medium": 0.8, "hard": 0.6}[rating]
    if quality is not None:
        return quality / 5.0
    return None


def fold_events(events: list) -> NodeMasteryResult:
    """Replay events in occurred_at order -> mastery state. Pure: same input,
    same output, no I/O. This is the ONLY place m_learned is produced.

    Tracked as two independent running totals — one folding only uncapped
    (T1/T2) evidence, one folding only capped (T3 / CONTENT_CONSUMED)
    evidence with the §4.2 ceiling — combined by `max()` at the end. A single
    shared running total would make the fold's result depend on *when* a
    capped event happens to land relative to the uncapped evidence (its small
    early contribution survives if folded before the uncapped push, but is
    clamped away if folded after) — order-dependence the design doc doesn't
    intend. Two independent streams make the fold a true commutative replay:
    same set of events, any order, same result.
    """
    live_events = [e for e in events if getattr(e, "deleted_at", None) is None]
    ordered = sorted(live_events, key=lambda e: (e.occurred_at, e.id))

    m_uncapped = 0.0
    m_capped = 0.0
    evidence_count = 0
    uncapped_evidence_count = 0
    capped_evidence_count = 0
    last_event_at = None

    for event in ordered:
        last_event_at = event.occurred_at if last_event_at is None else max(last_event_at, event.occurred_at)
        weight = w(event)
        if weight == 0.0:
            continue
        evidence_count += 1
        if is_capped(event):
            capped_evidence_count += 1
            m_capped = apply_event_weight(m_capped, weight, capped=True)
        else:
            uncapped_evidence_count += 1
            m_uncapped = apply_event_weight(m_uncapped, weight, capped=False)

    return NodeMasteryResult(
        m_learned=max(m_uncapped, m_capped),
        evidence_count=evidence_count,
        last_event_at=last_event_at,
        exposure_capped=capped_evidence_count > 0 and uncapped_evidence_count == 0,
    )


def fold_events_trace(events: list) -> list[tuple]:
    """Same replay as fold_events, but returns each event alongside its own
    weight and the running composite m_learned right after it — the "why is
    this number what it is" trace (spec §7, GET /nodes/{id}/events). Mirrors
    fold_events's algorithm; kept separate since the two return shapes
    (aggregate vs. per-step trace) don't share enough to be worth unifying.
    Soft-deleted events are included (weight 0, m_learned unchanged) so the
    drill-down shows full history, not just what still counts.
    """
    ordered = sorted(events, key=lambda e: (e.occurred_at, e.id))
    m_uncapped = 0.0
    m_capped = 0.0
    trace = []
    for event in ordered:
        if getattr(event, "deleted_at", None) is not None:
            trace.append((event, 0.0, max(m_uncapped, m_capped)))
            continue
        weight = w(event)
        if weight != 0.0:
            if is_capped(event):
                m_capped = apply_event_weight(m_capped, weight, capped=True)
            else:
                m_uncapped = apply_event_weight(m_uncapped, weight, capped=False)
        trace.append((event, weight, max(m_uncapped, m_capped)))
    return trace


# --- DB layer ---------------------------------------------------------------
# Never commits (rides the caller's transaction, same convention as
# services/metrics.py) — a bug here must not be able to half-commit unrelated
# state, and callers don't pay an extra round-trip.

async def record_event(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    event_type: str,
    trust_tier: str,
    source: str,
    node_id: Optional[uuid.UUID] = None,
    duration_min: int = 0,
    difficulty: Optional[str] = None,
    assistance: Optional[str] = None,
    outcome: Optional[str] = None,
    grade: Optional[float] = None,
    entity_id: Optional[uuid.UUID] = None,
    payload: Optional[dict] = None,
    occurred_at: Optional[datetime] = None,
) -> Optional[LearningEvent]:
    """Insert one immutable learning_events row, then refold the affected
    node's mastery. Returns None when the insert was deduped by
    uq_learning_event_dedupe (a polling producer re-reading a source row it
    already wrote) — nothing changed, so there's nothing to refold.

    The dedupe check is a SAVEPOINT (`db.begin_nested()`), not a pre-query:
    a duplicate is an expected, common case (not a bug), and without a
    savepoint the IntegrityError would poison the caller's whole transaction
    in Postgres (an aborted transaction rejects further commands until
    ROLLBACK) — exactly the failure Producer A's isolation (§6.1) can't
    tolerate.

    "Refold" replays that ONE node's full history via recompute_node rather
    than hand-updating m_learned in place. The two-tier fold (fold_events)
    needs the capped/uncapped split to combine correctly, and node_mastery's
    schema (spec §2.2) deliberately has no column for that split — so a
    true O(1) incremental update isn't possible without adding state the
    spec doesn't define. Replaying one node's (small, bounded) history costs
    nothing at this scale and is *exactly* recompute_node by construction,
    which is what test 12 / Design law 2 actually require.
    """
    kwargs = dict(
        user_id=user_id, event_type=event_type, trust_tier=trust_tier, source=source,
        node_id=node_id, duration_min=duration_min, difficulty=difficulty, assistance=assistance,
        outcome=outcome, grade=grade, entity_id=entity_id, payload=payload or {},
    )
    if occurred_at is not None:
        kwargs["occurred_at"] = occurred_at
    event = LearningEvent(**kwargs)

    try:
        async with db.begin_nested():
            db.add(event)
            await db.flush()
    except IntegrityError:
        return None

    if node_id is not None:
        await recompute_node(db, user_id, node_id)

    return event


async def recompute_node(db: AsyncSession, user_id: uuid.UUID, node_id: uuid.UUID) -> NodeMastery:
    """Full replay from learning_events. The correctness oracle."""
    events = (
        await db.execute(
            select(LearningEvent).where(
                LearningEvent.user_id == user_id,
                LearningEvent.node_id == node_id,
            )
        )
    ).scalars().all()
    folded = fold_events(events)

    node_mastery = (
        await db.execute(
            select(NodeMastery).where(NodeMastery.user_id == user_id, NodeMastery.node_id == node_id)
        )
    ).scalar_one_or_none()
    if node_mastery is None:
        node_mastery = NodeMastery(user_id=user_id, node_id=node_id, weights_version=WEIGHTS_VERSION)
        db.add(node_mastery)

    node_mastery.m_learned = folded.m_learned
    node_mastery.evidence_count = folded.evidence_count
    node_mastery.last_event_at = folded.last_event_at
    node_mastery.exposure_capped = folded.exposure_capped
    node_mastery.weights_version = WEIGHTS_VERSION
    node_mastery.updated_at = datetime.utcnow()

    await db.flush()
    return node_mastery


async def recompute_user(db: AsyncSession, user_id: uuid.UUID) -> int:
    """Full replay for every node with events. Returns node count. Idempotent."""
    node_ids = (
        await db.execute(
            select(LearningEvent.node_id)
            .where(LearningEvent.user_id == user_id, LearningEvent.node_id.is_not(None))
            .distinct()
        )
    ).scalars().all()
    for node_id in node_ids:
        await recompute_node(db, user_id, node_id)
    return len(node_ids)


# --- Read-side derivations (§5.1) ------------------------------------------

def retrievability_for(activity: Any, now: datetime) -> float:
    """Wraps scheduler._retrievability; 1.0 (no decay yet) if never reviewed."""
    if activity is None or activity.stability is None or activity.last_reviewed_at is None:
        return 1.0
    elapsed_days = max((now - activity.last_reviewed_at).total_seconds() / 86400, 0.0)
    return _retrievability(elapsed_days, activity.stability)


def displayed_mastery(m_learned: float, r: float) -> float:
    return m_learned * r


# Node state thresholds — named constants so tuning is a config edit, not a
# code change (parent doc leaves these open to calibration against real data).
EXPOSED_MIN = 0.0
PRACTICING_MIN = 0.35
SOLID_MIN = 0.65
INTERVIEW_READY_MIN = 0.85


def node_state(m: float, has_unassisted_pass: bool) -> str:
    """unexposed -> exposed -> practicing -> solid -> interview_ready.
    interview_ready additionally requires >=1 unassisted T1/T2 pass — a node
    can sit at m=0.9 on llm_assisted evidence alone and still only read
    `solid` (spec §5.1, deliberate; don't drop this gate for tidiness)."""
    if m <= EXPOSED_MIN:
        return "unexposed"
    if m < PRACTICING_MIN:
        return "exposed"
    if m < SOLID_MIN:
        return "practicing"
    if m < INTERVIEW_READY_MIN:
        return "solid"
    return "interview_ready" if has_unassisted_pass else "solid"


# Confidence thresholds (§5.1) — an open question in the parent doc (§16);
# named constants here so tuning stays a config edit.
CONFIDENCE_HIGH_MIN_EVENTS = 5
CONFIDENCE_HIGH_MAX_AGE_DAYS = 14
CONFIDENCE_HIGH_MIN_TIERS = 2
CONFIDENCE_MEDIUM_MIN_EVENTS = 2
CONFIDENCE_MEDIUM_MAX_AGE_DAYS = 30


def confidence(evidence_count: int, last_event_at: Optional[datetime], distinct_tiers: int, now: datetime) -> str:
    if evidence_count <= 0 or last_event_at is None:
        return "low"
    age_days = (now - last_event_at).total_seconds() / 86400
    if (
        evidence_count >= CONFIDENCE_HIGH_MIN_EVENTS
        and age_days <= CONFIDENCE_HIGH_MAX_AGE_DAYS
        and distinct_tiers >= CONFIDENCE_HIGH_MIN_TIERS
    ):
        return "high"
    if evidence_count >= CONFIDENCE_MEDIUM_MIN_EVENTS and age_days <= CONFIDENCE_MEDIUM_MAX_AGE_DAYS:
        return "medium"
    return "low"
