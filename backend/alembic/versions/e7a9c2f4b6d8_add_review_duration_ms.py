"""Add reviews.duration_ms (HANDOFF-sentry-push-analytics.md C1)

Nullable int on an existing table — no new RLS needed (reviews already has it).
Clamped server-side in routes/reviews.py::complete_review, not here: anything
outside (0, 1_800_000] ms is stored as NULL rather than rejected, since a
garbage client-side timer value shouldn't fail the review completion itself.

Revision ID: e7a9c2f4b6d8
Revises: d4f6a8c1e3b7
Create Date: 2026-07-13
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e7a9c2f4b6d8"
down_revision: Union[str, Sequence[str], None] = "d4f6a8c1e3b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("reviews", sa.Column("duration_ms", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("reviews", "duration_ms")
