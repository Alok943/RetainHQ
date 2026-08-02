"""Map neetcode.io slugs onto the EXISTING LeetCode catalog (`problem_aliases`).

Replaces `import_neetcode_catalog.py`'s approach, which imported a parallel
`source='neetcode'` catalog. Measured 2026-08-02, which is what changed the
design (D-071 reverses D-064): NeetCode's problems ARE LeetCode's problems,
re-slugged. `two-integer-sum` is Two Sum; `duplicate-integer` is Contains
Duplicate. On a 60-problem random sample, 56 resolved to an existing LeetCode
catalog row by exact normalised title.

That matters because `problem_concepts` — which roadmap node each problem
teaches — cost a whole curated LLM pass to build for LeetCode
(`reviewed_by='pass3-blind:gemini-3.1-pro'`, 2828 problems). Aliasing inherits
all of it, and keeps inheriting it as that mapping improves. A separate NeetCode
catalog would have needed its own pass and would then drift from this one.

RESOLUTION ORDER (each alias records which rule produced it):
  slug_identical - the NeetCode slug IS the LeetCode slug. Most of the catalog:
                   NeetCode only renamed a minority. Costs no network call.
  title_match    - fetch NeetCode's own metadata, match its `name` (the real
                   LeetCode title, e.g. "Two Sum" for `two-integer-sum`)
                   against `problems.title`, normalised.
  override       - NeetCode renamed the PROBLEM, not just the slug, so its title
                   doesn't match either. Hand-listed below; small and explicit.

Only `tag == 'NeetCode150'` entries are attempted. The other ~350 catalog
entries are NeetCode's own courses (SQL, Python For Beginners, ML, Design
Patterns) - not interview problems, with no LeetCode counterpart to alias to.
They're counted and reported, never silently dropped.

Both NeetCode endpoints used here are public: confirmed 200 unauthenticated,
no cookies, no account (this codebase cannot create one).

Usage (from backend/, venv active):
    python -m scripts.sync_neetcode_aliases --dry-run
    python -m scripts.sync_neetcode_aliases --commit
"""
import argparse
import asyncio
import logging
import re

import httpx
from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import async_session_maker
from app.models.models import Problem, ProblemAlias

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CATALOG_URL = "https://neetcode.io/api/getProblemListFunctionHttp"
METADATA_URL = "https://neetcode.io/api/getProblemMetadataFunctionHttp"
SOURCE = "neetcode"
DSA_TAG = "NeetCode150"

# Concurrency against someone else's public API. Deliberately modest: this is a
# one-off catalog sync, not a hot path, and there is no reason to hammer it.
FETCH_CONCURRENCY = 6

# NeetCode renamed the problem itself, so neither its slug nor its title matches
# LeetCode's. Hand-listed because there is no rule to derive them — extend it
# from the "unresolved" list this script prints. Keys are NeetCode slugs, values
# are LeetCode slugs.
# Every target below was confirmed to exist in the live LeetCode catalog before
# being written here, not recalled — a wrong target attributes a solve to the
# wrong problem and therefore the wrong node, which is silently-wrong mastery
# rather than a loud failure. `resolve()` logs a warning and skips any override
# whose target is missing, so a stale entry degrades to unmapped, never to
# mis-mapped.
OVERRIDES = {
    "copy-linked-list-with-random-pointer": "copy-list-with-random-pointer",
    "design-word-search-data-structure": "design-add-and-search-words-data-structure",
    "islands-and-treasure": "walls-and-gates",
    "kth-smallest-integer-in-bst": "kth-smallest-element-in-a-bst",
    "linked-list-cycle-detection": "linked-list-cycle",
    "longest-increasing-path-in-matrix": "longest-increasing-path-in-a-matrix",
    "lowest-common-ancestor-in-binary-search-tree": "lowest-common-ancestor-of-a-binary-search-tree",
    "merge-k-sorted-linked-lists": "merge-k-sorted-lists",
    "merge-triplets-to-form-target": "merge-triplets-to-form-target-triplet",
    "merge-two-sorted-linked-lists": "merge-two-sorted-lists",
    "min-cost-to-connect-points": "min-cost-to-connect-all-points",
    "non-cyclical-number": "happy-number",
    "products-of-array-discluding-self": "product-of-array-except-self",
    "reconstruct-flight-path": "reconstruct-itinerary",
    "reorder-linked-list": "reorder-list",
    "rotting-fruit": "rotting-oranges",
    "same-binary-tree": "same-tree",
    "two-integer-sum-ii": "two-sum-ii-input-array-is-sorted",
    "valid-binary-search-tree": "validate-binary-search-tree",
}


def normalize(text: str) -> str:
    """Title key for matching. Case and punctuation differ freely between the
    two sites ("Merge k Sorted Lists" vs "Merge K Sorted Lists"), so neither is
    load-bearing; word content is."""
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())


async def fetch_catalog(client: httpx.AsyncClient) -> dict[str, dict]:
    resp = await client.post(CATALOG_URL, json={"data": {}}, timeout=30.0)
    resp.raise_for_status()
    return resp.json()["data"]


