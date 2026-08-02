"""NeetCode's completed-problem import — the T3 path.

This endpoint exists because `getCompletedProblems` (confirmed live 2026-08-02)
returns LeetCode URLs for problems the user marked complete on neetcode.io. What
it CANNOT tell us is whether any of them was actually judged, which is the whole
reason its trust tier differs from every other backfill in this codebase. These
tests pin that difference down, because "make it consistent with the LeetCode
one" is the obvious and wrong refactor.
"""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.models import LearningEvent, NodeMastery, Problem, ProblemConcept, Roadmap, RoadmapNode
from app.services.evidence_weights import T3_EXPOSURE_CAP
from tests.conftest import USER_A


@pytest.fixture
async def node(db: AsyncSession) -> RoadmapNode:
    roadmap = Roadmap(title="DSA", audience="career", slug="dsa")
    db.add(roadmap)
    await db.commit()
    node = RoadmapNode(roadmap_id=roadmap.id, phase="1", section="1", title="Two Pointers")
    db.add(node)
    await db.commit()
    return node


@pytest.fixture
async def problems(db: AsyncSession, node: RoadmapNode) -> list[Problem]:
    rows = [
        Problem(source="leetcode", external_id=i, slug=slug, title=slug,
                difficulty=diff, catalog_version="v1")
        for i, (slug, diff) in enumerate(
            [("valid-palindrome", "easy"), ("3sum", "medium"), ("trapping-rain-water", "hard")], start=1
        )
    ]
    for p in rows:
        db.add(p)
    await db.commit()
    for p in rows:
        db.add(ProblemConcept(problem_id=p.id, node_id=node.id, role="primary",
                              confidence=1.0, mapping_version="v1.2"))
    await db.commit()
    return rows


async def _events(db: AsyncSession) -> list[LearningEvent]:
    rows = await db.execute(select(LearningEvent).where(LearningEvent.user_id == uuid.UUID(USER_A.id)))
    return list(rows.scalars().all())


async def test_completions_are_T3_not_T1(client: AsyncClient, db: AsyncSession, problems: list[Problem]):
    """getCompletedProblems proves engagement, not a judged run — a 'completed'
    entry may be a checkbox ticked after solving on LeetCode, or after reading
    the solution. Nothing distinguishes them, so it cannot claim T1."""
    res = await client.post(
        "/api/evidence/neetcode/backfill",
        json={"leetcode_slugs": ["valid-palindrome", "3sum", "trapping-rain-water"]},
    )
    assert res.status_code == 204

    events = await _events(db)
    assert len(events) == 3
    assert {e.trust_tier for e in events} == {"T3_observed"}
    assert {e.source for e in events} == {"neetcode"}


async def test_the_whole_import_cannot_lift_a_node_past_the_exposure_cap(
    client: AsyncClient, db: AsyncSession, node: RoadmapNode, problems: list[Problem]
):
    """The load-bearing consequence of T3. Three solves including a hard one
    would comfortably clear 0.35 at T1; capped, they cannot. This is what stops
    a checkbox list from reading as mastery."""
    await client.post(
        "/api/evidence/neetcode/backfill",
        json={"leetcode_slugs": ["valid-palindrome", "3sum", "trapping-rain-water"]},
    )
    mastery = (await db.execute(
        select(NodeMastery).where(NodeMastery.user_id == uuid.UUID(USER_A.id), NodeMastery.node_id == node.id)
    )).scalars().one()
    assert 0 < mastery.m_learned <= T3_EXPOSURE_CAP


async def test_difficulty_comes_from_the_catalog_and_assistance_is_understated(
    client: AsyncClient, db: AsyncSession, problems: list[Problem]
):
    await client.post("/api/evidence/neetcode/backfill", json={"leetcode_slugs": ["3sum"]})
    event = (await _events(db))[0]
    assert event.difficulty == "medium"
    # NOT "none" — we know nothing about how it was solved, and "none" is the
    # most generous row in the weight table.
    assert event.assistance == "llm_assisted"


