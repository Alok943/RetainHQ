"""Block TRUNCATE on user-data tables (incident: 2026-07-26 catalog re-import wipe)

On 2026-07-26 every user's `activities` and `reviews` rows vanished. The cause was
not a migration and not a DELETE: `pg_stat_user_tables` showed n_live_tup=0 with
n_tup_del still at its historical 7/8, which only TRUNCATE produces (TRUNCATE
empties a table without incrementing the delete counter).

The blast radius was exactly the transitive FK closure of `TRUNCATE problems CASCADE`:

    problems ─┬─► problem_concepts
              └─► concept_cards ─► activities ─┬─► reviews
                                               └─► question_sets

`activities.concept_card_id` (added days earlier by 37714df921de) is what welded
irreplaceable user data onto a bulk-rebuildable content catalog. Its ON DELETE is
NO ACTION, which is why this looked safe — but TRUNCATE ... CASCADE ignores
referential actions entirely and empties every referencing table regardless.

Dropping that one FK would not fix the class of bug: `activities.node_id` and
`user_progress.node_id` are the same kind of bridge from `roadmap_nodes`, and the
~32 roadmap seed scripts all rewrite content tables. So the guard goes on the
user-data side instead, where it holds no matter which content table someone
truncates next.

A BEFORE TRUNCATE statement trigger fires on cascaded truncates too, and raising
inside it aborts the whole statement — so `TRUNCATE problems CASCADE` now fails
loudly instead of silently draining user history. Nothing in the codebase
truncates these tables (seed_classroom_demo.py and every seed script use scoped
DELETEs), so this blocks only accidents.

To intentionally truncate one of these tables, drop its trigger in an explicit
migration — the deliberate step is the point.

Revision ID: a9d4f7c2e618
Revises: 37714df921df
Create Date: 2026-07-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a9d4f7c2e618'
down_revision: Union[str, Sequence[str], None] = '37714df921df'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Tables holding per-user history that cannot be regenerated from content files.
# Every one of these is reachable by a CASCADE from a content table.
GUARDED_TABLES = (
    'activities',
    'reviews',
    'question_sets',
    'user_progress',
    'learning_events',
    'node_mastery',
    'test_attempts',
    'metric_events',
    'career_goals',
    'user_prefs',
)


def upgrade() -> None:
    op.execute("""
        CREATE OR REPLACE FUNCTION forbid_truncate_user_data()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RAISE EXCEPTION
                'TRUNCATE is blocked on %.% — it holds irreplaceable user history',
                TG_TABLE_SCHEMA, TG_TABLE_NAME
                USING HINT = 'This fires on cascaded truncates too. Use a scoped DELETE, '
                             'or drop this table''s no_truncate_<table> trigger in an '
                             'explicit migration if you really mean to empty it.';
        END;
        $$;
    """)

    for table in GUARDED_TABLES:
        op.execute(f"""
            CREATE TRIGGER no_truncate_{table}
            BEFORE TRUNCATE ON {table}
            FOR EACH STATEMENT
            EXECUTE FUNCTION forbid_truncate_user_data();
        """)


def downgrade() -> None:
    for table in GUARDED_TABLES:
        op.execute(f"DROP TRIGGER IF EXISTS no_truncate_{table} ON {table};")
    op.execute("DROP FUNCTION IF EXISTS forbid_truncate_user_data();")
