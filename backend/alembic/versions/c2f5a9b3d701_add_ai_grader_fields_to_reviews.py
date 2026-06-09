"""Add LLM grader output fields to reviews

Persists the recall grader's proposal (verdict / machine-recalled / feedback)
alongside the user's own rating+recalled. The gap between `recalled` (self-report)
and `ai_recalled` (machine) is the calibration metric. The verdict is advisory —
the user's signals remain authoritative for SM-2.

Revision ID: c2f5a9b3d701
Revises: 73c79267ec74
Create Date: 2026-06-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2f5a9b3d701'
down_revision: Union[str, Sequence[str], None] = '73c79267ec74'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('reviews', sa.Column('ai_verdict', sa.String(), nullable=True))
    op.add_column('reviews', sa.Column('ai_recalled', sa.Boolean(), nullable=True))
    op.add_column('reviews', sa.Column('ai_feedback', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('reviews', 'ai_feedback')
    op.drop_column('reviews', 'ai_recalled')
    op.drop_column('reviews', 'ai_verdict')
