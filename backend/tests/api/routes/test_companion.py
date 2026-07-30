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
                    # A client-supplied node_id means no server classification
                    # ran — these AI-attribution fields are forgeable client
                    # input and must never reach the stored event verbatim
                    # (see test_companion_sync_strips_client_supplied_ai_fields).
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
    assert "classifier" not in event.payload
    assert "confidence_band" not in event.payload


async def test_companion_sync_strips_client_supplied_ai_fields(client: AsyncClient, db: AsyncSession, official_node: RoadmapNode):
    # A client that supplies node_id directly must not be able to forge
    # server-verified-looking classification provenance (confidence_band,
    # classifier, reason, candidates, etc.) — those fields are only ever
    # legitimately written by the classification ladder itself.
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
                    "confidence_band": "high",
                    "classifier": "gemini-3.1-flash-lite",
                    "prompt_version": "v99-forged",
                    "embedding_model": "forged-model",
                    "reason": "forged reason",
                    "candidates": [{"node": "forged", "rank": 1}],
                    "study_type": "forged",
                    "assistance_level": "none",
                }
            }
        ]
    }
    resp = await client.post("/api/companion/sessions", json=payload)
    assert resp.status_code == 200, resp.text

    stmt = select(LearningEvent).where(LearningEvent.entity_id == session_id)
    event = (await db.execute(stmt)).scalar_one()
    for forged_field in ("classifier", "prompt_version", "embedding_model", "confidence_band", "candidates", "reason", "study_type", "assistance_level"):
        assert forged_field not in event.payload, f"{forged_field} should have been stripped from client-supplied payload"
    assert event.payload["sources"] == ["leetcode.com"]


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


from unittest.mock import patch, AsyncMock

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


# --- Chat content / topic segmentation (IMPLEMENTATION-companion-chat-content.md) --

async def test_companion_sync_rejects_content_nested_in_payload(client: AsyncClient, official_node: RoadmapNode):
    # `content` is a SIBLING of `payload`, never inside it — payload.extra="forbid"
    # must still reject it there regardless of the top-level content field's existence.
    session_id = uuid.uuid4()
    payload = {
        "sessions": [
            {
                "session_id": str(session_id),
                "node_id": str(official_node.id),
                "duration_min": 25,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "payload": {"sources": ["claude.ai"], "content": "U: hi A: hello"},
            }
        ]
    }
    resp = await client.post("/api/companion/sessions", json=payload)
    assert resp.status_code == 422
    assert "Extra inputs are not permitted" in resp.text


async def _grant_cloud_consent(db: AsyncSession):
    from app.models.models import MetricEvent
    from tests.conftest import USER_A
    db.add(MetricEvent(user_id=uuid.UUID(USER_A.id), event_type="companion_consent", payload={"tier": "cloud"}))
    await db.commit()


async def test_companion_sync_topic_fanout(client: AsyncClient, db: AsyncSession):
    from app.services.topic_segmentation import SessionTopic

    await _grant_cloud_consent(db)

    mock_topics = [
        SessionTopic(label="Postgres index tuning", share=0.6, study_type="debugging", assistance_level="llm_assisted"),
        SessionTopic(label="React re-render bug", share=0.4, study_type="debugging", assistance_level="hint"),
    ]

    session_id = uuid.uuid4()
    body = {
        "sessions": [
            {
                "session_id": str(session_id),
                "duration_min": 20,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "payload": {"sources": ["chatgpt.com"], "title_sample": "New chat"},
                "content": "U: how do I speed up this query A: use an index ... U: my component keeps re-rendering A: use useMemo",
            }
        ]
    }

    with patch("app.api.routes.companion.segment_session_topics", new=AsyncMock(return_value=mock_topics)), \
         patch("app.api.routes.companion.top_k_suggested_nodes", return_value=[]):
        resp = await client.post("/api/companion/sessions", json=body)

    assert resp.status_code == 200, resp.text
    assert resp.json()["synced"] == 2

    stmt = select(LearningEvent).where(LearningEvent.source == "companion_browser")
    events = (await db.execute(stmt)).scalars().all()
    assert len(events) == 2

    by_label = {e.payload["title_sample"]: e for e in events}
    assert by_label["Postgres index tuning"].duration_min == 12  # 20 * 0.6
    assert by_label["React re-render bug"].duration_min == 8    # 20 * 0.4
    # Distinct rows, not deduped against each other, but still both T3/TIME_BLOCK/weight-0.
    assert len({e.entity_id for e in events}) == 2
    for e in events:
        assert e.event_type == "TIME_BLOCK"
        assert e.trust_tier == "T3_observed"
        assert e.payload["session_id"] == str(session_id)


