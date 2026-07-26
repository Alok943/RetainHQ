"""Career Coach Phase 2 — Goal, Tree & Topic Mapping (SPEC-career-coach-phase2.md).

Tree generation follows syllabus.py's two-step shape: /tree/generate is a
PROPOSAL — nothing is saved — and a separate /tree/commit (added alongside
the commit-transaction work) persists the user-edited draft.
"""
import asyncio
import logging
import uuid
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, get_current_user
from app.core.config import settings
from app.core.security import SupabaseUser
from app.models.models import (
    Activity, CareerGoal, CareerGoalRoadmap, LearningEvent, MetricEvent, NodeMastery,
    NodeMeta, Review, Roadmap, RoadmapNode, RoadmapNodePrerequisite, UserPref,
)
from app.schemas.career import (
    AssignNodeIn,
    AssignNodeOut,
    AttachedRoadmapOut,
    AttachRoadmapIn,
    AvailableRoadmapOut,
    AvailableRoadmapsOut,
    CareerGoalIn,
    CareerGoalOut,
    CareerTemplateOut,
    DiagnosticAnswerIn,
    DiagnosticProbeOut,
    DiagnosticResultOut,
    GoalPatchIn,
    NodeOut,
    NodePatchIn,
    PlanItemOut,
    SprintIn,
    SuggestedNodeOut,
    TodayFeedbackIn,
    TodayPlanOut,
    TreeCommitIn,
    TreeGenerateIn,
    UnmappedActivityOut,
)
from app.services import evidence, metrics, planner, topic_mapping, embeddings
from app.services.career_tree import CareerTreeDraft, CareerTreeError, _load_template, generate_career_tree, list_templates
from app.services.grader import GraderError, grade_recall
from app.services.scheduler import REVIEW_SESSION_CAP

router = APIRouter()
logger = logging.getLogger(__name__)

# 5-8 items (§4) — the template SHOULD have >=5 probe-bearing nodes (the
# validator warns otherwise); this is just the display ceiling.
DIAGNOSTIC_PROBE_COUNT = 8

# Per-user daily generation counter — same in-memory-is-fine-for-single-instance
# reasoning as routes/syllabus.py's _check_and_bump_daily_limit. An API-budget
# guard, not a security boundary; resets on redeploy (only ever relaxes it).
_generate_counts: dict[str, tuple[date, int]] = {}


def _check_and_bump_daily_limit(user_id: str) -> None:
    today = datetime.utcnow().date()
    day, count = _generate_counts.get(user_id, (today, 0))
    if day != today:
        count = 0
    if count >= settings.CAREER_TREE_DAILY_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily limit of {settings.CAREER_TREE_DAILY_LIMIT} tree generations reached — try again tomorrow.",
        )
    _generate_counts[user_id] = (today, count + 1)


@router.get("/templates", response_model=list[CareerTemplateOut])
async def get_templates():
    return list_templates()


