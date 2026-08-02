"""Alias resolution — a NeetCode solve credited to the LeetCode catalog row.

The design this covers (D-071): NeetCode has NO catalog rows of its own.
Its problems are LeetCode's re-slugged, so `two-integer-sum` resolves through
`problem_aliases` to the existing Two Sum row and inherits the roadmap-node
mapping the curated LeetCode pass already produced.

What must hold, and what each test here pins down:
  - a NeetCode solve moves the SAME node a LeetCode solve on that problem does
  - a site's own slug always beats an alias (LeetCode is unaffected by any of this)
  - an alias cannot leak across sources
  - an unaliased slug stays a visible gap, never silently-wrong mastery
"""
import uuid

import pytest
from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.models import (
    LearningEvent, MetricEvent, Problem, ProblemAlias, ProblemConcept, Roadmap, RoadmapNode,
)
from tests.conftest import USER_A


@pytest.fixture
async def node(db: AsyncSession) -> RoadmapNode:
    roadmap = Roadmap(title="DSA", audience="career", slug="dsa")
    db.add(roadmap)
    await db.commit()
    node = RoadmapNode(roadmap_id=roadmap.id, phase="1", section="1", title="Hash tables")
    db.add(node)
    await db.commit()
    return node


@pytest.fixture
async def leetcode_two_sum(db: AsyncSession, node: RoadmapNode) -> Problem:
    """A LeetCode catalog row WITH a curated primary mapping — the thing an
    alias exists to reuse."""
    problem = Problem(
        source="leetcode", external_id=1, slug="two-sum", title="Two Sum",
        difficulty="easy", catalog_version="v1",
    )
    db.add(problem)
    await db.commit()
    db.add(ProblemConcept(
        problem_id=problem.id, node_id=node.id, role="primary",
        confidence=1.0, mapping_version="v1.2",
    ))
    await db.commit()
    return problem


@pytest.fixture
async def neetcode_alias(db: AsyncSession, leetcode_two_sum: Problem) -> ProblemAlias:
    alias = ProblemAlias(
        problem_id=leetcode_two_sum.id, source="neetcode",
        alias_slug="two-integer-sum", resolved_by="title_match",
    )
    db.add(alias)
    await db.commit()
    return alias


async def _events(db: AsyncSession) -> list[LearningEvent]:
    rows = await db.execute(select(LearningEvent).where(LearningEvent.user_id == uuid.UUID(USER_A.id)))
    return list(rows.scalars().all())


async def test_neetcode_solve_credits_the_leetcode_problems_node(
    client: AsyncClient, db: AsyncSession, node: RoadmapNode, neetcode_alias: ProblemAlias
):
    """The whole point: no NeetCode catalog, no NeetCode curation pass, and the
    solve still lands on a real node."""
    res = await client.post(
        "/api/evidence/neetcode/solve",
        json={"problem_slug": "two-integer-sum", "submission_id": "nc-1", "duration_min": 12},
    )
    assert res.status_code == 204

    events = await _events(db)
    assert len(events) == 1
    assert events[0].node_id == node.id
    # Source stays truthful about WHERE it was solved even though the problem
    # row it points at is LeetCode's.
    assert events[0].source == "neetcode"
    assert events[0].trust_tier == "T1_verified_external"


async def test_difficulty_comes_from_the_aliased_catalog_row(
    client: AsyncClient, db: AsyncSession, neetcode_alias: ProblemAlias
):
    """The weight table is keyed on (difficulty, assistance); reading difficulty
    off the resolved LeetCode row is what makes an aliased solve score the same
    as the native one rather than falling back to the medium default."""
    await client.post(
        "/api/evidence/neetcode/solve",
        json={"problem_slug": "two-integer-sum", "submission_id": "nc-2", "needed_hint": False},
    )
    events = await _events(db)
    assert events[0].difficulty == "easy"
    assert events[0].assistance == "none"


async def test_a_native_row_beats_an_alias(
    client: AsyncClient, db: AsyncSession, node: RoadmapNode, leetcode_two_sum: Problem
):
    """A site's own catalog row wins. Pinned because the fallback order is the
    only thing stopping an alias from shadowing a real row, and nothing else in
    the type system enforces it."""
    native = Problem(
        source="neetcode", external_id=2, slug="shared-slug", title="Native NeetCode",
        difficulty="hard", catalog_version="v1",
    )
    db.add(native)
    await db.commit()
    db.add(ProblemConcept(
        problem_id=native.id, node_id=node.id, role="primary", confidence=1.0, mapping_version="v1",
    ))
    # An alias that would point the same slug at the LeetCode row instead.
    db.add(ProblemAlias(
        problem_id=leetcode_two_sum.id, source="neetcode",
        alias_slug="shared-slug", resolved_by="title_match",
    ))
    await db.commit()

    await client.post(
        "/api/evidence/neetcode/solve",
        json={"problem_slug": "shared-slug", "submission_id": "nc-3"},
    )
    events = await _events(db)
    # 'hard' is the native row's difficulty; the aliased LeetCode row is 'easy'.
    assert events[0].difficulty == "hard"


async def test_an_alias_does_not_leak_to_another_source(
    client: AsyncClient, db: AsyncSession, neetcode_alias: ProblemAlias
):
    """A NeetCode alias must not make `two-integer-sum` resolvable via the
    LeetCode endpoint — aliases are scoped to the site they describe."""
    res = await client.post(
        "/api/evidence/leetcode/solve",
        json={"problem_slug": "two-integer-sum", "submission_id": "lc-1"},
    )
    assert res.status_code == 204
    assert await _events(db) == []

    unmapped = (await db.execute(
        select(MetricEvent).where(MetricEvent.event_type == "evidence_unmapped")
    )).scalars().all()
    assert len(unmapped) == 1


async def test_an_unaliased_slug_stays_a_visible_gap(
    client: AsyncClient, db: AsyncSession, leetcode_two_sum: Problem
):
    """~7% of NeetCode's catalog resolves to nothing (renames the OVERRIDES list
    hasn't caught). Those must record evidence_unmapped, not get attached to
    some near-miss node — understate, never overstate."""
    res = await client.post(
        "/api/evidence/neetcode/solve",
        json={"problem_slug": "some-neetcode-only-slug", "submission_id": "nc-4"},
    )
    assert res.status_code == 204
    assert await _events(db) == []

    unmapped = (await db.execute(
        select(MetricEvent).where(MetricEvent.event_type == "evidence_unmapped")
    )).scalars().all()
    assert len(unmapped) == 1
    assert unmapped[0].payload["source"] == "neetcode"


async def test_leetcode_solves_are_untouched_by_the_alias_table(
    client: AsyncClient, db: AsyncSession, node: RoadmapNode, neetcode_alias: ProblemAlias
):
    """Regression guard: adding the alias fallback must not change the LeetCode
    path at all, since that path always hits the native branch first."""
    res = await client.post(
        "/api/evidence/leetcode/solve",
        json={"problem_slug": "two-sum", "submission_id": "lc-2"},
    )
    assert res.status_code == 204
    events = await _events(db)
    assert len(events) == 1
    assert events[0].source == "leetcode"
    assert events[0].node_id == node.id
