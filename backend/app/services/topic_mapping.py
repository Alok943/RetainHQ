"""Topic mapping for previously-unmapped evidence (SPEC-career-coach-phase2.md
§5). Phase-1's Producer A skips RECALL_GRADED events when an activity has no
node_id (§6.3) and records an `evidence_unmapped` MetricEvent instead. This
module is what SPENDS that finding:

  Tier 1 — exact/structured (activity.node_id already set, or the diagnostic
  path) needs nothing from here; it's handled at the point of review
  completion / commit.
  Tier 2 — a text-similarity match against the user's committed career tree,
  auto-mapping above AUTO_MAP_THRESHOLD, flagging for triage in the band
  below it, and leaving anything lower in the unmapped bucket (Tier 3).
  Tier 3 — the unmapped bucket: a human assigns a node by hand via
  routes/career.py's /unmapped endpoints.
"""
import uuid
from typing import Optional, TypedDict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Activity, CareerGoal, NodeMeta, Review, RoadmapNode
from app.services import evidence, embeddings

# §5 thresholds — provisional, NOT yet gated against ground truth. §1.3's
# validation gate (re-run backfill_career_mapping.py, owner judges the 6
# known-unmapped activities) has not been run since these moved off the
# Jaccard-era defaults. Do not treat these as tuned until that gate passes.
AUTO_MAP_THRESHOLD = 0.75
TRIAGE_THRESHOLD = 0.65


class CandidateNode(TypedDict):
    node_id: uuid.UUID
    stable_key: str
    title: str
    description: Optional[str]
    embedding: list[float]


class MappingSuggestion(TypedDict):
    node_id: uuid.UUID
    stable_key: str
    title: str
    description: Optional[str]
    confidence: float
    tier: str  # 'auto' | 'triage'


async def candidate_nodes_for_active_goal(db: AsyncSession, user_id: uuid.UUID) -> list:
    """The user's currently committed career tree, as `suggest_node`'s
    candidate shape. Scoped to the ACTIVE goal's tree — the one the user is
    currently building evidence toward — not every tree they've ever had.
    Shared by the /unmapped route (one user, live) and the bulk backfill
    script (step 10, same query)."""
    goal = (
        await db.execute(select(CareerGoal).where(CareerGoal.user_id == user_id, CareerGoal.status == "active"))
    ).scalar_one_or_none()
    if goal is None or goal.roadmap_id is None:
        return []

    rows = (
        await db.execute(
            select(NodeMeta, RoadmapNode)
            .join(RoadmapNode, RoadmapNode.id == NodeMeta.node_id)
            .where(RoadmapNode.roadmap_id == goal.roadmap_id)
        )
    ).all()
    return [
        {
            "node_id": rn.id,
            "stable_key": meta.stable_key,
            "title": rn.title,
            "description": rn.description,
            "embedding": meta.embedding or []
        }
        for meta, rn in rows
    ]


def suggest_node(topic_text: str, candidate_nodes: list) -> Optional[MappingSuggestion]:
    """Best-matching node for `topic_text` among `candidate_nodes` (a user's
    committed career tree). Returns None if nothing scores >= TRIAGE_THRESHOLD
    — i.e. Tier 3, the unmapped bucket, is where this belongs."""
    if not candidate_nodes:
        return None
        
    try:
        topic_embedding = embeddings.embed(topic_text)
    except Exception:
        # If embedding fails (e.g. rate limit, config missing), we fall back to no-match
        return None

    best = None
    best_score = 0.0
    for node in candidate_nodes:
        # Fallback to 0 if node was created before embeddings were added
        if not node.get("embedding"):
            continue
            
        score = embeddings.similarity(topic_embedding, node["embedding"])
        if score > best_score:
            best_score = score
            best = node

    if best is None or best_score < TRIAGE_THRESHOLD:
        return None

    tier = "auto" if best_score >= AUTO_MAP_THRESHOLD else "triage"
    return MappingSuggestion(
        node_id=best["node_id"], stable_key=best["stable_key"], title=best["title"],
        description=best["description"], confidence=best_score, tier=tier,
    )

