"""Add metric_events table (HANDOFF-sentry-push-analytics.md C2)

Generic, heterogeneous learning-analytics event store — a JSONB payload keyed
by event_type, rather than a dedicated table per exploratory signal. First
producer: syllabus commit records extraction_edit_delta.

RLS enabled with no policies (deny-all for PostgREST/anon), same convention
as every table since migration f8a3b5c2d9e1 — the backend connects as table
owner and bypasses RLS.

Revision ID: f1b3d5e7a9c0
Revises: e7a9c2f4b6d8
Create Date: 2026-07-13
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "f1b3d5e7a9c0"
down_revision: Union[str, Sequence[str], None] = "e7a9c2f4b6d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "metric_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=True),
        sa.Column("payload", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_metric_events_user_id", "metric_events", ["user_id"])
    op.create_index("ix_metric_events_event_type", "metric_events", ["event_type"])
    op.execute("ALTER TABLE metric_events ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.drop_index("ix_metric_events_event_type", table_name="metric_events")
    op.drop_index("ix_metric_events_user_id", table_name="metric_events")
    op.drop_table("metric_events")
