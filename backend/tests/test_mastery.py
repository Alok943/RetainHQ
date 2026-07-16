"""Golden-case unit tests for services/mastery.py — pure functions, no DB."""
from datetime import datetime, timedelta

from app.services.mastery import (
    at_risk_flag,
    class_cell_status,
    compute_node_status,
    find_root_cause,
)


# ---------------------------------------------------------------------------
# compute_node_status
# ---------------------------------------------------------------------------

def test_untouched_no_test_no_review():
    assert compute_node_status(0, 0, 0, [], None) == "untouched"


def test_untouched_single_test_result_no_review():
    # 1 test result is below MIN_TEST_RESULTS, and no review history to fall
    # back on -> honest floor, not weak/strong.
    assert compute_node_status(1, 0, 0, [], None) == "untouched"


def test_untouched_single_review_no_test():
    # Vice-versa case: no test results, only 1 review entry.
    assert compute_node_status(0, 0, 0, [True], None) == "untouched"


def test_weak_via_test_evidence():
    assert compute_node_status(1, 3, 0, [], None) == "weak"


def test_developing_via_test_evidence():
    assert compute_node_status(3, 2, 0, [], None) == "developing"  # 0.6 accuracy


def test_strong_via_test_evidence():
    assert compute_node_status(9, 1, 0, [], None) == "strong"  # 0.9 accuracy


def test_test_accuracy_boundary_exactly_weak_max_is_developing():
    # accuracy == 0.5 -> not < WEAK_ACCURACY_MAX, so developing, not weak.
    assert compute_node_status(1, 1, 0, [], None) == "developing"


def test_test_accuracy_boundary_exactly_developing_max_is_strong():
    # accuracy == 0.8 -> not < DEVELOPING_ACCURACY_MAX, so strong.
    assert compute_node_status(4, 1, 0, [], None) == "strong"


def test_test_total_boundary_exactly_min_results_counts_as_test_evidence():
    assert compute_node_status(2, 0, 0, [], None) == "strong"  # accuracy 1.0, total == MIN_TEST_RESULTS


def test_weak_via_review_evidence_only():
    assert compute_node_status(0, 0, 0, [False, False], None) == "weak"


def test_developing_via_review_evidence_recalled_but_low_stability():
    assert compute_node_status(0, 0, 0, [False, True], 3.0) == "developing"


def test_developing_via_review_evidence_recalled_with_null_stability():
    assert compute_node_status(0, 0, 0, [True, True], None) == "developing"


def test_strong_via_review_evidence_recalled_with_high_stability():
    assert compute_node_status(0, 0, 0, [False, True], 10.0) == "strong"


def test_stability_boundary_exactly_weak_threshold_is_strong():
    assert compute_node_status(0, 0, 0, [True, True], 7.0) == "strong"


def test_stability_boundary_just_below_weak_threshold_is_developing():
    assert compute_node_status(0, 0, 0, [True, True], 6.99) == "developing"


def test_single_recent_miss_after_a_hit_is_developing_not_weak():
    assert compute_node_status(0, 0, 0, [True, False], 10.0) == "developing"


def test_test_evidence_overrides_conflicting_review_evidence():
    # Review history alone would read "weak" (two misses), but 10 solid test
    # results say otherwise -- test evidence wins entirely.
    assert compute_node_status(9, 1, 0, [False, False], None) == "strong"


def test_below_min_test_results_falls_back_to_sufficient_review_evidence():
    # A single stray test result shouldn't block a real review history from
    # being used.
    assert compute_node_status(1, 0, 0, [False, False], None) == "weak"


# ---------------------------------------------------------------------------
# class_cell_status
# ---------------------------------------------------------------------------

def test_class_cell_insufficient_data_below_coverage():
    counts = {"untouched": 8, "weak": 2, "developing": 0, "strong": 0}
    assert class_cell_status(counts, total_students=10) == "insufficient_data"


def test_class_cell_insufficient_data_no_students():
    assert class_cell_status({"untouched": 0, "weak": 0, "developing": 0, "strong": 0}, total_students=0) == "insufficient_data"


def test_class_cell_weak_dominant_by_plurality():
    counts = {"untouched": 0, "weak": 6, "developing": 2, "strong": 2}
    assert class_cell_status(counts, total_students=10) == "weak"


def test_class_cell_weak_lean_beats_naive_plurality():
    # developing has the largest raw count, but weighted precedence still
    # tips a meaningful weak share to "weak" rather than naive plurality.
    counts = {"untouched": 0, "weak": 4, "developing": 5, "strong": 1}
    assert class_cell_status(counts, total_students=10) == "weak"


def test_class_cell_strong_dominant():
    counts = {"untouched": 1, "weak": 0, "developing": 1, "strong": 8}
    assert class_cell_status(counts, total_students=10) == "strong"


