"""add reminder_log

Revision ID: d4e8a1b2c903
Revises: c2f5a9b3d701
Create Date: 2026-06-11 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e8a1b2c903'
down_revision: Union[str, Sequence[str], None] = 'c2f5a9b3d701'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'reminder_log',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('sent_on', sa.Date(), nullable=False),
        sa.Column('due_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'sent_on', name='uq_reminder_user_day'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('reminder_log')
