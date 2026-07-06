"""
Tenant-isolation tests: user B must never see or mutate user A's data.

Every user-scoped route relies on an app-code WHERE clause for isolation
(the DB role bypasses RLS), so each route gets an explicit cross-user probe.
"""
import uuid

from tests.conftest import USER_A, USER_B, ADMIN

ACTIVITY_PAYLOAD = {
    "topic": "Binary search",
    "difficulty": 3,
    "needed_hint": False,
    "key_memory": "Halve the search space each step; O(log n).",
}


async def _create_activity(client, **overrides):
    resp = await client.post("/api/activities/", json={**ACTIVITY_PAYLOAD, **overrides})
    assert resp.status_code == 200, resp.text
    return resp.json()


# --------------------------------------------------------------------------- #
# Activities
# --------------------------------------------------------------------------- #
async def test_activity_list_is_scoped_to_owner(client, as_user):
    await _create_activity(client)
    await _create_activity(client, topic="Two pointers")

    resp = await client.get("/api/activities/")
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    as_user(USER_B)
    resp = await client.get("/api/activities/")
    assert resp.status_code == 200
    assert resp.json() == []  # B must not see A's activities


async def test_activity_is_created_under_caller_not_payload(client):
    created = await _create_activity(client)
    assert created["user_id"] == USER_A.id  # user_id comes from the JWT, never the body


# --------------------------------------------------------------------------- #
# Reviews
# --------------------------------------------------------------------------- #
async def test_due_reviews_are_scoped_to_owner(client, as_user):
    created = await _create_activity(client)
    assert created["review_due_now"] is True  # first-ever activity → demo review due now

    resp = await client.get("/api/reviews/due")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    as_user(USER_B)
    resp = await client.get("/api/reviews/due")
    assert resp.status_code == 200
    assert resp.json() == []  # B must not see A's due reviews


