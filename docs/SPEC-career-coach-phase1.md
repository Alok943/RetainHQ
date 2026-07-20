# Career Coach — Phase 1 Implementation Spec: The Evidence Spine

**Status:** Ready to implement · **Owner:** Alok · **Date:** 18 Jul 2026
**Parent doc:** `retainhq-career-coach-design-doc.md` (v1.2) — that doc owns *what and why*; this doc owns *exactly what ships in phase 1*.
**Maps to parent §17:** Phase 0 (Contract) + the Evidence Engine half of Phase 1.

---

## 0. Why this is the first phase

The parent doc's Phase 1 bundles four hard things (tree generation, evidence engine, LeetCode ingestion, scheduler + Today screen). Shipping them together means the first thing you can test is the last thing you build, and the riskiest unknown — *does typed evidence produce a mastery number that feels honest?* — is answered last.

This phase inverts that. It builds **only the immutable event log and the deterministic mastery function**, wired to producers that already exist in RetainHQ. It has:

- **no LLM calls** (topic mapping is exact-match only here),
- **no external integrations** (LeetCode is explicitly deferred — it's the parent doc's one blocking open question),
- **no scheduler** (the highest-risk component gets its own phase, with the golden-scenario suite),
- **no new user-facing UI** beyond one debug surface.

What it produces is the thing every later phase reads from. Per Design law 2, mastery state is a derived cache — so getting the *event log* right matters more than getting the *weights* right, and weights stay config-tunable forever.

**Exit criterion (verbatim from parent §17 Phase 0, plus one):** two producers write the same table; and `GET /api/evidence/nodes` returns a mastery number for the owner's real RetainHQ history that the owner reads and agrees with. If the number feels wrong, phase 1 is not done — that's the whole point of doing this first.

### Explicitly out of scope for this phase
Taxonomy/tree generation · role templates · diagnostic · LeetCode or GitHub sync · balance score · daily scheduler · Today screen · weekly report · coach agent · companion · confidence probes · LLM-assistance redemption · frontend beyond §7.

Do not build these. If something here seems to need one of them, it's a spec bug — flag it rather than expanding scope (parent §17 scope rule: additions require a removal).

---

## 1. Repo context you need

Read `CLAUDE.md` first; it overrides anything here that conflicts. Key constraints that bite in this phase:

