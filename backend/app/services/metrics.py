"""
Generic learning-analytics event recorder. No mailer/posthog-style "unconfigured"
gate — metric_events is always on (it's a first-party table, not a third-party
integration), but record_metric_event NEVER commits: it's meant to ride the
caller's existing transaction, so one failed metric write can't silently
half-commit unrelated state, and callers don't pay an extra round-trip.
"""
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import MetricEvent


async def record_metric_event(
    db: AsyncSession,
    user_id: uuid.UUID,
    event_type: str,
    payload: Optional[dict] = None,
    entity_id: Optional[uuid.UUID] = None,
) -> None:
    db.add(MetricEvent(user_id=user_id, event_type=event_type, entity_id=entity_id, payload=payload or {}))


async def get_latest_consent_tier(db: AsyncSession, user_id: uuid.UUID) -> Optional[str]:
    """The user's current companion consent tier, derived from the newest
    `companion_consent` metric_event — no new column
    (IMPLEMENTATION-companion-consent.md §4.3). None = never asked (or never
    reached the server). The extension's own consentTier===null already
    blocks all LLM-surface capture client-side, but a content-bearing server
    code path must check this independently — the extension is client code a
    user controls, the server is where the tier actually holds."""
    event = (
        await db.execute(
            select(MetricEvent)
            .where(MetricEvent.user_id == user_id, MetricEvent.event_type == "companion_consent")
            .order_by(MetricEvent.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if event is None:
        return None
    return (event.payload or {}).get("tier")
