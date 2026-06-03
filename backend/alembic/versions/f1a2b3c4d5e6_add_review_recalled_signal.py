"""Add objective recall signal to reviews

Captures whether the user actually reconstructed the answer (got-it / missed-it),
stored distinctly from the subjective easy/medium/hard rating. See design doc
§5.2 / §6 — two distinct signals: objective verdict vs. felt difficulty.

Revision ID: f1a2b3c4d5e6
Revises: e5b2c8d41f30
Create Date: 2026-06-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = 'e5b2c8d41f30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('reviews', sa.Column('recalled', sa.Boolean(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('reviews', 'recalled')
