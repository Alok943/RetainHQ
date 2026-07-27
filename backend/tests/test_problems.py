"""LeetCode problems on DSA nodes + manual capture (IMPLEMENTATION-problem-capture.md).

The load-bearing test is `test_marking_writes_no_evidence`: a manual click is a
completion checkbox, never evidence — it must never create a learning_event or
change node_mastery, which is the product's whole thesis ("track what you
remember, not what you complete").
"""
import pytest
from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.models import LearningEvent, NodeMastery, Problem, ProblemAttempt, ProblemConcept, Roadmap, RoadmapNode
from tests.conftest import USER_A, USER_B


@pytest.fixture
async def dsa_node(db: AsyncSession) -> RoadmapNode:
    roadmap = Roadmap(title="DSA", audience="career", slug="dsa")
    db.add(roadmap)
    await db.commit()
    node = RoadmapNode(roadmap_id=roadmap.id, phase="1", section="1", title="Hash Tables")
    db.add(node)
    await db.commit()
    return node


@pytest.fixture
async def empty_node(db: AsyncSession) -> RoadmapNode:
    """A node with zero mapped problems — one of the 12 uncovered DSA nodes."""
    roadmap = (await db.execute(select(Roadmap).where(Roadmap.slug == "dsa"))).scalar_one_or_none()
    if roadmap is None:
        roadmap = Roadmap(title="DSA", audience="career", slug="dsa")
        db.add(roadmap)
        await db.commit()
    node = RoadmapNode(roadmap_id=roadmap.id, phase="1", section="1", title="Some Uncovered Concept")
    db.add(node)
    await db.commit()
    return node


async def _make_problem(db, dsa_node, *, external_id, slug, title, difficulty, role, paid_only=False):
    problem = Problem(
        source="leetcode", external_id=external_id, slug=slug, title=title,
        difficulty=difficulty, catalog_version="v1", paid_only=paid_only,
        url=f"https://leetcode.com/problems/{slug}/",
    )
    db.add(problem)
    await db.commit()
    db.add(ProblemConcept(problem_id=problem.id, node_id=dsa_node.id, role=role, confidence=1.0, mapping_version="v1"))
    await db.commit()
    return problem


@pytest.fixture
async def problems(db: AsyncSession, dsa_node: RoadmapNode):
    """One of each role, spanning difficulty, so ordering is actually exercised."""
    hard_primary = await _make_problem(db, dsa_node, external_id=3, slug="hard-one", title="Hard One", difficulty="hard", role="primary")
    easy_primary = await _make_problem(db, dsa_node, external_id=1, slug="two-sum", title="Two Sum", difficulty="easy", role="primary")
    supporting = await _make_problem(db, dsa_node, external_id=2, slug="supporting-one", title="Supporting One", difficulty="medium", role="supporting")
    alternative = await _make_problem(db, dsa_node, external_id=4, slug="alt-one", title="Alt One", difficulty="easy", role="alternative", paid_only=True)
    return {"hard_primary": hard_primary, "easy_primary": easy_primary, "supporting": supporting, "alternative": alternative}


# --------------------------------------------------------------------------
# GET /by-node/{node_id}
# --------------------------------------------------------------------------

