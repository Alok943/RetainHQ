"""add problem_aliases

Lets a second site's slug resolve to an EXISTING catalog problem instead of
duplicating the catalog under a new `source`.

Concretely (D-071): NeetCode's problems are LeetCode's problems re-slugged —
`two-integer-sum` is Two Sum, `duplicate-integer` is Contains Duplicate — so a
solve on neetcode.io is evidence about a problem this catalog already holds,
already mapped to a roadmap node by the curated LeetCode mapping pass. An alias
row makes that identity explicit and lets NeetCode inherit all of it.

Deliberately generic (`source` + `alias_slug`), not neetcode-specific: the next
site to add is the same shape, and a `neetcode_slug` column would have to be
re-invented for it.

Revision ID: c2d4f6a8b013
Revises: b1c3e5a7d902
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'c2d4f6a8b013'
down_revision: Union[str, Sequence[str], None] = 'b1c3e5a7d902'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "problem_aliases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("problem_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("problems.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("alias_slug", sa.String(), nullable=False),
        # How this identity was established — 'slug_identical', 'title_match',
        # 'override'. Kept because a wrong alias silently attributes one
        # problem's evidence to another, and the first question then is which
        # rule produced it.
        sa.Column("resolved_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        # One meaning per (site, slug). Without this a re-run of the sync could
        # leave two rows pointing a single NeetCode slug at two problems, and
        # the lookup would pick whichever came back first.
        sa.UniqueConstraint("source", "alias_slug", name="uq_problem_alias_source_slug"),
    )
    op.create_index("ix_problem_aliases_problem_id", "problem_aliases", ["problem_id"])
    # Shared catalog data, no user_id — but RLS is enabled anyway, per the repo
    # convention: the backend connects as owner and bypasses it, while Supabase's
    # anon/PostgREST path stays blocked by default.
    op.execute("ALTER TABLE problem_aliases ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.execute("ALTER TABLE problem_aliases DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_problem_aliases_problem_id", table_name="problem_aliases")
    op.drop_table("problem_aliases")
