"""Career Coach Phase 3 — the scheduler's pure core (SPEC-career-coach-phase3.md
§3, IMPLEMENTATION-career-coach-phase3.md §3). `build_plan` answers one
question: "given ~N minutes today, what should I touch, in what order?"

Hard constraints (never violate these): no imports from app.models or
app.core.database, no async, no datetime.now()/date.today() (the clock is an
input), no randomness. Same inputs -> byte-identical output, forever — the
route layer (api/routes/career.py) is the only thing allowed to touch the DB
or the clock; this module is the golden-suite-verified oracle it calls.

The law this module enforces (ARCHITECTURE-learning-system.md §0, spec §1):
the scheduler never overrides FSRS. Reviews enter the plan in the exact order
they're given, always ahead of study items, never dropped, never reordered.
"""
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

# --- Constants (do not tune — spec §7 / IMPLEMENTATION §3.1; shipped at
# their specified defaults, pending >=2 weeks of post-D-039 dogfood evidence) ---

PREREQ_UNLOCK_THRESHOLD = 0.35   # matches the 'practicing' state boundary
URGENCY_MAX = 2.0
UNLOCK_BONUS = 0.05               # per dependent
UNLOCK_WEIGHT_CAP = 1.5
BALANCE_WINDOW_DAYS = 21
BALANCE_FLAG_THRESHOLD = -0.15
# Evidence floor (§3.8a) — NOT in the parent spec, added to the implementation
# doc 2026-07-26. Below this much logged time in the trailing window, a_s=0
# for every subject and balance_s=-p_s, so the *largest* subject always trips
# the flag on zero evidence (every new user's first plan). Gate the entire
# balance signal on it, not just the promotion — see _compute_balance below.
BALANCE_MIN_WINDOW_MINUTES = 120
REVIEW_COST_MIN = 4
MAX_STUDY_ITEMS = 5
DAILY_MINUTES_DEFAULT = 60
MASTERED_THRESHOLD = 0.85         # G8's 'tree complete' bar
# Urgency's timeline anchor (§3.5 DECISION) — career_goals has no stored start
# date, so "remaining fraction of the goal's timeline" isn't derivable. A
# fixed 180-day horizon is the smallest honest substitute.
PLAN_HORIZON_DAYS = 180


@dataclass(frozen=True)
class PlanNode:
    node_id: str            # str, not UUID — keeps the core free of uuid semantics
    title: str
    subject: str
    priority: int            # 1..5 from node_meta
    est_effort_min: int
    order_index: int         # template order; the deterministic tie-break
    m_learned: float          # 0..1, evidence-accumulated. Gates prerequisites.
    m: float                  # m_learned * retrievability. Drives the score.
    prereq_ids: tuple = ()


@dataclass(frozen=True)
class PlanReview:
    review_id: str
    label: str                # node_title or activity title, for the UI
    scheduled_for: datetime


@dataclass(frozen=True)
class PlanInputs:
    nodes: tuple
    due_reviews: tuple                       # ALREADY ordered oldest-first by the route
    subject_time_shares: dict                # subject -> a_s, share of trailing-window minutes
    total_window_minutes: int                # raw minutes behind those shares — the §3.8a floor
    sprint_node_id: Optional[str]
    sprint_until: Optional[date]
    target_date: Optional[date]
    daily_minutes: int
    now: datetime                             # naive UTC


@dataclass(frozen=True)
class PlanItem:
    kind: str                  # 'review' | 'study' | 'balance'
    review_id: Optional[str]
    node_id: Optional[str]
    label: str
    reason: str                 # REQUIRED, never empty — the trust surface
    est_share: float             # 0..1 of the post-review budget; 0.0 for reviews


