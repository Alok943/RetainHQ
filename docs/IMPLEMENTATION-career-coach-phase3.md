# Implementation Plan — Career Coach Phase 3 (Scheduler & Today Screen)

**For the implementer (Sonnet).** `SPEC-career-coach-phase3.md` owns *what and why* and is the
authority on intent — read it once before starting. **This doc owns exactly how**: file paths,
signatures, data shapes, test names, and the order to build in. Where the spec left something
ambiguous, this doc decides it (every such decision is marked **[DECISION]** with its reasoning,
so a reviewer can overrule it in one place rather than hunting through code).

**Do not re-derive decisions already made here.** If you disagree with one, say so in your report
and implement it as written anyway — except where following it would produce a bug, in which case
stop and say why.

Written 2026-07-26. Status of the world at that date: **nothing in phase 3 exists.** No
`services/planner.py`, no `/api/career/today`, no `daily_minutes` column. Phases 1 and 2 are
shipped and are your inputs.

---

## 0. Preflight — repo conventions you will otherwise violate

These are from `CLAUDE.md` and are non-negotiable. Most phase-3 bugs will come from here, not
from the algorithm.

| Rule | What it means for you |
|---|---|
| **Async DB** | Eager-load relationships with `selectinload`. Lazy attribute access on a closed async session raises `MissingGreenlet`. Sessions use `expire_on_commit=False`. |
| **Auth object** | `get_current_user` returns `SupabaseUser` — attribute access (`.id`), never dict. `current_user.id` is a **string**; cast with `uuid.UUID(...)` before any query. |
| **Authorization** | Every query scoped by `user_id`. Mutating routes verify ownership in the `WHERE` (`WHERE id = :id AND user_id = :uid`). An IDOR test is mandatory for every new route. |
| **Pydantic v2** | Response schemas that serialize ORM objects need `model_config = ConfigDict(from_attributes=True)`. |
| **Migrations** | Alembic only. Never hand-edit the live DB. `career_goals` already has RLS, so no new RLS statement is needed for a column add. |
| **Timestamps** | Naive-UTC in the DB. Normalize any tz-aware input with `.astimezone(timezone.utc).replace(tzinfo=None)`. |
| **Trailing slashes** | Collection POSTs use a trailing slash. Match existing paths exactly to avoid 307s. |
| **Commits** | No `Co-Authored-By: Claude` trailer. **Never push.** Deploy only on an explicit "push" from the owner. |
| **Dark mode** | Reuse existing color classes and it is free. New hardcoded hex values break it. |

Run the suite with:

```bash
cd backend && .\.venv\Scripts\python.exe -m pytest -q
```

Baseline as of 2026-07-26 is **198 passed**. Do not finish with fewer.

---

## 1. Scope — and the one gate you cannot pass

Build **steps 1–5** of the spec's §8 build order. That is: golden suite, pure planner, migration,
routes, Today card.

**Do NOT do step 6 (constant tuning), and do not pretend to.** The spec's §9 step-0 gate requires
≥2 weeks of the owner's real dogfood evidence before touching the §7 constants. On 2026-07-26 a
`TRUNCATE … CASCADE` destroyed every `activities` and `reviews` row (see `DECISIONS.md` D-039),
and `learning_events` holds exactly **1** row. That evidence no longer exists and cannot be
rebuilt.

Consequences you must respect:

- Ship the §7 constants at their **specified defaults**, as named module-level constants. Do not
  tune them. Do not "improve" them because a golden scenario looks nicer with a different value —
  if a scenario needs a different constant, the *scenario* is wrong, or the spec is, and you say
  so in your report.
- Write G-fixtures from **synthetic** data. That is explicitly permitted by §8 step 0.
- The spec's Definition of Done includes "owner has followed 3 real daily plans". You cannot
  satisfy that. Leave it unchecked and say so.

### Out of scope (do not build)
Weekly report · coach agent · confidence probes · LeetCode/GitHub sync · companion apps · **any
LLM call whatsoever** (this scheduler is fully deterministic) · template-upgrade UX · goal
switch/restore UX · a `day_plans` table (the plan is derived, never stored).

---

## 2. File manifest

Create:

| Path | What |
|---|---|
| `backend/app/services/planner.py` | Pure core. No DB, no `datetime.now()`. |
| `backend/tests/test_planner.py` | G1–G10. Written **before** `planner.py`. |
| `backend/tests/test_career_today.py` | Route-level tests. |
| `backend/alembic/versions/<rev>_add_daily_minutes.py` | One column. |
| `backend/tests/goldens/plan_g1.json`, `plan_g4.json`, `plan_g7.json` | Exact-output snapshots. |

