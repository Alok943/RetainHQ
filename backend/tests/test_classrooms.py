"""
Ownership / IDOR / privacy-boundary tests for the classrooms router
(SPEC-teacher-dashboard.md §6): teacher A cannot read teacher B's class; a
student cannot call teacher endpoints on a class they merely belong to; a
removed student's stats stop resolving; and the "aggregation authorization
rule" (§4.2) — a teacher must never receive a number computed from a
student's non-classroom activity.

Runs on the same in-memory SQLite harness as test_ownership.py. Some
analytics helpers (_recall_rate_last_n, and _node_status_matrix's
test_attempts lookup) use Postgres-only raw SQL (array binds / jsonb) and
can't execute on SQLite — same documented boundary as test_dashboard_analytics.py.
Tests that need those endpoints to fully resolve monkeypatch just that one
raw-SQL step; since none of these tests seed any TestAttempt rows, an empty
result is exactly what the real query would return anyway; the ORM-based
scoping under test (Activity.roadmap_id/node_id membership) still runs for real.
"""
import uuid
from datetime import datetime

from sqlalchemy import text

from tests.conftest import USER_A, USER_B

# Empty result set, same shape as the real Postgres queries — valid stand-ins
# because these tests never seed TestAttempt rows (the real query would also
# return nothing) and never need the at-risk recall-window number itself.
_EMPTY_TEST_ROWS_SQL = text(
    "select null as user_id, null as roadmap_id, null as node_title, "
    "0 as got, 0 as missed, 0 as wrong where 1=0"
)


_EMPTY_NODE_ACCURACY_SQL = text(
    "select null as node_title, 0 as got, 0 as missed, 0 as wrong, 0 as total where 1=0"
)


async def _fake_recall_rate_last_n(db, student_ids, roadmap_ids, node_ids):
    return {}


async def _fake_get_heatmap(db, user_id, roadmap_scope):
    # cast(Review.completed_at, Date) — a genuine SQLite/Postgres DATE-cast
    # incompatibility (reproduced independently of jsonb/array), not exercised
    # end-to-end anywhere else in this suite either. Only weekly_recall_trend
    # depends on it; not what this test asserts.
    from app.schemas.dashboard import HeatmapResponse

    return HeatmapResponse(days=[], current_streak=0, longest_streak=0, total_reviews=0, active_days=0)


def _patch_postgres_only_helpers(monkeypatch):
    from app.api.routes import classrooms
    from app.services import learner_stats

    monkeypatch.setattr(classrooms, "_CLASS_NODE_TEST_SQL", _EMPTY_TEST_ROWS_SQL)
    monkeypatch.setattr(classrooms, "_recall_rate_last_n", _fake_recall_rate_last_n)
    monkeypatch.setattr(learner_stats, "_NODE_ACCURACY_SQL", _EMPTY_NODE_ACCURACY_SQL)
    monkeypatch.setattr(classrooms, "_get_learner_heatmap", _fake_get_heatmap)


async def _seed_roadmap(db, **overrides):
    from app.models.models import Roadmap

    r = Roadmap(title=overrides.pop("title", "Physics 9"), audience="school", user_id=None, **overrides)
    db.add(r)
    await db.flush()
    return r


async def _seed_node(db, roadmap_id, **overrides):
    from app.models.models import RoadmapNode

    n = RoadmapNode(
        roadmap_id=roadmap_id,
        phase=overrides.pop("phase", "Motion"),
        section=overrides.pop("section", "Kinematics"),
        title=overrides.pop("title", "Equations of Motion"),
        **overrides,
    )
    db.add(n)
    await db.flush()
    return n


async def _seed_activity(db, user_id, **overrides):
    from app.models.models import Activity

    a = Activity(
        user_id=user_id,
        topic=overrides.pop("topic", "Topic"),
        difficulty=3,
        key_memory="k",
        created_at=overrides.pop("created_at", datetime.utcnow()),
        **overrides,
    )
    db.add(a)
    await db.flush()
    return a


