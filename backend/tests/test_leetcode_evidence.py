"""Producer C — LeetCode solve/backfill evidence endpoints.

Rewritten 2026-07-26. The original version overrode `get_current_user` on the
shared `app` object at MODULE IMPORT time and never overrode `get_db`, so it
(a) hit whatever real database `DATABASE_URL` pointed at — failing with
ConnectionRefused rather than testing anything — and (b) leaked its auth
override into every other test module in the session. Both endpoints therefore
shipped with zero working coverage. This version uses the suite's own
`client`/`db`/`as_user` fixtures like the rest of the tests.

The behaviors worth pinning here are the honesty defaults: difficulty and
assistance are decided by OUR catalog and OUR fallback rules, never by the
client, because the weight table is keyed on that pair and a generous default
silently inflates mastery (ARCHITECTURE-learning-system.md §0).
"""
import uuid
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.models import LearningEvent, Problem, ProblemConcept, Roadmap, RoadmapNode
from tests.conftest import USER_A, USER_B


@pytest.fixture
async def dsa_node(db: AsyncSession) -> RoadmapNode:
    roadmap = Roadmap(title="DSA", audience="career", slug="dsa")
    db.add(roadmap)
    await db.commit()
    node = RoadmapNode(roadmap_id=roadmap.id, phase="1", section="1", title="Hash Maps")
    db.add(node)
    await db.commit()
    return node


