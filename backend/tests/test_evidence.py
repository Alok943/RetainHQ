"""Career Coach evidence spine (SPEC-career-coach-phase1 §8). Built up
incrementally alongside the spec's build order (§9) — see that doc for the
full numbered test list this file works through.
"""
import random
import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy import select

from app.models.models import LearningEvent, MetricEvent, NodeMastery, Roadmap, RoadmapNode
from app.services.evidence import fold_events, node_state, record_event, recompute_node
from app.services.evidence_weights import (
    EventInput,
    apply_event_weight,
    is_capped,
    w,
)
from tests.conftest import USER_A, USER_B
from tests.test_ownership import ACTIVITY_PAYLOAD

_T0 = datetime(2026, 1, 1)


def _event(offset_seconds=0, **kwargs):
    kwargs.setdefault("id", uuid.uuid4())
    kwargs.setdefault("occurred_at", _T0 + timedelta(seconds=offset_seconds))
    return EventInput(**kwargs)


# --- Weights and tiers (§8 tests 1-6) --------------------------------------

# (event_type, outcome, difficulty, assistance, grade, duration_min) -> expected w
PROBLEM_SOLVED_TABLE = [
    ("pass", "hard", "none", 0.35),
    ("pass", "hard", "hint", 0.21),
    ("pass", "hard", "llm_assisted", 0.08),
    ("pass", "hard", "solution_seen", 0.08),
    ("pass", "medium", "none", 0.25),
    ("pass", "medium", "hint", 0.15),
    ("pass", "medium", "llm_assisted", 0.06),
    ("pass", "medium", "solution_seen", 0.06),
    ("pass", "easy", "none", 0.10),
    ("pass", "easy", "hint", 0.04),
    ("pass", "easy", "llm_assisted", 0.04),
    ("pass", "easy", "solution_seen", 0.04),
]


@pytest.mark.parametrize("outcome,difficulty,assistance,expected", PROBLEM_SOLVED_TABLE)
def test_problem_solved_pass_table(outcome, difficulty, assistance, expected):
    event = EventInput(
        event_type="PROBLEM_SOLVED", trust_tier="T1_verified_external",
        outcome=outcome, difficulty=difficulty, assistance=assistance,
    )
    assert w(event) == pytest.approx(expected)


def test_recall_graded_weight():
    event = EventInput(event_type="RECALL_GRADED", trust_tier="T2_verified_internal", grade=0.8)
    assert w(event) == pytest.approx(0.20 * 0.8)


def test_concept_explained_weight():
    event = EventInput(event_type="CONCEPT_EXPLAINED", trust_tier="T2_verified_internal", grade=0.5)
    assert w(event) == pytest.approx(0.18 * 0.5)


def test_artifact_built_weight():
    event = EventInput(event_type="ARTIFACT_BUILT", trust_tier="T2_verified_internal")
    assert w(event) == pytest.approx(0.30)


def test_content_consumed_weight():
    event = EventInput(event_type="CONTENT_CONSUMED", trust_tier="T3_observed")
    assert w(event) == pytest.approx(0.04)


def test_time_block_weight():
    event = EventInput(event_type="TIME_BLOCK", trust_tier="T4_claimed")
    assert w(event) == pytest.approx(0.0)


@pytest.mark.parametrize("event_type", [
    "RECALL_GRADED", "PROBLEM_SOLVED", "ARTIFACT_BUILT",
    "CONCEPT_EXPLAINED", "CONTENT_CONSUMED", "TIME_BLOCK",
])
def test_t4_never_moves_mastery(event_type):
    event = EventInput(
        event_type=event_type, trust_tier="T4_claimed",
        outcome="pass", difficulty="hard", assistance="none", grade=1.0,
    )
    assert w(event) == 0.0


def test_t3_content_consumed_caps_at_035():
    m = 0.0
    event = EventInput(event_type="CONTENT_CONSUMED", trust_tier="T3_observed")
    weight = w(event)
    capped = is_capped(event)
    for _ in range(200):
        m = apply_event_weight(m, weight, capped)
    assert m == pytest.approx(0.35)


