"""add question_sets table (persisted, reusable review question sets)

Revision ID: b3d9f1a4c6e2
Revises: a1c5e8f2d7b3
Create Date: 2026-07-11

One row = one LLM-generated question set for a card (activity), reused for at
least QUESTION_SET_REUSE review sessions (served shuffled) before regeneration.
items = JSONB [{question, reference_answer}]; reference answers stay server-side.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "b3d9f1a4c6e2"
down_revision = "a1c5e8f2d7b3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "question_sets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("activity_id", sa.Uuid(), nullable=False),
        sa.Column("depth", sa.String(), nullable=False, server_default="main"),
        sa.Column("items", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("times_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["activity_id"], ["activities.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_question_sets_user_id", "question_sets", ["user_id"])
    op.create_index("ix_question_sets_activity_id", "question_sets", ["activity_id"])
    # Block the Supabase PostgREST/anon-key path; the backend connects as the
    # table owner (postgres) and bypasses RLS. Same posture as every other table.
    op.execute("ALTER TABLE question_sets ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.drop_index("ix_question_sets_activity_id", table_name="question_sets")
    op.drop_index("ix_question_sets_user_id", table_name="question_sets")
    op.drop_table("question_sets")
