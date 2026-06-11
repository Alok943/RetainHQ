"""
Transactional email via Resend. One thin wrapper, gated on RESEND_API_KEY so the
app runs (and the reminder job no-ops) when email isn't configured.

The Resend SDK is synchronous (uses `requests`), so callers in async code should
run `send_email` via `asyncio.to_thread` to avoid blocking the event loop.
"""
from app.core.config import settings


class MailerError(RuntimeError):
    pass


def is_configured() -> bool:
    return bool(settings.RESEND_API_KEY)


def send_email(to: str, subject: str, html: str) -> str:
    """Send one email. Returns the provider message id. Raises MailerError on
    misconfiguration or send failure."""
    if not settings.RESEND_API_KEY:
        raise MailerError("RESEND_API_KEY is not set — email is disabled.")

    try:
        import resend
    except ImportError as e:
        raise MailerError("The 'resend' package is not installed (pip install resend).") from e

    resend.api_key = settings.RESEND_API_KEY
    try:
        resp = resend.Emails.send({
            "from": settings.RESEND_FROM,
            "to": [to],
            "subject": subject,
            "html": html,
        })
        # SDK returns a dict-like with an "id" on success.
        return resp.get("id") if isinstance(resp, dict) else getattr(resp, "id", "")
    except Exception as e:
        raise MailerError(f"Resend send failed: {e}") from e