async def candidate_nodes_for_user(db: AsyncSession, user_id: uuid.UUID) -> list:
    """Returns ALL nodes a user has access to (their active career goal + any personal roadmaps)."""
    from app.models.models import Roadmap
    
    # 1. Get personal roadmaps
    personal_stmt = select(Roadmap.id).where(Roadmap.user_id == user_id)
    personal_ids = (await db.execute(personal_stmt)).scalars().all()
    
    # 2. Get active catalog roadmap from career goal
    goal = (
        await db.execute(select(CareerGoal).where(CareerGoal.user_id == user_id, CareerGoal.status == "active"))
    ).scalar_one_or_none()
    
    roadmap_ids = list(personal_ids)
    if goal and goal.roadmap_id and goal.roadmap_id not in roadmap_ids:
        roadmap_ids.append(goal.roadmap_id)
        
    if not roadmap_ids:
        return []
        
    rows = (
        await db.execute(
            select(NodeMeta, RoadmapNode)
            .join(RoadmapNode, RoadmapNode.id == NodeMeta.node_id)
            .where(RoadmapNode.roadmap_id.in_(roadmap_ids))
        )
    ).all()
    
    return [
        {
            "node_id": rn.id,
            "stable_key": meta.stable_key,
            "title": rn.title,
            "description": rn.description,
            "embedding": meta.embedding or []
        }
        for meta, rn in rows
    ]

def top_k_suggested_nodes(topic_text: str, candidate_nodes: list, k: int = 5) -> list[MappingSuggestion]:
    """Returns the top K best-matching nodes for `topic_text` among `candidate_nodes`
    using embedding similarity."""
    if not candidate_nodes:
        return []
        
    try:
        topic_embedding = embeddings.embed(topic_text)
    except Exception:
        return []

    scored_nodes = []
    for node in candidate_nodes:
        if not node.get("embedding"):
            continue
            
        score = embeddings.similarity(topic_embedding, node["embedding"])
        tier = "auto" if score >= AUTO_MAP_THRESHOLD else "triage"
        scored_nodes.append(MappingSuggestion(
            node_id=node["node_id"], stable_key=node["stable_key"], title=node["title"],
            description=node.get("description"), confidence=score, tier=tier,
        ))

    scored_nodes.sort(key=lambda x: x["confidence"], reverse=True)
    return scored_nodes[:k]


async def backfill_activity(
    db: AsyncSession, user_id: uuid.UUID, activity_id: uuid.UUID, node_id: uuid.UUID,
) -> int:
    """Assign `node_id` to `activity_id` and retroactively write the
    RECALL_GRADED events Producer A skipped for each of its completed
    reviews — the concrete fix for the phase-1 finding (§5's "Backfill"),
    shared by the /unmapped/{id}/assign endpoint (one activity) and the bulk
    backfill script (step 10, every unmapped activity). Never commits — rides
    the caller's transaction. Returns events written (0 if none, or all were
    already-recorded dedupe hits)."""
    activity = (
        await db.execute(select(Activity).where(Activity.id == activity_id, Activity.user_id == user_id))
    ).scalar_one_or_none()
    if activity is None:
        raise ValueError(f"Activity {activity_id} not found for this user.")

    activity.node_id = node_id
    db.add(activity)

    reviews = (
        await db.execute(
            select(Review).where(
                Review.activity_id == activity_id,
                Review.user_id == user_id,
                Review.status == "completed",
            )
        )
    ).scalars().all()

    written = 0
    for review in reviews:
        grade = evidence.recall_grade(review.recalled, review.rating, review.quality)
        if grade is None:
            continue
        event = await evidence.record_event(
            db, user_id,
            event_type="RECALL_GRADED",
            trust_tier="T2_verified_internal",
            source="retainhq_review",
            node_id=node_id,
            grade=grade,
            outcome="pass" if review.recalled else "fail",
            duration_min=round(review.duration_ms / 60000) if review.duration_ms else 0,
            entity_id=review.id,
            occurred_at=review.completed_at,
            payload={
                "rating": review.rating, "recalled": review.recalled, "quality": review.quality,
                "ai_verdict": review.ai_verdict, "backfilled": True,
            },
        )
        if event is not None:
            written += 1

    return written
