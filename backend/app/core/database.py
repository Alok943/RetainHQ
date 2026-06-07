from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel import SQLModel
from app.core.config import settings

# asyncpg expects postgresql+asyncpg:// but Supabase provides postgresql://
DB_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
if "?" in DB_URL:
    DB_URL = DB_URL.split("?")[0] # Strip pgbouncer query params if present for direct connection

engine = create_async_engine(
    DB_URL,
    echo=settings.DEBUG,  # only log SQL in dev; never in prod (leaks PII to logs)
    future=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    # Validate a pooled connection before use so a dropped/stale connection
    # (e.g. after a network blip) is recycled instead of raising mid-request.
    pool_pre_ping=True,
    connect_args={
        "prepared_statement_cache_size": 0,
        "statement_cache_size": 0
    }
)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
