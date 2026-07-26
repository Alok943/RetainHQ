"""
metric_events: allowlisted client POST, RLS on the table, and the syllabus
commit flow's server-side extraction_edit_delta producer.
"""
import uuid
from sqlalchemy import select, text

from app.models.models import MetricEvent
from app.services.metrics import get_latest_consent_tier
from tests.conftest import USER_A, USER_B

DRAFT = {
    "title": "Operating Systems",
    "description": "Sem 5 core",
    "units": [
        {
            "title": "Unit I",
            "topics": [{"title": "Define a process", "description": "PCB, states"}],
        }
    ],
}


async def test_allowlisted_event_type_succeeds(client):
    resp = await client.post(
        "/api/metrics/events",
        json={"event_type": "review_depth_chosen", "payload": {"depth": "deep"}},
    )
    assert resp.status_code == 204


async def test_disallowed_event_type_rejected(client):
    resp = await client.post(
        "/api/metrics/events",
        json={"event_type": "something_not_allowlisted", "payload": {}},
    )
    assert resp.status_code == 422


async def test_oversized_payload_rejected(client):
    resp = await client.post(
        "/api/metrics/events",
        json={"event_type": "review_depth_chosen", "payload": {"blob": "x" * 3000}},
    )
    assert resp.status_code == 422


async def test_syllabus_commit_records_edit_delta(client, db):
    edit_delta = {"topics_original": 5, "topics_final": 4, "topics_added": 1, "topics_removed": 2}
    resp = await client.post("/api/syllabus/commit", json={**DRAFT, "edit_delta": edit_delta})
    assert resp.status_code == 201
    roadmap_id = resp.json()["roadmap_id"]

    row = (await db.execute(
        text("select event_type, entity_id, payload from metric_events where event_type = 'extraction_edit_delta'")
    )).first()
    assert row is not None
    # SQLite's Uuid variant round-trips as a bare hex string (no dashes);
    # normalize both sides through uuid.UUID before comparing.
    assert str(uuid.UUID(str(row[1]))) == roadmap_id
    import json
    payload = row[2] if isinstance(row[2], dict) else json.loads(row[2])
    assert payload == edit_delta


async def test_syllabus_commit_without_edit_delta_records_nothing(client, db):
    resp = await client.post("/api/syllabus/commit", json=DRAFT)
    assert resp.status_code == 201
    row = (await db.execute(text("select 1 from metric_events"))).first()
    assert row is None


# --- companion_consent (IMPLEMENTATION-companion-consent.md §4.1/§6) -----------

async def test_companion_consent_allowlisted(client):
    resp = await client.post(
        "/api/metrics/events",
        json={"event_type": "companion_consent", "payload": {"tier": "cloud", "copy_version": "v1", "surface": "popup"}},
    )
    assert resp.status_code == 204


async def test_companion_consent_unknown_event_type_still_422s(client):
    """Allowlisting one more event type must not accidentally open the gate —
    the validator is a fixed set, not a prefix/pattern match."""
    resp = await client.post(
        "/api/metrics/events",
        json={"event_type": "companion_consent_debug", "payload": {}},
    )
    assert resp.status_code == 422


async def test_companion_consent_record_has_tier_and_server_set_timestamp(client, db):
    user_id = uuid.UUID(USER_A.id)
    resp = await client.post(
        "/api/metrics/events",
        json={"event_type": "companion_consent", "payload": {"tier": "nano", "copy_version": "v1", "surface": "popup"}},
    )
    assert resp.status_code == 204

    row = (
        await db.execute(
            select(MetricEvent).where(MetricEvent.user_id == user_id, MetricEvent.event_type == "companion_consent")
        )
    ).scalar_one()
    assert row.payload["tier"] == "nano"
    # MetricEventIn carries no client-settable timestamp field at all — this
    # is a structural guarantee, not a value comparison against a spoofed one.
    assert row.created_at is not None

    tier = await get_latest_consent_tier(db, user_id)
    assert tier == "nano"


async def test_companion_consent_latest_tier_wins_on_repeated_choice(client, db):
    user_id = uuid.UUID(USER_A.id)
    for tier in ("cloud", "titles"):
        resp = await client.post(
            "/api/metrics/events",
            json={"event_type": "companion_consent", "payload": {"tier": tier, "copy_version": "v1", "surface": "popup"}},
        )
        assert resp.status_code == 204

    assert await get_latest_consent_tier(db, user_id) == "titles"


async def test_companion_consent_is_scoped_per_user(client, db, as_user):
    """No IDOR surface exists here by construction — user_id always comes from
    the auth dependency, never the client — but pin the outcome directly:
    each user's consent event lands under their own id and nobody else's."""
    user_a_id = uuid.UUID(USER_A.id)
    user_b_id = uuid.UUID(USER_B.id)

    resp_a = await client.post(
        "/api/metrics/events",
        json={"event_type": "companion_consent", "payload": {"tier": "cloud", "copy_version": "v1", "surface": "popup"}},
    )
    assert resp_a.status_code == 204

    as_user(USER_B)
    resp_b = await client.post(
        "/api/metrics/events",
        json={"event_type": "companion_consent", "payload": {"tier": "titles", "copy_version": "v1", "surface": "popup"}},
    )
    assert resp_b.status_code == 204

    assert await get_latest_consent_tier(db, user_a_id) == "cloud"
    assert await get_latest_consent_tier(db, user_b_id) == "titles"

    a_events = (
        await db.execute(select(MetricEvent).where(MetricEvent.user_id == user_a_id, MetricEvent.event_type == "companion_consent"))
    ).scalars().all()
    assert len(a_events) == 1
    assert a_events[0].payload["tier"] == "cloud"  # never overwritten by B's POST
