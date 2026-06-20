from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_session_maker
from app.core.security import verify_token, SupabaseUser
from app.core.config import settings

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


# --- DEV ONLY auth bypass (settings.DEV_AUTH_BYPASS, default False) ----------
# Lets the authenticated app be previewed locally without Google OAuth. The
# impersonated account is resolved ONCE (by email) and cached, so the JWT-less
# auth path stays cheap. This is gated entirely by DEV_AUTH_BYPASS, which is
# False by default and must never be set in production.
_dev_user_cache: Optional[SupabaseUser] = None

async def _dev_bypass_user() -> SupabaseUser:
    global _dev_user_cache
    if _dev_user_cache is not None:
        return _dev_user_cache
    email = settings.DEV_USER_EMAIL or settings.ADMIN_EMAIL
    uid = settings.DEV_USER_ID
    if not uid:
        # Resolve the account id by email (the app role can read auth.users, same
        # as the admin funnel). Falls back to a nil UUID = an empty dev account.
        async with async_session_maker() as session:
            row = (await session.execute(
                text("select id::text from auth.users where lower(email) = lower(:e) limit 1"),
                {"e": email},
            )).first()
        uid = row[0] if row else "00000000-0000-0000-0000-000000000000"
    _dev_user_cache = SupabaseUser(id=uid, email=email, role="authenticated")
    return _dev_user_cache


async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security)) -> SupabaseUser:
    """
    Extract the Bearer token and validate it against the Supabase JWKS.
    DEV ONLY: when settings.DEV_AUTH_BYPASS is set, skip verification entirely
    and return the dev account (see _dev_bypass_user).
    """
    if settings.DEV_AUTH_BYPASS:
        return await _dev_bypass_user()
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return verify_token(credentials.credentials)

async def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security)) -> Optional[SupabaseUser]:
    """
    Optional dependency that returns the user if a valid token is provided, otherwise None.
    """
    if settings.DEV_AUTH_BYPASS:
        return await _dev_bypass_user()
    if not credentials:
        return None
    try:
        return verify_token(credentials.credentials)
    except HTTPException:
        return None

async def get_admin_user(current_user: SupabaseUser = Depends(get_current_user)) -> SupabaseUser:
    """Gate to the founder/admin email (settings.ADMIN_EMAIL). 403 for everyone else."""
    if not current_user.email or current_user.email.lower() != settings.ADMIN_EMAIL.lower():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user
