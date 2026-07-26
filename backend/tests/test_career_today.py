"""Career Coach Phase 3 — route-level tests for GET/PATCH/POST /api/career/today*
(SPEC-career-coach-phase3.md §4, IMPLEMENTATION-career-coach-phase3.md §6).
The pure-core behavior itself is pinned by tests/test_planner.py; this file
only exercises the DB-shell assembly (query correctness, 404s, clamping,
IDOR, the lazy sprint-expiry side effect).
"""
import uuid
from datetime import date, datetime, timedelta

from sqlalchemy import select

from app.models.models import (
    CareerGoal, LearningEvent, MetricEvent, NodeMeta, Roadmap, RoadmapNode,
)
from tests.conftest import USER_A, USER_B
from tests.test_career import BACKEND_ROLE, _commit_backend_tree


async def test_today_404s_without_a_goal(client):
    resp = await client.get("/api/career/today")
    assert resp.status_code == 404


async def test_today_404s_with_goal_but_no_committed_tree(client):
    from app.api.routes import career as career_routes
    career_routes._generate_counts.clear()
    resp = await client.post("/api/career/goals/", json={"role_key": BACKEND_ROLE, "title": "No tree yet"})
    assert resp.status_code == 201

    today = await client.get("/api/career/today")
    assert today.status_code == 404


async def test_today_returns_a_plan_with_a_reason_on_every_item(client, db):
    await _commit_backend_tree(client, db, title="Today happy path")

    resp = await client.get("/api/career/today")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "daily_minutes" in body
    assert isinstance(body["items"], list)
    assert all(item["reason"] for item in body["items"])


async def test_daily_minutes_clamp_at_both_ends(client, db):
    await _commit_backend_tree(client, db, title="Clamp check")

    low = await client.patch("/api/career/goals/active", json={"daily_minutes": 5})
    assert low.status_code == 200, low.text
    assert low.json()["daily_minutes"] == 30

    high = await client.patch("/api/career/goals/active", json={"daily_minutes": 9000})
    assert high.status_code == 200
    assert high.json()["daily_minutes"] == 240

    in_range = await client.patch("/api/career/goals/active", json={"daily_minutes": 45})
    assert in_range.status_code == 200
    assert in_range.json()["daily_minutes"] == 45


async def test_feedback_writes_exactly_one_metric_event(client, db):
    await _commit_backend_tree(client, db, title="Feedback check")
    user_id = uuid.UUID(USER_A.id)

    resp = await client.post(
        "/api/career/today/feedback",
        json={"item_ref": "dsa.arrays.basics", "action": "done"},
    )
    assert resp.status_code == 204

    events = (
        await db.execute(
            select(MetricEvent).where(
                MetricEvent.user_id == user_id, MetricEvent.event_type == "plan_item_feedback",
            )
        )
    ).scalars().all()
    assert len(events) == 1
    assert events[0].payload == {"item_ref": "dsa.arrays.basics", "action": "done"}


async def test_user_b_gets_404_on_todays_plan_and_cannot_patch_goal(client, db, as_user):
    await _commit_backend_tree(client, db, title="IDOR check")

    as_user(USER_B)

    today = await client.get("/api/career/today")
    assert today.status_code == 404

    patch = await client.patch("/api/career/goals/active", json={"daily_minutes": 90})
    assert patch.status_code == 404


async def test_expired_sprint_is_cleared_by_get_today(client, db):
    stable_key_to_node_id = await _commit_backend_tree(client, db, title="Sprint expiry check")
    node_id = stable_key_to_node_id["dsa.arrays.basics"]
    user_id = uuid.UUID(USER_A.id)

    goal = (
        await db.execute(select(CareerGoal).where(CareerGoal.user_id == user_id, CareerGoal.status == "active"))
    ).scalar_one()
    goal.sprint_node_id = node_id
    goal.sprint_until = date.today() - timedelta(days=1)
    db.add(goal)
    await db.commit()
    goal_id = goal.id  # captured before expire_all() below — see its docstring note

    resp = await client.get("/api/career/today")
    assert resp.status_code == 200, resp.text

    # The GET ran on a different session (client's own, per request) — this
    # session's identity map still holds the pre-clear object, so force a
    # fresh read. Accessing an attribute on the ORM object AFTER expire_all()
    # would itself trigger a lazy reload outside a sync greenlet and raise —
    # query by the id captured above instead.
    db.expire_all()
    refreshed = (
        await db.execute(select(CareerGoal).where(CareerGoal.id == goal_id))
    ).scalar_one()
    assert refreshed.sprint_node_id is None
    assert refreshed.sprint_until is None


async def test_balance_window_ignores_events_from_another_goals_tree(client, db):
    """Regression: `node_meta` rows outlive goal archival, so the trailing-window
    query used to sweep up learning events belonging to a PREVIOUS career tree.
    Those minutes inflated total_window_minutes (and landed under subjects the
    current tree may not even have) while p_s stayed normalized over the current
    tree alone — deflating every real a_s and manufacturing "you're neglecting X"
    nudges for anyone who had ever switched goals.

    200 minutes on a foreign tree is well past BALANCE_MIN_WINDOW_MINUTES (120),
    so before the fix this produced a non-empty balance dict on an account with
    no activity of its own at all.
    """
    await _commit_backend_tree(client, db, title="Foreign-tree balance check")
    user_id = uuid.UUID(USER_A.id)

    # A node belonging to some OTHER roadmap, with node_meta (i.e. it looks
    # exactly like an archived career-tree node).
    other_roadmap = Roadmap(title="An older career tree", audience="career", user_id=user_id)
    db.add(other_roadmap)
    await db.commit()
    other_node = RoadmapNode(roadmap_id=other_roadmap.id, phase="1", section="1", title="Old Node")
    db.add(other_node)
    await db.commit()
    db.add(NodeMeta(node_id=other_node.id, stable_key="old.tree.node", subject="dsa", priority=5))
    db.add(LearningEvent(
        user_id=user_id, node_id=other_node.id, event_type="TIME_BLOCK",
        trust_tier="T4_ambient", source="companion", duration_min=200,
        occurred_at=datetime.utcnow(),
    ))
    await db.commit()

    resp = await client.get("/api/career/today")
    assert resp.status_code == 200, resp.text
    assert resp.json()["balance"] == {}, (
        "minutes logged against another tree must not reach this goal's balance window"
    )
