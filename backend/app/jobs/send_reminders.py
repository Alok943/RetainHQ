"""
CLI entrypoint for the due-review reminder pass — host-agnostic cron.

    python -m app.jobs.send_reminders

Use this when the host has a native scheduled job (Railway cron, Render cron job,
a system crontab). The HTTP endpoint POST /api/internal/send-reminders does the
same thing for schedulers that can only make web requests (e.g. GitHub Actions).
Exits non-zero if any send errored, so a cron runner surfaces failures.
"""
import asyncio
import json
import sys

from app.core.database import async_session_maker
from app.services.reminders import send_due_reminders


async def _run() -> dict:
    async with async_session_maker() as db:
        return await send_due_reminders(db)


def main() -> None:
    summary = asyncio.run(_run())
    print(json.dumps(summary))
    if summary.get("errors"):
        sys.exit(1)


if __name__ == "__main__":
    main()
