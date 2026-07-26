"""Career Coach Phase 2 — Goal, Tree & Topic Mapping (SPEC-career-coach-phase2.md
§9). Built up incrementally alongside the spec's build order (§10) — see that
doc for the full numbered test list this file works through.
"""
import json
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes import career as career_routes
from app.models.models import Activity, CareerGoal, LearningEvent, MetricEvent, NodeMastery, NodeMeta, Review, Roadmap, RoadmapNode, RoadmapNodePrerequisite
from app.services import career_tree, evidence, topic_mapping
from app.services.career_tree import (
    CareerTreeDraft,
    MAX_NEW_NODES,
    MAX_NODES,
    _find_cycle,
    _load_template,
    _template_to_draft,
    generate_career_tree,
)
from tests.conftest import USER_A, USER_B

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTENT_VALIDATOR = REPO_ROOT / "content" / "validate_career_templates.py"
TEMPLATES_DIR = REPO_ROOT / "content" / "career-templates"

BACKEND_ROLE = "backend"


async def _create_goal_and_generate_draft(client, role_key=BACKEND_ROLE, title="Backend SDE, Jan 2027"):
    # Reset the daily-generation counter — it's a module-level dict shared
    # across every test in this process, keyed by user id, and each helper
    # call spends one of CAREER_TREE_DAILY_LIMIT's slots.
    career_routes._generate_counts.clear()
    resp = await client.post("/api/career/goals/", json={"role_key": role_key, "title": title})
    assert resp.status_code == 201, resp.text
    gen = await client.post("/api/career/tree/generate", json={"role_key": role_key, "goal_title": title})
    assert gen.status_code == 200, gen.text
    return gen.json()


# --- Templates (§9 tests 1-2) ------------------------------------------------

