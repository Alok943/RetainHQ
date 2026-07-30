import asyncio
import json
import logging
import os
import re
import uuid
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import select

from app.core.database import async_session_maker
from app.models.models import Problem, ProblemConcept, Roadmap, RoadmapNode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CONTENT_DIR = Path(__file__).parent.parent.parent / "content" / "leetcode-catalog"

# Teaching-scaffold slugs — content/PROMPT-leetcode-mapping.md §"NOT EVERY SLUG IS
# A LEGAL primary". They explain fundamentals; they do not name a problem-solving
# pattern. Legal as `supporting`, NEVER as `primary`.
#
# The v1 run violated this 66 times (28 at confidence 0.9) and nothing caught it,
# because the contract lived only in the prompt. #418 Sentence Screen Fitting came
# back as "String traversal", #326 Power of Three as "Base case". Fixed by
# scripts/sql/2026-07-30_fix_scaffold_primaries.sql; enforced here so the next
# mapping run cannot reintroduce it.
SCAFFOLD_SLUGS = frozenset({
    "amortized-analysis", "arrays-and-memory", "base-case", "big-o-notation",
    "brute-force-first", "common-complexities", "counting-operations",
    "graph-representations", "hash-sets-vs-maps", "in-place-operations",
    "iteration-and-traversal", "linear-search", "logarithms-and-powers-of-two",
    "optimal-substructure", "overlapping-subproblems", "pattern-recognition-drill",
    "precomputation", "recognizing-divide-and-conquer", "recognizing-graph-problems",
    "recognizing-greedy-vs-dp", "recognizing-sliding-window", "recognizing-two-pointers",
    "string-traversal", "the-call-stack", "tracing-state-and-invariants",
    "what-is-an-algorithm",
})

