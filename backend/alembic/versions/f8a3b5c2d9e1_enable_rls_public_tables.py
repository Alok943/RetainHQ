"""Enable RLS on all public tables (Supabase security advisory)

The frontend never queries Postgres directly, but Supabase's auto-generated
REST API (PostgREST) exposes the public schema at the project URL, and the
anon key ships in the JS bundle. The anon/authenticated roles hold full table
grants by default, so with RLS disabled anyone could read/edit/delete these
tables through PostgREST, bypassing the FastAPI gateway entirely.

Fix: ENABLE ROW LEVEL SECURITY with ZERO policies = deny-all for PostgREST
callers. The backend is unaffected: it connects as `postgres`, which owns
every table, and table owners bypass RLS (we deliberately do NOT use FORCE).
roadmaps/roadmap_nodes/user_progress already had RLS enabled (and the backend
reads/writes them fine in prod — live proof of the owner bypass); this brings
the remaining seven tables in line.

Convention going forward: every new table's migration must include
ENABLE ROW LEVEL SECURITY.

Revision ID: f8a3b5c2d9e1
Revises: e7f2a4c9b1d5
Create Date: 2026-07-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f8a3b5c2d9e1'
down_revision: Union[str, Sequence[str], None] = 'e7f2a4c9b1d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Tables verified RLS-disabled on 2026-07-02 (pg_tables.rowsecurity = false).
TABLES = (
    'activities',
    'reviews',
    'tracks',
    'feedbacks',
    'reminder_log',
    'roadmap_node_prerequisites',
    'alembic_version',
)


def upgrade() -> None:
    for table in TABLES:
        op.execute(f'ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY;')


def downgrade() -> None:
    for table in TABLES:
        op.execute(f'ALTER TABLE public.{table} DISABLE ROW LEVEL SECURITY;')
