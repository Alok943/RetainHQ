# Career Coach — Phase 2 Implementation Spec: Goal, Tree & Topic Mapping

**Status:** Ready to implement · **Owner:** Alok · **Date:** 19 Jul 2026
**Parent doc:** `retainhq-career-coach-design-doc.md` (v1.2) — owns *what and why*.
**Predecessor:** `docs/SPEC-career-coach-phase1.md` (Evidence Spine) — **must be shipped and dogfooded before this starts.**
**Maps to parent §6 (Taxonomy), §7 topic-mapping rule, and the tree half of §17 Phase 1.**

---

## 0. Why this is phase 2 (and why the scheduler still isn't)

Phase 1 produces honest mastery numbers, but they land on whatever catalog nodes the owner happens to have linked — and §6.3 of that spec predicted a large `unmapped_events` count. Phase 1 measures; it has nothing to measure *against*.

This phase supplies the missing noun: **a per-user career tree that is ground truth for every classifier downstream** (parent §6: "user confirms/edits the tree before tracking starts"). It also closes the unmapped leak, because free-text and unlinked evidence can only be mapped once there's a tree to map onto.

The scheduler is still deliberately absent. It needs subject priorities (this phase), mastery (phase 1), *and* a golden-scenario suite. Building it before the tree exists means inventing the tree's shape from the scheduler's convenience — backwards. Phase 3 is scheduler + Today screen; phase 4 is the coach agent.

