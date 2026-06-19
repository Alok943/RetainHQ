# RetainHQ

**Track what you remember, not what you complete.**

RetainHQ is a learning-retention web app built on spaced repetition + active recall. It owns the entire learning loop — **Log → Capture → Schedule → Recall → Retain** — so knowledge actually sticks instead of evaporating a week after you study it.

Live at **[retainhq.app](https://retainhq.app)**.

---

## The core loop

The whole product is one loop, and every feature serves it:

1. **Log** an activity (something you just learned) → captures the single **Key Memory** worth keeping.
2. **Schedule** — logging schedules the first review for **tomorrow** (recall after a delay is what builds memory; an instant quiz just measures short-term recall and breeds review fatigue). The one exception: a user's **first-ever** activity gets a demo review *due now*, so a brand-new user sees the loop instantly. Reviews are capped per day (overflow rolls forward) so a backlog never balloons into a demoralizing "23 due".
3. **Recall** — the Review screen makes you commit a free-recall answer *before* revealing the key memory (retrieval practice, not recognition).
4. **Rate** how it went (Missed / Hard / Good / Easy) → this drives the **SM-2** scheduler, which spaces the next review based on how well you recalled.
5. **Retain** — each review is rescheduled to land right before you'd forget. The spacing widens as the memory strengthens.

> **Design rule:** *Ship the mechanic, freeze the intelligence.* The immediate goal is validating the core loop with ~20 real users — not piling on features.

---

## Architecture

```
React SPA (Vercel)
  ├─ Supabase Auth (Google OAuth) ──► ES256 JWT
  └─ apiFetch + Bearer JWT ──► FastAPI (Railway / Singapore) ──asyncpg──► Supabase Postgres
```

- The frontend talks **only** to FastAPI. Supabase is used purely as an **identity provider** (Google OAuth) and a **managed Postgres** database.
- FastAPI is the **single gateway** to the database — there are no direct `supabase.from(...)` DB calls in React.
- Auth is **ES256 JWT**, verified server-side via JWKS (`PyJWKClient`). Never HS256, never a hand-rolled OAuth.

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full picture.

---

## Tech stack

| Layer | Stack |
|---|---|
| **Frontend** | React 19 + Vite + Tailwind CSS, React Router, React Flow + dagre (roadmap flowchart), jsPDF (roadmap export). Deployed on **Vercel** (root = `frontend/`). |
| **Backend** | FastAPI (Python 3.10+), SQLModel + Alembic + asyncpg, pydantic-settings, PyJWT (crypto). Deployed on **Railway** (Singapore region, for latency to Supabase Mumbai). |
| **Database / Auth** | Supabase — Postgres (UUID PKs, naive-UTC timestamps) + Google OAuth. |
| **AI (advisory)** | Groq (`openai/gpt-oss-120b` by default) for the optional LLM recall grader + question mode. |

---

## Repository layout

```
RetainHQ/
├── frontend/                 # React SPA (Vercel root)
│   ├── src/
│   │   ├── App.jsx           # shell, routing, sidebar/mobile nav (+ due-count badge)
│   │   ├── Login.jsx         # landing + Google sign-in (intentionally always-dark)
│   │   ├── Home.jsx          # dashboard: due review, recent captures, stats
│   │   ├── FirstCapture.jsx  # full-screen first-capture gate for brand-new users
│   │   ├── LogActivity.jsx   # capture form → POST /api/activities/
│   │   ├── Review.jsx        # retrieval gate → reveal → rate (+ AI feedback box)
│   │   ├── Hint.jsx          # one-time contextual tutorial hints
│   │   ├── Roadmaps.jsx      # roadmap list with server-computed progress
│   │   ├── RoadmapDetail.jsx # List view (default) + Map view (React Flow) + PDF export
│   │   ├── KnowledgeVault.jsx# browse captured key-memories (client-side search)
│   │   ├── Analytics.jsx     # real stats + honest Phase-2 placeholders
│   │   ├── Admin.jsx         # founder-only funnel + feedback tabs
│   │   ├── Profile.jsx
│   │   └── lib/
│   │       ├── api.js        # apiFetch (Bearer JWT) + optionalAuth (guest reads)
│   │       ├── supabase.js
│   │       ├── theme.jsx     # dark-mode ThemeProvider
│   │       └── AuthContext.jsx  # PLG guest-exploration + requireAuth() gating
│   └── vercel.json           # SPA rewrite (fixes deep-link / OAuth 404s)
│
├── backend/                  # FastAPI (Railway root)
│   └── app/
│       ├── main.py           # app, CORS allow-list, router mounts, /health, /me
│       ├── core/
│       │   ├── config.py     # pydantic-settings (env)
│       │   ├── database.py   # async engine + session maker (expire_on_commit=False)
│       │   └── security.py   # SupabaseUser, verify_token (JWKS / ES256)
│       ├── api/
│       │   ├── deps.py       # get_db, get_current_user, get_admin_user
│       │   └── routes/       # activities, reviews, dashboard, roadmaps, feedback, admin
│       ├── schemas/          # Pydantic request/response models
│       ├── services/
│       │   ├── scheduler.py  # SM-2 scheduling logic
│       │   └── grader.py     # LLM recall grader (Groq)
│       ├── models/models.py  # single source of truth for the schema
│       ├── alembic/versions/ # migrations
│       └── seed_*.py         # idempotent roadmap seed scripts (dev)
│
└── docs/                     # ARCHITECTURE, API, FLOWS, CONTRIBUTING, funnel.sql, …
```

---

## Local development

### Prerequisites
- Node 18+ and npm
- Python 3.10+
- A Supabase project (Postgres + Google OAuth configured)

### Frontend

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
```

`frontend/.env`:
```
VITE_API_BASE_URL=http://localhost:8000
VITE_SUPABASE_URL=https://<your-ref>.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=<anon/publishable key>   # VITE_SUPABASE_ANON_KEY also accepted
```

### Backend

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1        # Windows PowerShell  (use source .venv/bin/activate on macOS/Linux)
pip install -e .
alembic upgrade head                 # apply migrations
uvicorn app.main:app --reload        # http://localhost:8000/docs
```

`backend/.env`:
```
DATABASE_URL=postgresql+asyncpg://postgres.<ref>:<pw>@aws-1-ap-south-1.pooler.supabase.com:6543/postgres
SUPABASE_URL=https://<your-ref>.supabase.co
SUPABASE_JWT_SECRET=<jwt secret>           # JWKS-based ES256 verification
ADMIN_EMAIL=you@example.com                # founder-only Admin gate
# Optional AI grader + question mode (off by default):
GRADER_ENABLED=false
GROQ_API_KEY=<groq key>
GROQ_MODEL=openai/gpt-oss-120b      # any Groq model; reasoning models get reasoning_effort=low
```

> **DB connection gotchas** (hard-won while deploying): use the Supabase **transaction pooler** (`...pooler.supabase.com:6543`) — the engine sets `statement_cache_size=0` + `prepared_statement_cache_size=0` and `pool_pre_ping=True`. The host shard is **`aws-1`**, not `aws-0`. Use an **alphanumeric** DB password (special chars break the URL). The direct `db.<ref>.supabase.co` host is IPv6-only — avoid it.

### Seeding roadmaps (dev)

```bash
cd backend
python seed_striver_a2z.py    # each roadmap has its own idempotent seed_*.py with a fixed UUID
```

---

## Data model

Postgres, UUID primary keys, naive-UTC timestamps.

- **activities** — `user_id`, `topic`, `key_memory` (capped at 500 chars on create), `mistake?`, `difficulty(1–5)`, `needed_hint`, `source_type?`, `roadmap_id?` (optional FK → `roadmaps`, ON DELETE SET NULL), `created_at`, plus SM-2 card state: `ease_factor` (2.5), `repetitions` (0), `interval_days` (0), `last_reviewed_at?`, `next_review_at?`.
- **reviews** — `user_id`, `activity_id`, `status('due'|'completed')`, `scheduled_for`, `completed_at?`, `rating?('easy'|'medium'|'hard')`, `recalled?` (objective got-it/missed-it), `quality?` (0–5 SM-2 grade), and AI grader output `ai_verdict?` / `ai_recalled?` / `ai_feedback?`.
- **roadmaps** — `title`, `description`.
- **roadmap_nodes** — `roadmap_id`, `phase`, `section`, `title`, `tier(easy|medium|hard)`, `order_index`, `description?`, `parent_id?` (self-ref → subtopics are completable child nodes).
- **user_progress** — `user_id`, `node_id`, `status`.
- **feedbacks** — `user_id`, `message`, `status('new'|'reviewed'|'resolved')`, `created_at`.

> **Schema changes always go through Alembic migrations** — never hand-edit the live DB. Current DB head: `f4a9c2e1b370`.

---

## API

All routes are under `/api` and require a Bearer JWT (some support `optionalAuth` for guest reads).

| Method & Path | Purpose |
|---|---|
| `GET /api/activities/` | List the user's captured activities (Knowledge Vault), newest first |
| `POST /api/activities/` | Create activity (optional `roadmap_id`); init SM-2 state + schedule the first review (tomorrow; *now* for the user's first-ever activity). Returns `review_due_now`. |
| `POST /api/activities/suggest-key-points` | **Capture assist** (gated): `{topic, draft?}` → `{points[]}` — core sub-points under the topic so a stuck user can recognize + keep what they learned. Suggestion only, never auto-applied. |
| `GET /api/reviews/due` | Due reviews (`status='due'`, `scheduled_for ≤ now`) with activity eager-loaded. Capped to one session (overflow rolls forward). |
| `POST /api/reviews/{id}/complete` | Complete with `rating` + optional `recalled`; advances SM-2 and schedules the next review (IDOR-protected) |
| `POST /api/reviews/{id}/grade` | LLM grader (gated on `GRADER_ENABLED`): grades free recall vs `key_memory` → `{verdict, recalled, feedback, revision_note, related_subtopics}`. Advisory only. |
| `POST /api/reviews/{id}/questions` | **Question mode** (gated): generate 2–3 short-answer questions grounded in `key_memory`. 404 when disabled → UI falls back to free recall. |
| `POST /api/reviews/{id}/grade-questions` | **Question mode** (gated): grade the answer set vs `key_memory` → `{recalled, feedback, items[], related_subtopics}`. Advisory only. |
| `GET /api/dashboard/` | `due_count`, `consistency_window`, `daily_progress`, `total_activities`, `total_reviews_completed`, `next_review_at` |
| `GET /api/roadmaps/` | List roadmaps with server-computed progress |
| `GET /api/roadmaps/{id}` | Roadmap + nodes + per-node user status |
| `PUT /api/roadmaps/nodes/{id}/progress` | Idempotent upsert of `done` / `not_started` |
| `POST /api/feedback/` | Submit a feedback message |
| `GET /api/admin/funnel` | **Admin-only** activation funnel (signups → logged → reviewed → returned) |
| `GET /api/admin/feedback` | **Admin-only** list of submitted feedback |

Full detail in [`docs/API.md`](docs/API.md). Interactive docs at `/docs` when the backend is running.

**Conventions that matter:**
- Every query is scoped by `current_user.id`; mutating endpoints verify ownership (`WHERE id = :id AND user_id = :uid`) for IDOR protection.
- Collection POST routes use a **trailing slash** (`/api/activities/`) — call exact paths to avoid 307 redirects.
- Async DB: eager-load relationships with `selectinload` (lazy access on a closed async session → `MissingGreenlet` crash). Cast the JWT `sub` string to `uuid.UUID` before queries.

---

## How scheduling works (SM-2)

Every logged activity is a single SM-2 "card" — its scheduling state lives on the `activities` row. Logic is in [`backend/app/services/scheduler.py`](backend/app/services/scheduler.py).

- Logging schedules the first review for **tomorrow** (`repetitions=1`, so the ladder reads **+1 day → +6 days → `round(interval × ease_factor)`**). A user's **first-ever** activity instead gets a demo review *due now* (`immediate=True`, `repetitions=0`) as the onboarding aha — a one-time exception, not per-log, so it doesn't reintroduce fatigue.
- Each completion maps `rating` + `recalled` → a quality score 0–5:
  - `recalled = false` → quality 2 (a **lapse** → interval resets to 1 day, `repetitions` resets to **1** so the next pass jumps to 6 days, avoiding an awkward 1d→1d).
  - otherwise Hard / Good / Easy → quality 3 / 4 / 5.
- `quality` is persisted on the review; the **next** review is scheduled immediately.
- **Daily session cap** (`REVIEW_SESSION_CAP`, default 10): the due queue and the dashboard `due_count` are both capped at one session's worth, oldest-first. Overdue cards beyond the cap stay `due` and roll forward — a fallen-behind user always sees a bounded, finishable set instead of the classic unbounded-backlog death spiral.

FSRS is the planned v2 successor (the `rating` + `recalled` signals are already being captured to feed it).

---

## The LLM recall grader + question mode (advisory)

[`backend/app/services/grader.py`](backend/app/services/grader.py) — **shipped and wired, gated by `GRADER_ENABLED`** (off in prod until the env is set). One Groq call per step; default model `openai/gpt-oss-120b`. gpt-oss is a *reasoning* model, so `_groq_json` pins `reasoning_effort=low` for it (gpt-oss-only flag) to bound latency and stop reasoning tokens from truncating the JSON. Uses `json_object` mode (not the stricter `json_schema`, which gpt-oss ignores).

**Free-recall grader** (`/grade`):
- Grades the user's answer **only against the stored `key_memory`** (the reference), never the model's outside knowledge.
- Returns strict JSON `{verdict, recalled, feedback, revision_note, related_subtopics}`, validated with Pydantic.
- **Advisory only** — it judges *recalled vs missed* and writes a short revision note, then suggests a rating chip. The user always makes the final call; the AI **never** auto-submits and never proposes "Hard" (felt difficulty is subjective).

**Question mode** (`/questions` + `/grade-questions`, prototype):
- Instead of one open "describe the topic" prompt, the LLM turns the `key_memory` into **2–3 short-answer questions**, then grades the answer set. This probes the forgettable *edges* of what was captured rather than letting a two-line summary skate by.
- Guardrail: questions must be answerable **solely from the `key_memory`** — no un-captured "gotcha" trivia (an unfair failure is exactly the friction that breeds fatigue). Open-ended short answer, never multiple choice. `key_memory` stays the single grading ground truth.
- **Additive, not a replacement** — the UI probes `/questions` per card; a 404 (disabled) or any failure falls back to the single free-recall box, so the live path stays pristine.

**Related subtopics** (both modes): each grade also returns 1–2 `related_subtopics` (`title` + one-line `explainer`) — adjacent topics worth learning next. These are **suggestions, never graded** — the constructive answer to "what about material they didn't capture?": surface it as a nudge, don't quiz them on it. Highlighted as a distinct callout in the Review UI.

**Capture assist** (`/suggest-key-points`, prototype): the LLM also runs at *log* time, not just review time. When a user is stuck summarizing what they learned, an on-demand "Suggest key points" button returns the core sub-points under the topic so they can **recognize and keep** the ones they actually studied (recognition is far easier than blank-page recall). It's a suggestion the user curates — **never auto-applied** — so they never end up capturing (and later being quizzed on) material they didn't learn.

- Failures degrade silently (`GraderError` → 503 → frontend skips the AI box).
- The gap between the AI's `ai_recalled` and the user's self-reported `recalled` is the calibration metric we care about.

---

## Roadmaps

10 seeded learning paths (Python for SWE, DSA — Striver A2Z, DSA — NeetCode 150, Core CS, Aptitude, Web Dev, System Design, Python Backend, SQL, AI Engineering). Each has an idempotent `seed_*.py` with a fixed UUID.

- **List view (default)** — collapsible phases with `done/total` counts (completed phases auto-collapse), explicit checkboxes, tier dots, indented subtopics, and inline notes/links. Scans fast and works on touch.
- **Map view** — the original React Flow + dagre flowchart, available via a toggle.
- **Download PDF** — styled jsPDF export reflecting your progress.
- **Complete → Log** — checking a node off prompts a "Log what you learned" toast that pre-fills the capture form, closing the roadmap → loop.

`phase` = sub-track (step spine), `tier` ∈ {easy, medium, hard}. Roadmap progress counts subtopics as nodes.

---

## Deployment

- **Frontend → Vercel** (root = `frontend/`). `vercel.json` SPA rewrite is **required** (fixes 404s on deep links / OAuth redirects). Auto-deploys on push to `main`.
- **Backend → Railway** (root = `backend/`, Singapore region). Env includes `DATABASE_URL`, `SUPABASE_*`, `ADMIN_EMAIL`, the CORS allow-list (apex + www), and `GROQ_API_KEY` / `GRADER_ENABLED`. Run `alembic upgrade head` against the DB.
- **CORS** is an explicit allow-list (`https://retainhq.app`, `https://www.retainhq.app`), never `*`.
- **Secrets** live only in `.env` (git-ignored) — never committed.

> Deploy-time note: repeated DB auth failures can trip Supabase's **ECIRCUITBREAKER** — stop redeploying and wait a few minutes for it to re-arm (redeploying keeps it tripped).

---

## Conventions

- **Commits** are authored solely by the user — no `Co-Authored-By` trailer. Work goes on `main` (solo, deploys from main).
- **One data path** — React → `apiFetch` → FastAPI → DB. No direct Supabase DB calls in the client.
- **Pydantic v2** — response schemas serializing ORM objects use `model_config = ConfigDict(from_attributes=True)`.
- **Dark mode** is a centralized override layer in `index.css` that remaps the app's color utilities under `html.dark` — new components inherit dark mode for free **if they reuse existing color classes**.
- **Admin gate (interim)** — founder-only access is an email check (`current_user.email == ADMIN_EMAIL`), not a full admin auth system. Good enough for the first cohort.

---

## Documentation

| Doc | Contents |
|---|---|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | System design, data flow, auth |
| [`docs/API.md`](docs/API.md) | Full endpoint reference |
| [`docs/FLOWS.md`](docs/FLOWS.md) | User + data flows |
| [`docs/walkthrough-guide.md`](docs/walkthrough-guide.md) | Product walkthrough |
| [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) | Contribution notes |
| [`docs/hardening-plan.md`](docs/hardening-plan.md) | Security / robustness backlog |
| [`docs/funnel.sql`](docs/funnel.sql) | Activation-funnel query (Supabase SQL editor) |
| [`CLAUDE.md`](CLAUDE.md) | Full project context + conventions (source of truth for agents) |

---

## Status & roadmap

**Phase 1 (core loop) is live end-to-end and deployed to production.** A real user can sign up, log an activity, run the scheduled review, and exercise the full spaced-repetition loop.

**Anti-fatigue redesign (latest):** first review deferred to tomorrow (first-ever activity keeps an instant demo), daily review session cap with rollover, and an LLM **question mode** + **related-subtopics** suggestions — both gated behind `GRADER_ENABLED`, free recall stays the fallback.

**Next, in order of leverage:**
1. Flip the AI grader + question mode on in prod (`GRADER_ENABLED=true`, `GROQ_API_KEY`, `GROQ_MODEL=openai/gpt-oss-120b` on Railway) and validate question/subtopic quality on real cards.
2. Expand seed content (e.g. a proper Git section; fine-tuning + evals for AI Engineering).
3. Logged Reviews Vault (review history).
4. Real Track / Roadmap pickers on the log form (currently capture-only).
5. Feedback status workflow + full admin auth.
6. Rate limiting (slowapi) on write endpoints.

**Phase 2:** FSRS scheduling, real momentum / retention-strength metrics, Re-entry Mode, custom user roadmaps ("Bring Your Own Path").

---

*Solo-founder build. The product advertises itself by working — so the loop comes first.*
