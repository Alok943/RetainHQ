# Implementation Plan — Attach Roadmaps to a Career Goal

**For the implementer (Sonnet).** Same contract as `IMPLEMENTATION-career-coach-phase3.md`:
that doc's §0 preflight (async DB, `SupabaseUser`, IDOR, Pydantic v2, naive-UTC, no push) applies
here **unchanged** — read it first. This doc owns only what is new.

**Predecessor:** Career Coach Phase 3 (shipped 2026-07-26, `D-041`). This feature has no meaning
without the planner — attaching a roadmap is only interesting because `/api/career/today` then
schedules from it.

Baseline before you start: **326 tests passing.** Do not finish with fewer.

---

## 1. What the user asked for

> "Add an option to add roadmaps in the career coach — either the inbuilt roadmaps, or bring your own."

Today a `CareerGoal` points at exactly **one** roadmap: the LLM-generated career tree
(`career_goals.roadmap_id`). Everything else in the product — the DSA roadmap with 126 nodes, the
Python/SQL/Core-CS catalogs, and any personal roadmap the user built from a syllabus — is invisible
to the coach. A user grinding the DSA roadmap gets **zero** credit in their plan or their balance
strip, because the planner never sees those nodes.

After this change a goal draws its plan from its generated tree **plus** any roadmaps the user has
attached, from two sources:

| Source | What it is |
|---|---|
| **Inbuilt** | Official catalog roadmaps — `roadmaps.user_id IS NULL`, filtered to the caller's `user_prefs.audience` (same rule `GET /api/roadmaps/` already applies) |
| **Bring your own** | The user's own roadmaps — `roadmaps.user_id = <caller>`, created via the existing syllabus flow |

---

## 2. The crux — read this before designing anything

**The planner INNER JOINs `node_meta`.** `GET /api/career/today` does:

```python
select(RoadmapNode, NodeMeta, NodeMastery).join(NodeMeta, NodeMeta.node_id == RoadmapNode.id)
```

and `node_meta` rows exist **only for career-tree nodes** — every catalog node has zero. That
sidecar is where `subject`, `priority` and `est_effort_min` live, and the planner cannot score a
node without all three.

So attaching a roadmap is not a pointer change. **It means creating `node_meta` rows for that
roadmap's nodes.** That is the whole feature; everything below is consequence.

### Rejected: copying nodes into the career tree
Duplicating `roadmap_nodes` into the goal's roadmap would break lesson deep-links (they resolve
`/<roadmap-slug>/learn/<lesson-slug>`), fork `user_progress`, and split FSRS history across two
node ids for the same concept. **Do not do this.** The roadmap stays exactly where it is; only the
sidecar is new.

---

## 3. Schema

### 3.1 New table `career_goal_roadmaps`

```python
class CareerGoalRoadmap(SQLModel, table=True):
    """A roadmap this goal draws its plan from, beyond its own generated tree.
    Nodes stay in their home roadmap — only node_meta sidecar rows are created."""
    __tablename__ = "career_goal_roadmaps"
    __table_args__ = (UniqueConstraint("goal_id", "roadmap_id", name="uq_goal_roadmap"),)
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    goal_id: uuid.UUID = Field(foreign_key="career_goals.id", ondelete="CASCADE", index=True)
    roadmap_id: uuid.UUID = Field(foreign_key="roadmaps.id", ondelete="CASCADE", index=True)
    subject: str                      # the balance bucket these nodes fold into
    default_priority: int = Field(default=3, ge=1, le=5)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

Migration: `down_revision` = current head (**check with `alembic history`** — do not assume; it was
`b7b1755c4d22` on 2026-07-26). New table ⇒ **`op.execute("ALTER TABLE career_goal_roadmaps ENABLE ROW LEVEL SECURITY;")`**
is mandatory per `CLAUDE.md`. No policies.

> **[DECISION]** The join row carries `subject` and `default_priority` rather than relying purely
> on the `node_meta` rows it creates, so that detach-then-reattach is idempotent and a future
> "re-sync this roadmap" can regenerate sidecars without asking the user again.

### 3.2 No change to `node_meta`
Its `stable_key` is already free-form. Use `f"attached.{roadmap_slug_or_id}.{node.id}"`. Unlike
template keys this needs no cross-version stability — an attached roadmap's nodes are addressed by
their real UUIDs, which do not regenerate the way template trees do.

---

## 4. Routes — all under the existing `career` router

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/career/roadmaps/available` | What the user may attach, split into `inbuilt` and `mine`, each already excluding anything attached |
| `POST` | `/api/career/roadmaps/` | Attach. Body `{roadmap_id, subject, default_priority}` |
| `DELETE` | `/api/career/roadmaps/{roadmap_id}` | Detach |
| `GET` | `/api/career/roadmaps/` | Currently attached, with node counts |

