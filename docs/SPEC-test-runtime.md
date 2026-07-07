# SPEC — Test-runtime (the "Tests" section)

Locks the design; implementation follows this doc. Content contract: `content/PROMPT-tests.md`.
Gold sample banks: `content/roadmaps/{python-swe,physics-9-10,sql}/_test/*.json`.

## Architecture (matches the existing content/backend split)

**Content is client-side only** — same as every lesson. The backend never reads `content/*.json`;
it owns auth, user state (FSRS/`Activity`/`Review`), and the one LLM call (fillup grading). This
mirrors how `Review.jsx` already fetches lesson JSON directly and how DSA/SQL lessons run entirely
in-browser (Pyodide/PGlite) — the Test section adds no new content-serving path.

Wire contract uses **`RoadmapNode.title`** as the join key (not the content slug) — same as
`ReviewResponse.node_title` already does. The frontend owns the slug→title mapping via
`/content/manifest.json` (already loaded for lesson resolution); it converts each bank question's
`node` (a lesson slug) to a title before talking to the backend.

## Session flow

1. **`GET /api/tests/weights?roadmap_slug=X`** — backend returns, per node in that roadmap, the
   signal needed to WEIGHT sampling: due/overdue state (from `Activity.next_review_at`) and recent
   accuracy (from the user's last ~10 `TestAttempt` rows for that roadmap, aggregated in Python —
   no JSONB query gymnastics at this scale).
2. **Frontend fetches the bank JSON** (`/content/roadmaps/<key>/_test/<phase>.json`, static) and
   samples ~8–10 questions: weight toward nodes that are due/overdue or have low recent accuracy,
   enforce the bank's own mix (≥3 types, ≥25% traps, ≤20% MCQ — already true of a well-authored
   bank; the sampler just needs to not accidentally drop them), shuffle question order AND (for MCQ)
   option order.
3. **One pass.** No same-session repeat quizzing (that measures short-term memory, not learning —
   FSRS already owns spaced re-testing). A **redemption lap** at the END of the session re-asks only
   the questions the student got `wrong`/`missed` — this is the one legitimate in-session repeat,
   framed to the student as practice, not double-counted in the score or the FSRS bridge.
4. **Grading per type** (client-side, deterministic, except fillup):
   - `numeric`: `abs(answer - correct) <= tolerance`.
   - `code-output`: trimmed string compare against `answer` (this is "predict what it prints" —
     no execution needed, the student never runs code).
   - `code-fix` / `code-write`: run via `pyodideRunner` (existing CDN-lazy Pyodide) — exec the
     student's code, then run `asserts`; pass = all asserts pass, no exception.
   - `query-write`: run via `pgliteRunner.runSql(studentQuery, schema_sql)` — compare the result set
     against running `canonical_query` the same way (`order_matters` controls list vs set compare).
   - `mcq`: index compare; on wrong, look up `misconceptions[selectedIndex]` to show WHY that option
     is a real wrong answer (not just "incorrect").
   - `fillup`: **`POST /api/tests/grade-fillup`** — the one LLM call in this whole system. Grades the
     student's answer against the bank's `answer` (the reference/rubric), same trust model as the
     existing review grader. If `GRADER_ENABLED` is false or the call fails: show the canonical
     `answer` and let the student self-mark got/missed (same fallback pattern as `Review.jsx`).
5. **`POST /api/tests/attempts`** — submit the whole session's results at once. Backend: persists a
   `TestAttempt` row, computes the score (below), and runs the FSRS bridge (below).

## Outcome taxonomy

Every graded question resolves to exactly one of: **`got`** | **`missed`** (skipped / no attempt) |
**`wrong`** (attempted, incorrect). This is the user-specified trichotomy — `missed` is intentionally
NOT penalized the same as `wrong`; skipping honestly must never score worse than a bad guess would,
or the format rewards guessing.

## Scoring (feeds gamification; kept as a pure, auditable function)

```
got:                         +10  (+15 if trap: true — bonus for defeating an engineered trap)
missed:                        0  (no penalty — honesty costs nothing)
wrong, non-MCQ type:            0  (a genuine attempt that missed isn't punished beyond not scoring)
wrong, MCQ:                    -5  (guess penalty — offsets ~25% guess odds so E[guessing] < 0)
```
`score = sum(...)`, returned alongside `max_score = 10*n + 5*trap_count` (traps counted at their
bonus value) so the frontend can show a percentage. This function lives in
`app/services/test_scoring.py`, pure and unit-testable — no hidden state, so gamification/leaderboard
features can read it later without touching the grading path.