Modify:

| Path | What |
|---|---|
| `backend/app/models/models.py` | `CareerGoal.daily_minutes` |
| `backend/app/schemas/career.py` | Plan response schemas + `GoalPatchIn` + `TodayFeedbackIn` |
| `backend/app/api/routes/career.py` | 3 new routes |
| `frontend/src/CareerTree.jsx` | `TodayCard` + `BalanceStrip` |
| `docs/SYSTEM-OVERVIEW.md` | §1 services/routes, §2 column, + one changelog line |
| `docs/DECISIONS.md` | one entry (see §9) |
| `docs/BACKLOG.md` | groom: add the deferred tuning item |

---

## 3. The pure core — `services/planner.py`

**Hard constraints.** No imports from `app.models`, `app.core.database`, or anything async. No
`datetime.now()` / `date.today()` — the clock is an input. No randomness. Same inputs → byte-identical
output, forever.

### 3.1 Constants (module level, exact values — do not tune)

```python
PREREQ_UNLOCK_THRESHOLD = 0.35   # matches the 'practicing' state boundary
URGENCY_MAX             = 2.0
UNLOCK_BONUS            = 0.05   # per dependent
UNLOCK_WEIGHT_CAP       = 1.5
BALANCE_WINDOW_DAYS     = 21
BALANCE_FLAG_THRESHOLD  = -0.15
BALANCE_MIN_WINDOW_MINUTES = 120  # evidence floor — see §3.8. NOT in the spec; added 2026-07-26.
REVIEW_COST_MIN         = 4
MAX_STUDY_ITEMS         = 5
DAILY_MINUTES_DEFAULT   = 60
MASTERED_THRESHOLD      = 0.85   # G8's 'tree complete' bar
```

### 3.2 Input/output dataclasses

Plain `@dataclass(frozen=True)`. Not Pydantic — this layer has no serialization concerns.

```python
@dataclass(frozen=True)
class PlanNode:
    node_id: str            # str, not UUID — keeps the core free of uuid semantics
    title: str
    subject: str
    priority: int           # 1..5 from node_meta
    est_effort_min: int
    order_index: int        # template order; the deterministic tie-break
    m_learned: float        # 0..1, evidence-accumulated. Gates prerequisites.
    m: float                # m_learned * retrievability. Drives the score.
    prereq_ids: tuple[str, ...]

@dataclass(frozen=True)
class PlanReview:
    review_id: str
    label: str              # node_title or activity title, for the UI
    scheduled_for: datetime

@dataclass(frozen=True)
class PlanInputs:
    nodes: tuple[PlanNode, ...]
    due_reviews: tuple[PlanReview, ...]     # ALREADY ordered oldest-first by the route
    subject_time_shares: dict[str, float]   # subject -> a_s, share of trailing-window minutes
    total_window_minutes: int               # raw minutes behind those shares — the §3.8a floor
    sprint_node_id: str | None
    sprint_until: date | None
    target_date: date | None
    daily_minutes: int
    now: datetime                           # naive UTC

@dataclass(frozen=True)
class PlanItem:
    kind: str               # 'review' | 'study' | 'balance'
    review_id: str | None
    node_id: str | None
    label: str
    reason: str             # REQUIRED, never empty — the trust surface
    est_share: float        # 0..1 of the post-review budget; 0.0 for reviews

@dataclass(frozen=True)
class DayPlan:
    items: tuple[PlanItem, ...]
    balance: dict[str, float]     # subject -> a_s - p_s
    overflow: bool
    tree_complete: bool
```

### 3.3 `build_plan(inputs: PlanInputs) -> DayPlan`

Execute in this order.

**Step 1 — reviews.** Every review in `inputs.due_reviews`, in the given order, becomes a
`PlanItem(kind='review', est_share=0.0, reason='due review')`. Never reorder, never drop, never
add. This is the law (§1 of the spec).

**Step 2 — budget.** `review_cost = len(due_reviews) * REVIEW_COST_MIN`. If
`review_cost >= daily_minutes`: set `overflow=True`, return **reviews only** — no study items.
Otherwise `overflow=False` and `study_budget = daily_minutes - review_cost`.

