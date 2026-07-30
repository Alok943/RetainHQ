"""Drop orphaned attached-roadmap node_meta sidecars (A1 fix, Q1 option b)

`node_meta` has `UniqueConstraint("node_id")` with no user or goal column, but
the attach-roadmap feature (D-042) wrote `attached.<slug>.%` sidecars into it
per user — the exact bridge that let one user's detach delete rows a second
user's plan depended on (BUGFIX-career-coach-docs-review.md, finding A1).

Verified 2026-07-28 (Supabase MCP) that these sidecars carry zero per-node
information: `subject`/`priority` are the same for every node in an
attachment (both come straight off the `career_goal_roadmaps` row), effort is
a flat constant, and `embedding` is never set on them. So the fix is not a
migration to per-user scoping (that would still leave the shared-state
problem, just narrower) — it's to stop persisting them at all.
`career_goal_roadmaps` becomes the sole source of truth for an attachment's
subject/priority; `/today` synthesizes plan nodes for attached roadmaps from
that row instead of joining `node_meta` (career.py).

This is a DATA cleanup, not a schema change — no column is added or dropped.
148 such rows existed in prod as of 2026-07-28; this deletes exactly the ones
the attach feature is known to have written (its stable_key prefix) and
never a template-tree sidecar, and never one a user has since hand-edited
(`user_edited=True` is preserved even though the code path that used to read
it for attached rows is gone, since a user's edit is real intent regardless
of why the row first existed).

Revision ID: a3f8c1d92b47
Revises: d5f1a7c3e284
Create Date: 2026-07-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'a3f8c1d92b47'
down_revision: Union[str, Sequence[str], None] = 'd5f1a7c3e284'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DELETE FROM node_meta
        WHERE stable_key LIKE 'attached.%'
          AND user_edited = false
    """)


def downgrade() -> None:
    # Data deletion is not reversible — the rows carried no information beyond
    # what career_goal_roadmaps already has, so there is nothing to restore
    # from within this migration. A downgrade that re-creates them would need
    # to re-derive them from career_goal_roadmaps + roadmap_nodes, which is
    # exactly what the application code now does at read time instead.
    pass
