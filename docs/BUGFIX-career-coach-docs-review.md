# Career Coach — Docs & Implementation Review Findings

**Status:** A1 fixed (code + tests + migration, not yet applied to prod) · A2–A7 still open · **Date:** 28 Jul 2026
**Scope reviewed:** `SPEC-career-coach-phase1/2/3.md`, `SPEC-career-templates-v2.md`,
`IMPLEMENTATION-career-coach-phase3.md`, `IMPLEMENTATION-career-attached-roadmaps.md`,
cross-checked line-by-line against the shipped code (`routes/career.py`, `routes/evidence.py`,
`services/planner.py`, `services/evidence.py`, `services/evidence_weights.py`,
`services/topic_mapping.py`, `models/models.py`, migrations, schemas, tests).

Two kinds of findings, kept separate: **(A) real bugs the doc review surfaced in the code**
(fix the code), and **(B) doc drift** (the code moved on deliberately; fix the doc).
Per the parent doc's rule — spec edit before code — every A-item that changes behavior
should get its spec amended in the same commit as the fix.

---

## A. Bugs found in the code while verifying the docs

### A1 · HIGH (latent — not yet firing in prod) — Detaching a shared roadmap destroys other goals' sidecars (cross-user data loss)

**Where:** `DELETE /api/career/roadmaps/{roadmap_id}` ([career.py:1052](../backend/app/api/routes/career.py))
**Doc:** `IMPLEMENTATION-career-attached-roadmaps.md` §3.1/§4 — the [DECISION] never considers
a *second* goal or user attaching the same shared roadmap.

`node_meta` is unique per `node_id` with **no user or goal scoping** (`uq_node_meta_node`),
but the attach feature treats it as per-attachment state. Catalog roadmaps
(`roadmaps.user_id IS NULL`) are shared by every user. Consequences, in order of severity:

1. **Detach deletes globally.** The detach route deletes `node_meta` by
   `stable_key LIKE 'attached.<slug>.%'` with no goal/user filter. If users A and B both
   attach the catalog DSA roadmap, A's detach deletes the sidecars **B's plan depends on**.
   B's join row survives, but `/today` INNER JOINs `node_meta`, so B's attached nodes
   silently vanish from their plan with no error anywhere.

   **Severity corrected 2026-07-28 (prod queried via Supabase MCP):** this section originally
   read "The app is live — this is a real multi-user correctness bug, not a theoretical one."
   The defect is real, but "live" was wrong. Prod holds **1 attachment, 1 distinct user, and
   0 roadmaps attached by more than one user** — no cross-user destruction has happened, and
   none can until a second user attaches the same catalog roadmap. Correct framing: **real,
   currently latent, fires silently and unrecoverably the first time two users overlap.**
   Priority stays HIGH — the trigger is an ordinary user action, the failure is silent, and
   the destroyed rows are not reconstructible from the surviving join row — but this is not
   an active incident and must not be described as one. (148 `attached.%` sidecar rows do
   already exist in prod; that's the cleanup scope, not damage.)
2. **Second attacher inherits the first attacher's labels.** B's attach finds every node in
   `already_meta`, creates nothing (`nodes_added=0`), and B's balance strip buckets those
   nodes under **A's** chosen `subject` and priority — which can differ from the `subject`
   stored on B's own `career_goal_roadmaps` row. The two sources of truth disagree.
3. Same collision applies to one user across goals: attach on goal 1, archive, new goal,
   attach again → `nodes_added=0` and a later detach on either goal strips the other.

**Direction to decide (open question Q1):** either (a) scope sidecars per attachment —
add `user_id` (or `goal_id`) to `node_meta` and drop the global uniqueness for attached rows,
or (b) stop persisting attached-node meta entirely and have `/today` synthesize
`PlanNode`s for attached roadmaps from the `career_goal_roadmaps` row
(subject/priority/flat-60 effort are all already on it — the sidecars carry no per-node
information for attached roadmaps anyway). Option (b) needs no migration and removes the
shared-state problem at the root; template-tree sidecars stay as they are.

### A2 · MEDIUM — `AttachRoadmapIn.default_priority` is unvalidated → 500 instead of 422

**Where:** [schemas/career.py:175](../backend/app/schemas/career.py) + [career.py:986](../backend/app/api/routes/career.py)

`default_priority: Optional[int]` has no `ge`/`le`. The route does
`body.default_priority or 3` and writes it into both `CareerGoalRoadmap` and `NodeMeta`.
`node_meta` has a DB CHECK (1–5), so `default_priority=99` surfaces as an unhandled
`IntegrityError` → 500 mid-commit rather than a 422. Also `default_priority=0` is silently
coerced to 3 by the `or`. Fix: `Field(default=None, ge=1, le=5)` on the schema.

### A3 · MEDIUM — Plan is nondeterministic when several activities map to one node

**Where:** [career.py:687-694](../backend/app/api/routes/career.py) (`activities_by_node`)
**Doc:** `SPEC-career-coach-phase1.md` §2.2 assumes one linked Activity per node;
`SPEC-career-coach-phase3.md` §3.1 rule 7 promises "same inputs → same plan".

Many activities can share a `node_id` (several cards created from one lesson; the
topic-mapping backfill assigns whole activities to nodes). The dict comprehension keeps
whichever row the DB returns last — there is no `ORDER BY` — so `retrievability_for` uses an
**arbitrary** activity's `stability`/`last_reviewed_at`. `m` therefore varies between
identical calls, which can reorder study items. Determinism holds in the pure core but is
violated at the route. Decide the intended semantics (open question Q3): most-recently
reviewed? Minimum r (conservative)? Then order the query accordingly and amend phase-1 §5.1.

### A4 · LOW — Attach cap and duplicate check are read-then-write

**Where:** [career.py:976-983](../backend/app/api/routes/career.py)

Concurrent attaches can exceed `MAX_ATTACHED_ROADMAPS` (both requests read `len(existing)=4`),
and a duplicate under race hits `uq_goal_roadmap` as an unhandled `IntegrityError` → 500
instead of the documented 409. Low priority solo-scale, but the 409 path should catch
`IntegrityError` the way `record_event` does.

### A5 · LOW — Attached catalog nodes can be planned but not sprinted, edited, or re-labeled

**Where:** `_get_owned_node_and_meta` ([career.py:495](../backend/app/api/routes/career.py))
requires `Roadmap.user_id == user_id`, so for attached **catalog** nodes (owner NULL):

- `POST /api/career/sprint` → 404. The plan recommends a node the user cannot pin.
- `PATCH /api/career/nodes/{id}` → 404. The attach docstring says "the user can refine both
  afterwards", but there is **no route at all** to edit an attachment's `subject`/`default_priority`
  after the fact (and no UI). Either add `PATCH /api/career/roadmaps/{roadmap_id}` or delete
  the promise from the docstring.

(Blocking `DELETE /nodes/{id}` on catalog nodes is correct — keep that.)

### A6 · LOW — Failed tree generation still consumes the daily quota

**Where:** [career.py:104-105](../backend/app/api/routes/career.py)

`_check_and_bump_daily_limit` bumps before `generate_career_tree` runs, so a
`CareerTreeError` 400 (bad role_key etc.) burns one of the 3 daily generations. Bump after
success, or don't count failures.

### A7 · LOW — Re-committing a tree on the same goal orphans the old roadmap

**Where:** `POST /tree/commit` ([career.py:375](../backend/app/api/routes/career.py))
**Doc:** phase-2 §7 says "on goal switch, the old roadmap is archived, not dropped" — but the
*same-goal recommit* path (generate again → commit again without a new goal) just overwrites
`goal.roadmap_id`. The old roadmap + its `node_meta` rows linger unreferenced, and mastery
built on the old tree's node ids silently drops out of `/today`. Decide: block recommit when
`roadmap_id` is already set (force a new goal), or clean up/archive the orphan explicitly.

---

## B. Doc drift — code is (deliberately) ahead; fix the docs

### B1 — Phase-2 §5 topic-mapping thresholds and mechanism are stale

- Doc: "≥0.75 auto-maps; 0.55–0.75 triage; <0.55 unmapped". Code
  ([topic_mapping.py:28-29](../backend/app/services/topic_mapping.py)): `AUTO_MAP_THRESHOLD=0.75`,
  `TRIAGE_THRESHOLD=0.65` — the 0.55 band no longer exists. The stale 0.55 also survives in a
  comment at [schemas/career.py:95](../backend/app/schemas/career.py).
- Doc: embeddings go in "`node_meta`-adjacent storage or a `payload` column … a small
  in-process cosine match is adequate". Shipped: a real `embedding` JSONB **column on
  `node_meta`** (migration `fd9b3eaf3c37`) filled via Gemini `embed_batch` at commit.
- Doc: "≥0.75 **auto-maps**" and "`payload.mapping_confidence` (parent §7 requires this
  field)". Shipped: nothing auto-maps — Tier 2 only produces *suggestions* in the triage UI
  (`suggest_node` → `tier: 'auto' | 'triage'`), assignment is always a manual action, and no
  event carries `mapping_confidence`. If auto-map is still intended, that's an unbuilt
  feature, not drift — decide which (open question Q2).

