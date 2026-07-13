from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.api.deps import get_db, get_current_user
from app.core.config import settings
from app.core.security import SupabaseUser
from app.schemas.push import VapidPublicKeyOut, PushSubscribeIn

router = APIRouter()

# Same upsert-by-natural-key shape as reminders.py's claim SQL: endpoint is the
# unique key (a re-subscribe from the same device/browser updates in place),
# so ownership can shift if a subscription outlives a sign-out/sign-in swap.
# id/created_at are bound params (not gen_random_uuid()/now()) so this stays
# portable to the SQLite test harness — same reasoning every model already
# uses default_factory=uuid.uuid4 instead of a DB-side default.
_UPSERT_SQL = text("""
    insert into push_subscriptions (id, user_id, endpoint, p256dh, auth, user_agent, created_at)
    values (:id, :user_id, :endpoint, :p256dh, :auth, :user_agent, :created_at)
    on conflict (endpoint) do update
        set user_id = excluded.user_id,
            p256dh = excluded.p256dh,
            auth = excluded.auth,
            user_agent = excluded.user_agent
""")

_DELETE_SQL = text("""
    delete from push_subscriptions
    where user_id = :user_id and endpoint = :endpoint
""")


@router.get("/vapid-public-key", response_model=VapidPublicKeyOut)
async def get_vapid_public_key():
    """404 when push isn't configured — single source of truth is the Render
    env var, avoiding a Vercel/Render key-sync hazard."""
    if not settings.VAPID_PUBLIC_KEY:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Push not configured")
    return VapidPublicKeyOut(key=settings.VAPID_PUBLIC_KEY)


@router.post("/subscribe", status_code=status.HTTP_204_NO_CONTENT)
async def subscribe(
    body: PushSubscribeIn,
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    user_id = uuid.UUID(current_user.id)
    await db.execute(
        _UPSERT_SQL,
        {
            # str(), not the UUID object — text() binds params through the raw
            # driver with no column-type coercion, and sqlite3 can't bind a
            # UUID object directly (Postgres accepts the string form fine).
            "id": str(uuid.uuid4()),
            "user_id": str(user_id),
            "endpoint": body.endpoint,
            "p256dh": body.p256dh,
            "auth": body.auth,
            "user_agent": body.userAgent,
            "created_at": datetime.utcnow(),
        },
    )
    await db.commit()


@router.delete("/subscribe", status_code=status.HTTP_204_NO_CONTENT)
async def unsubscribe(
    endpoint: str = Query(..., min_length=1, max_length=2000),
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    user_id = uuid.UUID(current_user.id)
    await db.execute(_DELETE_SQL, {"user_id": str(user_id), "endpoint": endpoint})
    await db.commit()