async def _seed_review(db, user_id, activity_id, **overrides):
    from app.models.models import Review

    r = Review(
        user_id=user_id,
        activity_id=activity_id,
        status="completed",
        scheduled_for=datetime.utcnow(),
        completed_at=overrides.pop("completed_at", datetime.utcnow()),
        recalled=overrides.pop("recalled", True),
        rating=overrides.pop("rating", "easy"),
        **overrides,
    )
    db.add(r)
    await db.flush()
    return r


async def _create_classroom(client, **overrides):
    payload = {"name": "Class 9-A Physics", **overrides}
    resp = await client.post("/api/classrooms/", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _join(client, code, display_name="Priya Sharma"):
    return await client.post("/api/classrooms/join", json={"code": code, "display_name": display_name})


# --------------------------------------------------------------------------- #
# Lifecycle / roster
# --------------------------------------------------------------------------- #
async def test_created_classroom_visible_only_to_creator(client, as_user):
    created = await _create_classroom(client)

    mine = (await client.get("/api/classrooms/mine")).json()
    assert [c["id"] for c in mine["teaching"]] == [created["id"]]

    as_user(USER_B)
    mine_b = (await client.get("/api/classrooms/mine")).json()
    assert mine_b["teaching"] == []  # B must not see A's classroom


async def test_student_join_appears_in_enrolled_with_own_display_name(client, as_user):
    created = await _create_classroom(client)

    as_user(USER_B)
    resp = await _join(client, created["join_code"], display_name="Priya Sharma, Roll 14")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["classroom_id"] == created["id"]
    assert body["display_name"] == "Priya Sharma, Roll 14"

    mine = (await client.get("/api/classrooms/mine")).json()
    assert mine["teaching"] == []
    assert len(mine["enrolled"]) == 1
    assert mine["enrolled"][0]["display_name"] == "Priya Sharma, Roll 14"
    assert mine["enrolled"][0]["name"] == created["name"]
    # No teacher identity leak to the student.
    assert "teacher_user_id" not in mine["enrolled"][0]
    assert "teacher_email" not in mine["enrolled"][0]


async def test_roster_never_leaks_student_email_or_identity(client, as_user):
    created = await _create_classroom(client)

    as_user(USER_B)
    await _join(client, created["join_code"], display_name="Priya Sharma")

    as_user(USER_A)
    resp = await client.get(f"/api/classrooms/{created['id']}/students")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["students"]) == 1
    row = body["students"][0]
    assert row["display_name"] == "Priya Sharma"
    assert "email" not in row
    assert "student_user_id" not in row  # only the classroom-scoped member_id, never the account id


async def test_unknown_join_code_is_404(client):
    resp = await _join(client, "NOSUCHCODE")
    assert resp.status_code == 404


async def test_archived_classroom_join_code_is_404_same_shape_as_unknown(client):
    created = await _create_classroom(client)
    archive_resp = await client.patch(f"/api/classrooms/{created['id']}", json={"archived": True})
    assert archive_resp.status_code == 200

    unknown = await _join(client, "NOSUCHCODE")
    archived = await _join(client, created["join_code"])
    assert archived.status_code == unknown.status_code == 404
    assert archived.json()["detail"] == unknown.json()["detail"]  # same shape — don't leak which


# --------------------------------------------------------------------------- #
# Ownership / IDOR
# --------------------------------------------------------------------------- #
async def test_teacher_b_cannot_get_or_patch_teacher_a_classroom(client, as_user):
    created = await _create_classroom(client)

    as_user(USER_B)
    get_resp = await client.get(f"/api/classrooms/{created['id']}/overview")
    patch_resp = await client.patch(f"/api/classrooms/{created['id']}", json={"name": "Hijacked"})
    assert get_resp.status_code == 404  # 404, not 403 — don't confirm existence
    assert patch_resp.status_code == 404

    # A's classroom is untouched.
    as_user(USER_A)
    mine = (await client.get("/api/classrooms/mine")).json()
    assert mine["teaching"][0]["name"] == "Class 9-A Physics"


