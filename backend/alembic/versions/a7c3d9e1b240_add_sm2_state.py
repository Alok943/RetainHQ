"""Add SM-2 memory state to activities

Each activity is one spaced-repetition "card" carrying its own SM-2 state:
ease_factor (default 2.5), repetitions (default 1), interval_days (default 1).
Server defaults backfill existing rows into a sane starting state. See
services/scheduler.py for the algorithm.

Revision ID: a7c3d9e1b240
Revises: f1a2b3c4d5e6
Create Date: 2026-06-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7c3d9e1b240'
down_revision: Union[str, Sequence[str], None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('activities', sa.Column('ease_factor', sa.Float(), nullable=False, server_default='2.5'))
    op.add_column('activities', sa.Column('repetitions', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('activities', sa.Column('interval_days', sa.Integer(), nullable=False, server_default='1'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('activities', 'interval_days')
    op.drop_column('activities', 'repetitions')
    op.drop_column('activities', 'ease_factor')