async def import_catalog(db: AsyncSession):
    catalog_path = CONTENT_DIR / "catalog.v1.json"
    if not catalog_path.exists():
        logger.error(f"Catalog file not found: {catalog_path}")
        return

    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog_data = json.load(f)

    catalog_version = catalog_data.get("catalog_version", "v1")
    problems_data = catalog_data.get("problems", [])

    logger.info(f"Importing {len(problems_data)} problems from {catalog_path}")

    # Process in batches to avoid overwhelming memory/DB
    batch_size = 500
    upserted = 0

    # One query instead of a SELECT per problem. At 3999 problems that removed
    # ~4000 sequential round trips to Mumbai from every run, including re-runs
    # (this loop is idempotent, so a resumed import used to pay the full cost
    # again just to discover it had nothing to do).
    existing_problems = {
        (p.source, p.external_id): p
        for p in (await db.execute(select(Problem))).scalars().all()
    }
    logger.info(f"Preloaded {len(existing_problems)} existing problems")

    for i in range(0, len(problems_data), batch_size):
        batch = problems_data[i:i + batch_size]
        for p_data in batch:
            problem = existing_problems.get((p_data["source"], p_data["external_id"]))

            if not problem:
                problem = Problem(
                    source=p_data["source"],
                    external_id=p_data["external_id"],
                    slug=p_data["slug"],
                    title=p_data["title"],
                    difficulty=p_data["difficulty"],
                    tags=p_data.get("tags", []),
                    url=p_data.get("url"),
                    acceptance=p_data.get("acceptance"),
                    catalog_version=catalog_version
                )
                db.add(problem)
                existing_problems[(p_data["source"], p_data["external_id"])] = problem
            else:
                problem.slug = p_data["slug"]
                problem.title = p_data["title"]
                problem.difficulty = p_data["difficulty"]
                problem.tags = p_data.get("tags", [])
                problem.url = p_data.get("url")
                problem.acceptance = p_data.get("acceptance")
                problem.catalog_version = catalog_version
            upserted += 1
        
        await db.commit()
        logger.info(f"Committed batch up to {i + len(batch)}")

    logger.info(f"Upserted {upserted} problems.")

    # Import mapping if exists
    mapping_path = CONTENT_DIR / "mapping.v1.json"
    if mapping_path.exists():
        with open(mapping_path, "r", encoding="utf-8") as f:
            raw_mapping = json.load(f)

        # mapping.v1.json is an OBJECT with provenance (mapping_version, model,
        # prompt_version, generated_at, counts) wrapping the `mappings` list - not a
        # bare list. Iterating the object yields its 7 KEY STRINGS, so the loop below
        # used to die on `m_data["external_id"]` with "string indices must be integers"
        # after every problem had already been committed. Accept both shapes.
        if isinstance(raw_mapping, dict):
            mapping_data = raw_mapping["mappings"]
        else:
            mapping_data = raw_mapping

        logger.info(f"Importing {len(mapping_data)} problem concepts from {mapping_path}")
        
        # Resolve mapping-vocabulary slug -> node_id.
        #
        # NOT via NodeMeta.stable_key: node_meta rows exist ONLY for career-tree nodes
        # (see its model docstring). All 126 DSA catalog nodes have zero node_meta rows,
        # so that lookup resolves nothing and every mapping silently lands unmapped.
        #
        # Catalog roadmap_nodes have no slug column at all, so TITLE is the only join key
        # available - the same convention seed_*_prereqs.py already uses. The slug->title
        # table is checked in at content/leetcode-catalog/node_slug_map.json (verified
        # 124/124 against prod, no ambiguity under normalization).
        slug_map_path = CONTENT_DIR / "node_slug_map.json"
        if not slug_map_path.exists():
            raise RuntimeError(
                f"{slug_map_path} is missing - cannot resolve concept slugs to nodes. "
                "Regenerate it before importing mappings."
            )
        with open(slug_map_path, "r", encoding="utf-8") as f:
            slug_to_title = json.load(f)["slug_to_node_title"]

        def _norm(t: str) -> str:
            return re.sub(r"\s+", " ", t).strip().lower()

        # The generator emits a confidence BAND, not a number, but
        # ProblemConcept.confidence is a float column - passing "high" straight
        # through fails at insert time. Bands are the source of truth; these floats
        # are just their storage form, so keep the ladder here rather than inventing
        # precision the classifier never had.
        _CONFIDENCE_BANDS = {"high": 0.9, "medium": 0.6, "low": 0.3}

        def _confidence(raw) -> float:
            if isinstance(raw, (int, float)):
                return float(raw)
            return _CONFIDENCE_BANDS.get(raw, 0.6)

        # Sentinel for the deliberate out-of-scope bucket (spec 3.2.0) - a problem the
        # classifier judged unmappable to our closed vocabulary. Distinct from a slug
        # that SHOULD resolve but doesn't, which is a vocabulary bug worth shouting about.
        _OUT_OF_SCOPE = "out_of_scope"

        dsa_roadmap_id = (await db.execute(
            select(Roadmap.id).where(Roadmap.slug == "dsa")
        )).scalar_one_or_none()
        if dsa_roadmap_id is None:
            raise RuntimeError("No roadmap with slug 'dsa' - cannot resolve concept nodes.")

        nodes = (await db.execute(
            select(RoadmapNode).where(RoadmapNode.roadmap_id == dsa_roadmap_id)
        )).scalars().all()
        title_to_node_id: dict[str, uuid.UUID] = {}
        for n in nodes:
            title_to_node_id.setdefault(_norm(n.title), n.id)

        slug_to_node_id = {}
        unresolved_slugs = []
        for slug, title in slug_to_title.items():
            node_id = title_to_node_id.get(_norm(title))
            if node_id is None:
                unresolved_slugs.append(f"{slug} -> {title!r}")
            else:
                slug_to_node_id[slug] = node_id

        # Fail loudly. A partially-resolved vocabulary produces a mapping that looks
        # imported but is quietly missing whole concepts - the exact failure mode this
        # phase has already hit twice.
        if unresolved_slugs:
            raise RuntimeError(
                f"{len(unresolved_slugs)} of {len(slug_to_title)} concept slugs do not "
                f"resolve to a seeded DSA node. Seed the missing nodes (or fix "
                f"node_slug_map.json) before importing:\n  "
                + "\n  ".join(sorted(unresolved_slugs))
            )
        logger.info(f"Resolved {len(slug_to_node_id)}/{len(slug_to_title)} concept slugs to DSA nodes")

        # Also need external_id -> problem_id
        problems = (await db.execute(select(Problem))).scalars().all()
        ext_to_prob_id = {p.external_id: p.id for p in problems}

        # Preload the whole (problem_id, node_id) -> row index ONCE. The previous
        # shape issued a SELECT per candidate mapping and then a lone commit at the
        # very end: ~10k sequential round trips to the Mumbai pooler holding one
        # transaction open for half an hour, where any blip discarded every row.
        # One query + periodic commits turns that into minutes, and makes a
        # re-run resumable because the upsert is idempotent.
        existing_pcs = {
            (pc.problem_id, pc.node_id): pc
            for pc in (await db.execute(select(ProblemConcept))).scalars().all()
        }
        logger.info(f"Preloaded {len(existing_pcs)} existing problem_concepts")

        concepts_upserted = 0
        out_of_scope = 0
        unknown_slugs: dict[str, int] = {}
        scaffold_primaries: dict[str, int] = {}
        for processed, m_data in enumerate(mapping_data, start=1):
            if processed % 250 == 0:
                await db.commit()
                logger.info(f"Committed concepts through mapping {processed}/{len(mapping_data)}")
            problem_id = ext_to_prob_id.get(m_data["external_id"])
            if not problem_id:
                logger.warning(f"Problem {m_data['external_id']} not found, skipping concept mapping")
                continue

            # Count the buckets before mapping so a silently-empty import is
            # impossible to mistake for a successful one.
            _p = m_data.get("primary")
            if _p == _OUT_OF_SCOPE:
                out_of_scope += 1
            elif _p in SCAFFOLD_SLUGS:
                # Collected, not raised here — one report of every offender beats
                # failing on the first and re-running to discover the next.
                scaffold_primaries[_p] = scaffold_primaries.get(_p, 0) + 1
            elif _p and _p not in slug_to_node_id:
                unknown_slugs[_p] = unknown_slugs.get(_p, 0) + 1

            # Map primary concept. A scaffold slug is skipped outright: writing it
            # and cleaning up later is how the 66 bad rows reached prod.
            primary_slug = m_data.get("primary")
            if primary_slug in SCAFFOLD_SLUGS:
                primary_slug = None
            if primary_slug and primary_slug in slug_to_node_id:
                node_id = slug_to_node_id[primary_slug]
                pc = existing_pcs.get((problem_id, node_id))
                if not pc:
                    pc = ProblemConcept(
                        problem_id=problem_id,
                        node_id=node_id,
                        role="primary",
                        confidence=_confidence(m_data.get("confidence")),
                        reviewed_by=m_data.get("reviewed_by"),
                        mapping_version="v1"
                    )
                    db.add(pc)
                    # Register immediately: a problem whose `primary` and one of its
                    # `alternatives` resolve to the SAME node would otherwise insert
                    # twice and trip uq_problem_concept.
                    existing_pcs[(problem_id, node_id)] = pc
                else:
                    pc.role = "primary"
                    pc.confidence = _confidence(m_data.get("confidence"))
                    pc.reviewed_by = m_data.get("reviewed_by")
                    pc.mapping_version = "v1"
                
                concepts_upserted += 1

            # Map alternatives / supporting
            for role_type in ["alternatives", "supporting"]:
                for alt_slug in m_data.get(role_type, []):
                    if alt_slug in slug_to_node_id:
                        node_id = slug_to_node_id[alt_slug]
                        pc = existing_pcs.get((problem_id, node_id))
                        if not pc:
                            pc = ProblemConcept(
                                problem_id=problem_id,
                                node_id=node_id,
                                role="supporting" if role_type == "supporting" else "alternative",
                                confidence=0.8, # fallback
                                mapping_version="v1"
                            )
                            db.add(pc)
                            existing_pcs[(problem_id, node_id)] = pc
                        concepts_upserted += 1
                        
        await db.commit()
        logger.info(
            f"Upserted {concepts_upserted} problem concepts "
            f"({out_of_scope} problems deliberately out-of-scope)."
        )

        # Same reasoning as the unresolved-slug guard above: a mapping that looks
        # imported but quietly dropped whole concepts is the failure this phase has
        # already hit twice. An unrecognised primary slug is a vocabulary drift bug,
        # not an out-of-scope problem, so refuse to exit 0 on it.
        # A scaffold slug as `primary` is a contract violation, not a data quirk:
        # it puts a "what is Big-O" node in front of a learner as the thing a
        # problem taught them, and it silently pollutes the concept the Log
        # Activity chip auto-fills. Refuse the import rather than clean up after.
        if scaffold_primaries:
            raise RuntimeError(
                f"{sum(scaffold_primaries.values())} problems name a TEACHING-SCAFFOLD "
                "concept as `primary`. PROMPT-leetcode-mapping.md forbids this - if "
                "nothing else fits, the answer is 'out_of_scope'. Their primary was "
                "skipped; re-run the mapping for these before trusting the import:\n  "
                + "\n  ".join(f"{s} ({n} problems)" for s, n in sorted(scaffold_primaries.items()))
            )
        if unknown_slugs:
            raise RuntimeError(
                f"{sum(unknown_slugs.values())} problems name a primary concept that is "
                f"neither in node_slug_map.json nor the '{_OUT_OF_SCOPE}' bucket - their "
                "mappings were silently skipped. Fix the vocabulary before trusting this "
                "import:\n  "
                + "\n  ".join(f"{s} ({n} problems)" for s, n in sorted(unknown_slugs.items()))
            )
        if concepts_upserted == 0:
            raise RuntimeError(
                "Mapping file was read but produced ZERO problem_concepts. Every LeetCode "
                "solve would be logged as evidence_unmapped and the feature would look "
                "healthy while recording nothing."
            )
    else:
        logger.info(f"No mapping file found at {mapping_path}, skipping problem_concepts")


