# RetainHQ — Technical Audit Report

> Generated 2026-08-20 from direct source-code analysis. Every claim has a file path + line reference.

---

## 1. Stack Inventory

### Frontend (Vite + React SPA)

| Layer | Tech | Evidence |
|---|---|---|
| Framework | React 19.2 | [package.json:32](file:///c:/Users/aloks/Desktop/RetainHQ/frontend/package.json#L32) |
| Build tool | Vite 8.0 | [package.json:52](file:///c:/Users/aloks/Desktop/RetainHQ/frontend/package.json#L52) |
| Styling | Tailwind CSS 3.4 | [package.json:51](file:///c:/Users/aloks/Desktop/RetainHQ/frontend/package.json#L51) |
| Routing | react-router-dom 7.16 | [package.json:34](file:///c:/Users/aloks/Desktop/RetainHQ/frontend/package.json#L34) |
| Animations | framer-motion 12.42 | [package.json:27](file:///c:/Users/aloks/Desktop/RetainHQ/frontend/package.json#L27) |
| 3D | @react-three/fiber 9.6 + drei 10.7 + three 0.185 | [package.json:20-21,37](file:///c:/Users/aloks/Desktop/RetainHQ/frontend/package.json#L20-L21) |
| Graph viz | reactflow 11.11 + dagre 0.8 | [package.json:26,35](file:///c:/Users/aloks/Desktop/RetainHQ/frontend/package.json#L26) |
| Math | katex 0.16 | [package.json:29](file:///c:/Users/aloks/Desktop/RetainHQ/frontend/package.json#L29) |
| PDF gen | jspdf 4.2 | [package.json:28](file:///c:/Users/aloks/Desktop/RetainHQ/frontend/package.json#L28) |
| Auth client | @supabase/supabase-js 2.106 | [package.json:23](file:///c:/Users/aloks/Desktop/RetainHQ/frontend/package.json#L23) |
| Analytics | posthog-js 1.396 + @vercel/analytics 2.0 | [package.json:24,31](file:///c:/Users/aloks/Desktop/RetainHQ/frontend/package.json#L24) |
| Error tracking | @sentry/react 10.65 | [package.json:22](file:///c:/Users/aloks/Desktop/RetainHQ/frontend/package.json#L22) |
| Icons | lucide-react 1.17 + simple-icons 16.23 | [package.json:30,36](file:///c:/Users/aloks/Desktop/RetainHQ/frontend/package.json#L30) |
| Fonts | IBM Plex Sans + JetBrains Mono (fontsource) | [package.json:18-19](file:///c:/Users/aloks/Desktop/RetainHQ/frontend/package.json#L18-L19) |

### Backend (FastAPI + Supabase Postgres)

| Layer | Tech | Evidence |
|---|---|---|
| Framework | FastAPI ≥0.111 | [pyproject.toml:7](file:///c:/Users/aloks/Desktop/RetainHQ/backend/pyproject.toml#L7) |
| Server | Uvicorn (standard) ≥0.30 | [pyproject.toml:8](file:///c:/Users/aloks/Desktop/RetainHQ/backend/pyproject.toml#L8) |
| ORM | SQLModel ≥0.0.19 (SQLAlchemy 2 wrapper) | [pyproject.toml:9](file:///c:/Users/aloks/Desktop/RetainHQ/backend/pyproject.toml#L9) |
| Migrations | Alembic ≥1.13 | [pyproject.toml:10](file:///c:/Users/aloks/Desktop/RetainHQ/backend/pyproject.toml#L10) |
| DB driver | asyncpg ≥0.29 (async Postgres) | [pyproject.toml:11](file:///c:/Users/aloks/Desktop/RetainHQ/backend/pyproject.toml#L11) |
| Auth JWT | PyJWT ≥2.8 (with cryptography) | [pyproject.toml:13](file:///c:/Users/aloks/Desktop/RetainHQ/backend/pyproject.toml#L13) |
| LLM: Groq | groq ≥0.11 | [pyproject.toml:14](file:///c:/Users/aloks/Desktop/RetainHQ/backend/pyproject.toml#L14) |
| LLM: Anthropic | anthropic ≥0.116 | [pyproject.toml:16](file:///c:/Users/aloks/Desktop/RetainHQ/backend/pyproject.toml#L16) |
| LLM: Google | google-genai ≥1.0 | [pyproject.toml:17](file:///c:/Users/aloks/Desktop/RetainHQ/backend/pyproject.toml#L17) |
| Email | resend ≥2.0 | [pyproject.toml:15](file:///c:/Users/aloks/Desktop/RetainHQ/backend/pyproject.toml#L15) |
| Analytics | posthog ≥3.7 | [pyproject.toml:19](file:///c:/Users/aloks/Desktop/RetainHQ/backend/pyproject.toml#L19) |
| Error tracking | sentry-sdk[fastapi] ≥2.0 | [pyproject.toml:20](file:///c:/Users/aloks/Desktop/RetainHQ/backend/pyproject.toml#L20) |
| Push notifications | pywebpush ≥2.0 (VAPID) | [pyproject.toml:21](file:///c:/Users/aloks/Desktop/RetainHQ/backend/pyproject.toml#L21) |
| Settings | pydantic-settings ≥2.3 | [pyproject.toml:12](file:///c:/Users/aloks/Desktop/RetainHQ/backend/pyproject.toml#L12) |

### Browser Extension (Companion)

| Layer | Tech | Evidence |
|---|---|---|
| Language | TypeScript 6.0 | [extension/package.json:20](file:///c:/Users/aloks/Desktop/RetainHQ/extension/package.json#L20) |
| Build | Vite 8.1 + @crxjs/vite-plugin 2.0-beta | [extension/package.json:16,21](file:///c:/Users/aloks/Desktop/RetainHQ/extension/package.json#L16) |
| Supabase | @supabase/supabase-js 2.110 | [extension/package.json:25](file:///c:/Users/aloks/Desktop/RetainHQ/extension/package.json#L25) |
| Manifest | MV3, targets Chrome + Firefox | [extension/manifest.json:2,39](file:///c:/Users/aloks/Desktop/RetainHQ/extension/manifest.json#L2) |
| Sites tracked | YouTube, LeetCode, NeetCode, Coursera, Notion, ChatGPT/Claude/Gemini, PDFs | [extension/manifest.json:56-136](file:///c:/Users/aloks/Desktop/RetainHQ/extension/manifest.json#L56-L136) |

### Database

**Supabase Postgres** (free plan). The app's `DATABASE_URL` goes through Supabase's transaction-mode pooler. The schema is managed by Alembic migrations, not the `supabase/schema.sql` (which is a legacy seed file).

- Connection setup: [database.py:6-25](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/core/database.py#L6-L25)
- Pool tuning: `pool_pre_ping=True`, configurable pool size/overflow/timeout — [database.py:14-23](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/core/database.py#L14-L23)

### AI/LLM Integration (Triple-provider)

The backend wires **three** LLM providers through a central routing layer:

| Provider | When used | Routing rule | Config |
|---|---|---|---|
| **Google Gemini** | Grader (`gemini-3.5-flash-lite`), Syllabus extraction (`gemini-3.6-flash`), Career tree gen (`gemini-3.6-flash`), Companion classifier (`gemini-3.5-flash-lite`), Embeddings (`gemini-embedding-001`) | Model id starts with `gemini*` | [config.py:49,95,109,129,135,141](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/core/config.py#L49) |
| **Groq** | Fallback for grader (if model id is non-gemini, e.g. `openai/gpt-oss-120b`) | Any model id NOT starting with `gemini` | [llm.py:43](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/services/llm.py#L43) |
| **Anthropic** | Fallback for syllabus extraction (if `SYLLABUS_MODEL=claude-*`) | Wired in `syllabus.py`, separate routing — not via `llm.py` | [config.py:66](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/core/config.py#L66) |
| **OpenAI-compat** | Career tree gen fallback (DeepSeek, Qwen, etc.) | Model id is neither `gemini*` nor `claude*` | [config.py:82-91](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/core/config.py#L82-L91) |

Central dispatch: [llm.py](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/services/llm.py) — `provider_for(model)` derives provider from the model id string. `syllabus.py` and `career_tree.py` carry separate routing copies (documented as deliberate, see [llm.py:22-24](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/services/llm.py#L22-L24)).

---

## 2. Architecture — Actual Request Flow

### Frontend → Backend

```
Browser (React SPA on Vercel)
  └─ apiFetch() ← lib/api.js
       ├─ Gets Supabase JWT from supabase.auth.getSession()
       ├─ Attaches as Bearer token
       └─ fetch() → https://retainhq.onrender.com/api/{resource}

Backend (FastAPI on Render)
  └─ CORSMiddleware (env-driven allow-list)
       └─ Router (app.include_router, all under /api/*)
            └─ Depends(get_current_user) ← deps.py
                 ├─ HTTPBearer extracts token
                 ├─ verify_token() ← security.py
                 │    ├─ PyJWKClient fetches Supabase JWKS
                 │    └─ jwt.decode(ES256, audience="authenticated")
                 └─ Business logic → AsyncSession (asyncpg → Supabase Postgres)
```

**Key paths:**

| Pattern | Route file | Notable |
|---|---|---|
| Activities CRUD | [routes/activities.py](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/api/routes/activities.py) | Creates FSRS card via `initial_review_for_activity()` |
| Reviews (SRS loop) | [routes/reviews.py](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/api/routes/reviews.py) | `apply_fsrs()` on completion; optional LLM grading |
| Career coach | [routes/career.py](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/api/routes/career.py) | LLM tree generation → roadmap creation |
| Syllabus upload | [routes/syllabus.py](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/api/routes/syllabus.py) | PDF → LLM → roadmap extraction |
| Teacher dashboard | [routes/classrooms.py](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/api/routes/classrooms.py) | Gap map, per-student mastery |
| Companion sync | [routes/companion.py](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/api/routes/companion.py) | Extension → session logs |
| LeetCode problems | [routes/problems.py](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/api/routes/problems.py) | Problem catalog + capture flow |
| Internal cron | [routes/internal.py](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/api/routes/internal.py) | Secret-gated reminder trigger |

**16 routers** registered in [main.py:54-70](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/main.py#L54-L70). All authenticated routes use `Depends(get_current_user)`. Admin routes use `Depends(get_admin_user)` which checks `current_user.email == ADMIN_EMAIL`.

### Extension → Backend

The Companion extension authenticates via the same Supabase JWT (user signs in via `chrome.identity` OAuth → Supabase). It POSTs sessions to `/api/companion/*`, which hits the same `get_current_user` dependency.

---

## 3. Auth Implementation (exact code)

### Backend JWT Verification

```python
# security.py:16-20 — JWKS client
_jwks_client = PyJWKClient(
    f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json",
    cache_keys=True, lifespan=3600,
)

# security.py:22-56 — Token verification
def verify_token(token: str) -> SupabaseUser:
    signing_key = _jwks_client.get_signing_key_from_jwt(token)
    payload = jwt.decode(
        token, signing_key.key,
        algorithms=["ES256"],  # ES256 ONLY — HS256 removed to prevent algorithm-confusion
        audience="authenticated",
    )
```

- **Algorithm**: **ES256** (ECDSA with P-256 + SHA-256) — asymmetric, public key fetched from Supabase JWKS endpoint
- **JWKS caching**: keys cached for 3600s (`lifespan=3600`)
- **Audience check**: `audience="authenticated"` — [security.py:43](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/core/security.py#L43)
- **Role check**: `payload["role"] != "authenticated"` → 403 — [security.py:46-50](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/core/security.py#L46-L50)
- **Expiry handling**: `jwt.ExpiredSignatureError` → 401 — [security.py:58-63](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/core/security.py#L58-L63)
- **JWKS unavailable**: `PyJWKClientError` → 503 (retry-friendly) — [security.py:31-37](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/core/security.py#L31-L37)

### Auth Dependency Chain

```python
# deps.py:54 — The core auth dependency
async def get_current_user(credentials = Depends(optional_security)) -> SupabaseUser:

# deps.py:74 — Optional (for public reads)
async def get_optional_user(credentials = Depends(optional_security)) -> Optional[SupabaseUser]:

# deps.py:87 — Admin gate
async def get_admin_user(current_user = Depends(get_current_user)) -> SupabaseUser:
```

### Frontend Auth

- **Provider**: Supabase Auth (Google OAuth via `supabase.auth.signInWithOAuth`) — [AuthContext.jsx:42-68](file:///c:/Users/aloks/Desktop/RetainHQ/frontend/src/lib/AuthContext.jsx#L42-L68)
- **Token attachment**: `apiFetch()` calls `supabase.auth.getSession()`, attaches `session.access_token` as `Bearer` — [api.js:51-61](file:///c:/Users/aloks/Desktop/RetainHQ/frontend/src/lib/api.js#L51-L61)
- **Session handling**: Supabase JS client handles `autoRefreshToken: true`, `persistSession: true` — [supabase.js:6-12](file:///c:/Users/aloks/Desktop/RetainHQ/frontend/src/lib/supabase.js#L6-L12)
- **401 handling**: dispatches `retainhq:unauthorized` custom event → AuthContext signs out — [api.js:98-101](file:///c:/Users/aloks/Desktop/RetainHQ/frontend/src/lib/api.js#L98-L101), [AuthContext.jsx:73-78](file:///c:/Users/aloks/Desktop/RetainHQ/frontend/src/lib/AuthContext.jsx#L73-L78)

### Dev Auth Bypass

Both frontend and backend have a `DEV_AUTH_BYPASS` flag, gated so it **cannot** ship to production:
- Backend: requires `DEBUG=true` — validated at startup with a `model_validator` that **crashes the process** if `DEV_AUTH_BYPASS=true` without `DEBUG=true` — [config.py:178-191](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/core/config.py#L178-L191)
- Frontend: gated on `import.meta.env.DEV` (Vite tree-shakes it from prod builds) — [AuthContext.jsx:27-28](file:///c:/Users/aloks/Desktop/RetainHQ/frontend/src/lib/AuthContext.jsx#L27-L28)

---

## 4. Scheduling / Grading Logic

### Spaced Repetition: FSRS-4.5

> **Not SM-2.** The scheduler implements **FSRS-4.5** (Free Spaced Repetition Scheduler), the published successor to SM-2.

**Core file**: [services/scheduler.py](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/services/scheduler.py) (229 lines, complete)

**Published 19-weight parameter set** — [scheduler.py:107-111](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/services/scheduler.py#L107-L111):
```python
FSRS_WEIGHTS = (
    0.4072, 1.1829, 3.1262, 15.4722, 7.2102, 0.5316, 1.0651, 0.0234,
    1.616, 0.1544, 1.0824, 1.9813, 0.0953, 0.2975, 2.2042, 0.2407,
    2.9466, 0.5034, 0.6567,
)
DESIRED_RETENTION = 0.9
```

**Key functions:**

| Function | Line | Purpose |
|---|---|---|
| `apply_fsrs(activity, rating, now)` | [scheduler.py:191](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/services/scheduler.py#L191) | Main entry: advances memory state, returns next `Review` |
| `initial_review_for_activity()` | [scheduler.py:40](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/services/scheduler.py#L40) | First review: +1 day by default, or immediate for onboarding demo |
| `_init_stability(rating)` | [scheduler.py:141](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/services/scheduler.py#L141) | FSRS `S₀(g) = w_{g-1}` |
| `_init_difficulty(rating)` | [scheduler.py:146](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/services/scheduler.py#L146) | FSRS `D₀(g) = w₄ - exp(w₅(g-1)) + 1` |
| `_next_stability(S, D, R, g)` | [scheduler.py:163](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/services/scheduler.py#L163) | Post-lapse and success stability update |
| `_retrievability(elapsed, S)` | [scheduler.py:158](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/services/scheduler.py#L158) | `(1 + factor * elapsed/S)^decay` |
| `_interval_from_stability(S)` | [scheduler.py:186](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/services/scheduler.py#L186) | Interval at target retention |
| `fsrs_rating_from_outcome()` | [scheduler.py:125](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/services/scheduler.py#L125) | Maps RetainHQ's `(rating, recalled)` → FSRS 1-4 scale |

**Per-card state** lives on `Activity`: `stability` and `difficulty_fsrs` (both `NULL` until first graded review). Legacy SM-2 columns (`ease_factor`, `repetitions`) are still written to maintain NOT NULL constraints but are not used for scheduling. — [models.py:114-126](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/models/models.py#L114-L126)

**Session cap**: `REVIEW_SESSION_CAP = 10` — prevents the SRS death spiral — [scheduler.py:37](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/services/scheduler.py#L37)

### LLM Grading

**Core file**: [services/grader.py](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/services/grader.py) (473 lines)

**Feature gate**: `GRADER_ENABLED` (default `False`) — [config.py:50](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/core/config.py#L50). All grading endpoints check this and return 404 when off.

**Four grading modes:**

| Mode | Function | Line | Purpose |
|---|---|---|---|
| Free recall | `grade_recall(topic, key_memory, user_answer)` | [grader.py:116](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/services/grader.py#L116) | One-shot grade of freeform answer vs key_memory |
| Question set gen | `generate_question_items(topic, depth, ...)` | [grader.py:242](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/services/grader.py#L242) | Generates 2-5 short-answer questions + reference answers |
| Question set grade | `grade_question_set(topic, key_memory, qa_pairs)` | [grader.py:401](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/services/grader.py#L401) | Grades a set of answers in one call |
| Test fillup | `grade_fillup(question, reference, answer)` | [grader.py:454](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/services/grader.py#L454) | Fill-in-the-blank test grading |
| Capture assist | `suggest_key_points(topic, draft)` | [grader.py:381](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/services/grader.py#L381) | Recognition prompts for stuck learners |

**Validation**: All LLM responses are validated with **Pydantic** (`model_validate_json`) — e.g. `GraderVerdict`, `QuestionSetGrade`, `FillupVerdict`. When Gemini is the provider, native `response_schema` structured output is used ([llm.py:71](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/services/llm.py#L71)); for Groq, `response_format={"type":"json_object"}` plus prompt instructions.

### Evidence / Mastery System (Career Coach)

A second evaluation layer separate from FSRS, for career-goal mastery tracking:

- **Weight table**: [evidence_weights.py](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/services/evidence_weights.py) — event types (`RECALL_GRADED`, `PROBLEM_SOLVED`, etc.), trust tiers (`T1_verified_external` → `T4_claimed`), per-(difficulty, assistance) weights
- **Evidence engine**: [evidence.py](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/services/evidence.py) — `fold_events()` replays events → `NodeMasteryResult`; `record_event()` + `recompute_node()` for DB writes
- **Mastery computation**: [mastery.py](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/services/mastery.py) — `compute_node_status()` → `"untouched" | "weak" | "developing" | "strong"` from test attempts + FSRS recall history

---

## 5. Dead Code / Unfinished Features

### Confirmed Dead or Partially Wired

| Item | Status | Evidence |
|---|---|---|
| **`DsaDev` route** (`/dsa-dev`) | Temp pilot harness, comment says `TEMP` | [App.jsx:37](file:///c:/Users/aloks/Desktop/RetainHQ/frontend/src/App.jsx#L37) — `// TEMP: DSA pilot harness (/dsa-dev)` |
| **`ComingSoon` component** | Used in `KnowledgeVault` — a placeholder for an unimplemented feature | [KnowledgeVault.jsx:5,189](file:///c:/Users/aloks/Desktop/RetainHQ/frontend/src/KnowledgeVault.jsx#L5) |
| **LLM grader** | Code is complete but **gated off** by default (`GRADER_ENABLED: bool = False`) — explicitly labeled `EXPERIMENT (frozen)` | [config.py:50](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/core/config.py#L50), [grader.py:1-2](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/services/grader.py#L1-L2) |
| **`supabase/schema.sql`** | Legacy seed file (hardcoded UUIDs for one roadmap). The actual schema is managed by Alembic. This file appears **unused** in any workflow. | [supabase/schema.sql](file:///c:/Users/aloks/Desktop/RetainHQ/supabase/schema.sql) |
| **SM-2 columns on Activity** | `ease_factor`, `repetitions` are written but **not used for scheduling** — kept only to satisfy NOT NULL constraints from before the FSRS migration | [scheduler.py:30](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/services/scheduler.py#L30), [models.py:120-123](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/models/models.py#L120-L123) |
| **Root-level Python scripts** | `fix.py`, `patch_log_activity.py`, `process_json*.py`, `update_file*.py`, `update_files.py` — one-off migration/data scripts left in the repo root | [project root](file:///c:/Users/aloks/Desktop/RetainHQ) |
| **`routeszip.zip`** | A zip file sitting inside `backend/app/api/` — unclear purpose, likely a snapshot | [backend/app/api/routeszip.zip](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/api) |
| **`_image-staging` + `scratch`** | Staging directories at the project root | [project root](file:///c:/Users/aloks/Desktop/RetainHQ) |
| **`Groq` in `[project.optional-dependencies].experiment`** | Groq is already in the main deps — the `experiment` extra re-lists it with a comment "frozen intelligence features, not part of launch install" but it's now a core dep | [pyproject.toml:31-35](file:///c:/Users/aloks/Desktop/RetainHQ/backend/pyproject.toml#L31-L35) |

### Documented but Partially Implemented

| Feature (per docs/) | Status | Evidence |
|---|---|---|
| **SPEC-teacher-dashboard.md** | Implemented — Classroom, ClassroomMember, ClassroomRoadmap models + routes + tests exist | Routes in [classrooms.py](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/api/routes/classrooms.py), tests in [test_classrooms.py](file:///c:/Users/aloks/Desktop/RetainHQ/backend/tests/test_classrooms.py) |
| **SPEC-leetcode-retention.md** | Implemented — Problem, ProblemConcept, ProblemAlias, ConceptCard models + companion capture + approach inference | [models.py:450-544](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/models/models.py#L450-L544) |
| **Career Coach phase 3 (scheduler priorities)** | Documented in `SPEC-career-coach-phase3.md` + planner.py exists, but the `daily_minutes` / sprint fields on `CareerGoal` are stored but the full daily planner is a service, not yet the primary UX driver | [planner.py](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/services/planner.py), [models.py:402-404](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/models/models.py#L402-L404) |
| **SPEC-test-runtime.md** | Implemented — TestAttempt model + tests routes + LLM fillup grading (gated on GRADER_ENABLED) | [routes/tests.py](file:///c:/Users/aloks/Desktop/RetainHQ/backend/app/api/routes/tests.py) |
| **SEO static lesson pages** | Documented in `docs/SEO-IMPLEMENTATION.md`; `postbuild` script `generate-lesson-html.mjs` exists | [package.json:12](file:///c:/Users/aloks/Desktop/RetainHQ/frontend/package.json#L12) |
| **`design-system/`** | Directory with `components/`, `foundations/`, `marketing/` subdirs — appears to be documentation/assets, not code consumed by the build | [design-system/](file:///c:/Users/aloks/Desktop/RetainHQ/design-system) |

---

## 6. Deployment: What's Live vs Local-Only

### ✅ Genuinely Deployed

| Component | Host | Evidence |
|---|---|---|
| **Frontend** | **Vercel** (retainhq.app) | [frontend/vercel.json](file:///c:/Users/aloks/Desktop/RetainHQ/frontend/vercel.json) — 648 redirect rules + SPA rewrite. Domain `retainhq.app` referenced throughout SEO code ([useSeo.js:3](file:///c:/Users/aloks/Desktop/RetainHQ/frontend/src/lib/useSeo.js#L3)) |
| **Backend** | **Render** (retainhq.onrender.com) | Dockerfile builds for Render (`${PORT:-8000}`) — [Dockerfile:12](file:///c:/Users/aloks/Desktop/RetainHQ/backend/Dockerfile#L12). Health endpoint pinged by keep-alive workflow: `curl https://retainhq.onrender.com/health` — [keep-alive.yml:21](file:///c:/Users/aloks/Desktop/RetainHQ/.github/workflows/keep-alive.yml#L21). Extension hardcodes this URL — [extension/src/config.ts:12](file:///c:/Users/aloks/Desktop/RetainHQ/extension/src/config.ts#L12) |
| **Database** | **Supabase** (free plan, ap-south-1) | Confirmed by JWKS URL pattern in security.py + backup workflow referencing `pooler.supabase.com` — [backup-db.yml:29](file:///c:/Users/aloks/Desktop/RetainHQ/.github/workflows/backup-db.yml#L29) |
| **Extension** | **Chrome Web Store** + **Firefox AMO** | Separate build targets: `build:chrome`, `build:firefox` — [extension/package.json:9-10](file:///c:/Users/aloks/Desktop/RetainHQ/extension/package.json#L9-L10). Firefox gecko id: `companion@retainhq.app` — [manifest.json:41](file:///c:/Users/aloks/Desktop/RetainHQ/extension/manifest.json#L41). AMO submission docs exist: [IMPLEMENTATION-amo-submission.md](file:///c:/Users/aloks/Desktop/RetainHQ/docs/IMPLEMENTATION-amo-submission.md) |

### ✅ Live CI/CD (GitHub Actions)

| Workflow | Schedule | Purpose |
|---|---|---|
| [keep-alive.yml](file:///c:/Users/aloks/Desktop/RetainHQ/.github/workflows/keep-alive.yml) | Every 10 min | Pings Render `/health` to prevent free-tier sleep |
| [backup-db.yml](file:///c:/Users/aloks/Desktop/RetainHQ/.github/workflows/backup-db.yml) | 19:00 UTC daily | `pg_dump` → AES256-encrypted → 90-day artifact. Includes data-loss canary. |
| [reminders.yml](file:///c:/Users/aloks/Desktop/RetainHQ/.github/workflows/reminders.yml) | 01:30 UTC daily | POSTs to `/api/internal/send-reminders` (email + web push) |
| [validate-content.yml](file:///c:/Users/aloks/Desktop/RetainHQ/.github/workflows/validate-content.yml) | On push to `content/**` | Runs `validate.py` + `validate_career_templates.py` |

### ⚠️ Noteworthy Deployment Details

- **No Docker Compose / K8s** — single Dockerfile for Render. No multi-service orchestration.
- **No frontend CI** — no build/test workflow for the React app. Vercel handles build on push.
- **No backend CI for tests** — 30 test files exist ([backend/tests/](file:///c:/Users/aloks/Desktop/RetainHQ/backend/tests)) but no GitHub Actions workflow runs them automatically. Tests are local-only (`pytest`).
- **Render free tier** — the keep-alive workflow confirms this. Cold boot is ~30-50s per [keep-alive.yml:4](file:///c:/Users/aloks/Desktop/RetainHQ/.github/workflows/keep-alive.yml#L4).
- **Supabase free plan** — no daily backups or PITR from Supabase; the nightly `backup-db.yml` workflow is the only backup, written after a data-loss incident (documented at [backup-db.yml:4-6](file:///c:/Users/aloks/Desktop/RetainHQ/.github/workflows/backup-db.yml#L4-L6)).
- **Sentry** — backend + frontend, gated on `SENTRY_DSN` — live when the env var is set.
- **PostHog** — server + client-side, gated on `POSTHOG_API_KEY`.
- **Resend** — email reminders, gated on `RESEND_API_KEY`.
- **Web Push (VAPID)** — gated on `VAPID_PRIVATE_KEY` + `VAPID_PUBLIC_KEY`.

---

## Summary Table

| Claim you might make | Accurate? | Nuance |
|---|---|---|
| "React frontend" | ✅ | React 19 + Vite 8, NOT Next.js |
| "FastAPI backend" | ✅ | With SQLModel ORM, Alembic migrations, asyncpg |
| "Supabase Postgres" | ✅ | Free plan, transaction pooler |
| "Supabase Auth" | ✅ | Google OAuth, ES256 JWTs verified server-side via JWKS |
| "FSRS spaced repetition" | ✅ | FSRS-4.5 with published 19-weight params. **Not SM-2** (SM-2 columns are vestigial). |
| "LLM grading" | ⚠️ | Code exists and is complete, but **gated off by default** (`GRADER_ENABLED=False`). Say "built, feature-flagged" not "ships to users". |
| "Multi-provider LLM" | ✅ | Gemini (primary), Groq, Anthropic, OpenAI-compat — provider derived from model id |
| "Browser extension" | ✅ | MV3, Chrome + Firefox, tracks LeetCode/NeetCode/YouTube/Coursera/Notion/LLM chats/PDFs |
| "Deployed on Vercel + Render" | ✅ | Frontend on Vercel (retainhq.app), backend on Render (free tier) |
| "Has CI/CD" | ⚠️ | Has 4 GitHub Actions workflows (backup, keep-alive, reminders, content validation) but **no automated test pipeline** for frontend or backend |
| "Career coach / mastery tracking" | ✅ | Evidence-based mastery system (LearningEvent → NodeMastery), separate from FSRS |
| "Teacher dashboard" | ✅ | Classrooms, join codes, gap map — implemented and has tests |
