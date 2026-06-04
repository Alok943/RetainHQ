# RetainHQ — Project Context for Claude

A learning-retention web app: spaced repetition + active recall. Solo-founder build.
Goal: own the entire learning loop — **Log Activity → Capture Key Memory → Schedule Reviews → Active Recall → Retain** — so knowledge sticks. Immediate priority is validating the core loop with real users, not adding features.

Help like a pragmatic senior engineer: verify changes by running/testing before claiming done, be honest about tradeoffs, keep scope tight, flag bugs/security proactively, match existing style.

---

## Architecture (monorepo)

```
React SPA (Vercel)
  ├─ Supabase Auth (Google OAuth) ──► ES256 JWT
  └─ apiFetch + Bearer JWT ──► FastAPI (Render/Railway) ──asyncpg──► Supabase Postgres
```

- **`frontend/`** — React + Vite + Tailwind. Deployed on Vercel (root = `frontend/`).
- **`backend/`** — FastAPI (Python 3.10+), SQLModel + Alembic + asyncpg. Deployed on Render/Railway (root = `backend/`).
- **Supabase** — Postgres database + Google OAuth (identity provider only).

The frontend talks **only** to FastAPI; Supabase is auth + managed Postgres. FastAPI is the single gateway to the DB.

---

## Critical conventions — FOLLOW THESE

- **Auth:** Frontend signs in via Supabase (Google) → **ES256** JWT. FastAPI verifies via `PyJWKClient`/JWKS (requires `pyjwt[crypto]` → `cryptography`). Never rebuild OAuth; never use HS256. `get_current_user` returns a `SupabaseUser` (attribute access `.id`, not a dict).
- **One data path:** React calls the backend through `frontend/src/lib/api.js` (`apiFetch`, which attaches the Bearer JWT). Do **not** add direct `supabase.from(...)` DB calls in React.
- **Async DB gotchas:** eager-load relationships with `selectinload` (lazy access on a closed async session → MissingGreenlet crash); session uses `expire_on_commit=False`; cast JWT `sub` (string) to `uuid.UUID` before queries.
- **Authorization:** every query scoped by `current_user.id`; mutating endpoints verify ownership (IDOR protection: `WHERE id = :id AND user_id = :uid`).
- **Pydantic v2:** response schemas serializing ORM objects need `model_config = ConfigDict(from_attributes=True)`.
- **Schema changes:** always via Alembic migrations — never hand-edit the live DB.
- **Secrets:** only in `.env` (git-ignored). Never commit. CORS is an explicit allow-list, not `*`.
- **Trailing slashes:** collection POST routes use trailing slash (`/api/activities/`); call exact paths to avoid 307 redirects.

---

## Backend layout (`backend/app/`)

- `main.py` — app, CORS, router mounts, `/health`, `/me`
- `core/config.py` — pydantic-settings (env)
- `core/database.py` — async engine + `async_session_maker` (`expire_on_commit=False`)
- `core/security.py` — `SupabaseUser`, `verify_token` (JWKS/ES256)
- `api/deps.py` — `get_db`, `get_current_user`
- `api/routes/` — `activities.py`, `reviews.py`, `dashboard.py`, `roadmaps.py`
- `schemas/` — Pydantic request/response models
- `services/scheduler.py` — review scheduling logic
- `models/models.py` — **single source of truth for the schema**
- `alembic/versions/` — migrations
- `seed_striver_a2z.py`, `seed_a2z_content.py` — roadmap seed scripts (dev)

## Frontend layout (`frontend/src/`)

`App.jsx` (shell/routing), `Login.jsx`, `Home.jsx`, `LogActivity.jsx`, `Review.jsx`,
`Roadmaps.jsx` + `RoadmapDetail.jsx` (React Flow + dagre flowchart), `Analytics.jsx`,
`Profile.jsx`, `Logo.jsx`, `lib/api.js`, `lib/supabase.js`, `lib/theme.jsx`. (`NodeDrawer.jsx` = dead code.)

- **Dark mode:** `ThemeProvider` toggles a `.dark` class on `<html>` (persisted; pre-paint script in `index.html` avoids FOUC). Theming is a **centralized override layer in `index.css`** that remaps the app's hardcoded color utilities under `html.dark` — so new components inherit dark mode for free *if they reuse existing color classes*. The Login page is intentionally always-dark (theme-independent via inline styles). Logo variant is theme-aware in `App.jsx`.

---

## Data model (Postgres, UUID PKs, naive-UTC timestamps)

- **tracks** — user_id, name
- **activities** — user_id, track_id?, topic, notes?, difficulty(1–5), needed_hint, key_memory, mistake?, created_at
- **reviews** — user_id, activity_id, status('due'|'completed'), scheduled_for, completed_at?, rating?('easy'|'medium'|'hard'), **recalled?**(bool — objective got-it/missed-it, distinct from felt difficulty)
- **roadmaps** — title, description
- **roadmap_nodes** — roadmap_id, phase, section, title, tier, order_index, description?, **parent_id?** (self-ref → subtopics are completable child nodes)
- **user_progress** — user_id, node_id, status

