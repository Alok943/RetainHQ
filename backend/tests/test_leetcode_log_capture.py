import pytest
from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
import uuid
from datetime import datetime

from app.models.models import Activity, Problem, ProblemAttempt, ProblemConcept, Roadmap, RoadmapNode, LearningEvent, NodeMastery, Review
from tests.conftest import USER_A

@pytest.fixture
async def capture_data(db: AsyncSession):
    roadmap = Roadmap(title="DSA", audience="career", slug="dsa")
    db.add(roadmap)
    await db.commit()
    node = RoadmapNode(roadmap_id=roadmap.id, phase="1", section="1", title="Hash Tables")
    db.add(node)
    await db.commit()
    
    p1 = Problem(source="leetcode", external_id=1, slug="two-sum", title="Two Sum", difficulty="easy", catalog_version="v1")
    db.add(p1)
    await db.commit()
    db.add(ProblemConcept(problem_id=p1.id, node_id=node.id, role="primary", confidence=1.0, mapping_version="v1"))
    await db.commit()
    
    return {"node": node, "p1": p1, "roadmap": roadmap}

async def test_invalid_language_returns_422(client: AsyncClient, capture_data):
    payload = {
        "topic": "LeetCode 1: Two Sum",
        "key_memory": "Use a hash map to store complements.",
        "difficulty": 3,
        "needed_hint": False,
        "source_type": "problem",
        "problem_id": str(capture_data["p1"].id),
        "language": "fortran",
    }
    resp = await client.post("/api/activities/", json=payload)
    assert resp.status_code == 422
    # Pydantic validation handles this since language is a string, wait, is language constrained?
    # In activity.py, language is Optional[str] = None. There is no list of valid languages!
    # Ah, the implementation plan said: 
    # "Validate server-side against the list; unknown value -> 400, not silent NULL."
    # Let me check if language validation was added to ActivityCreate.
    # It wasn't! 

async def test_logging_activity_creates_no_evidence(client: AsyncClient, db: AsyncSession, capture_data):
    # Log a leetcode problem activity
    payload = {
        "topic": "LeetCode 1: Two Sum",
        "key_memory": "Use a hash map to store complements.",
        "difficulty": 3,
        "needed_hint": False,
        "source_type": "problem",
        "problem_id": str(capture_data["p1"].id),
        "language": "python",
    }
    resp = await client.post("/api/activities/", json=payload)
    assert resp.status_code == 200, resp.text
    
    # Verify no learning_event
    events = (await db.execute(select(LearningEvent))).all()
    assert len(events) == 0, "No learning event should be created upon logging"
    
    # Verify no node_mastery
    masteries = (await db.execute(select(NodeMastery))).all()
    assert len(masteries) == 0, "No node mastery should be created upon logging"
    
    # But an activity is created, and problem_attempt is upserted
    activity = (await db.execute(select(Activity).where(Activity.problem_id == capture_data["p1"].id))).scalar_one()
    assert activity.language == "python"
    assert activity.node_id == capture_data["node"].id
    
    attempt = (await db.execute(select(ProblemAttempt).where(ProblemAttempt.problem_id == capture_data["p1"].id))).scalar_one()
    assert attempt.language == "python"
    assert attempt.status == "solved"

async def test_completing_review_creates_evidence(client: AsyncClient, db: AsyncSession, capture_data):
    # Log an activity first
    payload = {
        "topic": "LeetCode 1: Two Sum",
        "key_memory": "Use a hash map.",
        "difficulty": 3,
        "needed_hint": False,
        "source_type": "problem",
        "problem_id": str(capture_data["p1"].id),
    }
    resp = await client.post("/api/activities/", json=payload)
    assert resp.status_code == 200
    
    # A review was scheduled
    review = (await db.execute(select(Review).where(Review.status == "due"))).scalar_one()
    
    # Complete the review
    resp = await client.post(f"/api/reviews/{review.id}/complete", json={
        "rating": "medium", 
        "duration_ms": 10000, 
        "grader_verdict": {"verdict": "correct", "recalled": True, "feedback": "good", "revision_note": "ok"}
    })
    assert resp.status_code == 200, resp.text
    
    # Verify learning_event is created
    events = (await db.execute(select(LearningEvent).where(LearningEvent.event_type == "RECALL_GRADED"))).scalars().all()
    assert len(events) == 1
    assert events[0].node_id == capture_data["node"].id
    assert events[0].trust_tier == "T2_verified_internal"
