"""Career Coach Phase 3 — Scheduler golden suite (SPEC-career-coach-phase3.md
§5, IMPLEMENTATION-career-coach-phase3.md §4). Written BEFORE services/planner.py
exists — every G1-G10 scenario here pins a behavioral promise the pure core
must satisfy. If a scenario can't be written as inputs -> expected properties,
the behavior is underspecified and must not ship (spec §0).

make_inputs() builds a small synthetic 6-node tree across three subjects
(dsa/os/dbms) so each scenario states only what it changes. G4/G4b/G5/G6 use
a smaller custom 2-3 node set where the balance/sprint arithmetic needs to
hit exact thresholds.

`total_window_minutes` defaults to 0 (below BALANCE_MIN_WINDOW_MINUTES) so
every scenario that doesn't care about balance gets it silently for free
(§3.8a's evidence floor) — only G4/G4b/G5/G6 opt in by raising it.
"""
import json
import random
from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path

import pytest

from app.services.planner import (
    BALANCE_FLAG_THRESHOLD,
    BALANCE_MIN_WINDOW_MINUTES,
    MASTERED_THRESHOLD,
    MAX_STUDY_ITEMS,
    PREREQ_UNLOCK_THRESHOLD,
    REVIEW_COST_MIN,
    DayPlan,
    PlanInputs,
    PlanItem,
    PlanNode,
    PlanReview,
    build_plan,
)

GOLDENS_DIR = Path(__file__).parent / "goldens"
DEFAULT_NOW = datetime(2026, 7, 26, 9, 0, 0)

# (node_id, subject, priority, est_effort_min, order_index, prereq_ids)
DEFAULT_NODE_DEFS = [
    ("dsa.arrays", "dsa", 5, 30, 0, ()),
    ("dsa.two_pointers", "dsa", 4, 30, 1, ("dsa.arrays",)),
    ("dsa.graphs", "dsa", 5, 45, 2, ("dsa.two_pointers",)),
    ("os.processes", "os", 3, 20, 3, ()),
    ("os.threads", "os", 3, 25, 4, ("os.processes",)),
    ("dbms.sql_basics", "dbms", 2, 20, 5, ()),
]


def _node(node_id, subject, priority, effort, order_index, prereq_ids, m_learned):
    return PlanNode(
        node_id=node_id, title=node_id, subject=subject, priority=priority,
        est_effort_min=effort, order_index=order_index,
        m_learned=m_learned, m=m_learned, prereq_ids=tuple(prereq_ids),
    )


def make_inputs(
    m_learned=None,
    due_reviews=(),
    subject_time_shares=None,
    total_window_minutes=0,
    sprint_node_id=None,
    sprint_until=None,
    target_date=None,
    daily_minutes=60,
    now=DEFAULT_NOW,
    nodes=None,
):
    m_learned = m_learned or {}
    if nodes is None:
        nodes = tuple(
            _node(nid, subj, pr, eff, oi, prereqs, m_learned.get(nid, 0.0))
            for nid, subj, pr, eff, oi, prereqs in DEFAULT_NODE_DEFS
        )
    return PlanInputs(
        nodes=nodes,
        due_reviews=tuple(due_reviews),
        subject_time_shares=subject_time_shares or {},
        total_window_minutes=total_window_minutes,
        sprint_node_id=sprint_node_id,
        sprint_until=sprint_until,
        target_date=target_date,
        daily_minutes=daily_minutes,
        now=now,
    )


def _review(review_id, label, scheduled_for):
    return PlanReview(review_id=review_id, label=label, scheduled_for=scheduled_for)


def _serialize(plan: DayPlan) -> dict:
    """JSON-comparable snapshot — sorted keys, datetimes as isoformat, mirrors
    the DSA golden convention (exact-output snapshot)."""
    return json.loads(json.dumps(asdict(plan), default=str, sort_keys=True))