### B2 — Phase-2 §6 unmapped API is event-based in the doc, activity-based in code

Doc table: `POST /api/career/unmapped/{event_id}/assign` → "insert corrected event →
recompute". Shipped: `POST /api/career/unmapped/{activity_id}/assign` — sets
`Activity.node_id`, then retroactively writes RECALL_GRADED events for **all** of that
activity's completed reviews (`backfill_activity`). The shipped model is strictly better
(one triage action fixes the whole history); the doc should describe it.

### B3 — Phase-3 §3.1 rule 6 "budget fill" doesn't match what shipped

Spec: "Study items **fill the remaining share of `daily_minutes`** after reviews … Minimum 1
study item even on tiny budgets." Shipped (per IMPLEMENTATION §3 step 9, faithfully):
`daily_minutes` only gates the all-reviews `overflow` case; once past it, the plan always
takes up to `MAX_STUDY_ITEMS=5` frontier nodes **regardless of remaining minutes** — a
45-minute day and a 240-minute day get the same five study items, only `est_share` differs.
The "minimum 1 on tiny budgets" branch is unreachable as written. Either amend spec §3.1
rule 6 to say the budget proportions shares but never the item count, or treat the shipped
behavior as the bug and make item count scale with `study_budget` (open question Q4).

### B4 — Phase-1 §4.2/§5 fold algorithm was superseded without a spec edit

Spec describes a **single running total** with an in-fold clamp
(`if capped and after > 0.35: after = max(before, 0.35)`), which is order-sensitive (its own
test 10 says so). Shipped ([evidence.py:45](../backend/app/services/evidence.py)): **two
independent streams** (capped vs uncapped) combined with `max()` — commutative by
construction, a genuinely better design, well-documented in the code — but phase-1's own
§12.5 rule ("spec edit before code") was never honored. Amend §4.2/§5 to describe the
two-stream fold.

### B5 — Phase-1 §3 enumerations are stale

`SOURCES` gained `companion_browser` (migration `d47fe16300ee`); the spec still lists seven
sources. Also the evidence router now carries `/leetcode/solve` and `/leetcode/backfill`
(from `SPEC-leetcode-retention.md`) — worth one line in phase-1's §7 table noting the router
grew beyond the phase-1 surface, since phase-1 declared LeetCode "explicitly deferred".

### B6 — Attached-roadmaps doc §4 contradicts the shipped attach preconditions and body

- Doc: "Active goal **with a committed tree**, else 404 (reuse `_get_active_goal_with_tree`)".
  Shipped: deliberately weakened to `_get_active_goal` (tree not required) so the picker works
  during onboarding — the code documents why, and
  `test_can_attach_during_onboarding_before_the_tree_is_committed` codifies it. Doc §4 step 1
  is now wrong.
- Doc: body `{roadmap_id, subject, default_priority}` and §6 "ask for the subject … then POST".
  Shipped: one-click attach — only `roadmap_id` required; subject defaults to slug/title,
  priority to 3.

### B7 — Phase-2 §2.2 `node_meta` docstring/claims no longer hold

"Rows exist only for career-tree nodes" — false since attached roadmaps (rows now exist for
catalog nodes too), which is exactly what makes A1 possible. The model docstring in
`models.py` says the same. Update both when A1 is resolved.

---

## Open questions for the owner (answers unblock the A-fixes)

- **Q1 (drives A1):** For attached-roadmap planning metadata — migrate `node_meta` to
  per-user scoping, or drop persisted sidecars for attachments and synthesize plan nodes
  from the `career_goal_roadmaps` row at read time? (b) is smaller and removes the shared
  state entirely; (a) keeps one uniform node-meta read path.