def test_class_cell_coverage_boundary_exactly_min_is_sufficient():
    # exactly 30% coverage should NOT be insufficient (>= threshold).
    counts = {"untouched": 7, "weak": 3, "developing": 0, "strong": 0}
    assert class_cell_status(counts, total_students=10) == "weak"


# ---------------------------------------------------------------------------
# find_root_cause
# ---------------------------------------------------------------------------

def test_find_root_cause_full_overlap():
    weak_students = {"s1", "s2", "s3"}
    node_status_by_student = {
        "prereq-a": {"s1": "weak", "s2": "weak", "s3": "weak", "s4": "strong"},
    }
    assert find_root_cause("node-x", weak_students, ["prereq-a"], node_status_by_student) == "prereq-a"


def test_find_root_cause_majority_overlap_qualifies():
    weak_students = {"s1", "s2", "s3", "s4"}
    node_status_by_student = {
        "prereq-a": {"s1": "weak", "s2": "weak", "s3": "strong", "s4": "strong"},  # 50% overlap
    }
    assert find_root_cause("node-x", weak_students, ["prereq-a"], node_status_by_student) == "prereq-a"


def test_find_root_cause_below_majority_does_not_qualify():
    weak_students = {"s1", "s2", "s3", "s4"}
    node_status_by_student = {
        "prereq-a": {"s1": "weak", "s2": "strong", "s3": "strong", "s4": "strong"},  # 25% overlap
    }
    assert find_root_cause("node-x", weak_students, ["prereq-a"], node_status_by_student) is None


def test_find_root_cause_picks_strongest_match_among_candidates():
    weak_students = {"s1", "s2", "s3", "s4"}
    node_status_by_student = {
        "prereq-a": {"s1": "weak", "s2": "weak", "s3": "strong", "s4": "strong"},  # 50%
        "prereq-b": {"s1": "weak", "s2": "weak", "s3": "weak", "s4": "strong"},  # 75%
    }
    assert find_root_cause("node-x", weak_students, ["prereq-a", "prereq-b"], node_status_by_student) == "prereq-b"


def test_find_root_cause_no_weak_students_returns_none():
    assert find_root_cause("node-x", set(), ["prereq-a"], {}) is None


def test_find_root_cause_no_prereqs_returns_none():
    assert find_root_cause("node-x", {"s1"}, [], {}) is None


# ---------------------------------------------------------------------------
# at_risk_flag
# ---------------------------------------------------------------------------

def test_at_risk_flag_not_at_risk():
    now = datetime(2026, 7, 16)
    last_active = now - timedelta(days=1)
    at_risk, reasons = at_risk_flag(last_active, now, recall_rate_last10=0.8, overdue_count=3)
    assert at_risk is False
    assert reasons == []


def test_at_risk_flag_no_activity_ever():
    now = datetime(2026, 7, 16)
    at_risk, reasons = at_risk_flag(None, now, recall_rate_last10=None, overdue_count=0)
    assert at_risk is True
    assert len(reasons) == 1


def test_at_risk_flag_inactive_boundary_exactly_7_days():
    now = datetime(2026, 7, 16)
    last_active = now - timedelta(days=7)
    at_risk, reasons = at_risk_flag(last_active, now, recall_rate_last10=None, overdue_count=0)
    assert at_risk is True
    assert "activity" in reasons[0]


def test_at_risk_flag_low_recall_rate():
    now = datetime(2026, 7, 16)
    last_active = now - timedelta(days=1)
    at_risk, reasons = at_risk_flag(last_active, now, recall_rate_last10=0.4, overdue_count=0)
    assert at_risk is True
    assert any("recall" in r.lower() or "Recall" in r for r in reasons)


def test_at_risk_flag_recall_rate_boundary_exactly_half_not_flagged():
    now = datetime(2026, 7, 16)
    last_active = now - timedelta(days=1)
    at_risk, reasons = at_risk_flag(last_active, now, recall_rate_last10=0.5, overdue_count=0)
    assert at_risk is False
    assert reasons == []


def test_at_risk_flag_overdue_count():
    now = datetime(2026, 7, 16)
    last_active = now - timedelta(days=1)
    at_risk, reasons = at_risk_flag(last_active, now, recall_rate_last10=0.9, overdue_count=16)
    assert at_risk is True
    assert any("overdue" in r.lower() for r in reasons)


def test_at_risk_flag_overdue_boundary_exactly_15_not_flagged():
    now = datetime(2026, 7, 16)
    last_active = now - timedelta(days=1)
    at_risk, reasons = at_risk_flag(last_active, now, recall_rate_last10=0.9, overdue_count=15)
    assert at_risk is False
    assert reasons == []


def test_at_risk_flag_multiple_reasons():
    now = datetime(2026, 7, 16)
    at_risk, reasons = at_risk_flag(None, now, recall_rate_last10=0.2, overdue_count=20)
    assert at_risk is True
    assert len(reasons) == 3
