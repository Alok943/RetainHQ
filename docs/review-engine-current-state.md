# Review Engine — Current State (findings for Fable 5 architecture session)

Scope: how RetainHQ schedules, stacks, and stores spaced-repetition reviews today. Pure map — no recommendations, no proposed fixes.

---

## 1. Current scheduling logic

### FSRS implementation

Lives entirely in [backend/app/services/scheduler.py](../backend/app/services/scheduler.py). It's a from-scratch FSRS-4.5 implementation (no external `fsrs` package) using the **published open-spaced-repetition default weights**, hardcoded as a 19-tuple:

```python
FSRS_WEIGHTS = (
    0.4072, 1.1829, 3.1262, 15.4722, 7.2102, 0.5316, 1.0651, 0.0234,
    1.616, 0.1544, 1.0824, 1.9813, 0.0953, 0.2975, 2.2042, 0.2407,
    2.9466, 0.5034, 0.6567,
)
```

Constants:
- `DESIRED_RETENTION = 0.9` — target recall probability the scheduler solves for.
- `_DECAY = -0.5`, `_FACTOR = 0.9 ** (1/_DECAY) - 1` — the power-law forgetting-curve shape; chosen so `interval(S) == S` at 90% retention.
- `MIN_STABILITY = 0.1`, `MAX_INTERVAL_DAYS = 365` — hard floor/ceiling on the computed interval.
- FSRS grade scale is 1–4: `RATING_AGAIN=1, RATING_HARD=2, RATING_GOOD=3, RATING_EASY=4` (distinct from the legacy 0–5 SM-2 "quality" scale, which is still computed in parallel — see §3).

