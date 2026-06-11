"""
Due-review reminder batch. Finds users with reviews due now (and not already
reminded today), sends each a short nudge, and records the send so it can't repeat.

Design:
  - One read query for candidates (reviews + auth.users + activities), excluding
    anyone already reminded today via the reminder_log ledger.
  - Per user: CLAIM a reminder_log row first (INSERT ... ON CONFLICT DO NOTHING).
    Only if the claim succeeds do we send — so two concurrent runs can't double-send.
    A failed send leaves the claim in place: we'd rather a user miss one day's email
    (they still see it in-app) than risk spamming. Transient outages self-heal next day.
  - Email send is sync (Resend SDK), run off the event loop via asyncio.to_thread.
"""
import asyncio
import html as _html
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.mailer import send_email, is_configured, MailerError


# Candidates: users with ≥1 due review now, who have an email and haven't been
# reminded today. Naive-UTC timestamps → compare against UTC wall clock.
_CANDIDATES_SQL = text("""
    select r.user_id,
           u.email,
           count(*)                                          as due_count,
           (array_agg(a.topic order by r.scheduled_for))[1:3] as sample_topics
    from reviews r
    join auth.users u on u.id = r.user_id
    join activities a on a.id = r.activity_id
    where r.status = 'due'
      and r.scheduled_for <= (now() at time zone 'utc')
      and u.email is not null
      and not exists (
        select 1 from reminder_log rl
        where rl.user_id = r.user_id
          and rl.sent_on = (now() at time zone 'utc')::date
      )
    group by r.user_id, u.email
""")

# Atomic claim: succeeds (returns a row) only for the first run of the day per user.
_CLAIM_SQL = text("""
    insert into reminder_log (id, user_id, sent_on, due_count, created_at)
    values (gen_random_uuid(), :user_id, :sent_on, :due_count, (now() at time zone 'utc'))
    on conflict (user_id, sent_on) do nothing
    returning id
""")


def _estimate_minutes(due_count: int) -> int:
    # ~1.5 min per recall, floor of 2 so it never reads as trivially short.
    return max(2, round(due_count * 1.5))


def build_email(due_count: int, sample_topics: list[str]) -> tuple[str, str]:
    """Return (subject, html) for a reminder. Plain, one accent, one CTA."""
    review_url = f"{settings.APP_BASE_URL.rstrip('/')}/reviews"
    mins = _estimate_minutes(due_count)
    noun = "review" if due_count == 1 else "reviews"
    subject = f"{due_count} {noun} due on RetainHQ"

    topics = [t for t in (sample_topics or []) if t][:3]
    shown = len(topics)
    extra = due_count - shown
    topic_items = "".join(
        f'<li style="margin:0 0 6px;color:#0F172A;font-size:14px;line-height:1.5;">{_html.escape(t)}</li>'
        for t in topics
    )
    more_line = (
        f'<li style="margin:0;color:#64748B;font-size:14px;list-style:none;">+ {extra} more</li>'
        if extra > 0 else ""
    )
    topic_block = (
        f'<ul style="margin:0 0 24px;padding-left:20px;">{topic_items}{more_line}</ul>'
        if topics else '<div style="height:8px;"></div>'
    )

    html = f"""\
<div style="margin:0;padding:24px;background:#f9f9f6;font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;">
  <div style="max-width:480px;margin:0 auto;background:#ffffff;border:1px solid #e2e8f0;border-radius:12px;padding:28px 28px 32px;">
    <p style="margin:0 0 4px;font-size:13px;font-weight:600;color:#0891B2;letter-spacing:0.5px;">RETAINHQ</p>
    <h1 style="margin:0 0 8px;font-size:20px;font-weight:600;color:#0F172A;">
      You have {due_count} {noun} due
    </h1>
    <p style="margin:0 0 20px;font-size:14px;color:#64748B;line-height:1.6;">
      A quick recall pass now is what keeps these from fading — about {mins} minutes.
    </p>
    {topic_block}
    <a href="{review_url}"
       style="display:inline-block;background:#0891B2;color:#ffffff;text-decoration:none;font-size:15px;font-weight:600;padding:12px 24px;border-radius:8px;">
      Start reviewing →
    </a>
    <p style="margin:24px 0 0;font-size:12px;color:#94a3b8;line-height:1.5;">
      You're getting this because you have active reviews on RetainHQ.
    </p>
  </div>
</div>"""
    return subject, html


async def send_due_reminders(db: AsyncSession) -> dict:
    """Run one reminder pass. Returns a summary dict (safe to log/return)."""
    if not is_configured():
        return {"status": "disabled", "reason": "RESEND_API_KEY not set", "sent": 0, "errors": 0, "candidates": 0}

    # Pin to UTC so the claim's sent_on matches the candidates SQL's
    # (now() at time zone 'utc')::date regardless of the host's process timezone.
    today = datetime.now(timezone.utc).date()
    rows = (await db.execute(_CANDIDATES_SQL)).mappings().all()

    sent = 0
    errors = 0
    error_samples: list[str] = []

    for row in rows:
        user_id = row["user_id"]
        email = row["email"]
        due_count = row["due_count"]
        sample_topics = list(row["sample_topics"] or [])

        # Claim first — only proceed if we won the day for this user.
        claimed = (await db.execute(
            _CLAIM_SQL, {"user_id": user_id, "sent_on": today, "due_count": due_count}
        )).first()
        if not claimed:
            continue
        await db.commit()  # persist the claim before the (slow, external) send

        subject, html = build_email(due_count, sample_topics)
        try:
            await asyncio.to_thread(send_email, email, subject, html)
            sent += 1
        except MailerError as e:
            errors += 1
            if len(error_samples) < 5:
                error_samples.append(str(e))

    return {
        "status": "ok",
        "candidates": len(rows),
        "sent": sent,
        "errors": errors,
        "error_samples": error_samples,
    }