def _assert_snapshot(plan: DayPlan, name: str):
    path = GOLDENS_DIR / name
    actual = _serialize(plan)
    if not path.exists():
        path.write_text(json.dumps(actual, indent=2, sort_keys=True), encoding="utf-8")
        pytest.fail(f"Golden {name} did not exist — wrote it. Re-run after reviewing it.")
    expected = json.loads(path.read_text(encoding="utf-8"))
    assert actual == expected, f"{name} snapshot diverged — a diff must be a deliberate, reviewed decision"


def _study_node_ids(plan: DayPlan) -> list:
    return [i.node_id for i in plan.items if i.kind in ("study", "balance")]


def _review_ids(plan: DayPlan) -> list:
    return [i.review_id for i in plan.items if i.kind == "review"]


# --- G1: Cold start -----------------------------------------------------------

def _g1_inputs():
    return make_inputs()  # total_window_minutes=0 -> below the evidence floor


def test_g1_cold_start_is_root_nodes_only_no_balance_noise():
    inputs = _g1_inputs()
    plan = build_plan(inputs)
    root_ids = {nid for nid, _, _, _, _, prereqs in DEFAULT_NODE_DEFS if not prereqs}
    assert set(_study_node_ids(plan)) <= root_ids
    assert len(plan.items) <= 5
    assert all(i.reason for i in plan.items)
    # §3.8a: zero logged time must never produce a confident "under-served" nudge.
    assert plan.balance == {}
    assert all(i.kind != "balance" for i in plan.items)
    _assert_snapshot(plan, "plan_g1.json")


# --- G2: Overdue pile -----------------------------------------------------------

def _g2_inputs():
    reviews = [
        _review(f"r{i}", f"Review {i}", DEFAULT_NOW.replace(hour=0))
        for i in range(10)
    ]
    return make_inputs(due_reviews=reviews, daily_minutes=30)


def test_g2_overdue_pile_is_reviews_only_overflow():
    inputs = _g2_inputs()
    plan = build_plan(inputs)
    assert _review_ids(plan) == [r.review_id for r in inputs.due_reviews]
    assert len(_review_ids(plan)) == 10
    assert _study_node_ids(plan) == []
    assert plan.overflow is True


# --- G3: Deadline crunch --------------------------------------------------------

def _g3_inputs(target_date):
    m_learned = {"dsa.arrays": 0.5, "os.processes": 0.4}
    return make_inputs(m_learned=m_learned, target_date=target_date, daily_minutes=90)


def test_g3_crunch_vs_open_ended_never_drops_reviews_or_higher_priority_study():
    crunch = build_plan(_g3_inputs(date(2026, 8, 9)))          # 14 days out
    open_ended = build_plan(_g3_inputs(None))

    assert _review_ids(crunch) == _review_ids(open_ended) == []
    # Urgency is a plan-wide multiplier (same factor for every frontier node),
    # so it cannot reorder or drop anything relative to the open-ended plan —
    # the crunch study set is always a superset (here, equal to) the open-ended one.
    assert set(_study_node_ids(open_ended)) <= set(_study_node_ids(crunch))


# --- G4: Neglected subject, evidence floor cleared ------------------------------

def _g4_inputs(total_window_minutes=600):
    nodes = (
        _node("dsa.solo", "dsa", 6, 30, 0, (), 0.0),
        _node("os.solo", "os", 4, 30, 1, (), 0.0),
    )
    # p_s(os) = 4/10 = 0.4, a_s(os) = 0.1 -> balance_s = -0.3 < -0.15
    return make_inputs(
        nodes=nodes,
        subject_time_shares={"os": 0.1, "dsa": 0.9},
        total_window_minutes=total_window_minutes,
    )


def test_g4_neglected_subject_gets_one_balance_item_at_slot_0():
    inputs = _g4_inputs()
    plan = build_plan(inputs)
    balance_items = [i for i in plan.items if i.kind == "balance"]
    assert len(balance_items) == 1
    study_items = [i for i in plan.items if i.kind in ("study", "balance")]
    assert study_items[0].kind == "balance"
    assert study_items[0].node_id == "os.solo"
    assert "os" in balance_items[0].reason
    assert plan.balance["os"] < BALANCE_FLAG_THRESHOLD
    _assert_snapshot(plan, "plan_g4.json")