@router.post("/tree/generate", response_model=CareerTreeDraft)
async def generate_tree(
    body: TreeGenerateIn,
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Draft tree — proposal only, writes nothing (§3.3/§6). Rate-limited to
    CAREER_TREE_DAILY_LIMIT/user/day; regeneration during onboarding is
    expected (users try a goal, dislike the tree, retry)."""
    _check_and_bump_daily_limit(current_user.id)

    try:
        return await generate_career_tree(
            role_key=body.role_key,
            goal_title=body.goal_title,
            target_date=body.target_date,
            diagnostic_results=body.diagnostic_results,
            free_text=body.free_text,
        )
    except CareerTreeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/goals/", response_model=CareerGoalOut, status_code=status.HTTP_201_CREATED)
async def create_goal(
    body: CareerGoalIn,
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Create a goal, archiving any existing active one (parent A1: one active
    goal per user). The DB's partial unique index (career_goals, WHERE
    status='active') is the real backstop — this UPDATE-then-INSERT is just
    what makes the common case not 409."""
    user_id = uuid.UUID(current_user.id)
    await db.execute(
        update(CareerGoal)
        .where(CareerGoal.user_id == user_id, CareerGoal.status == "active")
        .values(status="archived", updated_at=datetime.utcnow())
    )
    goal = CareerGoal(user_id=user_id, role_key=body.role_key, title=body.title, target_date=body.target_date)
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    return goal


@router.get("/goals/active", response_model=CareerGoalOut)
async def get_active_goal(
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    user_id = uuid.UUID(current_user.id)
    goal = (
        await db.execute(select(CareerGoal).where(CareerGoal.user_id == user_id, CareerGoal.status == "active"))
    ).scalar_one_or_none()
    if goal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active goal")
    return goal


def _select_diagnostic_probes(template: dict, count: int = DIAGNOSTIC_PROBE_COUNT) -> list[dict]:
    """Subject-aware round-robin probe selection (SPEC-career-templates-v2 §2).

    A flat priority sort is subject-blind: Python's stable sort breaks priority
    ties by file order, so a template whose early subjects are foundational
    (math, classical ML) fills every slot before a later subject (RAG, agents)
    gets one — the AI Engineer diagnostic asked zero AI questions. Round-robin
    across subjects in template order, best-probe-first within each subject,
    guarantees spread by construction. Deterministic: no randomness, so repeat
    calls (and the retake-after-refresh case) serve the same set."""
    per_subject: list[list[dict]] = []
    for subject in template.get("subjects", []):
        probes = [
            n for n in subject.get("nodes", [])
            if n.get("diagnostic_probe") and n.get("diagnostic_answer")
        ]
        probes.sort(key=lambda n: -n["priority"])  # stable → template order within a priority
        if probes:
            per_subject.append(probes)

    selected: list[dict] = []
    round_index = 0
    while len(selected) < count and any(round_index < len(p) for p in per_subject):
        for probes in per_subject:
            if round_index < len(probes) and len(selected) < count:
                selected.append(probes[round_index])
        round_index += 1
    return selected


@router.get("/diagnostic", response_model=list[DiagnosticProbeOut])
async def get_diagnostic(
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """5-8 probes drawn from the active goal's template — not generated fresh
    (§4: probes are authored content, reviewable and stable). Selection is
    round-robin across subjects — see _select_diagnostic_probes."""
    user_id = uuid.UUID(current_user.id)
    goal = (
        await db.execute(select(CareerGoal).where(CareerGoal.user_id == user_id, CareerGoal.status == "active"))
    ).scalar_one_or_none()
    if goal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active goal — create one first.")

    template = _load_template(goal.role_key)
    selected = _select_diagnostic_probes(template)
    return [
        DiagnosticProbeOut(stable_key=n["stable_key"], node_title=n["title"], probe=n["diagnostic_probe"])
        for n in selected
    ]


@router.post("/diagnostic/submit", response_model=list[DiagnosticResultOut])
async def submit_diagnostic(
    body: list[DiagnosticAnswerIn],
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Grade diagnostic answers with the existing recall grader — no new
    grading path (§4). Nothing is written to learning_events here: results
    are returned for the client to hold and thread into /tree/commit, which
    is the only place a diagnostic ever produces evidence (nodes must exist
    first)."""
    if not settings.GRADER_ENABLED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grader is disabled")

    user_id = uuid.UUID(current_user.id)
    goal = (
        await db.execute(select(CareerGoal).where(CareerGoal.user_id == user_id, CareerGoal.status == "active"))
    ).scalar_one_or_none()
    if goal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active goal — create one first.")

    template = _load_template(goal.role_key)
    nodes_by_key = {n["stable_key"]: n for s in template.get("subjects", []) for n in s.get("nodes", [])}

    results = []
    for answer in body:
        node = nodes_by_key.get(answer.stable_key)
        if node is None or not node.get("diagnostic_answer"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown probe '{answer.stable_key}'")

        try:
            verdict = await grade_recall(topic=node["title"], key_memory=node["diagnostic_answer"], user_answer=answer.answer)
        except GraderError as e:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

        grade = {"correct": 1.0, "partial": 0.5, "incorrect": 0.0}[verdict.verdict]
        results.append(DiagnosticResultOut(
            stable_key=answer.stable_key, verdict=verdict.verdict, recalled=verdict.recalled,
            grade=grade, feedback=verdict.feedback,
        ))
    return results


@router.post("/tree/commit", response_model=CareerGoalOut, status_code=status.HTTP_201_CREATED)
async def commit_tree(
    body: TreeCommitIn,
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Draft -> Roadmap + RoadmapNode + NodeMeta + prerequisite rows, pinning
    template_version on the caller's active goal. Single transaction (§6):
    every SQLModel id is generated client-side (default_factory=uuid.uuid4),
    so the whole tree is built in memory and staged with one add_all() before
    the one commit() — a half-written tree with orphaned prerequisite rows
    would be worse than a failed commit."""
    user_id = uuid.UUID(current_user.id)

    goal = (
        await db.execute(select(CareerGoal).where(CareerGoal.user_id == user_id, CareerGoal.status == "active"))
    ).scalar_one_or_none()
    if goal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active goal — create one first.")

    all_nodes = [n for s in body.subjects for n in s.nodes]
    if not all_nodes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The tree has no nodes.")

    audience = (
        await db.execute(select(UserPref.audience).where(UserPref.user_id == user_id))
    ).scalar_one_or_none() or "career"

    roadmap = Roadmap(title=body.title.strip() or body.role_key, audience=audience, user_id=user_id)

    stable_key_to_node_id: dict[str, uuid.UUID] = {}
    roadmap_nodes: list[RoadmapNode] = []
    node_metas: list[NodeMeta] = []
    order = 0
    
    # Pre-compute embeddings for all nodes
    flat_nodes_text = []
    for subject in body.subjects:
        for node in subject.nodes:
            # We embed title only since template/draft nodes have no description field.
            flat_nodes_text.append(node.title)
    
    node_embeddings = []
    if flat_nodes_text:
        try:
            # embed_batch is a synchronous SDK call, self-bounded to
            # embeddings._EMBED_TIMEOUT_SEC — run it off the event loop so a
            # slow/unreachable Gemini endpoint can't stall every other
            # request this worker is handling while it waits out that bound.
            node_embeddings = await asyncio.to_thread(embeddings.embed_batch, flat_nodes_text)
        except Exception:
            # If embedding fails (no key, rate limit, timeout, etc), fall back to empty to not break commit
            logger.warning("Tree-commit embedding pre-compute failed; committing with empty embeddings", exc_info=True)
            node_embeddings = [[] for _ in flat_nodes_text]
            
    flat_index = 0
    for subject in body.subjects:
        for node in subject.nodes:
            rn = RoadmapNode(
                roadmap_id=roadmap.id,
                phase=subject.title,
                section=subject.title,
                title=node.title,
                order_index=order,
            )
            stable_key_to_node_id[node.stable_key] = rn.id
            roadmap_nodes.append(rn)
            node_metas.append(NodeMeta(
                node_id=rn.id,
                stable_key=node.stable_key,
                priority=node.priority,
                est_effort_min=node.est_effort_min,
                subject=subject.key,
                embedding=node_embeddings[flat_index] if flat_index < len(node_embeddings) else []
            ))
            order += 1
            flat_index += 1

    prerequisites: list[RoadmapNodePrerequisite] = []
    for subject in body.subjects:
        for node in subject.nodes:
            node_id = stable_key_to_node_id[node.stable_key]
            for dep_key in node.depends_on:
                prereq_id = stable_key_to_node_id.get(dep_key)
                if prereq_id is not None:
                    prerequisites.append(RoadmapNodePrerequisite(node_id=node_id, prerequisite_node_id=prereq_id))

    # Staged flushes, not one add_all()-then-flush: none of these mapped
    # classes have an ORM relationship() to each other (they're linked only by
    # bare FK columns), so the unit-of-work has no dependency edge telling it
    # roadmap must precede roadmap_nodes, which must precede node_meta/
    # prerequisites/the goal update. Without explicit boundaries, asyncpg's
    # executemany batching can send a child table's INSERT (or the goal's
    # UPDATE) before its parent row exists and hit a FK violation. Still one
    # transaction — no commit() until the very end — so still atomic.
    db.add(roadmap)
    await db.flush()

    db.add_all(roadmap_nodes)
    await db.flush()

    db.add_all(node_metas)
    db.add_all(prerequisites)
    goal.roadmap_id = roadmap.id
    goal.template_version = body.template_version
    goal.updated_at = datetime.utcnow()
    db.add(goal)

    # Flush the goal update BEFORE any diagnostic replay: record_event's
    # dedupe savepoint (§6.1-style isolation) rolls back everything flushed
    # since it began if the LearningEvent insert collides — that must never
    # take the freshly-built tree down with it.
    await db.flush()

    # Diagnostic replay (§4): each graded probe becomes an ordinary
    # RECALL_GRADED/T2_verified_internal learning_event, written only now that
    # the nodes it targets actually exist. entity_id is derived, not
    # client-supplied, so resubmitting the same goal's diagnostic can't
    # double-count.
    for result in body.diagnostic_results or []:
        node_id = stable_key_to_node_id.get(result.stable_key)
        if node_id is None:
            continue  # user deleted this node from the draft before committing
        await evidence.record_event(
            db, user_id,
            event_type="RECALL_GRADED",
            trust_tier="T2_verified_internal",
            source="retainhq_coach",
            node_id=node_id,
            grade=result.grade,
            outcome="pass" if result.recalled else "fail",
            entity_id=uuid.uuid5(goal.id, result.stable_key),
        )

    await db.commit()
    await db.refresh(goal)
    return goal


@router.get("/unmapped", response_model=list[UnmappedActivityOut])
async def get_unmapped(
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Tier 3 triage bucket (§5): activities Producer A skipped for lacking a
    node_id, still unmapped, with a Tier-2 suggestion where the user's active
    tree has one. Read-only — assigning is a separate explicit action."""
    user_id = uuid.UUID(current_user.id)

    unmapped_events = (
        await db.execute(
            select(MetricEvent).where(MetricEvent.user_id == user_id, MetricEvent.event_type == "evidence_unmapped")
        )
    ).scalars().all()

    skip_counts: dict[uuid.UUID, int] = {}
    for e in unmapped_events:
        raw_id = (e.payload or {}).get("activity_id")
        if not raw_id:
            continue
        aid = uuid.UUID(raw_id)
        skip_counts[aid] = skip_counts.get(aid, 0) + 1

    if not skip_counts:
        return []

    # Only activities STILL unmapped — assigning a node (which sets
    # Activity.node_id) makes it disappear from here on its own; no separate
    # "resolved" flag needed on metric_events.
    activities = (
        await db.execute(
            select(Activity).where(
                Activity.id.in_(skip_counts.keys()), Activity.user_id == user_id, Activity.node_id.is_(None),
            )
        )
    ).scalars().all()

    candidates = await topic_mapping.candidate_nodes_for_active_goal(db, user_id)

    out = []
    for activity in activities:
        suggestion = topic_mapping.suggest_node(activity.topic, candidates) if candidates else None
        out.append(UnmappedActivityOut(
            activity_id=activity.id,
            topic=activity.topic,
            skipped_count=skip_counts.get(activity.id, 0),
            suggested_node=SuggestedNodeOut(**suggestion) if suggestion else None,
        ))
    return out


@router.post("/unmapped/{activity_id}/assign", response_model=AssignNodeOut)
async def assign_unmapped_activity(
    activity_id: uuid.UUID,
    body: AssignNodeIn,
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Assign a node to a previously-unmapped activity: sets Activity.node_id
    and retroactively writes the RECALL_GRADED events Producer A skipped for
    every one of its completed reviews, then recomputes that node's mastery."""
    user_id = uuid.UUID(current_user.id)

    # Ownership on the TARGET node too — IDOR guard per CLAUDE.md.
    node = (
        await db.execute(
            select(RoadmapNode)
            .join(Roadmap, Roadmap.id == RoadmapNode.roadmap_id)
            .where(RoadmapNode.id == body.node_id, Roadmap.user_id == user_id)
        )
    ).scalar_one_or_none()
    if node is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")

    try:
        written = await topic_mapping.backfill_activity(db, user_id, activity_id, body.node_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    await db.commit()
    return AssignNodeOut(activity_id=activity_id, node_id=body.node_id, events_written=written)


async def _get_owned_node_and_meta(db: AsyncSession, user_id: uuid.UUID, node_id: uuid.UUID):
    node = (
        await db.execute(
            select(RoadmapNode).join(Roadmap, Roadmap.id == RoadmapNode.roadmap_id)
            .where(RoadmapNode.id == node_id, Roadmap.user_id == user_id)
        )
    ).scalar_one_or_none()
    if node is None:
        return None, None
    meta = (await db.execute(select(NodeMeta).where(NodeMeta.node_id == node_id))).scalar_one_or_none()
    return node, meta


@router.patch("/nodes/{node_id}", response_model=NodeOut)
async def patch_node(
    node_id: uuid.UUID,
    body: NodePatchIn,
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Edit title/priority/effort — sets user_edited=true so a future template
    version upgrade doesn't silently clobber the user's own correction."""
    user_id = uuid.UUID(current_user.id)
    node, meta = await _get_owned_node_and_meta(db, user_id, node_id)
    if node is None or meta is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")

    if body.title is not None:
        node.title = body.title.strip()
        db.add(node)
    if body.priority is not None:
        meta.priority = body.priority
    if body.est_effort_min is not None:
        meta.est_effort_min = body.est_effort_min
    meta.user_edited = True
    db.add(meta)

    await db.commit()
    await db.refresh(node)
    await db.refresh(meta)
    return NodeOut(
        node_id=node.id, stable_key=meta.stable_key, title=node.title,
        priority=meta.priority, est_effort_min=meta.est_effort_min, user_edited=meta.user_edited,
    )


@router.delete("/nodes/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_node(
    node_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Remove a node from the tree. Evidence SURVIVES (§7) — this is a soft
    detach, not a cascade: learning_events.node_id gets nulled (with a
    payload marker) and any activities pointing here move to the unmapped
    bucket, rather than the immutable event log being silently destroyed.
    Design law 2 (phase 1) outranks referential tidiness here.

    learning_events.node_id carries no ondelete=CASCADE (confirmed at
    migration b6f2d8a1c934) — so the DB itself would reject the node DELETE
    below with a FK violation if this nulling-and-flushing step were skipped.
    Same story for activities.node_id.
    """
    user_id = uuid.UUID(current_user.id)
    node, meta = await _get_owned_node_and_meta(db, user_id, node_id)
    if node is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")
    stable_key = meta.stable_key if meta else None

    events = (
        await db.execute(select(LearningEvent).where(LearningEvent.node_id == node_id, LearningEvent.user_id == user_id))
    ).scalars().all()
    for event in events:
        event.node_id = None
        event.payload = {**(event.payload or {}), "detached_from_stable_key": stable_key}
        db.add(event)

    activities = (
        await db.execute(select(Activity).where(Activity.node_id == node_id, Activity.user_id == user_id))
    ).scalars().all()
    for activity in activities:
        activity.node_id = None
        db.add(activity)
        await metrics.record_metric_event(
            db, user_id, "evidence_unmapped",
            payload={"reason": "node_deleted", "activity_id": str(activity.id)},
        )

    # Flush the nulling BEFORE the FK-checked delete — see docstring.
    await db.flush()
    await db.execute(delete(RoadmapNode).where(RoadmapNode.id == node_id))
    await db.commit()


@router.post("/sprint", response_model=CareerGoalOut)
async def declare_sprint(
    body: SprintIn,
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Sprint Mode (parent A3): a user-declared temporary weight override on
    one node, stored on the active goal. Phase 3's scheduler/balance score
    consumes it to suppress balance flags until sprint_until — nothing reads
    it yet."""
    user_id = uuid.UUID(current_user.id)
    goal = (
        await db.execute(select(CareerGoal).where(CareerGoal.user_id == user_id, CareerGoal.status == "active"))
    ).scalar_one_or_none()
    if goal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active goal — create one first.")

    node, _meta = await _get_owned_node_and_meta(db, user_id, body.node_id)
    if node is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")

    goal.sprint_node_id = body.node_id
    goal.sprint_until = body.sprint_until
    goal.updated_at = datetime.utcnow()
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    return goal


# --- Phase 3: Scheduler & Today screen (SPEC-career-coach-phase3.md §4) ------
# services/planner.py is the pure core (no DB, no clock) — this route owns
# both, assembling PlanInputs in one query pass and handing off to build_plan.

async def _get_active_goal_with_tree(db: AsyncSession, user_id: uuid.UUID) -> CareerGoal:
    """No goal, or a goal with no committed tree yet, is the same 404 — the
    plan function must never see a treeless goal (§6 step 1)."""
    goal = (
        await db.execute(select(CareerGoal).where(CareerGoal.user_id == user_id, CareerGoal.status == "active"))
    ).scalar_one_or_none()
    if goal is None or goal.roadmap_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active goal with a committed tree")
    return goal


def _plan_item_out(item) -> PlanItemOut:
    return PlanItemOut(
        kind=item.kind, review_id=item.review_id, node_id=item.node_id,
        label=item.label, reason=item.reason, est_share=item.est_share,
    )


@router.get("/today", response_model=TodayPlanOut)
async def get_today_plan(
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    user_id = uuid.UUID(current_user.id)
    now = datetime.utcnow()
    goal = await _get_active_goal_with_tree(db, user_id)

    # Lazily clear an expired sprint BEFORE building inputs (§6 step 6) — a
    # stale sprint_until must never leak into the plan we're about to build.
    if goal.sprint_until is not None and goal.sprint_until < now.date():
        goal.sprint_node_id = None
        goal.sprint_until = None
        goal.updated_at = now
        db.add(goal)
        await db.commit()
        await db.refresh(goal)

    node_rows = (
        await db.execute(
            select(RoadmapNode, NodeMeta, NodeMastery)
            .join(NodeMeta, NodeMeta.node_id == RoadmapNode.id)
            .outerjoin(
                NodeMastery,
                and_(NodeMastery.node_id == RoadmapNode.id, NodeMastery.user_id == user_id),
            )
            # The goal's own tree PLUS anything attached. node_ids flows on into
            # the balance-window filter below, so an attached roadmap the user
            # actively studies contributes its minutes — without that, attaching
            # a roadmap would make its own subject look permanently neglected.
            .where(RoadmapNode.roadmap_id.in_([goal.roadmap_id, *await _attached_roadmap_ids(db, goal.id)]))
        )
    ).all()
    node_ids = [row.RoadmapNode.id for row in node_rows]

    prereqs_by_node: dict = {}
    if node_ids:
        prereq_rows = (
            await db.execute(
                select(RoadmapNodePrerequisite).where(RoadmapNodePrerequisite.node_id.in_(node_ids))
            )
        ).scalars().all()
        for pr in prereq_rows:
            prereqs_by_node.setdefault(pr.node_id, []).append(pr.prerequisite_node_id)

    activities_by_node = {}
    if node_ids:
        activities_by_node = {
            a.node_id: a
            for a in (
                await db.execute(select(Activity).where(Activity.user_id == user_id, Activity.node_id.in_(node_ids)))
            ).scalars().all()
        }

    # m per node: m_learned * retrievability, via the phase-1 read-side — the
    # planner never re-derives decay math (§6 step 3).
    plan_nodes = []
    for row in node_rows:
        node, meta, nm = row.RoadmapNode, row.NodeMeta, row.NodeMastery
        m_learned = nm.m_learned if nm is not None else 0.0
        r = evidence.retrievability_for(activities_by_node.get(node.id), now)
        m = evidence.displayed_mastery(m_learned, r)
        plan_nodes.append(planner.PlanNode(
            node_id=str(node.id), title=node.title, subject=meta.subject, priority=meta.priority,
            est_effort_min=meta.est_effort_min, order_index=node.order_index,
            m_learned=m_learned, m=m,
            prereq_ids=tuple(str(p) for p in prereqs_by_node.get(node.id, [])),
        ))

    # subject_time_shares (§6 step 4): trailing-window minutes per subject,
    # normalized; total_window_minutes is the RAW total behind those shares —
    # the planner needs the magnitude (not just the ratios) for the §3.8a floor.
    window_start = now - timedelta(days=planner.BALANCE_WINDOW_DAYS)
    duration_rows = (
        await db.execute(
            select(NodeMeta.subject, func.sum(LearningEvent.duration_min))
            .join(LearningEvent, LearningEvent.node_id == NodeMeta.node_id)
            .where(
                LearningEvent.user_id == user_id,
                LearningEvent.deleted_at.is_(None),
                LearningEvent.occurred_at >= window_start,
                # Scope to THIS goal's tree. node_meta rows survive goal archival,
                # so without this an old tree's events inflate total_window_minutes
                # while contributing a_s under subjects the current tree may not
                # have. p_s is normalized over the current tree only, so every
                # current subject's a_s is deflated and balance_s = a_s - p_s
                # skews negative — manufacturing "you're neglecting X" nudges for
                # anyone who has ever switched career goals.
                LearningEvent.node_id.in_(node_ids),
            )
            .group_by(NodeMeta.subject)
        )
    ).all()
    total_window_minutes = sum(minutes or 0 for _, minutes in duration_rows)
    subject_time_shares = (
        {subject: (minutes or 0) / total_window_minutes for subject, minutes in duration_rows}
        if total_window_minutes > 0 else {}
    )

    # Due reviews (§6 step 5) — same shape as GET /api/reviews/due: oldest-first, capped.
    review_rows = (
        await db.execute(
            select(Review, RoadmapNode.title.label("node_title"))
            .join(Activity, Review.activity_id == Activity.id)
            .outerjoin(RoadmapNode, Activity.node_id == RoadmapNode.id)
            .where(Review.user_id == user_id, Review.status == "due", Review.scheduled_for <= now)
            .options(selectinload(Review.activity))
            .order_by(Review.scheduled_for.asc())
            .limit(REVIEW_SESSION_CAP)
        )
    ).all()
    due_reviews = tuple(
        planner.PlanReview(
            review_id=str(row.Review.id),
            label=row.node_title or row.Review.activity.topic,
            scheduled_for=row.Review.scheduled_for,
        )
        for row in review_rows
    )

    inputs = planner.PlanInputs(
        nodes=tuple(plan_nodes),
        due_reviews=due_reviews,
        subject_time_shares=subject_time_shares,
        total_window_minutes=total_window_minutes,
        sprint_node_id=str(goal.sprint_node_id) if goal.sprint_node_id else None,
        sprint_until=goal.sprint_until,
        target_date=goal.target_date,
        daily_minutes=goal.daily_minutes,
        now=now,
    )
    plan = planner.build_plan(inputs)

    return TodayPlanOut(
        items=[_plan_item_out(item) for item in plan.items],
        balance=plan.balance,
        overflow=plan.overflow,
        tree_complete=plan.tree_complete,
        daily_minutes=goal.daily_minutes,
    )


@router.patch("/goals/active", response_model=CareerGoalOut)
async def patch_active_goal(
    body: GoalPatchIn,
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Clamp, don't merely validate — a slider that overshoots 30-240 should
    silently land in range, not 422 (§6)."""
    user_id = uuid.UUID(current_user.id)
    goal = (
        await db.execute(select(CareerGoal).where(CareerGoal.user_id == user_id, CareerGoal.status == "active"))
    ).scalar_one_or_none()
    if goal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active goal")

    goal.daily_minutes = max(30, min(240, body.daily_minutes))
    goal.updated_at = datetime.utcnow()
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    return goal


@router.post("/today/feedback", status_code=status.HTTP_204_NO_CONTENT)
async def post_today_feedback(
    body: TodayFeedbackIn,
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Telemetry only — mutates no plan state. The plan is derived, never
    stored, so the next GET /today recomputes from scratch regardless."""
    user_id = uuid.UUID(current_user.id)
    await metrics.record_metric_event(
        db, user_id, event_type="plan_item_feedback",
        payload={"item_ref": body.item_ref, "action": body.action},
    )
    await db.commit()


# --- Attached roadmaps (IMPLEMENTATION-career-attached-roadmaps.md) ----------
# A goal plans from its generated tree PLUS any roadmaps the user attaches.
# The planner INNER JOINs node_meta and cannot score a node without
# subject/priority/effort, and catalog nodes have no node_meta at all — so
# attaching means creating sidecar rows, never copying roadmap_nodes.

MAX_ATTACHED_ROADMAPS = 5
_ATTACHED_EFFORT_MIN = 60  # flat: effort only ever *proportions* a session (spec §0)


def _attached_key(roadmap: Roadmap) -> str:
    """Prefix identifying node_meta rows this feature generated, so detach can
    remove exactly its own and nothing a template tree owns."""
    return f"attached.{roadmap.slug or roadmap.id}"


async def _caller_audience(db: AsyncSession, user_id: uuid.UUID) -> str:
    pref = (
        await db.execute(select(UserPref.audience).where(UserPref.user_id == user_id))
    ).scalar_one_or_none()
    return pref or "career"


async def _get_active_goal(db: AsyncSession, user_id: uuid.UUID) -> CareerGoal:
    """Active goal, tree or not — deliberately weaker than
    `_get_active_goal_with_tree`.

    Attaching needs only `career_goals.id`; the committed tree is irrelevant to
    it. Requiring one locked the picker out of onboarding, which is precisely
    where users discover the gap that makes them want it (the AI Engineer
    template carries no DSA subject at all, and generation may not invent one —
    an invented subject is a hard-rule violation in career_tree.py). The goal row
    exists from onboarding step 1; only `roadmap_id` is NULL until commit.
    """
    goal = (
        await db.execute(
            select(CareerGoal).where(CareerGoal.user_id == user_id, CareerGoal.status == "active")
        )
    ).scalar_one_or_none()
    if goal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active goal")
    return goal


async def _attached_roadmap_ids(db: AsyncSession, goal_id: uuid.UUID) -> list[uuid.UUID]:
    return list(
        (
            await db.execute(
                select(CareerGoalRoadmap.roadmap_id).where(CareerGoalRoadmap.goal_id == goal_id)
            )
        ).scalars().all()
    )


@router.get("/roadmaps/available", response_model=AvailableRoadmapsOut)
async def list_available_roadmaps(
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """What this goal may attach, minus anything already attached and its own tree."""
    user_id = uuid.UUID(current_user.id)
    goal = await _get_active_goal(db, user_id)
    audience = await _caller_audience(db, user_id)
    excluded = set(await _attached_roadmap_ids(db, goal.id)) | {goal.roadmap_id}

    # Same visibility rule as GET /api/roadmaps/: official catalog for the
    # caller's audience, plus the caller's own. A school user must never be
    # offered career roadmaps.
    rows = (
        await db.execute(
            select(Roadmap, func.count(RoadmapNode.id).label("node_count"))
            .outerjoin(RoadmapNode, RoadmapNode.roadmap_id == Roadmap.id)
            .where(
                or_(
                    and_(Roadmap.user_id.is_(None), Roadmap.audience == audience),
                    Roadmap.user_id == user_id,
                )
            )
            .group_by(Roadmap.id)
            .order_by(Roadmap.title.asc())
        )
    ).all()

    inbuilt, mine = [], []
    for row in rows:
        rm = row.Roadmap
        if rm.id in excluded:
            continue
        item = AvailableRoadmapOut(
            id=rm.id, slug=rm.slug, title=rm.title, node_count=row.node_count,
            source="mine" if rm.user_id is not None else "inbuilt",
        )
        (mine if rm.user_id is not None else inbuilt).append(item)
    return AvailableRoadmapsOut(inbuilt=inbuilt, mine=mine)


@router.get("/roadmaps/", response_model=list[AttachedRoadmapOut])
async def list_attached_roadmaps(
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    user_id = uuid.UUID(current_user.id)
    goal = await _get_active_goal(db, user_id)
    rows = (
        await db.execute(
            select(CareerGoalRoadmap, Roadmap, func.count(RoadmapNode.id).label("node_count"))
            .join(Roadmap, Roadmap.id == CareerGoalRoadmap.roadmap_id)
            .outerjoin(RoadmapNode, RoadmapNode.roadmap_id == Roadmap.id)
            .where(CareerGoalRoadmap.goal_id == goal.id)
            .group_by(CareerGoalRoadmap.id, Roadmap.id)
            .order_by(CareerGoalRoadmap.created_at.asc())
        )
    ).all()
    return [
        AttachedRoadmapOut(
            roadmap_id=r.Roadmap.id, slug=r.Roadmap.slug, title=r.Roadmap.title,
            subject=r.CareerGoalRoadmap.subject,
            default_priority=r.CareerGoalRoadmap.default_priority,
            node_count=r.node_count,
        )
        for r in rows
    ]


@router.post("/roadmaps/", response_model=AttachedRoadmapOut, status_code=status.HTTP_201_CREATED)
async def attach_roadmap(
    body: AttachRoadmapIn,
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Attach in one click: only roadmap_id is required. Subject defaults to the
    roadmap's slug (or its lowercased title) and priority to 3, so the UI needs
    no form — the user can refine both afterwards."""
    user_id = uuid.UUID(current_user.id)
    goal = await _get_active_goal(db, user_id)

    roadmap = (
        await db.execute(select(Roadmap).where(Roadmap.id == body.roadmap_id))
    ).scalar_one_or_none()
    if roadmap is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roadmap not found")

    # THE IDOR GATE for this feature. Without it any user could attach — and so
    # read the node titles of — any other user's private syllabus roadmap.
    if roadmap.user_id is not None and roadmap.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your roadmap")

    if roadmap.id == goal.roadmap_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="That roadmap is already this goal's tree",
        )

    existing = await _attached_roadmap_ids(db, goal.id)
    if roadmap.id in existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already attached")
    if len(existing) >= MAX_ATTACHED_ROADMAPS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"At most {MAX_ATTACHED_ROADMAPS} roadmaps can be attached to a goal",
        )

    subject = (body.subject or roadmap.slug or roadmap.title).strip().lower()
    priority = body.default_priority or 3
    db.add(CareerGoalRoadmap(
        goal_id=goal.id, roadmap_id=roadmap.id, subject=subject, default_priority=priority,
    ))

    # Sidecars for every node that lacks one. Never overwrite an existing
    # node_meta — it may be a template row carrying user_edited=True.
    nodes = (
        await db.execute(select(RoadmapNode).where(RoadmapNode.roadmap_id == roadmap.id))
    ).scalars().all()
    node_ids = [n.id for n in nodes]
    already_meta = set()
    if node_ids:
        already_meta = set(
            (
                await db.execute(select(NodeMeta.node_id).where(NodeMeta.node_id.in_(node_ids)))
            ).scalars().all()
        )
    prefix = _attached_key(roadmap)
    nodes_added = 0
    for n in nodes:
        if n.id in already_meta:
            continue
        db.add(NodeMeta(
            node_id=n.id, stable_key=f"{prefix}.{n.id}", subject=subject,
            priority=priority, est_effort_min=_ATTACHED_EFFORT_MIN,
        ))
        nodes_added += 1

    await db.commit()
    return AttachedRoadmapOut(
        roadmap_id=roadmap.id, slug=roadmap.slug, title=roadmap.title, subject=subject,
        default_priority=priority, node_count=len(nodes), nodes_added=nodes_added,
    )


@router.delete("/roadmaps/{roadmap_id}", status_code=status.HTTP_204_NO_CONTENT)
async def detach_roadmap(
    roadmap_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Stops planning from this roadmap. Deliberately leaves learning_events,
    node_mastery, activities and user_progress alone — evidence is append-only
    (ARCHITECTURE-learning-system.md), and detaching must not erase the fact
    that the user studied something."""
    user_id = uuid.UUID(current_user.id)
    goal = await _get_active_goal(db, user_id)

    link = (
        await db.execute(
            select(CareerGoalRoadmap).where(
                CareerGoalRoadmap.goal_id == goal.id,
                CareerGoalRoadmap.roadmap_id == roadmap_id,
            )
        )
    ).scalar_one_or_none()
    if link is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not attached")

    roadmap = (
        await db.execute(select(Roadmap).where(Roadmap.id == roadmap_id))
    ).scalar_one_or_none()
    if roadmap is not None:
        # Only the sidecars THIS feature generated, and never one the user has
        # since edited by hand.
        await db.execute(
            delete(NodeMeta).where(
                NodeMeta.stable_key.like(f"{_attached_key(roadmap)}.%"),
                NodeMeta.user_edited.is_(False),
            )
        )
    await db.delete(link)
    await db.commit()