def test_t3_event_never_drags_down_already_higher_node():
    event = EventInput(event_type="CONTENT_CONSUMED", trust_tier="T3_observed")
    weight = w(event)
    capped = is_capped(event)
    m_after = apply_event_weight(0.7, weight, capped)
    assert m_after == pytest.approx(0.7)


@pytest.mark.parametrize("duration_min,expected", [(0, 0.0), (5, 0.0), (14, 0.0), (15, 0.03), (30, 0.03)])
def test_problem_solved_fail_duration_threshold(duration_min, expected):
    event = EventInput(
        event_type="PROBLEM_SOLVED", trust_tier="T1_verified_external",
        outcome="fail", duration_min=duration_min,
    )
    assert w(event) == pytest.approx(expected)


def test_missing_assistance_treated_as_llm_assisted_not_none():
    event = EventInput(
        event_type="PROBLEM_SOLVED", trust_tier="T1_verified_external",
        outcome="pass", difficulty="medium", assistance=None,
    )
    assert w(event) == pytest.approx(0.06)
    assert w(event) != pytest.approx(0.25)  # would be the "none"-assistance weight


# --- Fold (§8 tests 7-11) ---------------------------------------------------

def test_empty_events_gives_unexposed():
    result = fold_events([])
    assert result.m_learned == 0.0
    assert node_state(result.m_learned, has_unassisted_pass=False) == "unexposed"


def test_diminishing_returns_easy_passes_stay_below_one_and_shrink():
    events = [
        _event(i, event_type="PROBLEM_SOLVED", trust_tier="T1_verified_external",
               outcome="pass", difficulty="easy", assistance="none")
        for i in range(20)
    ]
    deltas = []
    prev_m = 0.0
    for n in range(1, 21):
        m = fold_events(events[:n]).m_learned
        deltas.append(m - prev_m)
        prev_m = m

    assert prev_m < 1.0
    assert all(earlier > later for earlier, later in zip(deltas, deltas[1:]))


def test_m_learned_never_leaves_unit_interval():
    rng = random.Random(1234)
    event_types = ["RECALL_GRADED", "PROBLEM_SOLVED", "ARTIFACT_BUILT", "CONCEPT_EXPLAINED", "CONTENT_CONSUMED"]
    tiers = ["T1_verified_external", "T2_verified_internal", "T3_observed", "T4_claimed"]
    for _ in range(50):
        events = []
        for i in range(rng.randint(0, 40)):
            events.append(_event(
                i,
                event_type=rng.choice(event_types),
                trust_tier=rng.choice(tiers),
                outcome=rng.choice(["pass", "fail", "partial", None]),
                difficulty=rng.choice(["easy", "medium", "hard", None]),
                assistance=rng.choice(["none", "hint", "llm_assisted", "solution_seen", None]),
                grade=rng.choice([0.0, 0.3, 0.7, 1.0, None]),
                duration_min=rng.choice([0, 10, 20]),
            ))
        m = fold_events(events).m_learned
        assert 0.0 <= m <= 1.0


def test_order_independence_across_t1_and_t3_events():
    t1 = dict(event_type="PROBLEM_SOLVED", trust_tier="T1_verified_external",
              outcome="pass", difficulty="hard", assistance="none")  # w = 0.35
    t3 = dict(event_type="CONTENT_CONSUMED", trust_tier="T3_observed")  # w = 0.04, capped

    t3_then_t1 = [_event(0, **t3), _event(1, **t1)]
    t1_then_t3 = [_event(0, **t1), _event(1, **t3)]

    t1_alone_value = fold_events([_event(0, **t1)]).m_learned

    assert fold_events(t3_then_t1).m_learned == pytest.approx(t1_alone_value)
    assert fold_events(t1_then_t3).m_learned == pytest.approx(t1_alone_value)


@pytest.mark.parametrize("m,has_unassisted_pass,expected", [
    (0.0, False, "unexposed"),
    (0.01, False, "exposed"),
    (0.34, False, "exposed"),
    (0.35, False, "practicing"),
    (0.64, False, "practicing"),
    (0.65, False, "solid"),
    (0.84, False, "solid"),
    (0.9, False, "solid"),        # only llm_assisted passes -> solid, NOT interview_ready
    (0.9, True, "interview_ready"),
    (0.85, True, "interview_ready"),
])
def test_node_state_thresholds(m, has_unassisted_pass, expected):
    assert node_state(m, has_unassisted_pass) == expected


