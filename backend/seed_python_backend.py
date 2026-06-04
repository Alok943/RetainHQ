"""
Seed script: Python Backend (Production) roadmap.

Sub-tracks (phase = step spine): Async Python · FastAPI · Pydantic ·
Data Layer · Errors & Logging · Testing · Production & Docker.

The production-backend bar (async, FastAPI, Pydantic, error handling, testing,
Docker). Concept-level recall material, not command memorisation.

Idempotent. Run: ./.venv/Scripts/python.exe seed_python_backend.py
"""
import asyncio
import uuid
from sqlalchemy import text
from app.core.database import engine

ROADMAP_ID = uuid.UUID("88888888-8888-8888-8888-888888888888")
TITLE = "Python Backend (Production)"
DESCRIPTION = "Production-grade Python services: async, FastAPI, Pydantic, robust error handling, testing and Docker — the bar real backend roles hire for."

NODES = [
    # ---------------- Async Python ----------------
    ("Async Python", "Concurrency", "Concurrency vs parallelism", "easy", "Concurrency = overlapping tasks; parallelism = truly simultaneous."),
    ("Async Python", "Concurrency", "The GIL", "medium", "One thread runs Python bytecode at a time; I/O releases it."),
    ("Async Python", "asyncio", "Coroutines, async / await", "medium", "async def returns a coroutine; await yields control to the loop."),
    ("Async Python", "asyncio", "The event loop", "medium", "Single-threaded scheduler driving coroutines."),
    ("Async Python", "asyncio", "Tasks & gather", "medium", "create_task + gather run awaitables concurrently."),
    ("Async Python", "asyncio", "Sync vs async I/O", "medium", "Async wins for I/O-bound work, not CPU-bound."),
    ("Async Python", "Pitfalls", "Blocking calls in async code", "hard", "A sync blocking call freezes the whole loop; use run_in_executor."),

    # ---------------- FastAPI ----------------
    ("FastAPI", "Routing", "Path & query parameters", "easy", "Typed params → automatic validation + docs."),
    ("FastAPI", "Routing", "Request body & response_model", "easy", "Pydantic models in and out; shape responses."),
    ("FastAPI", "Routing", "Routers & app structure", "easy", "APIRouter splits endpoints; include_router."),
    ("FastAPI", "Async", "async vs def endpoints", "medium", "async for awaitable I/O; def runs in a threadpool."),
    ("FastAPI", "DI", "Dependency injection (Depends)", "medium", "Reusable deps: DB session, current user, pagination."),
    ("FastAPI", "Middleware", "Middleware & CORS", "medium", "Cross-cutting logic; CORS as an explicit allow-list."),
    ("FastAPI", "Tasks", "Background tasks", "medium", "Fire-and-forget work after the response is sent."),
    ("FastAPI", "Docs", "Status codes & OpenAPI", "easy", "Correct codes; /docs generated from your types."),

    # ---------------- Pydantic ----------------
    ("Pydantic", "Models", "BaseModel & field types", "easy", "Declarative schema with validation."),
    ("Pydantic", "Models", "Validators", "medium", "field_validator / model_validator for custom rules."),
    ("Pydantic", "v2", "ConfigDict & from_attributes", "medium", "Serialise ORM objects (from_attributes=True)."),
    ("Pydantic", "Settings", "pydantic-settings (env config)", "easy", "Typed config from .env; never hardcode secrets."),
    ("Pydantic", "Serialization", "Serialization & aliases", "medium", "model_dump(by_alias), exclude, JSON output."),

    # ---------------- Data Layer ----------------
    ("Data Layer", "ORM", "SQLAlchemy / SQLModel async", "medium", "AsyncSession with an async engine."),
    ("Data Layer", "ORM", "Sessions & expire_on_commit", "hard", "expire_on_commit=False to use objects after commit."),
    ("Data Layer", "ORM", "Eager loading (selectinload)", "hard", "Avoid lazy-load on a closed async session (MissingGreenlet)."),
    ("Data Layer", "Migrations", "Alembic migrations", "medium", "Versioned schema changes; never hand-edit prod."),
    ("Data Layer", "Performance", "Connection pooling", "medium", "Reuse connections; tune pool size & overflow."),
    ("Data Layer", "Performance", "N+1 queries", "medium", "Join / batch instead of querying per row."),

    # ---------------- Errors & Logging ----------------
    ("Errors & Logging", "Exceptions", "HTTPException & error shape", "easy", "Raise with status + detail; consistent payload."),
    ("Errors & Logging", "Exceptions", "Custom exception handlers", "medium", "@app.exception_handler for uniform errors."),
    ("Errors & Logging", "Validation", "Validation error responses", "medium", "422 from Pydantic; shape the message."),
    ("Errors & Logging", "Logging", "Structured logging", "medium", "JSON logs, levels, request IDs."),

    # ---------------- Testing ----------------
    ("Testing", "pytest", "pytest basics & fixtures", "easy", "Arrange/act/assert; fixtures for setup/teardown."),
    ("Testing", "pytest", "Async tests", "medium", "pytest-asyncio to await inside tests."),
    ("Testing", "API", "httpx / TestClient", "medium", "Hit endpoints in-process."),
    ("Testing", "API", "Mocking & a test database", "medium", "Override deps; throwaway DB per run."),
    ("Testing", "Quality", "Coverage & CI", "easy", "Measure coverage; run the suite in CI."),

    # ---------------- Production & Docker ----------------
    ("Production & Docker", "Docker", "Dockerfile & layer caching", "medium", "Order layers for cache; use .dockerignore."),
    ("Production & Docker", "Docker", "Multi-stage builds", "medium", "Small final image; split build vs runtime deps."),
    ("Production & Docker", "Serving", "uvicorn / gunicorn workers", "medium", "ASGI workers; count scales with cores."),
    ("Production & Docker", "Config", "Env vars & secrets", "easy", "12-factor config; secrets out of the image."),
    ("Production & Docker", "Security", "Auth (JWT) & CORS", "medium", "Verify tokens; explicit CORS allow-list."),
    ("Production & Docker", "Ops", "Health checks & observability", "medium", "/health; logs, metrics, traces."),
    ("Production & Docker", "Ops", "Rate limiting", "medium", "Protect endpoints from abuse."),
]


async def main():
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM roadmap_nodes WHERE roadmap_id = :rid"), {"rid": str(ROADMAP_ID)})
        await conn.execute(text("DELETE FROM roadmaps WHERE id = :rid"), {"rid": str(ROADMAP_ID)})
        await conn.execute(
            text("INSERT INTO roadmaps (id, title, description, created_at) VALUES (:id, :title, :desc, now())"),
            {"id": str(ROADMAP_ID), "title": TITLE, "desc": DESCRIPTION},
        )
        for i, (phase, section, title, tier, desc) in enumerate(NODES):
            await conn.execute(
                text("INSERT INTO roadmap_nodes "
                     "(id, roadmap_id, phase, section, title, tier, order_index, description) "
                     "VALUES (:id, :rid, :phase, :section, :title, :tier, :idx, :desc)"),
                {"id": str(uuid.uuid4()), "rid": str(ROADMAP_ID), "phase": phase,
                 "section": section, "title": title, "tier": tier, "idx": i, "desc": desc},
            )
    print(f"Seeded '{TITLE}' with {len(NODES)} nodes.")


if __name__ == "__main__":
    asyncio.run(main())