Core functions and what each does:
- `_init_stability(rating)` — new-card stability = `FSRS_WEIGHTS[rating-1]`, floored at `MIN_STABILITY`.
- `_init_difficulty(rating)` — new-card difficulty via `w4 - exp(w5*(g-1)) + 1`, clamped to `[1,10]`.
- `_next_difficulty(difficulty, rating)` — linear nudge by grade then mean-reverts toward the Easy-graded baseline.
- `_retrievability(elapsed_days, stability)` — predicted P(recall) right now, given elapsed time since last review and current stability. This is the piece that makes FSRS **elapsed-time-aware** (vs. SM-2's fixed ladder).
- `_next_stability(stability, difficulty, retrievability, rating)` — two branches: a lapse formula (`rating == RATING_AGAIN`, stability drops, capped below the pre-lapse value) and a growth formula (successful recall, stability grows by a factor driven by difficulty, current stability, and how surprising the elapsed gap was).
- `_interval_from_stability(stability)` — solves `interval` so predicted retention at that interval equals `DESIRED_RETENTION`; result is `round()`ed and clamped to `[1, 365]` days.
- `apply_fsrs(activity, rating, now)` — the orchestrator, called from the `/reviews/{id}/complete` endpoint. Branches on whether the card is new (`stability is None or difficulty_fsrs is None`) vs. established. For an established card it computes `elapsed` from `activity.last_reviewed_at` (falling back to `interval_days` if that's somehow unset), derives `retrievability`, updates difficulty/stability, computes the new interval, **mutates the `Activity` row in place**, and constructs+returns a new `Review(status="due", scheduled_for=due_at)`. The caller (`reviews.py`) adds this new Review to the session and commits in the same transaction as the completion update — this is the single place a new due-date is assigned after the first review.

### SM-2 → FSRS migration history

Three-stage evolution, visible in the alembic chain and the code comments:

1. **`a7c3d9e1b240_add_sm2_state.py`** (2026-06-07) — original scheduler. Added `ease_factor` (default 2.5), `repetitions` (default 1), `interval_days` (default 1) to `activities`. Fixed ease-ladder: 1 → 6 → ×ease_factor.
2. **`a1b2c3d4e5f6_add_fsrs_state.py`** (2026-06-20) — added `stability` and `difficulty_fsrs` (both nullable, no server default — NULL means "new card, no FSRS memory state yet"). This is purely additive; the SM-2 columns were **not dropped**.
3. Current `scheduler.py` runs FSRS end to end but still writes to the legacy SM-2 columns:
   - `ease_factor` is set to `DEFAULT_EASE_FACTOR = 2.5` on init and never changed again (kept only to satisfy a NOT NULL + a CHECK constraint `chk_activities_ease_factor: ease_factor >= 1.3` from `73c79267ec74_hardening_constraints_and_indexes.py`).
   - `repetitions` is still incremented/reset (`1 if rating==Again else repetitions+1`) — "kept roughly meaningful" per the inline comment, but nothing reads it for scheduling.
   - `interval_days`, `last_reviewed_at`, `next_review_at` are **not legacy** — these are live fields FSRS itself writes and depends on (`next_review_at` mirrors the open due review for cheap dashboard queries; `last_reviewed_at` is the elapsed-time anchor for the next `_retrievability` call).
   - `reviews.quality` (0–5) is also still computed on every completion via `quality_from_outcome()`, described in the code as "persisted purely for analytics continuity" — FSRS itself only consumes the 1–4 `fsrs_rating_from_outcome()` value.

Net effect: the schema and write path carry **two full generations of scheduling metadata simultaneously** (SM-2 columns unused for scheduling but still written; FSRS columns live). Nothing currently reads `ease_factor`/`repetitions` for anything except the CHECK constraint and vault-list display (`ActivityListItem.repetitions` is exposed to the frontend, see §3).

### Anti-fatigue logic already in place

Two independent mechanisms, both in `scheduler.py`:

1. **Deferred first review** (`initial_review_for_activity`, called from `POST /api/activities/`): every newly logged activity's first review is scheduled for **+1 day**, not immediately — rationale documented inline as avoiding "instant-quiz fatigue" (logging 4 topics back-to-back would otherwise mean 4 immediate exams). Exception: a user's **first-ever** activity (`existing_count == 0`, checked in `activities.py` before insert) gets `immediate=True` → due **now** — this is the one-time onboarding "aha" demo, not a per-log behavior.
2. **`REVIEW_SESSION_CAP = 10`** (module-level constant in `scheduler.py`, not env-configurable) — bounds how many reviews are surfaced as "due" in any single fetch. Applied in two independent places (see §2): the `/reviews/due` query (`.limit(REVIEW_SESSION_CAP)`) and the dashboard's `due_count` (`min(rev.due, REVIEW_SESSION_CAP)`). Overdue cards beyond the cap simply stay `status='due'` in the table and roll forward — there is no separate overflow queue or table; "capped" here means "capped at read time," not "capped at schedule time" (see §4).

No interval fuzz/jitter/randomization exists anywhere in the scheduling path today (confirmed by search — no `random`/`fuzz`/`jitter` references in `backend/app/services/` or the scheduler).

---

## 2. Where review-stacking happens

"Stacking" = multiple activities' reviews landing on the same `scheduled_for` date. Trace:

- **Every** `Review` row's `scheduled_for` is assigned in exactly two functions, both in `scheduler.py`:
  - `initial_review_for_activity()` — sets `due_at = now + timedelta(days=1)` (or `now` for the immediate/demo case). `now` is wall-clock `datetime.utcnow()` at insert time — i.e., **whatever moment the user happened to log the activity**, not any per-topic offset.
  - `apply_fsrs()` — sets `due_at = now + timedelta(days=interval)` where `interval = _interval_from_stability(stability)`, an **integer** number of days (`round()`ed in `_interval_from_stability`). `now` is wall-clock completion time.
- Because both entry points derive `due_at` from **the current wall-clock time plus an integer day count**, and completion typically happens in a batch (a user does a "review session" covering several cards back-to-back), **any two cards graded in the same sitting with the same computed interval land on the same calendar day** — there is no per-card offset, stagger, or time-of-day spread. This is the exact mechanism by which topics stack: same session → same `now` (to within seconds/minutes) → same integer interval → same due date.
- There's a second, independent stacking source: a user logging several activities in one sitting all get `interval_days=1` from `initial_review_for_activity`, so all their first reviews land on the same next-day date.
- **No deduplication or spacing pass** exists across a user's `Review` rows — nothing groups by `user_id` and redistributes `scheduled_for` values. Each `Review` is scheduled purely from its own `Activity`'s FSRS state, independent of what else is already due that day.

Where the stack actually surfaces to the user:
- `GET /api/reviews/due` (`backend/app/api/routes/reviews.py:37-62`) — the query that assembles a review session: `WHERE status='due' AND scheduled_for <= now`, `ORDER BY scheduled_for ASC`, `LIMIT REVIEW_SESSION_CAP`. This is oldest-first, capped at 10 — so on a heavy-stack day the user sees at most 10 of however many are actually due, and the rest silently roll to the next session (they stay `status='due'`, `scheduled_for` unchanged, and reappear once the earlier 10 are cleared).
- `GET /api/dashboard/` (`backend/app/api/routes/dashboard.py:21-85`) — `due_count = min(rev.due, REVIEW_SESSION_CAP)`, a separate COUNT query over the same `WHERE status='due' AND scheduled_for <= now` predicate (not reusing the `/due` query, just mirroring its cap so the two numbers agree).

Indexing relevant to these queries: `ix_reviews_user_id_status_scheduled` (`user_id, status, scheduled_for`) from `73c79267ec74_hardening_constraints_and_indexes.py` — covers both the `/due` query and the dashboard count.

Existing capping/spacing mechanisms (all already covered above, repeated here for the "even if unused" ask):
- **Capping**: `REVIEW_SESSION_CAP=10`, applied at *read time* in two places (`/due` limit, dashboard count-min), not at *schedule time*. No DB-level cap on how many `Review` rows can share a `scheduled_for` date.
- **Randomization/fuzz**: none present anywhere in the codebase.
- **Spacing/redistribution**: none present — no code inspects a user's other due dates before assigning a new one.

---

## 3. Data model

### `activities` table (`backend/app/models/models.py`, `Activity` class) — the "card"

| Field | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID | not FK-constrained in the model (no `foreign_key=` on this column) |
| `track_id` | UUID? | FK → `tracks.id` |
| `roadmap_id` | UUID? | FK → `roadmaps.id`, `ON DELETE SET NULL` |
| `node_id` | UUID? | FK → `roadmap_nodes.id`, `ON DELETE SET NULL`; set when a card originates from a lesson's "Add to reviews" |
| `topic` | str | |
| `notes` | str? | |
| `difficulty` | int 1–5 | **user's own** self-rated difficulty at log time — distinct from `difficulty_fsrs` |
| `needed_hint` | bool | |
| `key_memory` | str, capped 500 chars | the testable claim; what review/grading is checked against |
| `mistake` | str? | |
| `source_type` | str? | free-text-ish, constrained by `ActivityCreate`'s `Literal` at the API layer only (not a DB CHECK constraint) — see below |
| `created_at` | datetime | naive-UTC |
| `stability` | float? | **FSRS**: days-to-target-decay; NULL = new card |
| `difficulty_fsrs` | float? | **FSRS**: 1–10 intrinsic difficulty; NULL = new card |
| `ease_factor` | float, default 2.5 | **legacy SM-2**, CHECK `>= 1.3`, still written, not read for scheduling |
| `repetitions` | int, default 0 | **legacy SM-2**, still written/incremented, exposed to frontend Vault list, not read for scheduling |
| `interval_days` | int, default 0 | **live** — last computed interval, also the elapsed-time fallback in `apply_fsrs` |
| `last_reviewed_at` | datetime? | **live** — FSRS elapsed-time anchor |
| `next_review_at` | datetime? | **live** — denormalized mirror of the currently-open due review, for cheap dashboard/vault reads without joining `reviews` |

### `reviews` table (`Review` class) — one row per scheduled/completed review instance

| Field | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID | |
| `activity_id` | UUID | FK → `activities.id`, `ON DELETE CASCADE` |
| `status` | str, default `"due"` | CHECK `IN ('due','completed')`; **invariant** (per scheduler.py comment): an activity in rotation has exactly one open `status='due'` review at a time |
| `scheduled_for` | datetime | the due date — set only by `initial_review_for_activity` / `apply_fsrs` (§2) |
| `completed_at` | datetime? | |
| `rating` | str? | CHECK `IN ('easy','medium','hard')` or NULL — **subjective** felt-difficulty |
| `recalled` | bool? | **objective** got-it/missed-it, independent axis from `rating` |
| `quality` | int? | 0–5 SM-2-style grade, derived from `(rating, recalled)` via `quality_from_outcome()`, persisted for analytics only |
| `ai_verdict` | str? | LLM grader output: `correct`/`partial`/`incorrect`, advisory |
| `ai_recalled` | bool? | LLM grader's own recalled judgment |
| `ai_feedback` | str? | one-sentence LLM feedback |
| `created_at` | datetime | |

Relationship: `Activity.reviews` / `Review.activity` (SQLModel `Relationship`), eager-loaded via `selectinload` everywhere it's touched (required for the async engine — lazy access after the session closes raises `MissingGreenlet`).

### How "format" is represented today

There is **no dedicated review-format field**. The closest existing concept is `Activity.source_type` — a nullable string set at *log time* (`ActivityCreate.source_type: Optional[Literal["problem","lecture","video","book","article","course","project","lesson","other"]]`), constrained only at the Pydantic layer (no DB CHECK constraint on this column, unlike `rating`/`status`). It's currently used exclusively for:
- A cosmetic badge in the Knowledge Vault list (`frontend/src/KnowledgeVault.jsx`, `SOURCE_LABELS` map + a `<span>`).
- Idempotency logic for lesson-originated cards (`source_type === 'lesson'` combined with `node_id` dedupes "Add to reviews" taps in `POST /api/activities/`).

`source_type` is **not** read anywhere in the review/scheduling path (`scheduler.py`, `reviews.py`), and it describes the *source of the knowledge* (where the user learned it), not the *review interaction format* (e.g., free-recall vs. flashcard vs. multiple-choice). The one thing that does vary review *interaction* format today is "question mode" — but that's an ephemeral, per-request LLM-generated artifact (`POST /api/reviews/{id}/questions`), not a persisted or schedulable property of the `Review` or `Activity` row. Whether a given due review renders as free-recall-only or free-recall-plus-generated-questions is decided client-side at render time (`Review.jsx` probes `/questions` and falls back on 404/503) and depends only on the `GRADER_ENABLED` flag — it is not stored per-item and not something the scheduler is aware of.

---

## 4. Integration points for three candidate fixes

Descriptive only — where each concern's plumbing already exists, not whether/how to add it.

### Interval fuzz (±10–15%)

The single point where an interval becomes a concrete `due_at` is `_interval_from_stability()` (returns an `int` day count) and its two call sites: `initial_review_for_activity()` (hardcoded `interval_days = 1`, no call to `_interval_from_stability` at all — the first-review offset is a separate literal `timedelta(days=1)`) and `apply_fsrs()` (`due_at = now + timedelta(days=interval)`). Any fuzz would touch the gap between "interval computed from stability" and "due_at written to the Review/Activity row" — currently there is zero transformation between those two steps in either function. Note the first-ever-review path (+1 day, +0 day demo) is a **separate literal**, not derived from `_interval_from_stability`, so it's a second site, not covered by touching just the FSRS interval function.

### Daily review cap + overflow

Cap enforcement today is **read-time only**, in two separate queries that must stay in sync by convention (no shared cap-aware helper beyond importing the same `REVIEW_SESSION_CAP` constant):
- `reviews.py:get_due_reviews` — `.limit(REVIEW_SESSION_CAP)` on the `SELECT`.
- `dashboard.py:get_dashboard_stats` — `min(rev.due, REVIEW_SESSION_CAP)` on a separate `COUNT`.

There is no schedule-time cap (nothing prevents N reviews from all getting `scheduled_for` = the same date) and no overflow structure: "overflow" today is implicit — any due review beyond the 10 returned by `/due` simply isn't selected by that query's `LIMIT`+`ORDER BY scheduled_for ASC`; it stays `status='due'` in the same `reviews` table, unmarked, and reappears (still ordered oldest-first) once earlier due rows move to `status='completed'`. There is no separate overflow/deferred table, no flag distinguishing "shown today" from "pushed," and no record of how many times a review has rolled over a cap boundary.

### Format variation

No per-item format field exists on `Review` or `Activity` (see §3). The nearest analogous existing pattern — a server-computed, request-time-generated artifact layered on top of a stored row without persisting the choice — is question mode (`generate_questions()` in `grader.py`, called fresh on every `/questions` request, nothing about "this card uses question-mode" is written back to the DB). `source_type` exists as a string column but is semantically the knowledge source, not an interaction/review format, and has no CHECK constraint (only a Pydantic `Literal` at the create-request boundary) — extending it or adding a sibling column would follow the same nullable-string-plus-optional-CHECK pattern used for `rating`/`status`/`source_type` elsewhere in this schema.

---

## 5. Constraints to flag

- **Single DB gateway, no direct client DB access.** Per project convention, the React frontend talks only to FastAPI (`frontend/src/lib/api.js` → `apiFetch`); Supabase is Postgres + Google OAuth only, no `supabase.from(...)` calls in the client. Any scheduling change must be expressed as backend logic/schema, not client-side computation, to stay inside this boundary.
- **Async SQLAlchemy + eager loading is load-bearing, not optional.** Every route touching `Review.activity` uses `selectinload(Review.activity)` explicitly; lazy access after the async session context closes raises `MissingGreenlet`. `async_session_maker` is configured with `expire_on_commit=False` (`backend/app/core/database.py:25`) so ORM objects returned from a completed transaction can still be read — an architectural crutch that a redesign needs to keep in mind if it changes commit boundaries.
- **`apply_fsrs()` mutates `Activity` in place and returns a new `Review`, both added to the session and committed together** with the `Review.status` transition in `reviews.py:complete_review` — i.e., completing a review and scheduling the next one are one atomic transaction today. The completion endpoint also does an **atomic conditional UPDATE** (`WHERE status='due'`) before the FSRS step specifically to prevent double-completion races. Any redesign that changes *how many* Review rows get created per completion (e.g., generating an overflow-queue entry) needs to preserve this single-transaction, race-safe shape.
- **`REVIEW_SESSION_CAP` is a hardcoded Python constant** (`scheduler.py:37`), not an env var or DB-configurable setting, and it's imported independently into `reviews.py` and `dashboard.py`. There is no single source of truth beyond "both files import the same Python name" — a schema-level cap (e.g., materialized in a table) would be a structural change, not a config change.
- **Two full generations of scheduling metadata coexist on `Activity`** (SM-2 columns still written, FSRS columns live) — a redesign touching the scheduling write path touches both, and the `chk_activities_ease_factor >= 1.3` CHECK constraint is a live DB constraint tied to a column nothing functionally reads anymore.
- **Naive-UTC timestamps throughout** (`datetime.utcnow()`, no `tzinfo`) — flagged in the project's own known-debt list. `scheduled_for`, `last_reviewed_at`, `next_review_at`, `created_at` are all naive-UTC. The frontend renders some of these with `new Date(iso)` (no `Z` suffix), which some browsers interpret as local time — a cosmetic date-label bug already acknowledged as unfixed, worth knowing about since a fuzz/cap redesign will touch these same fields.
- **Authorization pattern**: every query in `reviews.py`/`dashboard.py`/`activities.py` filters by `Review.user_id == user_id` / `Activity.user_id == user_id` derived from `uuid.UUID(current_user.id)` (JWT `sub`, ES256, verified via `PyJWKClient`/JWKS in `core/security.py`). `activities.user_id` is **not** a DB-level foreign key to `auth.users` (Supabase-managed table outside this schema) — ownership is enforced entirely in application-layer `WHERE` clauses, not DB constraints. Any new table (e.g., an overflow queue) would need to follow this same app-layer-ownership pattern since there's no DB-level FK to hang a constraint off of.
- **Migration discipline**: schema changes go through Alembic only (`alembic revision` → `alembic upgrade head`); the current head is `a4b2e9f1c8d3`. Per project notes, `a3f1c0d4e7b2` (roadmap slug) and `a4b2e9f1c8d3` (node_id) are **not yet applied to prod** as of this writing — worth confirming prod's actual migration state before assuming any of these columns exist there yet.
- **Reminder-email batch job reads `reviews` independently** (`services/reminders.py`, raw SQL via `text()`, not the ORM) with its own due-count aggregation (`count(*) as due_count` per user, uncapped — no `REVIEW_SESSION_CAP` applied here). This is a third place that computes "how many reviews are due," alongside `/reviews/due` and `/api/dashboard/` — any cap/overflow redesign has three independent read paths to reconcile, not two.
- **No test suite observed** for `scheduler.py`'s FSRS math during this exploration — changes to interval computation would be manually verified rather than regression-tested against known FSRS reference values.
