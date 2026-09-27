"""Backfill embeddings for CATALOG roadmap nodes (dsa, sql, python-swe, ...),
not just career-tree nodes (docs/IMPLEMENTATION-quiz-capture-v2.md Step 5.4).

WHY THIS EXISTS: `node_meta.embedding` (migration fd9b3eaf3c37) has only ever
been populated for nodes attached to a committed career tree
(`career_tree.py`'s `commit_tree`) — `services/topic_mapping.py`'s own
docstring says "Rows exist only for career-tree nodes." Quiz v2's topic-key
resolution needs an embedding match for cards with no node_id/roadmap_id/
problem mapping (services/topic_key.py's Step 4 fallback), and today that
fallback would have ZERO candidates for anyone not on a career track — most
of the catalog (dsa, sql, python-swe, ...) has no embedding coverage at all.
This script closes that gap: every `roadmap_nodes` row without a `node_meta`
row yet gets one, embedding `"<title>. <description>"` the same way
`commit_tree` does for career-tree nodes.

`node_meta`'s other columns (`priority`, `est_effort_min`, `review_policy`,
`user_edited`) are career-tree-specific and meaningless for a catalog node;
left at their schema defaults. `stable_key` is a required column whose
documented job ("stable across template versions") doesn't apply to catalog
nodes either — used here only as a human-readable label
(`"<roadmap-slug>.<node-id>"`); nothing reads it for a catalog-sourced
NodeMeta row. `subject` (also required) is set to the roadmap's slug, the
closest catalog analog of "top-level grouping." This widens `NodeMeta`'s
actual population beyond its original docstring, which this script's
docstring — and `node_meta`'s in models.py — should be read alongside.

Idempotent: only creates rows for nodes that don't already have one; safe to
re-run after new lessons are added. Real Gemini API calls (embed_batch),
batched — this has a real cost proportional to the catalog size, so it
defaults to --dry-run (reports what it WOULD do and its rough cost) and only
writes with --commit.

Run from backend/ (venv active):
    python -m scripts.backfill_catalog_node_embeddings --dry-run
    python -m scripts.backfill_catalog_node_embeddings --commit
"""
import argparse
import asyncio
import logging

from sqlalchemy import select

from app.core.database import async_session_maker
from app.models.models import NodeMeta, Roadmap, RoadmapNode
from app.services import embeddings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BATCH_SIZE = 50


async def find_nodes_needing_embeddings(db):
    """Every RoadmapNode with no NodeMeta row yet, paired with its roadmap's slug."""
    already_covered = set((await db.execute(select(NodeMeta.node_id))).scalars().all())
    rows = (
        await db.execute(
            select(RoadmapNode, Roadmap.slug).join(Roadmap, Roadmap.id == RoadmapNode.roadmap_id)
        )
    ).all()
    return [(node, slug) for node, slug in rows if node.id not in already_covered]


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", action="store_true", default=True)
    group.add_argument("--commit", action="store_true")
    args = parser.parse_args()
    commit = args.commit

    async with async_session_maker() as db:
        pending = await find_nodes_needing_embeddings(db)
        print(f"{len(pending)} roadmap node(s) have no node_meta row yet.")
        if not pending:
            return
        if not commit:
            print("DRY RUN — no writes, no API calls will be made. Re-run with --commit to actually embed + write.")
            for node, slug in pending[:10]:
                print(f"  would embed: {slug} / {node.title}")
            if len(pending) > 10:
                print(f"  ... and {len(pending) - 10} more")
            return

        created = 0
        failed = 0
        for i in range(0, len(pending), BATCH_SIZE):
            batch = pending[i : i + BATCH_SIZE]
            texts = [f"{node.title}. {node.description or ''}".strip() for node, _ in batch]
            try:
                vectors = embeddings.embed_batch(texts)
            except Exception as e:
                logger.error("batch %d-%d: embedding call failed, skipping (%s)", i, i + len(batch), e)
                failed += len(batch)
                continue
            for (node, slug), vector in zip(batch, vectors):
                if not vector:
                    failed += 1
                    continue
                db.add(
                    NodeMeta(
                        node_id=node.id,
                        stable_key=f"{slug}.{node.id}",
                        subject=slug,
                        embedding=vector,
                    )
                )
                created += 1
            await db.commit()
            print(f"  batch {i}-{i + len(batch)}: {created} created so far, {failed} failed so far")

        print(f"Done. Created {created} node_meta row(s); {failed} node(s) failed/skipped.")


if __name__ == "__main__":
    asyncio.run(main())
