"""Add roadmaps.user_id — personal (syllabus-upload) roadmaps

NULL = official catalog roadmap (seeded, visible to its audience). Non-NULL =
a personal roadmap created by that user via the syllabus-upload flow — visible
only to its owner. No new table, so no RLS statement needed here (roadmaps
already has RLS enabled since f8a3b5c2d9e1).

Revision ID: a1c5e8f2d7b3
Revises: f2b7d3a9c8e4
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1c5e8f2d7b3"
down_revision: Union[str, Sequence[str], None] = "f2b7d3a9c8e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("roadmaps", sa.Column("user_id", sa.Uuid(), nullable=True))
    op.create_index("ix_roadmaps_user_id", "roadmaps", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_roadmaps_user_id", table_name="roadmaps")
    op.drop_column("roadmaps", "user_id")