async def fetch_name(client: httpx.AsyncClient, sem: asyncio.Semaphore, slug: str) -> tuple[str, str | None]:
    """NeetCode's own title for a slug. `getProblemListFunctionHttp` omits
    `name` for every NeetCode150 entry (present on only 350 of 938 — a shape
    the earlier importer's docstring got wrong, which would have titled 588
    problems with their raw slug), so it has to be fetched per problem."""
    async with sem:
        try:
            resp = await client.post(METADATA_URL, json={"data": {"problemId": slug}}, timeout=30.0)
            resp.raise_for_status()
            return slug, (resp.json().get("data") or {}).get("name")
        except Exception as exc:  # noqa: BLE001 - one bad slug must not kill the sync
            logger.warning("metadata fetch failed for %s: %s", slug, exc)
            return slug, None


async def resolve(
    client: httpx.AsyncClient, slugs: list[str], by_slug: dict[str, Problem], by_title: dict[str, Problem]
) -> tuple[dict[str, tuple[Problem, str]], list[str]]:
    """NeetCode slug -> (LeetCode problem, rule that matched). Cheap rules first
    so the network is only touched for what actually needs it."""
    resolved: dict[str, tuple[Problem, str]] = {}
    needs_lookup: list[str] = []

    for slug in slugs:
        if slug in OVERRIDES:
            target = by_slug.get(OVERRIDES[slug])
            if target is None:
                logger.warning("override %s -> %s: no such LeetCode slug", slug, OVERRIDES[slug])
                continue
            resolved[slug] = (target, "override")
        elif slug in by_slug:
            resolved[slug] = (by_slug[slug], "slug_identical")
        else:
            needs_lookup.append(slug)

    logger.info(
        "%d resolved without a network call (%d identical slugs, %d overrides); "
        "fetching titles for the remaining %d",
        len(resolved),
        sum(1 for _, rule in resolved.values() if rule == "slug_identical"),
        sum(1 for _, rule in resolved.values() if rule == "override"),
        len(needs_lookup),
    )

    sem = asyncio.Semaphore(FETCH_CONCURRENCY)
    for slug, name in await asyncio.gather(*(fetch_name(client, sem, s) for s in needs_lookup)):
        target = by_title.get(normalize(name)) if name else None
        if target is not None:
            resolved[slug] = (target, "title_match")

    unresolved = [s for s in slugs if s not in resolved]
    return resolved, unresolved


async def sync(db: AsyncSession, resolved: dict[str, tuple[Problem, str]], commit: bool) -> None:
    existing = {
        alias.alias_slug: alias
        for alias in (
            await db.execute(select(ProblemAlias).where(ProblemAlias.source == SOURCE))
        ).scalars().all()
    }

    created, repointed, unchanged = 0, 0, 0
    for slug, (problem, rule) in resolved.items():
        alias = existing.get(slug)
        if alias is None:
            db.add(ProblemAlias(problem_id=problem.id, source=SOURCE, alias_slug=slug, resolved_by=rule))
            created += 1
        elif alias.problem_id != problem.id:
            # A re-run pointing an existing alias somewhere new means either the
            # catalog changed or a rule did. Loud, because past evidence was
            # attributed under the OLD target and is not retroactively moved.
            logger.warning("alias %s repointed: %s -> %s (%s)", slug, alias.problem_id, problem.id, rule)
            alias.problem_id = problem.id
            alias.resolved_by = rule
            repointed += 1
        else:
            unchanged += 1

    # Flush even on a dry run so column constraints and the (source, alias_slug)
    # uniqueness are exercised for real; the rollback still persists nothing.
    # A dry run that never flushes validates nothing about whether the write
    # would actually succeed.
    await db.flush()
    verb = "Created" if commit else "Would create"
    logger.info("%s %d aliases, repointed %d, unchanged %d", verb, created, repointed, unchanged)

    if commit:
        await db.commit()
    else:
        await db.rollback()
        logger.info("Rolled back — the INSERTs above ran and were validated, then discarded.")


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", action="store_true", default=True)
    group.add_argument("--commit", action="store_true")
    args = parser.parse_args()

    async with httpx.AsyncClient() as client:
        catalog = await fetch_catalog(client)
        dsa = [slug for slug, meta in catalog.items() if meta.get("tag") == DSA_TAG]
        logger.info(
            "Catalog: %d entries, %d tagged %s; %d non-problem course entries skipped",
            len(catalog), len(dsa), DSA_TAG, len(catalog) - len(dsa),
        )

        async with async_session_maker() as db:
            problems = (
                await db.execute(select(Problem).where(Problem.source == "leetcode"))
            ).scalars().all()
            by_slug = {p.slug: p for p in problems}
            # Titles are not unique-constrained; first wins, deterministically
            # ordered so a re-run cannot pick a different row for the same title.
            by_title: dict[str, Problem] = {}
            for problem in sorted(problems, key=lambda p: p.external_id):
                by_title.setdefault(normalize(problem.title), problem)
            logger.info("LeetCode catalog: %d problems", len(problems))

            resolved, unresolved = await resolve(client, dsa, by_slug, by_title)
            logger.info("Resolved %d/%d (%.1f%%)", len(resolved), len(dsa), 100 * len(resolved) / max(len(dsa), 1))

            await sync(db, resolved, commit=args.commit)

    if unresolved:
        # Never a silent cap: an unresolved slug means a real solve on that
        # problem will be logged as evidence_unmapped and move no node.
        logger.warning("%d unresolved — add to OVERRIDES if they are renames:", len(unresolved))
        for slug in sorted(unresolved):
            logger.warning("    %s", slug)

    if not args.commit:
        logger.info("DRY RUN — nothing written. Re-run with --commit to apply.")


if __name__ == "__main__":
    asyncio.run(main())