- **Q2 (drives B1):** Is Tier-2 **auto-mapping** (evidence written automatically at ≥0.75
  with `payload.mapping_confidence`) still a goal, or is suggest-and-confirm the intended
  final behavior? If the latter, the phase-2 spec and parent-§7 field requirement should be
  formally amended.
- **Q3 (drives A3):** When several activities share a node, which one defines
  retrievability — most recently reviewed, or the minimum r (most conservative)?
- **Q4 (drives B3):** Should `daily_minutes` bound the *number* of study items (spec
  reading), or only their proportions (shipped reading)? Whichever wins, one of the two
  documents needs the edit.

---

# Answers (2026-07-28, after re-verifying every A-finding against the code)

**Review accuracy: all seven A-findings confirmed against the source, none overstated.**
Spot-checked the load-bearing claims rather than taking them on trust — `node_meta` really
does carry `UniqueConstraint("node_id")` with no user column
([models.py:412](../backend/app/models/models.py)); `_attached_key` really is
`f"attached.{roadmap.slug or roadmap.id}"` with no user component
([career.py:836](../backend/app/api/routes/career.py)); the detach really does filter on
that key alone; and [career.py:663](../backend/app/api/routes/career.py) really is a plain
`.join(...)` — SQLAlchemy's INNER JOIN — which is what makes A1 fail *silently* rather than
loudly.

**Correction to this line as first written (2026-07-28, after querying prod via Supabase MCP):**
I originally echoed the review's "a genuine live multi-user bug, not a theoretical one." The
code defect is real and the severity ranking stands, but "live" was overstated. Prod holds
**1 attachment, 1 distinct user, and 0 roadmaps attached by more than one user** — so no
cross-user destruction has occurred, and none can until a second user attaches the same
catalog roadmap. A1 is **real but currently latent**. That doesn't lower its fix priority
(it fires silently and unrecoverably the first time two users overlap, which is a normal
thing for users to do), but it does mean this is not an active incident, and it should not
be described as one. Related prod fact for the fix: **148 `attached.%` sidecar rows already
exist**, which is the concrete scope of the cleanup migration below.

## Q1 → **Option (b): stop persisting sidecars for attached roadmaps.** High confidence.

The review reached the right answer; here is the evidence that makes it decisive rather than
merely smaller. Attached sidecars carry **literally zero per-node information**:

```python
NodeMeta(node_id=n.id, stable_key=f"{prefix}.{n.id}", subject=subject,
         priority=priority, est_effort_min=_ATTACHED_EFFORT_MIN)
```

`subject` and `priority` are the same for every node in the attachment (both come straight
off the `career_goal_roadmaps` row), `est_effort_min` is a flat constant, `stable_key` is
synthetic, and **`embedding` is never set** — so it is NULL on every attached row.

That last point kills the strongest argument for option (a). One could reasonably object
that (a) preserves attached nodes as embedding targets for topic mapping. It doesn't, twice
over: their embeddings are NULL (`topic_mapping` scores a NULL-embedding node 0 and skips
it — [topic_mapping.py:97](../backend/app/services/topic_mapping.py)), *and*
`candidate_nodes_for_user` scopes to `personal_ids + [goal.roadmap_id]`, which never
includes an attached **catalog** roadmap in the first place. So option (b) gives up nothing
that currently works.

Option (a) also has a cost the review understates: it would leave `node_meta` with two
different uniqueness semantics depending on row provenance (global for template rows,
per-user for attached rows), and every read path would need to know which kind it is looking
at. That is a worse invariant than the one being fixed.

**Ship (b).** No migration; delete the sidecar-creation loop in attach and the sidecar
`DELETE` in detach; `/today` synthesizes `PlanNode`s for attached roadmaps from the
`career_goal_roadmaps` row. It resolves A1 and B7 together, and it makes the
`career_goal_roadmaps` row the single source of truth for an attachment's subject/priority —
which also dissolves finding A1's consequence #2 (the two sources can no longer disagree,
because there is only one).

**Two things to get right in that change**, neither of which the review flags:
1. `/today`'s node query must stop being a single INNER JOIN on `node_meta`. Template nodes
   still come from `node_meta`; attached nodes now come from `career_goal_roadmaps ⋈
   roadmap_nodes`. Getting this wrong reproduces A1's exact silent-disappearance symptom.
