# Lesson → Review bridge (the content→card P0)

**Problem:** lessons (`python-swe`, `sql`, `aptitude`) are read-once-and-forget. Their
`recall_questions` never enter the review queue, so the retention moat —
*"studied it 2 months ago, still remember it"* — is currently **impossible for lesson content**.
The FSRS engine only schedules manually-logged `activities`.

**Key insight:** a lesson-card **IS an `Activity`.** The scheduler (`initial_review_for_activity`,
`apply_fsrs`), the `/reviews/due` queue, the daily cap, and `Review.jsx` all operate on activities.
So the bridge is *"a lesson creates a pre-filled Activity, linked to its node"* — **not** new
scheduling logic. ~90% of this already exists.

---

## Data model (one small, safe migration)
Add to `activities` (and the `Activity` model):
```
node_id: Optional[uuid.UUID] = Field(default=None, foreign_key="roadmap_nodes.id")
```
- Nullable FK → `roadmap_nodes`. Non-breaking (existing rows = NULL). `roadmap_id` already exists
  (roadmap-level); `node_id` adds the lesson-level link.
- `source_type = "lesson"` (plain string, already supported — no schema change) marks lesson-cards.
- **Why node_id:** (1) idempotency — one card per (user, node), so "Add to reviews" can't double-add;
  (2) the lesson UI can show "In your reviews ✓"; (3) review can pull that lesson's `recall_questions`
  from the static JSON via node → slug.
- Migration: `alembic revision -m "activities.node_id (lesson link)"` → **Alok runs `alembic upgrade
  head`** on the live DB (per working style; not auto-run).

## Trigger — explicit opt-in
A **"Add to my reviews"** button on `LessonView`. Pre-fills the card from the lesson:
- `topic` = lesson title
- `key_memory` = the lesson's core claim (aptitude: `mental_model.intuition` + `formula.statement`;
  python/sql: `overview.what` first line or `aha_moment`). Capped 500 chars.
- `roadmap_id` = the lesson's roadmap, `node_id` = the node, `source_type = "lesson"`,
  `difficulty = 3` default, `needed_hint = false`.
Reuses the existing `POST /api/activities/` exactly — same FSRS init, same "first review tomorrow"
(first-ever activity still gets the demo-due-now aha).

## Endpoint — extend, don't add
Add `node_id` to `ActivityCreate` + pass it through `log_activity`. One guard: if
`source_type == "lesson"` and a card for `(user_id, node_id)` already exists, **return that card
(idempotent)** instead of inserting a duplicate. No new route.

## Review experience
- **MVP:** lesson-cards flow through `/reviews/due` + `Review.jsx` **unchanged** — they're activities.
  The retrieval gate quizzes the card's `key_memory` (the lesson core). Ships the loop immediately.
- **P1 (next):** when `review.activity.node_id` is set, `Review.jsx` fetches the lesson JSON and
  presents its full `recall_questions` set (richer than the single key_memory). Display-only change.

---

## The fork (decide before the migration)
**One card per lesson** (recommended) vs **one card per `recall_question`**.
- *Per-lesson:* matches the existing "one activity = one card"; simplest; review can still quiz the
  multiple recall_questions inside one card. Card count = #lessons.
- *Per-question:* SRS-purer (each fact scheduled independently) but 3–4× the cards + needs a new
  card source distinct from `activities`. Heavier model change.
- **Recommendation: per-lesson for MVP.** Revisit per-question only if retention data shows topics
  are too coarse to grade. (Avoids a bigger model change now.)

## Scope cut
- **MVP (this build):** migration + `node_id` on ActivityCreate/log_activity + idempotency guard +
  "Add to reviews" button on LessonView. Lesson-cards retain via the existing engine. **Done = a
  lesson you add today resurfaces in tomorrow's review queue.**
- **P1:** Review.jsx renders the lesson's full recall_questions for lesson-cards.
- **P2:** the existing backlog item "node-complete → pre-filled Log modal" becomes a second trigger
  on top of the same bridge.
- **Not now:** per-question cards; auto-add on lesson open (keep it intentional/opt-in).
