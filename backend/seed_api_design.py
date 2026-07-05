"""
Seed script: API Design & Distributed APIs roadmap.

Sub-tracks (phase = step spine): REST Fundamentals · Auth & Authorization · Versioning & Evolution.

STATUS: FOUNDATIONAL + KEY INTERMEDIATE (5 phases, 21 nodes). Phases 1-3 (14 nodes) are the
validated first research run (Gemini Deep Research, India backend 0-4yr). Phases 4-5 (7 nodes)
are the highest-leverage additions that lift it past beginner-only and earn the "Distributed
APIs" title — protocol choice, contract docs, and the resilience/distributed contract. Audit
trail in content/research/api-design/nodes.md. Replaces the old "Coming Soon" stub.
Still deferred (a later research run, then MERGE + seed once): broader OWASP security items
(broken auth, mass assignment, injection), deeper gRPC/GraphQL protocol mechanics. Re-seeding
after users have progress wipes user_progress + nulls activities.node_id — don't promote to prod
until you're done adding phases.

Boundary (kept crisp): this roadmap owns the CONTRACT (protocol/resource semantics, auth
protocols, versioning, and the CLIENT-FACING contract of resilience — 429/Retry-After, idempotency
keys, webhook signatures). It does NOT own the INFRA that implements them: gateway internals +
the distributed rate-limit algorithm (token bucket etc.) = System Design; framework specifics
(FastAPI/Express/Spring) = Python Backend. See the excluded list in the audit.

Idempotent. Run: ./.venv/Scripts/python.exe seed_api_design.py
"""
import asyncio
import uuid
from sqlalchemy import text
from app.core.database import engine

ROADMAP_ID = uuid.UUID("e0e0e0e0-e0e0-e0e0-e0e0-e0e0e0e0e0e0")
SLUG = "api-design"  # content folder key + URL id; matches content/roadmaps/api-design/
TITLE = "API Design & Distributed APIs"
DESCRIPTION = "Foundational REST semantics, authentication protocols, and versioning strategies for backend engineers — the API contract, interview-scoped."

NODES = [
    # ---- REST Fundamentals ----
    ("REST Fundamentals", "Verbs & Actions", "GET vs POST semantics", "easy", "GET fetches data safely via URLs; POST creates new resources via body payloads without idempotency guarantees."),
    ("REST Fundamentals", "Verbs & Actions", "PUT vs PATCH updates", "medium", "PUT replaces the entire resource completely; PATCH applies partial modifications to an existing resource."),
    ("REST Fundamentals", "State & Reliability", "Idempotency mechanisms", "hard", "GET, PUT, and DELETE are idempotent; retrying failed POSTs without an idempotency key risks duplicate data creation."),
    ("REST Fundamentals", "Resource Naming", "Noun-based URI design", "easy", "URIs identify resources using nouns, not verbs, relying on standard HTTP methods to define the action taken."),
    ("REST Fundamentals", "Contract & State", "HTTP status codes", "medium", "2xx confirms success, 4xx rejects bad client data (401/403/404), and 5xx signals the server failed internally."),
    ("REST Fundamentals", "Data Flow", "Pagination & filtering", "medium", "Query parameters handle filtering and pagination, preventing large payloads from breaking clients or DB memory."),
    ("REST Fundamentals", "Contract & State", "Error response design", "medium", "A consistent error envelope (code, message, details) lets clients parse failures uniformly; see RFC 7807 problem+json."),
    ("REST Fundamentals", "Browser Contract", "CORS & preflight", "medium", "Browsers block cross-origin calls unless the server returns CORS headers; unsafe methods trigger a preflight OPTIONS first."),

    # ---- Auth & Authorization ----
    ("Auth & Authorization", "Identity Concepts", "AuthN vs AuthZ", "easy", "Authentication verifies identity via credentials; authorization checks roles/permissions to allow specific actions."),
    ("Auth & Authorization", "Tokens", "JWT statelessness & structure", "medium", "JWTs store state client-side; the signature verifies integrity, but the base64 payload is readable by anyone."),
    ("Auth & Authorization", "Tokens", "Access vs refresh tokens", "medium", "Short-lived access tokens limit theft impact; long-lived refresh tokens fetch new access tokens without relogging."),
    ("Auth & Authorization", "Security", "Token storage & XSS", "hard", "Storing tokens in localStorage exposes them to XSS; HttpOnly cookies block JS access but require CSRF guards."),
    ("Auth & Authorization", "Security", "BOLA / IDOR vulnerabilities", "hard", "BOLA occurs when an API fetches resources by client-provided ID without verifying the user owns that resource."),

    # ---- Versioning & Evolution ----
    ("Versioning & Evolution", "Lifecycle Management", "URI vs header versioning", "medium", "URI versioning routes via path (/v1/users); header versioning uses Accept headers to keep URLs clean."),
    ("Versioning & Evolution", "Lifecycle Management", "Backward compatibility", "hard", "Adding optional fields is safe; renaming, changing types, or removing fields breaks older, un-updated clients."),
    ("Versioning & Evolution", "Lifecycle Management", "Endpoint deprecation", "hard", "Sunsetting needs a deprecation window: communicate end-of-life dates via headers before removing the endpoint."),

    # ---- Protocol Choice & Interop ----
    ("Protocol Choice & Interop", "Choosing a Protocol", "REST vs gRPC vs GraphQL", "medium", "REST suits CRUD over HTTP; gRPC gives low-latency typed internal RPC; GraphQL lets clients fetch exactly the fields needed."),
    ("Protocol Choice & Interop", "Contract-First", "OpenAPI / Swagger", "medium", "An OpenAPI spec documents the contract and generates clients/servers; contract-first catches breaking changes before code."),

    # ---- Resilience & Distributed Contract ----
    ("Resilience & Distributed Contract", "Throttling", "Rate limiting & 429", "medium", "A throttled API returns 429 with Retry-After so clients back off — that contract, not the gateway's bucket algorithm."),
    ("Resilience & Distributed Contract", "Safe Retries", "Idempotency keys", "hard", "A client-sent Idempotency-Key lets the server dedupe retried POSTs, returning the first result instead of re-creating."),
    ("Resilience & Distributed Contract", "Event Delivery", "Webhooks & signatures", "hard", "Webhooks push events to a client URL; verify the HMAC signature and keep consumers idempotent since delivery retries."),
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
    print(f"Seeded '{TITLE}' with {len(NODES)} nodes (FOUNDATIONAL SLICE — see docstring).")


if __name__ == "__main__":
    asyncio.run(main())
