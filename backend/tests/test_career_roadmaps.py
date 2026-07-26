"""Attaching roadmaps to a career goal (IMPLEMENTATION-career-attached-roadmaps.md).

The feature is "make catalog + personal roadmaps visible to the planner", and the
mechanism is node_meta sidecars — the planner INNER JOINs node_meta and cannot
score a node without subject/priority/effort. So most of what's worth pinning
here is about the sidecars: that they get created, that attaching never copies
nodes, that detaching removes exactly its own and no evidence.
"""
import uuid
from datetime import datetime, timedelta

from sqlalchemy import select

from app.models.models import (
    CareerGoalRoadmap, LearningEvent, NodeMastery, NodeMeta, Roadmap, RoadmapNode, UserPref,
)
from tests.conftest import USER_A, USER_B
from tests.test_career import BACKEND_ROLE, _commit_backend_tree


async def _make_roadmap(db, *, title, owner=None, audience="career", slug=None, nodes=3):
    rm = Roadmap(title=title, audience=audience, slug=slug, user_id=owner)
    db.add(rm)
    await db.commit()
    for i in range(nodes):
        db.add(RoadmapNode(roadmap_id=rm.id, phase="1", section="1", title=f"{title} node {i}", order_index=i))
    await db.commit()
    return rm


async def test_attach_inbuilt_roadmap_creates_sidecars_and_reaches_the_plan(client, db):
    stable_to_node = await _commit_backend_tree(client, db, title="Attach inbuilt")
    rm = await _make_roadmap(db, title="DSA Catalog", slug="dsa-cat", nodes=4)

    resp = await client.post("/api/career/roadmaps/", json={"roadmap_id": str(rm.id)})
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["nodes_added"] == 4
    assert body["subject"] == "dsa-cat"          # derived from slug — one-click, no form
    assert body["default_priority"] == 3

    metas = (await db.execute(
        select(NodeMeta).where(NodeMeta.stable_key.like("attached.dsa-cat.%"))
    )).scalars().all()
    assert len(metas) == 4
    assert {m.subject for m in metas} == {"dsa-cat"}

    # Nodes were NOT copied — they still live in their own roadmap.
    assert (await db.execute(
        select(RoadmapNode).where(RoadmapNode.roadmap_id == rm.id)
    )).scalars().all().__len__() == 4

    # Master every node of the goal's own tree so the frontier contains nothing
    # but the attached roadmap. Without this the assertion is a lottery: the plan
    # holds MAX_STUDY_ITEMS=5, and a 63-node template tree has priority-5 roots
    # with unlock bonuses that legitimately outrank a priority-3 attachment. That
    # ranking is correct behaviour, so the test isolates *eligibility* instead.
    for node_id in stable_to_node.values():
        db.add(NodeMastery(
            user_id=uuid.UUID(USER_A.id), node_id=node_id, m_learned=0.95, weights_version="v1",
        ))
    await db.commit()

    today = await client.get("/api/career/today")
    assert today.status_code == 200
    body = today.json()
    assert body["tree_complete"] is False, "attached nodes are unmastered, so the tree isn't done"
    labels = {i["label"] for i in body["items"]}
    assert any(l.startswith("DSA Catalog node") for l in labels), (
        "attached nodes must be schedulable, not merely recorded"
    )


async def test_attach_my_own_roadmap(client, db):
    await _commit_backend_tree(client, db, title="Attach mine")
    rm = await _make_roadmap(db, title="My Syllabus", owner=uuid.UUID(USER_A.id), slug="mine-1")

    resp = await client.post("/api/career/roadmaps/", json={"roadmap_id": str(rm.id)})
    assert resp.status_code == 201, resp.text
    assert resp.json()["nodes_added"] == 3


async def test_cannot_attach_another_users_private_roadmap(client, db):
    """The IDOR gate. Without it, attaching is a read primitive for anyone's
    private syllabus roadmap — the response returns its title and node count."""
    await _commit_backend_tree(client, db, title="IDOR attach")
    theirs = await _make_roadmap(db, title="Someone else's plan", owner=uuid.uuid4(), slug="theirs")

    resp = await client.post("/api/career/roadmaps/", json={"roadmap_id": str(theirs.id)})
    assert resp.status_code == 403


async def test_cannot_attach_the_goals_own_tree(client, db):
    await _commit_backend_tree(client, db, title="Own tree")
    goal = (await client.get("/api/career/goals/active")).json()
    resp = await client.post("/api/career/roadmaps/", json={"roadmap_id": goal["roadmap_id"]})
    assert resp.status_code == 400


