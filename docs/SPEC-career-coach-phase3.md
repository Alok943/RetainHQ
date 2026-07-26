# Career Coach — Phase 3 Implementation Spec: Scheduler & Today Screen

**Status:** Draft for owner review · **Owner:** Alok · **Date:** 20 Jul 2026
**Parent doc:** `retainhq-career-coach-design-doc.md` (v1.2) — owns *what and why*.
**Predecessors:** `SPEC-career-coach-phase1.md` (evidence spine, shipped) · `SPEC-career-coach-phase2.md` (goal/tree/mapping, shipped) · `SPEC-career-templates-v2.md` (template quality, shipped).
**Maps to parent:** the scheduler + Balance half of Phase 1 (§10) and the Today screen.

---

## 0. Why the golden scenarios come before the code

The parent doc calls the scheduler the **highest-trust-risk component** (§10): a mastery number that's slightly off is a display bug; a schedule that's off tells the user to spend their day on the wrong thing. The evidence spine and tree exist precisely so this component could be built last, against validated inputs.

The discipline this spec enforces: **the scheduler core is one pure function, and every behavioral promise it makes is a golden scenario written before the function is** (§5). If a scenario can't be written down as inputs → expected properties, the behavior is underspecified and must not ship. This mirrors phase 1's fold: pure core, DB shell, property tests as the contract.

**Two hard preconditions before starting implementation (checked in §9 step 0):**
1. **Dogfood data exists — a one-time, owner-only calibration gate, NOT a per-user requirement.** New users get a plan on day zero (that's G1: diagnostic + template priorities + prerequisite structure produce a plan from empty mastery, and it sharpens as evidence accrues). What needs two weeks of the owner's real evidence is *tuning the constants* (§7) — urgency curve, balance threshold — because tuning them against a nearly-empty `node_mastery` means shipping numbers nobody has ever felt. This gates the calibration step, not the feature and not any user.
2. **Effort is relative, never absolute** (BACKLOG, 2026-07-20): `est_effort_min` is ~3-5× optimistic. The scheduler may use it to *proportion* a session, never to promise wall-clock time or completion dates.

### Explicitly out of scope
Weekly report · coach agent (phase 4) · confidence probes · LeetCode/GitHub sync · companion apps · LLM calls of any kind (this scheduler is fully deterministic) · template-upgrade UX · goal switch/restore UX. Parent scope rule applies: additions require a removal.

---

## 1. What the scheduler is — and the one thing it must never do

**It answers one question: "given ~N minutes today, what should I touch, in what order?"** It produces a small ordered plan mixing three item kinds:

| Kind | Source | Who decides timing |
|---|---|---|
| `review` | The existing FSRS due queue (`GET /api/reviews/due`, cap 10) | **FSRS, untouched** |
| `study` | Frontier nodes of the career tree (prereqs met, low mastery) | This scheduler |
| `balance` | A neglected high-priority subject's best frontier node | This scheduler |

**The law: the scheduler never overrides FSRS.** Review timing is memory-physics; the scheduler only decides *where reviews sit in today's ordering* and *what new material fills the rest*. It never reschedules, drops, or reorders reviews relative to each other (the due queue's oldest-first order is preserved). This is the phase-3 equivalent of phase 1's "T4 never moves mastery" — non-negotiable, own test.

**Everything is derived.** No `day_plans` table. The plan is computed on read from existing state (Design law 2 extended: if the plan can't be recomputed from inputs, it can't be trusted). Accepted/skipped telemetry goes to `metric_events` (§6), which phase 4's coach learns from.

---

## 2. Inputs (all already exist)

| Input | Source | Notes |
|---|---|---|
| Per-node mastery `m = m_learned × r` | `node_mastery` + `retrievability_for` | Phase 1 read-side, reuse as-is |
| Node priority / subject / relative effort | `node_meta` | v2 templates |
| Prerequisite edges | `roadmap_node_prerequisites` | |
| Deadline | `career_goals.target_date` | NULL = open-ended |
| Sprint override | `career_goals.sprint_node_id` / `sprint_until` | **First consumer** — stored since phase 2 |
| Actual time spent per subject | `learning_events.duration_min` (incl. w=0 TIME_BLOCK rows) | Producer B's purpose realized |
| Due reviews | existing reviews query | |
| Daily budget | **new** `career_goals.daily_minutes` (§6) | default 60 |

---

## 3. The plan function (pure core)

```python
# services/planner.py — NO DB access, NO datetime.now() (clock passed in)
def build_plan(inputs: PlanInputs) -> DayPlan
```

`PlanInputs` is a plain dataclass: nodes (id, subject, priority, effort, m, state, prereq_ids), due_reviews (ordered), subject_time_shares, sprint, target_date, daily_minutes, now. `DayPlan` = ordered list of `PlanItem(kind, node_id | review_id, reason: str, est_share: float)` + `balance: dict[subject, float]`. Every item carries a **human-readable `reason`** ("due review", "unlocks 4 nodes in DSA", "OS is 3 weeks neglected") — the trust surface, same philosophy as the evidence log.