2. **A cleanup migration is still needed even though the schema does not change** — every
   `attached.%` row already written to prod is now orphaned state that nothing reads and
   detach no longer removes. Delete them (`stable_key LIKE 'attached.%' AND user_edited =
   false`) in the same commit, or they linger forever and keep poisoning `already_meta` for
   anyone who re-attaches.

## Q2 → **Suggest-and-confirm is the correct final behavior. Amend the spec; do not build auto-map.**

This is the same call the codebase has now made three times, and it should be made
consistently: D-046 kept manual LeetCode marks out of the evidence spine entirely; D-047 held
chat-derived topics at weight 0. Auto-mapping would break that pattern in the most damaging
possible place, because of what it actually writes — via `backfill_activity` (B2), assigning
a node retroactively emits `RECALL_GRADED` events for every completed review of that
activity, and `RECALL_GRADED_WEIGHT = 0.20` is **real, uncapped, T2-tier weight**. This is
not the companion's weight-0 `TIME_BLOCK` path; it moves mastery directly.

The asymmetry decides it. A missed suggestion costs one click. A wrong auto-map silently
writes weighted evidence to the wrong node, corrupts the exact number the product's entire
thesis rests on, and is close to undetectable after the fact — cosine ≥0.75 on a short title
string is a weak basis for that. Formally amend phase-2 §5 and the parent §7
`mapping_confidence` requirement to describe suggest-and-confirm as the intended design, not
a way-station.

## Q3 → **Minimum r (most conservative).** The codebase has already answered this.

[evidence_weights.py:35](../backend/app/services/evidence_weights.py) states the governing
principle in its own words: *"Conservative defaults for missing fields — mastery may
understate, it must never overstate."* Most-recently-reviewed is the maximally optimistic
choice: review one card of a five-card node today and the whole node reads fresh while four
cards rot. That is precisely overstating.

Minimum r also gives the behavior a spaced-repetition product should want — a node surfaces
for study when *any* of its material has decayed, which is the thing you actually want to be
told. Mean is defensible but has no principle behind it in this repo and is harder to reason
about; minimum has both.

Note this is a real ordering change, not a tie-break: it lowers `m` for multi-activity nodes,
which will move them up the study list. That is the intended effect, but it means A3's fix
should land with a golden-suite snapshot update, not silently. Amend phase-1 §5.1 to state
the rule, and add `ORDER BY` to make the query deterministic regardless.

## Q4 → **Budget should bound the count, with a floor. Lowest-stakes of the four; defer it.**

The shipped behavior is defensible as a *menu* (five ranked options, user picks, `est_share`
tells the truth about time). But five study items against a 15-minute remaining budget is a
plan the day cannot keep, and the design bible's research pass is consistent on this theme —
bounded queues, honest framing, never a backlog that reads as debt.

Recommendation: `n_items = clamp(study_budget // 15, 2, MAX_STUDY_ITEMS)` — scales with the
budget, keeps at least two so a single unappealing suggestion doesn't end the session, and
makes the spec's unreachable "minimum 1" branch reachable and meaningful. Then amend spec
§3.1 rule 6 to describe exactly that.

**But this is genuinely a product call, not a correctness one** — unlike Q1–Q3 it has no
right answer derivable from the code, and nothing is broken today. It is fine to keep the
shipped behavior and amend the *spec* instead; what is not fine is leaving the two documents
contradicting each other. Either edit closes it.

## Suggested fix order

1. ~~**A1**~~ **FIXED 2026-07-28** — per Q1 option (b). Also resolved B7 and A1's consequence #2.
   See §D below.
2. **A2** (one-line schema fix) and **A4** (catch `IntegrityError` → 409).
3. **A3** per Q3 (with golden-suite snapshot update); **A5** (add attachment PATCH or retract
   the promise); **A6**, **A7**.
4. Doc-only pass in one commit: B1–B6 + the phase-1/2/3 spec amendments Q2/Q3/Q4 require.

---

# D. A1 fix, shipped (2026-07-28)

**What changed.** No per-node `node_meta` sidecar is written or read for attached roadmaps
anymore. `CareerGoalRoadmap` (subject/default_priority) is now the sole source of truth for
an attachment, applied uniformly to every node in that roadmap:

