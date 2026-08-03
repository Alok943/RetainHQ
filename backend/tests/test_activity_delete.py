"""DELETE /api/activities/{id} — ownership, cascade, and the evidence boundary.

The load-bearing property: deleting a card must not retract evidence a
completed review already wrote. LearningEvent carries no FK back to Activity
(entity_id=review.id, no relationship) precisely so that deleting a mislabeled
card can never un-earn mastery already recorded from it (D-038: once written,
evidence stands).
"""
import uuid
from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.models import (
    Activity, LearningEvent, NodeMastery, Problem, ProblemAttempt,
    ProblemConcept, QuestionSet, Review, Roadmap, RoadmapNode,
)
from tests.conftest import USER_A, USER_B


@pytest.fixture
async def node(db: AsyncSession):
    roadmap = Roadmap(title="DSA", audience="career", slug="dsa")
    db.add(roadmap)
    await db.commit()
    n = RoadmapNode(roadmap_id=roadmap.id, phase="1", section="1", title="Hash Tables")
    db.add(n)
    await db.commit()
    return n


async def _create_activity(client: AsyncClient, **over) -> dict:
    payload = {
        "topic": "Two Sum",
        "key_memory": "Hash map of complements.",
        "difficulty": 3,
        "needed_hint": False,
    }
    payload.update(over)
    resp = await client.post("/api/activities/", json=payload)
    assert resp.status_code == 200, resp.text
    return resp.json()


async def test_owner_can_delete_their_own_card(client: AsyncClient, db: AsyncSession):
    created = await _create_activity(client)
    activity_id = created["id"]

    resp = await client.delete(f"/api/activities/{activity_id}")
    assert resp.status_code == 204

    assert (await db.execute(select(Activity).where(Activity.id == uuid.UUID(activity_id)))).scalars().first() is None


async def test_delete_cascades_reviews_and_question_sets(client: AsyncClient, db: AsyncSession):
    created = await _create_activity(client)
    activity_id = uuid.UUID(created["id"])

    # Give it a second review row and a question set, so cascade has something
    # real to cascade (the initial log already scheduled one review).
    db.add(Review(
        activity_id=activity_id, user_id=uuid.UUID(USER_A.id), status="due",
        scheduled_for=datetime.utcnow() + timedelta(days=1),
    ))
    db.add(QuestionSet(activity_id=activity_id, user_id=uuid.UUID(USER_A.id), depth="main", items=[]))
    await db.commit()

    assert (await db.execute(select(Review).where(Review.activity_id == activity_id))).scalars().all()
    assert (await db.execute(select(QuestionSet).where(QuestionSet.activity_id == activity_id))).scalars().all()

    resp = await client.delete(f"/api/activities/{activity_id}")
    assert resp.status_code == 204

    assert (await db.execute(select(Review).where(Review.activity_id == activity_id))).scalars().all() == []
    assert (await db.execute(select(QuestionSet).where(QuestionSet.activity_id == activity_id))).scalars().all() == []


async def test_deleting_a_reviewed_card_does_not_retract_its_evidence(
    client: AsyncClient, db: AsyncSession, node
):
    """The card that produced a RECALL_GRADED event can be deleted; the event
    (and any mastery it moved) must survive it."""
    created = await _create_activity(client, source_type="lesson", node_id=str(node.id))
    activity_id = uuid.UUID(created["id"])

    review = (await db.execute(select(Review).where(Review.activity_id == activity_id))).scalars().first()
    resp = await client.post(f"/api/reviews/{review.id}/complete", json={
        "rating": "medium", "duration_ms": 5000,
        "grader_verdict": {"verdict": "correct", "recalled": True, "feedback": "ok", "revision_note": "ok"},
    })
    assert resp.status_code == 200, resp.text

    events_before = (await db.execute(select(LearningEvent))).scalars().all()
    assert len(events_before) == 1

    resp = await client.delete(f"/api/activities/{activity_id}")
    assert resp.status_code == 204

    events_after = (await db.execute(select(LearningEvent))).scalars().all()
    assert len(events_after) == 1, "evidence must not be retracted by deleting the card that earned it"
    assert events_after[0].id == events_before[0].id


async def test_delete_leaves_problem_attempt_intact(client: AsyncClient, db: AsyncSession, node):
    """problem_attempts is the roadmap's separate 'solved' checkbox
    (IMPLEMENTATION-problem-capture.md) — deleting a mislabeled review card
    must not un-mark the problem as solved."""
    p1 = Problem(source="leetcode", external_id=1, slug="two-sum", title="Two Sum",
                 difficulty="easy", catalog_version="v1")
    db.add(p1)
    await db.commit()
    db.add(ProblemConcept(problem_id=p1.id, node_id=node.id, role="primary", confidence=1.0, mapping_version="v1"))
    await db.commit()

    created = await _create_activity(
        client, source_type="problem", problem_id=str(p1.id), language="python"
    )
    activity_id = created["id"]

    resp = await client.delete(f"/api/activities/{activity_id}")
    assert resp.status_code == 204

    attempt = (
        await db.execute(select(ProblemAttempt).where(ProblemAttempt.problem_id == p1.id))
    ).scalars().first()
    assert attempt is not None
    assert attempt.status == "solved"


async def test_deleting_someone_elses_card_404s(client: AsyncClient, as_user):
    as_user(USER_A)
    created = await _create_activity(client)

    as_user(USER_B)
    resp = await client.delete(f"/api/activities/{created['id']}")
    assert resp.status_code == 404

    as_user(USER_A)
    resp = await client.get("/api/activities/")
    ids = {a["id"] for a in resp.json()}
    assert created["id"] in ids, "the card must survive an IDOR attempt"


async def test_deleting_unknown_id_404s(client: AsyncClient):
    resp = await client.delete(f"/api/activities/{uuid.uuid4()}")
    assert resp.status_code == 404