### 3.1 Selection rules

1. **Reviews first.** All due reviews (≤10, FSRS-capped) enter the plan before any study item, oldest-first. Rationale: retention is the product's moat; new material never crowds out maintenance.
2. **Frontier = available nodes.** A node is *available* iff every prerequisite has `m_learned ≥ PREREQ_UNLOCK_THRESHOLD` (config, initial 0.35 — matches `practicing`). Deleted/absent mastery rows count as 0.
3. **Study score** (deterministic, all factors config constants):
   `score = priority × (1 − m) × urgency × unlock_weight`
   - `urgency`: 1.0 open-ended; scales up to `URGENCY_MAX` (2.0) as `target_date` nears, per remaining-fraction of the goal's timeline. Never scales *down* below 1.
   - `unlock_weight`: `1 + UNLOCK_BONUS × dependents_count` (0.05/dependent, capped ×1.5) — prerequisite-heavy nodes surface earlier.
4. **Balance correction** (parent's `p_s`/`a_s`): per subject, `p_s` = its share of summed node priorities; `a_s` = its share of `duration_min` over the trailing `BALANCE_WINDOW_DAYS` (21). `balance_s = a_s − p_s`. **Evidence floor** (added during implementation, 2026-07-26 — see `IMPLEMENTATION-career-coach-phase3.md` §3.3 step 8a): if total logged minutes across that window is below `BALANCE_MIN_WINDOW_MINUTES` (120), emit no balance item at all and report `balance={}` — with no evidence, `a_s=0` for every subject and the *largest* subject in the tree always trips the threshold on zero data, which is exactly the false-positive this floor exists to block. Otherwise: excluding the active sprint node's subject from consideration first (not just checking it after — see rule 5), find the most-negative remaining subject; if it's below `BALANCE_FLAG_THRESHOLD` (−0.15), its best frontier node is **promoted into slot 1 of the study items** with kind `balance` and the reason naming the neglect. At most one balance item per plan — a nudge, not a takeover.
5. **Sprint mode** (parent A3): while `now.date() ≤ sprint_until`, the sprint node (if not mastered) is pinned as the first study item. Its own subject is excluded from balance-nudge consideration entirely (not merely disqualified after being found "most neglected" — a different, non-sprint subject that's also below threshold must still be flaggable). Expired sprints are ignored (and cleared lazily by the route).
6. **Budget fill.** Study items fill the remaining share of `daily_minutes` after reviews (reviews costed at `REVIEW_COST_MIN` = 4 min each), by **relative** effort: `est_share = node_effort / Σ selected efforts`. Minimum 1 study item even on tiny budgets; hard cap `MAX_STUDY_ITEMS` (5) — a plan longer than that is a backlog, not a plan.
7. **Determinism.** Same inputs → same plan. Ties break by (priority desc, template order via `order_index`). No randomness anywhere.

### 3.2 Degenerate cases (each is a golden scenario in §5)

Empty mastery + no reviews → pure onboarding plan (roots of the tree). All nodes mastered → reviews only + honest "tree complete" flag. No committed tree → 404 at the route (plan function never sees it). Zero due reviews → all-study plan. `daily_minutes` smaller than review load → reviews only, `overflow: true` on the plan.

---

## 4. API + Today screen

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/career/today` | Assemble `PlanInputs` (one query pass), call `build_plan`, return the plan. Auth + active-goal-with-tree required (404 otherwise). Also lazily clears an expired sprint. |
| `PATCH` | `/api/career/goals/active` | Set `daily_minutes` (30–240 clamp). New route; also the natural home for future goal edits. |
| `POST` | `/api/career/today/feedback` | `{item_ref, action: 'done'|'skipped'}` → `metric_events` (`plan_item_feedback`). No plan mutation — the next `GET` recomputes. |

**Frontend:** a "Today" card at the top of `CareerTree.jsx` (`/coach`) — the plan as an ordered checklist: reviews link to `/reviews`, study/balance items deep-link to the node (and its lesson when `topic_mapping` finds one). Each item shows its `reason` line. A small balance strip (per-subject over/under bar) sits under the list. Reuse existing color classes (dark mode free). **No new page** — Today is a section, not a destination; the tree remains the home surface.

---

## 5. Golden-scenario suite (`backend/tests/test_planner.py`) — written FIRST

Table-driven: each scenario = frozen `PlanInputs` fixture + property assertions, plus **exact-output snapshot goldens** for G1/G4/G7 (any diff = deliberate decision + snapshot update in the same commit, mirroring the DSA golden convention).

| # | Scenario | Must hold |
|---|---|---|
| G1 | Cold start: empty mastery, no reviews, 60 min | Only root nodes (no unmet prereqs); ≤5 items; every item has a reason |
| G2 | Overdue pile: 10 due reviews, 30 min budget | All 10 reviews, zero study items, `overflow: true`; review order untouched |
| G3 | Deadline crunch: target_date in 14 days vs same inputs open-ended | Crunch plan's study set ⊇ higher-priority nodes; urgency never *removes* reviews |
| G4 | Neglected subject: OS at `a_s − p_s < −0.15`, frontier available, evidence floor cleared | Exactly one `balance` item, slot 1 of study, reason names OS |
| G4b | Same shares as G4, but total logged minutes below `BALANCE_MIN_WINDOW_MINUTES` | No balance item; `balance={}` — thin evidence must not produce a confident nudge |
| G5 | Sprint mode active on a DSA node, DSA also neglected | Sprint node first study item; NO balance flag for DSA; other subjects still flaggable |
| G6 | Sprint expired yesterday | Plan identical to no-sprint plan |
| G7 | Mid-journey: mixed mastery, 3 due reviews, 90 min | Reviews before study; every study node's prereqs ≥ threshold; `Σ est_share ≈ 1` |
| G8 | Everything mastered (`m_learned ≥ 0.85` all nodes) | Reviews only + `tree_complete: true`; no study items invented |
| G9 | Prereq integrity under adversarial mastery (random 200-node graphs, property test) | No plan ever contains a node with an unmet prerequisite; determinism (same seed → same plan) |
| G10 | FSRS non-interference (the law) | For every scenario above: plan's review list == input due list, same order, always ahead of study |

Route-level tests: 404 without tree · `daily_minutes` clamp · feedback writes `metric_events` · IDOR (user B cannot read A's plan) — per `CLAUDE.md`, mandatory.

---

## 6. Schema change (one column, one migration)

`career_goals.daily_minutes INT NOT NULL DEFAULT 60` + CHECK `(daily_minutes BETWEEN 30 AND 240)`. Alembic migration (table already has RLS). No other schema change — the plan is derived, feedback rides `metric_events`.

---

## 7. Config constants (all in `services/planner.py`, tunable without logic edits)

`PREREQ_UNLOCK_THRESHOLD=0.35` · `URGENCY_MAX=2.0` · `UNLOCK_BONUS=0.05` (cap 1.5) · `BALANCE_WINDOW_DAYS=21` · `BALANCE_FLAG_THRESHOLD=-0.15` · `BALANCE_MIN_WINDOW_MINUTES=120` (evidence floor, added during implementation — not an original parent-§16 question) · `REVIEW_COST_MIN=4` · `MAX_STUDY_ITEMS=5` · `DAILY_MINUTES_DEFAULT=60` · `PLAN_HORIZON_DAYS=180` (urgency's timeline anchor, added during implementation — `career_goals` has no stored start date). All are parent-§16 open questions — ship named constants, tune on the owner's own plans first.

**Known open question, not yet resolved:** `BALANCE_FLAG_THRESHOLD` is a share-of-tree-priority comparison, so it's structurally biased toward whichever subject is largest — measured against the three shipped v2 templates, only one subject per template can ever trip it even at zero logged time (see the phase-3 implementation report, 2026-07-26, for the per-template numbers). Left as-is pending dogfood evidence, same as every other §7 constant.

---

## 8. Build order

0. **Gate check:** owner confirms ≥2 weeks of dogfood evidence exists (else pause here — write G-fixtures from synthetic data but don't tune constants). Recommended precursor from the status review: ship the embedding upgrade to `topic_mapping._similarity` first so historic evidence maps in.
1. Golden suite G1–G10 as failing tests + frozen fixtures. **No planner code yet.**
2. `services/planner.py` pure core until G1–G10 green.
3. Migration (`daily_minutes`) + `alembic upgrade head`.
4. `GET /today` + `PATCH /goals/active` + `POST /today/feedback` + route tests.
5. Today card in `CareerTree.jsx` + balance strip; live browser verification (per repo convention — SQLite hides what Postgres/real flows catch).
6. **Owner runs his own plan for 3 consecutive days and judges it** — the phase-1 "does the number feel honest" criterion, applied to plans. If a plan feels wrong, the fix is a constant or a golden scenario, in the spec, before code.
7. Docs same commit: SYSTEM-OVERVIEW (§1 services/routes, §2 column, changelog) + DECISIONS (pure-planner/no-plan-table/FSRS-non-interference entry) + BACKLOG grooming.

Do not push. Deploy only on explicit "push".

## 9. Definition of done

- [ ] G1–G10 green, including the two property tests (G9, G10) and 3 snapshot goldens
- [ ] `GET /api/career/today` returns a plan with a reason on every item
- [ ] FSRS review flow byte-identical to before (its own tests untouched and passing)
- [ ] Sprint mode consumed end-to-end (set via existing `POST /sprint` → visible in plan)
- [ ] Owner has followed 3 real daily plans and stated whether they scheduled the right things
- [ ] Docs updated same commit

The last box is the exit criterion — a scheduler the owner won't follow is worse than no scheduler, because it burns trust the evidence spine earned.

---

## 10. Report back on completion

1. Three real plans (verbatim) + the owner's verdict on each.
2. Balance table over the owner's real 21-day window — does the neglect flag point where he already knows he's slacking?
3. Constants changed during tuning, with the scenario that forced each change.
4. Anything this spec got wrong — spec edit before code, per the parent rule.