- **Attach** (`POST /roadmaps/`) — deleted the sidecar-creation loop entirely. Only writes the
  `CareerGoalRoadmap` link.
- **Detach** (`DELETE /roadmaps/{id}`) — deleted the sidecar `DELETE` entirely (and the now-dead
  `_attached_key` helper). Only deletes the caller's own `CareerGoalRoadmap` link, so it can
  never touch a row another user's plan depends on — the bug is structurally impossible now,
  not just less likely.
- **`GET /today`** ([career.py](../backend/app/api/routes/career.py)) — the node query split in
  two: template-tree nodes keep the real `INNER JOIN node_meta` (unchanged); attached nodes
  are fetched with no `node_meta` join at all, and `PlanNode.subject`/`priority`/`est_effort_min`
  are synthesized from the node's `CareerGoalRoadmap` link (`_ATTACHED_EFFORT_MIN`, same flat
  constant as before). The balance-window query had the same problem one level down — it
  grouped by `NodeMeta.subject` via a join, which would have silently dropped every
  attached-roadmap minute now that those nodes have no sidecar to join against. Rewritten to
  fetch `duration_min` per `node_id` and aggregate by subject in Python, using a `node_id ->
  subject` map built from both sources (template `node_meta` rows + attached links) — this is
  what keeps `test_attached_roadmap_minutes_reach_the_balance_window` passing.
- **Migration `a3f8c1d92b47`** (`drop_attached_roadmap_node_meta`, revises `d5f1a7c3e284`) —
  data-only, deletes existing `attached.%` sidecar rows (`user_edited=False` only). **148 such
  rows exist in prod** (measured via Supabase MCP 2026-07-28) — **written but not yet applied**,
  per this repo's convention of never hand-applying schema/data migrations to prod without an
  explicit go-ahead.
- **Tests** (`tests/test_career_roadmaps.py`) — rewrote the two tests whose whole premise was
  sidecar mechanics (`test_attach_inbuilt_roadmap_creates_sidecars_and_reaches_the_plan` →
  `..._writes_no_sidecars_and_reaches_the_plan`; the user-edited-sidecar test, which no longer
  has a sidecar to edit, replaced outright). Added
  `test_two_users_attaching_the_same_catalog_roadmap_do_not_collide` — the actual A1 regression
  test: two users attach the same catalog roadmap with different subjects, A detaches, and B's
  plan and `CareerGoalRoadmap` link are asserted unaffected. All 12 pre-existing tests in the
  file still pass unmodified. 378/378 backend suite green.

**What this does NOT change:** `NodeMeta` itself, its schema, its use for template-tree
sidecars, or `topic_mapping.py` (already excluded attached roadmaps before this fix, per the
BACKLOG finding below — unaffected either way, since attached nodes never had a usable
embedding regardless of whether a sidecar row existed).

**Before applying `a3f8c1d92b47` to prod:** deploy the code first (so nothing re-reads the
rows the migration is about to delete), then apply. Order matters here — applying the
migration before the code deploy would only remove dead rows the code isn't reading yet
anyway, so the *cost* of getting the order wrong is low, but do it in the stated order regardless.

## Found while answering — not in the original review

**`candidate_nodes_for_user` excludes attached roadmaps entirely.** It scopes to
`personal_ids + [goal.roadmap_id]`
([topic_mapping.py:114-132](../backend/app/services/topic_mapping.py)); an attached **catalog**
roadmap is neither. So a user who attaches the catalog DSA roadmap can have it planned by
`/today` but it can never be a topic-mapping or companion-classification target — including
for the browser extension's session classification. This is a coherence gap between "what the
planner plans from" and "what evidence can map to", it is independent of A1, and option (b)
neither causes nor fixes it. Worth its own decision: either add attached roadmap ids to that
query (and backfill embeddings for those nodes, which are NULL today), or accept and document
that attached roadmaps are plan-only. Logged to `BACKLOG.md`.

---

# C. Second pass (2026-07-28): SYSTEM-OVERVIEW.md and DECISIONS.md

