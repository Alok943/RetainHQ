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
- **`backend/`** — FastAPI (Python 3.10+), SQLModel + Alembic + asyncpg. Deployed on **Railway (Singapore region)** (root = `backend/`).
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
`Roadmaps.jsx` + `RoadmapDetail.jsx` (React Flow + dagre flowchart), `KnowledgeVault.jsx` (browse captured key-memories; client-side search), `Analytics.jsx`,
`Admin.jsx` (founder-only; funnel + feedback tabs, shown only when email === `ADMIN_EMAIL`), `Profile.jsx`, `Logo.jsx`, `lib/api.js` (`apiFetch` + `optionalAuth` for guest reads), `lib/supabase.js`, `lib/theme.jsx`, `lib/AuthContext.jsx` + `AuthModal` (PLG guest-exploration / `requireAuth()` gating). `vercel.json` = SPA rewrite (deep-link/OAuth 404 fix). (`NodeDrawer.jsx` = dead code.)

- **Dark mode:** `ThemeProvider` toggles a `.dark` class on `<html>` (persisted; pre-paint script in `index.html` avoids FOUC). Theming is a **centralized override layer in `index.css`** that remaps the app's hardcoded color utilities under `html.dark` — so new components inherit dark mode for free *if they reuse existing color classes*. The Login page is intentionally always-dark (theme-independent via inline styles). Logo variant is theme-aware in `App.jsx`.

---

## Data model (Postgres, UUID PKs, naive-UTC timestamps)

- **tracks** — user_id, name
- **activities** — user_id, track_id?, topic, notes?, difficulty(1–5), needed_hint, key_memory, mistake?, **source_type?**(problem/lecture/video/book/article/course/project/other — plain string, for filtering + future analytics), created_at, **ease_factor**(SM-2, default 2.5), **repetitions**(SM-2, default 0), **interval_days**(SM-2, default 0), **last_reviewed_at?**, **next_review_at?** (mirrors the open due review)
- **reviews** — user_id, activity_id, status('due'|'completed'), scheduled_for, completed_at?, rating?('easy'|'medium'|'hard'), **recalled?**(bool — objective got-it/missed-it, distinct from felt difficulty), **quality?**(int 0–5 — persisted SM-2 grade), **ai_verdict?**/**ai_recalled?**/**ai_feedback?** (LLM grader output, migration `c2f5a9b3d701`)
- **feedbacks** — user_id, message, status('new'|'reviewed'|'resolved'), created_at (user-submitted suggestions; admin-readable)
- **roadmaps** — title, description
- **roadmap_nodes** — roadmap_id, phase, section, title, tier, order_index, description?, **parent_id?** (self-ref → subtopics are completable child nodes)
- **user_progress** — user_id, node_id, status

## API (all `/api`, require Bearer JWT)

| Method & Path | Purpose |
|---|---|
| `GET /api/activities/` | List the user's captured activities (Knowledge Vault), newest first |
| `POST /api/activities/` | Create activity; initializes SM-2 state and schedules a **Day-0 baseline review due now** (every activity, no gate) |
| `GET /api/reviews/due` | Due reviews (status='due', scheduled_for ≤ now) with activity eager-loaded |
| `POST /api/reviews/{id}/complete` | Complete with `rating`(easy/med/hard, schema-constrained) + optional `recalled`; IDOR-protected (400 if done, 404 if not owned). **Advances SM-2 state and schedules the next review.** |
| `POST /api/reviews/{id}/grade` | **LLM grader** (gated on `GRADER_ENABLED`, else 404): grades free-recall answer vs `key_memory` → `{verdict, recalled, feedback, revision_note}`; persists `ai_*` on review. Advisory only. |
| `GET /api/dashboard/` | due_count, consistency_window, daily_progress, total_activities, total_reviews_completed |
| `GET /api/roadmaps/` | List with server-computed `progress_pct` |
| `GET /api/roadmaps/{id}` | Roadmap + nodes + per-node user status |
| `PUT /api/roadmaps/nodes/{id}/progress` | Idempotent upsert of done/not_started |
| `POST /api/feedback/` | Submit a feedback message (any authed user) |
| `GET /api/admin/funnel` | **Admin-only** activation funnel (signups→logged→reviewed→returned) + per-user + by-source, from existing data |
| `GET /api/admin/feedback` | **Admin-only** list of submitted feedback (joined to user email) |

## Core loop & metrics

