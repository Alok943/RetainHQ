"""
Ownership / tenant-isolation test harness.

WHY THIS SUITE EXISTS: the backend connects to Postgres with a role that
bypasses RLS, so per-user isolation lives ONLY in each route's WHERE clauses.
One forgotten `.where(X.user_id == user_id)` is a silent cross-user data leak
that nothing at the DB layer would catch. These tests hit every user-scoped
route as two different users and assert neither can read or mutate the
other's rows.

Runs against in-memory SQLite (aiosqlite) — no Supabase or network needed.
Endpoints built on Postgres-only SQL (admin funnel over auth.users, the
pg-dialect progress upsert, reminder queries) are exercised only for their
auth-gate behavior, which is the point of this suite anyway.
"""
import os
import uuid

# Must be set BEFORE any `app.*` import — Settings() is constructed at import
# time and would otherwise pick up backend/.env (which has DEBUG/DEV_AUTH_BYPASS
# enabled for local dev). Plain assignment, not setdefault, for the dangerous ones.
os.environ["DEBUG"] = "false"
os.environ["DEV_AUTH_BYPASS"] = "false"
os.environ["GRADER_ENABLED"] = "false"
# Blank, not left to .env's real key: without this, embeddings.embed_batch
# and llm_classifier.classify_session attempt genuine Gemini calls during
# tests. Both have their own fallback paths for a missing key (immediate
# ValueError / "not configured" result) — with a real key those paths are
# skipped and the test instead pays each call's full network round-trip
# (or its multi-second timeout, if the sandbox has no egress at all).
os.environ["GEMINI_API_KEY"] = ""
os.environ["ADMIN_EMAIL"] = "admin@example.com"
os.environ["CRON_SECRET"] = "test-cron-secret"
os.environ.setdefault("SUPABASE_URL", "https://test-project.supabase.co")
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-only-secret")
# Import-time engine only — never connected to, because get_db is overridden.
# Must stay a postgres URL: database.py passes asyncpg-specific pool/connect
# args that other dialects reject at create_async_engine() time.
os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/test_never_connected"

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from app.main import app
from app.api.deps import get_current_user, get_db, get_optional_user
from app.core.security import SupabaseUser

# Two ordinary users and the admin. Fixed UUIDs so failures are reproducible.
USER_A = SupabaseUser(id="11111111-1111-4111-8111-111111111111", email="alice@example.com", role="authenticated")
USER_B = SupabaseUser(id="22222222-2222-4222-8222-222222222222", email="bob@example.com", role="authenticated")
ADMIN = SupabaseUser(id="99999999-9999-4999-8999-999999999999", email="admin@example.com", role="authenticated")

# Who the overridden auth dependency returns. Tests flip this via `as_user`.
_current: dict = {"user": USER_A}


@pytest_asyncio.fixture
async def db_env():
    """Fresh in-memory DB per test. StaticPool shares the single sqlite
    connection across sessions so every session sees the same data."""
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    yield maker
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_env):
    async def _get_db():
        async with db_env() as session:
            yield session

    async def _get_user() -> SupabaseUser:
        return _current["user"]

    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_current_user] = _get_user
    app.dependency_overrides[get_optional_user] = _get_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()
    _current["user"] = USER_A


@pytest_asyncio.fixture
async def db(db_env):
    """Direct DB session on the same in-memory DB, for seeding rows that
    can't go through the API on sqlite (e.g. roadmap fixtures)."""
    async with db_env() as session:
        yield session


@pytest.fixture
def as_user():
    """Switch which user the auth dependency impersonates."""
    def _set(user: SupabaseUser) -> None:
        _current["user"] = user
    yield _set
    _current["user"] = USER_A
