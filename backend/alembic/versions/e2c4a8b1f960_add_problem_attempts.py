"""Add problem_attempts (manual LeetCode completion marks)

Manual "I solved this" marks made from the roadmap UI, for when the browser
extension isn't running. Deliberately NOT evidence: never writes a
learning_event and never moves node_mastery — the extension's verified-
submission path is the only writer of those. See
docs/IMPLEMENTATION-problem-capture.md §1/§3.

Note for a future migration (not this one): problem_attempts bridges user
data to problems, a bulk-rebuildable catalog table already reachable by
TRUNCATE CASCADE (see a9d4f7c2e618). It should be added to that migration's
GUARDED_TABLES list so a future `TRUNCATE problems CASCADE` can't silently
take these rows with it — tracked in BACKLOG.md rather than done here, to
keep this migration scoped to the one table it's actually about.

Revision ID: e2c4a8b1f960
Revises: c3e8a1f47b92
Create Date: 2026-07-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'e2c4a8b1f960'
down_revision: Union[str, Sequence[str], None] = 'c3e8a1f47b92'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'problem_attempts',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('problem_id', sa.Uuid(), nullable=False),
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default=sa.text("'solved'")),
        sa.Column('marked_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['problem_id'], ['problems.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'problem_id', name='uq_problem_attempt'),
    )
    op.create_index('ix_problem_attempts_user_id', 'problem_attempts', ['user_id'])
    op.create_index('ix_problem_attempts_problem_id', 'problem_attempts', ['problem_id'])

    # Mandatory for every new table (CLAUDE.md): blocks Supabase's PostgREST/anon-key
    # path. The backend connects as owner and bypasses RLS. No policies.
    op.execute("ALTER TABLE problem_attempts ENABLE ROW LEVEL SECURITY;")


def downgrade() -> None:
    op.drop_index('ix_problem_attempts_problem_id', table_name='problem_attempts')
    op.drop_index('ix_problem_attempts_user_id', table_name='problem_attempts')
    op.drop_table('problem_attempts')
