"""Topic-key resolution for Quiz v2's due-queue grouping
(docs/IMPLEMENTATION-quiz-capture-v2.md Step 5.4).

A topic_key groups due cards for PRESENTATION AND SELECTION ONLY — FSRS
scheduling stays per-card and untouched
(docs/ARCHITECTURE-learning-system.md §0, §2 Layer 4/5). Resolution order,
first match wins:

  1. `activity.node_id`             -> a FACT (lesson card, or a card a human
                                        explicitly linked to a node)
  2. `problem_concepts` primary map -> a FACT (LeetCode card, mapped to a
                                        roadmap node by the curated pass)
  3. `activity.roadmap_id`          -> a FACT, coarser (logged against a
                                        roadmap but no specific node)
  4. embedding match >= TRIAGE_THRESHOLD, cached on the activity            -> a
                                        HYPOTHESIS — never written to
                                        `activity.node_id` (that stays a fact
                                        the user or the catalog set; an
                                        inference may recommend/group, never
                                        overwrite — architecture law §0)
  5. `standalone:<activity_id>`     -> no signal at all

Use `resolve_topic_keys()` for a batch of activities (e.g. one due-queue
response) — it embeds every activity that needs the fallback in ONE
`embed_batch()` call instead of one blocking `embed()` round trip per
activity, and runs that call via `asyncio.to_thread` so it can't stall the
event loop for other requests while it waits.
"""
import asyncio
import uuid
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Activity, NodeMeta, ProblemConcept, Roadmap, RoadmapNode
from app.services import embeddings, topic_mapping

# Bump whenever the matching logic or thresholds change, so a cached match
# made under the old logic is recomputed instead of trusted forever.
TOPIC_CACHE_VERSION = 1


@dataclass
class TopicKey:
    key: str
    label: str


async def _node_topic_key(db: AsyncSession, node_id: uuid.UUID) -> TopicKey:
    node = (await db.execute(select(RoadmapNode).where(RoadmapNode.id == node_id))).scalar_one_or_none()
    return TopicKey(key=f"node:{node_id}", label=node.title if node else "Unknown topic")


async def _resolve_fact_based(db: AsyncSession, activity: Activity) -> Optional[TopicKey]:
    """Tiers 1-3 — no embedding involved, so no batching concern."""
    if activity.node_id is not None:
        return await _node_topic_key(db, activity.node_id)

    if activity.problem_id is not None:
        primary_node_id = (
            await db.execute(
                select(ProblemConcept.node_id).where(
                    ProblemConcept.problem_id == activity.problem_id,
                    ProblemConcept.role == "primary",
                )
            )
        ).scalar_one_or_none()
        if primary_node_id is not None:
            return await _node_topic_key(db, primary_node_id)

    if activity.roadmap_id is not None:
        roadmap = (
            await db.execute(select(Roadmap).where(Roadmap.id == activity.roadmap_id))
        ).scalar_one_or_none()
        return TopicKey(
            key=f"roadmap:{activity.roadmap_id}",
            label=roadmap.title if roadmap else "Unknown roadmap",
        )

    return None


def _cached_topic_key(activity: Activity) -> Optional[TopicKey]:
    """Trust the cache whenever it was written under the CURRENT matching
    logic — including a cached "no match found" (`topic_node_cache_id is
    None`). That's a real, previously-computed answer, not an empty cache;
    treating it as a miss would re-run the embedding match (and its API
    call) on every single due-queue request for exactly the standalone
    activities least likely to ever match anything."""
    if activity.topic_cache_version != TOPIC_CACHE_VERSION:
        return None
    if activity.topic_node_cache_id is not None:
        return "cached_node"  # caller resolves the node; see resolve_topic_keys
    return TopicKey(key=f"standalone:{activity.id}", label=activity.topic)


async def resolve_topic_keys(db: AsyncSession, activities: list[Activity]) -> dict:
    """Resolve topic keys for a BATCH of activities (e.g. one due-queue
    response), keyed by activity.id. Every activity needing the embedding
    fallback is embedded in a single batched call rather than one per
    activity — see the module docstring."""
    results: dict = {}
    needs_fresh_match: list[Activity] = []

    for activity in activities:
        fact = await _resolve_fact_based(db, activity)
        if fact is not None:
            results[activity.id] = fact
            continue

        cached = _cached_topic_key(activity)
        if cached == "cached_node":
            results[activity.id] = await _node_topic_key(db, activity.topic_node_cache_id)
            continue
        if cached is not None:
            results[activity.id] = cached
            continue

        needs_fresh_match.append(activity)

    if needs_fresh_match:
        results.update(await _batch_embedding_match_and_cache(db, needs_fresh_match))

    return results


async def resolve_topic_key(db: AsyncSession, activity: Activity) -> TopicKey:
    """Single-activity convenience wrapper around `resolve_topic_keys` — for
    call sites resolving just one card (e.g. a test, or a future endpoint
    that isn't already looping over a batch)."""
    return (await resolve_topic_keys(db, [activity]))[activity.id]


async def _batch_embedding_match_and_cache(db: AsyncSession, activities: list[Activity]) -> dict:
    """Embedding match against every catalog node with an embedding (populated
    by scripts/backfill_catalog_node_embeddings.py — most catalog nodes have
    none until that's run), for a whole batch of activities in one
    `embed_batch()` call. Writes each activity's derived-cache columns in the
    session; does NOT commit — the caller commits once for the whole batch."""
    rows = (
        await db.execute(
            select(NodeMeta.node_id, NodeMeta.embedding, RoadmapNode.title)
            .join(RoadmapNode, RoadmapNode.id == NodeMeta.node_id)
            .where(NodeMeta.embedding.is_not(None))
        )
    ).all()
    candidates = [
        {"node_id": r.node_id, "stable_key": "", "title": r.title, "description": None, "embedding": r.embedding}
        for r in rows
    ]

    texts = [activity.topic for activity in activities]
    try:
        # embed_batch is a blocking call (a real network round trip behind a
        # ThreadPoolExecutor .result() wait) — run it in a worker thread so it
        # can't freeze the event loop for every OTHER request while it waits.
        vectors = await asyncio.to_thread(embeddings.embed_batch, texts)
    except Exception:
        vectors = [[] for _ in activities]

    results: dict = {}
    for activity, vector in zip(activities, vectors):
        suggestion = topic_mapping.suggest_node_for_embedding(vector, candidates) if vector else None

        activity.topic_cache_version = TOPIC_CACHE_VERSION
        activity.topic_node_cache_id = suggestion["node_id"] if suggestion else None
        db.add(activity)

        if suggestion is not None:
            results[activity.id] = TopicKey(key=f"node:{suggestion['node_id']}", label=suggestion["title"])
        else:
            results[activity.id] = TopicKey(key=f"standalone:{activity.id}", label=activity.topic)

    return results
