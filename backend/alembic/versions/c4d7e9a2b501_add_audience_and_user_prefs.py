"""Add roadmaps.audience + user_prefs table (school/career platform split).

- roadmaps.audience: 'career' (default, all 20 existing roadmaps) | 'school'.
  GET /api/roadmaps/ filters by the caller's preference so school users never
  see DSA and career users never see Class 9-10 Physics.
- user_prefs: one row per user holding their chosen audience. Server-side so the
  choice survives devices/sign-outs (school kids share devices).
  RLS enabled with no policies (blocks PostgREST anon access; backend connects
  as table owner and bypasses it) — same convention as migration f8a3b5c2d9e1.

Revision ID: c4d7e9a2b501
Revises: f8a3b5c2d9e1
"""
import sqlalchemy as sa
from alembic import op

revision = "c4d7e9a2b501"
down_revision = "f8a3b5c2d9e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "roadmaps",
        sa.Column("audience", sa.String(), nullable=False, server_default="career"),
    )
    op.create_table(
        "user_prefs",
        sa.Column("user_id", sa.Uuid(), primary_key=True),
        sa.Column("audience", sa.String(), nullable=False, server_default="career"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_check_constraint(
        "ck_user_prefs_audience", "user_prefs", "audience IN ('career', 'school')"
    )
    op.create_check_constraint(
        "ck_roadmaps_audience", "roadmaps", "audience IN ('career', 'school')"
    )
    op.execute("ALTER TABLE user_prefs ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.drop_table("user_prefs")
    op.drop_constraint("ck_roadmaps_audience", "roadmaps")
    op.drop_column("roadmaps", "audience")
