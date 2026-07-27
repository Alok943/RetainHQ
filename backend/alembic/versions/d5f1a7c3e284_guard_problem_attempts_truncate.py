"""Add problem_attempts to the TRUNCATE guard (D-039 follow-through)

`problem_attempts` holds manual "I solved this" marks — user data — and FKs to
`problems`, a bulk-rebuildable catalog table that gets re-imported wholesale.
That is precisely the bridge that caused the 2026-07-26 wipe: `TRUNCATE problems
CASCADE` ignores referential actions and empties every referencing table, so
without a trigger here a routine catalog re-import silently deletes every mark a
user ever made.

Flagged in IMPLEMENTATION-problem-capture.md §3 and missed in the build.

Revision ID: d5f1a7c3e284
Revises: e2c4a8b1f960
Create Date: 2026-07-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'd5f1a7c3e284'
down_revision: Union[str, Sequence[str], None] = 'e2c4a8b1f960'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # forbid_truncate_user_data() already exists (a9d4f7c2e618); reuse it.
    op.execute("""
        CREATE TRIGGER no_truncate_problem_attempts
        BEFORE TRUNCATE ON problem_attempts
        FOR EACH STATEMENT
        EXECUTE FUNCTION forbid_truncate_user_data();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS no_truncate_problem_attempts ON problem_attempts;")