async def main():
    """Prefer a dedicated bulk-import connection when one is configured.

    The app's DATABASE_URL is Supabase's TRANSACTION pooler (:6543), which is
    built for short web-request transactions and terminates long ones — on
    2026-07-26 it killed this import mid-run with WinError 10054 after ~39
    minutes, discarding all 5084 pending concept rows. Bulk work belongs on the
    SESSION pooler (:5432, user postgres.<ref>), same connection the backup
    runbook uses. Set IMPORT_DATABASE_URL to it:

        postgresql+asyncpg://postgres.<ref>:<pw>@aws-1-ap-south-1.pooler.supabase.com:5432/postgres

    Without it the script still runs on the app connection — the periodic
    commits above keep each transaction short enough that this is survivable,
    and the upsert is idempotent so a killed run resumes on re-run.
    """
    # os.environ alone is not enough: pydantic-settings reads backend/.env without
    # exporting it into the process environment, so a value the owner sensibly put
    # in .env next to DATABASE_URL would be silently ignored. Check both.
    import_url = os.getenv("IMPORT_DATABASE_URL")
    if not import_url:
        try:
            from dotenv import dotenv_values
            import_url = dotenv_values(Path(__file__).parent.parent / ".env").get("IMPORT_DATABASE_URL")
        except ImportError:
            pass
    if not import_url:
        logger.warning(
            "IMPORT_DATABASE_URL not set — using the app's transaction pooler. "
            "This works but is what dropped the 2026-07-26 run; re-run on failure, it resumes."
        )
        async with async_session_maker() as db:
            await import_catalog(db)
        return

    logger.info("Using IMPORT_DATABASE_URL (dedicated bulk-import connection)")
    engine = create_async_engine(
        import_url,
        pool_pre_ping=True,
        connect_args={"prepared_statement_cache_size": 0, "statement_cache_size": 0},
    )
    try:
        async with async_sessionmaker(engine, expire_on_commit=False)() as db:
            await import_catalog(db)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