@dataclass(frozen=True)
class DayPlan:
    items: tuple
    balance: dict                # subject -> a_s - p_s
    overflow: bool
    tree_complete: bool


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _ordered_unique(values) -> list:
    """Dedupe preserving first-seen order. Plain `set()` iteration order in
    CPython depends on PYTHONHASHSEED for strings — using one here to decide
    a tie-break (see _compute_balance's "most negative subject") would break
    the "same seed -> identical plan" determinism promise (G9) across process
    restarts even though nothing about the *inputs* changed."""
    return list(dict.fromkeys(values))


def _compute_balance(inputs: PlanInputs) -> dict:
    """subject -> a_s - p_s, or {} entirely below the §3.8a evidence floor.
    p_s is each subject's share of summed priority over ALL nodes (not just
    frontier); a_s is its share of trailing-window minutes (given, not
    recomputed here)."""
    if inputs.total_window_minutes < BALANCE_MIN_WINDOW_MINUTES:
        return {}
    if not inputs.nodes:
        return {}

    total_priority = sum(n.priority for n in inputs.nodes)
    subjects = _ordered_unique(n.subject for n in inputs.nodes)
    balance = {}
    for subject in subjects:
        p_s = sum(n.priority for n in inputs.nodes if n.subject == subject) / total_priority
        a_s = inputs.subject_time_shares.get(subject, 0.0)
        balance[subject] = a_s - p_s
    return balance


