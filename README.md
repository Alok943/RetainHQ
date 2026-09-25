# RetainHQ

**Track what you remember, not what you complete.**

RetainHQ is an engineering learning-retention platform designed to solve the "learning evaporation" problem — where developers study for dozens of hours only to forget 80%+ of concepts within weeks. It combines automated study capture via browser extensions, structured roadmaps with client-side interactive code runtimes, a mathematically rigorous spaced repetition engine (**FSRS-4.5**), and an evidence-based career mastery tracking system.

- **Web Application**: [retainhq.app](https://retainhq.app)
- **Browser Companion**: Available for [Chrome Web Store](https://chromewebstore.google.com) and [Firefox AMO](https://addons.mozilla.org/firefox/addon/retainhq-companion/) (`companion@retainhq.app`)
- **API Health**: [`https://retainhq.onrender.com/health`](https://retainhq.onrender.com/health)

---

## System Implementation Status

To provide an honest and transparent view for users, evaluators, and interviewers, the platform's features are classified by implementation state based on direct source-code analysis:

| Subsystem / Feature | Implementation Status | Technical Details |
|---|---|---|
| **Spaced Repetition (FSRS-4.5)** | **Implemented & Live** | 19-weight parameter set, target retention 0.9, continuous stability & difficulty, 10-review daily session cap with rollover. (SM-2 columns are vestigial). |
| **Authentication & Authorization** | **Implemented & Live** | Google OAuth via Supabase Auth → Asymmetric ES256 JWT → Server-side JWKS validation via `PyJWKClient` (3600s key cache). |
| **Browser Companion Extension** | **Implemented & Live** | Manifest V3 (TypeScript 6.0 + Vite CRXJS) for Chrome and Firefox. Captures LeetCode, NeetCode, YouTube, Coursera, Notion, LLM chats, and PDFs. |
| **Interactive Roadmaps & Lessons** | **Implemented & Live** | 10 seeded curricula. List view, React Flow map view, PDF progress export. Client-side WASM runtimes (Pyodide for Python, PGlite for SQL) and SVG process animations. |
| **Lesson-to-Review Bridge** | **Implemented & Live** | Idempotent "Add to reviews" button on lessons creates FSRS cards linked via `activities.node_id`. |
| **Classroom & Teacher Dashboard** | **Implemented & Live** | Teacher-created classrooms, invite/join codes, student rosters, and aggregate "Gap Map" class weakness analysis. Fully tested in [`backend/tests/test_classrooms.py`](backend/tests/test_classrooms.py). |
| **LeetCode Problem Retention** | **Implemented & Live** | Problem catalog, alias resolution (NeetCode → LeetCode), concept mapping, and solution approach inference. |
| **Automated Operations (CI/CD)** | **Implemented & Live** | GitHub Actions workflows for Render free-tier keep-alive (10-min ping), encrypted daily database backups (AES-256 + canary), daily reminder cron, and content validation. |
| **LLM Recall Grader & Question Mode** | **Implemented & Live** | Multi-mode AI evaluation in [`backend/app/services/grader.py`](backend/app/services/grader.py) (Gemini / Groq) is active in production (`GRADER_ENABLED = True`). Evaluates free-recall against key memories, generates short-answer questions, and provides advisory rating chips. |
| **Interactive Test Runtime** | **Implemented & Live** | Test attempts, objective scoring, and fill-in-the-blank freeform LLM grading are live and active with `GRADER_ENABLED = True`. |
| **Career Coach & Evidence Engine** | **Live Core / Partial UX** | Evidence-based mastery engine ([`backend/app/services/evidence.py`](backend/app/services/evidence.py), T1–T4 trust tiers, status folding) is live. Daily planner service ([`backend/app/services/planner.py`](backend/app/services/planner.py)) exists, but full daily sprint UX integration is in progress. |
| **Syllabus PDF Extraction** | **Partially Implemented** | PDF extraction via LLM into structured roadmaps is implemented with daily/lifetime quotas; model-dependent. |
| **Automated Test CI Pipeline** | **Unimplemented / Local-Only** | 30 test files exist in [`backend/tests/`](backend/tests), but no GitHub Actions CI workflow currently runs them automatically on push. Frontend has no automated CI test pipeline. |

---

## The Core Learning Loop

Every feature in RetainHQ directly feeds or protects the central learning loop:

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│     LOG      │ ───► │   SCHEDULE   │ ───► │    RECALL    │ ───► │     RATE     │ ───► │    RETAIN    │
│ Capture core │      │ Tomorrow (+1)│      │ Active gate  │      │ FSRS grade   │      │ Dynamic next │
│  key memory  │      │  Session cap │      │ before reveal│      │ (Again..Easy)│      │   interval   │
└──────────────┘      └──────────────┘      └──────────────┘      └──────────────┘      └──────────────┘
```

1. **Log & Capture**:
   - **Manual**: Log what was learned into a single, focused **Key Memory** (capped at 500 characters).
   - **From Lessons**: Click "Add to reviews" on any roadmap lesson to convert it into a tracking card (`source_type='lesson'`).
   - **Browser Companion**: Automatically detect LeetCode solves, YouTube lectures, or Coursera modules and ingest them as study sessions.
2. **Schedule**:
   - New cards are scheduled for **tomorrow (+1 day)** by default. Immediate testing only tests short-term working memory and leads to review fatigue.
   - **Onboarding Exception**: A user's very first card receives a demo review *due now* so they experience the full loop immediately upon signing up.
   - **Daily Session Cap (`REVIEW_SESSION_CAP = 10`)**: The due queue and dashboard badge are capped at 10 reviews per day (oldest-first). Overdue items roll forward rather than accumulating into a demoralizing backlog of 50+ cards.
3. **Recall**:
   - The review screen enforces retrieval practice: the user must actively commit a written answer *before* revealing the reference Key Memory.
4. **Rate**:
   - The user rates their recall (`Again`, `Hard`, `Good`, `Easy`), driving the FSRS scheduler. Advisory AI feedback (`GRADER_ENABLED = True`) evaluates the user's free-recall response against the stored key memory and suggests a rating chip, while the user retains the final rating decision.
5. **Retain**:
   - FSRS recalculates memory stability and schedules the next review date to target a 90% retention rate. The spacing interval expands as memory consolidates.

---

## System Architecture

The following diagram illustrates the complete, deployed full-stack architecture:

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                                         CLIENTS                                          │
│                                                                                          │
│   React 19 SPA (Vercel)                                   Browser Companion (MV3)        │
│   - Vite 8.0, Tailwind, React Router                      - Chrome Web Store             │
│   - React Flow, Pyodide/PGlite WASM                       - Firefox AMO                  │
│   - In-memory auth session                                - Content scripts & background │
└───────────────────────────┬──────────────────────────────────────────┬───────────────────┘
                            │                                          │
                            ▼                                          ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                                AUTHENTICATION & IDENTITY                                 │
│                                                                                          │
│   Supabase Auth (Google OAuth on web / chrome.identity in extension)                     │
│   └─► Issues Asymmetric ES256 JWT (ECDSA P-256 + SHA-256)                                │
└───────────────────────────┬──────────────────────────────────────────┬───────────────────┘
                            │ Bearer <ES256 JWT>                       │ Bearer <ES256 JWT>
                            └────────────────────┬─────────────────────┘
                                                 ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                            BACKEND API GATEWAY (FastAPI / Render)                        │
│                                                                                          │
│   CORSMiddleware: Explicit origin allow-list (https://retainhq.app)                      │
│   Security Layer: PyJWKClient fetches & caches Supabase JWKS (3600s TTL)                 │
│   JWT Verification: Enforces ES256, audience="authenticated", role="authenticated"       │
│   Dependencies: get_current_user, get_optional_user, get_admin_user                      │
│   17 API Routers mounted under /api/*                                                    │
└────────────────────────────────────────┬─────────────────────────────────────────────────┘
                                         │
                 ┌───────────────────────┴────────────────────────┐
                 ▼                                                ▼
┌──────────────────────────────────────────────┐   ┌──────────────────────────────────────────────┐
│             CORE DOMAIN SERVICES             │   │            AI & LLM ROUTING GATEWAY          │
│                                              │   │                                              │
│ ├─ FSRS-4.5 Scheduler                        │   │ Central Provider Dispatch (llm.py):          │
│ │  (19 parameters, S & D update, cap=10)     │   │                                              │
│ ├─ Career Coach & Evidence Engine            │   │ ├─ Google Gemini (Primary)                   │
│ │  (LearningEvent, T1-T4 tiers, NodeMastery) │   │ │  ├─ gemini-3.5-flash-lite (Grader,         │
│ ├─ Classroom & Teacher Service               │   │ │  │     Companion classifier, Approach)     │
│ │  (Join codes, student rosters, Gap Map)    │   │ │  ├─ gemini-3.6-flash (Syllabus, Career)    │
│ ├─ LeetCode Retention Service                │   │ │  └─ gemini-embedding-001 (Embeddings)     │
│ │  (Problem catalog, aliases, approach infer)│   │ ├─ Groq (Grader Fallback)                    │
│ ├─ Interactive Lesson Runtime Engine         │   │ │  └─ openai/gpt-oss-120b (low reasoning)    │
│ │  (Pyodide / PGlite / SVG animations)       │   │ ├─ Anthropic (Syllabus Fallback)             │
│ ├─ Interactive Test Runtime                  │   │ │  └─ claude-* via syllabus.py               │
│ │  (Objective scoring + fillup evaluation)   │   │ └─ OpenAI-Compatible Gateway                 │
│ └─ Syllabus PDF Processor                    │   │    └─ DeepSeek / Qwen via httpx (Career tree)│
│    (PDF extraction with rate limits)         │   │                                              │
│                                              │   │ * LLM Grader is LIVE in production           │
│                                              │   │   (GRADER_ENABLED = True)                    │
└──────────────────────┬───────────────────────┘   └──────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                                 DATA & PERSISTENCE LAYER                                 │
│                                                                                          │
│   SQLModel ORM (SQLAlchemy 2 core) + Alembic database migrations                         │
│   asyncpg async Postgres driver (statement_cache_size=0, pool_pre_ping=True)             │
│   Supabase Managed PostgreSQL (AWS ap-south-1 Mumbai, Transaction Pooler :6543)          │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Tech Stack

### Frontend Application
- **Core Framework**: React 19.2 + Vite 8.0
- **Styling**: Tailwind CSS 3.4 with centralized dark mode class overrides
- **Routing**: react-router-dom 7.16
- **Visuals & 3D**: framer-motion 12.42, Three.js 0.185 with @react-three/fiber 9.6 and @react-three/drei 10.7
- **Roadmap Visualization**: reactflow 11.11 + dagre 0.8
- **Client Runtimes**: Pyodide (CPython in WebAssembly), PGlite (Postgres in WebAssembly), KaTeX (math rendering)
- **Export & Icons**: jsPDF 4.2, lucide-react 1.17, simple-icons 16.23
- **Auth & Analytics**: @supabase/supabase-js 2.106, posthog-js 1.396, @sentry/react 10.65, @vercel/analytics 2.0

### Backend API
- **Framework**: FastAPI ≥0.111 running on Uvicorn ≥0.30 (Python 3.10+)
- **ORM & Migrations**: SQLModel ≥0.0.19 (SQLAlchemy 2 wrapper) + Alembic ≥1.13
- **Database Driver**: asyncpg ≥0.29 (asynchronous PostgreSQL)
- **Configuration & Security**: pydantic-settings ≥2.3, PyJWT ≥2.8 with `cryptography`
- **Communications & Monitoring**: resend ≥2.0 (email), pywebpush ≥2.0 (VAPID web push), posthog ≥3.7, sentry-sdk ≥2.0

### Browser Companion Extension
- **Manifest**: Manifest V3 (MV3) targeting Chrome and Firefox
- **Languages & Tooling**: TypeScript 6.0, Vite 8.1 with @crxjs/vite-plugin 2.0-beta
- **Auth Client**: @supabase/supabase-js 2.110

---

## Authentication & Security Architecture

RetainHQ uses a hardened token-based authentication flow where the frontend and browser extension never communicate directly with the database.

```
Browser / Extension           Supabase Auth                 FastAPI Gateway               Database
        │                           │                              │                         │
   1. Google OAuth                  │                              │                         │
   ────────────────────────────────►│                              │                         │
        │    2. Issues ES256 JWT    │                              │                         │
        │◄──────────────────────────│                              │                         │
        │                                                          │                         │
        │  3. API Request: Bearer <ES256 JWT>                      │                         │
        │─────────────────────────────────────────────────────────►│                         │
        │                           │  4. Fetch JWKS (.well-known) │                         │
        │                           │◄─────────────────────────────│                         │
        │                           │  5. Public Keys Cached (1 hr)│                         │
        │                           │─────────────────────────────►│                         │
        │                           │                              │  6. Query with user_id  │
        │                           │                              │────────────────────────►│
        │                           │                              │◄────────────────────────│
        │  7. Response Data         │                              │                         │
        │◄─────────────────────────────────────────────────────────│                         │
```

1. **Provider**: Supabase Auth handles Google OAuth (via `supabase.auth.signInWithOAuth` in web, `chrome.identity` in the extension).
2. **Asymmetric ES256 Verification**:
   - The backend validates tokens using **ES256** (ECDSA using P-256 and SHA-256). HS256 is explicitly removed to prevent algorithm-confusion attacks.
   - Public keys are fetched from Supabase's JWKS endpoint (`/auth/v1/.well-known/jwks.json`) via `PyJWKClient` and cached for 3,600 seconds (`lifespan=3600`).
   - If the JWKS endpoint is unreachable, a retry-friendly 503 is returned.
3. **Claims Verification**:
   - Strict validation of `audience="authenticated"` and `role="authenticated"`.
   - Expired tokens raise 401 Unauthorized; mismatched roles raise 403 Forbidden.
4. **Client Session Handling**:
   - The frontend's `apiFetch()` helper pulls the current token via `supabase.auth.getSession()` and injects it as an `Authorization: Bearer <token>` header.
   - On receiving a 401 response, `apiFetch` dispatches a `retainhq:unauthorized` event, clearing the session and cleanly returning to the sign-in screen.
5. **Development Auth Bypass Guard**:
   - For local offline development, a `DEV_AUTH_BYPASS` flag exists.
   - **Production Guard**: A Pydantic `@model_validator` in [`backend/app/core/config.py`](backend/app/core/config.py) crashes the backend process immediately on startup if `DEV_AUTH_BYPASS=true` is set without `DEBUG=true`.
   - On the frontend, dev auth is gated behind `import.meta.env.DEV`, which is completely tree-shaken by Vite in production builds.

---

## Spaced Repetition Engine (FSRS-4.5)

RetainHQ uses the **FSRS-4.5 (Free Spaced Repetition Scheduler)** algorithm. **It does not use SM-2.**

Implementation: [`backend/app/services/scheduler.py`](backend/app/services/scheduler.py)

### FSRS-4.5 vs SM-2
Unlike SM-2's discrete, rigid ease ladder ($1 \to 6 \to \text{interval} \times \text{EF}$), FSRS models human memory as a continuous forgetting curve determined by two core parameters per card:
- **Stability ($S$)**: The number of days required for predicted recall probability (retrievability) to fall to the target retention level ($R = 0.9$).
- **Difficulty ($D$, scale 1–10)**: The intrinsic cognitive difficulty of the concept.

Both parameters remain `NULL` until a card's first completed review (`NULL` denotes an uncalibrated card). FSRS achieves ~30% fewer reviews than SM-2 for the same long-term retention rate.

### Parameters & Formulae
The engine uses the published 19-weight parameter set (`FSRS_WEIGHTS`):
```python
FSRS_WEIGHTS = (
    0.4072, 1.1829, 3.1262, 15.4722, 7.2102, 0.5316, 1.0651, 0.0234,
    1.616, 0.1544, 1.0824, 1.9813, 0.0953, 0.2975, 2.2042, 0.2407,
    2.9466, 0.5034, 0.6567,
)
DESIRED_RETENTION = 0.9
```

- **Retrievability**:
  $$R(t, S) = \left(1 + \text{factor} \cdot \frac{t}{S}\right)^{\text{decay}}$$
- **Outcome Mapping**:
  User feedback (`rating`, `recalled`) maps directly into the FSRS 1–4 scale:
  - Missed recall $\to$ Grade 1 (Again)
  - Rating 'hard' $\to$ Grade 2 (Hard)
  - Rating 'medium' $\to$ Grade 3 (Good)
  - Rating 'easy' $\to$ Grade 4 (Easy)

### Vestigial SM-2 Fields
The `activities` database table retains legacy SM-2 columns (`ease_factor`, `repetitions`). These are vestigial fields written during updates solely to satisfy historical database `NOT NULL` constraints and maintain backward compatibility. They have **no influence** on scheduling intervals.

### Anti-Fatigue Safeguards
- **Deliberate Delay**: The first review is scheduled for tomorrow (+1 day). Testing immediately after logging measures working memory, not retention.
- **Session Cap (`REVIEW_SESSION_CAP = 10`)**: Daily due reviews are capped at 10 cards (oldest first). Overdue cards beyond 10 roll forward to subsequent sessions, preventing the classic "50 overdue reviews" SRS burnout cycle.

---

## AI & Multi-Provider LLM Architecture

RetainHQ features a unified multi-provider routing layer that dispatches requests based on model identifier strings:

Routing Module: [`backend/app/services/llm.py`](backend/app/services/llm.py)

| Provider | Model ID / Branch | Usage in RetainHQ | Protocol / Integration |
|---|---|---|---|
| **Google Gemini (Primary)** | Starts with `gemini*` | • Grader: `gemini-3.5-flash-lite`<br>• Syllabus extraction: `gemini-3.6-flash`<br>• Career tree generation: `gemini-3.6-flash`<br>• Companion classifier: `gemini-3.5-flash-lite`<br>• Approach inference: `gemini-3.5-flash-lite`<br>• Embeddings: `gemini-embedding-001` | Native SDK (`google-genai`), enforces strict JSON output schemas via `response_schema`. |
| **Groq (Grader Fallback)** | Non-Gemini grader IDs (e.g. `openai/gpt-oss-120b`) | Optional fallback for recall grader and question generation. | Groq SDK with `reasoning_effort=low` and `response_format={"type":"json_object"}`. |
| **Anthropic (Syllabus Fallback)** | `SYLLABUS_MODEL=claude-*` | Fallback for complex academic syllabus PDF structuring. | Dedicated Anthropic API client in `syllabus.py`. |
| **OpenAI-Compatible** | Non-Gemini / non-Claude career models | Career tree generation fallback for DeepSeek, Qwen, or local vLLM instances. | Direct `httpx` HTTP requests sending JSON schemas in prompt instructions. |

### LLM Grader Status: Implemented & Live in Production
The LLM recall grader in [`backend/app/services/grader.py`](backend/app/services/grader.py) is **implemented, live, and enabled in production** (`GRADER_ENABLED = True`). Powered primarily by Google Gemini (`gemini-3.5-flash-lite`, with Groq `openai/gpt-oss-120b` fallback), it runs automatically during review sessions.

Live Capabilities:
1. **Free-Recall Grader** (`POST /api/reviews/{id}/grade`): Evaluates user recall strictly against the stored `key_memory` ground truth (never outside model knowledge). Returns `{verdict, recalled, feedback, revision_note, related_subtopics}` validated with Pydantic. It is advisory — the user confirms the final rating decision.
2. **Question Mode** (`POST /api/reviews/{id}/questions` + `/grade-questions`): Deconstructs `key_memory` into 2–3 short-answer questions to probe concept boundaries.
3. **Capture Assist** (`POST /api/activities/suggest-key-points`): Suggests recognized sub-points for a topic at log time.
4. **Graceful Fallback**: If an LLM call fails or times out, the UI gracefully degrades to manual self-reported recall without interrupting the review flow.

---

## Career Coach & Evidence-Based Mastery System

The **Career Coach** is a distinct evaluation system independent of the card-level FSRS scheduler. While FSRS manages micro-retention for discrete flashcards, the Career Coach tracks macroscopic engineering competency across full skill trees.

Implementation: [`backend/app/services/evidence.py`](backend/app/services/evidence.py), [`backend/app/services/evidence_weights.py`](backend/app/services/evidence_weights.py), [`backend/app/services/mastery.py`](backend/app/services/mastery.py)

### Evidence Aggregation & Trust Tiers
Every interaction produces a `LearningEvent` assigned to a verifiable trust tier:
- **T1 (Verified External)**: Verified external data (e.g. LeetCode problem solve synced via browser companion).
- **T2 (Verified Internal)**: Objective internal test attempts and runtime code execution.
- **T3 (Observed)**: Passive study events (e.g. YouTube watch time, documentation reading). T3 evidence is capped at 0.35 mastery weight and cannot advance a node beyond "developing".
- **T4 (Claimed)**: Unverified self-reported completion.

### Node Mastery Calculation
The mastery engine calculates node status as one of four discrete levels:
$$\text{Status} \in \{\text{"untouched"}, \text{"weak"}, \text{"developing"}, \text{"strong"}\}$$
- If objective test results exist ($\ge 2$ attempts), accuracy dictates status ($< 50\%$ weak, $< 80\%$ developing, $\ge 80\%$ strong).
- If test evidence is below the floor, status falls back to FSRS stability and recall history (stability $< 7$ days marks a concept as weak/at-risk).

### Daily Planner Status
The daily study planning service ([`backend/app/services/planner.py`](backend/app/services/planner.py)) calculates targeted daily study sprints based on target career goal deadlines. The service logic is implemented and covered by unit tests, but full frontend integration into the primary dashboard is **partially implemented**.

---

## Browser Companion Extension

The RetainHQ Companion is a Manifest V3 browser extension built with TypeScript 6.0 and Vite.

Source Directory: [`extension/`](extension/)

- **Target Platforms**: Distributed for both Chrome (Chrome Web Store) and Firefox (Firefox Add-on / AMO with Gecko ID `companion@retainhq.app`).
- **Target Sites**:
  - **Coding Platforms**: LeetCode (`/problems/*`), NeetCode (`/problems/*`).
  - **Learning Platforms**: Coursera (`/learn/*`), YouTube (`/watch*`).
  - **Tools & Docs**: Notion (`notion.so`), PDF viewers (`*.pdf`).
  - **LLM Interfaces**: ChatGPT, Claude, Gemini (captures study session metadata).
- **Functionality**:
  - Automatically captures study duration and problem completions.
  - Ingests LeetCode and NeetCode submissions into the backend problem catalog.
  - Synchronizes session logs to `/api/companion/sessions` using the user's Supabase JWT.

---

## Specialized Domain Systems

### Teacher & Classroom Dashboard
- **Implementation**: [`backend/app/api/routes/classrooms.py`](backend/app/api/routes/classrooms.py) (tested in [`backend/tests/test_classrooms.py`](backend/tests/test_classrooms.py)).
- **Models**: `Classroom`, `ClassroomMember`, `ClassroomRoadmap`.
- **Capabilities**: Instructors create classrooms, issue join codes, assign roadmaps, and view a class-wide **Gap Map** that visualizes collective conceptual weak points across enrolled students.

### LeetCode Problem Retention & Concept Mapping
- **Implementation**: [`backend/app/api/routes/problems.py`](backend/app/api/routes/problems.py), [`backend/app/models/models.py`](backend/app/models/models.py).
- **Models**: `Problem`, `ProblemConcept`, `ProblemAlias`, `ConceptCard`.
- **Capabilities**: Curated LeetCode problem catalog mapped to roadmap nodes. NeetCode problems are resolved to existing LeetCode IDs via `ProblemAlias` rather than duplicating the catalog. Ingested solutions undergo automated approach inference (`gemini-3.5-flash-lite`) to classify implemented patterns (e.g. Two Pointers vs Hash Map).

### Syllabus Extraction
- **Implementation**: [`backend/app/api/routes/syllabus.py`](backend/app/api/routes/syllabus.py).
- **Capabilities**: Converts uploaded course syllabi (PDF up to 10MB) into structured roadmaps using `gemini-3.6-flash` or Anthropic Claude. Protected by budget safeguards: max 5 extractions per user/day, max 3 lifetime personal roadmaps.

### Interactive Lessons & In-Browser Runtimes
Lessons are authored as static JSON in `content/roadmaps/`, validated by [`content/validate.py`](content/validate.py), and rendered dynamically by `kind`:

| Lesson Kind | Primary Domain | Interactive Runtime / Technology |
|---|---|---|
| `concept` (python) | Python for SWE | **Pyodide** (CPython compiled to WebAssembly) client-side step execution |
| `concept` (sql) | SQL Curriculum | **PGlite** (PostgreSQL compiled to WebAssembly) reactive in-browser DB |
| `theory` | Core CS (OS, Networks, DBMS) | Dependency-free animated SVG diagrams (sequence and cycle flows) |
| `aptitude` | Quantitative Reasoning | Mental models, formula reference, and recall checks |
| `reasoning` | Logical Reasoning | Worked examples and method breakdowns |

All runtime code execution happens **100% client-side** in the browser with zero server compute overhead.

---

## Database & Data Model

Database: Supabase PostgreSQL (AWS `ap-south-1` Mumbai). Managed via **Alembic migrations** (current head `a4b2e9f1c8d3`). `supabase/schema.sql` is a legacy seed file; Alembic is the authoritative schema manager.

Key Tables:
- **`activities`**: Core cards carrying FSRS memory state (`stability`, `difficulty_fsrs`, `interval_days`, `next_review_at`). Legacy SM-2 fields (`ease_factor`, `repetitions`) are vestigial.
- **`reviews`**: Historical log of completed reviews (`rating`, `recalled`, `scheduled_for`, `completed_at`, AI grading results).
- **`roadmaps` & `roadmap_nodes`**: Learning paths and hierarchical topic nodes.
- **`user_progress`**: Node completion status per user.
- **`classrooms`**, **`classroom_members`**, **`classroom_roadmaps`**: Teacher dashboard structure.
- **`problems`**, **`problem_concepts`**, **`problem_aliases`**, **`concept_cards`**: LeetCode catalog and concept mapping.
- **`learning_events`**, **`node_mastery`**: Career Coach evidence and competency logs.
- **`test_attempts`**: Objective test runs and scoring.
- **`feedbacks`**: User feedback submissions.

---

## API Summary (17 Routers)

All routes are mounted under `/api` in [`backend/app/main.py`](backend/app/main.py):

| Route Prefix | Purpose | Auth Requirement |
|---|---|---|
| `/api/activities` | CRUD for captured cards, FSRS card creation, capture assist | `Bearer JWT` |
| `/api/reviews` | Due queue (`/due`, capped at 10), complete review, FSRS calculation, LLM grading | `Bearer JWT` |
| `/api/dashboard` | Due count, daily stats, consistency window, next review timestamp | `Bearer JWT` |
| `/api/roadmaps` | Roadmap list, node hierarchies, node progress upsert | Optional / Authenticated |
| `/api/classrooms` | Teacher classrooms, join codes, rosters, Gap Map analytics | `Bearer JWT` |
| `/api/career` | Career goals, target role skill trees, daily plan generation | `Bearer JWT` |
| `/api/evidence` | Evidence trail logging and node mastery inspection | `Bearer JWT` |
| `/api/companion` | Extension sync, study session logging, LeetCode ingest | `Bearer JWT` |
| `/api/problems` | LeetCode problem catalog search and concept mapping | `Bearer JWT` |
| `/api/syllabus` | PDF upload and LLM roadmap extraction | `Bearer JWT` |
| `/api/tests` | Interactive test generation and submission grading | `Bearer JWT` |
| `/api/push` | Web Push VAPID key delivery and subscription management | `Bearer JWT` |
| `/api/metrics` | User retention and study consistency metrics | `Bearer JWT` |
| `/api/prefs` | User settings and notification preferences | `Bearer JWT` |
| `/api/feedback` | User feedback submission | `Bearer JWT` |
| `/api/admin` | Founder activation funnel and feedback management | Admin Email Gate |
| `/api/internal` | Secret-gated endpoint (`CRON_SECRET`) for automated reminder dispatch | Bearer Cron Secret |

---

## Deployment & Infrastructure

```
┌─────────────────────────┐     ┌─────────────────────────┐     ┌─────────────────────────┐
│     VERCEL (Apex)       │     │     RENDER (Free Tier)  │     │     SUPABASE (Mumbai)   │
│                         │     │                         │     │                         │
│ • retainhq.app          │     │ • retainhq.onrender.com │     │ • Managed PostgreSQL    │
│ • React 19 SPA          │────►│ • FastAPI (Docker)      │────►│ • Transaction Pooler    │
│ • 648 redirect rules    │     │ • 10-min keep-alive ping│     │   (Port 6543, aws-1)    │
│ • SPA rewrite fallback  │     │ • Cold boot ~30-50s     │     │ • Auth / JWKS Issuer    │
└─────────────────────────┘     └─────────────────────────┘     └─────────────────────────┘
```

- **Frontend (Vercel)**: Deployed at `retainhq.app`. [`frontend/vercel.json`](frontend/vercel.json) handles SPA client-side routing rewrites and 648 redirect rules. Auto-deploys on push to `main`.
- **Backend (Render)**: Deployed at `retainhq.onrender.com` via a root [`backend/Dockerfile`](backend/Dockerfile). Operates on Render's free tier (cold boot latency ~30–50s, kept warm via GitHub Actions ping).
- **Database (Supabase)**: Hosted in AWS `ap-south-1` (Mumbai). Connected via Supabase's transaction pooler (`aws-1-ap-south-1.pooler.supabase.com:6543`). The engine sets `statement_cache_size=0`, `prepared_statement_cache_size=0`, and `pool_pre_ping=True`.
- **Browser Extension**: Built via CRXJS and packaged for Chrome Web Store and Firefox AMO.

---

## Testing & CI/CD Pipeline

### Automated GitHub Actions Workflows
The repository currently runs 4 scheduled and event-driven GitHub Actions workflows:

| Workflow | Trigger | Description | Evidence |
|---|---|---|---|
| `keep-alive.yml` | Every 10 min | Pings `https://retainhq.onrender.com/health` to prevent Render free-tier instance sleep | [`.github/workflows/keep-alive.yml`](.github/workflows/keep-alive.yml) |
| `backup-db.yml` | Daily at 19:00 UTC | Dumps database via `pg_dump`, encrypts with AES-256, verifies table-count canary, retains for 90 days | [`.github/workflows/backup-db.yml`](.github/workflows/backup-db.yml) |
| `reminders.yml` | Daily at 01:30 UTC | POSTs to `/api/internal/send-reminders` using `CRON_SECRET` to dispatch email and push notifications | [`.github/workflows/reminders.yml`](.github/workflows/reminders.yml) |
| `validate-content.yml` | Push to `content/**` | Runs `validate.py` and `validate_career_templates.py` on roadmap JSON content | [`.github/workflows/validate-content.yml`](.github/workflows/validate-content.yml) |

### Current CI/CD Limitations (Honest Assessment)
- **No Automated CI Test Suite**: While 30 test files exist in [`backend/tests/`](backend/tests) (covering FSRS scheduling, evidence computation, classrooms, companion sessions, and LLM routing), **there is currently no GitHub Actions workflow configured to run `pytest` on push or pull request**. Tests are executed locally by developers.
- **No Frontend CI Pipeline**: The frontend has no automated CI testing or linting workflow in GitHub Actions. Build verification occurs on Vercel deployment.
- **Single-Container Deployment**: No multi-container orchestration (Docker Compose or Kubernetes); backend runs as a single Render container.

---

## Local Development Setup

### Prerequisites
- Node.js 18+ and npm
- Python 3.10+
- A Supabase project (PostgreSQL + Google OAuth provider configured)

### 1. Frontend Setup
```bash
cd frontend
npm install
npm run dev   # Runs Vite dev server at http://localhost:5173
```

`frontend/.env`:
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_SUPABASE_URL=https://<your-project>.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=<your-anon-key>
```

### 2. Backend Setup
```bash
cd backend
python -m venv .venv
# Activate virtual environment:
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate

pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload   # Interactive docs at http://localhost:8000/docs
```

`backend/.env`:
```env
DATABASE_URL=postgresql+asyncpg://postgres.<ref>:<password>@aws-1-ap-south-1.pooler.supabase.com:6543/postgres
SUPABASE_URL=https://<your-project>.supabase.co
ADMIN_EMAIL=you@example.com

# Multi-Provider LLM Keys:
GEMINI_API_KEY=<gemini-key>          # Primary provider
GROQ_API_KEY=<groq-key>              # Grader fallback
ANTHROPIC_API_KEY=<anthropic-key>    # Syllabus fallback
OPENAI_COMPAT_BASE_URL=              # Optional (DeepSeek / Qwen)
OPENAI_COMPAT_API_KEY=

# Feature Flags:
GRADER_ENABLED=true
DEBUG=false
DEV_AUTH_BYPASS=false
```

> **Database Connection Gotchas**:
> - Always connect via the Supabase **Transaction Pooler** (`...pooler.supabase.com:6543`), not the direct database host (direct is IPv6-only).
> - Shard host is `aws-1`, not `aws-0`.
> - Use an alphanumeric database password (special characters can cause URL encoding issues).

### 3. Browser Extension Setup
```bash
cd extension
npm install
npm run build:chrome    # Outputs unpacked extension to extension/dist
npm run build:firefox   # Builds Firefox target
```
Load the unpacked extension directory into `chrome://extensions` or `about:debugging` in Firefox.

### Running Backend Tests Locally
```bash
cd backend
pytest
```

---

## Project Documentation Directory

| Document | Purpose |
|---|---|
| [`technical_report.md`](technical_report.md) | Exhaustive technical audit report with source code line citations |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | System design, database topology, and request flows |
| [`docs/API.md`](docs/API.md) | Endpoint specifications and parameter schemas |
| [`docs/FLOWS.md`](docs/FLOWS.md) | User interaction and data lifecycles |
| [`docs/SPEC-teacher-dashboard.md`](docs/SPEC-teacher-dashboard.md) | Classroom and Gap Map technical specification |
| [`docs/SPEC-leetcode-retention.md`](docs/SPEC-leetcode-retention.md) | LeetCode retention, problem aliases, and concept cards |
| [`docs/SPEC-career-coach-phase1.md`](docs/SPEC-career-coach-phase1.md) | Evidence engine, trust tiers, and weighting specifications |
| [`docs/SPEC-career-coach-phase2.md`](docs/SPEC-career-coach-phase2.md) | Career tree generation specification |
| [`docs/SPEC-career-coach-phase3.md`](docs/SPEC-career-coach-phase3.md) | Daily study planner specification |
| [`CLAUDE.md`](CLAUDE.md) | Architectural invariants, code guidelines, and development conventions |
