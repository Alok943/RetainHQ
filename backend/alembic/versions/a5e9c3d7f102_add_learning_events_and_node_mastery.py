"""Add learning_events + node_mastery tables (Career Coach Phase 1 — Evidence Spine)

SPEC-career-coach-phase1.md §2. learning_events is an immutable append-only
event log — every mastery-affecting signal, across producers, lands here
first. node_mastery is a derived cache (services/evidence.py), safe to
truncate and rebuild from learning_events alone.

RLS enabled with no policies (deny-all for PostgREST/anon), same convention
as every table since f8a3b5c2d9e1 — the backend connects as table owner and
bypasses RLS.

Revision ID: a5e9c3d7f102
Revises: 431279836d74
Create Date: 2026-07-19
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "a5e9c3d7f102"
down_revision: Union[str, Sequence[str], None] = "431279836d74"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Mirrors app.services.evidence_weights — kept as a local literal (not
# imported) so this migration stays reproducible even if the app-side
# enumeration changes later; a widened enum needs its own CHECK-altering
# migration (see d3a1f7c92e10 for that pattern).
_EVENT_TYPE_ARRAY = (
    "ARRAY['RECALL_GRADED','PROBLEM_SOLVED','ARTIFACT_BUILT',"
    "'CONCEPT_EXPLAINED','CONTENT_CONSUMED','TIME_BLOCK']"
)
_TRUST_TIER_ARRAY = (
    "ARRAY['T1_verified_external','T2_verified_internal','T3_observed','T4_claimed']"
)


def upgrade() -> None:
    op.create_table(
        "learning_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("trust_tier", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("node_id", sa.Uuid(), sa.ForeignKey("roadmap_nodes.id"), nullable=True),
        sa.Column("duration_min", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("difficulty", sa.String(), nullable=True),
        sa.Column("assistance", sa.String(), nullable=True),
        sa.Column("outcome", sa.String(), nullable=True),
        sa.Column("grade", sa.Float(), nullable=True),
        sa.Column("entity_id", sa.Uuid(), nullable=True),
        sa.Column("payload", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("grade IS NULL OR (grade >= 0 AND grade <= 1)", name="learning_events_grade_check"),
        sa.CheckConstraint("duration_min >= 0", name="learning_events_duration_check"),
        sa.CheckConstraint(
            f"(event_type)::text = ANY ({_EVENT_TYPE_ARRAY}::text[])",
            name="learning_events_event_type_check",
        ),
        sa.CheckConstraint(
            f"(trust_tier)::text = ANY ({_TRUST_TIER_ARRAY}::text[])",
            name="learning_events_trust_tier_check",
        ),
    )
    op.create_index("ix_learning_events_user_id", "learning_events", ["user_id"])
    op.create_index("ix_learning_events_occurred_at", "learning_events", ["occurred_at"])
    op.create_index("ix_learning_events_node_id", "learning_events", ["node_id"])
    op.create_index("ix_learning_events_entity_id", "learning_events", ["entity_id"])
    op.create_index("ix_learning_event_fold_path", "learning_events", ["user_id", "node_id", "occurred_at"])
    op.create_index(
        "uq_learning_event_dedupe", "learning_events", ["user_id", "source", "entity_id"],
        unique=True, postgresql_where=sa.text("entity_id IS NOT NULL"),
    )
    op.execute("ALTER TABLE learning_events ENABLE ROW LEVEL SECURITY")

    op.create_table(
        "node_mastery",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("node_id", sa.Uuid(), sa.ForeignKey("roadmap_nodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("m_learned", sa.Float(), nullable=False, server_default="0"),
        sa.Column("evidence_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_event_at", sa.DateTime(), nullable=True),
        sa.Column("exposure_capped", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("weights_version", sa.String(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("user_id", "node_id", name="uq_node_mastery"),
    )
    op.create_index("ix_node_mastery_user_id", "node_mastery", ["user_id"])
    op.create_index("ix_node_mastery_node_id", "node_mastery", ["node_id"])
    op.execute("ALTER TABLE node_mastery ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.execute("ALTER TABLE node_mastery DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_node_mastery_node_id", table_name="node_mastery")
    op.drop_index("ix_node_mastery_user_id", table_name="node_mastery")
    op.drop_table("node_mastery")

    op.execute("ALTER TABLE learning_events DISABLE ROW LEVEL SECURITY")
    op.drop_index("uq_learning_event_dedupe", table_name="learning_events")
    op.drop_index("ix_learning_event_fold_path", table_name="learning_events")
    op.drop_index("ix_learning_events_entity_id", table_name="learning_events")
    op.drop_index("ix_learning_events_node_id", table_name="learning_events")
    op.drop_index("ix_learning_events_occurred_at", table_name="learning_events")
    op.drop_index("ix_learning_events_user_id", table_name="learning_events")
    op.drop_table("learning_events")
