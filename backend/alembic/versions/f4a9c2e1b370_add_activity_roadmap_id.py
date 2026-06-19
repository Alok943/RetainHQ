"""Add roadmap_id to activities

Optional link from a logged activity to the roadmap it belongs to. Lets the Log
form offer a roadmap picker (in-progress roadmaps surfaced first to cut search
friction) and lets the Vault/analytics group captures by roadmap later. Nullable
FK -> roadmaps.id with ON DELETE SET NULL: roadmaps are seeded/static, and a
removal should never orphan or delete a user's activity.

Revision ID: f4a9c2e1b370
Revises: d4e8a1b2c903
Create Date: 2026-06-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f4a9c2e1b370'
down_revision: Union[str, Sequence[str], None] = 'd4e8a1b2c903'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('activities', sa.Column('roadmap_id', sa.Uuid(), nullable=True))
    op.create_foreign_key(
        'fk_activities_roadmap_id',
        'activities',
        'roadmaps',
        ['roadmap_id'],
        ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_activities_roadmap_id', 'activities', type_='foreignkey')
    op.drop_column('activities', 'roadmap_id')
