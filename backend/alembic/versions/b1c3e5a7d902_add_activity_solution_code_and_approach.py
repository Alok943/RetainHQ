"""add activity solution_code and inferred approach

Revision ID: b1c3e5a7d902
Revises: a5b6c7d8e9f0
Create Date: 2026-08-02 00:00:00.000000

Captures the user's own submitted solution on a LeetCode-mode card, plus the
approach inferred from it. The approach is INFERENCE, so it is stored beside
`node_id` and never in it — `node_id` remains the catalog's `role='primary'`
concept and stays the sole mastery-routing key (SPEC-leetcode-retention.md
§3.2.-1 defers approach-based mastery routing pending shadow validation).

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b1c3e5a7d902'
down_revision: Union[str, Sequence[str], None] = 'a5b6c7d8e9f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # The user's own solution, as pasted. Immutable per card for the same reason
    # `language` is (IMPLEMENTATION-leetcode-log-capture.md §3): the card's
    # questions are written against it, so rewriting it would orphan them.
    op.add_column('activities', sa.Column('solution_code', sa.Text(), nullable=True))

    # The approach inferred FROM that code, resolved against the closed roadmap
    # vocabulary. SET NULL, not CASCADE: a node delete must never take a user's
    # card with it (D-039, same rule as activities.problem_id).
    op.add_column('activities', sa.Column('approach_node_id', sa.Uuid(), nullable=True))
    op.create_foreign_key(
        'fk_activities_approach_node_id_roadmap_nodes',
        'activities', 'roadmap_nodes',
        ['approach_node_id'], ['id'],
        ondelete='SET NULL',
    )

    # 'high' | 'medium' | 'low' — ordinal band, never a raw float
    # (SPEC-leetcode-retention.md §3.2: the float is not a calibrated probability).
    op.add_column('activities', sa.Column('approach_confidence', sa.String(), nullable=True))

    # {"facts": [...], "model": "...", "version": "v1"} — the concrete observations
    # about what this code actually does, which is what makes the generated
    # questions specific to the user's implementation instead of the canonical one.
    op.add_column(
        'activities',
        sa.Column('approach_summary', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('activities', 'approach_summary')
    op.drop_column('activities', 'approach_confidence')
    op.drop_constraint(
        'fk_activities_approach_node_id_roadmap_nodes', 'activities', type_='foreignkey'
    )
    op.drop_column('activities', 'approach_node_id')
    op.drop_column('activities', 'solution_code')
