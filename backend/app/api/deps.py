from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_session_maker
from app.core.security import verify_token, SupabaseUser
from app.core.config import settings

security = HTTPBearer()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> SupabaseUser:
    """
    Dependency that extracts the token from the Bearer header
    and validates it against the Supabase JWT secret.
    """
    return verify_token(credentials.credentials)

async def get_admin_user(current_user: SupabaseUser = Depends(get_current_user)) -> SupabaseUser:
    """Gate to the founder/admin email (settings.ADMIN_EMAIL). 403 for everyone else."""
    if not current_user.email or current_user.email.lower() != settings.ADMIN_EMAIL.lower():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user
