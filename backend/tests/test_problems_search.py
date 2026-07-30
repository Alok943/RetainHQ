import pytest
from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
import uuid

from app.models.models import Problem, ProblemAttempt, ProblemConcept, Roadmap, RoadmapNode, CareerGoal, NodeMastery, LearningEvent
from tests.conftest import USER_A, USER_B

@pytest.fixture
async def search_data(db: AsyncSession):
    roadmap = Roadmap(title="DSA", audience="career", slug="dsa")
    db.add(roadmap)
    await db.commit()
    node = RoadmapNode(roadmap_id=roadmap.id, phase="1", section="1", title="Hash Tables")
    db.add(node)
    await db.commit()
    
    # 1. Two Sum (mapped)
    p1 = Problem(source="leetcode", external_id=1, slug="two-sum", title="Two Sum", difficulty="easy", catalog_version="v1")
    db.add(p1)
    await db.commit()
    db.add(ProblemConcept(problem_id=p1.id, node_id=node.id, role="primary", confidence=1.0, mapping_version="v1"))
    
    # 42. Trapping Rain Water (unmapped)
    p42 = Problem(source="leetcode", external_id=42, slug="trapping-rain-water", title="Trapping Rain Water", difficulty="hard", catalog_version="v1")
    db.add(p42)
    
    # A dummy problem with a % and _ in its name
    p99 = Problem(source="leetcode", external_id=99, slug="weird-problem", title="Weird_Problem %", difficulty="medium", catalog_version="v1")
    db.add(p99)
    
    # A problem for tier dominance test
    # title="3sum" external_id=15
    p15 = Problem(source="leetcode", external_id=15, slug="3sum", title="3Sum", difficulty="medium", catalog_version="v1")
    db.add(p15)
    
    # A problem whose external_id is 3
    p3 = Problem(source="leetcode", external_id=3, slug="longest-substring", title="Longest Substring", difficulty="medium", catalog_version="v1")
    db.add(p3)

    await db.commit()
    return {"node": node, "p1": p1, "p42": p42, "p99": p99, "p15": p15, "p3": p3}

async def test_search_exact_id_and_title(client: AsyncClient, search_data):
    # q="1" ranks 1. Two Sum first
    resp = await client.get("/api/problems/search?q=1")
    assert resp.status_code == 200
    res = resp.json()
    assert res[0]["external_id"] == 1
    
    # q="two sum" ranks it first
    resp = await client.get("/api/problems/search?q=two sum")
    res = resp.json()
    assert res[0]["external_id"] == 1
    
    # q="trapping" finds 42
    resp = await client.get("/api/problems/search?q=trapping")
    res = resp.json()
    assert res[0]["external_id"] == 42

async def test_tier_dominance(client: AsyncClient, search_data, db: AsyncSession, as_user):
    # We will give p15 (3sum) a massive boost by making it already logged? No, logged is negative boost.
    # Let's give p15 a boost by making it part of an active career goal and weak node.
    as_user(USER_A)
    # create a node for p15
    node15 = RoadmapNode(roadmap_id=search_data["node"].roadmap_id, phase="1", section="1", title="Arrays")
    db.add(node15)
    await db.commit()
    db.add(ProblemConcept(problem_id=search_data["p15"].id, node_id=node15.id, role="primary", confidence=1.0, mapping_version="v1"))
    
    goal = CareerGoal(user_id=uuid.UUID(USER_A.id), roadmap_id=search_data["node"].roadmap_id, status="active", title="My Goal", role_title="SWE", role_key="swe")
    db.add(goal)
    
    # Make node15 weak
    mastery = NodeMastery(user_id=uuid.UUID(USER_A.id), node_id=node15.id, m_learned=0.1, weights_version="v1")
    db.add(mastery)
    await db.commit()
    
    # Search for "3". 
    # For p3 (external_id=3), it's exact digit match -> tier 100, boost 0.
    # For p15 (3sum), title contains digit -> tier 60, boost 15+10 = 25.
    # Even with boost, tier 100 > tier 60 + boost. 
    resp = await client.get("/api/problems/search?q=3")
    res = resp.json()
    assert res[0]["external_id"] == 3
    assert res[1]["external_id"] == 15

async def test_escape_wildcards(client: AsyncClient, search_data):
    resp = await client.get("/api/problems/search?q=%")
    res = resp.json()
    assert len(res) == 1
    assert res[0]["external_id"] == 99
    
    resp = await client.get("/api/problems/search?q=_")
    res = resp.json()
    assert len(res) == 1
    assert res[0]["external_id"] == 99

async def test_unmapped_problem_returns_null_node_id(client: AsyncClient, search_data):
    resp = await client.get("/api/problems/search?q=trapping")
    res = resp.json()
    assert res[0]["node_id"] is None
    assert res[0]["external_id"] == 42

async def test_idor_already_logged_and_suggest(client: AsyncClient, search_data, db: AsyncSession, as_user):
    # A logs p1
    as_user(USER_A)
    await client.post(f"/api/problems/{search_data['p1'].id}/mark", json={"status": "solved"})
    
    # B searches p1 -> already_logged = False
    as_user(USER_B)
    resp = await client.get("/api/problems/search?q=1")
    res = resp.json()
    assert res[0]["already_logged"] is False
    
    # A searches p1 -> already_logged = True
    as_user(USER_A)
    resp = await client.get("/api/problems/search?q=1")
    res = resp.json()
    assert res[0]["already_logged"] is True
