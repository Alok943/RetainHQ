"""
Seed script: Web Development (full-stack) as a RetainHQ roadmap.

Per the design doc's Phase-3 caveat: web dev is partly a "build skill" where
commands/syntax fade fast and aren't ideal SR material. So this roadmap is
deliberately curated toward the CONCEPTS that DO reward spaced recall —
how Redux state flows, what a Dockerfile does, how JWT auth works — not
framework command memorisation.

Sub-tracks rendered as the step spine via `phase`.
Idempotent. Run: ./.venv/Scripts/python.exe seed_web_dev.py
"""
import asyncio
import uuid
from sqlalchemy import text
from app.core.database import engine

ROADMAP_ID = uuid.UUID("66666666-6666-6666-6666-666666666666")
TITLE = "Web Development — Full-Stack"
DESCRIPTION = "Full-stack web concepts that actually reward recall — the web model, JS internals, React data flow, API & auth design, and deployment fundamentals."

# (phase = sub-track, section, title, tier, recall hint)
NODES = [
    ("Web Fundamentals", "How the Web Works", "URL to rendered page", "easy", "DNS lookup, TCP/TLS, HTTP request, response, browser render."),
    ("Web Fundamentals", "How the Web Works", "HTTP methods & status codes", "easy", "GET/POST/PUT/PATCH/DELETE; 2xx/3xx/4xx/5xx families."),
    ("Web Fundamentals", "How the Web Works", "HTTPS & TLS basics", "medium", "Encryption + certificates; protects data in transit."),
    ("Web Fundamentals", "How the Web Works", "Client-server & REST principles", "easy", "Stateless, resource-based, uniform interface."),

    ("Frontend", "Markup & Style", "HTML semantics & accessibility", "easy", "Semantic tags; alt text; basic ARIA."),
    ("Frontend", "Markup & Style", "CSS box model, flexbox & grid", "easy", "content/padding/border/margin; 1D vs 2D layout."),
    ("Frontend", "JavaScript", "Types, scope & hoisting", "medium", "var/let/const; hoisting; temporal dead zone."),
    ("Frontend", "JavaScript", "Closures", "medium", "A function plus the lexical scope it captures."),
    ("Frontend", "JavaScript", "Event loop & async", "hard", "Call stack, microtask/callback queues; promises, async/await."),
    ("Frontend", "JavaScript", "The DOM & events", "easy", "Node tree; bubbling/capturing; event delegation."),
    ("Frontend", "React", "Components, props vs state", "easy", "Props = passed in (read-only); state = internal & mutable."),
    ("Frontend", "React", "Hooks: useState & useEffect", "medium", "State + side effects; the dependency array."),
    ("Frontend", "React", "Virtual DOM & reconciliation", "medium", "Diff the virtual tree, apply minimal real-DOM updates."),
    ("Frontend", "React", "How Redux state flows", "medium", "dispatch(action) -> reducer -> new store state -> re-render."),
    ("Frontend", "React", "SPA vs SSR vs SSG", "medium", "Client render vs server render vs build-time render."),

    ("Backend", "Server", "Routing & middleware", "easy", "Route maps path->handler; middleware = request pipeline."),
    ("Backend", "Server", "Request lifecycle", "medium", "Parse -> auth -> validate -> handle -> respond."),
    ("Backend", "API Design", "REST API design", "medium", "Resources, correct verbs/status, idempotency, versioning."),
    ("Backend", "API Design", "REST vs GraphQL", "medium", "Fixed endpoints vs client-specified queries."),
    ("Backend", "Patterns", "MVC pattern", "easy", "Model / View / Controller separation of concerns."),
    ("Backend", "Patterns", "ORM concept & N+1", "medium", "Objects <-> tables; watch the N+1 query trap."),

    ("Data", "Databases", "SQL vs NoSQL", "easy", "Relational/ACID vs flexible/scalable; pick by access pattern."),
    ("Data", "Databases", "Schema design basics", "medium", "Normalisation vs denormalisation tradeoffs."),
    ("Data", "Performance", "Indexing (concept)", "medium", "Speeds reads, costs writes and storage."),
    ("Data", "Performance", "Caching (concept)", "medium", "Cache-aside, TTL; invalidation is the hard part."),

    ("Auth & Security", "Identity", "Authentication vs authorization", "easy", "Who you are vs what you're allowed to do."),
    ("Auth & Security", "Identity", "Sessions vs JWT", "medium", "Server session + cookie vs signed stateless token."),
    ("Auth & Security", "Identity", "OAuth flow (concept)", "hard", "Delegated access: auth code -> access token."),
    ("Auth & Security", "Browser", "CORS", "medium", "Same-origin policy; server allow-list of origins."),
    ("Auth & Security", "Threats", "XSS, CSRF & SQL injection", "hard", "Sanitise input; anti-CSRF tokens; parameterised queries."),
    ("Auth & Security", "Threats", "Password storage", "medium", "Hash + salt (bcrypt); never store plaintext."),

    ("DevOps & Deploy", "Delivery", "What a container/Dockerfile does", "medium", "Packages app + deps into a portable, reproducible image."),
    ("DevOps & Deploy", "Delivery", "CI/CD concept", "medium", "Automated build -> test -> deploy pipeline."),
    ("DevOps & Deploy", "Config", "Environment config & secrets", "easy", "Env vars per environment; never commit secrets."),
    ("DevOps & Deploy", "Config", "Git essentials", "easy", "Commits, branches, merge vs rebase."),
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