# --- Invariant (§8 test 12) --------------------------------------------------

async def test_incremental_record_event_matches_full_recompute(db):
    roadmap = Roadmap(title="Evidence test roadmap", slug="evidence-test-roadmap", audience="career")
    db.add(roadmap)
    await db.flush()
    node = RoadmapNode(roadmap_id=roadmap.id, phase="p1", section="s1", title="Evidence test node")
    db.add(node)
    await db.flush()

    user_id = uuid.UUID(USER_A.id)
    rng = random.Random(42)
    event_types = ["RECALL_GRADED", "PROBLEM_SOLVED", "ARTIFACT_BUILT", "CONCEPT_EXPLAINED", "CONTENT_CONSUMED"]
    tiers = ["T1_verified_external", "T2_verified_internal", "T3_observed", "T4_claimed"]

    for i in range(50):
        await record_event(
            db, user_id,
            event_type=rng.choice(event_types),
            trust_tier=rng.choice(tiers),
            source="manual",
            node_id=node.id,
            outcome=rng.choice(["pass", "fail", "partial", None]),
            difficulty=rng.choice(["easy", "medium", "hard", None]),
            assistance=rng.choice(["none", "hint", "llm_assisted", "solution_seen", None]),
            grade=rng.choice([0.0, 0.3, 0.7, 1.0, None]),
            duration_min=rng.choice([0, 10, 20]),
            occurred_at=_T0 + timedelta(seconds=i),
        )
    await db.commit()

    incremental = (
        await db.execute(select(NodeMastery).where(NodeMastery.user_id == user_id, NodeMastery.node_id == node.id))
    ).scalar_one()
    incremental_value = incremental.m_learned

    full = await recompute_node(db, user_id, node.id)
    await db.commit()

    assert full.m_learned == pytest.approx(incremental_value, abs=1e-9)


# --- Integration: Producer A / review hook (§8 tests 13-16) -----------------

async def _seed_node(db, slug):
    roadmap = Roadmap(title="Review evidence test roadmap", slug=slug, audience="career")
    db.add(roadmap)
    await db.flush()
    node = RoadmapNode(roadmap_id=roadmap.id, phase="p1", section="s1", title="Node")
    db.add(node)
    await db.commit()
    return node


async def test_review_completion_writes_one_learning_event_and_updates_mastery(client, db):
    node = await _seed_node(db, "review-evidence-writes-event")

    resp = await client.post("/api/activities/", json={**ACTIVITY_PAYLOAD, "node_id": str(node.id)})
    assert resp.status_code == 200
    review_id = (await client.get("/api/reviews/due")).json()[0]["id"]

    complete = await client.post(
        f"/api/reviews/{review_id}/complete", json={"rating": "easy", "recalled": True}
    )
    assert complete.status_code == 200

    events = (await db.execute(select(LearningEvent).where(LearningEvent.node_id == node.id))).scalars().all()
    assert len(events) == 1
    assert events[0].event_type == "RECALL_GRADED"
    assert events[0].trust_tier == "T2_verified_internal"

    mastery = (
        await db.execute(select(NodeMastery).where(NodeMastery.node_id == node.id))
    ).scalar_one()
    assert mastery.m_learned > 0.0


async def test_record_event_dedupe_does_not_double_count(db):
    node = await _seed_node(db, "review-evidence-dedupe")
    user_id = uuid.UUID(USER_A.id)
    entity_id = uuid.uuid4()

    first = await record_event(
        db, user_id, event_type="RECALL_GRADED", trust_tier="T2_verified_internal",
        source="retainhq_review", node_id=node.id, grade=1.0, outcome="pass", entity_id=entity_id,
    )
    await db.commit()
    assert first is not None

    second = await record_event(
        db, user_id, event_type="RECALL_GRADED", trust_tier="T2_verified_internal",
        source="retainhq_review", node_id=node.id, grade=1.0, outcome="pass", entity_id=entity_id,
    )
    await db.commit()
    assert second is None

    events = (await db.execute(select(LearningEvent).where(LearningEvent.node_id == node.id))).scalars().all()
    assert len(events) == 1