> `study_budget` proportions the plan; it is never surfaced as a wall-clock promise. Spec §0
> precondition 2: `est_effort_min` is 3–5× optimistic.

**Step 3 — tree_complete.** `all(n.m_learned >= MASTERED_THRESHOLD for n in nodes)` (vacuously
`False` when `nodes` is empty — an empty tree is not a completed one). If true, return reviews
only with `tree_complete=True`. **Invent no study items.**

**Step 4 — frontier.** A node is available iff, for every `p` in `prereq_ids`, the node with that
id has `m_learned >= PREREQ_UNLOCK_THRESHOLD`. A prereq id not present in `nodes` counts as
`m_learned = 0.0` → **not available**. Also exclude nodes already at `m_learned >= MASTERED_THRESHOLD`.

> **[DECISION]** A dangling prereq id blocks rather than unlocks. The spec says "deleted/absent
> mastery rows count as 0", which is about missing *mastery*; a missing *node* is a different case
> it does not name. Blocking is the conservative reading — it can only delay a node, never
> recommend one whose foundation is unverified.

**Step 5 — score.**

```
score(n) = n.priority * (1 - n.m) * urgency * unlock_weight(n)
```

- `urgency`: `1.0` if `target_date is None`. Otherwise let
  `days_left = (target_date - now.date()).days`. Anchor the timeline at
  `PLAN_HORIZON_DAYS = 180`:
  `urgency = 1.0 + (URGENCY_MAX - 1.0) * clamp(1 - days_left / PLAN_HORIZON_DAYS, 0.0, 1.0)`.
  A past-due `target_date` yields `URGENCY_MAX`. **Never below 1.0.**

  > **[DECISION]** The spec says urgency scales "per remaining-fraction of the goal's timeline"
  > but the goal has no stored start date, so "the timeline" is not derivable. A fixed 180-day
  > horizon is the smallest honest substitute. Add `PLAN_HORIZON_DAYS = 180` to §3.1 and flag it
  > in your report — this is the constant most likely to be wrong.

- `unlock_weight(n)`: `min(1 + UNLOCK_BONUS * dependents(n), UNLOCK_WEIGHT_CAP)` where
  `dependents(n)` = count of nodes listing `n.node_id` in their `prereq_ids` (direct only, not
  transitive).

**Step 6 — ordering.** Sort frontier by `(-score, -priority, order_index)`. That triple is fully
deterministic given the inputs; never sort by anything with an unstable value.

**Step 7 — sprint.** If `sprint_node_id` is set **and** `sprint_until is not None` **and**
`now.date() <= sprint_until` **and** the sprint node is in the frontier: move it to position 0.
Reason: `"sprint: you pinned this until {sprint_until}"`. An expired or mastered sprint is ignored
entirely (G6: the plan must be identical to the no-sprint plan).

**Step 8 — balance.**

**Step 8a — the evidence floor. Check this FIRST.** If
`inputs.total_window_minutes < BALANCE_MIN_WINDOW_MINUTES`, emit **no balance item at all** and
return `balance={}`. Skip the rest of step 8 entirely.

> **[DECISION]** This gate is **not in the spec** and is the most important correction in this
> doc. Without it the rule misfires on exactly the user it matters most for. With no logged time,
> `a_s = 0` for every subject, so `balance_s = -p_s`, and the *most negative* subject is simply the
> *largest* one. Every subject holding >15% of the tree's priority trips the -0.15 threshold. The
> result: every new user's first plan opens with "dsa is under-served — 0% of your time vs 25% of
> your plan", on a day when they have done nothing and nothing can be under-served. The same
> failure persists in miniature at low volume — 30 minutes of DSA gives `a_dsa = 1.0` and flags
> every other subject off a single session.
>
> This is what `ARCHITECTURE-learning-system.md` §5.0 and D-038 already forbid: an inference with
> no evidence behind it must not drive a user-visible recommendation. 120 minutes across a 21-day
> window is a deliberately low bar — enough that the ratio means something, low enough that it
> stops gating within the first week of real use. Flag it for tuning alongside the §7 constants.

Otherwise compute `p_s` = subject's share of `sum(priority)` over **all** nodes (not just
frontier), `a_s = subject_time_shares.get(subject, 0.0)`, `balance_s = a_s - p_s`, for every
subject present in `nodes`. Then:

