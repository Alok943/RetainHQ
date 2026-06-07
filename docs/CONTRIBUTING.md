# Contributing to RetainHQ

This is a solo-founder project. This guide exists so a collaborator or future team member can get oriented quickly, understand the conventions, and make changes without breaking the core loop.

---

## Prerequisites

- Python 3.10+
- Node.js 18+
- A Supabase project with Google OAuth configured
- A `.env` file in `backend/` (see below)

---

## Local Setup

### 1. Clone and create the backend virtualenv

```bash
git clone <repo>
cd RetainHQ/backend
python -m venv .venv

# Windows
.\.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Set up backend environment variables

Create `backend/.env`:
```
DATABASE_URL=postgresql://postgres.<ref>:password@aws-0-<region>.pooler.supabase.com:6543/postgres
SUPABASE_URL=https://<ref>.supabase.co
SUPABASE_JWT_SECRET=<your-jwt-secret>
ADMIN_EMAIL=your@email.com
```

**Important DB URL notes:**
- Use the **transaction pooler** URL from Supabase (`pooler.supabase.com:6543`), not the direct connection.
- The direct URL (`db.<ref>.supabase.co`) is IPv6-only and will fail in most local environments.
- Do not include pgbouncer query params (`?pgbouncer=true`); `database.py` strips them automatically.

### 3. Apply migrations

```bash
cd backend
alembic upgrade head
```

This applies all migrations in `alembic/versions/` in order. Always run this after pulling changes that include new migration files.

### 4. (Optional) Seed roadmap data

```bash
cd backend
python seed_python_swe.py
python seed_striver_a2z.py
# ... etc for any roadmaps you want locally
```

Seed scripts are idempotent (use fixed UUIDs + `ON CONFLICT DO NOTHING`). Safe to run multiple times.

### 5. Start the backend

```bash
cd backend
uvicorn app.main:app --reload
# → http://localhost:8000
# → http://localhost:8000/docs  (Swagger UI)
```

### 6. Set up the frontend

```bash
cd frontend
npm install
```

Create `frontend/.env.local`:
```
VITE_API_BASE_URL=http://localhost:8000
VITE_SUPABASE_URL=https://<ref>.supabase.co
VITE_SUPABASE_ANON_KEY=<your-anon-key>
```

```bash
npm run dev
# → http://localhost:5173
```

---

## Project Conventions

### Auth — never rebuild, never bypass

- The frontend authenticates via Supabase (Google OAuth) and gets an **ES256 JWT**.
- That JWT is attached to every API request as a Bearer token via `apiFetch()` in `frontend/src/lib/api.js`.
- FastAPI verifies it via JWKS in `core/security.py`. Never use HS256. Never hardcode secrets.
- `get_current_user` returns a `SupabaseUser` — use attribute access (`.id`, `.email`), not dict access.
- Always cast `current_user.id` (string) to `uuid.UUID` before DB queries.

### One data path

React → `apiFetch()` → FastAPI → Postgres. Never add direct `supabase.from(...)` DB calls in the frontend. Supabase is identity-provider only on the frontend.

### Schema changes go through Alembic

Never hand-edit the live DB. Always:
```bash
# create a new migration
alembic revision -m "describe what changed"
# edit the generated file in alembic/versions/
alembic upgrade head
```

`models/models.py` is the single source of truth for the ORM schema. Keep it in sync with migrations.

### Async DB patterns

```python
# CORRECT: eager-load with selectinload
stmt = select(Review).options(selectinload(Review.activity))

# WRONG: accessing a relationship outside eager-load raises MissingGreenlet
review = result.scalars().first()
print(review.activity.topic)  # crashes if not eagerly loaded
```

Sessions use `expire_on_commit=False` — ORM objects remain accessible after `commit()` and `refresh()`.

### Authorization — every query scoped by user

Every route that touches user data must filter by `user_id`. Mutating endpoints must verify ownership:

```python
# CORRECT: IDOR protection
stmt = select(Review).where(
    Review.id == review_id,
    Review.user_id == user_id  # must own it
)

# WRONG: fetches any user's review
stmt = select(Review).where(Review.id == review_id)
```

### Pydantic v2 — ORM response models need `from_attributes`

```python
class MyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    # ...
```

Without this, `return orm_object` raises a validation error.

### Trailing slashes — POST collection routes

Collection POST routes use a trailing slash: `POST /api/activities/`. Match it exactly to avoid FastAPI issuing a 307 redirect (which strips the request body).

### Commits are authored by the human only

Do not add `Co-Authored-By: Claude` or any AI attribution to commits. All commits are attributed to the solo founder.

---

## Making a Backend Change

1. **Define or update the schema** in `models/models.py`.
2. **Write the Alembic migration**: `alembic revision -m "describe change"` → fill in `upgrade()` / `downgrade()`.
3. **Add or update the Pydantic schema** in `schemas/`.
4. **Implement the route** in `api/routes/`.
5. **Test via Swagger**: `http://localhost:8000/docs` — authenticate with the dev JWT from the Profile page.
6. **Apply the migration**: `alembic upgrade head`.

