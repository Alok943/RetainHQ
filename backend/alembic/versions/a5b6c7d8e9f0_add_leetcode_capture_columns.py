"""add leetcode capture columns

Revision ID: a5b6c7d8e9f0
Revises: a3f8c1d92b47
Create Date: 2026-07-30 21:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a5b6c7d8e9f0'
down_revision: Union[str, Sequence[str], None] = 'a3f8c1d92b47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add problem_id to activities with SET NULL on delete
    op.add_column('activities', sa.Column('problem_id', sa.Uuid(), nullable=True))
    op.create_foreign_key(
        'fk_activities_problem_id_problems',
        'activities', 'problems',
        ['problem_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Add language to activities
    op.add_column('activities', sa.Column('language', sa.String(), nullable=True))
    
    # Add language to problem_attempts
    op.add_column('problem_attempts', sa.Column('language', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('problem_attempts', 'language')
    op.drop_column('activities', 'language')
    op.drop_constraint('fk_activities_problem_id_problems', 'activities', type_='foreignkey')
    op.drop_column('activities', 'problem_id')
