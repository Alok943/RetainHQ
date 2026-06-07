# RetainHQ — Architecture

## Overview

RetainHQ is a learning-retention app built around one core loop:
**Log Activity → Capture Key Memory → Schedule Reviews → Active Recall → Retain.**

The system is a React SPA backed by a FastAPI service, with Supabase providing Postgres and Google OAuth.

---

## High-Level Topology

```
Browser (React SPA — Vercel)
  │
  │  HTTPS + ES256 Bearer JWT
  ▼
FastAPI (Render / Railway)
  │
  │  asyncpg / SQLAlchemy async
  ▼
Supabase Postgres (managed)
  │
  └─ auth.users  (Supabase Auth — Google OAuth, identity-provider only)
```

The frontend talks **only** to FastAPI. Supabase is used for two things and nothing else:
- **Auth:** Google OAuth via Supabase Auth, which issues ES256 JWTs.
- **Postgres:** managed database accessed exclusively through FastAPI.

There are no direct `supabase.from(...)` DB calls in the React code.

---

## Request Authentication Flow

```
1. User signs in via Supabase Auth (Google OAuth)
2. Supabase issues an ES256 JWT (sub = user UUID, role = "authenticated")
3. Frontend stores the JWT in Supabase's session and attaches it as
   "Authorization: Bearer <token>" on every apiFetch() call
4. FastAPI HTTPBearer extracts the token
5. PyJWKClient fetches Supabase's JWKS endpoint (cached 1 hour) and
   verifies the signature + audience + expiry
6. get_current_user() returns a SupabaseUser(id, email, role)
7. Every route handler receives the verified user as a dependency
```

Key constraints:
- Only `ES256` and `RS256` are accepted (no HS256 — avoids algorithm confusion attacks).
- The `sub` claim (string UUID) is cast to `uuid.UUID` before every DB query.
- Every query is scoped by `user_id` — there is no shared data path except roadmaps/nodes (read-only, shared across all users).

---

## Backend Structure

```
backend/
├── app/
│   ├── main.py               # FastAPI app, CORS, router mounts, /health, /me
│   ├── core/
│   │   ├── config.py         # pydantic-settings (reads .env)
│   │   ├── database.py       # async SQLAlchemy engine + session factory
│   │   └── security.py       # SupabaseUser model, verify_token (JWKS/ES256)
│   ├── api/
│   │   ├── deps.py           # get_db, get_current_user, get_admin_user
│   │   └── routes/
│   │       ├── activities.py # Knowledge logging (POST creates activity + first review)
│   │       ├── reviews.py    # Due reviews + completion (SM-2 advancement)
│   │       ├── dashboard.py  # Aggregated stats (7 queries → should be 1 CTE)
│   │       ├── roadmaps.py   # Roadmap list/detail + node progress upsert
│   │       ├── feedback.py   # User-submitted suggestions
│   │       └── admin.py      # Founder-gated funnel + feedback (raw SQL, auth.users)
│   ├── models/
│   │   └── models.py         # Single source of truth for the ORM schema
│   ├── schemas/              # Pydantic v2 request/response models
│   └── services/
│       ├── scheduler.py      # SM-2 spaced-repetition logic
│       └── grader.py         # LLM recall grader (FROZEN — GRADER_ENABLED=false)
├── alembic/
│   └── versions/             # All schema changes as migrations (never hand-edit DB)
└── seed_*.py                 # Idempotent roadmap seed scripts (fixed UUIDs)
```

### Database Session Lifecycle

`get_db` yields an `AsyncSession` per request using `async_session_maker`.
Sessions use `expire_on_commit=False` — ORM objects remain accessible after `commit()`.
Relationships are loaded with `selectinload` (never lazy-load on an async session — that raises `MissingGreenlet`).

### Async Engine Config

The engine connects to Supabase's **transaction pooler** (`pooler.supabase.com:6543`).
Required settings for pgbouncer compatibility:
```python
connect_args={
    "prepared_statement_cache_size": 0,
    "statement_cache_size": 0
}
```
`pool_pre_ping=True` recycles stale connections after network blips.
`echo=True` is set — **must be changed to `False` before production** (logs SQL + params).

---

## Frontend Structure

```
frontend/src/
├── App.jsx           # Shell: routing, auth state, theme toggle, admin gate
├── Login.jsx         # Always-dark landing/sign-in page
├── Home.jsx          # Dashboard: due count, consistency, quick actions
├── LogActivity.jsx   # Activity logging form → POST /api/activities/
├── Review.jsx        # Spaced-repetition review session (retrieval gate → reveal → rate)
├── KnowledgeVault.jsx # Browse all captured memories, client-side search
├── Roadmaps.jsx      # Roadmap index with progress bars
├── RoadmapDetail.jsx # React Flow + dagre graph, node completion, PDF export
├── Analytics.jsx     # Stats + Phase-2 placeholders
├── Admin.jsx         # Founder-only: funnel + user feedback tabs
├── Profile.jsx       # Theme toggle, sign-out, dev JWT copy button
└── lib/
    ├── api.js        # apiFetch() — attaches Bearer JWT to all requests
    ├── supabase.js   # Supabase client (auth only)
    └── theme.jsx     # ThemeProvider + dark-mode toggle (persisted, FOUC-free)
```