### `GET /roadmaps/available`
Two lists. **Inbuilt**: `user_id IS NULL` **and** `audience == the caller's user_prefs.audience`
(reuse the filter in `GET /api/roadmaps/` — do not reinvent it; a school-audience user must never
be offered career roadmaps). **Mine**: `user_id == caller`. Exclude the goal's own
`roadmap_id` from both, and anything already in `career_goal_roadmaps` for this goal. Each entry:
`{id, slug, title, node_count, source: 'inbuilt' | 'mine'}`.

### `POST /roadmaps/`
1. Active goal with a committed tree, else **404** (reuse `_get_active_goal_with_tree`).
2. Load the roadmap. **Reject with 403 unless `roadmap.user_id IS NULL` or `roadmap.user_id == caller`.**
   This is the IDOR surface of the whole feature — without it any user attaches, and thereby reads
   the node titles of, any other user's private roadmap. Its own test is mandatory.
3. Reject the goal's own `roadmap_id` (400) — it is already the tree.
4. Insert the join row. The unique constraint makes double-attach a 409, not a duplicate.
5. **Create `node_meta` for every node in that roadmap that lacks one**, in one bulk insert:
   `subject` from the body, `priority = default_priority`, `est_effort_min = 60`,
   `stable_key` as §3.2. Nodes that already have a sidecar (because they were in a template tree)
   are left alone — **never overwrite an existing `node_meta`**, it may carry `user_edited=True`.
6. Return the attachment with `nodes_added`.

> **[DECISION]** `est_effort_min = 60` flat. The spec's §0 precondition 2 already says effort is
> only ever used to *proportion* a session, never to promise wall-clock time, and a flat value
> proportions evenly — which is honest for nodes nobody has estimated. Do not invent per-node
> estimates from difficulty; that is a guess wearing a number's clothes.

### `DELETE /roadmaps/{roadmap_id}`
Delete the join row **and** the `node_meta` rows this attachment created (match on the
`attached.{...}` `stable_key` prefix, and never delete one with `user_edited=True`).
**Do not touch `learning_events`, `node_mastery`, `activities`, or `user_progress`** — evidence is
immutable and append-only (`ARCHITECTURE-learning-system.md`). Detaching removes a roadmap from
*planning*, it does not erase that the user studied it. Say so in the UI.

### Cap
`user_prefs.custom_roadmaps_created` (lifetime limit 3) governs **creating** a syllabus roadmap and
must not be consumed by attaching one. Attaching is free. Add a separate
`MAX_ATTACHED_ROADMAPS = 5` guard in the route so a goal cannot be diluted into a backlog.

---

## 5. Planner integration — one query change, no planner change

`services/planner.py` **is not modified.** It already takes an opaque node list; where those nodes
live is the route's problem. In `get_today_plan`, replace the single-roadmap filter:

```python
# before
.where(RoadmapNode.roadmap_id == goal.roadmap_id)
# after
attached_ids = (await db.execute(
    select(CareerGoalRoadmap.roadmap_id).where(CareerGoalRoadmap.goal_id == goal.id)
)).scalars().all()
.where(RoadmapNode.roadmap_id.in_([goal.roadmap_id, *attached_ids]))
```

Then verify each of these still holds — write a test for each:

1. **`node_ids` feeds the balance window.** The 2026-07-26 scoping fix filters the trailing-window
   query by `LearningEvent.node_id.in_(node_ids)`. Attached nodes must be in `node_ids`, otherwise
   attaching a roadmap the user actively studies makes its subject look permanently neglected —
   the exact false-nudge failure that fix existed to prevent.
