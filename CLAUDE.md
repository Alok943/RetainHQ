# RetainHQ — Project Context for Claude

A learning-retention web app (spaced repetition + active recall), **live in production at retainhq.app**. Solo-founder build.
Core loop: **Log Activity → Capture Key Memory → Schedule Reviews (FSRS) → Active Recall → Retain.** A growing library of interactive lessons (Python / SQL / DSA / aptitude / Core-CS / Physics) feeds cards into that loop.

Help like a pragmatic senior engineer: verify changes by running/testing before claiming done, be honest about tradeoffs (critique, don't rubber-stamp), keep scope tight, flag bugs/security proactively, match existing style.

---

## Where knowledge lives — read files, don't rely on chat memory

| You need… | Read |
|---|---|
| Current system state: architecture, API surface, schema, security, plans | **`docs/SYSTEM-OVERVIEW.md`** — the single living source of truth |
| Why a choice was made | `docs/DECISIONS.md` (2026-07-10 onward); older rationale in the archive below |
| Unprioritized ideas / "we should also…" items | `docs/BACKLOG.md` |
| How to run Claude Code sessions on this repo (session names, token discipline) | `docs/claude-code-workflow.md` |
| Pre-2026-07-10 history, build log, detailed feature rationale | `docs/CLAUDE-ARCHIVE-2026-07.md` (frozen copy of the old CLAUDE.md) |
| Lesson content contracts | `content/PROMPT-*.md`, gate = `content/validate.py` |
| Design system | `docs/design-bible.md` |

`ARCHITECTURE.md` / `API.md` / `FLOWS.md` are legacy and stale — trust SYSTEM-OVERVIEW over them.

## Update routing rules — if X changes, update Y **in the same commit**

| When you… | You MUST… |
|---|---|
| Add/remove an endpoint or router · touch `models/models.py` or add a migration · add a service/integration (LLM, email, analytics…) · change deploy topology/env · move the security posture | Update the relevant section of `docs/SYSTEM-OVERVIEW.md` **+ one line in its Changelog**, same commit. Prod-state claims (migration head, catalog counts) must be verified via the read-only Supabase MCP, never assumed |
| Make a non-obvious product/architecture decision | Append an entry to `docs/DECISIONS.md` (what / why / tradeoffs / date) |
| Hit a new idea mid-task ("we should also…") | Add one line to `docs/BACKLOG.md` and return to the task — don't derail the session |
| Add or edit lesson JSON under `content/` | It must pass `content/validate.py`; `sync-content.mjs` copies to `frontend/public/content/` on predev/prebuild |
| Change how sessions/docs are organized | Update `docs/claude-code-workflow.md` |
| Feel tempted to log status or history **here** | **Don't.** CLAUDE.md carries no status. State → SYSTEM-OVERVIEW; history → git + the archive |

---

## Architecture (monorepo)

```
React SPA (Vercel, root=frontend/)  ←  retainhq.app
  ├─ Supabase Auth (Google OAuth) ──► ES256 JWT
  └─ apiFetch + Bearer JWT ──► FastAPI (Render, root=backend/) ──asyncpg──► Supabase Postgres (Mumbai, pooler :6543)
```

- The frontend talks **only** to FastAPI via `frontend/src/lib/api.js` (`apiFetch` attaches the JWT; `optionalAuth` = guest reads). Never add direct `supabase.from(...)` DB calls in React — Supabase on the client is auth-only.
- FastAPI is the single DB gateway. Heavy interactive compute is client-side (Pyodide, PGlite, pure-JS DSA trace player) — zero server compute for lessons.
- Full topology, routers, schema (12 tables), and env vars: `docs/SYSTEM-OVERVIEW.md` §1–2.

## Critical conventions — FOLLOW THESE

- **Auth:** Supabase Google OAuth → **ES256** JWT; FastAPI verifies via `PyJWKClient`/JWKS. Never rebuild OAuth; never use HS256. `get_current_user` returns `SupabaseUser` (attribute access `.id`, not a dict). Cast JWT `sub` (string) to `uuid.UUID` before queries.
- **Authorization:** every query scoped by `current_user.id`; mutating endpoints verify ownership (`WHERE id = :id AND user_id = :uid` — IDOR protection).
- **Async DB gotchas:** eager-load relationships with `selectinload` (lazy access on a closed async session → MissingGreenlet crash); sessions use `expire_on_commit=False`.
- **Pydantic v2:** response schemas serializing ORM objects need `model_config = ConfigDict(from_attributes=True)`.
- **Schema changes:** always via Alembic — never hand-edit the live DB. Every new table's migration MUST include `ENABLE ROW LEVEL SECURITY` (no policies) to block Supabase's PostgREST/anon-key path; the backend connects as `postgres` (owner) and bypasses RLS.
- **DB connection:** `DATABASE_URL` = Supabase **transaction pooler** (`aws-1-ap-south-1…:6543`) → engine needs `statement_cache_size=0`, `prepared_statement_cache_size=0`, `pool_pre_ping=True` (already set). Direct `db.<ref>` host is IPv6-only — avoid. Alphanumeric DB password only; repeated auth failures trip Supabase's ECIRCUITBREAKER (stop and wait, don't redeploy).
- **Secrets:** only in `.env` (git-ignored). CORS is an explicit allow-list, never `*`.
- **Trailing slashes:** collection POST routes use trailing slash (`/api/activities/`); call exact paths to avoid 307s.
- **Dark mode:** centralized override layer in `index.css` remaps hardcoded color utilities under `html.dark` — new components inherit dark mode for free **if they reuse existing color classes**. Login page is intentionally always-dark.
- **Timestamps:** naive-UTC in the DB; frontend renders with `new Date(iso)` (known cosmetic off-by-one near midnight IST — deferred).