async def test_member_student_cannot_call_teacher_only_routes(client, as_user):
    created = await _create_classroom(client)

    as_user(USER_B)
    await _join(client, created["join_code"])

    # B belongs to the class but does not own it — teacher routes must 404,
    # not 200: membership is not ownership.
    patch_resp = await client.patch(f"/api/classrooms/{created['id']}", json={"name": "Hijacked"})
    gap_map_resp = await client.get(
        f"/api/classrooms/{created['id']}/gap-map", params={"roadmap_id": str(uuid.uuid4())}
    )
    students_resp = await client.get(f"/api/classrooms/{created['id']}/students")
    assert patch_resp.status_code == 404
    assert gap_map_resp.status_code == 404
    assert students_resp.status_code == 404


async def test_max_classrooms_per_teacher_cap(client):
    from app.core.config import settings

    for _ in range(settings.MAX_CLASSROOMS_PER_TEACHER):
        resp = await client.post("/api/classrooms/", json={"name": "Class"})
        assert resp.status_code == 201, resp.text

    over_cap = await client.post("/api/classrooms/", json={"name": "One too many"})
    assert over_cap.status_code == 403


async def test_removed_member_stats_stop_resolving(client, as_user, monkeypatch):
    _patch_postgres_only_helpers(monkeypatch)

    created = await _create_classroom(client)

    as_user(USER_B)
    join_resp = await _join(client, created["join_code"])
    member_id = join_resp.json()["member_id"]

    as_user(USER_A)
    detail_before = await client.get(f"/api/classrooms/{created['id']}/students/{member_id}")
    assert detail_before.status_code == 200  # exists before removal

    remove_resp = await client.delete(f"/api/classrooms/{created['id']}/members/{member_id}")
    assert remove_resp.status_code == 204

    detail_after = await client.get(f"/api/classrooms/{created['id']}/students/{member_id}")
    assert detail_after.status_code == 404  # removed student's stats stop resolving

    # Double-remove also 404s (not idempotent-200) — there's nothing left to remove.
    second_remove = await client.delete(f"/api/classrooms/{created['id']}/members/{member_id}")
    assert second_remove.status_code == 404


# --------------------------------------------------------------------------- #
# Privacy boundary (§4.2's "aggregation authorization rule" — load-bearing)
# --------------------------------------------------------------------------- #
async def test_overview_counts_only_assigned_roadmap_activity(client, db, as_user, monkeypatch):
    _patch_postgres_only_helpers(monkeypatch)

    created = await _create_classroom(client)
    assigned_roadmap = await _seed_roadmap(db, title="Physics 9 — assigned")
    other_roadmap = await _seed_roadmap(db, title="Chemistry 9 — NOT assigned")
    await db.commit()

    as_user(USER_B)
    join_resp = await _join(client, created["join_code"])
    student_id = uuid.UUID(USER_B.id)
    assert join_resp.status_code == 200

    as_user(USER_A)
    roadmaps_resp = await client.put(
        f"/api/classrooms/{created['id']}/roadmaps",
        json={"roadmap_ids": [str(assigned_roadmap.id)]},
    )
    assert roadmaps_resp.status_code == 200

    # In-scope: activity + completed review linked to the assigned roadmap.
    in_scope_activity = await _seed_activity(db, student_id, topic="Assigned card", roadmap_id=assigned_roadmap.id)
    await _seed_review(db, student_id, in_scope_activity.id, recalled=True)

    # Out-of-scope: activity linked to a roadmap NOT assigned to this classroom
    # (could equally be roadmap_id=None — a free-form/personal card).
    out_of_scope_activity = await _seed_activity(db, student_id, topic="Other-roadmap card", roadmap_id=other_roadmap.id)
    await _seed_review(db, student_id, out_of_scope_activity.id, recalled=True)
    await db.commit()

    resp = await client.get(f"/api/classrooms/{created['id']}/overview")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["active_last_7d"] == 1
    assert body["reviews_completed_7d"] == 1  # NOT 2 — the other-roadmap review must not count
    assert body["class_recall_rate_7d"] == 1.0