- Find the subject with the **most negative** `balance_s`.
- If that value `< BALANCE_FLAG_THRESHOLD` **and** the subject is not the active sprint node's
  subject **and** it has at least one frontier node: take its best-scoring frontier node, mark it
  `kind='balance'`, and place it **after the sprint item if one exists, otherwise at position 0**.
  Reason: `"{subject} is under-served: {pct}% of your time vs {pct}% of your plan"`.
- **At most one balance item, ever.** It is a nudge, not a takeover.

> **[DECISION]** Spec rule 5 says the sprint node is "the first study item" and rule 4 says the
> balance item is promoted "into slot 1" — these collide when both fire. Sprint wins slot 0
> because it is an explicit user declaration, and balance is an inference; the asymmetry rule
> (`ARCHITECTURE-learning-system.md` §5.0) says inference may reorder but must not override what
> the user directly asked for. G5 must assert this ordering.

**Step 9 — truncate and proportion.** Take the first `MAX_STUDY_ITEMS` study items. **Always keep
at least 1** even if `study_budget` is tiny (spec rule 6). Then
`est_share = n.est_effort_min / sum(est_effort_min of selected)`. Shares sum to 1.0 within float
tolerance; assert this in G7.

**Step 10 — reasons.** Every item carries a non-empty `reason`. Study-item default:
`"unlocks {k} nodes in {subject}"` when `dependents > 0`, else
`"{subject}: highest-priority available"`. A missing reason is a test failure, not a cosmetic one.

---

## 4. Golden suite — `tests/test_planner.py`, written FIRST

Write all ten as **failing** tests before `planner.py` exists. Table-driven where it fits. Build a
`make_inputs(**overrides)` helper so each scenario states only what it changes.

| # | Scenario | Assertions |
|---|---|---|
| G1 | Cold start: all `m_learned=0`, no reviews, 60 min, `total_window_minutes=0` | Only nodes with no prereqs; `len(items) <= 5`; every `reason` non-empty; **`balance == {}` and NO item has `kind=='balance'`** (§3.8a — this is the new-user case and the rule must stay silent); **snapshot** `plan_g1.json` |
| G2 | 10 due reviews, `daily_minutes=30` | 10 review items, **0** study items, `overflow is True`; review ids in input order |
| G3 | `target_date` in 14 days vs same inputs open-ended | Crunch plan's study set ⊇ the open-ended plan's higher-priority nodes; review list identical between the two |
| G4 | `os` subject at `a_s - p_s = -0.30`, frontier available, `total_window_minutes=600` | Exactly one `kind=='balance'`; it is at index 0 of the study items; reason contains `"os"`; **snapshot** `plan_g4.json` |
| G4b | **Same inputs as G4 but `total_window_minutes=119`** | No balance item; `balance == {}`. The shares are identical — only the evidence behind them is thin. Sub-threshold volume must not produce a confident nudge. |
| G5 | Sprint active on a `dsa` node **and** `dsa` neglected | Sprint item at study index 0; **no** balance item for `dsa`; a different neglected subject is still flaggable |
| G6 | `sprint_until` = yesterday | Plan `==` the plan built with `sprint_node_id=None` |
| G7 | Mixed mastery, 3 due reviews, 90 min | All reviews precede all study; every study node's prereqs `>= 0.35`; `abs(sum(est_share) - 1.0) < 1e-6`; **snapshot** `plan_g7.json` |
| G8 | All nodes `m_learned >= 0.85` | `tree_complete is True`; zero study items |
| G9 | **Property test.** Random 200-node DAGs, random mastery, 50 seeds | No item ever has an unmet prerequisite; same seed → identical plan |
| G10 | **Property test.** Every scenario above | `[i.review_id for i in plan if i.kind=='review'] == [r.review_id for r in inputs.due_reviews]`, same order, and no study item appears before any review |

**Snapshot convention** (mirrors the DSA goldens): serialize the `DayPlan` to JSON with sorted
keys, compare to the committed file. A diff is a deliberate decision — update the snapshot in the
**same commit** as the change that caused it, and say why in the commit body. Never regenerate
snapshots to make a red test green without understanding the diff.

G9 builds DAGs by generating nodes in topological order and only ever pointing prereqs backwards —
that guarantees acyclicity without a cycle check. Use `random.Random(seed)`, never the global
`random`.

---

## 5. Migration

```python
op.add_column('career_goals', sa.Column(
    'daily_minutes', sa.Integer(), nullable=False, server_default=sa.text('60')))
op.create_check_constraint(
    'ck_career_goals_daily_minutes', 'career_goals',
    'daily_minutes BETWEEN 30 AND 240')
```

