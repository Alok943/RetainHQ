"""Sync the `problems` catalog (source='neetcode') from neetcode.io's own public API.

Why this exists (2026-08-02): NeetCode has its own problem catalog, entirely
separate from LeetCode's — different slugs, different problem text even for
"the same" interview question (NeetCode's Two Sum is `two-integer-sum`, not
`two-sum`, confirmed live). It cannot reuse `import_leetcode_catalog.py`'s data
or the existing LeetCode `problems` rows at all.

`getProblemListFunctionHttp` is genuinely public — confirmed by calling it from
an unauthenticated browser session (no cookies, no sign-in) and getting a full
200 response, ~250 problems, every time. Response shape:
    {"data": {"<slug>": {"difficulty": "Easy"|"Medium"|"Hard",
                          "free": bool, "tag": "<category>", "name": "<title>"}}}

NeetCode has no numeric problem id anywhere in this response (unlike LeetCode's
`stat.frontend_question_id`), but `problems.external_id` is NOT NULL and must be
unique per source — so this script derives a stable synthetic one via CRC32 of
the slug. Deterministic across re-runs (same slug -> same id every time), which
is what makes the upsert idempotent rather than creating a duplicate row per run.

**Deliberately does NOT write `problem_concepts` (roadmap-node mappings).**
Curating which DSA-roadmap node each of ~250 problems teaches is real content
judgment — the same class of work as `mapping.v1.json`'s LeetCode mapping,
which was a whole separate curation pass, not something this script's LeetCode
counterpart does inline either. Per CLAUDE.md's content-pipeline convention,
bulk content curation is Antigravity's job, not something to invent here.
Every imported problem is `evidence_unmapped` until that mapping exists — a
real solve on neetcode.io will be received and logged as an unmapped metric,
not silently dropped, but it won't move any node's mastery until mapped.

**Not run against prod by this session.** Writes are local/whatever
DATABASE_URL the environment points at — same convention as
purge_leetcode_backfill.py: dry-run by default, the operator decides when to
point it at prod and commit.

Usage (from backend/, venv active):
    python -m scripts.import_neetcode_catalog --dry-run
    python -m scripts.import_neetcode_catalog --commit
"""
import argparse
import asyncio
import logging
import zlib

import httpx
from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import async_session_maker
from app.models.models import Problem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CATALOG_URL = "https://neetcode.io/api/getProblemListFunctionHttp"
CATALOG_VERSION = "v1"


# `problems.external_id` is a Postgres INTEGER (int4, max 2_147_483_647) —
# verified against prod, not assumed. Bare zlib.crc32 returns a full unsigned
# 32-bit value (up to 4_294_967_295), so 453 of the 938 real NeetCode slugs
# (48.3%, measured) would have raised NumericValueOutOfRange on INSERT.
# Masking to 31 bits keeps every id inside int4 and positive.
#
# This was NOT caught by the importer's own --dry-run, and could not have
# been: the dry-run calls db.add() then rollback() without ever flushing, so
# no INSERT is attempted and no column constraint is exercised. A dry-run here
# proves the fetch and the create/update split, nothing about whether the
# write would succeed.
_INT4_MASK = 0x7FFFFFFF


def slug_to_external_id(slug: str) -> int:
    """Deterministic, source-scoped synthetic id — NeetCode gives us none.
    A collision would silently upsert one problem's data onto another's row,
    so it is checked against the real slug set rather than assumed unlikely
    (see fetch_catalog)."""
    return zlib.crc32(slug.encode("utf-8")) & _INT4_MASK


async def fetch_catalog(client: httpx.AsyncClient) -> dict[str, dict]:
    resp = await client.post(CATALOG_URL, json={"data": {}}, timeout=30.0)
    resp.raise_for_status()
    catalog = resp.json()["data"]
    logger.info(f"Fetched {len(catalog)} problems from neetcode.io")

    # Verify the CRC32 external_id scheme is actually collision-free for the
    # REAL slug set, not just "probably fine" — cheap to check, expensive to
    # discover wrong via a silently-overwritten catalog row.
    seen: dict[int, str] = {}
    for slug in catalog:
        ext_id = slug_to_external_id(slug)
        if ext_id in seen and seen[ext_id] != slug:
            raise RuntimeError(
                f"external_id collision: {seen[ext_id]!r} and {slug!r} both hash to {ext_id}. "
                "slug_to_external_id needs a different scheme before this can import safely."
            )
        seen[ext_id] = slug
    return catalog


async def import_catalog(db: AsyncSession, catalog: dict[str, dict], commit: bool) -> None:
    existing = {
        p.external_id: p
        for p in (await db.execute(select(Problem).where(Problem.source == "neetcode"))).scalars().all()
    }

    created, updated = 0, 0
    for slug, meta in catalog.items():
        ext_id = slug_to_external_id(slug)
        difficulty = (meta.get("difficulty") or "").lower()
        problem = existing.get(ext_id)
        if problem is None:
            problem = Problem(
                source="neetcode",
                external_id=ext_id,
                slug=slug,
                title=meta.get("name", slug),
                difficulty=difficulty,
                tags=[meta["tag"]] if meta.get("tag") else [],
                url=f"https://neetcode.io/problems/{slug}",
                paid_only=not meta.get("free", True),
                catalog_version=CATALOG_VERSION,
            )
            db.add(problem)
            created += 1
        else:
            problem.slug = slug
            problem.title = meta.get("name", slug)
            problem.difficulty = difficulty
            problem.tags = [meta["tag"]] if meta.get("tag") else []
            problem.paid_only = not meta.get("free", True)
            problem.catalog_version = CATALOG_VERSION
            updated += 1

    # FLUSH even on a dry run, then roll back. Without this the dry run never
    # sends a single INSERT, so it cannot surface a column-constraint failure
    # (int4 overflow, a too-long string, a NOT NULL violation) — which is
    # exactly how a 48%-failure-rate external_id scheme passed a "clean" dry
    # run. Flushing inside the transaction exercises every constraint for
    # real; the rollback still guarantees nothing is persisted.
    await db.flush()
    logger.info(f"{'Would create' if not commit else 'Created'} {created}, {'would update' if not commit else 'updated'} {updated}")

    if commit:
        await db.commit()
    else:
        await db.rollback()
        logger.info("Rolled back — the INSERTs above were executed and validated, then discarded.")


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", action="store_true", default=True)
    group.add_argument("--commit", action="store_true")
    args = parser.parse_args()

    async with httpx.AsyncClient() as client:
        catalog = await fetch_catalog(client)

    async with async_session_maker() as db:
        await import_catalog(db, catalog, commit=args.commit)

    if not args.commit:
        logger.info("DRY RUN — nothing written. Re-run with --commit to apply.")
    logger.warning(
        "No problem_concepts (roadmap-node mappings) were written — every imported "
        "problem is evidence_unmapped until a curated mapping pass covers it."
    )


if __name__ == "__main__":
    asyncio.run(main())