async def test_companion_sync_topic_fanout_never_moves_mastery(client: AsyncClient, db: AsyncSession, official_node: RoadmapNode):
    # Same invariant as test_companion_time_block_never_moves_mastery, but for
    # the fan-out path specifically — the whole point of §1 of the
    # implementation doc: more topics must never mean more mastery.
    from app.services.topic_segmentation import SessionTopic
    from app.models.models import NodeMastery

    await _grant_cloud_consent(db)

    mock_topics = [
        SessionTopic(label="Topic A", share=0.5, study_type="reading", assistance_level="llm_assisted"),
        SessionTopic(label="Topic B", share=0.5, study_type="reading", assistance_level="llm_assisted"),
    ]

    body = {
        "sessions": [
            {
                "session_id": str(uuid.uuid4()),
                "duration_min": 60,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "payload": {"sources": ["chatgpt.com"], "title_sample": "chat"},
                "content": "U: topic A stuff A: reply ... U: topic B stuff A: reply",
            }
        ]
    }

    with patch("app.api.routes.companion.segment_session_topics", new=AsyncMock(return_value=mock_topics)), \
         patch("app.api.routes.companion.top_k_suggested_nodes", return_value=[{"node_id": official_node.id, "title": "Official Node", "description": ""}]), \
         patch("app.api.routes.companion.classify_session", new=AsyncMock(return_value=__import__("app.services.llm_classifier", fromlist=["ClassificationResult"]).ClassificationResult(
             candidates=[], selected=str(official_node.id), confidence_band="high", study_type="reading", assistance_level="llm_assisted", reason="mocked",
         ))):
        resp = await client.post("/api/companion/sessions", json=body)

    assert resp.status_code == 200, resp.text
    assert resp.json()["synced"] == 2

    stmt = select(NodeMastery).where(NodeMastery.node_id == official_node.id)
    mastery = (await db.execute(stmt)).scalar_one_or_none()
    assert mastery is not None
    assert mastery.m_learned == 0.0


async def test_companion_sync_content_ignored_without_cloud_consent(client: AsyncClient, db: AsyncSession):
    # No companion_consent metric recorded at all -> get_latest_consent_tier
    # returns None -> segmentation must never be attempted, regardless of
    # what the client sends as `content`.
    body = {
        "sessions": [
            {
                "session_id": str(uuid.uuid4()),
                "duration_min": 20,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "payload": {"sources": ["chatgpt.com"], "title_sample": "chat"},
                "content": "U: something A: reply",
            }
        ]
    }
    segment_mock = AsyncMock(return_value=[])
    with patch("app.api.routes.companion.segment_session_topics", new=segment_mock), \
         patch("app.api.routes.companion.top_k_suggested_nodes", return_value=[]):
        resp = await client.post("/api/companion/sessions", json=body)

    assert resp.status_code == 200, resp.text
    segment_mock.assert_not_called()


async def test_companion_sync_short_session_skips_segmentation(client: AsyncClient, db: AsyncSession):
    # Below MIN_SEGMENTATION_DURATION_MIN even with cloud consent + LLM source + content.
    await _grant_cloud_consent(db)
    body = {
        "sessions": [
            {
                "session_id": str(uuid.uuid4()),
                "duration_min": 2,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "payload": {"sources": ["chatgpt.com"], "title_sample": "chat"},
                "content": "U: quick question A: quick answer",
            }
        ]
    }
    segment_mock = AsyncMock(return_value=[])
    with patch("app.api.routes.companion.segment_session_topics", new=segment_mock), \
         patch("app.api.routes.companion.top_k_suggested_nodes", return_value=[]):
        resp = await client.post("/api/companion/sessions", json=body)

    assert resp.status_code == 200, resp.text
    segment_mock.assert_not_called()


async def test_companion_topic_fanout_is_idempotent_on_retry(client: AsyncClient, db: AsyncSession):
    # A client retrying the same batch (network retry after an actually-
    # successful sync) must not double-insert per-topic rows — each topic's
    # derived entity_id has to be stable across the two calls.
    from app.services.topic_segmentation import SessionTopic

    await _grant_cloud_consent(db)
    mock_topics = [
        SessionTopic(label="Topic A", share=0.5, study_type="reading", assistance_level="llm_assisted"),
        SessionTopic(label="Topic B", share=0.5, study_type="reading", assistance_level="llm_assisted"),
    ]
    body = {
        "sessions": [
            {
                "session_id": str(uuid.uuid4()),
                "duration_min": 20,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "payload": {"sources": ["chatgpt.com"], "title_sample": "chat"},
                "content": "U: a A: b ... U: c A: d",
            }
        ]
    }

    with patch("app.api.routes.companion.segment_session_topics", new=AsyncMock(return_value=mock_topics)), \
         patch("app.api.routes.companion.top_k_suggested_nodes", return_value=[]):
        resp1 = await client.post("/api/companion/sessions", json=body)
        resp2 = await client.post("/api/companion/sessions", json=body)

    assert resp1.json()["synced"] == 2
    assert resp2.json()["synced"] == 0
    assert resp2.json()["ignored"] == 2


