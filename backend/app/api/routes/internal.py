"""
Internal, machine-triggered endpoints (no user JWT). Guarded by a shared secret
in the `X-Cron-Secret` header so any scheduler — GitHub Actions, a host cron, a
third-party pinger — can drive them. Host-agnostic by design: switching from
Railway to Render changes only the target URL, not this code.
"""
import hmac

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.config import settings
from app.services.reminders import send_due_reminders

router = APIRouter()


def verify_cron_secret(x_cron_secret: str = Header(default="")) -> None:
    """Reject unless the caller presents the configured secret. If CRON_SECRET is
    unset, the endpoint is closed to everyone (no open trigger in prod)."""
    if not settings.CRON_SECRET or not hmac.compare_digest(x_cron_secret, settings.CRON_SECRET):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid cron secret")


@router.post("/send-reminders", dependencies=[Depends(verify_cron_secret)])
async def trigger_send_reminders(db: AsyncSession = Depends(get_db)) -> dict:
    """Run one due-review reminder pass. Idempotent per user per UTC day."""
    return await send_due_reminders(db)
