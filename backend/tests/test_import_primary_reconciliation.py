"""The importer must leave at most one role='primary' row per problem.

Both cases below actually reached production in the 2026-07-30 v1.2 merge and had
to be repaired by hand — the importer upserts on (problem_id, node_id), which
never visits the row at the OLD node_id when a problem's primary moves or
disappears. Pinned here so a re-run can't recreate them.

Pure-function tests: no DB, no fixture files. The reconciliation logic is
extracted precisely so it's checkable without standing up the whole import.
"""
import uuid

from scripts.import_leetcode_catalog import plan_stale_primary_cleanup

NODE_A = uuid.uuid4()  # where the primary used to be
NODE_B = uuid.uuid4()  # where the mapping now puts it
NODE_C = uuid.uuid4()  # an unrelated supporting concept


def test_primary_moved_to_another_node_deletes_the_old_one():
    """The 311-row bug: primary moves A -> B, both end up role='primary'."""
    to_delete, to_demote = plan_stale_primary_cleanup(
        existing_roles={NODE_A: "primary"},
        intended_primary_node_id=NODE_B,
        intended_secondary={},
    )
    assert to_delete == {NODE_A}
    assert to_demote == {}


def test_primary_became_out_of_scope_deletes_the_stale_row():
    """The 34-row bug: mapping resolves to out_of_scope/scaffold, so no new
    primary is written at all — and nothing ever revisits the old row."""
    to_delete, to_demote = plan_stale_primary_cleanup(
        existing_roles={NODE_A: "primary"},
        intended_primary_node_id=None,
        intended_secondary={},
    )
    assert to_delete == {NODE_A}
    assert to_demote == {}


def test_old_primary_still_listed_as_supporting_is_demoted_not_deleted():
    """Losing primary status is not the same as losing the mapping entirely."""
    to_delete, to_demote = plan_stale_primary_cleanup(
        existing_roles={NODE_A: "primary"},
        intended_primary_node_id=NODE_B,
        intended_secondary={NODE_A: "supporting"},
    )
    assert to_delete == set()
    assert to_demote == {NODE_A: "supporting"}


def test_unchanged_primary_is_left_alone():
    to_delete, to_demote = plan_stale_primary_cleanup(
        existing_roles={NODE_A: "primary"},
        intended_primary_node_id=NODE_A,
        intended_secondary={},
    )
    assert to_delete == set()
    assert to_demote == {}


def test_supporting_rows_are_never_touched():
    """Scoped to `primary` on purpose — a supporting row the mapping no longer
    lists is not an integrity violation, and deleting on absence would discard
    curation from earlier mapping versions."""
    to_delete, to_demote = plan_stale_primary_cleanup(
        existing_roles={NODE_A: "primary", NODE_C: "supporting"},
        intended_primary_node_id=NODE_A,
        intended_secondary={},  # NODE_C dropped from the file
    )
    assert to_delete == set()
    assert to_demote == {}


def test_alternative_role_is_preserved_on_demotion():
    to_delete, to_demote = plan_stale_primary_cleanup(
        existing_roles={NODE_A: "primary"},
        intended_primary_node_id=NODE_B,
        intended_secondary={NODE_A: "alternative"},
    )
    assert to_demote == {NODE_A: "alternative"}


def test_no_existing_rows_is_a_no_op():
    assert plan_stale_primary_cleanup({}, NODE_B, {}) == (set(), {})
