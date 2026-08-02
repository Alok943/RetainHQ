import pytest
from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
import uuid
from datetime import datetime

from app.models.models import Activity, Problem, ProblemAttempt, ProblemConcept, Roadmap, RoadmapNode, LearningEvent, NodeMastery, Review
from app.services.approach_inference import InferredApproach
from tests.conftest import USER_A

@pytest.fixture
async def capture_data(db: AsyncSession):
    roadmap = Roadmap(title="DSA", audience="career", slug="dsa")
    db.add(roadmap)
    await db.commit()
    node = RoadmapNode(roadmap_id=roadmap.id, phase="1", section="1", title="Hash Tables")
    db.add(node)
    alt_node = RoadmapNode(roadmap_id=roadmap.id, phase="1", section="1", title="Sliding window (fixed)")
    db.add(alt_node)
    await db.commit()

    p1 = Problem(source="leetcode", external_id=1, slug="two-sum", title="Two Sum", difficulty="easy", catalog_version="v1")
    db.add(p1)
    await db.commit()
    db.add(ProblemConcept(problem_id=p1.id, node_id=node.id, role="primary", confidence=1.0, mapping_version="v1"))
    db.add(ProblemConcept(problem_id=p1.id, node_id=alt_node.id, role="alternative", confidence=1.0, mapping_version="v1"))
    await db.commit()

    return {"node": node, "alt_node": alt_node, "p1": p1, "roadmap": roadmap}


def _payload(problem_id, **over):
    base = {
        "topic": "LeetCode 1: Two Sum",
        "key_memory": "Use a hash map to store complements.",
        "difficulty": 3,
        "needed_hint": False,
        "source_type": "problem",
        "problem_id": str(problem_id),
        "language": "python",
    }
    base.update(over)
    return base

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
    # ActivityCreate.language is a closed Literal, so an unknown value is rejected
    # by validation rather than stored as free text (the `C++`/`cpp`/`Cpp` landfill
    # argument, IMPLEMENTATION-leetcode-log-capture.md §4.2).
    assert resp.status_code == 422

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


# --------------------------------------------------------------------------- #
# Solution capture → approach inference.
#
# The inference call itself is stubbed everywhere: these tests assert the WIRING
# and the boundaries (what it may and may not touch), not the model's judgment.
# --------------------------------------------------------------------------- #

_CODE = "class Solution:\n    def checkInclusion(self, s1, s2):\n        return False\n"


def _stub_infer(monkeypatch, result, spy=None):
    """Replace the inference call as imported by the activities route."""
    async def fake(**kwargs):
        if spy is not None:
            spy.update(kwargs)
        return result
    monkeypatch.setattr("app.api.routes.activities.infer_approach", fake)


async def test_solution_code_stores_inferred_approach(
    client: AsyncClient, db: AsyncSession, capture_data, monkeypatch
):
    _stub_infer(monkeypatch, InferredApproach(
        node_id=capture_data["alt_node"].id,
        node_title="Sliding window (fixed)",
        confidence_band="high",
        facts=["Compares two dicts for equality on every slide, O(k) per step."],
        reason="Two frequency dicts compared directly.",
    ))

    resp = await client.post("/api/activities/", json=_payload(capture_data["p1"].id, solution_code=_CODE))
    assert resp.status_code == 200, resp.text

    body = resp.json()
    # Echoed back so the read is auditable at capture time.
    assert body["approach_node_title"] == "Sliding window (fixed)"
    assert body["approach_confidence"] == "high"
    assert len(body["approach_facts"]) == 1

    activity = (await db.execute(select(Activity).where(Activity.problem_id == capture_data["p1"].id))).scalar_one()
    assert activity.solution_code == _CODE
    assert activity.approach_node_id == capture_data["alt_node"].id
    assert activity.approach_summary["facts"][0].startswith("Compares two dicts")


async def test_inferred_approach_never_overwrites_node_id(
    client: AsyncClient, db: AsyncSession, capture_data, monkeypatch
):
    """The load-bearing boundary. The inferred approach reframes QUESTIONS; the
    catalog's role='primary' node stays the mastery-routing key, because a
    solve's node assignment must remain re-resolvable from the mapping
    (SPEC-leetcode-retention.md §3.2.-1). If this ever flips, mastery starts
    moving on an LLM's read of a code snippet."""
    _stub_infer(monkeypatch, InferredApproach(
        node_id=capture_data["alt_node"].id,
        node_title="Sliding window (fixed)",
        confidence_band="high",
        facts=["Fixed-size window."],
    ))

    resp = await client.post("/api/activities/", json=_payload(capture_data["p1"].id, solution_code=_CODE))
    assert resp.status_code == 200

    activity = (await db.execute(select(Activity).where(Activity.problem_id == capture_data["p1"].id))).scalar_one()
    assert activity.node_id == capture_data["node"].id, "node_id must stay the catalog primary"
    assert activity.approach_node_id == capture_data["alt_node"].id

    # And still no evidence from the log itself.
    assert len((await db.execute(select(LearningEvent))).all()) == 0


