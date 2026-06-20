"""Add FSRS memory state to activities

FSRS (Free Spaced Repetition Scheduler) succeeds SM-2 as the scheduler. Each
activity-card gains two continuous FSRS variables:
  - stability       : days until predicted recall decays to the target retention
  - difficulty_fsrs : FSRS difficulty (1-10), distinct from the existing
                      `difficulty` column (the user's 1-5 self-rating at log time)
Both are nullable with no server default: NULL means "new card with no memory
state yet", which FSRS establishes from the card's first GRADED review. Existing
rows therefore stay NULL and get initialized into FSRS on their next completion.
The legacy SM-2 columns (ease_factor/repetitions/interval_days) are kept.

Revision ID: a1b2c3d4e5f6
Revises: f4a9c2e1b370
Create Date: 2026-06-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f4a9c2e1b370'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('activities', sa.Column('stability', sa.Float(), nullable=True))
    op.add_column('activities', sa.Column('difficulty_fsrs', sa.Float(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('activities', 'difficulty_fsrs')
    op.drop_column('activities', 'stability')