async def test_double_attach_is_a_conflict(client, db):
    await _commit_backend_tree(client, db, title="Double attach")
    rm = await _make_roadmap(db, title="Twice", slug="twice")

    assert (await client.post("/api/career/roadmaps/", json={"roadmap_id": str(rm.id)})).status_code == 201
    assert (await client.post("/api/career/roadmaps/", json={"roadmap_id": str(rm.id)})).status_code == 409


async def test_attach_cap_is_enforced(client, db):
    from app.api.routes.career import MAX_ATTACHED_ROADMAPS

    await _commit_backend_tree(client, db, title="Cap check")
    for i in range(MAX_ATTACHED_ROADMAPS):
        rm = await _make_roadmap(db, title=f"Cap {i}", slug=f"cap-{i}", nodes=1)
        assert (await client.post("/api/career/roadmaps/", json={"roadmap_id": str(rm.id)})).status_code == 201

    one_too_many = await _make_roadmap(db, title="Overflow", slug="overflow", nodes=1)
    resp = await client.post("/api/career/roadmaps/", json={"roadmap_id": str(one_too_many.id)})
    assert resp.status_code == 400


async def test_available_excludes_attached_own_tree_and_other_audiences(client, db):
    await _commit_backend_tree(client, db, title="Available check")
    db.add(UserPref(user_id=uuid.UUID(USER_A.id), audience="career"))
    await db.commit()

    keep = await _make_roadmap(db, title="Career one", slug="career-one")
    school = await _make_roadmap(db, title="School one", slug="school-one", audience="school")
    attached = await _make_roadmap(db, title="Already on", slug="already-on")
    assert (await client.post("/api/career/roadmaps/", json={"roadmap_id": str(attached.id)})).status_code == 201

    resp = await client.get("/api/career/roadmaps/available")
    assert resp.status_code == 200, resp.text
    ids = {r["id"] for r in resp.json()["inbuilt"]} | {r["id"] for r in resp.json()["mine"]}
    goal = (await client.get("/api/career/goals/active")).json()

    assert str(keep.id) in ids
    assert str(school.id) not in ids, "a career-audience user must never be offered school roadmaps"
    assert str(attached.id) not in ids
    assert goal["roadmap_id"] not in ids


async def test_detach_removes_sidecars_but_never_evidence(client, db):
    await _commit_backend_tree(client, db, title="Detach check")
    user_id = uuid.UUID(USER_A.id)
    rm = await _make_roadmap(db, title="Detachable", slug="detachable", nodes=3)
    assert (await client.post("/api/career/roadmaps/", json={"roadmap_id": str(rm.id)})).status_code == 201

    node = (await db.execute(
        select(RoadmapNode).where(RoadmapNode.roadmap_id == rm.id)
    )).scalars().first()
    db.add(LearningEvent(
        user_id=user_id, node_id=node.id, event_type="TIME_BLOCK", trust_tier="T4_ambient",
        source="companion", duration_min=45, occurred_at=datetime.utcnow(),
    ))
    db.add(NodeMastery(user_id=user_id, node_id=node.id, m_learned=0.4, weights_version="v1"))
    await db.commit()

    resp = await client.delete(f"/api/career/roadmaps/{rm.id}")
    assert resp.status_code == 204

    assert (await db.execute(
        select(CareerGoalRoadmap).where(CareerGoalRoadmap.roadmap_id == rm.id)
    )).scalars().all() == []
    assert (await db.execute(
        select(NodeMeta).where(NodeMeta.stable_key.like("attached.detachable.%"))
    )).scalars().all() == []

    # Evidence survives — detaching stops planning, it does not rewrite history.
    assert len((await db.execute(
        select(LearningEvent).where(LearningEvent.node_id == node.id)
    )).scalars().all()) == 1
    assert len((await db.execute(
        select(NodeMastery).where(NodeMastery.node_id == node.id)
    )).scalars().all()) == 1


async def test_detach_leaves_a_user_edited_sidecar_alone(client, db):
    await _commit_backend_tree(client, db, title="User-edited sidecar")
    rm = await _make_roadmap(db, title="Edited", slug="edited", nodes=2)
    assert (await client.post("/api/career/roadmaps/", json={"roadmap_id": str(rm.id)})).status_code == 201

    meta = (await db.execute(
        select(NodeMeta).where(NodeMeta.stable_key.like("attached.edited.%"))
    )).scalars().first()
    meta.user_edited = True
    db.add(meta)
    await db.commit()

    assert (await client.delete(f"/api/career/roadmaps/{rm.id}")).status_code == 204
    survivors = (await db.execute(
        select(NodeMeta).where(NodeMeta.stable_key.like("attached.edited.%"))
    )).scalars().all()
    assert len(survivors) == 1 and survivors[0].user_edited is True


