"""hardening constraints and indexes

Revision ID: 73c79267ec74
Revises: b769ae00d904
Create Date: 2026-06-07 14:03:53.175399

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '73c79267ec74'
down_revision: Union[str, Sequence[str], None] = 'b769ae00d904'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Clean up duplicate user_progress rows before creating unique index
    op.execute("""
        DELETE FROM user_progress
        WHERE id IN (
            SELECT id
            FROM (
                SELECT id, ROW_NUMBER() OVER (PARTITION BY user_id, node_id ORDER BY updated_at DESC) as rnum
                FROM user_progress
            ) t
            WHERE t.rnum > 1
        );
    """)

    # UNIQUE index on user_progress
    op.create_index('ix_user_progress_user_id_node_id', 'user_progress', ['user_id', 'node_id'], unique=True)
    # Fast paths for dashboard/due queries
    op.create_index('ix_reviews_user_id_status_scheduled', 'reviews', ['user_id', 'status', 'scheduled_for'])
    # Need sqlalchemy.text for the DESC index
    op.create_index('ix_activities_user_id_created_at', 'activities', ['user_id', sa.text('created_at DESC')])

    # CHECK constraints
    op.create_check_constraint('chk_reviews_status', 'reviews', "status IN ('due', 'completed')")
    op.create_check_constraint('chk_reviews_rating', 'reviews', "rating IN ('easy', 'medium', 'hard') OR rating IS NULL")
    op.create_check_constraint('chk_user_progress_status', 'user_progress', "status IN ('done', 'not_started', 'in_progress')")
    op.create_check_constraint('chk_feedbacks_status', 'feedbacks', "status IN ('new', 'reviewed', 'resolved')")
    op.create_check_constraint('chk_activities_ease_factor', 'activities', "ease_factor >= 1.3")


def downgrade() -> None:
    op.drop_constraint('chk_activities_ease_factor', 'activities', type_='check')
    op.drop_constraint('chk_feedbacks_status', 'feedbacks', type_='check')
    op.drop_constraint('chk_user_progress_status', 'user_progress', type_='check')
    op.drop_constraint('chk_reviews_rating', 'reviews', type_='check')
    op.drop_constraint('chk_reviews_status', 'reviews', type_='check')

    op.drop_index('ix_activities_user_id_created_at', table_name='activities')
    op.drop_index('ix_reviews_user_id_status_scheduled', table_name='reviews')
    op.drop_index('ix_user_progress_user_id_node_id', table_name='user_progress')