## API (all `/api`, require Bearer JWT)

| Method & Path | Purpose |
|---|---|
| `POST /api/activities/` | Create activity; auto-schedules 4 reviews (+3/+7/+14/+30d) if difficulty ≥ 4 **or** needed_hint |
| `GET /api/reviews/due` | Due reviews (status='due', scheduled_for ≤ now) with activity eager-loaded |
| `POST /api/reviews/{id}/complete` | Complete with `rating`(easy/med/hard, schema-constrained) + optional `recalled`; IDOR-protected (400 if done, 404 if not owned) |
| `GET /api/dashboard/` | due_count, consistency_window, daily_progress, total_activities, total_reviews_completed |
| `GET /api/roadmaps/` | List with server-computed `progress_pct` |
| `GET /api/roadmaps/{id}` | Roadmap + nodes + per-node user status |
| `PUT /api/roadmaps/nodes/{id}/progress` | Idempotent upsert of done/not_started |

## Core loop & metrics

- **Scheduling:** difficulty ≥ 4 OR needed_hint → 4 reviews at +3/+7/+14/+30 days (fixed in v1; adaptive Easy/Med/Hard in v2).
- **Learning Momentum** = 40% Consistency + 25% Completion + 20% Review Compliance + 15% Balance.
- **Retention Strength:** Mastered ≥90%, Strong 75–89%, Developing 50–74%, Weak <50% (recall: Easy=100, Med=70, Hard=30).
- **Roadmaps:** React Flow + dagre flowchart. Left-click=complete, right-click=notes/link, double-click=subtopics. Camera follows progress. **Download PDF** button (jsPDF, styled). **10 seeded roadmaps** (each has a `seed_*.py`, idempotent, fixed UUID): Python for SWE, DSA—Striver A2Z, DSA—NeetCode 150 (links to neetcode.io), Core CS (OS/DBMS/Networks), Aptitude, Web Dev, System Design, Python Backend, SQL, AI Engineering. DSA is language-independent (no C++/Java split). `phase`=sub-track (step spine), `tier`∈{easy,medium,hard}.

---

## Dev commands

```bash
# backend
cd backend && .\.venv\Scripts\Activate.ps1 && uvicorn app.main:app --reload   # http://localhost:8000/docs
cd backend && alembic upgrade head            # apply migrations
cd backend && alembic revision -m "msg"       # new migration

# frontend
cd frontend && npm run dev                     # http://localhost:5173
```

Env: `VITE_API_BASE_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` (frontend);
`DATABASE_URL`, `SUPABASE_JWT_SECRET`, `SUPABASE_URL` (backend).

---

## Status & next priorities

- **Phase 0 + Phase 1 (core loop): complete & validated.**
- **Done since:** Home/Roadmaps/Analytics wired to live data (Analytics shows real stats + honest "Phase 2" placeholders, no fabricated numbers). **Review flow wired with the retrieval gate** (commit-before-reveal: type a free-recall answer or "I don't know" before reveal; then key_memory + your attempt + prior mistake; Easy/Med/Hard rating). Dark mode (Profile toggle). Landing/Login redesigned. 10 roadmaps seeded + PDF export.
- **Next (high-leverage):** wire **node-complete → pre-filled Log modal** (design doc §9b — closes the roadmap→loop); funnel/activation events; then SM-2.
- **Phase 2:** SM-2 then FSRS scheduling (rating+recalled already captured for it), real momentum/retention metrics, Re-entry Mode.

## Decisions / conventions (this build)
- **Product thesis:** "Track what you remember, not what you complete." Rule: **ship the mechanic, freeze the intelligence.** Goal = 20 real users + activation funnel. (Full rationale: user's design-decisions doc.)
- **Commits:** authored **solely by the user — NO `Co-Authored-By: Claude` trailer** (was explicitly removed from contributors). Work goes on `main` (solo, deploys from main).
- **LLM recall grader** = frozen/dormant: `backend/app/services/grader.py` (Groq, one call, grades free recall vs `key_memory`), behind `GRADER_ENABLED` flag + optional `[experiment]` extra. Not wired into the review endpoint. Groq env: `GROQ_API_KEY`, `GROQ_MODEL`.
- **DB connection:** `DATABASE_URL` = Supabase **transaction pooler** (`...pooler.supabase.com:6543`) → engine needs `statement_cache_size=0` + `prepared_statement_cache_size=0` (already set) and `pool_pre_ping=True`. Direct `db.<ref>.supabase.co` is IPv6-only → avoid.
- **Supabase MCP** (read-only) configured in `.mcp.json` — good for read-only DB verification.

## Known debt
- Momentum / Retention Strength / Review Compliance are Phase-2 (Analytics shows them as labelled placeholders).
- Dev "Copy JWT" button in `Profile.jsx` pending pre-prod cleanup.
- Roadmap progress counts subtopics as nodes. DSA roadmaps are topic/problem-level, not full A2Z problem list.
