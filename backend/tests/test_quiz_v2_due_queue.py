"""Quiz v2 /reviews/due changes (docs/IMPLEMENTATION-quiz-capture-v2.md Step
5.1/5.4): ordered by lowest current retrievability (most at-risk first,
instead of oldest scheduled_for), and each card carries topic_key/topic_label/
last_question_served.
"""
import uuid
from datetime import datetime, timedelta

from sqlalchemy import select

from app.models.models import Activity, Review

ACTIVITY_PAYLOAD = {
    "topic": "Binary search",
    "difficulty": 3,
    "needed_hint": False,
    "key_memory": "Halve the search space each step; O(log n).",
}


async def _log_activity(client, topic):
    resp = await client.post("/api/activities/", json={**ACTIVITY_PAYLOAD, "topic": topic})
    assert resp.status_code == 200
    return resp.json()["id"]


async def test_due_queue_orders_lowest_retrievability_first(client, db):
    # Only a user's very FIRST-ever activity gets an immediate demo review;
    # a second one's first review waits until tomorrow — so force both
    # reviews due now directly, then give the activities distinguishable
    # FSRS state (a brand-new card, stability=None, is already the
    # maximally-at-risk case covered by test_due_card_carries_topic_key_and_label).
    await _log_activity(client, "Weak card")
    await _log_activity(client, "Strong card")

    activities = (await db.execute(select(Activity).order_by(Activity.created_at))).scalars().all()
    weak, strong = activities[0], activities[1]

    now = datetime.utcnow()
    # Same stability, but the weak card was reviewed much longer ago — its
    # predicted retrievability right now is lower (more decayed).
    weak.stability = 5.0
    weak.difficulty_fsrs = 5.0
    weak.last_reviewed_at = now - timedelta(days=20)
    strong.stability = 5.0
    strong.difficulty_fsrs = 5.0
    strong.last_reviewed_at = now - timedelta(hours=1)
    db.add(weak)
    db.add(strong)

    reviews = (await db.execute(select(Review).where(Review.status == "due"))).scalars().all()
    for review in reviews:
        review.scheduled_for = now
        db.add(review)
    await db.commit()

    resp = await client.get("/api/reviews/due")
    assert resp.status_code == 200
    topics = [r["activity"]["topic"] for r in resp.json()]
    assert topics.index("Weak card") < topics.index("Strong card")


async def test_due_card_carries_topic_key_and_label(client):
    await _log_activity(client, "Standalone topic with no node/roadmap link")
    resp = await client.get("/api/reviews/due")
    assert resp.status_code == 200
    card = resp.json()[0]
    assert card["topic_key"] == f"standalone:{card['activity_id']}"
    assert card["topic_label"] == "Standalone topic with no node/roadmap link"


async def test_last_question_served_reflects_most_recent_completed_review(client, db):
    activity_id = await _log_activity(client, "Repeats across sessions")
    review_id = (await client.get("/api/reviews/due")).json()[0]["id"]

    complete = await client.post(
        f"/api/reviews/{review_id}/complete",
        json={
            "rating": "medium", "recalled": True, "mode": "quick",
            "question_format": "typed", "question_source": "lesson",
            "question_served": "dsa/some-lesson#2",
        },
    )
    assert complete.status_code == 200

    # A "medium" outcome schedules the next review in the future — force it
    # due now so /due surfaces it and we can inspect the rotation hint.
    next_review = (
        await db.execute(select(Review).where(Review.activity_id == uuid.UUID(activity_id), Review.status == "due"))
    ).scalars().first()
    next_review.scheduled_for = datetime.utcnow()
    db.add(next_review)
    await db.commit()

    resp = await client.get("/api/reviews/due")
    assert resp.status_code == 200
    card = next(r for r in resp.json() if r["activity_id"] == activity_id)
    assert card["last_question_served"] == "dsa/some-lesson#2"