def test_all_shipped_templates_pass_validator():
    result = subprocess.run([sys.executable, str(CONTENT_VALIDATOR)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_stable_keys_unique_no_cycles_deps_resolve():
    for path in TEMPLATES_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        stable_keys = set()
        graph = {}
        for subject in data["subjects"]:
            for node in subject["nodes"]:
                assert node["stable_key"] not in stable_keys, f"duplicate {node['stable_key']} in {path.name}"
                stable_keys.add(node["stable_key"])
                graph[node["stable_key"]] = list(node.get("depends_on") or [])
        for stable_key, deps in graph.items():
            for dep in deps:
                assert dep in stable_keys, f"{path.name}: '{stable_key}' depends_on unresolved '{dep}'"
        assert _find_cycle(graph) is None, f"dependency cycle found in {path.name}"


# --- Generation (§9 tests 3-7) -----------------------------------------------

@pytest.fixture
def force_configured(monkeypatch):
    """generation_configured() checks live API keys, which tests never set —
    force it on so _call_model actually gets exercised instead of the
    unconfigured-provider fallback short-circuit."""
    monkeypatch.setattr(career_tree, "generation_configured", lambda: True)


def _draft_json(role_key, template):
    return _template_to_draft(role_key, template).model_dump_json()


async def test_invented_subject_rejected_retried_then_falls_back(monkeypatch, force_configured):
    template = _load_template(BACKEND_ROLE)
    bad = json.loads(_draft_json(BACKEND_ROLE, template))
    bad["subjects"][0]["key"] = "totally_new_subject_not_in_template"

    calls = {"n": 0}

    async def fake_call(prompt):
        calls["n"] += 1
        return json.dumps(bad)

    monkeypatch.setattr(career_tree, "_call_model", fake_call)

    draft = await generate_career_tree(BACKEND_ROLE, "Backend SDE")

    assert calls["n"] == 2  # one attempt + one retry, both rejected
    assert draft.model_dump() == _template_to_draft(BACKEND_ROLE, template).model_dump()  # fell back


async def test_too_many_nodes_rejected_retried_then_falls_back(monkeypatch, force_configured):
    template = _load_template(BACKEND_ROLE)
    bad = json.loads(_draft_json(BACKEND_ROLE, template))
    # Pad one subject with enough new custom.* nodes to exceed MAX_NODES.
    existing_total = sum(len(s["nodes"]) for s in bad["subjects"])
    extra_needed = MAX_NODES - existing_total + 1
    bad["subjects"][0]["nodes"].extend([
        {
            "stable_key": f"custom.extra_{i}",
            "title": f"Extra node {i}",
            "est_effort_min": 30,
            "priority": 3,
            "depends_on": [],
            "diagnostic_probe": None,
        }
        for i in range(extra_needed)
    ])

    calls = {"n": 0}

    async def fake_call(prompt):
        calls["n"] += 1
        return json.dumps(bad)

    monkeypatch.setattr(career_tree, "_call_model", fake_call)

    draft = await generate_career_tree(BACKEND_ROLE, "Backend SDE")

    assert calls["n"] == 2
    assert draft.model_dump() == _template_to_draft(BACKEND_ROLE, template).model_dump()


async def test_cyclic_depends_on_rejected_retried_then_falls_back(monkeypatch, force_configured):
    template = _load_template(BACKEND_ROLE)
    bad = json.loads(_draft_json(BACKEND_ROLE, template))
    n0 = bad["subjects"][0]["nodes"][0]
    n1 = bad["subjects"][0]["nodes"][1]
    n0["depends_on"] = [n1["stable_key"]]
    n1["depends_on"] = [n0["stable_key"]]  # cycle: n0 <-> n1

    calls = {"n": 0}

    async def fake_call(prompt):
        calls["n"] += 1
        return json.dumps(bad)

    monkeypatch.setattr(career_tree, "_call_model", fake_call)

    draft = await generate_career_tree(BACKEND_ROLE, "Backend SDE")

    assert calls["n"] == 2
    assert draft.model_dump() == _template_to_draft(BACKEND_ROLE, template).model_dump()


async def test_generation_never_touches_the_db(monkeypatch, force_configured):
    """Proposal-only guarantee: generate_career_tree takes no db session and
    can be called with nothing but in-memory state."""
    template = _load_template(BACKEND_ROLE)

    async def fake_call(prompt):
        return _draft_json(BACKEND_ROLE, template)

    monkeypatch.setattr(career_tree, "_call_model", fake_call)

    draft = await generate_career_tree(BACKEND_ROLE, "Backend SDE")
    assert isinstance(draft, CareerTreeDraft)
    assert len(draft.subjects) > 0


async def test_fourth_generation_in_a_day_is_rate_limited(client):
    """Unconfigured in the test env (no API keys set) -> every call takes the
    fast unmodified-template fallback path, so this only needs to exercise
    the route's daily counter, not the model call. The counter is a
    module-level dict (same in-memory-is-fine reasoning as syllabus.py's
    daily limit) — cleared here so test order can't leave it pre-tripped."""
    career_routes._generate_counts.clear()
    body = {"role_key": BACKEND_ROLE, "goal_title": "Backend SDE, Jan 2027"}
    for _ in range(3):
        resp = await client.post("/api/career/tree/generate", json=body)
        assert resp.status_code == 200

    resp = await client.post("/api/career/tree/generate", json=body)
    assert resp.status_code == 429


# --- Commit (§9 tests 8-11) --------------------------------------------------

async def test_commit_creates_roadmap_nodes_meta_and_prereq_edges(client, db):
    draft = await _create_goal_and_generate_draft(client)
    commit = await client.post("/api/career/tree/commit", json=draft)
    assert commit.status_code == 201, commit.text
    goal_out = commit.json()

    roadmap_id = uuid.UUID(goal_out["roadmap_id"])
    template_node_count = sum(len(s["nodes"]) for s in draft["subjects"])

    nodes = (await db.execute(select(RoadmapNode).where(RoadmapNode.roadmap_id == roadmap_id))).scalars().all()
    assert len(nodes) == template_node_count

    metas = (
        await db.execute(select(NodeMeta).where(NodeMeta.node_id.in_([n.id for n in nodes])))
    ).scalars().all()
    assert len(metas) == template_node_count

    # A known template edge: two_pointers depends on arrays.basics.
    stable_key_to_node = {m.stable_key: m.node_id for m in metas}
    child = stable_key_to_node["dsa.arrays.two_pointers"]
    parent = stable_key_to_node["dsa.arrays.basics"]
    edge = (
        await db.execute(
            select(RoadmapNodePrerequisite).where(
                RoadmapNodePrerequisite.node_id == child,
                RoadmapNodePrerequisite.prerequisite_node_id == parent,
            )
        )
    ).scalar_one_or_none()
    assert edge is not None


async def test_commit_is_atomic_on_injected_failure(client, db, monkeypatch):
    draft = await _create_goal_and_generate_draft(client, title="Atomicity check")

    async def boom(self, *args, **kwargs):
        raise RuntimeError("simulated failure mid-commit")

    monkeypatch.setattr(AsyncSession, "commit", boom)

    with pytest.raises(Exception):
        await client.post("/api/career/tree/commit", json=draft)

    monkeypatch.undo()  # restore real commit so this test's own verification query works
    user_id = uuid.UUID(USER_A.id)
    roadmaps = (await db.execute(select(Roadmap).where(Roadmap.user_id == user_id))).scalars().all()
    assert roadmaps == []


async def test_template_version_pinned_on_goal(client):
    draft = await _create_goal_and_generate_draft(client)
    commit = await client.post("/api/career/tree/commit", json=draft)
    assert commit.status_code == 201
    # Pinned to whatever version the draft was generated from — the CURRENT
    # latest on disk, not a hardcoded literal (templates version over time).
    latest = next(t["version"] for t in career_tree.list_templates() if t["role_key"] == BACKEND_ROLE)
    assert commit.json()["template_version"] == draft["template_version"] == latest


async def test_second_active_goal_archives_first(client, db):
    career_routes._generate_counts.clear()
    first = await client.post("/api/career/goals/", json={"role_key": BACKEND_ROLE, "title": "First goal"})
    assert first.status_code == 201
    first_id = uuid.UUID(first.json()["id"])

    second = await client.post("/api/career/goals/", json={"role_key": BACKEND_ROLE, "title": "Second goal"})
    assert second.status_code == 201
    second_id = uuid.UUID(second.json()["id"])

    user_id = uuid.UUID(USER_A.id)
    first_row = (await db.execute(select(CareerGoal).where(CareerGoal.id == first_id))).scalar_one()
    second_row = (await db.execute(select(CareerGoal).where(CareerGoal.id == second_id))).scalar_one()
    assert first_row.status == "archived"
    assert second_row.status == "active"

    active = await client.get("/api/career/goals/active")
    assert active.status_code == 200
    assert active.json()["id"] == str(second_id)


async def test_partial_unique_index_rejects_two_active_goals(db):
    """DB-level backstop, not just the route's archive-then-insert: two
    'active' rows for the same user must violate the partial unique index
    even when inserted directly, bypassing the route entirely."""
    user_id = uuid.UUID(USER_A.id)
    db.add(CareerGoal(user_id=user_id, role_key=BACKEND_ROLE, title="A", status="active"))
    await db.flush()

    db.add(CareerGoal(user_id=user_id, role_key=BACKEND_ROLE, title="B", status="active"))
    with pytest.raises(Exception):
        await db.flush()


# --- Diagnostic (§9 tests 12-13) ---------------------------------------------

async def test_get_diagnostic_returns_probes_for_active_goal(client):
    career_routes._generate_counts.clear()
    resp = await client.post("/api/career/goals/", json={"role_key": BACKEND_ROLE, "title": "Diagnostic probes check"})
    assert resp.status_code == 201

    diag = await client.get("/api/career/diagnostic")
    assert diag.status_code == 200
    probes = diag.json()
    assert 1 <= len(probes) <= career_routes.DIAGNOSTIC_PROBE_COUNT
    assert all(p["probe"] and p["node_title"] and p["stable_key"] for p in probes)
    # Highest-priority nodes first (priority 5 exists among the template's probes).
    template = _load_template(BACKEND_ROLE)
    priorities = {n["stable_key"]: n["priority"] for s in template["subjects"] for n in s["nodes"]}
    assert priorities[probes[0]["stable_key"]] == 5


async def test_diagnostic_submit_404s_when_grader_disabled(client):
    career_routes._generate_counts.clear()
    resp = await client.post("/api/career/goals/", json={"role_key": BACKEND_ROLE, "title": "Grader gate check"})
    assert resp.status_code == 201

    submit = await client.post(
        "/api/career/diagnostic/submit",
        json=[{"stable_key": "dsa.arrays.basics", "answer": "O(1) index, O(n) front insert"}],
    )
    assert submit.status_code == 404  # GRADER_ENABLED=False in the test env


async def test_diagnostic_results_replay_into_learning_events_and_mastery(client, db):
    from app.models.models import LearningEvent, NodeMastery

    draft = await _create_goal_and_generate_draft(client, title="Diagnostic replay check")
    draft["diagnostic_results"] = [
        {"stable_key": "dsa.arrays.basics", "grade": 1.0, "recalled": True},
        {"stable_key": "dbms.sql.basics", "grade": 0.5, "recalled": False},
    ]
    commit = await client.post("/api/career/tree/commit", json=draft)
    assert commit.status_code == 201, commit.text
    roadmap_id = uuid.UUID(commit.json()["roadmap_id"])

    nodes = (await db.execute(select(RoadmapNode).where(RoadmapNode.roadmap_id == roadmap_id))).scalars().all()
    metas = (await db.execute(select(NodeMeta).where(NodeMeta.node_id.in_([n.id for n in nodes])))).scalars().all()
    stable_key_to_node_id = {m.stable_key: m.node_id for m in metas}
    node_ids = list(stable_key_to_node_id.values())

    events = (await db.execute(select(LearningEvent).where(LearningEvent.node_id.in_(node_ids)))).scalars().all()
    assert len(events) == 2
    assert all(e.source == "retainhq_coach" for e in events)
    assert all(e.event_type == "RECALL_GRADED" for e in events)
    assert all(e.trust_tier == "T2_verified_internal" for e in events)

    mastery = (
        await db.execute(
            select(NodeMastery).where(NodeMastery.node_id == stable_key_to_node_id["dsa.arrays.basics"])
        )
    ).scalar_one_or_none()
    assert mastery is not None
    assert mastery.m_learned > 0.0


async def test_skipped_diagnostic_leaves_every_node_unexposed(client, db):
    from app.models.models import LearningEvent, NodeMastery

    draft = await _create_goal_and_generate_draft(client, title="No diagnostic check")
    commit = await client.post("/api/career/tree/commit", json=draft)
    assert commit.status_code == 201
    roadmap_id = uuid.UUID(commit.json()["roadmap_id"])

    nodes = (await db.execute(select(RoadmapNode).where(RoadmapNode.roadmap_id == roadmap_id))).scalars().all()
    node_ids = [n.id for n in nodes]

    events = (await db.execute(select(LearningEvent).where(LearningEvent.node_id.in_(node_ids)))).scalars().all()
    assert events == []

    masteries = (await db.execute(select(NodeMastery).where(NodeMastery.node_id.in_(node_ids)))).scalars().all()
    assert masteries == []  # unexposed == no row at all


# --- Mapping (§9 tests 14-16) -------------------------------------------------

async def _commit_backend_tree(client, db, title="Mapping check"):
    """Goal -> generate -> commit, returning {stable_key: node_id} for the
    committed tree."""
    draft = await _create_goal_and_generate_draft(client, title=title)
    commit = await client.post("/api/career/tree/commit", json=draft)
    assert commit.status_code == 201, commit.text
    roadmap_id = uuid.UUID(commit.json()["roadmap_id"])

    nodes = (await db.execute(select(RoadmapNode).where(RoadmapNode.roadmap_id == roadmap_id))).scalars().all()
    metas = (await db.execute(select(NodeMeta).where(NodeMeta.node_id.in_([n.id for n in nodes])))).scalars().all()
    return {m.stable_key: m.node_id for m in metas}


async def test_exact_match_wins_over_embedding(client, db):
    """An activity already mapped via Tier 1 (activity.node_id set) never
    surfaces in the Tier 3 unmapped bucket, regardless of any stray
    evidence_unmapped metric events pointing at it — exact/structured always
    wins, no Tier 2 search even runs."""
    stable_key_to_node_id = await _commit_backend_tree(client, db, title="Exact match check")
    user_id = uuid.UUID(USER_A.id)

    activity = Activity(
        user_id=user_id, topic="Arrays & Time Complexity", difficulty=3, key_memory="key",
        node_id=stable_key_to_node_id["dsa.arrays.basics"],  # already Tier-1 mapped
    )
    db.add(activity)
    await db.flush()
    db.add(MetricEvent(
        user_id=user_id, event_type="evidence_unmapped",
        payload={"reason": "no_node_id", "activity_id": str(activity.id)},
    ))
    await db.commit()

    resp = await client.get("/api/career/unmapped")
    assert resp.status_code == 200
    assert all(row["activity_id"] != str(activity.id) for row in resp.json())


async def test_low_confidence_goes_to_unmapped_bucket_not_a_wrong_assignment(client, db):
    stable_key_to_node_id = await _commit_backend_tree(client, db, title="Low confidence check")
    user_id = uuid.UUID(USER_A.id)

    candidates = [
        {"node_id": node_id, "stable_key": sk, "title": sk, "description": None}
        for sk, node_id in stable_key_to_node_id.items()
    ]
    # Sanity: totally unrelated text scores below the triage floor.
    assert topic_mapping.suggest_node("xyzzy plugh quux frobnicate", candidates) is None

    activity = Activity(user_id=user_id, topic="Completely unrelated gibberish nonsense", difficulty=3, key_memory="key")
    db.add(activity)
    await db.flush()
    db.add(MetricEvent(
        user_id=user_id, event_type="evidence_unmapped",
        payload={"reason": "no_node_id", "activity_id": str(activity.id)},
    ))
    await db.commit()

    resp = await client.get("/api/career/unmapped")
    assert resp.status_code == 200
    row = next(r for r in resp.json() if r["activity_id"] == str(activity.id))
    assert row["suggested_node"] is None  # unmapped, not a guessed wrong node


async def test_assigning_from_triage_recomputes_mastery(client, db):
    stable_key_to_node_id = await _commit_backend_tree(client, db, title="Assign check")
    user_id = uuid.UUID(USER_A.id)
    node_id = stable_key_to_node_id["dsa.arrays.basics"]

    activity = Activity(user_id=user_id, topic="mystery topic", difficulty=3, key_memory="key")
    db.add(activity)
    await db.flush()

    now = datetime.utcnow()
    completed_review = Review(
        user_id=user_id, activity_id=activity.id, status="completed",
        scheduled_for=now, completed_at=now, rating="easy", recalled=True, quality=5,
    )
    db.add(completed_review)
    db.add(MetricEvent(
        user_id=user_id, event_type="evidence_unmapped",
        payload={"reason": "no_node_id", "activity_id": str(activity.id)},
    ))
    await db.commit()

    resp = await client.post(f"/api/career/unmapped/{activity.id}/assign", json={"node_id": str(node_id)})
    assert resp.status_code == 200, resp.text
    assert resp.json()["events_written"] == 1

    await db.refresh(activity)
    assert activity.node_id == node_id

    mastery = (await db.execute(select(NodeMastery).where(NodeMastery.node_id == node_id))).scalar_one_or_none()
    assert mastery is not None
    assert mastery.m_learned > 0.0

    # No longer in the unmapped bucket.
    still_unmapped = await client.get("/api/career/unmapped")
    assert all(r["activity_id"] != str(activity.id) for r in still_unmapped.json())


# --- Evidence survival (§9 tests 17-18) --------------------------------------

async def test_deleting_node_nulls_event_node_id_but_keeps_the_event(client, db):
    stable_key_to_node_id = await _commit_backend_tree(client, db, title="Node delete check")
    node_id = stable_key_to_node_id["dsa.arrays.basics"]
    user_id = uuid.UUID(USER_A.id)

    await evidence.record_event(
        db, user_id,
        event_type="ARTIFACT_BUILT", trust_tier="T2_verified_internal", source="manual",
        node_id=node_id, entity_id=uuid.uuid4(),
    )
    await db.commit()

    events_before = (
        await db.execute(select(LearningEvent).where(LearningEvent.node_id == node_id))
    ).scalars().all()
    assert len(events_before) == 1
    event_id = events_before[0].id

    resp = await client.delete(f"/api/career/nodes/{node_id}")
    assert resp.status_code == 204, resp.text

    # The DELETE ran on a different session (client's own, per request) — this
    # session's identity map still holds the pre-delete object from
    # events_before above, so force a fresh read rather than the stale cache.
    db.expire_all()

    event = (await db.execute(select(LearningEvent).where(LearningEvent.id == event_id))).scalar_one_or_none()
    assert event is not None  # survives — never deleted
    assert event.node_id is None  # detached
    assert event.payload.get("detached_from_stable_key") == "dsa.arrays.basics"

    node = (await db.execute(select(RoadmapNode).where(RoadmapNode.id == node_id))).scalar_one_or_none()
    assert node is None  # the node itself IS gone


async def test_goal_switch_preserves_every_prior_learning_event(client, db):
    stable_key_to_node_id = await _commit_backend_tree(client, db, title="Goal switch check")
    node_id = stable_key_to_node_id["dsa.arrays.basics"]
    user_id = uuid.UUID(USER_A.id)

    await evidence.record_event(
        db, user_id,
        event_type="ARTIFACT_BUILT", trust_tier="T2_verified_internal", source="manual",
        node_id=node_id, entity_id=uuid.uuid4(),
    )
    await db.commit()

    events_before = (
        await db.execute(select(LearningEvent).where(LearningEvent.node_id == node_id))
    ).scalars().all()
    assert len(events_before) == 1

    career_routes._generate_counts.clear()
    switch = await client.post("/api/career/goals/", json={"role_key": BACKEND_ROLE, "title": "New goal"})
    assert switch.status_code == 201

    events_after = (
        await db.execute(select(LearningEvent).where(LearningEvent.node_id == node_id))
    ).scalars().all()
    assert len(events_after) == 1
    assert events_after[0].id == events_before[0].id

    # The old roadmap is archived, not dropped — the node still exists.
    node = (await db.execute(select(RoadmapNode).where(RoadmapNode.id == node_id))).scalar_one_or_none()
    assert node is not None


# --- Ownership (§9 test 19) ---------------------------------------------------

async def test_user_b_cannot_access_user_a_goal_nodes_or_unmapped(client, db, as_user):
    stable_key_to_node_id = await _commit_backend_tree(client, db, title="Ownership check")
    node_id = stable_key_to_node_id["dsa.arrays.basics"]
    user_a_id = uuid.UUID(USER_A.id)

    activity = Activity(user_id=user_a_id, topic="owner-only activity", difficulty=3, key_memory="key")
    db.add(activity)
    await db.flush()
    db.add(MetricEvent(
        user_id=user_a_id, event_type="evidence_unmapped",
        payload={"reason": "no_node_id", "activity_id": str(activity.id)},
    ))
    await db.commit()

    as_user(USER_B)

    active = await client.get("/api/career/goals/active")
    assert active.status_code == 404

    patch = await client.patch(f"/api/career/nodes/{node_id}", json={"priority": 1})
    assert patch.status_code == 404

    delete_resp = await client.delete(f"/api/career/nodes/{node_id}")
    assert delete_resp.status_code == 404

    unmapped = await client.get("/api/career/unmapped")
    assert unmapped.status_code == 200
    assert unmapped.json() == []  # B's own list, never A's

    assign = await client.post(f"/api/career/unmapped/{activity.id}/assign", json={"node_id": str(node_id)})
    assert assign.status_code == 404

    # Confirm nothing was touched on A's side.
    node = (await db.execute(select(RoadmapNode).where(RoadmapNode.id == node_id))).scalar_one_or_none()
    assert node is not None and node.title  # untouched, still exists

    sprint = await client.post("/api/career/sprint", json={"node_id": str(node_id), "sprint_until": "2026-08-01"})
    assert sprint.status_code == 404  # B has no active goal, and node isn't B's either


# --- Sprint Mode (§6, parent A3) ---------------------------------------------

async def test_declare_sprint_stores_node_and_end_date(client, db):
    stable_key_to_node_id = await _commit_backend_tree(client, db, title="Sprint check")
    node_id = stable_key_to_node_id["dsa.arrays.basics"]

    resp = await client.post("/api/career/sprint", json={"node_id": str(node_id), "sprint_until": "2026-08-01"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["sprint_node_id"] == str(node_id)
    assert body["sprint_until"] == "2026-08-01"

    user_id = uuid.UUID(USER_A.id)
    goal = (
        await db.execute(select(CareerGoal).where(CareerGoal.user_id == user_id, CareerGoal.status == "active"))
    ).scalar_one()
    assert goal.sprint_node_id == node_id


# --- Probe selection (SPEC-career-templates-v2 §2, tests T1-T3) ---------------

def _subject_of(template, stable_key):
    for subject in template["subjects"]:
        if any(n["stable_key"] == stable_key for n in subject["nodes"]):
            return subject["key"]
    return None


@pytest.mark.parametrize("role_key", [t["role_key"] for t in career_tree.list_templates()])
def test_probe_selection_spans_subjects(role_key):
    """T1: the flat priority sort was subject-blind (stable sort -> file order
    on ties -> early subjects monopolized all 8 slots). Round-robin must span
    min(8, subjects-with-probes) distinct subjects for every shipped template."""
    template = _load_template(role_key)
    selected = career_routes._select_diagnostic_probes(template)

    subjects_with_probes = {
        s["key"] for s in template["subjects"]
        if any(n.get("diagnostic_probe") and n.get("diagnostic_answer") for n in s["nodes"])
    }
    selected_subjects = {_subject_of(template, n["stable_key"]) for n in selected}
    assert len(selected_subjects) >= min(len(selected), len(subjects_with_probes))


def test_ai_engineer_diagnostic_includes_llm_and_genai_probes():
    """T2: the exact regression — the AI Engineer diagnostic previously asked
    8 math/classical-ML questions and zero LLM/GenAI questions."""
    template = _load_template("ai_engineer")
    selected = career_routes._select_diagnostic_probes(template)
    selected_subjects = {_subject_of(template, n["stable_key"]) for n in selected}
    assert "nlp_llms" in selected_subjects
    assert "genai_engineering" in selected_subjects


def test_probe_selection_is_deterministic():
    """T3: no randomness — a refresh mid-diagnostic must serve the same set."""
    template = _load_template("ai_engineer")
    first = [n["stable_key"] for n in career_routes._select_diagnostic_probes(template)]
    second = [n["stable_key"] for n in career_routes._select_diagnostic_probes(template)]
    assert first == second and len(first) == career_routes.DIAGNOSTIC_PROBE_COUNT


# --- Provider routing + generation observability -----------------------------

def test_provider_routes_three_ways(monkeypatch):
    """The old rule was 'gemini* -> Google, EVERYTHING else -> Anthropic', so a
    DeepSeek/Qwen/GLM id silently went to Anthropic and failed naming the wrong
    vendor. Cost-driven provider switches have to be an env change, not a code one."""
    from app.core.config import settings as s

    for model, expected in [
        ("gemini-3.6-flash", "gemini"),
        ("claude-opus-4-8", "anthropic"),
        ("deepseek-chat", "openai_compat"),
        ("qwen-max", "openai_compat"),
        ("glm-4-plus", "openai_compat"),
    ]:
        monkeypatch.setattr(s, "CAREER_TREE_MODEL", model)
        assert career_tree._provider() == expected, model


def test_generation_configured_per_provider(monkeypatch):
    from app.core.config import settings as s

    monkeypatch.setattr(s, "CAREER_TREE_MODEL", "deepseek-chat")
    monkeypatch.setattr(s, "OPENAI_COMPAT_BASE_URL", "")
    monkeypatch.setattr(s, "OPENAI_COMPAT_API_KEY", "")
    assert career_tree.generation_configured() is False, "must not claim configured without a base_url"

    monkeypatch.setattr(s, "OPENAI_COMPAT_BASE_URL", "https://api.deepseek.com/v1")
    monkeypatch.setattr(s, "OPENAI_COMPAT_API_KEY", "sk-test")
    assert career_tree.generation_configured() is True


async def test_fallback_reports_its_outcome(monkeypatch, force_configured):
    """The load-bearing one. A model that fails validation twice degrades every
    learner of a role to the identical unmodified template — and used to do it
    in total silence, returning a valid 200 with nothing logged. That made any
    model swap unmeasurable."""
    seen: list = []

    async def fake_call(prompt):
        return '{"role_key":"x","template_version":"v1","title":"t","subjects":[{"key":"INVENTED","title":"n","default_priority":3,"nodes":[]}]}'

    monkeypatch.setattr(career_tree, "_call_model", fake_call)
    draft = await generate_career_tree(
        BACKEND_ROLE, "Backend SDE",
        on_outcome=lambda outcome, role_key, violations: seen.append((outcome, violations)),
    )

    assert seen, "the fallback must report — silence here is the bug"
    outcome, violations = seen[0]
    assert outcome == "fallback_validation"
    assert any("invented" in v for v in violations)
    # Still returns a usable tree: never fail onboarding with an error screen.
    assert draft.model_dump() == _template_to_draft(BACKEND_ROLE, _load_template(BACKEND_ROLE)).model_dump()


async def test_clean_generation_reports_adapted(monkeypatch, force_configured):
    seen: list = []
    template = _load_template(BACKEND_ROLE)

    async def fake_call(prompt):
        return _draft_json(BACKEND_ROLE, template)

    monkeypatch.setattr(career_tree, "_call_model", fake_call)
    await generate_career_tree(
        BACKEND_ROLE, "Backend SDE",
        on_outcome=lambda outcome, role_key, violations: seen.append(outcome),
    )
    assert seen == ["adapted"]


async def test_outcome_reporter_failure_never_breaks_generation(monkeypatch, force_configured):
    """Observability must not be able to take down the feature it observes."""
    template = _load_template(BACKEND_ROLE)

    async def fake_call(prompt):
        return _draft_json(BACKEND_ROLE, template)

    def exploding(outcome, role_key, violations):
        raise RuntimeError("telemetry is down")

    monkeypatch.setattr(career_tree, "_call_model", fake_call)
    draft = await generate_career_tree(BACKEND_ROLE, "Backend SDE", on_outcome=exploding)
    assert isinstance(draft, CareerTreeDraft)


def test_openai_compat_prompt_carries_the_lowercase_json_token():
    """DeepSeek's and Qwen/DashScope's JSON modes both require the literal token
    "json" in the messages — DashScope validates it server-side and 400s without
    it. The serialized Pydantic schema cannot be relied on to supply it, so the
    instruction must. Regression guard: rewording this string without keeping a
    lowercase "json" breaks every OpenAI-compatible provider at once, and the
    failure looks like a generic 400, not like a prompt bug.
    """
    assert "json" in career_tree._JSON_ONLY_INSTRUCTION
