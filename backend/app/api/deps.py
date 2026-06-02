from typing import AsyncGenerator
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_session_maker
from app.core.security import verify_token, SupabaseUser

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