2. **Prerequisites keep working.** Catalog roadmaps already have `roadmap_node_prerequisites`
   (the DSA roadmap has 258 edges). They are read by `node_id`, so they work unchanged — but
   edges are **intra-roadmap only**, so an attached roadmap's roots are always frontier-available.
   That is correct and intended; do not add cross-roadmap edges (see `D-036`).
3. **`p_s` shifts.** Attaching a 126-node roadmap at priority 3 adds 378 priority to the
   denominator, shrinking every existing subject's `p_s`. This is arithmetically right but changes
   which subjects can ever trip `BALANCE_FLAG_THRESHOLD`. It is the same subject-count sensitivity
   already flagged in `BACKLOG.md`; **measure it and report**, do not silently retune the constant.

---

## 6. Frontend — `CareerTree.jsx`

An "Add a roadmap" control near the Today card, opening a picker with two tabs:

- **Inbuilt** — the catalog list, each row showing title and node count.
- **Yours** — the user's own roadmaps. Empty state links to the existing syllabus flow
  ("Build one from a syllabus"), which is a **separate existing feature — do not rebuild it**;
  deep-link and let the user come back.

On select: ask for the **subject** (prefilled with the roadmap title, lowercased) and priority
(1–5, default 3), then POST. Subject matters — it is the balance bucket, and two roadmaps given
the same subject merge into one bar on the strip.

Attached roadmaps list under the tree with a detach control. Detach confirms, and the confirm text
must state plainly that **progress and evidence are kept; only planning stops**.

Follow `Home.jsx`'s post-2026-07-24 loading pattern: track fetch failure separately from genuine
emptiness. "No roadmaps available" and "we couldn't load them" are different screens. Reuse
existing color classes → dark mode is free.

---

## 7. Tests

`backend/tests/test_career_roadmaps.py`:

- attach an inbuilt roadmap → join row + `node_meta` for every node; `/today` then includes its nodes
- attach one of the user's own → same
- **attach another user's private roadmap → 403** (the load-bearing IDOR test)
- attach the goal's own tree → 400
- double attach → 409
- attach beyond `MAX_ATTACHED_ROADMAPS` → 400
- `available` excludes attached, excludes the goal's tree, and respects `audience`
- detach → join row and generated sidecars gone; **`learning_events` and `node_mastery` untouched**
- detach leaves a `user_edited=True` `node_meta` alone
- attached-roadmap minutes **do** reach the balance window (regression guard for §5.1)
- no goal → 404 on every route

---

## 8. Build order

1. Model + migration (**RLS**) + `alembic history` check. Do not upgrade prod.
2. Schemas.
3. Routes + `test_career_roadmaps.py`.
4. The one-line planner-query change in `get_today_plan` + the three §5 verification tests.
5. Frontend picker + attached list + live browser check.
6. Docs same commit: SYSTEM-OVERVIEW (§1 routes, §2 table, changelog), DECISIONS (`D-042`:
   attach-by-sidecar, not by copy; detach keeps evidence), BACKLOG grooming.

**Do not push.**

---

## 9. Definition of done

- [ ] Full suite ≥ 326 passing, 0 failing
- [ ] A DSA roadmap attached to a real goal shows DSA nodes in `GET /api/career/today`
- [ ] The IDOR test (another user's private roadmap → 403) is green
- [ ] Detach provably leaves `learning_events` and `node_mastery` row counts unchanged
- [ ] Attached-roadmap study time moves the balance strip
- [ ] Verified in a live browser, console clean
- [ ] Docs updated in the same commit

## 10. Report back

1. Both **[DECISION]**s: agree or disagree, with reasoning.
2. The `p_s` shift from §5.3, measured: subject shares before and after attaching a 126-node
   roadmap, and which subjects can still trip `-0.15`.
3. Whether `est_effort_min = 60` flat produced sane `est_share` proportions in a real plan, or
   whether one attached roadmap swamped the day.
4. Confirm you did not modify `services/planner.py`, and did not push.
