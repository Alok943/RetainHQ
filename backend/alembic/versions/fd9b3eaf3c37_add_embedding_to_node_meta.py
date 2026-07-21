"""add_embedding_to_node_meta

Revision ID: fd9b3eaf3c37
Revises: b6f2d8a1c934
Create Date: 2026-07-20 20:29:43.095909

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'fd9b3eaf3c37'
down_revision: Union[str, Sequence[str], None] = 'b6f2d8a1c934'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('node_meta', sa.Column('embedding', postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('node_meta', 'embedding')