async def test_companion_rate_limit_counts_sessions_not_fanout_events(client: AsyncClient, db: AsyncSession):
    # A single session that fans out into several LearningEvent rows must
    # still only cost 1 against the daily session cap, not N.
    from app.services.topic_segmentation import SessionTopic
    from app.models.models import MetricEvent

    await _grant_cloud_consent(db)
    mock_topics = [
        SessionTopic(label=f"Topic {i}", share=1 / 5, study_type="reading", assistance_level="llm_assisted")
        for i in range(5)
    ]
    body = {
        "sessions": [
            {
                "session_id": str(uuid.uuid4()),
                "duration_min": 20,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "payload": {"sources": ["chatgpt.com"], "title_sample": "chat"},
                "content": "five topics of text",
            }
        ]
    }
    with patch("app.api.routes.companion.segment_session_topics", new=AsyncMock(return_value=mock_topics)), \
         patch("app.api.routes.companion.top_k_suggested_nodes", return_value=[]):
        resp = await client.post("/api/companion/sessions", json=body)

    assert resp.status_code == 200, resp.text
    assert resp.json()["synced"] == 5

    from tests.conftest import USER_A
    from sqlmodel import func as sql_func
    tracked = (await db.execute(select(sql_func.count(MetricEvent.id)).where(
        MetricEvent.user_id == uuid.UUID(USER_A.id),
        MetricEvent.event_type == "companion_session_tracked",
    ))).scalar()
    assert tracked == 1


# --- YouTube chapter fan-out (2026-07-27, verified against a real freeCodeCamp
# video's chapter markers) --------------------------------------------------

async def test_companion_sync_chapter_fanout(client: AsyncClient, db: AsyncSession):
    # No consent tier needed — chapters are public video metadata, not
    # user-authored/AI-derived text, unlike chat `content`.
    session_id = uuid.uuid4()
    body = {
        "sessions": [
            {
                "session_id": str(session_id),
                "duration_min": 20,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "payload": {"sources": ["youtube.com"], "title_sample": "Python for AI – freeCodeCamp"},
                "chapters": [
                    {"title": "Chapter 1 – Modules, Comments & pip", "seconds": 600},
                    {"title": "Chapter 2 – NumPy Basics", "seconds": 480},
                ],
            }
        ]
    }
    with patch("app.api.routes.companion.top_k_suggested_nodes", return_value=[]):
        resp = await client.post("/api/companion/sessions", json=body)

    assert resp.status_code == 200, resp.text
    assert resp.json()["synced"] == 2

    stmt = select(LearningEvent).where(LearningEvent.source == "companion_browser")
    events = (await db.execute(stmt)).scalars().all()
    assert len(events) == 2
    by_label = {e.payload["title_sample"]: e for e in events}
    assert by_label["Chapter 1 – Modules, Comments & pip"].duration_min == 10  # 600s
    assert by_label["Chapter 2 – NumPy Basics"].duration_min == 8              # 480s
    for e in events:
        assert e.event_type == "TIME_BLOCK"
        assert e.trust_tier == "T3_observed"
        assert "content" not in e.payload  # transport-only fields never leak into storage
        assert "chapters" not in e.payload


async def test_companion_sync_chapter_fanout_never_moves_mastery(client: AsyncClient, db: AsyncSession, official_node: RoadmapNode):
    body = {
        "sessions": [
            {
                "session_id": str(uuid.uuid4()),
                "duration_min": 60,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "payload": {"sources": ["youtube.com"], "title_sample": "some video"},
                "chapters": [
                    {"title": "Chapter A", "seconds": 1800},
                    {"title": "Chapter B", "seconds": 1800},
                ],
            }
        ]
    }
    from app.services.llm_classifier import ClassificationResult
    mock_result = ClassificationResult(
        candidates=[], selected=str(official_node.id), confidence_band="high",
        study_type="video_lecture", assistance_level="none", reason="mocked",
    )
    with patch("app.api.routes.companion.classify_session", new=AsyncMock(return_value=mock_result)), \
         patch("app.api.routes.companion.top_k_suggested_nodes", return_value=[{"node_id": official_node.id, "title": "Official Node", "description": ""}]):
        resp = await client.post("/api/companion/sessions", json=body)

    assert resp.status_code == 200, resp.text
    assert resp.json()["synced"] == 2

    stmt = select(NodeMastery).where(NodeMastery.node_id == official_node.id)
    mastery = (await db.execute(stmt)).scalar_one_or_none()
    assert mastery is not None
    assert mastery.m_learned == 0.0  # watching, however chapter-attributed, is still weight 0


