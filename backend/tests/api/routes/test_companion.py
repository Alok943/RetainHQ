import uuid
from datetime import datetime, timezone
import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.core.security import SupabaseUser
from app.models.models import LearningEvent, NodeMastery, Roadmap, RoadmapNode

@pytest.fixture
async def official_node(db: AsyncSession) -> RoadmapNode:
    roadmap = Roadmap(title="Official Catalog", audience="career")
    db.add(roadmap)
    await db.commit()
    node = RoadmapNode(roadmap_id=roadmap.id, phase="1", section="1", title="Official Node")
    db.add(node)
    await db.commit()
    return node

@pytest.fixture
async def personal_node(db: AsyncSession) -> RoadmapNode:
    # _current["user"] is USER_A by default, which is what we need
    # We will just generate a uuid for user_id for this test since we just need it to match
    # or not match the current user. Wait, we don't have access to USER_A here.
    # Let's import USER_A.
    from tests.conftest import USER_A
    roadmap = Roadmap(title="Personal Catalog", audience="career", user_id=USER_A.id)
    db.add(roadmap)
    await db.commit()
    node = RoadmapNode(roadmap_id=roadmap.id, phase="1", section="1", title="Personal Node")
    db.add(node)
    await db.commit()
    return node

@pytest.fixture
async def other_user_node(db: AsyncSession) -> RoadmapNode:
    roadmap = Roadmap(title="Other User Catalog", audience="career", user_id=uuid.uuid4())
    db.add(roadmap)
    await db.commit()
    node = RoadmapNode(roadmap_id=roadmap.id, phase="1", section="1", title="Other Node")
    db.add(node)
    await db.commit()
    return node