Extended the audit to the two living docs, per the owner. These are C-items, not A/B — they're
all doc-staleness in the *living* docs, which matters more than staleness in the frozen specs
because CLAUDE.md names SYSTEM-OVERVIEW "the single living source of truth" and its routing
rule requires §-body updates **in the same commit** as the change. Several below are cases
where the changelog got its line but the body sections it points at were never touched.

### C1 — Attached roadmaps updated the changelog but not §1/§2 (routing-rule violation)

The 2026-07-26 D-042 changelog line exists, but:

- **§1 API surface** still says the career router has "**15 routes** after phase 3" and lists
  none of the four attach routes (`GET/POST /api/career/roadmaps/`, `GET /roadmaps/available`,
  `DELETE /roadmaps/{id}`). Actual: 19.
- **§2 table list omits `career_goal_roadmaps` entirely**, and the heading count ("26 tables")
  predates it. The `node_meta` §2 entry also still reads as if rows exist only for career-tree
  nodes (same claim as B7 — false since attach).
- When the A1/Q1(b) fix lands, both D-042 and the changelog line will describe a reverted
  design — D-042 needs a superseding DECISIONS entry at that point, not an edit in place.

### C2 — Migration-chain and head claims are stale and mutually inconsistent

Within the same file: §1 says "**32 migrations; head `37714df921df`**" while §2 says
"**Migration chain (34)** … `b7b1755c4d22` (head; applied to prod 2026-07-26)". Both are
wrong: the versions dir now holds the chain through `c3e8a1f47b92` (career_goal_roadmaps) →
`e2c4a8b1f960` (problem_attempts) → `d5f1a7c3e284` (guard_problem_attempts_truncate), and
`fd9b3eaf3c37` (add_embedding_to_node_meta) + `d47fe16300ee` (add_companion_browser_source)
appear in no chain description at all. The §2 "Prod state (checked 2026-07-21)" paragraph
still asserts prod is at `37714df921df`, which §2's own chain line contradicts. Per CLAUDE.md,
the prod-state claim must be re-verified via the read-only Supabase MCP when this section is
rewritten — not assumed.

### C3 — `topic_mapping` §1 entry describes the dead Jaccard implementation

§1 services still says: "Jaccard word-overlap match … `TRIAGE_THRESHOLD=0.55` (placeholder
for a real embedding call — pgvector confirmed NOT installed, not worth adding for ≤90
vectors)". Shipped since: real Gemini embeddings (`services/embeddings.py` — **not listed in
§1 at all**), `TRIAGE_THRESHOLD=0.65`, `node_meta.embedding` column, and embedding
pre-compute inside `commit_tree`. The §2 `node_meta` entry doesn't mention `embedding`
either. Same root fact as B1, but this is the living doc so it's the copy that actually
misleads a future session.

### C4 — `CAREER_TREE_MODEL` value stale

§1 (and the D-037 changelog line, which was correct when written) says
`gemini-3.5-flash`; `config.py` now defaults to `gemini-3.6-flash`. One-word fix, but it's a
prod-behavior claim in the source-of-truth doc.

### C5 — §1 `tests/` row is two eras behind

Lists the suite as of 2026-07-19 ("171/171 passing") and omits every file since:
`test_planner.py`, `test_career_today.py`, `test_career_roadmaps.py`, `test_problems.py`,
`test_leetcode_evidence.py`, `test_llm_classifier.py`, `test_metrics.py`,
`api/routes/test_companion.py`, plus the `goldens/plan_g*.json` snapshots. The changelog's
newest entry says 378 backend tests. Also §1's models row says "**22 tables**" vs §2's "26"
vs actual 27 — three counts, zero agreeing.

### C6 — DECISIONS.md numbering gap: D-045 was never written

`IMPLEMENTATION-companion-firefox.md` §build-order instructed "DECISIONS (`D-045` — two
targets, one source tree)", but the entry landed as **D-044**; the sequence jumps D-044 →
D-046. Nothing is lost — but leave a one-line tombstone (or renumber nothing and note the gap)
so a future entry doesn't reuse D-045 and make cross-references ambiguous.

### C-fix suggestion

All of C1–C5 is one SYSTEM-OVERVIEW editing pass + one changelog line ("doc-sync pass, no
code change"), with the §2 prod-state paragraph re-verified against Supabase MCP at edit
time. Do it *before* the A-fixes land, so the A-fix commits diff against a truthful baseline.