## Working agreements

- **Commits:** authored solely by the user — **NO `Co-Authored-By: Claude` trailer**. Work on `main` (solo; deploys from main). **Never push/deploy without an explicit "push" from the user** — pushing main triggers Vercel + Render.
- **Content pipeline:** bulk lesson generation is delegated to **Antigravity, not Claude**. Claude owns the contracts (`schema`/`validate.py`/`PROMPT-*`), the runtime/renderer, and **critiquing** output (validator checks structure only; someone must check lessons actually teach).
- **Admin gate (interim):** email check — `get_admin_user` 403s unless `current_user.email == ADMIN_EMAIL`. `DEV_AUTH_BYPASS` is boot-guarded behind `DEBUG=true`.
- **Product thesis:** "Track what you remember, not what you complete." Retention engine is the moat; lessons are the hook. Out-teach YouTube+docs for the AI-assisted coder via docs-as-truth lessons, step-through execution, predict-before-reveal.

## Dev commands

```bash
# backend  → http://localhost:8000/docs
cd backend && .\.venv\Scripts\Activate.ps1 && uvicorn app.main:app --reload
cd backend && alembic upgrade head            # apply migrations
cd backend && alembic revision -m "msg"       # new migration

# frontend → http://localhost:5173
cd frontend && npm run dev
```

Env: `VITE_API_BASE_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` (frontend); `DATABASE_URL`, `SUPABASE_JWT_SECRET`, `SUPABASE_URL` (backend).

## Layout pointers (details in SYSTEM-OVERVIEW §1)

- `backend/app/` — `main.py` (app+CORS+routers), `core/` (config/database/security), `api/routes/`, `services/` (`scheduler.py` FSRS, `grader.py` Groq LLM, `mailer.py`, `reminders.py`), `models/models.py` (**schema source of truth**), `alembic/versions/`.
- `frontend/src/` — `App.jsx` shell, pages (`Home`, `LogActivity`, `Review`, `Roadmaps`/`RoadmapDetail`, `KnowledgeVault`, `LessonView`, `Analytics`, `Admin`, `CareerPaths`), `lib/` (`api.js`, `AuthContext.jsx`, `theme.jsx`), `dsa/` (Claude-owned trace-viz player: generators → compile.js → renderers).
- `content/roadmaps/<roadmapKey>/<slug>.json` — one lesson per node; kinds: `concept` / `aptitude` / `reasoning` / `theory` / `dsa`, each with its own `PROMPT-*.md`.
