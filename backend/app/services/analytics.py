"""
Server-side PostHog capture — the source of truth for events the client can't be
trusted to send (ad-blockers, closed tabs, background jobs).

Design:
  - No-op until POSTHOG_API_KEY is set, so it's safe to deploy gated-off (mirrors
    the mailer / grader pattern). Client analytics keep working regardless.
  - Never raises into a request. Every capture is best-effort and swallows errors;
    an analytics outage must not fail a review completion or a reminder send.
  - Same PostHog project as the frontend (posthog-js), keyed by the same distinct_id
    (the Supabase user id), so client and server events land on one person timeline.

Distinct id contract: pass str(user_id) — identical to the frontend's
identifyUser(session.user.id), so a user's client + server events unify.
"""
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

_client = None
_initialized = False


def _get_client():
    """Lazily build the PostHog client. Returns None when disabled or unavailable."""
    global _client, _initialized
    if _initialized:
        return _client
    _initialized = True
    if not settings.POSTHOG_API_KEY:
        return None
    try:
        from posthog import Posthog

        _client = Posthog(
            project_api_key=settings.POSTHOG_API_KEY,
            host=settings.POSTHOG_HOST,
            # Server events are low-volume and high-value — flush promptly rather
            # than batching for throughput.
            flush_at=1,
            flush_interval=0.5,
        )
    except Exception as e:  # import missing / bad config — stay a silent no-op
        logger.warning("PostHog server analytics disabled: %s", e)
        _client = None
    return _client


def is_configured() -> bool:
    return _get_client() is not None


def capture(distinct_id: str, event: str, properties: dict | None = None) -> None:
    """Best-effort event capture. Never raises."""
    client = _get_client()
    if client is None:
        return
    try:
        props = {"source": "backend", **(properties or {})}
        client.capture(distinct_id=str(distinct_id), event=event, properties=props)
    except Exception as e:
        logger.warning("PostHog capture failed for %s: %s", event, e)


def shutdown() -> None:
    """Flush any buffered events on app shutdown. Never raises."""
    client = _get_client()
    if client is None:
        return
    try:
        client.shutdown()
    except Exception:
        pass
