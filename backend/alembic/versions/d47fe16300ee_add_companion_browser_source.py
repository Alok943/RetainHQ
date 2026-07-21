"""add_companion_browser_source

Revision ID: d47fe16300ee
Revises: fd9b3eaf3c37
Create Date: 2026-07-20 21:17:51.163919

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd47fe16300ee'
down_revision: Union[str, Sequence[str], None] = 'fd9b3eaf3c37'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_OLD = (
    "ARRAY['leetcode','retainhq_review','retainhq_coach','github',"
    "'manual','companion_desktop','companion_android']"
)
_NEW = (
    "ARRAY['leetcode','retainhq_review','retainhq_coach','github',"
    "'manual','companion_desktop','companion_android','companion_browser']"
)

def upgrade() -> None:
    # Drop if exists (in case it was manually added or we are re-running)
    op.execute("ALTER TABLE learning_events DROP CONSTRAINT IF EXISTS learning_events_source_check")
    op.create_check_constraint(
        "learning_events_source_check",
        "learning_events",
        f"(source)::text = ANY ({_NEW}::text[])",
    )


def downgrade() -> None:
    op.execute("ALTER TABLE learning_events DROP CONSTRAINT IF EXISTS learning_events_source_check")
    # Restore the previous constraint
    op.create_check_constraint(
        "learning_events_source_check",
        "learning_events",
        f"(source)::text = ANY ({_OLD}::text[])",
    )