# --- G4b: same shares, evidence floor NOT cleared -------------------------------

def test_g4b_same_shares_but_below_evidence_floor_suppresses_balance():
    assert 119 < BALANCE_MIN_WINDOW_MINUTES
    inputs = _g4_inputs(total_window_minutes=119)
    plan = build_plan(inputs)
    assert plan.balance == {}
    assert all(i.kind != "balance" for i in plan.items)


# --- G5: Sprint + neglect on the same subject -----------------------------------

def _g5_inputs(sprint_until=date(2026, 8, 5)):
    # p_s: dsa=14/22, os=6/22, dbms=2/22 (same weights as the default tree).
    shares = {"dsa": 0.10, "os": 0.05, "dbms": 0.85}
    return make_inputs(
        subject_time_shares=shares,
        total_window_minutes=600,
        sprint_node_id="dsa.arrays",
        sprint_until=sprint_until,
    )


def test_g5_sprint_suppresses_own_subject_but_not_others():
    inputs = _g5_inputs()
    plan = build_plan(inputs)
    study_items = [i for i in plan.items if i.kind in ("study", "balance")]

    assert study_items[0].node_id == "dsa.arrays"
    assert study_items[0].kind == "study"
    assert study_items[0].reason.startswith("sprint:")

    balance_items = [i for i in plan.items if i.kind == "balance"]
    assert all(i.node_id != "dsa.arrays" for i in balance_items)
    # dsa is the worst-off subject but is suppressed (it's the sprint's own
    # subject) -> os (also below threshold) is the one that gets flagged.
    assert any(i.node_id == "os.processes" for i in balance_items)
    assert plan.balance["dsa"] < BALANCE_FLAG_THRESHOLD  # still reported, just not promoted


# --- G6: Expired sprint -----------------------------------------------------------

def test_g6_expired_sprint_is_identical_to_no_sprint():
    with_expired_sprint = build_plan(_g5_inputs(sprint_until=date(2026, 7, 25)))  # yesterday
    no_sprint = build_plan(make_inputs(
        subject_time_shares={"dsa": 0.10, "os": 0.05, "dbms": 0.85},
        total_window_minutes=600,
        sprint_node_id=None,
    ))
    assert with_expired_sprint == no_sprint


# --- G7: Mid-journey --------------------------------------------------------------

def _g7_inputs():
    m_learned = {
        "dsa.arrays": 0.5, "dsa.two_pointers": 0.0, "dsa.graphs": 0.0,
        "os.processes": 0.4, "os.threads": 0.0, "dbms.sql_basics": 0.2,
    }
    reviews = [
        _review("r1", "Review 1", DEFAULT_NOW.replace(hour=1)),
        _review("r2", "Review 2", DEFAULT_NOW.replace(hour=2)),
        _review("r3", "Review 3", DEFAULT_NOW.replace(hour=3)),
    ]
    return make_inputs(m_learned=m_learned, due_reviews=reviews, daily_minutes=90)


def test_g7_mid_journey_reviews_first_prereqs_respected_shares_sum_to_one():
    inputs = _g7_inputs()
    plan = build_plan(inputs)

    kinds = [i.kind for i in plan.items]
    first_study_idx = next(idx for idx, k in enumerate(kinds) if k in ("study", "balance"))
    assert all(k == "review" for k in kinds[:first_study_idx])

    nodes_by_id = {n.node_id: n for n in inputs.nodes}
    for item in plan.items:
        if item.kind not in ("study", "balance"):
            continue
        node = nodes_by_id[item.node_id]
        for prereq_id in node.prereq_ids:
            assert nodes_by_id[prereq_id].m_learned >= PREREQ_UNLOCK_THRESHOLD

    study_shares = [i.est_share for i in plan.items if i.kind in ("study", "balance")]
    assert abs(sum(study_shares) - 1.0) < 1e-6
    _assert_snapshot(plan, "plan_g7.json")