async def test_cannot_complete_another_users_review(client, as_user):
    await _create_activity(client)
    review_id = (await client.get("/api/reviews/due")).json()[0]["id"]

    # B tries to complete A's review — the atomic UPDATE must not match.
    as_user(USER_B)
    resp = await client.post(
        f"/api/reviews/{review_id}/complete",
        json={"rating": "easy", "recalled": True},
    )
    assert resp.status_code == 400

    # A's review is untouched and still completable.
    as_user(USER_A)
    resp = await client.post(
        f"/api/reviews/{review_id}/complete",
        json={"rating": "easy", "recalled": True},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"


async def test_review_cannot_be_completed_twice(client):
    await _create_activity(client)
    review_id = (await client.get("/api/reviews/due")).json()[0]["id"]

    first = await client.post(
        f"/api/reviews/{review_id}/complete", json={"rating": "medium", "recalled": True}
    )
    assert first.status_code == 200

    second = await client.post(
        f"/api/reviews/{review_id}/complete", json={"rating": "easy", "recalled": True}
    )
    assert second.status_code == 400  # double-completion race is closed


async def test_completing_review_schedules_next_one(client):
    await _create_activity(client)
    review_id = (await client.get("/api/reviews/due")).json()[0]["id"]
    resp = await client.post(
        f"/api/reviews/{review_id}/complete", json={"rating": "easy", "recalled": True}
    )
    assert resp.status_code == 200
    # Next review exists but is scheduled in the future, so /due is empty again.
    resp = await client.get("/api/reviews/due")
    assert resp.json() == []


# --------------------------------------------------------------------------- #
# LLM grader endpoints — must be hard-off when GRADER_ENABLED=false
# --------------------------------------------------------------------------- #
async def test_grader_endpoints_are_gated_off(client):
    rid = uuid.uuid4()
    assert (await client.post("/api/activities/suggest-key-points", json={"topic": "x"})).status_code == 404
    assert (await client.post(f"/api/reviews/{rid}/grade", json={"answer": "x"})).status_code == 404
    assert (await client.post(f"/api/reviews/{rid}/questions")).status_code == 404
    assert (await client.post(f"/api/reviews/{rid}/grade-questions", json={"answers": []})).status_code == 404


# --------------------------------------------------------------------------- #
# Prefs
# --------------------------------------------------------------------------- #
async def test_prefs_are_isolated_per_user(client, as_user):
    resp = await client.put("/api/prefs/", json={"audience": "school"})
    assert resp.status_code == 200

    as_user(USER_B)
    resp = await client.get("/api/prefs/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_set"] is False        # A's choice must not leak to B
    assert body["audience"] == "career"   # untouched default


# --------------------------------------------------------------------------- #
# Feedback
# --------------------------------------------------------------------------- #
async def test_feedback_is_attributed_to_caller(client):
    resp = await client.post("/api/feedback/", json={"message": "hello"})
    assert resp.status_code == 200
    assert resp.json()["user_id"] == USER_A.id


# --------------------------------------------------------------------------- #
# Admin gate
# --------------------------------------------------------------------------- #
async def test_admin_routes_reject_non_admin(client, as_user):
    for user in (USER_A, USER_B):
        as_user(user)
        assert (await client.get("/api/admin/funnel")).status_code == 403
        assert (await client.get("/api/admin/feedback")).status_code == 403


async def test_admin_gate_is_case_insensitive_on_email(client, as_user):
    from app.core.security import SupabaseUser
    as_user(SupabaseUser(id=ADMIN.id, email="ADMIN@EXAMPLE.COM", role="authenticated"))
    # Passing the gate means the route body runs — which on sqlite blows up on
    # the pg-only auth.users query. Either a non-403 response or that DB error
    # proves the dependency admitted the (case-differing) admin email.
    try:
        resp = await client.get("/api/admin/feedback")
        assert resp.status_code != 403
    except Exception as e:
        assert "auth.users" in str(e) or "no such table" in str(e)


# --------------------------------------------------------------------------- #
# Internal cron trigger
# --------------------------------------------------------------------------- #
async def test_cron_endpoint_rejects_missing_or_wrong_secret(client):
    assert (await client.post("/api/internal/send-reminders")).status_code == 401
    assert (
        await client.post(
            "/api/internal/send-reminders", headers={"X-Cron-Secret": "wrong"}
        )
    ).status_code == 401


async def test_cron_endpoint_accepts_correct_secret(client, monkeypatch):
    from app.api.routes import internal

    async def fake_send(db):
        return {"sent": 0}

    monkeypatch.setattr(internal, "send_due_reminders", fake_send)
    resp = await client.post(
        "/api/internal/send-reminders", headers={"X-Cron-Secret": "test-cron-secret"}
    )
    assert resp.status_code == 200
    assert resp.json() == {"sent": 0}


# --------------------------------------------------------------------------- #
# Roadmap progress visibility
# --------------------------------------------------------------------------- #
async def test_roadmap_progress_not_visible_to_other_users(client, db, as_user):
    from app.models.models import Roadmap, RoadmapNode, UserProgress

    roadmap = Roadmap(title="Test Roadmap", slug="test-roadmap", audience="career")
    db.add(roadmap)
    await db.flush()
    node = RoadmapNode(roadmap_id=roadmap.id, phase="p1", section="s1", title="Node 1")
    db.add(node)
    await db.flush()
    db.add(UserProgress(user_id=uuid.UUID(USER_A.id), node_id=node.id, status="done"))
    await db.commit()

    resp = await client.get(f"/api/roadmaps/{roadmap.id}")
    assert resp.status_code == 200
    assert resp.json()["nodes"][0]["status"] == "done"

    as_user(USER_B)
    resp = await client.get(f"/api/roadmaps/{roadmap.id}")
    assert resp.status_code == 200
    assert resp.json()["nodes"][0]["status"] == "not_started"  # A's progress must not leak


# NOTE: /api/dashboard/* and the admin funnel body use Postgres-only SQL
# (array_agg, auth.users), so their data paths can't run on sqlite. Their
# user_id scoping is visible in dashboard.py's WHERE clauses; cover them here
# if this suite is ever pointed at a disposable Postgres.
