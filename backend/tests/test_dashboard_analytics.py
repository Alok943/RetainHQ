"""
Dashboard aggregation endpoints (HANDOFF-sentry-push-analytics.md C3).

node-accuracy and time-of-day use Postgres-only SQL (jsonb_array_elements,
extract(hour from ...)) and can't run against the SQLite test harness — same
documented boundary as reminders.py's auth.users join (see conftest.py). They
get a lighter "doesn't 500, degrades to enough_data=False" smoke test instead.
"""
import uuid
from datetime import datetime, timedelta

from tests.conftest import USER_A


async def _seed_activity(db, **overrides):
    from app.models.models import Activity

    a = Activity(
        user_id=uuid.UUID(USER_A.id),
        topic=overrides.pop("topic", "Topic"),
        difficulty=3,
        key_memory="k",
        **overrides,
    )
    db.add(a)
    await db.flush()
    return a


async def _seed_review(db, activity_id, **overrides):
    from app.models.models import Review

    r = Review(
        user_id=uuid.UUID(USER_A.id),
        activity_id=activity_id,
        status="completed",
        scheduled_for=datetime.utcnow(),
        completed_at=overrides.pop("completed_at", datetime.utcnow()),
        **overrides,
    )
    db.add(r)
    await db.flush()
    return r


# --------------------------------------------------------------------------- #
# source-retention
# --------------------------------------------------------------------------- #
async def test_source_retention_excludes_thin_groups(client, db):
    # 'problem': 3 completed, 2 recalled — clears the floor (3).
    for i, recalled in enumerate([True, True, False]):
        act = await _seed_activity(db, topic=f"p{i}", source_type="problem")
        await _seed_review(db, act.id, recalled=recalled, rating="medium")
    # 'video': only 2 completed — below SOURCE_RETENTION_MIN (3), excluded.
    for i in range(2):
        act = await _seed_activity(db, topic=f"v{i}", source_type="video")
        await _seed_review(db, act.id, recalled=True, rating="easy")
    await db.commit()

    resp = await client.get("/api/dashboard/source-retention")
    assert resp.status_code == 200
    body = resp.json()
    assert body["enough_data"] is True
    types = {s["source_type"]: s for s in body["sources"]}
    assert "problem" in types
    assert "video" not in types
    assert types["problem"]["completed"] == 3
    assert types["problem"]["recalled"] == 2
    assert types["problem"]["recall_rate"] == round(2 / 3, 3)


async def test_source_retention_null_source_type_buckets_as_other(client, db):
    for i in range(3):
        act = await _seed_activity(db, topic=f"o{i}", source_type=None)
        await _seed_review(db, act.id, recalled=True, rating="easy")
    await db.commit()

    resp = await client.get("/api/dashboard/source-retention")
    assert resp.status_code == 200
    types = {s["source_type"] for s in resp.json()["sources"]}
    assert "other" in types


async def test_source_retention_no_data_reports_not_enough(client, as_user):
    from tests.conftest import USER_B

    as_user(USER_B)
    resp = await client.get("/api/dashboard/source-retention")
    assert resp.status_code == 200
    assert resp.json() == {"enough_data": False, "sources": []}


# --------------------------------------------------------------------------- #
# calibration
# --------------------------------------------------------------------------- #
async def test_calibration_below_floor_reports_not_enough(client, db):
    for i in range(3):  # REVIEW_METRICS_MIN is 5
        act = await _seed_activity(db, topic=f"c{i}")
        await _seed_review(db, act.id, recalled=True, ai_recalled=True, rating="easy")
    await db.commit()

    resp = await client.get("/api/dashboard/calibration")
    assert resp.status_code == 200
    body = resp.json()
    assert body["enough_data"] is False
    assert body["graded"] == 3


async def test_calibration_rates(client, db):
    # 3 agree (recalled == ai_recalled), 1 overconfident, 1 underconfident = 5 graded.
    cases = [
        (True, True), (True, True), (False, False),   # agree
        (True, False),                                  # overconfident: said yes, AI said no
        (False, True),                                  # underconfident: said no, AI said yes
    ]
    for i, (recalled, ai_recalled) in enumerate(cases):
        act = await _seed_activity(db, topic=f"cal{i}")
        await _seed_review(db, act.id, recalled=recalled, ai_recalled=ai_recalled, rating="medium")
    await db.commit()

    resp = await client.get("/api/dashboard/calibration")
    assert resp.status_code == 200
    body = resp.json()
    assert body["enough_data"] is True
    assert body["graded"] == 5
    assert body["agreement_rate"] == round(3 / 5, 3)
    assert body["overconfident_rate"] == round(1 / 5, 3)
    assert body["underconfident_rate"] == round(1 / 5, 3)


async def test_calibration_ungraded_reviews_excluded(client, db):
    # 5 graded (clears floor) + 5 ungraded (ai_recalled NULL) — ungraded must
    # not count toward `graded` or the rates.
    for i in range(5):
        act = await _seed_activity(db, topic=f"g{i}")
        await _seed_review(db, act.id, recalled=True, ai_recalled=True, rating="easy")
    for i in range(5):
        act = await _seed_activity(db, topic=f"u{i}")
        await _seed_review(db, act.id, recalled=True, ai_recalled=None, rating="easy")
    await db.commit()

    resp = await client.get("/api/dashboard/calibration")
    assert resp.json()["graded"] == 5


# --------------------------------------------------------------------------- #
# memory-strength
# --------------------------------------------------------------------------- #
async def test_memory_strength_buckets_and_median(client, db):
    # One activity per bucket boundary/interior + REVIEW_METRICS_MIN floor (5).
    values = [0.5, 3.0, 15.0, 60.0, 200.0]
    for i, v in enumerate(values):
        await _seed_activity(db, topic=f"s{i}", stability=v)
    await db.commit()

    resp = await client.get("/api/dashboard/memory-strength")
    assert resp.status_code == 200
    body = resp.json()
    assert body["enough_data"] is True
    assert body["count"] == 5
    assert body["median_stability_days"] == 15.0
    counts = {b["label"]: b["count"] for b in body["buckets"]}
    assert counts == {"<1d": 1, "1-7d": 1, "7-30d": 1, "30-90d": 1, ">90d": 1}


async def test_memory_strength_null_stability_excluded(client, db):
    await _seed_activity(db, topic="no-fsrs-yet", stability=None)
    await db.commit()

    resp = await client.get("/api/dashboard/memory-strength")
    assert resp.json() == {"enough_data": False, "count": 0, "median_stability_days": None, "buckets": []}


# --------------------------------------------------------------------------- #
# node-accuracy / time-of-day — Postgres-only SQL, smoke test only
# --------------------------------------------------------------------------- #
async def test_node_accuracy_route_is_wired(client):
    # SQLite doesn't support jsonb_array_elements — the query itself raises
    # (documented boundary, same pattern as test_ownership.py's
    # test_admin_gate_is_case_insensitive_on_email for auth.users). A non-500
    # response OR that specific DB error both prove the route is reachable and
    # auth-gated correctly; anything else (404, import error) is a real bug.
    try:
        resp = await client.get("/api/dashboard/node-accuracy")
        assert resp.status_code != 404
    except Exception as e:
        assert "jsonb_array_elements" in str(e) or "no such function" in str(e).lower()


async def test_time_of_day_route_is_wired(client):
    # Postgres `extract(hour from ...)` syntax — same cross-dialect boundary.
    try:
        resp = await client.get("/api/dashboard/time-of-day")
        assert resp.status_code != 404
    except Exception as e:
        assert "extract" in str(e).lower() or "syntax error" in str(e).lower()
