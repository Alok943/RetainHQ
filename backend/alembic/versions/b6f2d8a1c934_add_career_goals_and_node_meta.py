"""Add career_goals + node_meta tables (Career Coach Phase 2 — Goal, Tree & Topic Mapping)

SPEC-career-coach-phase2.md §2. career_goals is the user's active career
target (one active goal per user, DB-enforced via a partial unique index).
node_meta is a sidecar to roadmap_nodes carrying career-tree-specific fields
(priority/effort/subject/stable_key) — the shared catalog table stays
untouched.

RLS enabled with no policies (deny-all for PostgREST/anon), same convention
as every table since f8a3b5c2d9e1 — the backend connects as table owner and
bypasses RLS.

§7 cascade check (done as part of this migration, not a fix): confirmed
`learning_events.node_id`'s FK (migration a5e9c3d7f102) carries no
`ondelete="CASCADE"` — it defaults to NO ACTION, so Postgres will reject a
raw DELETE of a referenced roadmap_nodes row instead of silently cascading
away the immutable event log. The soft-detach node-delete flow (phase 2 §7)
must null `learning_events.node_id` before deleting the RoadmapNode row.

Revision ID: b6f2d8a1c934
Revises: a5e9c3d7f102
Create Date: 2026-07-19
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b6f2d8a1c934"
down_revision: Union[str, Sequence[str], None] = "a5e9c3d7f102"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "career_goals",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role_key", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("roadmap_id", sa.Uuid(), sa.ForeignKey("roadmaps.id"), nullable=True),
        sa.Column("template_version", sa.String(), nullable=True),
        sa.Column("sprint_node_id", sa.Uuid(), sa.ForeignKey("roadmap_nodes.id"), nullable=True),
        sa.Column("sprint_until", sa.Date(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("status = ANY (ARRAY['active','archived']::text[])", name="career_goals_status_check"),
    )
    op.create_index("ix_career_goals_user_id", "career_goals", ["user_id"])
    op.create_index("ix_career_goals_roadmap_id", "career_goals", ["roadmap_id"])
    op.create_index(
        "uq_career_goal_one_active", "career_goals", ["user_id"],
        unique=True, postgresql_where=sa.text("status = 'active'"),
    )
    op.execute("ALTER TABLE career_goals ENABLE ROW LEVEL SECURITY")

    op.create_table(
        "node_meta",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("node_id", sa.Uuid(), sa.ForeignKey("roadmap_nodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stable_key", sa.String(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("est_effort_min", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("subject", sa.String(), nullable=False),
        sa.Column("review_policy", sa.String(), nullable=False, server_default="default"),
        sa.Column("user_edited", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("node_id", name="uq_node_meta_node"),
        sa.CheckConstraint("priority >= 1 AND priority <= 5", name="node_meta_priority_check"),
        sa.CheckConstraint("est_effort_min > 0", name="node_meta_effort_check"),
    )
    op.create_index("ix_node_meta_node_id", "node_meta", ["node_id"])
    op.create_index("ix_node_meta_stable_key", "node_meta", ["stable_key"])
    op.execute("ALTER TABLE node_meta ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.execute("ALTER TABLE node_meta DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_node_meta_stable_key", table_name="node_meta")
    op.drop_index("ix_node_meta_node_id", table_name="node_meta")
    op.drop_table("node_meta")

    op.execute("ALTER TABLE career_goals DISABLE ROW LEVEL SECURITY")
    op.drop_index("uq_career_goal_one_active", table_name="career_goals")
    op.drop_index("ix_career_goals_roadmap_id", table_name="career_goals")
    op.drop_index("ix_career_goals_user_id", table_name="career_goals")
    op.drop_table("career_goals")
