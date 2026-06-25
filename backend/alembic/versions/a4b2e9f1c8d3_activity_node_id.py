"""activities.node_id — lesson-level link (the content->review bridge)

Adds a nullable FK from activities to roadmap_nodes so a card created from a
lesson ("Add to reviews") knows which lesson it came from. Enables one-card-per-
(user, node) dedup and surfacing the lesson's recall items at review time.

Revision ID: a4b2e9f1c8d3
Revises: a3f1c0d4e7b2
Create Date: 2026-06-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a4b2e9f1c8d3"
down_revision: Union[str, Sequence[str], None] = "a3f1c0d4e7b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("activities", sa.Column("node_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_activities_node_id", "activities", "roadmap_nodes",
        ["node_id"], ["id"], ondelete="SET NULL",
    )
    op.create_index("ix_activities_node_id", "activities", ["node_id"])


def downgrade() -> None:
    op.drop_index("ix_activities_node_id", table_name="activities")
    op.drop_constraint("fk_activities_node_id", "activities", type_="foreignkey")
    op.drop_column("activities", "node_id")
