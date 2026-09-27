"""Quiz v2 Quick mode — server-side MCQ verification and rating derivation
(docs/IMPLEMENTATION-quiz-capture-v2.md Step 5.3): "never trust a client
`correct: true`". These exercise app.api.routes.reviews.complete_review's
override of rating/recalled when question_format='mcq' and the served item
resolves in the synced answer key (app.services.recall_answer_key).
"""
from unittest.mock import patch

ACTIVITY_PAYLOAD = {
    "topic": "Binary search",
    "difficulty": 3,
    "needed_hint": False,
    "key_memory": "Halve the search space each step; O(log n).",
}

SERVED_ID = "dsa/fake-lesson#0"
ANSWER_KEY_ENTRY = {"correct_index": 0, "options_count": 4}


async def _due_review_id(client):
    resp = await client.post("/api/activities/", json=ACTIVITY_PAYLOAD)
    assert resp.status_code == 200
    return (await client.get("/api/reviews/due")).json()[0]["id"]


def _lookup_patch(entry=ANSWER_KEY_ENTRY):
    return patch(
        "app.api.routes.reviews.recall_answer_key.lookup",
        lambda served_id: entry if served_id == SERVED_ID else None,
    )


async def _complete_mcq(client, review_id, selected_option_index, hint_used=False, client_rating="easy", client_recalled=True):
    # The client's own rating/recalled are deliberately wrong here (always
    # "easy"/True) to prove the server ignores them on the verified MCQ path.
    return await client.post(
        f"/api/reviews/{review_id}/complete",
        json={
            "rating": client_rating,
            "recalled": client_recalled,
            "mode": "quick",
            "question_format": "mcq",
            "question_source": "lesson",
            "question_served": SERVED_ID,
            "selected_option_index": selected_option_index,
            "hint_used": hint_used,
        },
    )


async def test_correct_no_hint_is_medium_and_recalled(client):
    review_id = await _due_review_id(client)
    with _lookup_patch():
        resp = await _complete_mcq(client, review_id, selected_option_index=0, hint_used=False)
    assert resp.status_code == 200
    body = resp.json()
    assert body["rating"] == "medium"
    assert body["recalled"] is True


async def test_correct_with_hint_is_hard_and_recalled(client):
    review_id = await _due_review_id(client)
    with _lookup_patch():
        resp = await _complete_mcq(client, review_id, selected_option_index=0, hint_used=True)
    assert resp.status_code == 200
    body = resp.json()
    assert body["rating"] == "hard"
    assert body["recalled"] is True


async def test_wrong_option_is_hard_and_missed(client):
    review_id = await _due_review_id(client)
    with _lookup_patch():
        resp = await _complete_mcq(client, review_id, selected_option_index=2, hint_used=False)
    assert resp.status_code == 200
    body = resp.json()
    assert body["rating"] == "hard"
    assert body["recalled"] is False


async def test_i_dont_know_is_hard_and_missed(client):
    review_id = await _due_review_id(client)
    with _lookup_patch():
        resp = await _complete_mcq(client, review_id, selected_option_index=None, hint_used=False)
    assert resp.status_code == 200
    body = resp.json()
    assert body["rating"] == "hard"
    assert body["recalled"] is False


async def test_client_reported_correct_is_ignored_when_server_disagrees(client):
    """The core trust boundary: client claims easy/recalled=True, but picked
    the wrong option — the server's own verification must win."""
    review_id = await _due_review_id(client)
    with _lookup_patch():
        resp = await _complete_mcq(
            client, review_id, selected_option_index=3, hint_used=False,
            client_rating="easy", client_recalled=True,
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["rating"] == "hard"
    assert body["recalled"] is False


async def test_missing_answer_key_falls_back_to_client(client):
    """A question_served the server's manifest doesn't know (stale sync, or a
    manual/QuestionSet MCQ not yet covered) must never fail the completion —
    it just skips verification and trusts the client, same as every other
    (non-MCQ) path today."""
    review_id = await _due_review_id(client)
    with _lookup_patch(entry=None):
        resp = await client.post(
            f"/api/reviews/{review_id}/complete",
            json={
                "rating": "easy",
                "recalled": True,
                "mode": "quick",
                "question_format": "mcq",
                "question_source": "lesson",
                "question_served": "unknown/slug#9",
                "selected_option_index": 1,
            },
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["rating"] == "easy"
    assert body["recalled"] is True


async def test_typed_mode_completion_is_unaffected(client):
    """Regression: a plain typed-mode /complete (no question_format, exactly
    today's request shape) must behave exactly as before."""
    review_id = await _due_review_id(client)
    resp = await client.post(
        f"/api/reviews/{review_id}/complete",
        json={"rating": "hard", "recalled": True, "duration_ms": 5000},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["rating"] == "hard"
    assert body["recalled"] is True
    assert body["question_format"] is None
