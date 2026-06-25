"""Idempotent backfill of roadmaps.slug for the seeded roadmaps (fixed UUIDs).

The migration `a3f1c0d4e7b2` already backfills prod. The 3 content seeds
(python-swe, sql, aptitude) set their slug inline, so re-running them is safe.
The other (flowchart-only) seeds do NOT set slug, so re-running one would NULL it.
Run this afterwards to restore all slugs in one shot:

    ./.venv/Scripts/python.exe backfill_roadmap_slugs.py

Only fills rows where slug IS NULL, so it never clobbers an existing slug.
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine

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


async def main():
    async with engine.begin() as conn:
        stmt = text("UPDATE roadmaps SET slug = :slug WHERE id = :id AND slug IS NULL")
        n = 0
        for rid, slug in SLUGS.items():
            res = await conn.execute(stmt, {"slug": slug, "id": rid})
            n += res.rowcount or 0
    print(f"Backfilled slug on {n} roadmap(s).")


if __name__ == "__main__":
    asyncio.run(main())
