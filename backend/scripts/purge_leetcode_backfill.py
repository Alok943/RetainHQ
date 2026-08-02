"""Soft-delete backfilled LeetCode solves for one user, then recompute mastery.

Why this exists (2026-08-02): the first working companion import ran BEFORE the
language/window filters landed (D-060), so it pulled 136 problems spanning every
language and the whole account history — including a C++ back-catalogue the user
has since moved away from. Those events inflate mastery on nodes they'd now
struggle with, which is precisely the dishonesty the evidence spine exists to
avoid.

Targets ONLY rows this import created: event_type=PROBLEM_SOLVED, source=leetcode,
payload->>'backfilled' = 'true'. A live solve captured by the content script
(`/leetcode/solve`, no `backfilled` key) is real evidence and is left alone.

SOFT delete, matching `DELETE /api/evidence/events/{id}` — rows keep their data
and only gain `deleted_at`, so this is reversible with a single UPDATE (printed
at the end). `recompute_user` then replays the surviving events, exactly as
`POST /api/evidence/recompute` does.

Usage (from backend/, venv active):
    python -m scripts.purge_leetcode_backfill --email you@example.com --dry-run
    python -m scripts.purge_leetcode_backfill --email you@example.com --commit

Reads DATABASE_URL from the environment like the app does — point it at prod
deliberately, never by accident. --dry-run is the default.
"""
import argparse
import asyncio
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import engine
from app.models.models import LearningEvent
from app.services import evidence


async def _resolve_user_id(db: AsyncSession, email: str | None, user_id: str | None) -> uuid.UUID:
    if user_id:
        return uuid.UUID(user_id)
    # auth.users is Supabase-owned and not mapped in models.py, so this reads it
    # directly rather than pretending there's an ORM model for it.
    from sqlalchemy import text
    row = (await db.execute(
        text("select id from auth.users where email = :email"), {"email": email}
    )).first()
    if row is None:
        raise SystemExit(f"No auth user found for {email!r}")
    return row[0] if isinstance(row[0], uuid.UUID) else uuid.UUID(str(row[0]))


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", help="Supabase auth email of the user to clean up")
    parser.add_argument("--user-id", help="UUID, if you'd rather not hit auth.users")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", action="store_true", default=True)
    group.add_argument("--commit", action="store_true", help="Actually write the soft-deletes")
    args = parser.parse_args()

    if not args.email and not args.user_id:
        raise SystemExit("Pass --email or --user-id")

    async with AsyncSession(engine, expire_on_commit=False) as db:
        user_id = await _resolve_user_id(db, args.email, args.user_id)

        rows = (await db.execute(
            select(LearningEvent).where(
                LearningEvent.user_id == user_id,
                LearningEvent.event_type == "PROBLEM_SOLVED",
                LearningEvent.source == "leetcode",
                LearningEvent.deleted_at.is_(None),
            )
        )).scalars().all()

        # Filtered in Python, not SQL: payload is JSON and the ->> operator's
        # spelling differs across backends (the test suite runs SQLite), so a
        # portable filter here beats a Postgres-only WHERE clause.
        targets = [e for e in rows if (e.payload or {}).get("backfilled") is True]
        live_solves = len(rows) - len(targets)

        print(f"user_id            : {user_id}")
        print(f"live leetcode rows : {len(rows)}")
        print(f"  backfilled       : {len(targets)}  <- will be soft-deleted")
        print(f"  content-script   : {live_solves}  <- left alone (real evidence)")
        print(f"  distinct nodes   : {len({e.node_id for e in targets})}")

        if not args.commit:
            print("\nDRY RUN — nothing written. Re-run with --commit to apply.")
            return

        now = datetime.utcnow()
        for event in targets:
            event.deleted_at = now
            db.add(event)
        await db.commit()

        touched = await evidence.recompute_user(db, user_id)
        await db.commit()

        print(f"\nSoft-deleted {len(targets)} event(s); recomputed {touched} node(s).")
        print("Reversible with:")
        print(
            f"  update learning_events set deleted_at = null "
            f"where user_id = '{user_id}' and deleted_at = '{now.isoformat()}';"
        )
        print("  (then POST /api/evidence/recompute, or re-run recompute_user)")


if __name__ == "__main__":
    asyncio.run(main())