@pytest.fixture
async def mapped_problem(db: AsyncSession, dsa_node: RoadmapNode) -> Problem:
    """A catalog problem with a primary concept mapping — the happy path."""
    problem = Problem(
        source="leetcode",
        external_id=1,
        slug="two-sum",
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


# --------------------------------------------------------------------------
# /leetcode/solve
# --------------------------------------------------------------------------

async def test_solve_records_event_with_catalog_difficulty(
    client: AsyncClient, db: AsyncSession, mapped_problem: Problem, dsa_node: RoadmapNode
):
    resp = await client.post("/api/evidence/leetcode/solve", json={
        "problem_slug": "two-sum",
        "duration_min": 12,
        "occurred_at": "2026-07-21T18:00:00Z",
        # A lie the client has no business being believed about — the catalog says easy.
        "difficulty": "hard",
    })
    assert resp.status_code == 204

    events = await _events(db, USER_A.id)
    assert len(events) == 1
    ev = events[0]
    assert ev.event_type == "PROBLEM_SOLVED"
    assert ev.trust_tier == "T1_verified_external"
    assert ev.source == "leetcode"
    assert ev.node_id == dsa_node.id
    assert ev.duration_min == 12
    assert ev.difficulty == "easy", "difficulty must come from the catalog, not the client"
    assert ev.outcome == "pass"
    # Naive-UTC in the DB, per repo convention.
    assert ev.occurred_at.tzinfo is None
    assert ev.occurred_at == datetime(2026, 7, 21, 18, 0, 0)


async def test_solve_without_reflection_understates_assistance(
    client: AsyncClient, db: AsyncSession, mapped_problem: Problem
):
    """The load-bearing honesty default: no reflection must NOT mean 'clean solve'."""
    resp = await client.post("/api/evidence/leetcode/solve", json={"problem_slug": "two-sum"})
    assert resp.status_code == 204

    ev = (await _events(db, USER_A.id))[0]
    assert ev.assistance == "llm_assisted", (
        "an unreflected solve must fall back to the understated default, not 'none' "
        "(the most generous row in the weight table)"
    )
    assert ev.payload["reflected"] is False


@pytest.mark.parametrize("needed_hint,expected", [(False, "none"), (True, "hint")])
async def test_solve_reflection_sets_assistance(
    client: AsyncClient, db: AsyncSession, mapped_problem: Problem, needed_hint, expected
):
    resp = await client.post("/api/evidence/leetcode/solve", json={
        "problem_slug": "two-sum", "needed_hint": needed_hint,
    })
    assert resp.status_code == 204

    ev = (await _events(db, USER_A.id))[0]
    assert ev.assistance == expected
    assert ev.payload["reflected"] is True


async def test_solve_is_idempotent_per_problem(
    client: AsyncClient, db: AsyncSession, mapped_problem: Problem
):
    """Re-solving the same problem must not farm mastery — entity_id is the key."""
    for _ in range(3):
        resp = await client.post("/api/evidence/leetcode/solve", json={"problem_slug": "two-sum"})
        assert resp.status_code == 204

    assert len(await _events(db, USER_A.id)) == 1


async def test_solve_unknown_slug_is_logged_unmapped_not_dropped(
    client: AsyncClient, db: AsyncSession
):
    resp = await client.post("/api/evidence/leetcode/solve", json={
        "problem_slug": "not-in-our-catalog", "duration_min": 30,
    })
    assert resp.status_code == 204
    # No learning event (we cannot attribute it to a node)...
    assert await _events(db, USER_A.id) == []
    # ...but the miss is counted, so catalog gaps are visible rather than silent.
    from app.models.models import MetricEvent
    metrics = (await db.execute(
        select(MetricEvent).where(MetricEvent.event_type == "evidence_unmapped")
    )).scalars().all()
    assert len(metrics) == 1
    assert metrics[0].payload["problem_slug"] == "not-in-our-catalog"


async def test_solve_problem_without_mapping_is_unmapped(
    client: AsyncClient, db: AsyncSession
):
    """In the catalog but unmapped to a concept — still no invented attribution."""
    db.add(Problem(
        source="leetcode", external_id=2, slug="orphan-problem",
        title="Orphan", difficulty="medium", catalog_version="v1",
    ))
    await db.commit()

    resp = await client.post("/api/evidence/leetcode/solve", json={"problem_slug": "orphan-problem"})
    assert resp.status_code == 204
    assert await _events(db, USER_A.id) == []


async def test_solve_is_scoped_to_the_calling_user(
    client: AsyncClient, db: AsyncSession, mapped_problem: Problem, as_user
):
    """IDOR guard: B's solve must never land on A's ledger (CLAUDE.md convention)."""
    await client.post("/api/evidence/leetcode/solve", json={"problem_slug": "two-sum"})

    as_user(USER_B)
    await client.post("/api/evidence/leetcode/solve", json={"problem_slug": "two-sum"})

    a_events = await _events(db, USER_A.id)
    b_events = await _events(db, USER_B.id)
    assert len(a_events) == 1
    assert len(b_events) == 1
    assert a_events[0].id != b_events[0].id


# --------------------------------------------------------------------------
# /leetcode/backfill
# --------------------------------------------------------------------------

async def test_backfill_maps_known_slugs_and_ignores_the_rest(
    client: AsyncClient, db: AsyncSession, mapped_problem: Problem, dsa_node: RoadmapNode
):
    resp = await client.post("/api/evidence/leetcode/backfill", json={
        "solved_slugs": ["two-sum", "does-not-exist"],
    })
    assert resp.status_code == 204

    events = await _events(db, USER_A.id)
    assert len(events) == 1
    assert events[0].node_id == dsa_node.id
    assert events[0].payload["backfilled"] is True


async def test_backfill_uses_catalog_difficulty_and_understated_assistance(
    client: AsyncClient, db: AsyncSession, mapped_problem: Problem
):
    """Regression: backfill previously passed assistance='none' and no difficulty,
    inflating every historically-solved problem at import time — the exact
    opposite of the rule /solve documents."""
    resp = await client.post("/api/evidence/leetcode/backfill", json={"solved_slugs": ["two-sum"]})
    assert resp.status_code == 204

    ev = (await _events(db, USER_A.id))[0]
    assert ev.difficulty == "easy"
    assert ev.assistance == "llm_assisted"


async def test_backfill_empty_payload_is_a_noop(client: AsyncClient, db: AsyncSession):
    resp = await client.post("/api/evidence/leetcode/backfill", json={"solved_slugs": []})
    assert resp.status_code == 204
    assert await _events(db, USER_A.id) == []


async def test_backfill_then_solve_does_not_double_count(
    client: AsyncClient, db: AsyncSession, mapped_problem: Problem
):
    """Onboarding backfill followed by a live re-solve is the common real sequence."""
    await client.post("/api/evidence/leetcode/backfill", json={"solved_slugs": ["two-sum"]})
    await client.post("/api/evidence/leetcode/solve", json={"problem_slug": "two-sum"})

    assert len(await _events(db, USER_A.id)) == 1
