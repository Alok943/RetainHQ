"""
reviews.duration_ms: persisted when plausible, clamped to NULL otherwise
(HANDOFF-sentry-push-analytics.md C1).
"""
ACTIVITY_PAYLOAD = {
    "topic": "Binary search",
    "difficulty": 3,
    "needed_hint": False,
    "key_memory": "Halve the search space each step; O(log n).",
}


async def _due_review_id(client):
    resp = await client.post("/api/activities/", json=ACTIVITY_PAYLOAD)
    assert resp.status_code == 200
    return (await client.get("/api/reviews/due")).json()[0]["id"]


async def test_plausible_duration_is_persisted(client):
    review_id = await _due_review_id(client)
    resp = await client.post(
        f"/api/reviews/{review_id}/complete",
        json={"rating": "easy", "recalled": True, "duration_ms": 8_500},
    )
    assert resp.status_code == 200
    assert resp.json()["duration_ms"] == 8_500


async def test_absent_duration_stays_null(client):
    review_id = await _due_review_id(client)
    resp = await client.post(
        f"/api/reviews/{review_id}/complete",
        json={"rating": "easy", "recalled": True},
    )
    assert resp.status_code == 200
    assert resp.json()["duration_ms"] is None


async def test_over_30_minutes_is_clamped_to_null(client):
    review_id = await _due_review_id(client)
    resp = await client.post(
        f"/api/reviews/{review_id}/complete",
        json={"rating": "easy", "recalled": True, "duration_ms": 1_800_001},
    )
    assert resp.status_code == 200
    assert resp.json()["duration_ms"] is None


async def test_zero_or_negative_is_clamped_to_null(client):
    review_id = await _due_review_id(client)
    resp = await client.post(
        f"/api/reviews/{review_id}/complete",
        json={"rating": "easy", "recalled": True, "duration_ms": 0},
    )
    assert resp.status_code == 200
    assert resp.json()["duration_ms"] is None


async def test_exactly_30_minutes_is_kept(client):
    review_id = await _due_review_id(client)
    resp = await client.post(
        f"/api/reviews/{review_id}/complete",
        json={"rating": "easy", "recalled": True, "duration_ms": 1_800_000},
    )
    assert resp.status_code == 200
    assert resp.json()["duration_ms"] == 1_800_000