def build_plan(inputs: PlanInputs) -> DayPlan:
    nodes_by_id = {n.node_id: n for n in inputs.nodes}

    # Step 1 — reviews. Never reorder, never drop, never add (spec §1, the law).
    review_items = tuple(
        PlanItem(kind="review", review_id=r.review_id, node_id=None, label=r.label,
                 reason="due review", est_share=0.0)
        for r in inputs.due_reviews
    )

    # Step 2 — budget.
    review_cost = len(inputs.due_reviews) * REVIEW_COST_MIN
    if review_cost >= inputs.daily_minutes:
        return DayPlan(items=review_items, balance=_compute_balance(inputs), overflow=True, tree_complete=False)

    # Step 3 — tree_complete. Vacuously False when nodes is empty.
    tree_complete = bool(inputs.nodes) and all(n.m_learned >= MASTERED_THRESHOLD for n in inputs.nodes)
    if tree_complete:
        return DayPlan(items=review_items, balance=_compute_balance(inputs), overflow=False, tree_complete=True)

    # Step 4 — frontier. A dangling prereq id (not present in nodes) blocks
    # rather than unlocks — the conservative reading of "absent mastery counts
    # as 0" when it's the *node* that's missing, not just its mastery row.
    def _is_available(n) -> bool:
        if n.m_learned >= MASTERED_THRESHOLD:
            return False
        for prereq_id in n.prereq_ids:
            prereq = nodes_by_id.get(prereq_id)
            prereq_m = prereq.m_learned if prereq is not None else 0.0
            if prereq_m < PREREQ_UNLOCK_THRESHOLD:
                return False
        return True

    frontier = [n for n in inputs.nodes if _is_available(n)]

    # dependents(n): direct only, over ALL nodes (not just frontier).
    dependents_count: dict = {}
    for n in inputs.nodes:
        for prereq_id in n.prereq_ids:
            dependents_count[prereq_id] = dependents_count.get(prereq_id, 0) + 1

    # Step 5 — score.
    if inputs.target_date is None:
        urgency = 1.0
    else:
        days_left = (inputs.target_date - inputs.now.date()).days
        frac = _clamp(1 - days_left / PLAN_HORIZON_DAYS, 0.0, 1.0)
        urgency = 1.0 + (URGENCY_MAX - 1.0) * frac

    def _unlock_weight(n) -> float:
        return min(1 + UNLOCK_BONUS * dependents_count.get(n.node_id, 0), UNLOCK_WEIGHT_CAP)

    def _score(n) -> float:
        return n.priority * (1 - n.m) * urgency * _unlock_weight(n)

    # Step 6 — ordering. Fully deterministic given the inputs.
    scored = [(_score(n), n) for n in frontier]
    scored.sort(key=lambda t: (-t[0], -t[1].priority, t[1].order_index))
    ordered_nodes = [n for _, n in scored]

    # Step 7 — sprint. An expired or mastered sprint is ignored entirely.
    sprint_reason = None
    if (
        inputs.sprint_node_id is not None
        and inputs.sprint_until is not None
        and inputs.now.date() <= inputs.sprint_until
    ):
        frontier_ids = {n.node_id for n in ordered_nodes}
        if inputs.sprint_node_id in frontier_ids:
            sprint_node = nodes_by_id[inputs.sprint_node_id]
            ordered_nodes = [sprint_node] + [n for n in ordered_nodes if n.node_id != sprint_node.node_id]
            sprint_reason = f"sprint: you pinned this until {inputs.sprint_until}"

    sprint_applied = sprint_reason is not None
    sprint_subject = ordered_nodes[0].subject if sprint_applied else None

    # Step 8 — balance. §8a's evidence floor is enforced inside _compute_balance.
    balance = _compute_balance(inputs)
    balance_node_id = None
    balance_reason = None
    if balance:
        # The sprint's own subject is excluded from the CANDIDATE POOL, not
        # just checked after finding the global worst — otherwise a sprint on
        # the single most-neglected subject would suppress the balance signal
        # for every other subject too (contradicts G5: "a different neglected
        # subject is still flaggable").
        candidate_subjects = [s for s in _ordered_unique(n.subject for n in inputs.nodes) if s != sprint_subject]
        worst_subject = min(candidate_subjects, key=lambda s: balance[s]) if candidate_subjects else None
        worst_value = balance[worst_subject] if worst_subject is not None else 0.0
        if worst_subject is not None and worst_value < BALANCE_FLAG_THRESHOLD:
            subject_frontier = [n for n in ordered_nodes if n.subject == worst_subject]
            if subject_frontier:
                balance_node = subject_frontier[0]  # ordered_nodes is already best-scoring-first
                balance_node_id = balance_node.node_id
                a_s = inputs.subject_time_shares.get(worst_subject, 0.0)
                p_s = a_s - worst_value  # balance_s = a_s - p_s  =>  p_s = a_s - balance_s
                balance_reason = (
                    f"{worst_subject} is under-served: {a_s * 100:.0f}% of your time "
                    f"vs {p_s * 100:.0f}% of your plan"
                )
                ordered_nodes = [n for n in ordered_nodes if n.node_id != balance_node_id]
                insert_at = 1 if sprint_applied else 0
                ordered_nodes.insert(insert_at, balance_node)

    # Step 9 — truncate and proportion. AFTER sprint/balance repositioning —
    # a low-scoring pinned/neglected node can bump out whatever ranked #5.
    study_nodes = ordered_nodes[:MAX_STUDY_ITEMS]
    total_effort = sum(n.est_effort_min for n in study_nodes)

    # Step 10 — reasons. Every item carries a non-empty reason.
    def _default_reason(n) -> str:
        dep_count = dependents_count.get(n.node_id, 0)
        if dep_count > 0:
            return f"unlocks {dep_count} nodes in {n.subject}"
        return f"{n.subject}: highest-priority available"

    study_items = []
    for n in study_nodes:
        if sprint_applied and n.node_id == inputs.sprint_node_id:
            kind, reason = "study", sprint_reason
        elif n.node_id == balance_node_id:
            kind, reason = "balance", balance_reason
        else:
            kind, reason = "study", _default_reason(n)
        share = (n.est_effort_min / total_effort) if total_effort else 0.0
        study_items.append(PlanItem(
            kind=kind, review_id=None, node_id=n.node_id, label=n.title, reason=reason, est_share=share,
        ))

    return DayPlan(
        items=review_items + tuple(study_items),
        balance=balance,
        overflow=False,
        tree_complete=False,
    )
