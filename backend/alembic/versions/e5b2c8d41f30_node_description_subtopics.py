"""add description and parent_id (subtopics) to roadmap_nodes

Revision ID: e5b2c8d41f30
Revises: d3a1f7c92e10
Create Date: 2026-06-02
"""
from alembic import op
import sqlalchemy as sa

revision = "e5b2c8d41f30"
down_revision = "d3a1f7c92e10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("roadmap_nodes", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("roadmap_nodes", sa.Column("parent_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "roadmap_nodes_parent_id_fkey",
        "roadmap_nodes",
        "roadmap_nodes",
        ["parent_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("roadmap_nodes_parent_id_fkey", "roadmap_nodes", type_="foreignkey")
    op.drop_column("roadmap_nodes", "parent_id")
    op.drop_column("roadmap_nodes", "description")