async def test_attached_roadmap_minutes_reach_the_balance_window(client, db):
    """Guards the node_ids wiring. The 2026-07-26 scoping fix filters the balance
    window by node_ids; if attached nodes were missing from it, studying an
    attached roadmap would count for nothing and its subject would look
    permanently neglected — the exact false-nudge that fix prevented."""
    await _commit_backend_tree(client, db, title="Attached balance")
    user_id = uuid.UUID(USER_A.id)
    rm = await _make_roadmap(db, title="Studied", slug="studied", nodes=2)
    assert (await client.post("/api/career/roadmaps/", json={"roadmap_id": str(rm.id)})).status_code == 201

    node = (await db.execute(
        select(RoadmapNode).where(RoadmapNode.roadmap_id == rm.id)
    )).scalars().first()
    db.add(LearningEvent(
        user_id=user_id, node_id=node.id, event_type="TIME_BLOCK", trust_tier="T4_ambient",
        source="companion", duration_min=300, occurred_at=datetime.utcnow() - timedelta(days=1),
    ))
    await db.commit()

    body = (await client.get("/api/career/today")).json()
    assert body["balance"], "300 minutes is past the evidence floor — balance must engage"
    assert body["balance"].get("studied", 0) > 0, "attached-roadmap minutes must land in its subject"


async def test_attach_routes_404_without_a_goal(client, db):
    rm = await _make_roadmap(db, title="No goal", slug="no-goal")
    assert (await client.get("/api/career/roadmaps/available")).status_code == 404
    assert (await client.get("/api/career/roadmaps/")).status_code == 404
    assert (await client.post("/api/career/roadmaps/", json={"roadmap_id": str(rm.id)})).status_code == 404
    assert (await client.delete(f"/api/career/roadmaps/{rm.id}")).status_code == 404


async def test_user_b_cannot_see_or_detach_user_as_attachments(client, db, as_user):
    await _commit_backend_tree(client, db, title="Cross-user attach")
    rm = await _make_roadmap(db, title="A's pick", slug="a-pick")
    assert (await client.post("/api/career/roadmaps/", json={"roadmap_id": str(rm.id)})).status_code == 201

    as_user(USER_B)
    assert (await client.get("/api/career/roadmaps/")).status_code == 404
    assert (await client.delete(f"/api/career/roadmaps/{rm.id}")).status_code == 404


async def test_can_attach_during_onboarding_before_the_tree_is_committed(client, db):
    """The picker has to work mid-onboarding, because that's when users find out
    the template can't give them what they want — `ai_engineer.v2` has no DSA
    subject at all, and `career_tree.py` treats an invented subject as a hard-rule
    violation, so no amount of regenerating produces one. The goal row exists from
    onboarding step 1; only `roadmap_id` is NULL until commit, and attaching needs
    only the goal id.
    """
    from app.api.routes import career as career_routes
    career_routes._generate_counts.clear()

    created = await client.post(
        "/api/career/goals/", json={"role_key": BACKEND_ROLE, "title": "Mid-onboarding"}
    )
    assert created.status_code == 201
    assert created.json()["roadmap_id"] is None, "precondition: no tree committed yet"

    rm = await _make_roadmap(db, title="DSA Catalog", slug="dsa-onboarding", nodes=3)

    assert (await client.get("/api/career/roadmaps/available")).status_code == 200
    resp = await client.post("/api/career/roadmaps/", json={"roadmap_id": str(rm.id)})
    assert resp.status_code == 201, resp.text
    assert resp.json()["nodes_added"] == 3

    listed = await client.get("/api/career/roadmaps/")
    assert listed.status_code == 200
    assert [r["roadmap_id"] for r in listed.json()] == [str(rm.id)]


async def test_today_still_requires_a_committed_tree(client, db):
    """The relaxed guard is scoped to the roadmap routes — /today must keep the
    stricter one, since the planner cannot run without a tree."""
    from app.api.routes import career as career_routes
    career_routes._generate_counts.clear()

    assert (await client.post(
        "/api/career/goals/", json={"role_key": BACKEND_ROLE, "title": "No tree"}
    )).status_code == 201
    assert (await client.get("/api/career/today")).status_code == 404