async def test_companion_sync_success(client: AsyncClient, db: AsyncSession, official_node: RoadmapNode):
    session_id = uuid.uuid4()
    payload = {
        "sessions": [
            {
                "session_id": str(session_id),
                "node_id": str(official_node.id),
                "duration_min": 25,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "payload": {
                    "sources": ["leetcode.com"],
                    "study_type": "coding",
                    "assistance_level": "none",
                    "confidence_band": "high",
                    "classifier": "gemini-3.1-flash-lite"
                }
            }
        ]
    }
    resp = await client.post("/api/companion/sessions", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["synced"] == 1
    assert data["ignored"] == 0

    # Verify event was written
    stmt = select(LearningEvent).where(LearningEvent.entity_id == session_id)
    event = (await db.execute(stmt)).scalar_one()
    assert event.event_type == "TIME_BLOCK"
    assert event.trust_tier == "T3_observed"
    assert event.source == "companion_browser"
    assert event.duration_min == 25
    assert event.payload["classifier"] == "gemini-3.1-flash-lite"


async def test_companion_sync_dedupe(client: AsyncClient, official_node: RoadmapNode):
    session_id = uuid.uuid4()
    payload = {
        "sessions": [
            {
                "session_id": str(session_id),
                "node_id": str(official_node.id),
                "duration_min": 25,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "payload": {"sources": ["leetcode.com"]}
            }
        ]
    }
    # First sync
    resp1 = await client.post("/api/companion/sessions", json=payload)
    assert resp1.status_code == 200
    assert resp1.json()["synced"] == 1

    # Second sync should dedupe
    resp2 = await client.post("/api/companion/sessions", json=payload)
    assert resp2.status_code == 200
    assert resp2.json()["synced"] == 0
    assert resp2.json()["ignored"] == 1


async def test_companion_sync_rejects_unknown_fields(client: AsyncClient, official_node: RoadmapNode):
    # Verifies the no-persistence invariant (§6)
    session_id = uuid.uuid4()
    payload = {
        "sessions": [
            {
                "session_id": str(session_id),
                "node_id": str(official_node.id),
                "duration_min": 25,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "payload": {
                    "sources": ["claude.ai"],
                    "raw_chat_content": "User: What is DP? Assistant: Dynamic Programming is..."
                }
            }
        ]
    }
    resp = await client.post("/api/companion/sessions", json=payload)
    assert resp.status_code == 422
    assert "raw_chat_content" in resp.text
    assert "Extra inputs are not permitted" in resp.text


async def test_companion_sync_ownership_check(client: AsyncClient, other_user_node: RoadmapNode):
    session_id = uuid.uuid4()
    payload = {
        "sessions": [
            {
                "session_id": str(session_id),
                "node_id": str(other_user_node.id),
                "duration_min": 25,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "payload": {"sources": ["youtube.com"]}
            }
        ]
    }
    resp = await client.post("/api/companion/sessions", json=payload)
    assert resp.status_code == 200
    assert resp.json()["synced"] == 0
    assert resp.json()["ignored"] == 1


async def test_companion_rate_limit(client: AsyncClient, official_node: RoadmapNode):
    # First 50 requests
    for _ in range(50):
        payload = {
            "sessions": [
                {
                    "session_id": str(uuid.uuid4()),
                    "node_id": str(official_node.id),
                    "duration_min": 5,
                    "occurred_at": datetime.now(timezone.utc).isoformat(),
                    "payload": {"sources": ["leetcode.com"]}
                }
            ]
        }
        resp = await client.post("/api/companion/sessions", json=payload)
        assert resp.status_code == 200

    # 51st request should fail
    payload = {
        "sessions": [
            {
                "session_id": str(uuid.uuid4()),
                "node_id": str(official_node.id),
                "duration_min": 5,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "payload": {"sources": ["leetcode.com"]}
            }
        ]
    }
    resp = await client.post("/api/companion/sessions", json=payload)
    assert resp.status_code == 429
    assert "Daily limit" in resp.text


async def test_companion_school_audience_rejected(client: AsyncClient, db: AsyncSession):
    # We need to insert a UserPref for the test user
    from tests.conftest import USER_A
    from app.models.models import UserPref

    # Make sure we don't conflict with existing rows if any
    stmt = select(UserPref).where(UserPref.user_id == uuid.UUID(USER_A.id))
    pref = (await db.execute(stmt)).scalar_one_or_none()
    if pref:
        pref.audience = "school"
    else:
        pref = UserPref(user_id=uuid.UUID(USER_A.id), audience="school")
        db.add(pref)
    await db.commit()

    resp = await client.post("/api/companion/sessions", json={"sessions": []})
    assert resp.status_code == 403
    assert "school audience" in resp.text.lower()


from unittest.mock import patch

async def test_companion_sync_classification_ladder_high_band(client: AsyncClient, db: AsyncSession, official_node: RoadmapNode):
    # Ensure user has the goal active so candidate_nodes_for_user picks up the node
    from app.models.models import CareerGoal
    from tests.conftest import USER_A
    
    # Clean up existing goals if any, then create an active goal pointing to official_node's roadmap
    await db.execute(CareerGoal.__table__.delete().where(CareerGoal.user_id == uuid.UUID(USER_A.id)))
    goal = CareerGoal(user_id=uuid.UUID(USER_A.id), roadmap_id=official_node.roadmap_id, status="active", role_title="Dev", role_key="test_role", title="Test Goal")
    db.add(goal)
    await db.commit()

    # Mock the LLM classification result
    from app.services.llm_classifier import ClassificationResult, CandidateRank
    mock_result = ClassificationResult(
        candidates=[CandidateRank(node=str(official_node.id), rank=1)],
        selected=str(official_node.id),
        confidence_band="high",
        study_type="reading",
        assistance_level="none",
        reason="Mocked reason"
    )

    with patch('app.api.routes.companion.classify_session', return_value=mock_result), \
         patch('app.api.routes.companion.top_k_suggested_nodes') as mock_top_k:
         
        mock_top_k.return_value = [{"node_id": official_node.id, "title": "Official Node", "description": ""}]
        session_id = uuid.uuid4()
        payload = {
            "sessions": [
                {
                    "session_id": str(session_id),
                    "duration_min": 15,
                    "occurred_at": datetime.now(timezone.utc).isoformat(),
                    "payload": {
                        "sources": ["coursera.org"],
                        "title_sample": "Machine Learning Week 1"
                    }
                }
            ]
        }
        resp = await client.post("/api/companion/sessions", json=payload)
        assert resp.status_code == 200, resp.text
        
        # Verify event was written and node_id was assigned
        stmt = select(LearningEvent).where(LearningEvent.entity_id == session_id)
        event = (await db.execute(stmt)).scalar_one()
        assert event.node_id == official_node.id
        assert event.payload["confidence_band"] == "high"
        assert event.payload["reason"] == "Mocked reason"


async def test_companion_sync_classification_ladder_hallucination_triage(client: AsyncClient, db: AsyncSession, official_node: RoadmapNode):
    # Ensure user has the goal active
    from app.models.models import CareerGoal
    from tests.conftest import USER_A
    
    await db.execute(CareerGoal.__table__.delete().where(CareerGoal.user_id == uuid.UUID(USER_A.id)))
    goal = CareerGoal(user_id=uuid.UUID(USER_A.id), roadmap_id=official_node.roadmap_id, status="active", role_title="Dev", role_key="test_role", title="Test Goal")
    db.add(goal)
    await db.commit()
    
    from app.services.llm_classifier import ClassificationResult
    mock_result = ClassificationResult(
        candidates=[],
        selected=None,
        confidence_band="medium",
        study_type="unknown",
        assistance_level=None,
        reason="System override: LLM hallucinated node"
    )

    with patch('app.api.routes.companion.classify_session', return_value=mock_result), \
         patch('app.api.routes.companion.top_k_suggested_nodes') as mock_top_k:
         
        mock_top_k.return_value = [{"node_id": official_node.id, "title": "Official Node", "description": ""}]
        session_id = uuid.uuid4()
        payload = {
            "sessions": [
                {
                    "session_id": str(session_id),
                    "duration_min": 15,
                    "occurred_at": datetime.now(timezone.utc).isoformat(),
                    "payload": {
                        "sources": ["leetcode.com"],
                        "title_sample": "Random Unknown Problem"
                    }
                }
            ]
        }
        resp = await client.post("/api/companion/sessions", json=payload)
        assert resp.status_code == 200, resp.text
        
        # Verify event was written but node_id is NULL
        stmt = select(LearningEvent).where(LearningEvent.entity_id == session_id)
        event = (await db.execute(stmt)).scalar_one()
        assert event.node_id is None
        assert event.payload["confidence_band"] == "medium"


async def test_companion_time_block_never_moves_mastery(client: AsyncClient, db: AsyncSession, official_node: RoadmapNode):
    # SPEC-companion-phase1 §4/§8: TIME_BLOCK/T3_observed is ambient evidence
    # that must NEVER move mastery (w=0, Balance-only for Phase C1). Several
    # large-duration syncs against the same node should leave m_learned at 0.
    for i in range(3):
        payload = {
            "sessions": [
                {
                    "session_id": str(uuid.uuid4()),
                    "node_id": str(official_node.id),
                    "duration_min": 120,
                    "occurred_at": datetime.now(timezone.utc).isoformat(),
                    "payload": {"sources": ["leetcode.com"]}
                }
            ]
        }
        resp = await client.post("/api/companion/sessions", json=payload)
        assert resp.status_code == 200, resp.text

    stmt = select(NodeMastery).where(NodeMastery.node_id == official_node.id)
    mastery = (await db.execute(stmt)).scalar_one_or_none()
    assert mastery is not None
    assert mastery.m_learned == 0.0
    # w=0 means "no evidence at all" (fold_events skips zero-weight events
    # before they're counted), not "capped evidence" — exposure_capped stays
    # False rather than True, since no evidence (capped or otherwise) exists.
    assert mastery.evidence_count == 0
    assert mastery.exposure_capped is False