## FSRS bridge ("one brain, two sensors" — the constraint that must not be violated)

**Tests never create new cards and never accelerate on success.** Only `wrong`/`missed` outcomes
touch FSRS, and only for nodes that already have an `Activity` (i.e. the student tapped "Add to
reviews" on that lesson at some point) with a currently-OPEN `Review` (`status='due'`):

- For each **unique** `node_title` in the submitted results with outcome `wrong` or `missed`:
  1. Find the `Activity` for `(user_id, node)` via `RoadmapNode.title == node_title AND
     RoadmapNode.roadmap_id == roadmap.id`, then the Activity's open `Review` (`status='due'`).
  2. If found: mark that Review `status='superseded'` (a THIRD status, distinct from `due`/
     `completed` — it will not match either filter used anywhere in `dashboard.py`/`reviews.py`, so
     it cannot inflate completed-review counts or be double-surfaced as still-due).
  3. Call `apply_fsrs(activity, RATING_AGAIN, now)` — the exact same function `/reviews/{id}/complete`
     uses for a lapse — which advances the Activity's stability/difficulty and returns a fresh
     `Review(status='due', scheduled_for=...)`. Add it.
  4. If no Activity/open-Review exists for that node: do nothing to FSRS. The question still counts
     for score and for the weights aggregate (`test_attempts`), but a test never silently opts a
     lesson into spaced repetition — "Add to reviews" stays the one explicit entry point.
- **`got` outcomes never touch FSRS.** A single correct test answer does not extend a review
  interval — that would let a lucky guess (or a different recall format than the review itself
  uses) push out a card's real schedule. FSRS intervals are earned only through the review loop.

This keeps exactly one scheduler. The quiz is a sensor that can only ever pull a date CLOSER, never
push it further, and only for cards already in rotation.

## Data model

```python
class TestAttempt(SQLModel, table=True):
    __tablename__ = "test_attempts"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID
    roadmap_id: uuid.UUID = Field(foreign_key="roadmaps.id")
    phase: str                      # bank's phase name, e.g. "Class 9 - Motion"
    score: int
    max_score: int
    results: dict = Field(sa_column=Column(JSONB))  # [{question_id, node_title, type, outcome, trap, misconception}]
    created_at: datetime = Field(default_factory=datetime.utcnow)
```
No separate `node_mastery` table in v1 — per-node accuracy for `/weights` is computed by scanning
the user's recent `TestAttempt.results` in Python (cheap at pilot scale; revisit only if it's ever
a real query-time cost). This is a deliberate scope cut, not an oversight.

## Endpoints (all under `/api/tests`, mirrors `reviews.py` conventions exactly)

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/weights` | required | per-node due/accuracy signal for client-side sampling |
| POST | `/grade-fillup` | required | one LLM call, graded against the bank's reference answer |
| POST | `/attempts` | required | submit a completed session; persists + scores + FSRS bridge |

## Content validator

`content/validate.py` gets a `kind: "test"` branch (file lives under `_test/`, not matched by the
existing `*/*.json` roadmap-lesson glob — needs a second glob, same fix already applied for
`_numericals/`). Validates: `phase` present, `questions` non-empty, every question has `id` (unique
in file) + `node` (must resolve to a real lesson slug in that roadmap folder) + `type` (one of the
7) + `prompt` + `explain`; type-specific required fields per `PROMPT-tests.md`; `trap: true` requires
non-empty `trap_note`; `mcq` requires `options`/`answer`/`misconceptions` (same length as options).

## Explicit non-goals for this pass (documented cuts, not gaps)

- No leaderboard/streak UI — score is computed and returned; surfacing it beyond the completion
  screen is a follow-up.
- No `node_mastery` table / roadmap-graph mastery coloring — computed ad hoc from `TestAttempt` for
  now.
- No server-side code/query execution — grading is 100% client-side except the one fillup LLM call,
  matching the existing "no sandbox costs" constraint.
