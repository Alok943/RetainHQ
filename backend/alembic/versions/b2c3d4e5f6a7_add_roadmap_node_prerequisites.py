"""Add roadmap_node_prerequisites (dependency graph)

Directed prerequisite edges between roadmap nodes: a row means `node_id` requires
`prerequisite_node_id` first. Both FK -> roadmap_nodes.id ON DELETE CASCADE, so a
node removal cleans up its edges. Unique(node_id, prerequisite_node_id) keeps edges
idempotent. This is the structural half of the knowledge-graph / "why am I stuck"
diagnosis; edges are populated by the seed_*_prereqs.py scripts.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'roadmap_node_prerequisites',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('node_id', sa.Uuid(), nullable=False),
        sa.Column('prerequisite_node_id', sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(['node_id'], ['roadmap_nodes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['prerequisite_node_id'], ['roadmap_nodes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('node_id', 'prerequisite_node_id', name='uq_node_prereq'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('roadmap_node_prerequisites')
