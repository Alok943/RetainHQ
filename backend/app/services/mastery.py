"""Mastery computation (SPEC-teacher-dashboard.md §3). Pure functions, no DB —
the router does the SQL, folds rows into the primitives below, and never
re-derives status client-side.

Per-node status combines two signal sources: test_attempts (objective,
outcome-graded) and node-linked activity/review history (FSRS, self-reported
recall). When enough test evidence exists it wins outright; otherwise we fall
back to review evidence. Below the "enough evidence" floor on both sources,
status stays `untouched` rather than inventing precision from one data point
(the "honest floor" convention — see spec §3).
"""
from datetime import datetime, timedelta
from typing import Optional

# Tune these here only — nowhere else in the codebase should hardcode these
# thresholds (spec §3 / §4.2).
WEAK_ACCURACY_MAX = 0.5          # test accuracy below this -> weak
DEVELOPING_ACCURACY_MAX = 0.8    # test accuracy below this (and >= weak) -> developing
MIN_TEST_RESULTS = 2             # results needed before test evidence counts at all
WEAK_STABILITY_DAYS = 7.0        # FSRS stability below this -> "will forget by the exam"

AT_RISK_INACTIVE_DAYS = 7
AT_RISK_RECALL_RATE = 0.5
AT_RISK_RECALL_WINDOW = 10
AT_RISK_OVERDUE_COUNT = 15

CLASS_CELL_MIN_COVERAGE = 0.3    # fraction of the class needing real signal before a gap-map cell is anything but "insufficient data"

# Weighted precedence for class_cell_status: a meaningful weak share should
# tip the cell toward "weak" even if developing/strong have larger raw counts
# (spec §7 — "weighted weak > developing > strong", not naive plurality).
_CELL_STATUS_WEIGHT = {"weak": 3, "developing": 2, "strong": 1}


def compute_node_status(
    test_got: int,
    test_missed: int,
    test_wrong: int,
    review_recalled_history: list[bool],
    stability: Optional[float],
) -> str:
    """Returns one of "untouched" | "weak" | "developing" | "strong"."""
    test_total = test_got + test_missed + test_wrong

    if test_total == 0 and not review_recalled_history:
        return "untouched"

    if test_total >= MIN_TEST_RESULTS:
        accuracy = test_got / test_total
        if accuracy < WEAK_ACCURACY_MAX:
            return "weak"
        if accuracy < DEVELOPING_ACCURACY_MAX:
            return "developing"
        return "strong"

    # Below the test-evidence floor: fall back to review evidence, but only if
    # there's enough of it to say anything (a single review is as unreliable
    # as a single test attempt).
    if len(review_recalled_history) < 2:
        return "untouched"

    if review_recalled_history[-2:] == [False, False]:
        return "weak"

    if review_recalled_history[-1] is True:
        if stability is None or stability < WEAK_STABILITY_DAYS:
            return "developing"
        return "strong"

    # Latest was a single miss (not 2+ consecutive) — recent enough of a wobble
    # to not call it "strong", not enough to call it "weak" per spec's 2+ rule.
    return "developing"


def class_cell_status(counts: dict, total_students: int) -> str:
    """counts: {"untouched": int, "weak": int, "developing": int, "strong": int}
    for one class-by-node gap-map cell. Returns "insufficient_data" or the
    weighted-dominant status.
    """
    if total_students <= 0:
        return "insufficient_data"

    non_untouched = sum(counts.get(status, 0) for status in _CELL_STATUS_WEIGHT)
    if non_untouched / total_students < CLASS_CELL_MIN_COVERAGE:
        return "insufficient_data"

    scored = {status: counts.get(status, 0) * weight for status, weight in _CELL_STATUS_WEIGHT.items()}
    return max(scored, key=scored.get)


def find_root_cause(
    node_id,
    weak_student_ids: set,
    prereq_node_ids: list,
    node_status_by_student: dict,
) -> Optional[str]:
    """For a weak node, find the prerequisite (if any) that the same students
    are also weak on — the likely blocker. Picks the prerequisite with the
    strongest overlap (ties broken by prereq_node_ids order), requiring at
    least majority overlap (>=50%) to qualify.
    """
    if not weak_student_ids or not prereq_node_ids:
        return None

    best_prereq = None
    best_overlap_ratio = 0.0
    for prereq_id in prereq_node_ids:
        statuses = node_status_by_student.get(prereq_id, {})
        prereq_weak_ids = {sid for sid, status in statuses.items() if status == "weak"}
        overlap = weak_student_ids & prereq_weak_ids
        overlap_ratio = len(overlap) / len(weak_student_ids)
        if overlap_ratio >= 0.5 and overlap_ratio > best_overlap_ratio:
            best_prereq = prereq_id
            best_overlap_ratio = overlap_ratio

    return best_prereq


def at_risk_flag(
    last_active_at: Optional[datetime],
    now: datetime,
    recall_rate_last10: Optional[float],
    overdue_count: int,
) -> tuple[bool, list[str]]:
    """Spec §4.2: at-risk if any of — no activity in 7 days; recall rate < 0.5
    over the last 10 completed reviews; overdue reviews > 15. Reasons are
    always attached (teachers distrust unexplained flags).
    """
    reasons = []

    if last_active_at is None or now - last_active_at >= timedelta(days=AT_RISK_INACTIVE_DAYS):
        reasons.append(f"No activity in {AT_RISK_INACTIVE_DAYS}+ days")

    if recall_rate_last10 is not None and recall_rate_last10 < AT_RISK_RECALL_RATE:
        reasons.append(
            f"Recall rate below {int(AT_RISK_RECALL_RATE * 100)}% over the last {AT_RISK_RECALL_WINDOW} reviews"
        )

    if overdue_count > AT_RISK_OVERDUE_COUNT:
        reasons.append(f"{overdue_count} overdue reviews")

    return len(reasons) > 0, reasons