### Adding a new route

```python
# api/routes/my_feature.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.core.security import SupabaseUser
import uuid

router = APIRouter()

@router.get("/", response_model=list[MyResponse])
async def list_things(
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user)
):
    user_id = uuid.UUID(current_user.id)
    # ... always scope by user_id
```

Register in `main.py`:
```python
from app.api.routes import my_feature
app.include_router(my_feature.router, prefix="/api/my-feature", tags=["my-feature"])
```

---

## Making a Frontend Change

All API calls go through `apiFetch()`:
```js
import { apiFetch } from './lib/api';

// GET
const data = await apiFetch('/api/activities/');

// POST
await apiFetch('/api/activities/', {
  method: 'POST',
  body: JSON.stringify({ topic: '...', key_memory: '...', difficulty: 3, needed_hint: false }),
});
```

`apiFetch` throws on non-2xx responses. Errors have a `.message` string from the backend's `detail` field.

### Dark mode

New components that reuse existing color utility classes automatically inherit dark mode — the override layer in `index.css` handles it. Only add explicit `dark:` variants if you're using a color class that isn't already remapped in `index.css`.

---

## SM-2 Scheduler

The SM-2 logic lives entirely in `services/scheduler.py`. Three functions:

| Function | When called |
|---|---|
| `initial_review_for_activity(activity)` | On `POST /api/activities/` — sets up state, returns Day-0 review |
| `quality_from_outcome(rating, recalled)` | On review completion — maps user signals to SM-2 quality (0–5) |
| `apply_sm2(activity, quality)` | On review completion — updates activity state, returns next review |

If you change scheduling logic, the key invariant to preserve: **one activity has exactly one open `status='due'` review at any time.** `apply_sm2` creates the next review before the caller commits — both the completion and the new review go in the same transaction.

---

## Debugging Tips

### Get a JWT for local API testing
Sign in to the app, go to Profile, click "Copy JWT." Paste into Swagger UI's "Authorize" dialog (the lock icon). The token expires in ~1 hour.

### Check the DB state directly
Use the Supabase SQL editor or any Postgres client with the direct connection string (for local inspection only — use the pooler in the app).

Useful queries:
```sql
-- Check SM-2 state for a user's activities
SELECT topic, ease_factor, repetitions, interval_days, next_review_at
FROM activities WHERE user_id = '<uuid>' ORDER BY created_at DESC;

-- Check open reviews
SELECT r.id, a.topic, r.status, r.scheduled_for
FROM reviews r JOIN activities a ON a.id = r.activity_id
WHERE r.user_id = '<uuid>' AND r.status = 'due';
```

### Common errors and fixes

| Error | Cause | Fix |
|---|---|---|
| `MissingGreenlet` on relationship access | Lazy-loading on async session | Add `selectinload(Model.relationship)` to the query |
| `422 Unprocessable Entity` on POST | Request body missing required fields or wrong types | Check the Pydantic schema in `schemas/` |
| `307 Temporary Redirect` on POST | Missing trailing slash | Change `/api/activities` to `/api/activities/` |
| `401 Unauthorized` | Expired or missing JWT | Re-sign in; copy fresh JWT from Profile |
| `503 Service Unavailable` | JWKS endpoint unreachable | Transient; retry. Check `SUPABASE_URL` env var |
| Alembic `Target database is not up to date` | Unapplied migrations | `alembic upgrade head` |

---

## What's Not Wired (don't touch without reading context)

- **`services/grader.py`** — LLM recall grader (Groq). Frozen behind `GRADER_ENABLED=false`. Not connected to any endpoint. Do not enable without understanding the cost/latency implications.
- **`NodeDrawer.jsx`** — dead code, not rendered anywhere.
- **Track / Roadmap pickers in `LogActivity.jsx`** — the UI fields were removed to reduce friction. Re-add only when the backend models them properly (track assignment, roadmap linking).
- **`user_progress.status = 'in_progress'`** — the original schema had this, but the app uses only `done` / `not_started`. The supabase schema.sql still defines it; the ORM and app do not use it.