- **Backend is the only DB gateway.** No `supabase.from(...)` in React.
- **Schema changes go through Alembic.** Every new table's migration MUST include `ENABLE ROW LEVEL SECURITY` (no policies). See `backend/alembic/versions/f8a3b5c2d9e1_enable_rls_public_tables.py` for the existing pattern.
- **Async SQLAlchemy:** eager-load with `selectinload`; sessions are `expire_on_commit=False`.
- **Auth:** `get_current_user` returns a `SupabaseUser`; use attribute access (`.id`), and it's already a `uuid.UUID`-castable string — follow how `backend/app/api/routes/reviews.py` does it.
- **Authorization:** every query scoped by `current_user.id`; mutations use `WHERE id = :id AND user_id = :uid`.
- **Pydantic v2:** response models over ORM objects need `model_config = ConfigDict(from_attributes=True)`.
- **Trailing slashes:** collection POST routes end with `/`.
- **Timestamps:** naive UTC in the DB (`datetime.utcnow`), matching every existing model.
- **JSONB:** reuse the `_JSONB` variant already defined at the top of `backend/app/models/models.py` (it degrades to plain JSON under SQLite so the test suite's `create_all()` works).

Files you will touch:

| File | Change |
|---|---|
| `backend/app/models/models.py` | add `LearningEvent`, `NodeMastery` |
| `backend/alembic/versions/<new>.py` | create both tables + RLS + indexes |
| `backend/app/services/evidence.py` | **new** — weights, `w()`, mastery fold, recompute |
| `backend/app/services/evidence_weights.py` | **new** — versioned weights config |
| `backend/app/api/routes/evidence.py` | **new** — 3 endpoints |
| `backend/app/main.py` | register the router |
| `backend/app/api/routes/reviews.py` | emit an event on review completion |
| `backend/tests/test_evidence.py` | **new** — the suite in §8 |
| `docs/SYSTEM-OVERVIEW.md` | new tables + new router + changelog line, **same commit** |
| `docs/DECISIONS.md` | one entry (see §10) |

---

## 2. Data model

### 2.1 `learning_events` — immutable, append-only

The parent doc's §7 schema, mapped to the existing DB conventions. Add to `models.py`:

```python
class LearningEvent(SQLModel, table=True):
    """Immutable append-only evidence log — the source of truth for all mastery
    state (Career Coach design doc, Design law 2). Every producer (in-app review,
    manual log, and later LeetCode/GitHub/companion) writes this same shape.

    Rows are NEVER updated. Correction = insert a compensating event or soft-delete
    via `deleted_at` and recompute. Mastery in `node_mastery` is a derived cache and
    can be rebuilt from this table alone at any time."""
    __tablename__ = "learning_events"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(index=True)
    occurred_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    event_type: str            # see EVENT_TYPES
    trust_tier: str            # 'T1_verified_external' | 'T2_verified_internal' | 'T3_observed' | 'T4_claimed'
    source: str                # 'retainhq_review' | 'manual' | ... (see SOURCES)
    node_id: Optional[uuid.UUID] = Field(default=None, foreign_key="roadmap_nodes.id", index=True)
    duration_min: int = Field(default=0)
    difficulty: Optional[str] = None    # 'easy' | 'medium' | 'hard'
    assistance: Optional[str] = None    # 'none' | 'hint' | 'llm_assisted' | 'solution_seen'
    outcome: Optional[str] = None       # 'pass' | 'fail' | 'partial'
    grade: Optional[float] = None       # 0.0-1.0
    # Loose FK to the producing row (reviews.id, activities.id, ...). No constraint:
    # the referenced table varies by source. Doubles as the idempotency key with
    # (user_id, source) — see uq_learning_event_dedupe.
    entity_id: Optional[uuid.UUID] = Field(default=None, index=True)
    payload: dict = Field(default_factory=dict, sa_column=Column(_JSONB))
    # Soft delete only — user-requested evidence removal (design doc §14). Excluded
    # from recompute; the row survives so history stays auditable.
    deleted_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

**Deviations from the parent doc's §7 JSON, and why — each is deliberate:**

| Parent | Here | Reason |
|---|---|---|
| `topic_ids[]` (array) | single `node_id` FK | Phase 1 producers each map to exactly one node. A real FK gives referential integrity and cheap joins. Multi-node events land in a `topic_ids` payload key when a producer needs it (phase 2+), and the column can become a join table without touching the fold. |
| `ts` | `occurred_at` | `ts` collides with nothing but reads poorly; `created_at` (ingest time) is separate and both matter for late-arriving syncs. |
| `type` | `event_type` | `type` shadows a builtin; matches `MetricEvent.event_type`. |
| — | `deleted_at` | Required by design doc §14 (per-event delete → mastery recomputes) without breaking append-only. |
| — | `entity_id` | Idempotency. Non-negotiable: LeetCode polling in a later phase re-reads the same solve repeatedly, and a double-counted event silently inflates mastery. Build the guard now while there are two producers, not later while there are six. |

**Constraints on the table (in the migration):**

- `UNIQUE (user_id, source, entity_id) WHERE entity_id IS NOT NULL` — partial unique index, name `uq_learning_event_dedupe`. Ingest uses `ON CONFLICT DO NOTHING`.
- `CHECK (grade IS NULL OR (grade >= 0 AND grade <= 1))`
- `CHECK (duration_min >= 0)`
- `CHECK` on `trust_tier` and `event_type` against the enumerations in §3. Follow `d3a1f7c92e10_expand_tier_check.py` for the CHECK-constraint style already used here.
- Index `(user_id, node_id, occurred_at)` — the fold's read path.
- `ENABLE ROW LEVEL SECURITY` (no policies).

### 2.2 `node_mastery` — derived cache, safe to truncate

```python
class NodeMastery(SQLModel, table=True):
    """Derived mastery cache — one row per (user, node). Recomputable in full from
    `learning_events`; deleting this table costs only CPU. Never write it from
    anywhere except services/evidence.py."""
    __tablename__ = "node_mastery"
    __table_args__ = (UniqueConstraint("user_id", "node_id", name="uq_node_mastery"),)
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(index=True)
    node_id: uuid.UUID = Field(foreign_key="roadmap_nodes.id", ondelete="CASCADE", index=True)
    m_learned: float = Field(default=0.0)      # evidence-accumulated skill, 0-1
    evidence_count: int = Field(default=0)     # non-deleted events folded in
    last_event_at: Optional[datetime] = None
    exposure_capped: bool = Field(default=False)  # True if only T3-capped evidence exists
    weights_version: str                       # which weights table produced this
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

Note what is **not** stored: displayed mastery `m = m_learned × r`. `r` (FSRS retrievability) is computed at read time from the linked `Activity`'s `stability` / `last_reviewed_at` — it decays continuously, so caching it would serve stale numbers. `_retrievability()` already exists in `backend/app/services/scheduler.py`; import it, don't reimplement it.

Also not stored: node state (`unexposed`/`exposed`/…) and confidence — both are pure functions of `m` and evidence stats, derived on read.

---

## 3. Enumerations (single source of truth)

Put these in `backend/app/services/evidence_weights.py` as module constants and import everywhere. The API validates against them; the DB CHECK-constrains them.

```python
EVENT_TYPES = ("RECALL_GRADED", "PROBLEM_SOLVED", "ARTIFACT_BUILT",
               "CONCEPT_EXPLAINED", "CONTENT_CONSUMED", "TIME_BLOCK")
TRUST_TIERS  = ("T1_verified_external", "T2_verified_internal", "T3_observed", "T4_claimed")
SOURCES      = ("leetcode", "retainhq_review", "retainhq_coach", "github",
                "manual", "companion_desktop", "companion_android")
```

Ship all six event types and all four tiers now even though phase-1 producers only emit two. The weights table is total over the enumeration, so later producers need zero engine changes — that's the whole point of the contract phase.

---

## 4. Weights (`evidence_weights.py`)

```python
WEIGHTS_VERSION = "v0"
```

Transcribe the parent doc's §9 table exactly. Key it by `(event_type, outcome, difficulty, assistance)` with `None` as a wildcard, most-specific match wins:

| event_type | outcome | difficulty | assistance | w |
|---|---|---|---|---|
| PROBLEM_SOLVED | pass | hard | none | 0.35 |
| PROBLEM_SOLVED | pass | medium | none | 0.25 |
| PROBLEM_SOLVED | pass | medium | hint | 0.15 |
| PROBLEM_SOLVED | pass | medium | llm_assisted / solution_seen | 0.06 |
| PROBLEM_SOLVED | pass | easy | none | 0.10 |
| PROBLEM_SOLVED | fail | * | * | 0.03 *(only if `duration_min >= 15` — genuine attempt; else 0.0)* |
| RECALL_GRADED | * | * | * | 0.20 × grade |
| CONCEPT_EXPLAINED | * | * | * | 0.18 × grade |
| ARTIFACT_BUILT | * | * | * | 0.30 |
| CONTENT_CONSUMED | * | * | * | 0.04, caps node at m_learned ≤ 0.35 |
| TIME_BLOCK | * | * | * | 0.00 |

Gaps the parent table leaves open — fill them as follows and note the choice in a code comment (these are the honest-direction defaults per Philosophy #3, "mastery may understate; it must never overstate"):

- **PROBLEM_SOLVED pass, hard, hint** → 0.21 · **hard, llm_assisted/solution_seen** → 0.08
- **PROBLEM_SOLVED pass, easy, any assistance** → 0.04
- **PROBLEM_SOLVED `outcome=partial`** → half the corresponding `pass` weight
- **Missing `difficulty`** → treat as `medium`. **Missing `assistance`** → treat as `llm_assisted` (the conservative assumption, not the flattering one)
- **`grade` missing on RECALL_GRADED / CONCEPT_EXPLAINED** → w = 0.0, and log a warning: an ungraded "graded" event is a producer bug

### 4.1 The `w()` interface — mandatory shape

Parent §9 requires `w` to be an interface, not a lookup. Implement it with the full signature from day one even though v1 ignores two arguments:

```python
def w(event: LearningEvent, node_state: NodeMastery | None,
      user_history: dict | None = None) -> float:
    """Evidence weight for one event. v1 = table lookup + modifiers; `node_state`
    and `user_history` are unused but present so contextual/learned weights can
    land later without touching any caller."""
```

Every caller uses this signature. Do not let a caller reach into the table directly — that shortcut is what makes the interface unreplaceable later.

### 4.2 Two hard rules the tiers impose

Enforce these in `w()` (or immediately around it), not in the callers, and give each its own test:

1. **T4 can never move mastery.** `if event.trust_tier == "T4_claimed": return 0.0` — before any table lookup. Design doc §8, non-negotiable.
2. **T3 caps exposure.** T3 events (and any `CONTENT_CONSUMED`) may raise `m_learned` no higher than **0.35**. Implement in the fold: `if capped and m_learned_after > 0.35: m_learned_after = max(m_learned_before, 0.35)`. Note the `max` — an already-higher node earned from T1/T2 evidence must never be *dragged down* by watching a video.

---

## 5. The fold (`evidence.py`)

One pure function, no DB access, fully unit-testable:

```python
def fold_events(events: list[LearningEvent]) -> NodeMasteryResult:
    """Replay events in occurred_at order → mastery state. Pure: same input,
    same output, no I/O. This is the ONLY place m_learned is produced."""
```

Rules:

- Sort by `occurred_at` ascending, tie-break by `id` so replays are deterministic.
- Skip `deleted_at IS NOT NULL`.
- Update rule (parent §9): `m_learned ← m_learned + w × (1 − m_learned)`. Diminishing returns are the anti-grind mechanism — do not add special-casing for repeated easy solves; the math already handles it.
- Clamp to `[0, 1]`.
- Apply the T3 cap per §4.2.
- Track `evidence_count` (weight-bearing events only — a `w=0` event is logged and feeds Balance later, but doesn't count as evidence) and `last_event_at` (all non-deleted events).

Then the thin DB layer:

```python
async def record_event(session, user_id, **fields) -> LearningEvent | None
    # Insert with ON CONFLICT DO NOTHING on (user_id, source, entity_id); returns
    # None when deduped. Then incrementally fold the single new event into
    # node_mastery. Callers MUST NOT fail their own request if this raises —
    # see §6.1.

async def recompute_node(session, user_id, node_id) -> NodeMastery
    # Full replay from learning_events. The correctness oracle.

async def recompute_user(session, user_id) -> int
    # Every node with events. Returns node count.
```

**Incremental and full must agree.** That's a property test (§8) — it's the invariant that makes Design law 2 real rather than aspirational.

### 5.1 Read-side derivations

```python
def retrievability_for(activity, now) -> float   # wraps scheduler._retrievability; 1.0 if never reviewed
def displayed_mastery(m_learned, r) -> float     # m_learned * r
def node_state(m, has_unassisted_pass) -> str
    # unexposed (m == 0) → exposed (> 0) → practicing (>= 0.35)
    # → solid (>= 0.65) → interview_ready (>= 0.85 AND has_unassisted_pass)
def confidence(evidence_count, last_event_at, distinct_tiers, now) -> str
    # 'low' | 'medium' | 'high'
```

`interview_ready` requires ≥1 unassisted T1/T2 pass on top of the threshold — a node can sit at m=0.9 and still read `solid`. That gate is the point (parent §9); don't drop it for tidiness.

Confidence thresholds are an open question in the parent doc (§16). Ship these as **named config constants** so tuning is a config edit, not a code change:

- `high` — ≥5 weight-bearing events, most recent ≤14 days, ≥2 distinct trust tiers
- `medium` — ≥2 events, most recent ≤30 days
- `low` — everything else

---

## 6. Producers

### 6.1 Producer A — review completion → `RECALL_GRADED` (T2)

In `backend/app/api/routes/reviews.py`, at the end of `complete_review` (line ~81), after the FSRS update commits, emit:

| Field | Value |
|---|---|
| `event_type` | `RECALL_GRADED` |
| `trust_tier` | `T2_verified_internal` |
| `source` | `retainhq_review` |
| `node_id` | `activity.node_id` — **skip the event entirely if NULL** (§6.3) |
| `grade` | see below |
| `outcome` | `pass` if `recalled` else `fail` |
| `duration_min` | `round(duration_ms / 60000)` when present, else 0 |
| `entity_id` | `review.id` — the dedupe key |
| `payload` | `{"rating": ..., "recalled": ..., "quality": ..., "ai_verdict": ...}` |

**Grade mapping** — the review model has both a subjective `rating` (easy/medium/hard) and an objective `recalled` bool, plus an optional `quality` 0–5. Use the objective signal first:

- `recalled is False` → `0.0`
- `recalled is True` → `1.0` if `rating == "easy"`, `0.8` if `medium`, `0.6` if `hard`
- `recalled is None` and `quality` present → `quality / 5.0`
- neither present → skip the event (nothing was actually graded)

Ignore `ai_recalled` for grading — per the existing model comment the user's own signal stays authoritative; store the AI verdict in the payload for the calibration work in parent §16.

**Failure isolation — this matters more than the feature.** Wrap the emit in `try/except`, log the exception, and let the review complete regardless. A bug in the evidence spine must never break the review loop that is RetainHQ's actual product. Add a test asserting that a raising `record_event` still returns 200 from `complete_review`.

### 6.2 Producer B — manual quick-log → `TIME_BLOCK` (T4)

`POST /api/evidence/manual` — body `{node_id, minutes, note?}`.

Writes `TIME_BLOCK` / `T4_claimed` / `source="manual"`, `w = 0.0` by both rules in §4.2. It moves nothing. That's correct and intentional: it exists to prove the schema is producer-agnostic and to seed the Balance data that phase 2 consumes. `entity_id` is NULL here (no external row), so the dedupe index — being partial — doesn't block repeated logs.

Verify `node_id` belongs to a roadmap the user can see before inserting (ownership check per `CLAUDE.md`).

The parent doc's ≤5s flow and LLM topic mapping are **phase 2**. This is the API contract only; no UI.

### 6.3 The unmapped problem — read this before implementing

Most existing `activities` rows have `node_id = NULL` (it's only set when a card is created from a lesson). So on the owner's real history, a large share of reviews produce **no event at all**.

Do not paper over this. Handle it explicitly:

- Skip the event when `node_id IS NULL` (never guess a node — parent §6 cold-start rule: never guess initial mastery).
- Count what was skipped: emit a `MetricEvent` with `event_type="evidence_unmapped"` and `payload={"reason": "no_node_id", "activity_id": ...}`. The existing `metric_events` table is the right home; no new table.
- Surface the count in `GET /api/evidence/summary` as `unmapped_events`.

This number is a phase-1 finding, not a phase-1 bug. If it's large, the phase-2 priority is topic mapping — and you'll know that from data instead of guessing. Report the actual figure when you finish.

---

## 7. API

New router `backend/app/api/routes/evidence.py`, mounted at `/api/evidence`, registered in `main.py` alongside the others. All routes require `get_current_user` and scope every query by `current_user.id`.

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/evidence/manual` | Producer B (§6.2) |
| `GET` | `/api/evidence/nodes` | Per-node mastery: `node_id`, `title`, `m_learned`, `r`, `m`, `state`, `confidence`, `evidence_count`, `last_event_at`. Optional `?roadmap_id=` filter. |
| `GET` | `/api/evidence/nodes/{node_id}/events` | The evidence log for one node — every event with its computed `w` and the running `m_learned` after it. **This is the "why is this number what it is" surface** (parent story 7, §13). Build it now; it's how you debug the weights, and it's the trust feature. |
| `GET` | `/api/evidence/summary` | `{total_events, by_tier, by_type, unmapped_events, nodes_with_evidence, weights_version}` |
| `POST` | `/api/evidence/recompute` | Full replay for the calling user. Returns nodes recomputed. Idempotent. |
| `DELETE` | `/api/evidence/events/{event_id}` | Soft-delete (sets `deleted_at`) + recompute that node. Design doc §14. |

Frontend: **one dev-only page** at `/evidence` rendering `GET /nodes` as a table with the per-node event drill-down. Plain, unstyled-to-house-standard is fine — this is an instrument, not a product surface. Do not touch Home, Review, or any existing page.

---

## 8. Tests (`backend/tests/test_evidence.py`)

The fold is pure, so most of this is fast unit testing. Follow the existing `backend/tests/conftest.py` fixtures.

**Weights and tiers**
1. Each row of the §4 table returns its documented `w`.
2. T4 event → `w == 0.0` for every event type. *(the integrity guarantee)*
3. T3 / CONTENT_CONSUMED can raise `m_learned` to 0.35 but not past it.
4. A T3 event on a node already at 0.7 leaves it at 0.7 — never drags down.
5. `PROBLEM_SOLVED` fail with `duration_min < 15` → 0.0; ≥15 → 0.03.
6. Missing `assistance` is treated as `llm_assisted`, not `none`.

**Fold**
7. Empty events → `m_learned == 0.0`, state `unexposed`.
8. Diminishing returns: 20 identical easy passes stay well below 1.0 and each successive delta shrinks.
9. `m_learned` never exceeds 1.0 or drops below 0.0 under any event sequence.
10. Event order independence *where the math implies it*: the fold is order-sensitive by design only through the T3 cap — assert the two orderings (T3-then-T1 vs T1-then-T3) both end at the T1 value.
11. State thresholds, including: m=0.9 with only `llm_assisted` passes → `solid`, **not** `interview_ready`.

**Invariant (the important one)**
12. Property test: for a randomized 50-event sequence, incremental `record_event` folding and full `recompute_node` produce identical `m_learned` (within 1e-9). This is Design law 2 in executable form.

**Integration**
13. Completing a review with a node-linked activity writes exactly one `learning_event` and updates `node_mastery`.
14. Replaying the same review completion does not double-count (dedupe index holds).
15. A review on a `node_id IS NULL` activity writes no learning event and one `evidence_unmapped` metric event.
16. `record_event` raising → `complete_review` still returns 200. *(§6.1 failure isolation)*
17. Ownership: user B gets 404/403 on user A's node events and cannot soft-delete user A's event. *(IDOR — mandatory per `CLAUDE.md`)*
18. Soft-deleting an event lowers `m_learned` to exactly the value the remaining events produce.

---

## 9. Build order

Each step leaves the repo green — run `pytest` between steps.

1. Enumerations + weights config (`evidence_weights.py`) + tests 1–6. **No DB yet.** The pure core comes first.
2. `fold_events` + read-side derivations + tests 7–11.
3. Models + migration (both tables, RLS, indexes, CHECKs). `alembic upgrade head` locally.
4. `record_event` / `recompute_node` / `recompute_user` + test 12.
5. Producer A (review hook, with failure isolation) + tests 13–16.
6. Evidence router + Producer B + tests 17–18.
7. `POST /recompute` against the owner's own history; read `GET /nodes`. **Judge the numbers.**
8. Dev-only `/evidence` page.
9. Docs: `SYSTEM-OVERVIEW.md` (§1 tables, §2 routers, changelog line) + `DECISIONS.md` entry — same commit as the code, per `CLAUDE.md`'s routing rules.

Do not push. Deploy only on an explicit "push" from the owner.

---

## 10. Decisions to record in `docs/DECISIONS.md`

One entry, dated, covering:

- **Why an event log rather than incrementing mastery in place** — enables re-running any future mastery formula (including vectorized mastery) as a computation, not a data migration. Tradeoff: more storage, a recompute path to maintain, and mastery becomes a two-step read.
- **Why `node_id` FK instead of the design doc's `topic_ids[]`** — phase-1 producers are single-node; referential integrity and query simplicity now, with a documented path to a join table.
- **Why `entity_id` dedupe from day one** — polling producers arrive in phase 2+, and silent double-counting is the failure mode most likely to destroy trust in the number (Philosophy #3).
- **Why the scheduler is deliberately absent** — it's the highest-trust-risk component (parent §10) and needs its golden-scenario suite; it should be built against a mastery model already validated on real data.

---

## 11. Definition of done

- [ ] `pytest` green, all 18 tests
- [ ] `alembic upgrade head` clean; both tables have RLS enabled
- [ ] Review completion emits events in normal use; an evidence failure cannot break a review
- [ ] `GET /api/evidence/summary` returns real counts over the owner's history, including the honest `unmapped_events` number
- [ ] `GET /api/evidence/nodes/{id}/events` explains every mastery number event-by-event
- [ ] Full recompute reproduces incremental state exactly
- [ ] `SYSTEM-OVERVIEW.md` + `DECISIONS.md` updated in the same commit
- [ ] Owner has looked at his own mastery numbers and said whether they feel honest

That last box is the real exit criterion. Everything else is machinery.

---

## 12. Report back on completion

State plainly, with numbers:

1. Events written by tier and type over the owner's real history.
2. **`unmapped_events` count** — and what share of reviews it represents.
3. Nodes reaching each state; whether any node hit `interview_ready`.
4. Anything in the weights table that produced an obviously wrong-feeling number, with the specific node and event trace.
5. Any place this spec was wrong or underspecified — that's a spec edit before the code changes, per the parent doc's Rule.