async def test_inference_candidates_are_the_closed_mapped_set(
    client: AsyncClient, capture_data, monkeypatch
):
    """The classifier may only choose among concepts already mapped to this
    problem — never invent one (SPEC-leetcode-retention.md §2)."""
    spy = {}
    _stub_infer(monkeypatch, None, spy=spy)

    resp = await client.post("/api/activities/", json=_payload(capture_data["p1"].id, solution_code=_CODE))
    assert resp.status_code == 200

    titles = {c["title"] for c in spy["candidates"]}
    assert titles == {"Hash Tables", "Sliding window (fixed)"}
    assert spy["problem_title"] == "Two Sum"
    assert spy["language"] == "python"


async def test_inference_failure_degrades_to_plain_capture(
    client: AsyncClient, db: AsyncSession, capture_data, monkeypatch
):
    """Capture must never fail because an optional enrichment did."""
    _stub_infer(monkeypatch, None)

    resp = await client.post("/api/activities/", json=_payload(capture_data["p1"].id, solution_code=_CODE))
    assert resp.status_code == 200
    assert resp.json()["approach_node_title"] is None

    activity = (await db.execute(select(Activity).where(Activity.problem_id == capture_data["p1"].id))).scalar_one()
    assert activity.solution_code == _CODE       # the code is still kept
    assert activity.approach_node_id is None
    assert activity.node_id == capture_data["node"].id


async def test_no_solution_code_skips_inference_entirely(
    client: AsyncClient, capture_data, monkeypatch
):
    async def boom(**kwargs):
        raise AssertionError("inference must not run without solution_code")
    monkeypatch.setattr("app.api.routes.activities.infer_approach", boom)

    resp = await client.post("/api/activities/", json=_payload(capture_data["p1"].id))
    assert resp.status_code == 200


async def test_oversized_solution_code_is_rejected(client: AsyncClient, capture_data):
    resp = await client.post(
        "/api/activities/", json=_payload(capture_data["p1"].id, solution_code="x" * 8001)
    )
    assert resp.status_code == 422


# --------------------------------------------------------------------------- #
# The payoff: the stored approach reaches question generation.
# --------------------------------------------------------------------------- #

async def _log_and_open_review(client, db, capture_data, **over):
    resp = await client.post("/api/activities/", json=_payload(capture_data["p1"].id, **over))
    assert resp.status_code == 200, resp.text
    return (await db.execute(select(Review).where(Review.status == "due"))).scalars().first()


@pytest.fixture
def qgen_spy(monkeypatch):
    """Capture the kwargs question generation is called with."""
    from app.core.config import settings
    from app.services.grader import QuestionItem

    monkeypatch.setattr(settings, "GRADER_ENABLED", True)
    seen = {}

    async def fake(**kwargs):
        seen.update(kwargs)
        return [QuestionItem(question="Q?", reference_answer="A.")]

    monkeypatch.setattr("app.api.routes.reviews.generate_question_items", fake)
    return seen


async def test_approach_reaches_question_generation(
    client: AsyncClient, db: AsyncSession, capture_data, monkeypatch, qgen_spy
):
    """The whole point of the feature: the generator is told what the user
    actually wrote, so implementation questions stop describing the canonical
    solution."""
    _stub_infer(monkeypatch, InferredApproach(
        node_id=capture_data["alt_node"].id,
        node_title="Sliding window (fixed)",
        confidence_band="high",
        facts=["Compares two dicts for equality on every slide."],
    ))
    review = await _log_and_open_review(client, db, capture_data, solution_code=_CODE)

    resp = await client.post(f"/api/reviews/{review.id}/questions", json={"depth": "main"})
    assert resp.status_code == 200, resp.text

    ctx = qgen_spy["problem_context"]
    assert ctx["user_approach_title"] == "Sliding window (fixed)"
    assert ctx["user_approach_facts"] == ["Compares two dicts for equality on every slide."]
    assert ctx["primary_node_title"] == "Hash Tables"      # catalog view still present
    assert ctx["alternative_node_titles"] == ["Sliding window (fixed)"]
    # High confidence re-grounds the syllabus topic too, so the topic contract and
    # the code facts don't describe two different approaches.
    assert qgen_spy["node_title"] == "Sliding window (fixed)"


async def test_low_confidence_keeps_catalog_topic(
    client: AsyncClient, db: AsyncSession, capture_data, monkeypatch, qgen_spy
):
    """Facts still sharpen the implementation question; the topic contract does
    not move on a shaky read."""
    _stub_infer(monkeypatch, InferredApproach(
        node_id=capture_data["alt_node"].id,
        node_title="Sliding window (fixed)",
        confidence_band="medium",
        facts=["Uses two dicts."],
    ))
    review = await _log_and_open_review(client, db, capture_data, solution_code=_CODE)

    resp = await client.post(f"/api/reviews/{review.id}/questions", json={"depth": "main"})
    assert resp.status_code == 200

    assert qgen_spy["node_title"] == "Hash Tables"
    assert qgen_spy["problem_context"]["user_approach_facts"] == ["Uses two dicts."]


async def test_no_code_leaves_generation_unchanged(
    client: AsyncClient, db: AsyncSession, capture_data, qgen_spy
):
    review = await _log_and_open_review(client, db, capture_data)

    resp = await client.post(f"/api/reviews/{review.id}/questions", json={"depth": "main"})
    assert resp.status_code == 200

    ctx = qgen_spy["problem_context"]
    assert ctx["user_approach_title"] is None
    assert ctx["user_approach_facts"] == []
    assert qgen_spy["node_title"] == "Hash Tables"
