"""
metric_events: allowlisted client POST, RLS on the table, and the syllabus
commit flow's server-side extraction_edit_delta producer.
"""
import uuid
from sqlalchemy import text

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
