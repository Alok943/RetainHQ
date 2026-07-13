"""
Generic learning-analytics event recorder. No mailer/posthog-style "unconfigured"
gate — metric_events is always on (it's a first-party table, not a third-party
integration), but record_metric_event NEVER commits: it's meant to ride the
caller's existing transaction, so one failed metric write can't silently
half-commit unrelated state, and callers don't pay an extra round-trip.
"""
import uuid
from typing import Optional

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
