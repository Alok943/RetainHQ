"""roadmaps.slug — human-readable URL identifier

Adds a nullable, unique `slug` column to roadmaps and backfills the seeded
roadmaps (fixed UUIDs) so existing prod rows get clean URLs without re-seeding.
Routes resolve by slug OR id, so old UUID links keep working.

Revision ID: a3f1c0d4e7b2
Revises: b2c3d4e5f6a7
Create Date: 2026-06-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a3f1c0d4e7b2"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Canonical slug per seeded roadmap (fixed UUIDs from the seed_*.py scripts).
# The three content roadmaps (python-swe, sql, aptitude) MUST match their
# content/ folder keys — the frontend uses the slug as the content key.
SLUGS = {
    "11111111-1111-1111-1111-111111111111": "python-swe",
    "22222222-2222-2222-2222-222222222222": "dsa-striver",
    "33333333-3333-3333-3333-333333333333": "neetcode-150",
    "44444444-4444-4444-4444-444444444444": "core-cs",
    "55555555-5555-5555-5555-555555555555": "aptitude",
    "66666666-6666-6666-6666-666666666666": "web-dev",
    "77777777-7777-7777-7777-777777777777": "system-design",
    "88888888-8888-8888-8888-888888888888": "python-backend",
    "99999999-9999-9999-9999-999999999999": "sql",
    "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa": "ai-engineering",
    "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb": "git-github",
    "cccccccc-cccc-cccc-cccc-cccccccccccc": "blind-75",
    "dddddddd-dddd-dddd-dddd-dddddddddddd": "lld",
    "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee": "behavioral",
    "ffffffff-ffff-ffff-ffff-ffffffffffff": "java-swe",
    "10101010-1010-1010-1010-101010101010": "cpp-swe",
    "20202020-2020-2020-2020-202020202020": "machine-learning",
    "30303030-3030-3030-3030-303030303030": "deep-learning",
    "40404040-4040-4040-4040-404040404040": "devops-cloud",
    "50505050-5050-5050-5050-505050505050": "linux-shell",
}


def upgrade() -> None:
    op.add_column("roadmaps", sa.Column("slug", sa.String(), nullable=True))
    op.create_unique_constraint("uq_roadmaps_slug", "roadmaps", ["slug"])
    op.create_index("ix_roadmaps_slug", "roadmaps", ["slug"], unique=False)

    conn = op.get_bind()
    stmt = sa.text("UPDATE roadmaps SET slug = :slug WHERE id = :id AND slug IS NULL")
    for rid, slug in SLUGS.items():
        conn.execute(stmt, {"slug": slug, "id": rid})


def downgrade() -> None:
    op.drop_index("ix_roadmaps_slug", table_name="roadmaps")
    op.drop_constraint("uq_roadmaps_slug", "roadmaps", type_="unique")
    op.drop_column("roadmaps", "slug")