async def test_by_node_orders_role_then_difficulty_then_external_id(client: AsyncClient, dsa_node, problems):
    resp = await client.get(f"/api/problems/by-node/{dsa_node.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert [p["slug"] for p in body] == ["two-sum", "hard-one", "supporting-one", "alt-one"]
    assert [p["role"] for p in body] == ["primary", "primary", "supporting", "alternative"]
    assert body[3]["paid_only"] is True
    assert all(p["marked_status"] is None for p in body)


async def test_by_node_includes_callers_marks(client: AsyncClient, dsa_node, problems):
    await client.post(f"/api/problems/{problems['easy_primary'].id}/mark", json={"status": "solved"})
    resp = await client.get(f"/api/problems/by-node/{dsa_node.id}")
    body = {p["slug"]: p["marked_status"] for p in resp.json()}
    assert body["two-sum"] == "solved"
    assert body["hard-one"] is None


async def test_by_node_with_zero_problems_returns_empty_list_not_404(client: AsyncClient, empty_node):
    resp = await client.get(f"/api/problems/by-node/{empty_node.id}")
    assert resp.status_code == 200
    assert resp.json() == []


# --------------------------------------------------------------------------
# mark / unmark
# --------------------------------------------------------------------------

async def test_mark_creates_row(client: AsyncClient, db: AsyncSession, dsa_node, problems):
    resp = await client.post(f"/api/problems/{problems['easy_primary'].id}/mark", json={"status": "solved"})
    assert resp.status_code == 204

    rows = (await db.execute(select(ProblemAttempt))).scalars().all()
    assert len(rows) == 1
    assert str(rows[0].user_id) == USER_A.id
    assert rows[0].status == "solved"


async def test_marking_twice_is_idempotent_one_row(client: AsyncClient, db: AsyncSession, problems):
    problem_id = problems["easy_primary"].id
    await client.post(f"/api/problems/{problem_id}/mark", json={"status": "solved"})
    resp = await client.post(f"/api/problems/{problem_id}/mark", json={"status": "attempted"})
    assert resp.status_code == 204

    rows = (await db.execute(select(ProblemAttempt).where(ProblemAttempt.problem_id == problem_id))).scalars().all()
    assert len(rows) == 1
    assert rows[0].status == "attempted", "re-marking updates status in place, not a second row"


async def test_unmark_removes_the_row(client: AsyncClient, db: AsyncSession, problems):
    problem_id = problems["easy_primary"].id
    await client.post(f"/api/problems/{problem_id}/mark", json={"status": "solved"})
    resp = await client.delete(f"/api/problems/{problem_id}/mark")
    assert resp.status_code == 204

    rows = (await db.execute(select(ProblemAttempt).where(ProblemAttempt.problem_id == problem_id))).scalars().all()
    assert rows == []


async def test_marking_writes_no_evidence(client: AsyncClient, db: AsyncSession, dsa_node, problems):
    """The load-bearing test: manual capture must never reach the evidence spine."""
    resp = await client.post(f"/api/problems/{problems['easy_primary'].id}/mark", json={"status": "solved"})
    assert resp.status_code == 204

    events = (await db.execute(select(LearningEvent))).scalars().all()
    assert events == [], "marking a problem must never write a learning_event"

    mastery = (await db.execute(select(NodeMastery).where(NodeMastery.node_id == dsa_node.id))).scalars().all()
    assert mastery == [], "marking a problem must never create/move node_mastery"


# --------------------------------------------------------------------------
# IDOR
# --------------------------------------------------------------------------

async def test_idor_user_b_cannot_delete_user_as_mark(client: AsyncClient, db: AsyncSession, as_user, problems):
    problem_id = problems["easy_primary"].id
    await client.post(f"/api/problems/{problem_id}/mark", json={"status": "solved"})

    as_user(USER_B)
    resp = await client.delete(f"/api/problems/{problem_id}/mark")
    assert resp.status_code == 204  # no-op for B, not an error — nothing to leak either way

    rows = (await db.execute(select(ProblemAttempt).where(ProblemAttempt.problem_id == problem_id))).scalars().all()
    assert len(rows) == 1
    assert str(rows[0].user_id) == USER_A.id, "user B's delete must not remove user A's mark"


async def test_idor_user_b_sees_no_mark_of_their_own(client: AsyncClient, dsa_node, as_user, problems):
    """B never marked anything — B's view of the node must show unmarked, not A's mark."""
    problem_id = problems["easy_primary"].id
    await client.post(f"/api/problems/{problem_id}/mark", json={"status": "solved"})

    as_user(USER_B)
    resp = await client.get(f"/api/problems/by-node/{dsa_node.id}")
    body = {p["slug"]: p["marked_status"] for p in resp.json()}
    assert body["two-sum"] is None
