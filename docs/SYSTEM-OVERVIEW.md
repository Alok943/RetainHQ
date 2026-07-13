# RetainHQ — System Overview

**Last full verification: 2026-07-10** (every claim checked against the actual code and the live production database via the read-only Supabase MCP).

> **This is a LIVING document — the single source of truth for system state.** Convention (also in CLAUDE.md): any commit that adds/removes an endpoint or router, changes `models/models.py` or adds a migration, adds a service/integration, changes deploy topology, or moves the security posture **must update the relevant section here and add a Changelog line below, in the same commit**. Claims about prod state (migration head, catalog counts) must be re-verified via the Supabase MCP, not assumed. Roughly monthly — or before any launch/pitch — re-run a full verification pass and bump the date above. It supersedes the stale parts of `ARCHITECTURE.md` (last touched 2026-06-07), `API.md`, and the status sections of `CLAUDE.md`. See the [Stale-docs appendix](#appendix--doc-freshness) at the bottom for what to trust elsewhere.

RetainHQ is a learning-retention platform: **Log Activity → Capture Key Memory → Schedule Reviews (FSRS) → Active Recall → Retain**, with a growing library of interactive lessons (Python/SQL/DSA/aptitude/Core-CS/Physics) that feed cards into that loop. Solo-founder build, live in production at `retainhq.app`.

---

## 1. Architecture

### Topology

```
React SPA (Vercel, root=frontend/)  ←  retainhq.app (apex + www)
  ├─ Supabase Auth (Google OAuth) ──► ES256 JWT
  └─ apiFetch + Bearer JWT ──► FastAPI (Render, root=backend/)
                                  └─ asyncpg ──► Supabase Postgres (Mumbai, transaction pooler :6543)
GitHub Actions (daily 01:30 UTC) ──X-Cron-Secret──► POST /api/internal/send-reminders ──► Resend (email)
PostHog (product analytics): frontend `posthog-js` (no-op without VITE_POSTHOG_KEY) + backend `posthog` (server-truth events, no-op without POSTHOG_API_KEY); same project, keyed by Supabase user id
```

- The frontend talks **only** to FastAPI (`frontend/src/lib/api.js` → `apiFetch`, attaches the Bearer JWT; `optionalAuth` allows guest reads). No direct `supabase.from(...)` DB calls exist in React — Supabase on the client is auth-only.
- FastAPI is the single DB gateway. It connects as `postgres` (table owner), which bypasses RLS; RLS exists to block Supabase's auto-exposed PostgREST/anon-key path (see §4).
- Heavy interactive compute is **client-side**: Pyodide (Python step-tracer), PGlite (in-browser Postgres for SQL lessons), and a pure-JS DSA trace player. Zero server compute for lessons.

### Auth (verified in `backend/app/core/security.py`, `api/deps.py`)

- Supabase Google OAuth issues an **ES256** JWT; FastAPI verifies it via `PyJWKClient` against Supabase's JWKS (keys cached 1 h). **HS256 is removed** (`algorithms=["ES256"]` only — algorithm-confusion attack closed). JWKS outage → clean 503, not a 500.
- Claims checked: signature, `exp`, `aud="authenticated"`, `role == "authenticated"`. `sub` (string UUID) is cast to `uuid.UUID` before queries.
- `get_current_user` → `SupabaseUser` (attribute access). `get_optional_user` powers guest exploration. `get_admin_user` = case-insensitive email match against `ADMIN_EMAIL` (403 otherwise) — interim founder gate, not a role system.
- **`DEV_AUTH_BYPASS` is boot-guarded**: `config.py`'s model validator raises at startup unless `DEBUG=true` is also set, so a stray flag in the prod env (Render) crashes the deploy instead of silently handing admin to anonymous requests.

### Backend layout (`backend/app/`)

| Piece | Contents |
|---|---|
| `main.py` | App, env-driven CORS allow-list, `/health`, `/me`, mounts **10 routers** |
| `core/` | `config.py` (pydantic-settings + the bypass boot guard), `database.py` (async engine: pooler-safe `statement_cache_size=0`, `pool_pre_ping=True`, `echo=DEBUG` only), `security.py` |
| `api/routes/` | `activities`, `reviews`, `dashboard`, `roadmaps`, `admin`, `feedback`, **`internal`** (cron-only), **`prefs`** (audience), **`tests`** (test banks), **`syllabus`** (PDF → personal roadmap) |
| `services/` | `scheduler.py` (FSRS-4.5: `apply_fsrs`, `FSRS_WEIGHTS`, `DESIRED_RETENTION=0.9`, `REVIEW_SESSION_CAP=10`), `grader.py` (Groq LLM: recall grading, question mode, capture assist, fill-up grading), **`mailer.py`** (Resend), **`reminders.py`** (claim-then-send daily batch; emits `reminder_sent`), **`analytics.py`** (server-side PostHog: `capture()`/`shutdown()`, no-op without `POSTHOG_API_KEY`; emits `review_scheduled`, `reminder_sent`), **`test_scoring.py`**, **`syllabus.py`** (syllabus-PDF → draft roadmap; **provider-routed by `SYLLABUS_MODEL`** — `gemini*` id → Google `google-genai` inline-PDF + `response_schema`, else Anthropic `claude-opus-4-8` document block + structured outputs/streaming; both send the same prompt+schema so the two can be A/B'd on quality) |
| `models/models.py` | Single source of truth — 13 tables (see §2) |
| `alembic/versions/` | 24 migrations; head `c8e2a7f5d1b9` (`user_prefs.custom_roadmaps_created` — **pending in prod; Dockerfile runs `alembic upgrade head` on deploy**) |
| `tests/` | `test_ownership.py` (cross-tenant isolation), `test_question_sets.py` (question-set reuse/scoping/reference-answer injection), `test_syllabus_quota.py` (lifetime cap, no delete-refund); SQLite via JSONB→JSON variant; `pytest.ini`, `.dockerignore`, `Dockerfile` |
| `seed_*.py` | **33 seed scripts** (idempotent, fixed UUIDs): 31 roadmap seeds + 2 prereq-edge seeds (`python_swe_prereqs`, `physics_school_prereqs`) |

### API surface (all verified against route decorators)

| Endpoint | Notes |
|---|---|
| `GET/POST /api/activities/` | Vault list; create card (FSRS init, first review +1d, first-ever = demo due now; `source_type='lesson'` idempotent per node) |
| `POST /api/activities/suggest-key-points` | Capture assist (gated `GRADER_ENABLED`, else 404) |
| `GET /api/reviews/due` | Capped at 10, oldest first |
| `POST /api/reviews/{id}/complete` | Advances FSRS, schedules next |
| `POST /api/reviews/{id}/grade`, `/questions`, `/grade-questions` | LLM grader + question mode (all gated on `GRADER_ENABLED`). `/questions` serves a **persisted `question_sets` row** (reused `QUESTION_SET_REUSE`=2 sessions, shuffled each serve, then regenerated; optional body `{depth: 'main'\|'deep'}`); node-linked cards get **topic-grounded** generation (node title+description is the contract, key_memory only biases), free-form cards stay key_memory-grounded. `/grade-questions` injects the set's stored `reference_answer`s server-side (never sent to the client) |
| `GET /api/dashboard/` + **`/review-metrics`** + **`/heatmap`** | The last two are newer than CLAUDE.md |
| `GET /api/roadmaps/` (+`{id-or-slug}`, `{id}/blockers`, `PUT nodes/{id}/progress`) | List is **filtered by the caller's `user_prefs.audience`** (career vs school) **plus the caller's own personal roadmaps** (`user_id`); personal roadmaps resolve only for their owner (404 otherwise) |
| **`POST /api/syllabus/extract` · `/extract-text` · `/commit` · `GET /quota` · `DELETE /api/syllabus/{id}`** | Syllabus upload → personal roadmap. Extract = PDF (≤10 MB) → LLM → draft JSON, **nothing saved**; extract-text = pasted syllabus text (≤40K chars, the token-cheap default in the UI — no per-page document tokens; also how DOCX is handled: user copies the text) → same draft; both share the ≤5/user/day in-memory limit. Commit = user-edited draft → `roadmaps(user_id)` + nodes, **capped at `SYLLABUS_LIFETIME_LIMIT`=3 per user LIFETIME** (atomic claim on `user_prefs.custom_roadmaps_created`; delete ≠ refund; 403 when spent); quota = {used, limit, remaining} for the UI; delete = own roadmaps only (activities keep history, links nulled). Extraction gated on the selected provider's key — `GEMINI_API_KEY` or `ANTHROPIC_API_KEY` (404 when unset) |
| `POST /api/feedback/` · `GET /api/admin/funnel` · `GET /api/admin/feedback` | Feedback + founder admin |
| **`POST /api/internal/send-reminders`** | No user JWT — `X-Cron-Secret` header, `hmac.compare_digest`, closed entirely if `CRON_SECRET` unset. Driven by `.github/workflows/reminders.yml` (01:30 UTC daily + manual dispatch) |
| **`GET/PUT /api/prefs/`** | Server-side audience preference ('career' \| 'school') |
| **`GET /api/tests/weights` · `POST /api/tests/grade-fillup` · `POST /api/tests/attempts`** | Tests section: per-node weights from last 10 attempts, LLM fill-up grading (gated), attempt submission — **bridges into FSRS** (`apply_fsrs`, misses → Rating.Again) |

### Frontend layout (`frontend/src/`)

- **Shell/routing** (`App.jsx`): `/dashboard`, `/reviews`, `/log`, `/roadmaps(/:id)(/learn/:slug)`, **`/roadmaps/new`** (`SyllabusUpload.jsx` — upload → editable draft → commit; "Bring Your Own Path" card on `/roadmaps` links here; personal roadmaps render in a "Your Roadmaps" group with delete), **`/roadmaps/:slug/numericals/:phase`** (Physics), **`/roadmaps/:slug/test/:phase`** (Tests), `/paths`, `/vault`, `/analytics`, `/profile`, `/admin` (founder-only), `/dsa-dev` (dev player).
- **Newer than CLAUDE.md**: `Tests.jsx`, `AudiencePicker.jsx` (one-time career/school picker), **`SchoolRoadmaps.jsx`** (Class → Subject → Chapter browser, fully replaces the career catalog when `audience==='school'`; parses `RoadmapNode.phase` "Class 9 · Motion" — no backend change; + roadmap search; commit `b94d233`, D-006), `PhysicsNumericals.jsx` + `physics/` module, `ReviewHeatmap.jsx`, `SqlFlow/SqlJoinViz/SqlResult.jsx`, `GlossaryTerm.jsx`, `WelcomeModal.jsx`, `ToastContext.jsx`, `lib/analytics.js` (**PostHog** wrapper — autocapture OFF, curated events, silent no-op without key), `lib/useSeo.js` + prebuild sitemap generation (SEO pass), `lib/testGrading.js`.
- **DSA viz module (`src/dsa/`)** — canonical artifact is the event trace: pure generator (`generators/*.js`, golden-tested `*.golden.mjs`) → `compile.js` folds events into frames → renderers. **Far ahead of CLAUDE.md's claim**: ~29 generators live (through backtracking: `n-queens`, `permutations`, `subsets`, `combination-sum`, plus stacks/queues, sliding windows, `kadane`, `fast-slow-pointers`, `next-greater-element`, bounds…) and **9 renderers** (`ArrayViz`, `StateMachine`, `StackQueueViz`, `ListViz`, `TreeViz`, `GraphViz`, `GridViz`, `IntervalViz`, `BitsViz`) — the renderer gaps CLAUDE.md lists as "still needed" are built. Of the 9: 7 are view-dispatched, 2 (`StateMachine`, `StackQueueViz`) are always-on side panels; **4 still have no generator feeding them** (`ListViz`, `GraphViz`, `IntervalViz`, `BitsViz` — no `LIST/GRAPH/INTERVAL/BITS_INIT` emitter yet). Backtracking generators DO feed `TreeViz`/`GridViz` (n-queens → grid; template/permutations/subsets/combination-sum → tree).
- Dark mode = centralized `html.dark` override layer in `index.css`; Login page intentionally always-dark.

### Content system (`content/`)

- One JSON per lesson at `content/roadmaps/<key>/<slug>.json`; **9 content folders**: `python-swe`, `sql`, `aptitude`, `core-cs`, `dsa`, `ai-engineering`, `python-backend`, `cpp-swe`, `physics-9-10`.
- `content/validate.py` is **the gate**. Allowed `kind`s (its `KIND` set): `concept` (base shape, no explicit branch) + explicit branches for `aptitude` / `theory` / `engineering` / `dsa` / `reasoning` / `physics` / `numericals` / `test` (+ `milestone` allowed but unused in content); `content/scripts/` (glossary injection, prose extraction) is real pipeline code. `sync-content.mjs` copies to `frontend/public/content/` on `predev`/`prebuild` (git-ignored, Vercel regenerates).
- Test banks live at `content/roadmaps/<key>/_test/*.json` (static content; only attempt outcomes hit the DB).
- Bulk generation is delegated to Antigravity; Claude owns contracts (`schema.json`, `validate.py`, `PROMPT-*.md`), runtime/renderers, and critique. DSA content handoffs exist through **phase 13** (recursion/viz/prose) — CLAUDE.md's "phases 1–7" is stale.

---

## 2. Data model (13 tables; 12 prod-verified + `question_sets` pending deploy)

`tracks`, `activities` (the FSRS card: `stability`/`difficulty_fsrs` NULL until first graded review; legacy SM-2 columns still written; optional `roadmap_id`/`node_id` links), `reviews` (due/completed + `rating`/`recalled`/`quality` + `ai_*` grader columns), `feedbacks`, `roadmaps` (**+ `slug`, + `audience` 'career'|'school', + `user_id` NULL=catalog / set=personal syllabus-upload roadmap**), `roadmap_nodes` (self-ref `parent_id` subtopics), `roadmap_node_prerequisites` (directed edges, powers "Why am I stuck?"), `user_progress`, **`user_prefs`** (audience, server-side; + `custom_roadmaps_created` lifetime syllabus-commit counter — never decremented), **`test_attempts`** (JSONB per-question results; `node_title` is the join key), **`reminder_log`** (unique `(user_id, sent_on)` = at-most-once-daily email idempotency), **`question_sets`** (persisted LLM question set per card: JSONB `items` [{question, reference_answer}], `depth` 'main'|'deep', `times_used`; reused ≥2 sessions then regenerated; reference answers never leave the server), `alembic_version`.

**Migration chain (22):** `c71d8f31ee19` initial → … → `c2f5a9b3d701` ai-grader → `d4e8a1b2c903` reminder_log → `f4a9c2e1b370` roadmap_id → `a1b2c3d4e5f6` FSRS → `b2c3d4e5f6a7` prereqs → `a3f1c0d4e7b2` slug → `a4b2e9f1c8d3` node_id → `e7f2a4c9b1d5` review invariants (partial unique indexes) → `f8a3b5c2d9e1` RLS → `c4d7e9a2b501` audience+user_prefs → `f2b7d3a9c8e4` test_attempts → `a1c5e8f2d7b3` roadmaps.user_id (applied to prod 2026-07-11 via local `alembic upgrade` against the pooler — the migration file was uncommitted until this change, which crash-looped the deploy on an unresolvable revision) → `b3d9f1a4c6e2` question_sets (RLS enabled) → **`c8e2a7f5d1b9` user_prefs.custom_roadmaps_created (head; backfills from existing personal roadmaps; both auto-apply on next deploy via the Dockerfile's `alembic upgrade head`)**.

**Prod state (checked 2026-07-11 via Supabase MCP):** `alembic_version = a1c5e8f2d7b3` — **prod is at head** (`roadmaps.user_id` present). All 12 public tables have `relrowsecurity = true`. CLAUDE.md's note that `e7f2a4c9b1d5` + `f8a3b5c2d9e1` are "pending" is **wrong** — they are applied. Live catalog: **30 roadmaps (29 career + 1 school)**, seeded from 33 scripts — CLAUDE.md's "10 seeded roadmaps" is very stale; most of the "backlog" (Data Engineering, LLD, Git/GitHub, Blind 75, Behavioral, DevOps, Linux, TS-adjacent, ML, DL, MLOps, Math-for-ML, Java, C++, Cyber Security, Computer Architecture, Discrete Math…) is now seeded.

Hardening migration `73c79267ec74` adds CHECK constraints (`reviews.status/rating`, `user_progress.status`, `feedbacks.status`, `ease_factor ≥ 1.3`) and the hot-path indexes (`reviews(user_id,status,scheduled_for)`, `activities(user_id,created_at DESC)`, unique `user_progress(user_id,node_id)`).

---

## 3. Where the code is ahead of the docs (verified deltas)

| Claimed (CLAUDE.md / ARCHITECTURE.md) | Actual (verified 2026-07-10) |
|---|---|
| RLS + review-invariant migrations "pending" in prod | Applied; prod at head `f2b7d3a9c8e4` |
| 6 routers | 9 — `internal`, `prefs`, `tests` added |
| No email/reminder system | Full loop live: `reminder_log` + `mailer/reminders.py` + GH Actions cron + `CRON_SECRET` |
| 10 seeded roadmaps | 33 seed scripts, 30 live in prod |
| School platform = "vision / pitch-gated MVP" | Shipped in-product: `audience` split, `user_prefs`, `AudiencePicker`, Physics 9-10 roadmap + numericals route + content folder |
| Tests section absent | Live: `/api/tests/*`, `test_attempts`, `Tests.jsx`, `_test/` banks, FSRS bridge |
| DSA viz: renderers for stack/list/tree/graph/grid "still needed"; phases 1–7 | 9 renderers exist BUT 6 are unused (List/Tree/Graph/Grid/Interval/Bits — no generator feeds them); **24 registered generators** (array/string/stack/search/sort only) — **NO backtracking or linked-list generators yet** (audit 2026-07-10); prose handoffs through phase 13 |
| Dashboard has one endpoint | `/review-metrics` + `/heatmap` added (`ReviewHeatmap.jsx`) |
| No analytics | PostHog wrapper (`lib/analytics.js`), curated events, key-gated |
| No backend test suite / CI | `tests/test_ownership.py` (tenant isolation) + `reminders.yml` workflow; `Dockerfile` + `.dockerignore` |
| hardening-plan.md Tier-0 open | Done: ES256-only, `echo=DEBUG`, env CORS, required `ADMIN_EMAIL`, boot-guarded bypass, 15 `max_length` caps across request schemas |

---

## 4. Security

### Current posture (what's verifiably in place)

- **ES256-only JWT verification** via JWKS; algorithm-confusion closed; audience + role checked; expired/invalid → 401.
- **Tenant isolation**: every query scoped by `current_user.id`; mutating endpoints verify ownership (`WHERE id=:id AND user_id=:uid`); enforced by an automated test suite (`backend/tests/test_ownership.py`).
- **RLS enabled on all 12 public tables with zero policies** — deliberate: it blanket-denies Supabase's PostgREST/anon-key surface while the backend (table owner) bypasses it. Supabase's advisor flags this pattern as INFO ("RLS enabled, no policy"); that is the intended design, not a gap.
- **DB integrity as defense**: CHECK constraints on status/rating enums, partial unique indexes enforcing review invariants (`e7f2a4c9b1d5`), FK `ondelete` rules.
- **Secrets & config**: `.env` git-ignored; CORS is an explicit env-driven allow-list (no `*`); `ADMIN_EMAIL` has no hardcoded default; SQL echo off in prod; `DEV_AUTH_BYPASS` crashes the boot without `DEBUG`.
- **Machine endpoints**: `/api/internal/send-reminders` uses constant-time secret comparison and is fully closed when `CRON_SECRET` is unset; reminder sends are idempotent per user/day via an atomic `INSERT … ON CONFLICT DO NOTHING` claim.
- **Input bounding**: 15 `max_length` caps on request schemas (topic 300, key_memory 500, notes 5000, mistake 2000, …) — bounds both abuse and LLM token spend.
- **LLM gating**: all 5 LLM endpoints 404 unless `GRADER_ENABLED`; LLM output is advisory-only (never auto-applied, never auto-grades the user down).

### Open vulnerabilities / risks — CURRENT

1. **No rate limiting anywhere** (verified: no slowapi/limiter in the codebase). Highest-value targets: the 5 LLM endpoints (`/grade`, `/questions`, `/grade-questions`, `/suggest-key-points`, `/grade-fillup`) — any authenticated user can hammer them into a **Groq cost-DoS**; also `POST /api/feedback/` (spam) and `POST /api/activities/` (row flooding). Input caps bound per-request cost, not request count. *This is the #1 item to fix before opening signups wider.*
2. **Admin gate is an email string compare**, not a role system. Fine for a 3-user cohort; brittle the day a second admin or email change happens. Backend check is authoritative (frontend check is UX-only) — keep it that way.
3. **Prompt-injection surface in the graders**: user-controlled text (`key_memory`, free-recall answers, drafts) is interpolated into Groq prompts, and the returned `feedback`/`revision_note`/`related_subtopics` strings are rendered in the UI. Blast radius is low (advisory-only, JSON-parsed, no tool use), but a crafted card could make the grader emit misleading/hostile text to the user. Mitigation when it matters: treat LLM strings as untrusted display data (they already render as text, not HTML — keep it that way), and consider a moderation/format check.
4. **JWT lives in localStorage** (Supabase JS default) → any XSS = token theft. React's escaping + no `dangerouslySetInnerHTML` on user content is the real defense; re-audit if lesson content ever renders raw HTML.
5. **User content flows to a third party (Groq)** whenever the grader is on — `key_memory` and answers leave your infra. Not a bug, but a disclosure/ToS item before a paid cohort, and a DPDP consideration for the school pilot.
6. **Naive-UTC timestamps** rendered as local time — cosmetic date-label off-by-one near midnight for IST users (known debt; scheduling math unaffected).
7. **Supabase advisor WARN**: leaked-password (HIBP) protection disabled. Moot while auth is Google-only; becomes real if email+password is ever enabled.
8. **Guest surface** (`optionalAuth` reads) — currently read-only roadmap browsing; keep writes behind `requireAuth` as new endpoints are added.

### Watch-list — FUTURE (not bugs today, will bite at the next stage)

- **Opening signups / any marketing push** → rate limiting (slowapi or a Render edge/proxy) becomes blocking, and the Groq/Gemini/Anthropic spend needs a per-user daily budget + alerting (the syllabus extractor's 5/user/day cap is in-memory and resets on redeploy — not a hard budget guard).
- **School pilot with minors** → India DPDP Act: parental consent, data-minimization, and a data-processing story for Groq/PostHog/Resend before any real Class 9-10 cohort.
- **GitHub Actions cron** pauses after 60 days of repo inactivity and can lag ~15 min — reminder emails silently stop if the repo goes quiet; move to a host cron if cadence ever matters.
- **Transaction pooler limits**: `pool_size=5 + max_overflow=10` per instance is fine now; multiple Render instances or heavier traffic can exhaust Supabase pooler slots — revisit before scaling out.
- **Email deliverability/abuse**: Resend sender reputation once volume grows; unsubscribe/compliance (CAN-SPAM-style) before non-trivial sending.
- **Content supply chain**: lessons are Antigravity-generated JSON rendered by the app — the validator checks structure, not pedagogy or malice; keep the human/Claude critique step for anything that ships, and never render lesson fields as raw HTML.
- **PostHog**: once a key is set in prod, it's a third-party script + user-event stream — add it to the privacy story.
- **Single founder key risk**: Supabase/Render/Vercel/Groq/Google/Anthropic accounts + `CRON_SECRET`/`GROQ_API_KEY`/`GEMINI_API_KEY`/`ANTHROPIC_API_KEY` all hang off one identity; password-manager + 2FA hygiene is the actual security perimeter of this product.

---

## 5. Future plans (cross-checked: still genuinely open)

**Near-term product (in priority order, from CLAUDE.md §next — still valid):**
1. **Review-loop friction pass** (`docs/PROMPT-review-ux-friction.md`): lesson-grounded recall questions (use `recall_questions` instead of generic LLM questions — early verdict was "too generic"), visible grading state, outcome-chip descriptors, mobile nav to 5 items, Home Continue-card.
2. **Node-complete → pre-filled Log modal** — closes the roadmap→retention loop (design doc §9b).
3. **Logged-reviews vault** (review history).
4. Persist Track/Activity-Type properly in `ActivityCreate` (currently partially UI-only).
5. Feedback status workflow (new→reviewed→resolved) + real admin auth after the first cohort.
6. **Rate limiting** (see §4 — promote this above the fold).

**Content build order** (per JD research runs 1–3): finish **AI Engineering**, **DSA phases 8+** (stack/queue → linked lists → trees → graphs → DP; viz renderers already exist, content + generators are the remaining work), then **Data Engineering**, then ML Fundamentals. Verbal/vocab aptitude pending. Core-CS OS batch in progress.

**School platform** (Classes 6–12 on the same engine): the product split is **already live** (audience prefs + Physics 9-10 + numericals). Remaining: finish Physics 9-10 content to pitch-quality, then the Gorakhpur/private-school pitch (`docs/PROMPT-school-b2b-research.md`, `school-b2b-research-findings.md`).

**Career Paths v2**: live "% to role X" tracker on top of the static `lib/careerPaths.js` v1.

**Phase 2 engine work**: real Momentum/Retention-Strength metrics (Analytics currently shows honest placeholders), Re-entry Mode, FSRS parameter optimization once there's enough review data.

**SEO**: static lesson pages + sitemap work has started (`useSeo.js`, prebuild sitemap, `docs/PROMPT-seo-static-lessons.md`) — continue toward indexable lesson content as the organic-acquisition channel.

---

## 6. Operational notes

- **Deploy**: Vercel (frontend, SPA rewrite in `vercel.json` is load-bearing for deep links/OAuth) + **Render** (backend; `Dockerfile` present). Moved off Railway 2026-07-11 (free tier ended) — **region unverified; keep it close to Supabase Mumbai (Singapore) for latency**. Deploys from `main`. Never auto-deploy — the founder pushes. Prod env vars now include `ANTHROPIC_API_KEY` / `GEMINI_API_KEY` / `SYLLABUS_MODEL` (set on Render).
- **DB**: always the transaction pooler URL (`aws-1-ap-south-1…:6543`); direct host is IPv6-only. Engine already sets `statement_cache_size=0` + `pool_pre_ping`. Alphanumeric DB password only; repeated auth failures trip Supabase's circuit breaker (~minutes).
- **Schema changes**: Alembic only, and **every new table's migration must include `ENABLE ROW LEVEL SECURITY`** (the PostgREST-blocking pattern, migration `f8a3b5c2d9e1`).
- **Repo hygiene** (post-cleanup 2026-07-10): the repo root and `content/` hold **no** Python except `content/validate.py` and `content/scripts/`; `.gitignore` now enforces this (`/*.py`, `content/*.py`, `content/roadmaps/**/*.py`). One-off patch scripts should be written under the session scratchpad or deleted after use — their output (the JSON) is the artifact, not the script.
- **Verification tools**: read-only Supabase MCP is configured (`.mcp.json`) — use it to verify prod schema/migration state instead of trusting docs (this document was built that way).

---

## Appendix — doc freshness

| Doc | Status (2026-07-10) |
|---|---|
| `docs/SYSTEM-OVERVIEW.md` (this file) | **Current — verified against code + prod DB** |
| `CLAUDE.md` | **Rewritten 2026-07-10** as a lean rules + update-routing file (no status). The old ~450-line version is frozen at `docs/CLAUDE-ARCHIVE-2026-07.md` — its status/roadmap-count/DSA-viz sections were already stale (see §3) |
| `docs/claude-code-workflow.md`, `docs/DECISIONS.md`, `docs/BACKLOG.md` | Added 2026-07-10 — session playbook, go-forward decision log, idea inbox |
| `docs/ARCHITECTURE.md` | Topology/auth still broadly right; predates reminders, prefs, tests, audience split, 20+ roadmaps (2026-06-07) |
| `docs/API.md`, `docs/FLOWS.md` | Predate the 3 new routers + dashboard endpoints — **stale** |
| `docs/hardening-plan.md` | Tier-0/1 items largely **done in code**; still useful as the rationale + for unfinished items (rate limiting) |
| `docs/SPEC-test-runtime.md`, `dsa-*`, `content-engine.md`, `design-bible.md` | Recent, written alongside the shipped features — trustworthy |
| `docs/SESSION_HANDOFF.md`, `HANDOFF-*`, `PROMPT-*` | Point-in-time working docs — read with their dates in mind |

---

## Changelog

One line per system-state change, newest first: `YYYY-MM-DD — what changed (sections touched)`.

- 2026-07-13 — Analytics build-out (AARRR + North Star; plan in `docs/analytics-plan.md`). Frontend `lib/analytics.js` event vocab expanded (activation funnel: `signup_started`/`signed_up`/`onboarding_started`/`onboarding_completed`/`first_capture_shown`/`activated`; retention: `reviews_due_shown`/`review_queue_empty`/`reminder_clicked`; engagement: `lesson_completed`/`card_created_from_lesson`; friction: `api_error`) + `trackOnce` helper + `capture_pageleave:true` (Web Analytics bounce/duration). New backend `services/analytics.py` (server-side PostHog) emits `review_scheduled` (activities + reviews) and `reminder_sent` (reminders, link tagged `?src=reminder`). New env `POSTHOG_API_KEY`/`POSTHOG_HOST`; `posthog>=3.7.0` dep; flush on app shutdown (§1 topology/services/frontend). **No schema change.**
- 2026-07-12 — Syllabus commits capped at **3 per user lifetime** (`SYLLABUS_LIFETIME_LIMIT`; new `user_prefs.custom_roadmaps_created` counter, migration `c8e2a7f5d1b9`, atomic claim, delete ≠ refund) + `GET /api/syllabus/quota`; Home gains a "Customize your own" tile → `/roadmaps/new`; upload page shows remaining quota and blocks at 0. Content plan doc added: `docs/PLAN-lesson-generation.md` (Sonnet-drafted, founder to review) (§1–2).
- 2026-07-12 — Question mode goes persistent + topic-grounded: new `question_sets` table (migration `b3d9f1a4c6e2`, 13th table; RLS) — LLM sets generated with per-question `reference_answer`s, reused ≥2 review sessions shuffled, then regenerated; node-linked cards get topic-grounded generation with a user-facing `depth` choice ('main'|'deep', Review.jsx toggle); `/grade-questions` injects stored references server-side. Superseded key_memory-only `generate_questions` removed from `grader.py`. New tests `test_question_sets.py` (§1–2).
- 2026-07-12 — Syllabus: added `POST /api/syllabus/extract-text` (pasted text ≤40K chars, token-cheap default; shares the daily limit) + paste-text tab as the primary input in `SyllabusUpload.jsx`; `services/syllabus.py` grew `extract_roadmap_from_text` with shared `_finalize` guardrails (§1).
- 2026-07-11 — Backend deploy host moved **Railway → Render** (Railway free tier ended); env vars (incl. `ANTHROPIC_API_KEY`/`GEMINI_API_KEY`/`SYLLABUS_MODEL`) re-set on Render. Docs updated across SYSTEM-OVERVIEW §1/§4/§6, CLAUDE.md, README, BACKLOG. **Render region unverified** — keep near Supabase Mumbai (Singapore) for latency (§6, watch-list).
- 2026-07-11 — Syllabus → personal roadmap feature: `syllabus` router (extract/commit/delete, review-before-commit), `services/syllabus.py` (**provider-routed by `SYLLABUS_MODEL`**: Anthropic `claude-opus-4-8` or Google Gemini via `google-genai`; new `ANTHROPIC_API_KEY`/`GEMINI_API_KEY`/`SYLLABUS_*` env), migration `a1c5e8f2d7b3` `roadmaps.user_id` (**applied to prod 2026-07-11; file committed same day after it crash-looped the deploy while uncommitted**), roadmap visibility = catalog-by-audience + own, `/roadmaps/new` UI (§1, §2).
- 2026-07-11 — Agent audit vs code + prod DB: prod re-verified (head `f2b7d3a9c8e4`, RLS ×12, 30 roadmaps/1689 nodes); fixed validate.py kind list (was 5, actually 9 branched + base); DSA renderer-feed status precised (4 unfed, backtracking feeds Tree/Grid). Backend §1–2 verified clean.
- 2026-07-11 — Frontend layout: documented `SchoolRoadmaps.jsx` Class→Subject→Chapter browser + roadmap search (shipped in commit `b94d233` on 07-10 without a doc update; rationale in `DECISIONS.md` D-006).
- 2026-07-10 — Docs-layer restructure: CLAUDE.md slimmed to rules + update-routing (old version → `docs/CLAUDE-ARCHIVE-2026-07.md`); added `docs/claude-code-workflow.md`, `docs/DECISIONS.md` (D-001), `docs/BACKLOG.md` (Appendix updated).
- 2026-07-10 — Document created from a full code + prod-DB verification pass; repo cleanup (one-off scripts purged, `.gitignore` hardened); living-doc convention added to CLAUDE.md.
