# Implementation Plan — LeetCode Problems on DSA Nodes + Manual Capture

**For the implementer (Sonnet).** `IMPLEMENTATION-career-coach-phase3.md` §0 applies unchanged.
Baseline: 355 backend tests, 25 extension tests. Do not finish with fewer.

Step 7 of `SPEC-leetcode-retention.md` (concept-framed selection + the concept view), scoped to
what the owner actually asked for: a **capture fallback for when the extension isn't running**,
not a problem browser.

---

## 1. The rule that governs everything here

| Path | Writes | Reaches career tree? |
|---|---|---|
| **Extension** detects an Accepted submission | `learning_events` (`T1_verified_external`) → `node_mastery` | **Yes** |
| **Manual click** in the roadmap | `problem_attempts` only (see §3) | **No** |

This is the product thesis made structural — *"track what you remember, not what you complete."*
A manual click is a **completion checkbox**, not evidence. It must never create a `learning_event`,
never move `node_mastery`, and never touch the career tree.

**Do not be tempted to route manual clicks through `POST /api/evidence/leetcode/solve`.** That
endpoint hardcodes `trust_tier="T1_verified_external"`, which is honest only because the extension
observed a real submission. Reusing it would let a user reach the highest trust tier by clicking,
and the mastery number is the one thing this product sells.

`T4_claimed` was considered and rejected: it would still write a `learning_event` and still move
career-tree mastery, just less. The owner's rule is cleaner — manual capture stays out of the
evidence spine entirely. Side benefit: the difference is visible in the evidence log, which is a
truthful reason to install the extension.

---

## 2. Data already in prod (verified 2026-07-26 — do not re-derive)

- `problems`: 3,999 · `problem_concepts`: 5,084 (2,944 primary / 1,718 supporting / 422 alternative)
- Coverage: **114 of 126** DSA nodes have at least one problem
- Per node, primary problems: median **13**, mean 26, max **184** (hash tables); 16 nodes exceed 60
- **1,055 problems are `out_of_scope`** — deliberately unmapped, and therefore unreachable in this
  UI. That is intended: the product does not offer "browse all of LeetCode."

Two consequences to handle rather than discover:
- **12 nodes will render an empty Problems section.** Show an honest empty state, not a spinner or
  a hidden section.
- **The 16 big nodes need ordering**, not pagination-by-default. Sort by difficulty then problem
  number; the owner asked for sorting by topic and number, and *within a concept* number-sort is
  the sensible reading.

---

## 3. Schema — one new table

`user_progress` is keyed on `node_id` and cannot express per-problem state, so marking individual
problems needs its own table.

```python
class ProblemAttempt(SQLModel, table=True):
    """Manual 'I solved this' marks. Deliberately NOT evidence — see §1. This
    table is the completion checkbox; learning_events is the evidence spine, and
    nothing here is allowed to reach it."""
    __tablename__ = "problem_attempts"
    __table_args__ = (UniqueConstraint("user_id", "problem_id", name="uq_problem_attempt"),)
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(index=True)
    problem_id: uuid.UUID = Field(foreign_key="problems.id", ondelete="CASCADE", index=True)
    status: str = Field(default="solved")     # 'solved' | 'attempted'
    marked_at: datetime = Field(default_factory=datetime.utcnow)
```

Migration: `down_revision` = current head (**check `alembic history`**, do not assume). New table ⇒
**`ENABLE ROW LEVEL SECURITY`** is mandatory (`CLAUDE.md`).

> The FK to `problems` is a bridge from user data to a bulk-rebuildable catalog table — exactly the
> shape that caused D-039. `problems` is already guarded by the `no_truncate_*` triggers only on the
> user-data side, so **add `problem_attempts` to the guarded list** in a follow-up migration, or a
> future `TRUNCATE problems CASCADE` silently takes these rows with it.

---

## 4. Routes (`api/routes/evidence.py` or a new `problems` router)

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/problems/by-node/{node_id}` | Problems for a concept, grouped by role, with the caller's marks |
| `POST` | `/api/problems/{problem_id}/mark` | `{status}` → upsert `ProblemAttempt`. **204.** |
| `DELETE` | `/api/problems/{problem_id}/mark` | Unmark |

`GET` response per problem: `{id, external_id, slug, title, difficulty, url, paid_only, role, marked_status}`.
Order primary first, then supporting, then alternative; within each, `difficulty` (easy→hard) then
`external_id`. Return the whole set — median 13 does not need pagination, and the client sorts.

**Scope every query by `user_id`.** IDOR test mandatory: user B must not see or clear A's marks.
Marking is user-scoped only — `problems` itself is a shared catalog with no `user_id`, so there is
nothing to own-check on the problem, only on the attempt.

---

## 5. Frontend — `RoadmapDetail.jsx` (DSA nodes)

A collapsed **Problems (N)** section on the node detail panel:

- Rows: title → external LeetCode link (`target="_blank"`, `rel="noopener noreferrer"`), difficulty
  chip, a checkbox that marks/unmarks.
- Sort control: **difficulty** / **number**. Default difficulty.
- Group headings for supporting/alternative, collapsed by default — primary is the answer to
  "what should I solve for this concept."
- `paid_only` problems: label them. Sending a user to a paywall unlabelled is a bad experience.
- Empty state for the 12 uncovered nodes: "No problems mapped to this concept yet."
- Follow `Home.jsx`'s post-2026-07-24 pattern — **track fetch failure separately from emptiness**.
  "Couldn't load problems" and "no problems exist" are different screens.
- Reuse existing color classes → dark mode free.

Optimistic checkbox toggle, reverted on error.

---

## 6. Tests

Backend (`tests/test_problems.py`):
- mark → row created; idempotent (marking twice is one row, per the unique constraint)
- unmark → row gone
- **marking creates NO `learning_event` and does NOT change `node_mastery`** — the load-bearing test
- `GET by-node` returns primary/supporting/alternative correctly and includes the caller's marks
- a node with zero problems returns an empty list, not a 404
- IDOR: B cannot see or delete A's marks

---

## 7. Build order

1. Model + migration (**RLS**, `alembic history` first). Do not upgrade prod.
2. Schemas + routes + tests.
3. `RoadmapDetail.jsx` section; live browser check.
4. Docs same commit: SYSTEM-OVERVIEW (§1 routes, §2 table, changelog), DECISIONS (`D-046` — manual
   capture is completion, not evidence; why not T4), BACKLOG (add `problem_attempts` to the
   truncate-guard list).

**Do not push.**

## 8. Definition of done

- [ ] Backend ≥ 355 passing
- [ ] A DSA node shows its problems, sortable, links open LeetCode
- [ ] Marking a problem provably writes no `learning_event` and no `node_mastery` change
- [ ] IDOR green; the 12 empty nodes render an honest empty state
- [ ] Verified in a live browser, console clean

## 9. Report back

1. Whether `problem_attempts` should also feed the roadmap's node-level progress bar (it currently
   counts `user_progress` rows only) — a product call, not yours to make silently.
2. Anything the 184-problem node makes unusable in practice.