### Dark Mode

`ThemeProvider` toggles a `.dark` class on `<html>`. Dark-mode styles live in `index.css` as a **centralized override layer** — new components that reuse existing color classes inherit dark mode automatically. The Login page is intentionally always-dark via inline styles.

---

## Core Loop: SM-2 Spaced Repetition

Every logged activity is one SM-2 "card." State lives on the `activities` table.

```
Log Activity
    │
    ▼
initial_review_for_activity()
    │  Creates Review(status='due', scheduled_for=now)
    │  Sets activity.ease_factor=2.5, repetitions=0, interval_days=0
    ▼
User opens Review session → GET /api/reviews/due
    │
    ▼
Retrieval Gate: type free-recall or "I don't know" → Reveal
    │
    ▼
User rates: Missed / Hard / Good / Easy
    │  { rating: 'hard'|'medium'|'easy', recalled: true|false }
    ▼
POST /api/reviews/{id}/complete
    │
    ├─ quality_from_outcome(rating, recalled)
    │     recalled=False → quality=2 (lapse)
    │     recalled=True + easy/medium/hard → 5/4/3
    │
    └─ apply_sm2(activity, quality)
          quality < 3  → lapse: repetitions=1, interval=1d
          rep=1        → interval=1d
          rep=2        → interval=6d
          rep≥3        → interval=round(interval × ease_factor)
          ease_factor  → updated every completion, floored at 1.3
          Next Review  → Review(scheduled_for = now + interval_days)
```

The invariant: **exactly one open `status='due'` review per activity at any time.**
(This is enforced by application logic only — there is currently no DB constraint or row lock.)

---

## Data Model Summary

| Table | Key Columns | Notes |
|---|---|---|
| `activities` | user_id, topic, key_memory, ease_factor, repetitions, interval_days, next_review_at | One card per logged activity |
| `reviews` | user_id, activity_id, status, scheduled_for, rating, recalled, quality | status ∈ {due, completed} |
| `tracks` | user_id, name | Not yet wired to the logging UI |
| `roadmaps` | title, description | Shared across all users |
| `roadmap_nodes` | roadmap_id, phase, section, title, tier, parent_id | parent_id = self-ref for subtopics |
| `user_progress` | user_id, node_id, status | status ∈ {done, not_started} |
| `feedbacks` | user_id, message, status | status ∈ {new, reviewed, resolved} |

All PKs are UUID. Timestamps are naive UTC (`datetime.utcnow()` — deprecation-pending, should migrate to `datetime.now(timezone.utc)`).

---

## Admin Access

Admin routes (`/api/admin/funnel`, `/api/admin/feedback`) are gated by `get_admin_user`, which 403s unless `current_user.email == settings.ADMIN_EMAIL`. This is an email-check gate, **not** a full RBAC system. The frontend mirrors the gate in `App.jsx` for UX (hides the tab), but the backend is the real enforcement point.

Admin SQL queries cross into the `auth` schema (`auth.users`) to join signup data with activity/review data. This requires the DB role to have `USAGE` on the `auth` schema.

---

## Deployment

| Layer | Platform | Root dir | Key env vars |
|---|---|---|---|
| Frontend | Vercel | `frontend/` | `VITE_API_BASE_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` |
| Backend | Render / Railway | `backend/` | `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_JWT_SECRET`, `ADMIN_EMAIL` |
| DB / Auth | Supabase | — | Managed |

CORS must list the deployed Vercel domain explicitly. `main.py` currently only allows `localhost:5173` — update before launch.

---

## Known Architectural Debt

- **`echo=True` in `database.py`** — must be disabled in prod (leaks SQL to logs).
- **Dashboard fires 7 sequential queries** — should be a single CTE.
- **No pagination** on `GET /api/activities/` or `GET /api/reviews/due`.
- **No rate limiting** on write endpoints.
- **No unique constraint on `user_progress(user_id, node_id)`** at the DB level (the ORM does SELECT-then-INSERT/UPDATE which races under concurrency).
- **`datetime.utcnow()` used throughout** — deprecated in Python 3.12+.
- **SM-2 interval has no upper cap** — can schedule reviews years out.
- **GRADER_ENABLED flag** — the LLM recall grader (`services/grader.py`) is frozen and not wired to any endpoint.