`down_revision` = the current head. Check it with `alembic history` rather than assuming — as of
2026-07-26 the head is `a9d4f7c2e618` (the TRUNCATE guard), **not** the leetcode migration.
`career_goals` already has RLS; no new RLS statement.

Add `daily_minutes: int = Field(default=60, ge=30, le=240)` to `CareerGoal` in `models.py`.

Do **not** run `alembic upgrade head` against production. Leave that to the owner.

---

## 6. Routes — `api/routes/career.py`

### `GET /api/career/today`

1. Load the active goal (`status='active'`, `user_id=uid`). No goal **or** `roadmap_id is None`
   → **404**. The plan function must never see a treeless goal.
2. One query pass to assemble inputs — nodes joined to `node_meta` and `node_mastery`
   (`LEFT JOIN`; absent mastery ⇒ `m_learned=0.0`), plus prerequisite edges, plus due reviews.
   **Use `selectinload` for anything you touch after the session closes.**
3. `m` per node: `m_learned * retrievability`, using the phase-1 read-side
   (`services/evidence.displayed_mastery` / `retrievability_for`). Do **not** re-derive decay math
   inside the planner — that is exactly the duplication the pure/shell split exists to prevent.
4. `subject_time_shares`: sum `learning_events.duration_min` per subject over the trailing
   `BALANCE_WINDOW_DAYS`, filtered to `deleted_at IS NULL`, normalized to shares. All-zero total ⇒
   every share `0.0` (do not divide by zero). Pass the **unnormalized** total as
   `total_window_minutes` — the planner needs the raw magnitude, not just the ratios, to apply the
   §3.8a evidence floor.
5. Due reviews: reuse the existing `/api/reviews/due` query shape — `status='due'`,
   `scheduled_for <= now`, `ORDER BY scheduled_for ASC`, `LIMIT REVIEW_SESSION_CAP`. Import the
   cap from `services/scheduler`; do not hardcode 10.
6. **Lazily clear an expired sprint**: if `sprint_until` is set and `< today`, null both sprint
   fields and commit. Do this *before* building inputs.
7. Call `build_plan`, serialize, return.

### `PATCH /api/career/goals/active`

Body `{"daily_minutes": int}`. Clamp to 30–240 **server-side** (do not merely validate — clamp, so
a slider that overshoots does not 422). Scoped by `user_id`. Returns the updated `CareerGoalOut`.

### `POST /api/career/today/feedback`

Body `{"item_ref": str, "action": "done" | "skipped"}`. Writes a `metric_events` row via
`record_metric_event(db, user_id, event_type="plan_item_feedback", payload={...})`. **Mutates no
plan state** — the next `GET /today` recomputes from scratch. Returns 204.

### Response shape

```json
{
  "items": [
    {"kind": "review", "review_id": "…", "node_id": null,
     "label": "Two Sum", "reason": "due review", "est_share": 0.0}
  ],
  "balance": {"dsa": 0.12, "os": -0.21},
  "overflow": false,
  "tree_complete": false,
  "daily_minutes": 60
}
```

### Route tests — `tests/test_career_today.py`

Mandatory: 404 without a goal · 404 with a goal but no committed tree · `daily_minutes` clamp at
both ends · feedback writes exactly one `metric_events` row · **IDOR: user B gets 404 on A's plan
and cannot PATCH A's goal** · expired sprint is cleared by the GET and the response reflects it.

Use the existing `client` / `db` / `as_user` fixtures from `tests/conftest.py`. **Do not** mutate
`app.dependency_overrides` at module import time — a test file in this repo did exactly that and
silently leaked its auth override into every other module (fixed 2026-07-26 in
`test_leetcode_evidence.py`; do not reintroduce the pattern).

---

## 7. Frontend — `CareerTree.jsx`

A `TodayCard` at the top of the existing tree view. **No new page, no new route** — Today is a
section; the tree stays the home surface.

- Ordered checklist. Reviews link to `/reviews`; study/balance items deep-link to the node.
- Each item renders its `reason` line beneath the label — this is the trust surface, not
  decoration. Do not truncate it away on mobile.
