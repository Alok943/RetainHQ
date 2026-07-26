"""Add career_goals.daily_minutes (Career Coach Phase 3 scheduler)

The scheduler (services/planner.py) needs a per-goal daily study budget to
size a plan against. `career_goals` already has RLS enabled with no policies
(D-038 posture — the backend connects as `postgres` and bypasses it), so no
new RLS statement is needed for a column add.

Revision ID: b7b1755c4d22
Revises: a9d4f7c2e618
Create Date: 2026-07-26 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b7b1755c4d22'
down_revision: Union[str, Sequence[str], None] = 'a9d4f7c2e618'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('career_goals', sa.Column(
        'daily_minutes', sa.Integer(), nullable=False, server_default=sa.text('60')))
    op.create_check_constraint(
        'ck_career_goals_daily_minutes', 'career_goals',
        'daily_minutes BETWEEN 30 AND 240')


def downgrade() -> None:
    op.drop_constraint('ck_career_goals_daily_minutes', 'career_goals', type_='check')
    op.drop_column('career_goals', 'daily_minutes')
