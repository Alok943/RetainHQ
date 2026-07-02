"""Enforce review-engine invariants with partial unique indexes

Two invariants the code promises but the DB never enforced:

1. One open (status='due') review per activity. scheduler.py documents this and
   complete_review relies on it — if an activity ever carries two due reviews,
   completing both applies FSRS twice (lost update on stability/difficulty) and
   schedules two next reviews, doubling every cycle.
   -> partial unique index on reviews(activity_id) WHERE status='due'.

2. One lesson card per (user, node). The "Add to reviews" dedupe in
   POST /api/activities/ is a SELECT-then-INSERT — two concurrent taps both see
   "no card" and both insert, after which the scalar_one_or_none() check raises
   MultipleResultsFound (a permanent 500 on that lesson).
   -> partial unique index on activities(user_id, node_id) WHERE node_id IS NOT NULL.
   (node_id is only ever set by the lesson path, and the code's dedupe check
   filters on user_id+node_id alone, so the index matches the query exactly.)

Both cleanups keep the OLDEST row (earliest scheduled_for / created_at) and
delete later duplicates; deleting a duplicate activity cascades its reviews.

Revision ID: e7f2a4c9b1d5
Revises: a4b2e9f1c8d3
Create Date: 2026-07-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7f2a4c9b1d5'
down_revision: Union[str, Sequence[str], None] = 'a4b2e9f1c8d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Duplicate lesson cards first: keep the earliest activity per (user, node),
    # delete the rest (their reviews cascade via the activity_id FK).
    op.execute("""
        DELETE FROM activities
        WHERE id IN (
            SELECT id
            FROM (
                SELECT id, ROW_NUMBER() OVER (
                    PARTITION BY user_id, node_id ORDER BY created_at ASC
                ) AS rnum
                FROM activities
                WHERE node_id IS NOT NULL
            ) t
            WHERE t.rnum > 1
        );
    """)

    # Duplicate open reviews: keep the earliest-scheduled due review per activity
    # (preserves the soonest due date), delete the rest.
    op.execute("""
        DELETE FROM reviews
        WHERE id IN (
            SELECT id
            FROM (
                SELECT id, ROW_NUMBER() OVER (
                    PARTITION BY activity_id ORDER BY scheduled_for ASC, created_at ASC
                ) AS rnum
                FROM reviews
                WHERE status = 'due'
            ) t
            WHERE t.rnum > 1
        );
    """)

    op.create_index(
        'uq_reviews_one_open_per_activity',
        'reviews',
        ['activity_id'],
        unique=True,
        postgresql_where=sa.text("status = 'due'"),
    )
    op.create_index(
        'uq_activities_user_node',
        'activities',
        ['user_id', 'node_id'],
        unique=True,
        postgresql_where=sa.text('node_id IS NOT NULL'),
    )


def downgrade() -> None:
    op.drop_index('uq_activities_user_node', table_name='activities')
    op.drop_index('uq_reviews_one_open_per_activity', table_name='reviews')
