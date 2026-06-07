"""Add source_type to activities

Optional category of the learning resource (problem/lecture/video/book/article/
course/project/other) for filtering and future "retention by source" analytics.
Stored as a plain nullable string (no DB enum) so options can change without a
migration. Surfaced immediately as a badge in the Knowledge Vault.

Revision ID: c9e5f1a2d370
Revises: b8d4e2f3c510
Create Date: 2026-06-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9e5f1a2d370'
down_revision: Union[str, Sequence[str], None] = 'b8d4e2f3c510'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('activities', sa.Column('source_type', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('activities', 'source_type')
