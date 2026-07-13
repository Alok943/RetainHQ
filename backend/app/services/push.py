"""
Web Push sender (pywebpush). No-op until VAPID_PRIVATE_KEY/VAPID_PUBLIC_KEY are
set — mirrors the mailer.py pattern (RESEND_API_KEY), so it's safe to deploy
gated-off. VAPID keys live in Render only (single source of truth); the
frontend fetches the public key via GET /api/push/vapid-public-key.
"""
from app.core.config import settings


class PushError(Exception):
    """A send attempt failed for a reason other than the subscription being gone."""


class PushGone(Exception):
    """The subscription is dead (404/410 from the push service) — caller should
    delete the row so a stale endpoint doesn't get retried forever."""


def is_configured() -> bool:
    return bool(settings.VAPID_PRIVATE_KEY and settings.VAPID_PUBLIC_KEY)


def send_push(sub_row, payload: dict) -> None:
    """Send one push. `sub_row` needs .endpoint/.p256dh/.auth. Raises PushGone
    for a dead subscription (404/410), PushError for anything else. Caller runs
    this off the event loop (it's a sync network call) via asyncio.to_thread."""
    if not is_configured():
        raise PushError("Push not configured (VAPID keys unset)")

    from pywebpush import webpush, WebPushException
    import json

    subscription_info = {
        "endpoint": sub_row.endpoint,
        "keys": {"p256dh": sub_row.p256dh, "auth": sub_row.auth},
    }
    try:
        webpush(
            subscription_info=subscription_info,
            data=json.dumps(payload),
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={"sub": settings.VAPID_SUBJECT},
        )
    except WebPushException as e:
        status_code = getattr(e.response, "status_code", None)
        if status_code in (404, 410):
            raise PushGone(str(e)) from e
        raise PushError(str(e)) from e
