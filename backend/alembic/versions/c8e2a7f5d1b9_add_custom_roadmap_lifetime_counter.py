"""user_prefs.custom_roadmaps_created — lifetime counter for syllabus commits

The 3-per-user LIFETIME cap on personal roadmaps can't be enforced by counting
roadmaps rows (deletion would refund the quota), so commits increment a counter
that never decrements. Backfills from existing personal roadmaps; users who
created roadmaps before having a user_prefs row get their row created here.

Revision ID: c8e2a7f5d1b9
Revises: b3d9f1a4c6e2
Create Date: 2026-07-12
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c8e2a7f5d1b9"
down_revision: Union[str, Sequence[str], None] = "b3d9f1a4c6e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_prefs",
        sa.Column("custom_roadmaps_created", sa.Integer(), nullable=False, server_default="0"),
    )
    # Backfill: count existing personal roadmaps per user. Creators without a
    # user_prefs row get one (audience keeps its column default).
    op.execute(
        """
        INSERT INTO user_prefs (user_id, audience, created_at, updated_at)
        SELECT DISTINCT r.user_id, 'career', now(), now()
        FROM roadmaps r
        WHERE r.user_id IS NOT NULL
          AND NOT EXISTS (SELECT 1 FROM user_prefs p WHERE p.user_id = r.user_id)
        """
    )
    op.execute(
        """
        UPDATE user_prefs p
        SET custom_roadmaps_created = sub.n
        FROM (
            SELECT user_id, COUNT(*) AS n
            FROM roadmaps
            WHERE user_id IS NOT NULL
            GROUP BY user_id
        ) sub
        WHERE p.user_id = sub.user_id
        """
    )


def downgrade() -> None:
    op.drop_column("user_prefs", "custom_roadmaps_created")