- `kind='balance'` gets a distinct but quiet treatment (a small label, not a colored alarm).
- `BalanceStrip` under the list: one small over/under bar per subject from `plan.balance`.
- `overflow` → an honest line: "Today's reviews fill your time — no new material."
- `tree_complete` → "Nothing new to study. Reviews only." Never invent filler.
- A `daily_minutes` control (30–240) that `PATCH`es and refetches.
- Loading and error states must follow the pattern established in `Home.jsx` on 2026-07-24: track
  **fetch failure separately from genuine emptiness**, and render an explicit error + Retry. A
  failed `/today` must never render as "you have nothing to do today". This exact conflation was a
  shipped bug; do not repeat it.
- Reuse existing color classes only → dark mode is free.

Verify in a real browser, not just tests. The repo has caught bugs this way that SQLite could not
(FK ordering, a `useEffect` returning a Promise). Confirm: a plan renders, reasons are visible,
the minutes control round-trips, and the console is clean.

---

## 8. Build order

Each step ends with a green suite. Do not proceed on red.

0. Read `SPEC-career-coach-phase3.md` §1–§7 and `ARCHITECTURE-learning-system.md` §5.0.
1. G1–G10 + fixtures, all failing. **No planner code yet.**
2. `planner.py` until G1–G10 are green. Commit the three snapshots as generated *after* you have
   read them and agree they are correct.
3. Migration + model field. `alembic history` to confirm the head. Do not upgrade prod.
4. The three routes + `tests/test_career_today.py`.
5. `TodayCard` + `BalanceStrip` + live browser verification.
6. **SKIPPED — blocked.** Constant tuning needs dogfood evidence that no longer exists (§1).
7. Docs in the same commit: SYSTEM-OVERVIEW §1/§2 + changelog line, DECISIONS entry, BACKLOG grooming.

**Do not push.**

---

## 9. Docs you must write (same commit)

- **`SYSTEM-OVERVIEW.md`** — §1 gains `services/planner.py` and the three routes; §2 gains
  `career_goals.daily_minutes`; one changelog line at the top, newest first.
- **`DECISIONS.md`** — one entry covering: pure planner with no `day_plans` table (the plan is
  derived, so it can always be recomputed and therefore trusted); FSRS non-interference as an
  enforced law with its own property test; and the sprint-beats-balance precedence from §3.8.
  Include the tradeoffs and what you rejected.
- **`BACKLOG.md`** — add: "Tune the §7 planner constants against real dogfood evidence once ≥2
  weeks have re-accumulated post-D-039 — shipped at spec defaults, never validated against a real
  plan (2026-07-26)". Also add the `PLAN_HORIZON_DAYS` flag from §3.5.

---

## 10. Definition of done

- [ ] G1–G10 green, including both property tests and three committed snapshots
- [ ] Full backend suite ≥ 198 passed, 0 failed
- [ ] `GET /api/career/today` returns a plan with a non-empty `reason` on **every** item
- [ ] FSRS review flow untouched — `tests/` for reviews unmodified and passing
- [ ] Sprint mode works end-to-end: `POST /sprint` → visible as study item 0 in the next `GET /today`
- [ ] IDOR tests green on all three routes
- [ ] Today card verified in a live browser, console clean
- [ ] Docs updated in the same commit
- [ ] ~~Owner has followed 3 real daily plans~~ — **blocked, see §1. Leave unchecked.**

---

## 11. Report back

1. Each **[DECISION]** in this doc: agree or disagree, with reasoning. `PLAN_HORIZON_DAYS`
   (§3.5) and sprint-beats-balance (§3.8) are the two most likely to be wrong; the §3.8a evidence
   floor is the one most likely to need a different *value*.
2. **`BALANCE_FLAG_THRESHOLD` is subject-count-sensitive — measure it and report.** `p_s` is a
   share, so it shrinks as a template adds subjects. On a 10-subject tree the average `p_s` is
   0.10, so a subject with **zero** logged time sits at `-0.10` and can never reach the `-0.15`
   threshold — the rule would only ever flag the two or three biggest subjects and would be
   structurally blind to a genuinely neglected small one. On a 4-subject tree (`p_s = 0.25`) it
   fires constantly. Compute the actual `p_s` distribution for `backend.v2`, `ai_engineer.v2` and
   `sde_generalist.v2` and state, per template, which subjects can ever trip the flag. Do **not**
   change the constant — report the numbers so it can be decided with evidence.
3. The three snapshot plans, verbatim, with a one-line judgement of whether each looks like
   something a person would actually follow.
4. Anything the spec got wrong — spec edit before code, per the parent rule.
5. Confirm you did **not** tune any constant, and did **not** push.
