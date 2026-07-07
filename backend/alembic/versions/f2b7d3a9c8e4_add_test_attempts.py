"""Add test_attempts table (the Tests section — SPEC-test-runtime.md)

Persists one row per completed test session: the roadmap/phase, the score, and
the full per-question results (JSONB — question_id/node_title/type/outcome/
trap/misconception). Content (the question banks) lives client-side under
content/roadmaps/<key>/_test/*.json, same as every lesson; this table only
holds user-state (what they attempted and how it went), which is what the
FSRS bridge and the /weights accuracy aggregate read.

No node_mastery table in v1 — per-node accuracy is computed by scanning a
user's recent test_attempts.results in Python (cheap at pilot scale).

RLS enabled with no policies (deny-all for PostgREST/anon), same convention
as every table since migration f8a3b5c2d9e1 — the backend connects as table
owner and bypasses RLS.

Revision ID: f2b7d3a9c8e4
Revises: c4d7e9a2b501
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "f2b7d3a9c8e4"
down_revision: Union[str, Sequence[str], None] = "c4d7e9a2b501"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "test_attempts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("roadmap_id", sa.Uuid(), sa.ForeignKey("roadmaps.id"), nullable=False),
        sa.Column("phase", sa.String(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("max_score", sa.Integer(), nullable=False),
        sa.Column("results", JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_test_attempts_user_roadmap", "test_attempts", ["user_id", "roadmap_id", "created_at"])
    op.execute("ALTER TABLE test_attempts ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.drop_index("ix_test_attempts_user_roadmap", table_name="test_attempts")
    op.drop_table("test_attempts")
