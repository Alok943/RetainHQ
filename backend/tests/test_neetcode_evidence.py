"""Producer C — NeetCode solve evidence endpoint.

Mirrors test_leetcode_evidence.py's /solve coverage (same shared
_record_verified_solve helper underneath, same honesty defaults), plus the
one behavior that is NEW as of NeetCode existing at all: Problem lookups must
be scoped by `source`, not just `slug` — see evidence.py's
_record_verified_solve docstring for why an unscoped lookup was a real, if
previously invisible, bug.
"""
import uuid

import pytest
from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.models import LearningEvent, Problem, ProblemConcept, Roadmap, RoadmapNode
from tests.conftest import USER_A


@pytest.fixture
async def dsa_node(db: AsyncSession) -> RoadmapNode:
    roadmap = Roadmap(title="DSA", audience="career", slug="dsa")
    db.add(roadmap)
    await db.commit()
    node = RoadmapNode(roadmap_id=roadmap.id, phase="1", section="1", title="Two Pointers")
    db.add(node)
    await db.commit()
    return node


@pytest.fixture
async def mapped_neetcode_problem(db: AsyncSession, dsa_node: RoadmapNode) -> Problem:
    problem = Problem(
        source="neetcode",
        external_id=1,
        slug="two-integer-sum",
        title="Two Sum",
        difficulty="easy",
        catalog_version="v1",
    )
    db.add(problem)
    await db.commit()
    db.add(ProblemConcept(
        problem_id=problem.id,
        node_id=dsa_node.id,
        role="primary",
        confidence=1.0,
        mapping_version="v1",
    ))
    await db.commit()
    return problem


async def _events(db: AsyncSession, user_id: str) -> list[LearningEvent]:
    rows = await db.execute(
        select(LearningEvent).where(LearningEvent.user_id == uuid.UUID(user_id))
    )
    return list(rows.scalars().all())


async def test_solve_records_event_with_catalog_difficulty(
    client: AsyncClient, db: AsyncSession, mapped_neetcode_problem: Problem, dsa_node: RoadmapNode
):
    resp = await client.post("/api/evidence/neetcode/solve", json={
        "problem_slug": "two-integer-sum",
        "duration_min": 15,
        "occurred_at": "2026-08-02T10:00:00Z",
        "difficulty": "hard",  # client can't be trusted — catalog says easy
    })
    assert resp.status_code == 204

    events = await _events(db, USER_A.id)
    assert len(events) == 1
    ev = events[0]
    assert ev.event_type == "PROBLEM_SOLVED"
    assert ev.trust_tier == "T1_verified_external"
    assert ev.source == "neetcode"
    assert ev.node_id == dsa_node.id
    assert ev.difficulty == "easy", "difficulty must come from the catalog, not the client"
    assert ev.outcome == "pass"


async def test_solve_without_reflection_understates_assistance(
    client: AsyncClient, db: AsyncSession, mapped_neetcode_problem: Problem
):
    resp = await client.post("/api/evidence/neetcode/solve", json={"problem_slug": "two-integer-sum"})
    assert resp.status_code == 204
    ev = (await _events(db, USER_A.id))[0]
    assert ev.assistance == "llm_assisted"


async def test_solve_is_idempotent_per_problem(
    client: AsyncClient, db: AsyncSession, mapped_neetcode_problem: Problem
):
    for _ in range(3):
        resp = await client.post("/api/evidence/neetcode/solve", json={"problem_slug": "two-integer-sum"})
        assert resp.status_code == 204
    assert len(await _events(db, USER_A.id)) == 1


async def test_solve_unknown_slug_is_logged_unmapped_with_neetcode_source(
    client: AsyncClient, db: AsyncSession
):
    resp = await client.post("/api/evidence/neetcode/solve", json={
        "problem_slug": "not-in-our-catalog", "duration_min": 20,
    })
    assert resp.status_code == 204
    assert await _events(db, USER_A.id) == []

    from app.models.models import MetricEvent
    metrics = (await db.execute(
        select(MetricEvent).where(MetricEvent.event_type == "evidence_unmapped")
    )).scalars().all()
    assert len(metrics) == 1
    assert metrics[0].payload["source"] == "neetcode"


# --------------------------------------------------------------------------
# The scoping fix — a shared slug across sources must never cross-attribute
# --------------------------------------------------------------------------

async def test_same_slug_different_source_does_not_cross_attribute(
    client: AsyncClient, db: AsyncSession, dsa_node: RoadmapNode
):
    """The regression this session's fix targets directly: before Problem
    lookups were source-scoped, a NeetCode solve whose slug happened to match
    a LeetCode catalog row (or vice versa) could silently log evidence against
    the WRONG catalog problem — and therefore the wrong node, with the wrong
    catalog difficulty. Two problems sharing the literal slug "same-slug",
    one per source, each mapped to a DIFFERENT node, proves each endpoint
    only ever sees its own.
    """
    roadmap = (await db.execute(select(Roadmap).where(Roadmap.slug == "dsa"))).scalars().first()
    other_node = RoadmapNode(roadmap_id=roadmap.id, phase="1", section="2", title="Sliding Window")
    db.add(other_node)
    await db.commit()

    lc_problem = Problem(
        source="leetcode", external_id=101, slug="same-slug",
        title="LeetCode Version", difficulty="hard", catalog_version="v1",
    )
    nc_problem = Problem(
        source="neetcode", external_id=202, slug="same-slug",
        title="NeetCode Version", difficulty="easy", catalog_version="v1",
    )
    db.add(lc_problem)
    db.add(nc_problem)
    await db.commit()
    db.add(ProblemConcept(problem_id=lc_problem.id, node_id=dsa_node.id, role="primary", confidence=1.0, mapping_version="v1"))
    db.add(ProblemConcept(problem_id=nc_problem.id, node_id=other_node.id, role="primary", confidence=1.0, mapping_version="v1"))
    await db.commit()

    await client.post("/api/evidence/leetcode/solve", json={"problem_slug": "same-slug"})
    await client.post("/api/evidence/neetcode/solve", json={"problem_slug": "same-slug"})

    events = await _events(db, USER_A.id)
    assert len(events) == 2, "one event per source, not deduped/merged across sources"

    by_source = {e.source: e for e in events}
    assert by_source["leetcode"].node_id == dsa_node.id
    assert by_source["leetcode"].difficulty == "hard"
    assert by_source["neetcode"].node_id == other_node.id
    assert by_source["neetcode"].difficulty == "easy"