async def test_review_without_node_id_writes_no_event_and_one_unmapped_metric(client, db):
    resp = await client.post("/api/activities/", json=ACTIVITY_PAYLOAD)  # no node_id
    assert resp.status_code == 200
    review_id = (await client.get("/api/reviews/due")).json()[0]["id"]

    complete = await client.post(
        f"/api/reviews/{review_id}/complete", json={"rating": "medium", "recalled": True}
    )
    assert complete.status_code == 200

    assert (await db.execute(select(LearningEvent))).scalars().all() == []

    unmapped = (
        await db.execute(select(MetricEvent).where(MetricEvent.event_type == "evidence_unmapped"))
    ).scalars().all()
    assert len(unmapped) == 1
    assert unmapped[0].payload["reason"] == "no_node_id"


async def test_review_completion_survives_evidence_record_event_failure(client, db, monkeypatch):
    node = await _seed_node(db, "review-evidence-failure-isolation")

    resp = await client.post("/api/activities/", json={**ACTIVITY_PAYLOAD, "node_id": str(node.id)})
    assert resp.status_code == 200
    review_id = (await client.get("/api/reviews/due")).json()[0]["id"]

    async def _boom(*args, **kwargs):
        raise RuntimeError("evidence boom")

    monkeypatch.setattr("app.api.routes.reviews.evidence.record_event", _boom)

    complete = await client.post(
        f"/api/reviews/{review_id}/complete", json={"rating": "easy", "recalled": True}
    )
    assert complete.status_code == 200
    assert complete.json()["status"] == "completed"


# --- Evidence router / Producer B (§8 tests 17-18) --------------------------

async def test_evidence_events_are_scoped_and_delete_is_owner_only(client, db, as_user):
    node = await _seed_node(db, "evidence-ownership-node")  # official catalog roadmap
    user_id_a = uuid.UUID(USER_A.id)

    event = await record_event(
        db, user_id_a, event_type="RECALL_GRADED", trust_tier="T2_verified_internal",
        source="retainhq_review", node_id=node.id, grade=1.0, outcome="pass",
    )
    await db.commit()

    resp = await client.get(f"/api/evidence/nodes/{node.id}/events")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    # B sees the same (shared, official) node but none of A's events on it.
    as_user(USER_B)
    resp = await client.get(f"/api/evidence/nodes/{node.id}/events")
    assert resp.status_code == 200
    assert resp.json() == []

    # B cannot soft-delete A's event.
    resp = await client.delete(f"/api/evidence/events/{event.id}")
    assert resp.status_code == 404

    # A still can.
    as_user(USER_A)
    resp = await client.delete(f"/api/evidence/events/{event.id}")
    assert resp.status_code == 204


async def test_soft_delete_recomputes_to_exactly_the_remaining_events_value(client, db):
    node = await _seed_node(db, "evidence-soft-delete-node")
    user_id = uuid.UUID(USER_A.id)

    e1 = await record_event(
        db, user_id, event_type="PROBLEM_SOLVED", trust_tier="T1_verified_external",
        source="leetcode", node_id=node.id, outcome="pass", difficulty="hard", assistance="none",
        entity_id=uuid.uuid4(),
    )
    await db.commit()
    await record_event(
        db, user_id, event_type="PROBLEM_SOLVED", trust_tier="T1_verified_external",
        source="leetcode", node_id=node.id, outcome="pass", difficulty="medium", assistance="none",
        entity_id=uuid.uuid4(),
    )
    await db.commit()

    resp = await client.delete(f"/api/evidence/events/{e1.id}")
    assert resp.status_code == 204

    mastery = (
        await db.execute(select(NodeMastery).where(NodeMastery.node_id == node.id))
    ).scalar_one()

    remaining = (
        await db.execute(
            select(LearningEvent).where(LearningEvent.node_id == node.id, LearningEvent.deleted_at.is_(None))
        )
    ).scalars().all()
    expected = fold_events(remaining).m_learned

    assert mastery.m_learned == pytest.approx(expected)
    assert mastery.m_learned == pytest.approx(0.25)  # medium/none pass alone, e1 excluded