**Exit criterion:** the owner completes goal → diagnostic → tree confirm in under 5 minutes (parent Goal #1), and phase 1's `unmapped_events` share drops to a number the owner accepts, measured on the same history.

### Explicitly out of scope
Daily scheduler · Balance score · Today screen · weekly report · coach agent · tutoring/teach-back · LeetCode/GitHub sync · companion · template migration UX (parent §16, P2) · multi-goal (A1).

If something here seems to need one of those, it's a spec bug — flag it. Parent §17 scope rule: additions require a removal.

---

## 1. Reuse, don't reinvent

RetainHQ already ships the exact pattern this phase needs. `backend/app/services/syllabus.py` turns an uploaded PDF into a **draft** roadmap, the user edits it in the UI, and a separate `/commit` endpoint writes it. Its header comment states the governing constraint: *the output is a PROPOSAL, never written to the DB here — an LLM parse is ~90% right and the 10% must be user-correctable before save.*

That is exactly parent §6's mandatory confirm step. **Build tree generation as a second producer into the same draft → review → commit flow**, not a parallel system.

| Existing asset | How phase 2 uses it |
|---|---|
| `services/syllabus.py` — provider routing, structured output, Pydantic re-validation, size caps | Copy the shape for `services/career_tree.py`; reuse `_uses_gemini()`-style provider routing and the hand-written JSON schema discipline |
| `POST /api/syllabus/commit` — draft → `Roadmap` + `RoadmapNode` rows | The tree commits to the **same tables** (`roadmaps.user_id` set, `audience='career'`). A career tree *is* a personal roadmap. No new roadmap entity. |
| `RoadmapNodePrerequisite` | Carries the tree's `dependencies[]`. Already exists; already seeded by title elsewhere. |
| `UserPref.custom_roadmaps_created` + `SYLLABUS_LIFETIME_LIMIT` | Career-tree generation is quota-exempt (see §3.4) — but read `_check_and_bump_daily_limit` before deciding how to rate-limit. |
| `services/grader.py` `_groq_json` | The small-fast-model path for topic mapping (§5). Parent §12 model tiering: classification → Groq tier. |
| Phase 1 `node_id` FK on `learning_events` | Unchanged. Career-tree nodes are `roadmap_nodes` rows, so phase 1's evidence spine works against them with zero changes. |

**The single most important consequence:** because a career tree is just a personal roadmap, phase 1's evidence engine, the FSRS review loop, and the lesson runtime all work against it on day one. Do not introduce a separate node table.

---

## 2. Data model

Only two new tables. Everything else rides on existing schema.

### 2.1 `career_goals`

```python
class CareerGoal(SQLModel, table=True):
    """The user's active career target. Drives tree generation and (phase 3)
    scheduler priorities. One active goal per user — parent doc assumption A1;
    multi-goal is explicitly P2."""
    __tablename__ = "career_goals"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(index=True)
    role_key: str                       # 'backend' | 'ai_engineer' | 'sde_generalist' — a template key
    title: str                          # user-facing, editable: "Backend SDE, Jan 2027 placements"
    target_date: Optional[date] = None  # deadline proximity input for phase 3; None = open-ended
    # The tree this goal generated. NULL only between goal creation and tree commit.
    roadmap_id: Optional[uuid.UUID] = Field(default=None, foreign_key="roadmaps.id", index=True)
    template_version: Optional[str] = None  # pinned at commit — parent §6 versioning rule
    # Parent A3: user-declared temporary weight override. Stored now, consumed in
    # phase 3. Suppresses balance flags until the end date.
    sprint_node_id: Optional[uuid.UUID] = Field(default=None, foreign_key="roadmap_nodes.id")
    sprint_until: Optional[date] = None
    status: str = Field(default="active")   # 'active' | 'archived'
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

Partial unique index: `UNIQUE (user_id) WHERE status = 'active'` — one active goal, enforced by the DB rather than by application code that phase 3 might forget.

### 2.2 `node_meta`

Career trees need per-node fields (`priority`, `est_effort_min`, `stable_key`) that catalog roadmap nodes don't have. **Do not add them to `roadmap_nodes`** — that table is shared with the school platform and the catalog, and widening it for one feature makes every other surface carry the cost.

```python
class NodeMeta(SQLModel, table=True):
    """Career-tree-specific node attributes. Sidecar to roadmap_nodes so the
    shared catalog table stays untouched. Rows exist only for career-tree nodes."""
    __tablename__ = "node_meta"
    __table_args__ = (UniqueConstraint("node_id", name="uq_node_meta_node"),)
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    node_id: uuid.UUID = Field(foreign_key="roadmap_nodes.id", ondelete="CASCADE", index=True)
    # Stable across template versions — parent §6 mandatory rule. Template-authored
    # slug ('dsa.graphs.bfs'), NOT the UUID (node UUIDs are regenerated on re-seed,
    # see the RoadmapNodePrerequisite docstring).
    stable_key: str = Field(index=True)
    priority: int = Field(default=3, ge=1, le=5)
    est_effort_min: int = Field(default=60)
    subject: str                          # top-level grouping for phase-3 balance: 'dsa' | 'os' | 'dbms' | ...
    review_policy: str = Field(default="default")  # parent A7: per-node FSRS tuning, consumed later
    user_edited: bool = Field(default=False)       # protects user edits from template upgrades
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

`subject` matters more than it looks: phase 3's Balance formula (`p_s` / `a_s` per subject) needs a stable grouping key, and inferring it from tree depth later will be wrong for irregular trees. Set it now, at generation time.

Both tables: `ENABLE ROW LEVEL SECURITY` (no policies), per `CLAUDE.md`.

---

## 3. Role templates

### 3.1 Format and location

Versioned files in the repo — parent §6: *"The LLM adapts a template — it does not invent syllabi from scratch."*

`content/career-templates/<role_key>.v<N>.json`:

```json
{
  "role_key": "backend",
  "version": "v1",
  "title": "Backend Engineer",
  "subjects": [
    {
      "key": "dsa",
      "title": "Data Structures & Algorithms",
      "default_priority": 5,
      "nodes": [
        {
          "stable_key": "dsa.arrays.two_pointers",
          "title": "Two Pointers",
          "est_effort_min": 120,
          "priority": 4,
          "depends_on": ["dsa.arrays.basics"],
          "diagnostic_probe": "Given a sorted array, find two numbers summing to a target in O(n)."
        }
      ]
    }
  ]
}
```

Rules:
- `stable_key` is globally unique within a template and **never reused for a different concept** across versions. This is the load-bearing versioning primitive (parent §6).
- `depends_on` references `stable_key`s, resolved into `RoadmapNodePrerequisite` rows at commit.
- A validator (`content/validate_career_templates.py`, mirroring `content/validate.py`) enforces: unique stable keys, no dependency cycles, `depends_on` targets exist, priority 1–5, effort > 0. **Wire it into CI alongside the existing content gate.**

### 3.2 Which three ship

Parent §16 leaves this open. Decide it here: **`backend`, `ai_engineer`, `sde_generalist`** — matching the parent doc's own §6 list and the owner's stated build priority (AI-Eng → DSA → Data-Eng). Owner curates, as parent §16 says.

Target **40–70 nodes per template**. Below ~40 the tree can't express real coverage; above ~70 the confirm step exceeds the 5-minute budget and users rubber-stamp it — which silently destroys the "ground truth" property everything downstream depends on.

### 3.3 Generation is adaptation, not invention

`services/career_tree.py`, one model call (parent §12: roadmap generation → top-tier model, ≤1 call/user/week):

**Input:** the template JSON + goal (`role_key`, `target_date`) + diagnostic results (§4) + optional free-text context ("I've done 200 LeetCode problems, weak on DP").

**The model may:** drop nodes the user has demonstrably mastered, add ≤10 nodes for gaps the template misses, adjust `priority`, reorder within subjects, rewrite titles for clarity.

**The model may not:** invent new `subject` keys, produce nodes without a `stable_key` (new nodes get `custom.<slug>`), create dependency cycles, or exceed 90 nodes.

Enforce every one of these in Pydantic validation after the call — same defense-in-depth posture as `syllabus.py`. A model that violates a rule gets one retry with the violation in the prompt, then falls back to **the unmodified template**. Never fail the onboarding: a generic tree the user then edits beats an error screen.

### 3.4 Quota

Career-tree generation does **not** consume `custom_roadmaps_created`. That quota exists to bound syllabus-PDF abuse; a career tree is the product's primary onboarding path and gating it behind a lifetime limit would block the main flow. Rate-limit separately: **3 generations per user per day**, reusing the `_check_and_bump_daily_limit` pattern in `routes/syllabus.py`. Regeneration is expected during onboarding — users try a goal, dislike the tree, retry.

---

## 4. Diagnostic

Parent §6 cold start: *"Day-zero mastery comes from the diagnostic + imports only. Never guess initial mastery from stated confidence."*

- **5–8 items**, drawn from `diagnostic_probe` fields on the template's highest-priority nodes. Not generated fresh — probes are authored content, so they're reviewable and stable.
- Answers graded by the existing `grader.grade_recall` / `grade_question_set` pipeline. No new grading path.
- **Each graded probe writes a phase-1 `learning_event`**: `RECALL_GRADED`, `T2_verified_internal`, `source="retainhq_coach"`, `grade` from the grader, `entity_id` = the diagnostic attempt id. Cold-start mastery is therefore produced by the *same fold as everything else* — there is no separate "initial mastery" path to keep consistent. This is the cleanest possible use of phase 1.
- Events are written **after** tree commit (the nodes must exist). Hold results in the draft, replay them on commit.
- **Skippable.** No diagnostic → every node starts `unexposed`, exactly per parent §6. Do not substitute self-rated confidence — the parent doc forbids it by name.

---

## 5. Topic mapping (closing the phase-1 leak)

Phase 1 §6.3 counted unmapped evidence. This section spends that number.

**Tier 1 — exact/structured.** Deterministic lookup. For phase-2 producers this is `activity.node_id` when set, and the diagnostic path above. No model call. Always tried first.

**Tier 2 — embedding match** against the user's tree node titles + descriptions.
- Embed each tree node once at commit; store vectors in `node_meta`-adjacent storage or a `payload` column — **check whether `pgvector` is enabled on the Supabase project before designing this**; if not, a small in-process cosine match over ≤90 nodes is entirely adequate and avoids an extension dependency. Do not add pgvector just for 90 vectors.
- Confidence recorded in the event's `payload.mapping_confidence` (parent §7 requires this field).
- Threshold: **≥0.75 auto-maps**; 0.55–0.75 maps but flags for triage; **<0.55 goes to the unmapped bucket**. These are parent §16's open question — ship them as named config constants and tune on the owner's own logs first, exactly as that section instructs.

**Tier 3 — unmapped bucket.** A `GET /api/career/unmapped` list the user triages (parent §7: "an 'unmapped' bucket the user can triage weekly"). Assigning a node inserts the corrected event and recomputes.

**Backfill:** a one-shot admin script re-runs mapping over the owner's existing `activities` with `node_id IS NULL` against the newly committed tree, then calls phase 1's `recompute_user`. This is the concrete fix for phase 1's finding — and because phase 1 made mastery a pure fold over events, the backfill is a script, not a migration. That property is the payoff for phase 1's extra work; make sure it holds.

---

## 6. API

New router `backend/app/api/routes/career.py` at `/api/career`, registered in `main.py`. All routes `get_current_user`-gated and scoped by `current_user.id`; mutations verify ownership (`WHERE id = :id AND user_id = :uid`).

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/career/templates` | Available roles: `role_key`, `title`, `version`, node count |
| `POST` | `/api/career/goals/` | Create goal (role, title, target_date). Archives any existing active goal. Trailing slash per convention. |
| `GET` | `/api/career/goals/active` | Active goal + committed tree summary, or 404 |
| `GET` | `/api/career/diagnostic` | 5–8 probes for the goal's template |
| `POST` | `/api/career/diagnostic/submit` | Grade answers; returns per-probe results. Holds them for commit. |
| `POST` | `/api/career/tree/generate` | Draft tree. **Proposal only — writes nothing.** Rate-limited §3.4. |
| `POST` | `/api/career/tree/commit` | Draft → `Roadmap` + `RoadmapNode` + `NodeMeta` + prerequisite rows; pins `template_version`; replays diagnostic events. `201`. |
| `PATCH` | `/api/career/nodes/{node_id}` | Edit priority/effort/title; sets `user_edited=true` |
| `DELETE` | `/api/career/nodes/{node_id}` | Remove a node. Evidence survives (soft-detach — see §7). |
| `GET` | `/api/career/unmapped` | Triage bucket (§5) |
| `POST` | `/api/career/unmapped/{event_id}/assign` | Assign node → insert corrected event → recompute |
| `POST` | `/api/career/sprint` | Declare Sprint Mode (node + end date). Stored; consumed in phase 3. |

Commit is a **single transaction**. A half-written tree with orphaned prerequisite rows is worse than a failed commit — the tree is ground truth, and partial ground truth is a correctness bug in everything downstream.

---

## 7. Evidence survives goal and tree changes

Parent A1: *"Goal switch requested → regenerate tree, keep event log (evidence survives goals)."* This is a real constraint with a real failure mode.

`learning_events.node_id` is an FK to `roadmap_nodes`. If tree regeneration deletes nodes, that FK breaks or cascades — and cascading would **delete the immutable event log**, violating phase 1's Design law 2.

Handle it explicitly:
- Node deletion via the API is a **soft detach**: null the event's `node_id`, write `payload.detached_from_stable_key`, move it to the unmapped bucket. Never delete a `learning_event`.
- Confirm the phase-1 migration did **not** put `ondelete="CASCADE"` on `learning_events.node_id`. If it did, fix it in this phase's migration — flag it as a phase-1 spec error per that doc's §12.5.
- On goal switch, the old roadmap is archived, not dropped. Events keep pointing at real rows.
- Re-mapping by `stable_key` across trees is a natural extension; **not in scope here** — the detach + triage path is sufficient and doesn't need to be clever.

---

## 8. Frontend

Real UI this time, unlike phase 1. Match `docs/design-bible.md`; reuse the syllabus draft-review components where the shapes align.

**Onboarding wizard** (`frontend/src/CareerOnboarding.jsx`) — four steps, ≤5 minutes total:
1. **Goal** — role cards, editable title, optional target date.
2. **Diagnostic** — 5–8 probes, prominently skippable.
3. **Tree review** — grouped by subject, collapsible; inline edit of title/priority/effort; delete nodes. Copy states plainly that this tree is what everything is measured against.
4. **Confirm** — commits, routes to the tree view.

**Tree view** (`frontend/src/CareerTree.jsx`) — nodes by subject with phase-1 state badges (`unexposed` → `interview_ready`) and confidence; tap a node → the phase-1 evidence log (`GET /api/evidence/nodes/{id}/events`). This is where phase 1's debug endpoint becomes parent story 7's trust feature — same endpoint, real surface.

**Unmapped triage** — a simple list; assign or dismiss.

Dark mode comes free via `index.css` overrides **if you reuse existing color classes** (`CLAUDE.md`). Don't hand-roll colors.

Step 3 is where the 5-minute budget is won or lost. If 70 nodes render as a wall of text, users rubber-stamp and the ground-truth property quietly dies. Collapse subjects by default; surface counts.

---

## 9. Tests (`backend/tests/test_career.py`)

**Templates**
1. All three shipped templates pass `validate_career_templates.py`.
2. Stable keys unique; no dependency cycles; every `depends_on` resolves.

**Generation**
3. Model output with an invented `subject` → rejected, retried, then falls back to the raw template.
4. >90 nodes → rejected.
5. Cyclic `depends_on` → rejected.
6. Generation writes nothing to the DB. *(proposal-only guarantee)*
7. 4th generation in a day → 429.

**Commit**
8. Commit creates `Roadmap` + N `RoadmapNode` + N `NodeMeta` + correct prerequisite edges.
9. Commit is atomic: an injected failure mid-commit leaves zero rows.
10. `template_version` pinned on the goal.
11. Second active goal archives the first; the partial unique index holds under a concurrent double-insert.
12. Diagnostic results replay into `learning_events` with `source="retainhq_coach"`, and phase-1 mastery reflects them.
13. Skipped diagnostic → all nodes `unexposed`, zero events.

**Mapping**
14. Exact match wins over embedding.
15. Confidence <0.55 → unmapped bucket, not a wrong assignment. *(a wrong map is worse than no map — Philosophy #3)*
16. Assigning from triage recomputes mastery correctly.

**Evidence survival (§7)**
17. Deleting a tree node nulls the event's `node_id` and does **not** delete the event.
18. Goal switch preserves every prior `learning_event`.

**Ownership**
19. User B cannot read/patch/delete user A's goal, tree nodes, or unmapped events. *(IDOR — mandatory)*

---

## 10. Build order

`pytest` green between steps.

1. Template format + validator + the `backend` template only. CI wired.
2. Models + migration (both tables, RLS, partial unique index) + §7 cascade check on the phase-1 table.
3. `career_tree.py` generation with full validation + fallback. Tests 3–7.
4. Commit transaction + prerequisite resolution. Tests 8–11.
5. Diagnostic → probes → grading → replay on commit. Tests 12–13.
6. Topic mapping tiers + unmapped triage. Tests 14–16.
7. Evidence-survival paths. Tests 17–19.
8. Remaining two templates.
9. Frontend wizard + tree view + triage.
10. **Backfill script** over the owner's real history; recompute; compare `unmapped_events` before/after.
11. Docs: `SYSTEM-OVERVIEW.md` (§1 tables, §2 router, changelog line) + `DECISIONS.md` — same commit.

Do not push. Deploy only on an explicit "push".

---

## 11. Decisions to record in `docs/DECISIONS.md`

- **Career tree = personal roadmap, not a new entity** — inherits the evidence spine, FSRS loop, and lesson runtime for free. Tradeoff: `roadmaps` now serves three purposes (catalog, syllabus-upload, career), so its queries need consistent filtering discipline.
- **`node_meta` sidecar instead of widening `roadmap_nodes`** — keeps the school/catalog path unburdened. Tradeoff: one extra join on career-tree reads.
- **Templates + adaptation, never free invention** — reviewable, versionable, diffable syllabi; the model personalizes within a curated bar. Tradeoff: three curated templates is a real content cost and caps early role coverage.
- **Diagnostic writes ordinary `learning_event`s** — no separate cold-start mastery path to keep in sync. Direct consequence of phase 1's fold-only design.
- **Node deletion soft-detaches evidence** — Design law 2 outranks referential tidiness.
- **Career-tree generation is quota-exempt, daily-rate-limited instead** — it's the primary onboarding path; a lifetime cap would gate the main flow.

---

## 12. Definition of done

- [ ] `pytest` green, all 19 tests
- [ ] `alembic upgrade head` clean; both tables RLS-enabled; phase-1 FK cascade verified safe
- [ ] Three templates ship and pass the validator in CI
- [ ] Owner completes goal → diagnostic → confirmed tree in **under 5 minutes**, timed
- [ ] Backfill run; `unmapped_events` before/after recorded with real numbers
- [ ] Tree view shows phase-1 mastery states and drills into the evidence log
- [ ] Generation failure falls back to the raw template — never an error screen
- [ ] `SYSTEM-OVERVIEW.md` + `DECISIONS.md` updated in the same commit
- [ ] Owner has confirmed the tree reflects what he actually needs to study

That last box is the exit criterion. A tree the owner doesn't believe in poisons every number phase 3 computes.

---

## 13. Report back on completion

1. Timed onboarding run — actual minutes, and which step consumed most.
2. `unmapped_events` **before and after** backfill, as counts and as a share of reviews.
3. Nodes per template; how many the model dropped/added/reprioritized for the owner.
4. Any template node the owner deleted or heavily edited — that's a curation bug worth fixing in the template, not just in his tree.
5. Mapping-threshold behavior: how many events landed in each confidence band.
6. Where this spec was wrong or underspecified — spec edit before code, per the parent doc's Rule.
