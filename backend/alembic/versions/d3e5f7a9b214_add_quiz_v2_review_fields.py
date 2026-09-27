"""Add Quiz v2 (Quick mode) fields to reviews + a topic-key cache to activities

docs/IMPLEMENTATION-quiz-capture-v2.md Step 5.5. All columns are nullable and
additive — old rows and old clients keep working unchanged; `/complete` accepts
these fields optionally.

`reviews` gains: `mode` ('quick'|'typed'), `question_format` ('mcq'|'typed'|
'free'), `question_tier` ('tier1'|'tier2'|'tier3'), `question_source`
('lesson'|'question_set'|'none'), `question_served` (a stable id of the
specific item served, e.g. "<roadmap>/<slug>#<index>" — lets a later session
avoid repeating it), `hint_used` (bool), `think_ms` (int, reveal-to-answer
latency).

`activities` gains a DERIVED CACHE for the topic-key embedding fallback
(Step 5.4): `topic_node_cache_id` (best-guess roadmap_node match for a card
with no node_id/roadmap_id/problem mapping) + `topic_cache_version` (bumped
whenever the matching logic/thresholds change, so stale cache entries can be
detected and recomputed instead of trusted forever). This is a cache, never a
fact: nothing here is ever promoted to `activities.node_id` automatically — an
architecture law from docs/ARCHITECTURE-learning-system.md §0 ("never overwrite
anything derived from facts from an inference"). Two plain nullable columns
(not a separate cache table) because this is a 1:1 derived value per activity,
matching the existing `approach_node_id`/`approach_confidence`/`approach_summary`
precedent on the same table for the exact same "cached inference, never
authoritative" shape.

Revision ID: d3e5f7a9b214
Revises: c2d4f6a8b013
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'd3e5f7a9b214'
down_revision: Union[str, Sequence[str], None] = 'c2d4f6a8b013'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('reviews', sa.Column('mode', sa.String(), nullable=True))
    op.add_column('reviews', sa.Column('question_format', sa.String(), nullable=True))
    op.add_column('reviews', sa.Column('question_tier', sa.String(), nullable=True))
    op.add_column('reviews', sa.Column('question_source', sa.String(), nullable=True))
    op.add_column('reviews', sa.Column('question_served', sa.String(), nullable=True))
    op.add_column('reviews', sa.Column('hint_used', sa.Boolean(), nullable=True))
    op.add_column('reviews', sa.Column('think_ms', sa.Integer(), nullable=True))

    op.add_column(
        'activities',
        sa.Column('topic_node_cache_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('roadmap_nodes.id', ondelete='SET NULL'), nullable=True),
    )
    op.add_column('activities', sa.Column('topic_cache_version', sa.Integer(), nullable=True))
    op.create_index('ix_activities_topic_node_cache_id', 'activities', ['topic_node_cache_id'])


def downgrade() -> None:
    op.drop_index('ix_activities_topic_node_cache_id', table_name='activities')
    op.drop_column('activities', 'topic_cache_version')
    op.drop_column('activities', 'topic_node_cache_id')

    op.drop_column('reviews', 'think_ms')
    op.drop_column('reviews', 'hint_used')
    op.drop_column('reviews', 'question_served')
    op.drop_column('reviews', 'question_source')
    op.drop_column('reviews', 'question_tier')
    op.drop_column('reviews', 'question_format')
    op.drop_column('reviews', 'mode')
