"""
Seed script: Python for Backend Roles roadmap.

Placement-prep spine (phase = step): Python Language Core · Pythonic Constructs ·
OOP in Python · Concurrency, Memory & Performance · Web Framework & API ·
Data Layer · Testing · Production & Deployment.

Derived by content/PROMPT-roadmap-topics.md (extend mode). Audit trail:
content/research/python-backend/nodes.md. Interview/OA gate first (language
internals), production bar last. Concept-level recall material, not command memorisation.

Idempotent. Run: ./.venv/Scripts/python.exe seed_python_backend.py
"""
import asyncio
import uuid
from sqlalchemy import text
from app.core.database import engine

ROADMAP_ID = uuid.UUID("88888888-8888-8888-8888-888888888888")
SLUG = "python-backend"
TITLE = "Python for Backend Roles"
DESCRIPTION = "The Python-backend hiring gate end to end: language internals interviewers hammer (is vs ==, decorators, the GIL), then FastAPI, ORMs, testing and Docker — the production bar real backend roles screen for."

NODES = [
    # ---------------- 1 · Python Language Core ----------------
    ("Python Language Core", "Objects & Identity", "Mutable vs immutable types", "easy", "list/dict/set are mutable; int/str/tuple/frozenset are immutable."),
    ("Python Language Core", "Objects & Identity", "is vs ==", "easy", "== compares value; is compares identity (same object in memory)."),
    ("Python Language Core", "Objects & Identity", "None & truthiness", "easy", "Empty/0/None are falsy; test with `is None`, not `== None`."),
    ("Python Language Core", "Objects & Identity", "Variables as references", "medium", "Names bind to objects; assignment rebinds the name, it doesn't copy."),
    ("Python Language Core", "Collections", "list vs tuple", "easy", "Tuple is immutable + hashable; list is mutable and not hashable."),
    ("Python Language Core", "Collections", "dict internals & ordering", "medium", "Hash table; O(1) average lookup; insertion-ordered since 3.7."),
    ("Python Language Core", "Collections", "set & membership", "easy", "Unordered unique hashable items; O(1) average `in` test."),
    ("Python Language Core", "Collections", "Comprehensions", "easy", "[f(x) for x in xs if cond] builds a collection in one expression."),
    ("Python Language Core", "Collections", "Slicing", "easy", "s[start:stop:step]; stop is excluded; a negative step reverses."),
    ("Python Language Core", "Functions & Scope", "*args & **kwargs", "medium", "*args = tuple of extra positionals; **kwargs = dict of keywords."),
    ("Python Language Core", "Functions & Scope", "Mutable default argument pitfall", "hard", "Default is evaluated once; use a None sentinel, not []/{}."),
    ("Python Language Core", "Functions & Scope", "Closures & LEGB scope", "hard", "Inner fn captures enclosing vars; lookup Local→Enclosing→Global→Builtin."),
    ("Python Language Core", "Functions & Scope", "Positional vs keyword arguments", "easy", "Positional by order; keyword by name; keyword-only params come after *."),

    # ---------------- 2 · Pythonic Constructs ----------------
    ("Pythonic Constructs", "Lazy Evaluation", "Iterators & the iterator protocol", "medium", "__iter__ returns an iterator; __next__ yields, raises StopIteration."),
    ("Pythonic Constructs", "Lazy Evaluation", "Generators & yield", "hard", "yield produces values lazily; never holds the whole sequence in memory."),
    ("Pythonic Constructs", "Lazy Evaluation", "Generator expressions", "easy", "(x for x in xs) is lazy and memory-cheap vs a list comprehension."),
    ("Pythonic Constructs", "Function Tools", "Decorators", "hard", "A fn wrapping a fn; @deco means f = deco(f)."),
    ("Pythonic Constructs", "Function Tools", "functools.wraps", "medium", "Preserves the wrapped fn's __name__/__doc__ on the wrapper."),
    ("Pythonic Constructs", "Resource Safety", "Context managers (with)", "medium", "__enter__/__exit__ guarantee cleanup; `with` opens then closes safely."),
    ("Pythonic Constructs", "Error Handling", "try / except / else / finally", "easy", "else runs only if no exception; finally always runs."),
    ("Pythonic Constructs", "Error Handling", "Custom exceptions & EAFP", "medium", "Subclass Exception; prefer try/except over pre-checks (EAFP)."),

    # ---------------- 3 · OOP in Python ----------------
    ("OOP in Python", "Classes", "Class vs instance attributes", "easy", "Class attribute is shared; instance attribute is per-object via self."),
    ("OOP in Python", "Classes", "instance / class / static methods", "medium", "self / cls (@classmethod) / neither (@staticmethod)."),
    ("OOP in Python", "Classes", "@property", "medium", "A method accessed like an attribute; adds getters/setters."),
    ("OOP in Python", "Data Model", "Dunder methods (__eq__/__hash__)", "hard", "__eq__ defines equality; pair it with __hash__ to stay hashable."),
    ("OOP in Python", "Data Model", "__str__ vs __repr__", "easy", "str is readable for users; repr is unambiguous for developers."),
    ("OOP in Python", "Reuse", "Inheritance & super() (MRO)", "hard", "super() calls the parent; MRO is C3 linearization (left-to-right)."),
    ("OOP in Python", "Reuse", "Duck typing", "easy", "If it behaves like a duck, use it — protocol matters, not the type."),
    ("OOP in Python", "Reuse", "dataclasses", "easy", "@dataclass auto-generates __init__/__repr__/__eq__."),

    # ---------------- 4 · Concurrency, Memory & Performance ----------------
    ("Concurrency, Memory & Performance", "Concurrency Model", "Concurrency vs parallelism", "easy", "Concurrency = interleaving tasks; parallelism = truly simultaneous."),
    ("Concurrency, Memory & Performance", "Concurrency Model", "The GIL", "medium", "One thread runs Python bytecode at a time; I/O releases it."),
    ("Concurrency, Memory & Performance", "Concurrency Model", "Threading vs multiprocessing", "hard", "Threads for I/O-bound; processes for CPU-bound (bypass the GIL)."),
    ("Concurrency, Memory & Performance", "asyncio", "Coroutines, async / await", "medium", "async def returns a coroutine; await yields control to the loop."),
    ("Concurrency, Memory & Performance", "asyncio", "The event loop", "medium", "A single-threaded scheduler driving coroutines."),
    ("Concurrency, Memory & Performance", "asyncio", "Tasks & gather", "medium", "create_task + gather run awaitables concurrently."),
    ("Concurrency, Memory & Performance", "asyncio", "Blocking calls in async code", "hard", "A sync blocking call freezes the whole loop; use run_in_executor."),
    ("Concurrency, Memory & Performance", "Memory", "Reference counting & GC", "hard", "Objects freed at refcount 0; a cyclic GC catches reference cycles."),
    ("Concurrency, Memory & Performance", "Memory", "Shallow vs deep copy", "medium", "copy() shares nested objects; deepcopy() clones them fully."),

    # ---------------- 5 · Web Framework & API ----------------
    ("Web Framework & API", "Server Model", "WSGI vs ASGI", "medium", "WSGI is sync (Flask/gunicorn); ASGI is async (FastAPI/uvicorn)."),
    ("Web Framework & API", "Routing", "Path & query parameters", "easy", "Typed params → automatic validation + docs."),
    ("Web Framework & API", "Routing", "Request body & response_model", "easy", "Pydantic models in and out; shape the response."),
    ("Web Framework & API", "Routing", "Routers & app structure", "easy", "APIRouter splits endpoints; include_router mounts them."),
    ("Web Framework & API", "Request Lifecycle", "async vs def endpoints", "medium", "async for awaitable I/O; def runs in a threadpool."),
    ("Web Framework & API", "Request Lifecycle", "Dependency injection (Depends)", "medium", "Reusable deps: DB session, current user, pagination."),
    ("Web Framework & API", "Request Lifecycle", "Middleware & CORS", "medium", "Cross-cutting logic; CORS as an explicit allow-list."),
    ("Web Framework & API", "Request Lifecycle", "Status codes & OpenAPI", "easy", "Correct codes; /docs generated from your types."),
    ("Web Framework & API", "Request Lifecycle", "Background tasks", "medium", "Fire-and-forget work after the response is sent."),
    ("Web Framework & API", "Validation", "Pydantic models & validators", "medium", "Declarative schema; field_validator for custom rules."),
    ("Web Framework & API", "Validation", "pydantic-settings (env config)", "easy", "Typed config from .env; never hardcode secrets."),
    ("Web Framework & API", "Validation", "ConfigDict & from_attributes", "medium", "Serialise ORM objects with from_attributes=True."),

    # ---------------- 6 · Data Layer ----------------
    ("Data Layer", "ORM", "SQLAlchemy / SQLModel async", "medium", "AsyncSession with an async engine."),
    ("Data Layer", "ORM", "Sessions & expire_on_commit", "hard", "expire_on_commit=False to use objects after commit."),
    ("Data Layer", "ORM", "Eager loading (selectinload)", "hard", "Avoid lazy-load on a closed async session (MissingGreenlet)."),
    ("Data Layer", "ORM", "N+1 queries", "medium", "Join / batch instead of querying once per row."),
    ("Data Layer", "Schema & Connections", "Alembic migrations", "medium", "Versioned schema changes; never hand-edit prod."),
    ("Data Layer", "Schema & Connections", "Transactions & atomicity", "medium", "Commit is all-or-nothing; roll back on error."),
    ("Data Layer", "Schema & Connections", "Connection pooling", "medium", "Reuse connections; tune pool size & overflow."),

    # ---------------- 7 · Testing ----------------
    ("Testing", "pytest", "pytest basics & fixtures", "easy", "Arrange/act/assert; fixtures for setup/teardown."),
    ("Testing", "pytest", "Parametrized tests", "easy", "@pytest.mark.parametrize runs one test over many inputs."),
    ("Testing", "Isolation", "Mocking & patching", "medium", "unittest.mock / monkeypatch to isolate external calls."),
    ("Testing", "Async & API", "Async tests", "medium", "pytest-asyncio to await inside tests."),
    ("Testing", "Async & API", "API tests (httpx / TestClient)", "medium", "Hit endpoints in-process; override deps for a test DB."),
    ("Testing", "Quality", "Coverage & CI", "easy", "Measure coverage; run the suite in CI."),

    # ---------------- 8 · Production & Deployment ----------------
    ("Production & Deployment", "Config", "Env vars & secrets (12-factor)", "easy", "Config lives in the environment, not code; secrets out of the image."),
    ("Production & Deployment", "Observability", "Structured logging", "medium", "JSON logs, levels, request IDs."),
    ("Production & Deployment", "Errors", "HTTPException & error shape", "easy", "Raise with status + detail; keep one consistent payload shape."),
    ("Production & Deployment", "Docker", "Dockerfile & multi-stage builds", "medium", "Order layers for cache; split build vs runtime for a small image."),
    ("Production & Deployment", "Serving", "uvicorn / gunicorn workers", "medium", "ASGI workers; worker count scales with CPU cores."),
    ("Production & Deployment", "Hardening", "Health checks, rate limiting & JWT/CORS", "medium", "/health for probes; verify tokens; rate-limit + explicit CORS allow-list."),
]


async def main():
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM roadmap_nodes WHERE roadmap_id = :rid"), {"rid": str(ROADMAP_ID)})
        await conn.execute(text("DELETE FROM roadmaps WHERE id = :rid"), {"rid": str(ROADMAP_ID)})
        await conn.execute(
            text("INSERT INTO roadmaps (id, slug, title, description, created_at) VALUES (:id, :slug, :title, :desc, now())"),
            {"id": str(ROADMAP_ID), "slug": SLUG, "title": TITLE, "desc": DESCRIPTION},
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
