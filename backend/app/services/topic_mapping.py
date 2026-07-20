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

Tier 2's similarity function is deliberately NOT a real embedding call.
pgvector is available on this Supabase project but NOT installed (confirmed
via list_extensions before writing this), and the spec explicitly says not
to enable it just for <=90 in-tree vectors. Word-overlap similarity is the
placeholder; a real embedding call (e.g. Gemini's embed_content — the same
provider already wired for syllabus extraction) is the natural upgrade once
triage volume on real data justifies the added cost — swapping it in only
touches `_similarity`.
"""
import re
import uuid
from typing import Optional, TypedDict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Activity, CareerGoal, NodeMeta, Review, RoadmapNode
from app.services import evidence

# §5 thresholds — named config constants. The parent doc marks these as an
# open question to tune on the owner's own triage logs; ship the numbers,
# don't hardcode the decision path around them.
AUTO_MAP_THRESHOLD = 0.75
TRIAGE_THRESHOLD = 0.55

_WORD_RE = re.compile(r"[a-z0-9]+")


class CandidateNode(TypedDict):
    node_id: uuid.UUID
    stable_key: str
    title: str
    description: Optional[str]


class MappingSuggestion(TypedDict):
    node_id: uuid.UUID
    stable_key: str
    title: str
    confidence: float
    tier: str  # 'auto' | 'triage'


def _tokens(text: str) -> set:
    return set(_WORD_RE.findall((text or "").lower()))


def _similarity(text_a: str, text_b: str) -> float:
    """Jaccard word overlap — see module docstring for why this isn't a real
    embedding call yet."""
    a, b = _tokens(text_a), _tokens(text_b)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


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
        {"node_id": rn.id, "stable_key": meta.stable_key, "title": rn.title, "description": rn.description}
        for meta, rn in rows
    ]


def suggest_node(topic_text: str, candidate_nodes: list) -> Optional[MappingSuggestion]:
    """Best-matching node for `topic_text` among `candidate_nodes` (a user's
    committed career tree). Returns None if nothing scores >= TRIAGE_THRESHOLD
    — i.e. Tier 3, the unmapped bucket, is where this belongs."""
    best = None
    best_score = 0.0
    for node in candidate_nodes:
        text = f"{node['title']} {node.get('description') or ''}"
        score = _similarity(topic_text, text)
        if score > best_score:
            best_score = score
            best = node

    if best is None or best_score < TRIAGE_THRESHOLD:
        return None

    tier = "auto" if best_score >= AUTO_MAP_THRESHOLD else "triage"
    return MappingSuggestion(
        node_id=best["node_id"], stable_key=best["stable_key"], title=best["title"],
        confidence=best_score, tier=tier,
    )


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