async def test_student_detail_review_metrics_reflect_only_assigned_roadmap_activity(client, db, as_user, monkeypatch):
    """The drill-down (GET .../students/{member_id}) reuses learner_stats.py
    scoped to (student, assigned roadmaps) — spec §4.3/§4.2. Seed 5 assigned-
    roadmap reviews (all recalled — clears REVIEW_METRICS_MIN) and 5
    NOT-assigned-roadmap reviews (all missed). If the scope filter leaked,
    recall_rate would read 0.5 and reviews_completed would read 10."""
    _patch_postgres_only_helpers(monkeypatch)

    created = await _create_classroom(client)
    assigned_roadmap = await _seed_roadmap(db, title="Physics 9 — assigned")
    other_roadmap = await _seed_roadmap(db, title="Chemistry 9 — NOT assigned")
    await db.commit()

    as_user(USER_B)
    join_resp = await _join(client, created["join_code"])
    member_id = join_resp.json()["member_id"]
    student_id = uuid.UUID(USER_B.id)

    as_user(USER_A)
    await client.put(
        f"/api/classrooms/{created['id']}/roadmaps",
        json={"roadmap_ids": [str(assigned_roadmap.id)]},
    )

    for i in range(5):
        act = await _seed_activity(db, student_id, topic=f"assigned-{i}", roadmap_id=assigned_roadmap.id)
        await _seed_review(db, student_id, act.id, recalled=True)
    for i in range(5):
        # Could equally be roadmap_id=None (a personal/free-form card) —
        # any non-assigned roadmap_id must be excluded the same way.
        act = await _seed_activity(db, student_id, topic=f"other-{i}", roadmap_id=other_roadmap.id)
        await _seed_review(db, student_id, act.id, recalled=False)
    await db.commit()

    resp = await client.get(f"/api/classrooms/{created['id']}/students/{member_id}")
    assert resp.status_code == 200, resp.text
    metrics = resp.json()["review_metrics"]
    assert metrics["enough_data"] is True
    assert metrics["reviews_completed"] == 5  # NOT 10 — the other-roadmap reviews must not count
    assert metrics["recall_rate"] == 1.0       # NOT 0.5 — the other-roadmap misses must not count


async def test_gap_map_only_shows_nodes_of_the_queried_roadmap(client, db, as_user, monkeypatch):
    _patch_postgres_only_helpers(monkeypatch)

    created = await _create_classroom(client)
    assigned_roadmap = await _seed_roadmap(db, title="Physics 9 — assigned")
    other_roadmap = await _seed_roadmap(db, title="Chemistry 9 — NOT assigned")
    assigned_node = await _seed_node(db, assigned_roadmap.id, title="Equations of Motion")
    other_node = await _seed_node(db, other_roadmap.id, title="Mole Concept")
    await db.commit()

    as_user(USER_B)
    await _join(client, created["join_code"])
    student_id = uuid.UUID(USER_B.id)

    as_user(USER_A)
    await client.put(
        f"/api/classrooms/{created['id']}/roadmaps",
        json={"roadmap_ids": [str(assigned_roadmap.id)]},
    )

    # Student is weak on BOTH nodes (two consecutive misses each) — only the
    # assigned-roadmap node may ever surface in this classroom's gap map.
    assigned_activity = await _seed_activity(db, student_id, topic="Assigned", node_id=assigned_node.id)
    await _seed_review(db, student_id, assigned_activity.id, recalled=False)
    await _seed_review(db, student_id, assigned_activity.id, recalled=False)
    other_activity = await _seed_activity(db, student_id, topic="Other", node_id=other_node.id)
    await _seed_review(db, student_id, other_activity.id, recalled=False)
    await _seed_review(db, student_id, other_activity.id, recalled=False)
    await db.commit()

    resp = await client.get(
        f"/api/classrooms/{created['id']}/gap-map", params={"roadmap_id": str(assigned_roadmap.id)}
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    node_ids = [n["node_id"] for n in body["nodes"]]
    assert node_ids == [str(assigned_node.id)]  # never the other roadmap's node
    assert body["nodes"][0]["counts"]["weak"] == 1


async def test_gap_map_rejects_unassigned_roadmap_id(client, db, as_user):
    created = await _create_classroom(client)
    other_roadmap = await _seed_roadmap(db, title="Not assigned")
    await db.commit()

    resp = await client.get(
        f"/api/classrooms/{created['id']}/gap-map", params={"roadmap_id": str(other_roadmap.id)}
    )
    assert resp.status_code == 400
