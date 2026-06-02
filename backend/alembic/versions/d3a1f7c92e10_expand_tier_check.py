"""expand roadmap_nodes tier check to allow difficulty labels

Revision ID: d3a1f7c92e10
Revises: b72bc0cf122c
Create Date: 2026-06-02

Adds 'easy', 'medium', 'hard' to the allowed values for roadmap_nodes.tier
(alongside the existing 't1', 't2', 't3', 'dsa') so DSA roadmaps can use
difficulty-based tiers.
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "d3a1f7c92e10"
down_revision = "b72bc0cf122c"
branch_labels = None
depends_on = None

_OLD = "ARRAY['t1','t2','t3','dsa']"
_NEW = "ARRAY['t1','t2','t3','dsa','easy','medium','hard']"


def upgrade() -> None:
    op.drop_constraint("roadmap_nodes_tier_check", "roadmap_nodes", type_="check")
    op.create_check_constraint(
        "roadmap_nodes_tier_check",
        "roadmap_nodes",
        f"(tier)::text = ANY ({_NEW}::text[])",
    )


def downgrade() -> None:
    op.drop_constraint("roadmap_nodes_tier_check", "roadmap_nodes", type_="check")
    op.create_check_constraint(
        "roadmap_nodes_tier_check",
        "roadmap_nodes",
        f"(tier)::text = ANY ({_OLD}::text[])",
    )