# --- G8: Tree complete --------------------------------------------------------------

def _g8_inputs():
    m_learned = {nid: 0.9 for nid, *_ in DEFAULT_NODE_DEFS}
    reviews = [_review("r1", "Review 1", DEFAULT_NOW.replace(hour=1))]
    return make_inputs(m_learned=m_learned, due_reviews=reviews)


def test_g8_everything_mastered_is_reviews_only_tree_complete():
    inputs = _g8_inputs()
    plan = build_plan(inputs)
    assert plan.tree_complete is True
    assert _study_node_ids(plan) == []
    assert _review_ids(plan) == ["r1"]


def test_g8_empty_tree_is_vacuously_not_complete():
    inputs = make_inputs(nodes=())
    plan = build_plan(inputs)
    assert plan.tree_complete is False


# --- G9: Prereq integrity under adversarial mastery (property test) -----------------

def _random_dag_inputs(seed: int, size: int = 200):
    rnd = random.Random(seed)
    subjects = ["dsa", "os", "dbms", "networks"]
    defs = []
    for i in range(size):
        node_id = f"n{i}"
        subject = rnd.choice(subjects)
        priority = rnd.randint(1, 5)
        effort = rnd.randint(10, 60)
        # Only ever point backwards -> acyclic by construction.
        num_prereqs = rnd.randint(0, min(3, i))
        prereq_ids = tuple(rnd.sample([f"n{j}" for j in range(i)], num_prereqs)) if i > 0 else ()
        defs.append((node_id, subject, priority, effort, i, prereq_ids))

    nodes = tuple(
        _node(nid, subj, pr, eff, oi, prereqs, rnd.random())
        for nid, subj, pr, eff, oi, prereqs in defs
    )
    return make_inputs(nodes=nodes, daily_minutes=120)


@pytest.mark.parametrize("seed", range(50))
def test_g9_no_plan_ever_has_an_unmet_prerequisite(seed):
    inputs = _random_dag_inputs(seed)
    plan = build_plan(inputs)
    nodes_by_id = {n.node_id: n for n in inputs.nodes}
    for item in plan.items:
        if item.kind not in ("study", "balance"):
            continue
        node = nodes_by_id[item.node_id]
        for prereq_id in node.prereq_ids:
            assert nodes_by_id[prereq_id].m_learned >= PREREQ_UNLOCK_THRESHOLD


@pytest.mark.parametrize("seed", range(50))
def test_g9_same_seed_is_deterministic(seed):
    plan_a = build_plan(_random_dag_inputs(seed))
    plan_b = build_plan(_random_dag_inputs(seed))
    assert plan_a == plan_b


# --- G10: FSRS non-interference (the law) -------------------------------------------

_ALL_SCENARIO_BUILDERS = [
    _g1_inputs,
    _g2_inputs,
    lambda: _g3_inputs(date(2026, 8, 9)),
    lambda: _g3_inputs(None),
    _g4_inputs,
    lambda: _g4_inputs(total_window_minutes=119),
    _g5_inputs,
    lambda: _g5_inputs(sprint_until=date(2026, 7, 25)),
    _g7_inputs,
    _g8_inputs,
]


@pytest.mark.parametrize("build_inputs", _ALL_SCENARIO_BUILDERS)
def test_g10_review_order_and_placement_never_disturbed(build_inputs):
    inputs = build_inputs()
    plan = build_plan(inputs)

    assert _review_ids(plan) == [r.review_id for r in inputs.due_reviews]

    kinds = [i.kind for i in plan.items]
    first_study_idx = next((idx for idx, k in enumerate(kinds) if k in ("study", "balance")), len(kinds))
    assert all(k == "review" for k in kinds[:first_study_idx])