async def test_companion_sync_single_chapter_does_not_fan_out(client: AsyncClient, db: AsyncSession):
    # A video with exactly one detected chapter (or one with nonzero seconds)
    # isn't "multi-topic" — falls back to the ordinary whole-video path.
    session_id = uuid.uuid4()
    body = {
        "sessions": [
            {
                "session_id": str(session_id),
                "duration_min": 10,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "payload": {"sources": ["youtube.com"], "title_sample": "short video"},
                "chapters": [{"title": "Intro", "seconds": 600}],
            }
        ]
    }
    with patch("app.api.routes.companion.top_k_suggested_nodes", return_value=[]):
        resp = await client.post("/api/companion/sessions", json=body)

    assert resp.status_code == 200, resp.text
    assert resp.json()["synced"] == 1
    stmt = select(LearningEvent).where(LearningEvent.entity_id == session_id)
    event = (await db.execute(stmt)).scalar_one()
    assert event.payload["title_sample"] == "short video"  # whole-video title, not the chapter's


async def test_companion_sync_chapters_ignored_on_mixed_tab_session(client: AsyncClient, db: AsyncSession):
    # A session spanning more than one source domain must never fan out by
    # chapter — the watched seconds could belong to either tab.
    session_id = uuid.uuid4()
    body = {
        "sessions": [
            {
                "session_id": str(session_id),
                "duration_min": 20,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "payload": {"sources": ["youtube.com", "leetcode.com"], "title_sample": "mixed"},
                "chapters": [
                    {"title": "Chapter 1", "seconds": 600},
                    {"title": "Chapter 2", "seconds": 600},
                ],
            }
        ]
    }
    with patch("app.api.routes.companion.top_k_suggested_nodes", return_value=[]):
        resp = await client.post("/api/companion/sessions", json=body)

    assert resp.status_code == 200, resp.text
    assert resp.json()["synced"] == 1  # one whole-session event, not 2 chapter legs


async def test_companion_sync_too_many_chapters_falls_back_to_single_event(client: AsyncClient, db: AsyncSession):
    session_id = uuid.uuid4()
    chapters = [{"title": f"Chapter {i}", "seconds": 60} for i in range(20)]  # > MAX_CHAPTERS_PER_SESSION
    body = {
        "sessions": [
            {
                "session_id": str(session_id),
                "duration_min": 20,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "payload": {"sources": ["youtube.com"], "title_sample": "very long tutorial"},
                "chapters": chapters,
            }
        ]
    }
    with patch("app.api.routes.companion.top_k_suggested_nodes", return_value=[]):
        resp = await client.post("/api/companion/sessions", json=body)

    assert resp.status_code == 200, resp.text
    assert resp.json()["synced"] == 1


async def test_companion_sync_rejects_chapters_nested_in_payload(client: AsyncClient, official_node: RoadmapNode):
    session_id = uuid.uuid4()
    body = {
        "sessions": [
            {
                "session_id": str(session_id),
                "node_id": str(official_node.id),
                "duration_min": 10,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "payload": {"sources": ["youtube.com"], "chapters": [{"title": "x", "seconds": 60}]},
            }
        ]
    }
    resp = await client.post("/api/companion/sessions", json=body)
    assert resp.status_code == 422
    assert "Extra inputs are not permitted" in resp.text


async def test_companion_chapter_fanout_is_idempotent_on_retry(client: AsyncClient, db: AsyncSession):
    body = {
        "sessions": [
            {
                "session_id": str(uuid.uuid4()),
                "duration_min": 20,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "payload": {"sources": ["youtube.com"], "title_sample": "video"},
                "chapters": [
                    {"title": "Chapter A", "seconds": 600},
                    {"title": "Chapter B", "seconds": 600},
                ],
            }
        ]
    }
    with patch("app.api.routes.companion.top_k_suggested_nodes", return_value=[]):
        resp1 = await client.post("/api/companion/sessions", json=body)
        resp2 = await client.post("/api/companion/sessions", json=body)

    assert resp1.json()["synced"] == 2
    assert resp2.json()["synced"] == 0
    assert resp2.json()["ignored"] == 2

