"""Add SM-2 tracking fields for analytics

Adds denormalized scheduling fields and the persisted quality grade so future
work (streaks, retention score, dashboards, calendar views) doesn't need to
scan review history:
  - activities.last_reviewed_at : timestamp of the most recent completed review
  - activities.next_review_at   : mirrors the open due review's date
  - reviews.quality             : SM-2 quality grade (0-5) for the completed review

All nullable; no backfill needed.

Revision ID: b8d4e2f3c510
Revises: a7c3d9e1b240
Create Date: 2026-06-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8d4e2f3c510'
down_revision: Union[str, Sequence[str], None] = 'a7c3d9e1b240'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('activities', sa.Column('last_reviewed_at', sa.DateTime(), nullable=True))
    op.add_column('activities', sa.Column('next_review_at', sa.DateTime(), nullable=True))
    op.add_column('reviews', sa.Column('quality', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('reviews', 'quality')
    op.drop_column('activities', 'next_review_at')
    op.drop_column('activities', 'last_reviewed_at')
