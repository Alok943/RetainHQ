"""Attach roadmaps to a career goal (career_goal_roadmaps)

Lets a goal draw its Today plan from the official catalog roadmaps and the user's
own syllabus-built roadmaps, not just its generated career tree. Attaching creates
`node_meta` sidecar rows for the roadmap's nodes (the planner INNER JOINs node_meta
and cannot score a node without subject/priority/effort) — it never copies
`roadmap_nodes`. See docs/IMPLEMENTATION-career-attached-roadmaps.md §2.

Revision ID: c3e8a1f47b92
Revises: b7b1755c4d22
Create Date: 2026-07-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'c3e8a1f47b92'
down_revision: Union[str, Sequence[str], None] = 'b7b1755c4d22'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'career_goal_roadmaps',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('goal_id', sa.Uuid(), nullable=False),
        sa.Column('roadmap_id', sa.Uuid(), nullable=False),
        sa.Column('subject', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('default_priority', sa.Integer(), nullable=False, server_default=sa.text('3')),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['goal_id'], ['career_goals.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['roadmap_id'], ['roadmaps.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('goal_id', 'roadmap_id', name='uq_goal_roadmap'),
    )
    op.create_index('ix_career_goal_roadmaps_goal_id', 'career_goal_roadmaps', ['goal_id'])
    op.create_index('ix_career_goal_roadmaps_roadmap_id', 'career_goal_roadmaps', ['roadmap_id'])

    # Mandatory for every new table (CLAUDE.md): blocks Supabase's PostgREST/anon-key
    # path. The backend connects as owner and bypasses RLS. No policies.
    op.execute("ALTER TABLE career_goal_roadmaps ENABLE ROW LEVEL SECURITY;")


def downgrade() -> None:
    op.drop_index('ix_career_goal_roadmaps_roadmap_id', table_name='career_goal_roadmaps')
    op.drop_index('ix_career_goal_roadmaps_goal_id', table_name='career_goal_roadmaps')
    op.drop_table('career_goal_roadmaps')