- **Scheduling (SM-2):** every logged activity is one SM-2 "card" (state on the activity: `ease_factor`/`repetitions`/`interval_days`, plus denormalized `last_reviewed_at`/`next_review_at`). Logging schedules a **Day-0 baseline review due now** (proves the loop instantly, beats the "dead week"). Completing it starts the ladder: +1d → +6d → `round(interval × ease_factor)`. Each completion maps `rating`+`recalled` → quality 0–5 (`recalled=False`→2 lapse→reset to 1d; else hard/med/easy→3/4/5), persists `quality` on the review, and schedules the **next** review. On lapse `repetitions` resets to **1** (so the next pass jumps to 6d — avoids an awkward 1d→1d). Logic in `services/scheduler.py` (`initial_review_for_activity`, `quality_from_outcome`, `apply_sm2`). FSRS is the v2 successor.
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

- **Phase 0 done. Phase 1 core loop is now end-to-end wired through the UI:** `LogActivity.jsx` → `POST /api/activities/` → auto-scheduled reviews → `/reviews/due` → Review retrieval gate → `/complete` → dashboard. A real user can now create an activity and exercise everything downstream. (Backend `POST /api/activities/` already worked; the form is now connected: field state, `apiFetch`, submit gated on Topic+Key Memory, redirect to Home on success.)
- **Done since:** **SM-2 adaptive scheduling live** (every activity is a card; first review +1d → +6d → ×ease-factor; completion maps rating+recalled → quality and schedules the next review; state on `activities`, logic in `services/scheduler.py`, migration `a7c3d9e1b240`). **`LogActivity.jsx` wired** (Topic/Key Memory/Mistake/Difficulty/needed-hint → `POST /api/activities/`; redirect Home). Home/Roadmaps/Analytics wired to live data (Analytics shows real stats + honest "Phase 2" placeholders, no fabricated numbers). **Review flow wired with the retrieval gate** (commit-before-reveal: type a free-recall answer or "I don't know" before reveal; then key_memory + your attempt + prior mistake; Easy/Med/Hard rating). Dark mode (Profile toggle). Landing/Login redesigned. 10 roadmaps seeded + PDF export.
- **Done since:** **Knowledge Vault** (`KnowledgeVault.jsx` + `GET /api/activities/`) — browse all captured key-memories with client-side search; read-only for now. **Source Type** field on activities (`source_type`, Vault badge). **Activation funnel** — both `docs/funnel.sql` (Supabase SQL editor) **and** an in-app **Admin** page (`Admin.jsx`, founder-gated by `ADMIN_EMAIL`): `GET /api/admin/funnel` (signup→logged→reviewed→returned + per-user + by-source) and `GET /api/admin/feedback`. **User feedback** — Home "suggest a change" modal → `POST /api/feedback/` → `feedbacks` table (migration `b769ae00d904`) → Admin "User Feedback" tab.
- **Done since (deploy + PLG + grader session):** **DEPLOYED TO PRODUCTION** — frontend on Vercel (`retainhq.app`, apex + www), backend on **Railway (Singapore region** — moved from US to cut ~200ms/round-trip to Supabase Mumbai). `frontend/vercel.json` SPA rewrite fixes 404s on deep links / OAuth redirects. CORS allow-list = both `https://retainhq.app,https://www.retainhq.app`. **PLG "Try Before You Buy"** guest-exploration flow (`lib/AuthContext.jsx` + `AuthModal`, `optionalAuth` reads in `api.js`, `requireAuth()` gating on writes, localStorage draft persistence) — guests can browse roadmaps/explore before signing in. **LLM recall grader is now LIVE** (advisory): `POST /api/reviews/{id}/grade` (gated on `GRADER_ENABLED`) calls Groq, judges recalled-vs-missed vs `key_memory`, returns verdict + feedback + a short **revision note** (2–4 grounded bullets); persists `ai_verdict`/`ai_recalled`/`ai_feedback` on the review (migration `c2f5a9b3d701`). Wired into `Review.jsx` (AI box + "Suggested" rating chip; AI judges recall only — never auto-suggests Hard). **Home `next_review_at`** (dashboard returns soonest future review → "Next in Xd" when nothing due). Shimmer **skeletons** (Home/Vault/Roadmaps loading states). Dev "Copy JWT" button **removed** from `Profile.jsx`. Current cohort: 3 signups, 1 activated/reviewed/retained.
- **Next (high-leverage, in order):** (1) **set `GRADER_ENABLED=true` + valid `GROQ_API_KEY` on Railway** to flip the grader live in prod (currently shipped but gated off). (2) node-complete → pre-filled Log modal (design doc §9b — closes the roadmap→loop). (3) Logged Reviews Vault (review history) — post-launch. (4) grow `ActivityCreate` to actually persist Track/Roadmap/Activity-Type (currently UI-only). (5) feedback status workflow (new→reviewed→resolved) + full admin auth once past the first cohort. (6) rate limiting (slowapi) on write endpoints.
- **Phase 2:** FSRS scheduling (SM-2 done; rating+recalled feed it), real momentum/retention metrics, Re-entry Mode.

