# Python Backend lesson generation — PROMPT (kind: engineering — FastAPI / ORM / testing / production)

> **North star (same as the rest):** *"Can the learner explain AND build this in an interview 30 days later?"*
> Backend engineering is **applied** — the concept only clicks when you see the code that runs it.
> This uses the existing **`kind: "engineering"`** schema (illustrative REAL CODE, **not executed in-browser** —
> it needs a server / a DB / threads, none of which exist in Pyodide). The code must be *correct and
> readable*, not runnable in the app. Do NOT write FastAPI docs — write the version that makes the
> request lifecycle / session lifecycle / test isolation *click* and leaves the learner able to draw it.
> Retention is the engine's job; the lesson is the hook.

You generate **one JSON per node** for the `python-backend` roadmap, `kind: "engineering"`. Topics +
slugs + which nodes to SKIP (reused from python-swe) are in `content/_TODO-backend.md`. Validate with
`python content/validate.py` (engineering branch — same schema, no changes needed). Write to
`content/roadmaps/python-backend/<slug>.json` (filename = slug).

**Gold reference for shape + depth:** `content/roadmaps/ai-engineering/embed-and-retrieve-top-k.json`.
Same template as `content/PROMPT-engineering.md` — everything below that differs is DOMAIN, not schema.

---

## THE TEMPLATE (field order = teaching order) — identical to PROMPT-engineering.md
| # | Field | Required? | Backend-specific guidance |
|---|---|---|---|
| 1 | `hook` | optional | A concrete production scene where this bites: a `500` at 2am from a lazy-load after commit; a page that fires 300 queries; a secret baked into a Docker layer on a public registry; a test suite green in CI but the app dead in prod. Skip if forced. |
| 2 | `mental_model` | **REQUIRED** | The analogy that makes it click. *"A session is a shopping cart — commit is checkout, and touching the cart after the store closed is MissingGreenlet." "Depends is a restaurant kitchen: the waiter doesn't cook, he declares what the dish needs." "N+1 is asking the librarian for one book, then going back 99 times instead of bringing the trolley."* |
| 3 | `sections` | **PREFERRED** | 4–7 blocks, ONE ~50–70-word idea each, `recap` checkpoints. Put a diagram/animation where the flow is genuinely spatial (request lifecycle, session lifecycle, worker model). |
| 4 | `code_snippets` | **REQUIRED, ≥1 (usually 2–3)** | THE POINT of this kind. See rules below. |
| 5 | `illustration` / `animation` | optional | `sequence` animations fit backend beautifully: request → middleware → router → dependency → handler → response; or session → query → commit → expire. Use them for lifecycle topics; skip for static ones. |
| 6 | `key_points` | optional | Discrete parts only (e.g. the 4 things a Depends can be; the 3 states of a session object). |
| — | `common_mistakes` | **REQUIRED, ≥1** | The classic production bug — see the ground-truth list below; prefer THOSE over generic mistakes. |
| 7 | `recall_questions` | **REQUIRED, ≥3** | tier1 = state it ("what does expire_on_commit do"), tier2 = debug it ("this endpoint 500s only after the first request — why"). |
| 8 | `oa_questions` | **REQUIRED, ≥2** | Real backend interview questions with `company` + `answer` + `approach`. The Step-1 question bank in `content/research/python-backend/nodes.md` maps every node to the question it answers — USE IT. |

**No `code_walkthrough`, no `understanding_checks`, no `formula`, no `method`** (those belong to other kinds).

## `code_snippets` — rules (backend edition)
- **Real APIs, current versions:** `fastapi`, `pydantic` **v2** (`model_config = ConfigDict(...)`, `field_validator` — NEVER v1 `class Config` / `@validator`), `sqlalchemy` 2.0 style (`select()`, not `Query`), `sqlmodel`, `pytest`, `httpx.AsyncClient`. A learner should be able to paste it into a project and have it work.
- **Build up in 2–3 snippets:** 1 = the naive/minimal version, 2 = the realistic version, 3 = the production form or the bug+fix pair. For pitfall topics (N+1, blocking-in-async, mutable state across requests) snippet 1 SHOULD BE the broken code, clearly labeled, with the fix as snippet 2.
- ~5–20 lines each, one idea per snippet, inline `# comments` that teach, 4-space indents, `\n`-escaped, single quotes inside code.
- `explanation` (1–3 sentences) = what to NOTICE — the invariant or the gotcha, not a restatement.

## Ground truth — bake these production facts in (they are this repo's own war stories)
Use these as the `common_mistakes` / snippet material for the matching lessons. They are verified, not folklore:
- **Sessions:** async session + lazy relationship access after the session closes → `MissingGreenlet`. Fix = `selectinload` at query time. `expire_on_commit=False` so objects stay readable after commit.
- **N+1:** loop over parents, touch `.children` → one query per row. Fix = eager load (`selectinload`) or join once.
- **Pydantic v2:** response schemas serializing ORM objects need `model_config = ConfigDict(from_attributes=True)`; v1 idioms are a rejected answer in 2026 interviews.
- **Blocking in async:** `time.sleep` / sync `requests` / sync DB driver inside `async def` freezes the whole event loop — every request, not just this one. Fix = `asyncio.sleep`, async clients, or `def` endpoint (FastAPI threadpools it).
- **`async def` vs `def` endpoints:** `def` runs in a threadpool (safe for sync libs); `async def` runs ON the loop (must never block).
- **Trailing slashes:** POST to `/items` when the route is `/items/` → 307 redirect; some clients drop the body.
- **Config:** secrets only via env (12-factor); pydantic-settings reads them; CORS is an explicit allow-list, never `*` with credentials.
- **Docker:** multi-stage = build deps in stage 1, copy only the venv/artifacts into a slim runtime stage; secrets must never be a layer.
- **Workers:** gunicorn manages N uvicorn workers = N event loops = N× memory; the GIL is why you scale with processes, not threads, for CPU-bound work.
- **Migrations:** schema changes via Alembic only; autogenerate then READ the diff — it misses renames (sees drop+add).
- **Testing:** override dependencies (`app.dependency_overrides`) instead of patching internals; async tests need an async test client (`httpx.AsyncClient` + ASGI transport), not `TestClient`, when the code under test awaits.

## Voice & scope guards
- Target learner: 0–2 yrs, prepping backend interviews + first 90 days on the job. Interview-signal first.
- Teach the CONCEPT through FastAPI/SQLAlchemy, don't tour the framework: "dependency injection" is the
  lesson; `Depends` is the vehicle. WSGI-vs-ASGI is a server-model lesson, not a uvicorn manual.
- Every claim testable; no version trivia, no benchmark numbers you can't source, no "it depends" hedging
  where a real answer exists.
- One lesson = one node = one JSON. Don't merge, don't add nodes.

## Self-check before writing each file
1. Could a learner answer this node's Step-1 interview question from this lesson alone? (bank: `content/research/python-backend/nodes.md`)
2. Is every code snippet something you would run in prod? (Pydantic v2? SQLAlchemy 2.0? async-safe?)
3. Does `common_mistakes` contain the REAL bug from the ground-truth list, if one matches?
4. `python content/validate.py` passes.
