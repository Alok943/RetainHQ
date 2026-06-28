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
- **activities** — user_id, track_id?, **roadmap_id?**(FK→roadmaps, ON DELETE SET NULL — optional link surfaced as the Log-form roadmap picker; migration `f4a9c2e1b370`), topic, notes?, difficulty(1–5), needed_hint, **key_memory**(capped at 500 chars in `ActivityCreate` — one testable claim, not a dump), mistake?, **source_type?**(problem/lecture/video/book/article/course/project/**lesson**/other — plain string, for filtering + future analytics), **node_id?**(FK→roadmap_nodes, ON DELETE SET NULL — the lesson a card came from via "Add to reviews"; idempotent one-card-per-(user,node); migration `a4b2e9f1c8d3`), created_at, **FSRS state: stability?/difficulty_fsrs?** (FSRS-4.5; NULL until first graded review = new card; migration `a1b2c3d4e5f6`), **interval_days**, **last_reviewed_at?**, **next_review_at?** (mirrors the open due review), **ease_factor/repetitions** (legacy SM-2 columns, still written so old rows + NOT NULL keep working). NOTE: `difficulty_fsrs` (1–10) ≠ `difficulty` (user's 1–5 self-rating).
- **reviews** — user_id, activity_id, status('due'|'completed'), scheduled_for, completed_at?, rating?('easy'|'medium'|'hard'), **recalled?**(bool — objective got-it/missed-it, distinct from felt difficulty), **quality?**(int 0–5 — persisted SM-2 grade), **ai_verdict?**/**ai_recalled?**/**ai_feedback?** (LLM grader output, migration `c2f5a9b3d701`)
- **feedbacks** — user_id, message, status('new'|'reviewed'|'resolved'), created_at (user-submitted suggestions; admin-readable)
- **roadmaps** — **slug**(unique URL id = content folder key, e.g. `aptitude`/`python-swe`; migration `a3f1c0d4e7b2`; set by each `seed_*.py` for the 3 content roadmaps + backfilled for all 20 — `GET /api/roadmaps/{ref}` resolves slug-or-UUID so old links still work; frontend routes by slug → `/roadmaps/aptitude/learn/<lesson-slug>`), title, description
- **roadmap_nodes** — roadmap_id, phase, section, title, tier, order_index, description?, **parent_id?** (self-ref → subtopics are completable child nodes)
- **user_progress** — user_id, node_id, status

## API (all `/api`, require Bearer JWT)

| Method & Path | Purpose |
|---|---|
| `GET /api/activities/` | List the user's captured activities (Knowledge Vault), newest first |
| `POST /api/activities/` | Create activity (optional `roadmap_id`/`node_id` link); initializes FSRS card and schedules the **first review tomorrow** (or **due now** for the user's first-ever activity = onboarding demo). Returns `review_due_now`. **`source_type='lesson'` cards are idempotent per `node_id`** (the lesson "Add to reviews" bridge). |
| `POST /api/activities/suggest-key-points` | **Capture assist** (gated, else 404): given `{topic, draft?}` → `{points[]}`, the core sub-points under the topic so a stuck user can recognize + keep what they learned. Suggestion only, never auto-applied. 503 on LLM failure. |
| `GET /api/reviews/due` | Due reviews (status='due', scheduled_for ≤ now) with activity eager-loaded. **Capped at `REVIEW_SESSION_CAP` (10), oldest-first; overflow rolls forward.** |
| `POST /api/reviews/{id}/complete` | Complete with `rating`(easy/med/hard, schema-constrained) + optional `recalled`; IDOR-protected (400 if done, 404 if not owned). **Advances FSRS state and schedules the next review.** |
| `POST /api/reviews/{id}/grade` | **LLM grader** (gated on `GRADER_ENABLED`, else 404): grades free-recall answer vs `key_memory` → `{verdict, recalled, feedback, revision_note, related_subtopics}`; persists `ai_*` on review. Advisory only. |
| `POST /api/reviews/{id}/questions` | **Question mode** (gated, else 404): generate 2–3 short-answer questions grounded in `key_memory`. 503 on LLM failure → UI falls back to free recall. |
| `POST /api/reviews/{id}/grade-questions` | **Question mode** (gated): grade the answer set vs `key_memory` → `{recalled, feedback, items[], related_subtopics}`; persists `ai_*`. Advisory only. |
| `GET /api/dashboard/` | due_count (capped at `REVIEW_SESSION_CAP`), consistency_window, daily_progress, total_activities, total_reviews_completed, next_review_at |
| `GET /api/roadmaps/` | List with server-computed `progress_pct` (+ `slug`) |
| `GET /api/roadmaps/{id-or-slug}` | Roadmap + nodes + per-node user status (resolves by slug OR UUID) |
| `PUT /api/roadmaps/nodes/{id}/progress` | Idempotent upsert of done/not_started |
| `POST /api/feedback/` | Submit a feedback message (any authed user) |
| `GET /api/admin/funnel` | **Admin-only** activation funnel (signups→logged→reviewed→returned) + per-user + by-source, from existing data |
| `GET /api/admin/feedback` | **Admin-only** list of submitted feedback (joined to user email) |

## Core loop & metrics

- **Scheduling (FSRS):** every logged activity is one **FSRS** "card" — state on the activity is `stability`/`difficulty_fsrs` (FSRS-4.5; both **NULL until the first graded review** = a new card), plus denormalized `interval_days`/`last_reviewed_at`/`next_review_at`. FSRS models stability (days-to-target-decay) + difficulty (1–10) instead of SM-2's fixed ease ladder; each completion updates both from the **elapsed** time since last review + the grade, then picks the next interval so predicted recall = `DESIRED_RETENTION` (0.9). ~30% fewer reviews than SM-2 for the same retention. **First-review timing is unchanged:** logging schedules the **first review for tomorrow** (+1d); the user's **first-ever** activity gets a **demo review due now** (`initial_review_for_activity(immediate=True)`) as the onboarding aha — one-time, not per-log. `rating`+`recalled` → FSRS grade via `fsrs_rating_from_outcome` (1=Again/2=Hard/3=Good/4=Easy; a miss is always Again). `quality` (0–5, `quality_from_outcome`) is still persisted for analytics, but FSRS uses the 1–4 grade. **Legacy SM-2 columns** (`ease_factor`/`repetitions`) are still written so old rows + NOT NULL constraints keep working. **Daily cap:** `REVIEW_SESSION_CAP` (10) bounds both the due queue and dashboard `due_count` (oldest-first; overflow rolls forward) — kills the unbounded-backlog "23 due" death spiral. Logic in `services/scheduler.py` (`initial_review_for_activity`, `fsrs_rating_from_outcome`, `apply_fsrs`, `FSRS_WEIGHTS`, `REVIEW_SESSION_CAP`). Migration `a1b2c3d4e5f6` added the FSRS columns.
- **Learning Momentum** = 40% Consistency + 25% Completion + 20% Review Compliance + 15% Balance.
- **Retention Strength:** Mastered ≥90%, Strong 75–89%, Developing 50–74%, Weak <50% (recall: Easy=100, Med=70, Hard=30).
- **Roadmaps:** React Flow + dagre flowchart. Left-click=complete, right-click=notes/link, double-click=subtopics. Camera follows progress. **Download PDF** button (jsPDF, styled). **10 seeded roadmaps** (each has a `seed_*.py`, idempotent, fixed UUID): Python for SWE, DSA—Striver A2Z, DSA—NeetCode 150 (links to neetcode.io), Core CS (OS/DBMS/Networks), Aptitude, Web Dev, System Design, Python Backend, SQL, AI Engineering. DSA is language-independent (no C++/Java split). `phase`=sub-track (step spine), `tier`∈{easy,medium,hard}.
- **Roadmap backlog (candidates to seed, not built yet):** next-3 by leverage = **DSA Blind 75 / patterns**, **Low-Level Design (LLD/OOD)**, **Git & GitHub**. Others: Behavioral+HR interview, DevOps & Cloud (Docker/CI/CD/K8s/AWS), Linux & Shell, TypeScript, React (deep), API Design, Testing, Machine Learning (Andrew Ng), Deep Learning, GenAI/LLM apps (RAG/agents), Math for ML, Data Analytics, Data Engineering, Java for SWE, C++/CP, Resume + Job Hunt. (Build via the `seed_*.py` pattern: idempotent, fixed UUID, `phase`/`tier` nodes.)

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
- **Done since (anti-fatigue redesign):** first review **deferred to tomorrow** (instant-quiz fatigue fix) with a **first-ever-activity demo review** exception (preserves activation aha); **daily review session cap** (`REVIEW_SESSION_CAP=10`) on queue + dashboard count, overflow rolls forward (kills the "23 due" spiral); session-framed Review header ("Today's review · N cards · ~M min"); copy cleanup (Home/FirstCapture/LogActivity/OnboardingGuide/Login) and post-log success states. **Question-mode prototype** (gated): grounded question gen + set grading (`grader.py` `generate_questions`/`grade_question_set`, two new endpoints, `Review.jsx` additive UI, free recall = fallback). **Related-subtopics** suggestions on both grade paths (highlighted callout). **Grader default model → `openai/gpt-oss-120b`** with `reasoning_effort=low` handling. No DB migration (all scheduling-logic + gated-LLM). *Live LLM path still unexercised — needs `GRADER_ENABLED=true` + `GROQ_API_KEY` to validate question/subtopic quality.*
- **Done since (capture-assist + roadmap link):** **Key Memory 500-char cap** + counter. **Capture assist** (gated, log-time): on-demand "Suggest key points" → `suggest_key_points()` + `POST /api/activities/suggest-key-points`; recognition prompts the user inserts, never auto-applied (`apiFetch` now carries `err.status`). **Activity→roadmap link** (`roadmap_id`, migration `f4a9c2e1b370`): Log-form roadmap picker, in-progress roadmaps first; replaced the dead "Coming Soon" card (+ removed its orphaned feedback modal). *UI restyle deferred (user is doing it via Claude design); node-level roadmap link still future.*
- **Done since (coding-education pillar — the white-space build):** **FSRS live** (replaced SM-2; `stability`/`difficulty_fsrs`; migration `a1b2c3d4e5f6`). **Dependency graph** — `roadmap_node_prerequisites` (migration `b2c3d4e5f6a7`; 70 edges seeded by title via `seed_python_swe_prereqs.py`), exposed as `prerequisites`/`unlocks`, plus **"Why am I stuck?"** diagnosis (`GET /api/roadmaps/{id}/blockers` → ready-frontier ranked by transitive unlocks; panel in `RoadmapDetail.jsx`). **Node-anchored lesson view** (`LessonView.jsx` @ `/roadmaps/:id/learn/:slug`; a "Learn" affordance on nodes that have content — NOT a separate tab) rendering overview/why/mistakes/recall/practice/challenge/sources. **Client-side Python visualizer** (`CodeTrace.jsx` + `lib/pyodideRunner.js`: lazy Pyodide + `sys.settrace` step scrubber, zero server compute). **Predict-before-reveal "aha moments"** (guess → run in the visualizer → why; output is never stored — runtime is truth). **Lesson content system** (`content/`): one JSON per node at `content/roadmaps/<roadmapKey>/<slug>.json`, validated by `content/validate.py` (**the gate — branches by `kind`**), synced to `frontend/public/content/` by `sync-content.mjs` (`predev`/`prebuild`). `LessonView.jsx` renders by **`kind`**: **`concept`** = python (Pyodide `code_walkthrough` + `understanding_checks`) / sql (PGlite `query_walkthrough`); **`aptitude`** = THIN (hook·mental_model·*pattern_discovery?*·formula·shortcuts·recall·oa — retention is the engine's job, not the lesson's); **`reasoning`** = method-based (mental_model·method·worked_example·recall·oa, for Logical/Verbal); **`theory`** = Core CS, DEEP (analogy·*process animation?*·a teach-from-scratch `explanation`·key_points·recall·oa — the lesson IS the learning resource, so depth is required, NOT thin). Each kind has its own `content/PROMPT-*.md` + `_TODO-*.md`. **Process animations** (`theory`): structured `animation` metadata (`actors`+directed `steps`, `type` `sequence`|`cycle`) → dependency-free SVG (`ProcessAnimation` in `LessonView.jsx`); content-as-single-source-of-truth (NO Lottie/Rive). **Content→review bridge:** the lesson "Add to reviews" button creates an FSRS card (`source_type='lesson'` + `activities.node_id`, idempotent; migration `a4b2e9f1c8d3`) so lesson recall enters the spaced-repetition loop. **Bulk generation is delegated to Antigravity, NOT Claude — Claude owns the contracts (schema/validate.py/PROMPT-*), the runtime/renderer, and critiquing output** (validator checks structure only; a human/Claude must check that lessons actually teach + that `method`s transfer). Content live: **python-swe** (full), **sql** (full), **aptitude** (quant 24 + logical-reasoning 11; verbal/vocab pending), **core-cs** (`theory`, OS batch in progress). Lesson URLs are slug-based: `/roadmaps/<slug>/learn/<lesson-slug>`.
- **Next (high-leverage, in order):** (1) **set `GRADER_ENABLED=true` + `GROQ_API_KEY` + `GROQ_MODEL=openai/gpt-oss-120b` on Railway** to flip grader + question mode live, and validate question/subtopic quality on real cards. (2) node-complete → pre-filled Log modal (design doc §9b — closes the roadmap→loop). (3) Logged Reviews Vault (review history) — post-launch. (4) grow `ActivityCreate` to actually persist Track/Roadmap/Activity-Type (currently UI-only). (5) feedback status workflow (new→reviewed→resolved) + full admin auth once past the first cohort. (6) rate limiting (slowapi) on write endpoints.
- **Phase 2:** real momentum/retention metrics, Re-entry Mode. (FSRS scheduling — was Phase 2 — is now **live**; migration `a1b2c3d4e5f6`.)

## Decisions / conventions (this build)
- **Product thesis:** "Track what you remember, not what you complete." The bet: out-teach YouTube + docs for the **AI-assisted coder** — someone who can prompt code but can't yet read, debug, or reason about it. We do it by stacking three pillars on the retention engine: **docs-as-truth lessons, step-through (Pyodide) execution, and predict-before-reveal "aha" moments.** Retention is the moat; the lessons are the hook. *"Bloomberg Terminal for your memory."*
- **Commits:** authored **solely by the user — NO `Co-Authored-By: Claude` trailer** (was explicitly removed from contributors). Work goes on `main` (solo, deploys from main).
- **Admin gate (interim):** founder-only access is an **email check**, not a full admin auth system. Backend `get_admin_user` (`api/deps.py`) 403s unless `current_user.email == settings.ADMIN_EMAIL` (env, default `aloksingh98541@gmail.com`); frontend mirrors it with `ADMIN_EMAIL` in `App.jsx` (UX only — backend is the real gate). Reads `auth.users` directly (the app DB role can). Good enough for the first cohort; revisit with real admin auth later.
- **LLM recall grader** = **shipped & wired, gated by `GRADER_ENABLED`** (default off in prod until env is set): `backend/app/services/grader.py` (Groq, one call → JSON `{verdict, recalled, feedback, revision_note, related_subtopics}`, `groq>=0.11.0` now in main `dependencies`). Endpoint `POST /api/reviews/{id}/grade` (ownership + status='due' checked; `GraderError` → 503 → frontend silently skips). **Advisory only** — judges recalled-vs-missed + revision note; user still picks felt difficulty (AI never suggests Hard). Persists `ai_verdict`/`ai_recalled`/`ai_feedback` on `reviews`. Groq env: `GROQ_API_KEY`, `GROQ_MODEL` (default **`openai/gpt-oss-120b`** — a *reasoning* model; the shared `_groq_json` helper pins `reasoning_effort=low` for `openai/gpt-oss*` and uses `json_object`, not strict `json_schema` which gpt-oss ignores). **NOTE: `.env`/Railway may override `GROQ_MODEL` — the code default only applies if the env var is unset.**
- **Question mode (PROTOTYPE)** = same `GRADER_ENABLED` gate, layered **additively** on the grader: `generate_questions()` turns `key_memory` into 2–3 short-answer questions (answerable **solely from `key_memory`** — no un-captured "gotcha" trivia; open-ended, never MCQ), `grade_question_set()` grades the set in one call. Endpoints `POST /api/reviews/{id}/questions` + `/grade-questions`. `Review.jsx` probes `/questions` per card and falls back to the single free-recall box on 404/503, so the live path stays pristine when off. Free recall remains the default/fallback.
- **Related subtopics** (both grade paths) = 1–2 `{title, explainer}` adjacent topics worth learning next — **suggestions, never graded** (the constructive answer to "what about material they didn't capture?": surface it, don't quiz it). Surfaced as a distinct highlighted callout in `Review.jsx`.
- **Capture assist (PROTOTYPE)** = same `GRADER_ENABLED` gate, but runs at **LOG time, not review time**: `suggest_key_points(topic, draft)` → 3–5 core sub-points under the topic. On-demand only ("Stuck? Suggest key points" button — no call per log), and **never auto-applied** — the user taps to insert what they actually learned (recognition > blank-page recall; the answer to "I can't articulate it" WITHOUT quizzing un-captured material). Endpoint `POST /api/activities/suggest-key-points`. `apiFetch` now attaches `err.status` so the UI hides the button on 404 (grader off).
- **Key Memory cap** = 500 chars (`ActivityCreate`, ~6 lines) + live counter in `LogActivity.jsx`. Enforces "one testable claim, not a paragraph dump" and bounds LLM input. Only validates new logs (existing rows untouched).
- **Roadmap link** = optional `activities.roadmap_id` (FK→roadmaps, ON DELETE SET NULL; migration `f4a9c2e1b370`). Log form has a roadmap picker with **in-progress roadmaps surfaced first** (sorted by `progress_pct` from `GET /api/roadmaps/`). Roadmap-LEVEL link (not node); node-level + node-complete→prefilled-log loop still future. (Replaced the old "Coming Soon: Track & Roadmap" card.)
- **DB connection:** `DATABASE_URL` = Supabase **transaction pooler** (`postgres.<ref>:<pw>@aws-1-ap-south-1.pooler.supabase.com:6543/postgres`) → engine needs `statement_cache_size=0` + `prepared_statement_cache_size=0` (already set) and `pool_pre_ping=True`. Direct `db.<ref>.supabase.co` is IPv6-only → avoid. Gotchas hit while deploying: host shard is **`aws-1`** not `aws-0` (wrong shard → ENOTFOUND); repeated auth failures trip Supabase's **ECIRCUITBREAKER** (must stop deploying and wait ~minutes for it to re-arm — re-deploying keeps it tripped); use an **alphanumeric** DB password (special chars break the URL).
- **Deploy:** frontend **Vercel** (root=`frontend/`, `vercel.json` SPA rewrite required), backend **Railway** (root=`backend/`, **Singapore** region for latency). Env on Railway incl. `ADMIN_EMAIL`, CORS allow-list (apex+www), `GROQ_API_KEY`/`GRADER_ENABLED`. Run `alembic upgrade head` (DB head = `a4b2e9f1c8d3` — `activities.node_id`; chain: …`a1b2c3d4e5f6` FSRS → `b2c3d4e5f6a7` prereqs → `a3f1c0d4e7b2` roadmap slug → `a4b2e9f1c8d3` node_id). **NOTE: the slug + node_id migrations are NOT yet applied to prod — run before relying on clean URLs / the lesson "Add to reviews" button.**
- **Supabase MCP** (read-only) configured in `.mcp.json` — good for read-only DB verification.

## Known debt
- **`LogActivity.jsx` fields** = Topic, Source Type, Key Memory, Mistake?, Difficulty, needed-hint — all wired to `POST /api/activities/`. The unwired Track/Roadmap/Activity-Type/Retention selects (UI-only, two with hardcoded fake options) were **removed** to cut logging friction; re-add **real** Track/Roadmap pickers when the backend models them. `source_type` (problem/lecture/video/…) is a plain nullable string, surfaced as a Vault badge; consumed by analytics later. NOTE: post-SM-2, `difficulty`/`needed_hint` no longer gate scheduling (all activities schedule) — kept as cheap signals for future FSRS/metrics + Vault badges.
- Momentum / Retention Strength / Review Compliance are Phase-2 (Analytics shows them as labelled placeholders).
- Roadmap progress counts subtopics as nodes. DSA roadmaps are topic/problem-level, not full A2Z problem list.
- **Naive-UTC timestamps** rendered with `new Date(iso)` in the frontend (no `Z` suffix) → interpreted as local time. Cosmetic off-by-one on date *labels* possible near midnight for non-UTC users (IST); scheduling math is unaffected (interval counts from `last_reviewed_at`). Cleanup deferred.