## Decisions / conventions (this build)
- **Product thesis:** "Track what you remember, not what you complete." Rule: **ship the mechanic, freeze the intelligence.** Goal = 20 real users + activation funnel. (Full rationale: user's design-decisions doc.)
- **Commits:** authored **solely by the user — NO `Co-Authored-By: Claude` trailer** (was explicitly removed from contributors). Work goes on `main` (solo, deploys from main).
- **Admin gate (interim):** founder-only access is an **email check**, not a full admin auth system. Backend `get_admin_user` (`api/deps.py`) 403s unless `current_user.email == settings.ADMIN_EMAIL` (env, default `aloksingh98541@gmail.com`); frontend mirrors it with `ADMIN_EMAIL` in `App.jsx` (UX only — backend is the real gate). Reads `auth.users` directly (the app DB role can). Good enough for the first cohort; revisit with real admin auth later.
- **LLM recall grader** = **shipped & wired, gated by `GRADER_ENABLED`** (default off in prod until env is set): `backend/app/services/grader.py` (Groq, one call → JSON `{verdict, recalled, feedback, revision_note}`, `groq>=0.11.0` now in main `dependencies`). Endpoint `POST /api/reviews/{id}/grade` (ownership + status='due' checked; `GraderError` → 503 → frontend silently skips). **Advisory only** — it judges recalled-vs-missed and writes a revision note; the user still picks felt difficulty (the AI never suggests Hard). Persists `ai_verdict`/`ai_recalled`/`ai_feedback` on `reviews`. Groq env: `GROQ_API_KEY`, `GROQ_MODEL` (default `llama-3.1-8b-instant`).
- **DB connection:** `DATABASE_URL` = Supabase **transaction pooler** (`postgres.<ref>:<pw>@aws-1-ap-south-1.pooler.supabase.com:6543/postgres`) → engine needs `statement_cache_size=0` + `prepared_statement_cache_size=0` (already set) and `pool_pre_ping=True`. Direct `db.<ref>.supabase.co` is IPv6-only → avoid. Gotchas hit while deploying: host shard is **`aws-1`** not `aws-0` (wrong shard → ENOTFOUND); repeated auth failures trip Supabase's **ECIRCUITBREAKER** (must stop deploying and wait ~minutes for it to re-arm — re-deploying keeps it tripped); use an **alphanumeric** DB password (special chars break the URL).
- **Deploy:** frontend **Vercel** (root=`frontend/`, `vercel.json` SPA rewrite required), backend **Railway** (root=`backend/`, **Singapore** region for latency). Env on Railway incl. `ADMIN_EMAIL`, CORS allow-list (apex+www), `GROQ_API_KEY`/`GRADER_ENABLED`. Run `alembic upgrade head` (DB head = `c2f5a9b3d701`).
- **Supabase MCP** (read-only) configured in `.mcp.json` — good for read-only DB verification.

## Known debt
- **`LogActivity.jsx` fields** = Topic, Source Type, Key Memory, Mistake?, Difficulty, needed-hint — all wired to `POST /api/activities/`. The unwired Track/Roadmap/Activity-Type/Retention selects (UI-only, two with hardcoded fake options) were **removed** to cut logging friction; re-add **real** Track/Roadmap pickers when the backend models them. `source_type` (problem/lecture/video/…) is a plain nullable string, surfaced as a Vault badge; consumed by analytics later. NOTE: post-SM-2, `difficulty`/`needed_hint` no longer gate scheduling (all activities schedule) — kept as cheap signals for future FSRS/metrics + Vault badges.
- Momentum / Retention Strength / Review Compliance are Phase-2 (Analytics shows them as labelled placeholders).
- Roadmap progress counts subtopics as nodes. DSA roadmaps are topic/problem-level, not full A2Z problem list.
- **Naive-UTC timestamps** rendered with `new Date(iso)` in the frontend (no `Z` suffix) → interpreted as local time. Cosmetic off-by-one on date *labels* possible near midnight for non-UTC users (IST); scheduling math is unaffected (interval counts from `last_reviewed_at`). Cleanup deferred.
