"""Add push_subscriptions table (Web Push — HANDOFF-sentry-push-analytics.md B3)

One row per browser/device subscription. `endpoint` unique = the natural
upsert key (services/push.py's INSERT ... ON CONFLICT (endpoint) DO UPDATE).
`user_id` indexed for the reminder fan-out's per-user subscription lookup.

RLS enabled with no policies (deny-all for PostgREST/anon), same convention
as every table since migration f8a3b5c2d9e1 — the backend connects as table
owner and bypasses RLS.

Revision ID: d4f6a8c1e3b7
Revises: c8e2a7f5d1b9
Create Date: 2026-07-13
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d4f6a8c1e3b7"
down_revision: Union[str, Sequence[str], None] = "c8e2a7f5d1b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "push_subscriptions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("endpoint", sa.String(), nullable=False),
        sa.Column("p256dh", sa.String(), nullable=False),
        sa.Column("auth", sa.String(), nullable=False),
        sa.Column("user_agent", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_unique_constraint("uq_push_subscriptions_endpoint", "push_subscriptions", ["endpoint"])
    op.create_index("ix_push_subscriptions_user_id", "push_subscriptions", ["user_id"])
    op.execute("ALTER TABLE push_subscriptions ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.drop_index("ix_push_subscriptions_user_id", table_name="push_subscriptions")
    op.drop_constraint("uq_push_subscriptions_endpoint", "push_subscriptions", type_="unique")
    op.drop_table("push_subscriptions")