async def test_uses_the_supplied_earliest_activity_date(
    client: AsyncClient, db: AsyncSession, problems: list[Problem]
):
    """NeetCode has no per-problem completion date, so the extension sends the
    user's EARLIEST activity date for the whole batch. Landing these on today
    would claim they were just learned — the exact bug the LeetCode import was
    fixed for."""
    long_ago = datetime(2026, 2, 17, tzinfo=timezone.utc)
    await client.post(
        "/api/evidence/neetcode/backfill",
        json={"leetcode_slugs": ["3sum"], "occurred_at": long_ago.isoformat()},
    )
    event = (await _events(db))[0]
    assert event.occurred_at.tzinfo is None  # naive-UTC, per repo convention
    assert event.occurred_at.date() == long_ago.date()


async def test_clamps_a_future_date(client: AsyncClient, db: AsyncSession, problems: list[Problem]):
    future = datetime.utcnow() + timedelta(days=400)
    await client.post(
        "/api/evidence/neetcode/backfill",
        json={"leetcode_slugs": ["3sum"], "occurred_at": future.isoformat()},
    )
    event = (await _events(db))[0]
    assert event.occurred_at <= datetime.utcnow()


async def test_reimporting_does_not_double_count(client: AsyncClient, db: AsyncSession, problems: list[Problem]):
    """Idempotency is problem-scoped, so pressing Import twice cannot farm
    mastery — the same guarantee the LeetCode backfill has."""
    for _ in range(2):
        await client.post("/api/evidence/neetcode/backfill", json={"leetcode_slugs": ["3sum"]})
    assert len(await _events(db)) == 1


async def test_unknown_and_unmapped_slugs_are_skipped_not_guessed(
    client: AsyncClient, db: AsyncSession, problems: list[Problem]
):
    unmapped = Problem(source="leetcode", external_id=99, slug="lonely-problem",
                       title="Lonely", difficulty="easy", catalog_version="v1")
    db.add(unmapped)
    await db.commit()

    res = await client.post(
        "/api/evidence/neetcode/backfill",
        json={"leetcode_slugs": ["3sum", "lonely-problem", "not-in-our-catalog-at-all"]},
    )
    assert res.status_code == 204
    events = await _events(db)
    assert len(events) == 1
    assert events[0].payload["problem_slug"] == "3sum"


async def test_empty_list_is_a_no_op(client: AsyncClient, db: AsyncSession):
    res = await client.post("/api/evidence/neetcode/backfill", json={"leetcode_slugs": []})
    assert res.status_code == 204
    assert await _events(db) == []


async def test_t3_import_cannot_drag_down_a_node_t1_evidence_already_raised(
    client: AsyncClient, db: AsyncSession, node: RoadmapNode, problems: list[Problem]
):
    """apply_event_weight's max(before, cap). Genuine T1 solves push the node
    above 0.35; the capped NeetCode import must leave it there.

    Uses /solve with needed_hint=False rather than /leetcode/backfill: that
    backfill also understates assistance to "llm_assisted", so three solves
    only reach ~0.17 and the test would pass without proving anything. Only a
    REFLECTED hint-free solve ("none") clears the cap.
    """
    for slug in ("trapping-rain-water", "3sum"):
        await client.post(
            "/api/evidence/leetcode/solve",
            json={"problem_slug": slug, "submission_id": f"lc-{slug}", "needed_hint": False},
        )
    before = (await db.execute(
        select(NodeMastery).where(NodeMastery.node_id == node.id)
    )).scalars().one().m_learned
    assert before > T3_EXPOSURE_CAP, "fixture must exceed the cap for this test to mean anything"

    await client.post(
        "/api/evidence/neetcode/backfill",
        json={"leetcode_slugs": ["valid-palindrome", "3sum", "trapping-rain-water"]},
    )
    after = (await db.execute(
        select(NodeMastery).where(NodeMastery.node_id == node.id)
    )).scalars().one().m_learned
    assert after >= before
