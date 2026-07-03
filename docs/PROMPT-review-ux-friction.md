# PROMPT — Review-loop friction pass (mobile nav · Home entry card · grader UX · grounded questions · outcome chips)

Paste this whole file to the implementing agent. Read `CLAUDE.md` first — all its conventions apply
(one data path via `apiFetch`, no `Co-Authored-By` trailer, match existing style, verify before claiming done).
All five tasks are frontend-heavy; only Task 4 touches the backend, and it needs **no DB migration**.
Do the tasks in order; each is independently shippable.

Design constraint: the user owns pixel-level visual design. Reuse existing color utilities and
component patterns (`kinetic-btn`, `kinetic-card`, `glass-nav`, `skeleton`) so dark mode keeps working
for free — do NOT invent new palettes or restyle anything beyond what each task requires.

---

## Task 1 — Mobile bottom nav: 8 items → 5

**File:** `frontend/src/App.jsx` (mobile `<nav>` around line 228; desktop sidebar around line 108).

Current mobile nav: Home, Review, Log, Learn, Paths, Vault, Analytics, (+Admin) with `overflow-x-auto`
— it horizontally scrolls, which hides tabs and shrinks tap targets.

Target mobile nav (exactly 5, no overflow scrolling — remove `overflow-x-auto`):

1. **Home**
2. **Review** (keeps the `dueCount` badge)
3. **Log** — center position, rendered as a visually distinct "+" action (slightly larger / accent
   circle, like a docked FAB) rather than a plain tab. Same `navigate('/log')`.
4. **Learn**
5. **More** — opens a small sheet/popover (built inline in `App.jsx`, no new dependency) listing:
   Career Paths, Vault, Analytics, and Admin (Admin only when `isAdmin`). Each item navigates and
   closes the sheet. "More" shows active state when the current tab is any of those four.

Do NOT touch: the desktop sidebar (keep all items), the profile button in the top-right mobile
header (stays as-is), the desktop FAB.

**Verify:** run the frontend, viewport 375px — 5 evenly spaced items, no horizontal scroll, More sheet
opens/closes, every route still reachable, active states correct (including More-child routes), Admin
hidden for non-admin. Check dark mode.

---

## Task 2 — Home: "Continue learning" / "Start learning" card

**Files:** `frontend/src/Home.jsx`; data from `GET /api/roadmaps/` (already returns `progress_pct` + `slug`).

Lessons are currently ~5 taps deep (nav → Learn → roadmap → flowchart node → Learn affordance).
Give Home a one-tap entry point:

- **Returning learner** (any roadmap with `0 < progress_pct < 100`): a **"Continue learning"** card
  showing the most-progressed in-progress roadmap (title + progress bar + `progress_pct`). Tapping it
  goes to that roadmap's detail (`/roadmaps/<slug>`). If you can cheaply compute the next uncompleted
  node **that has lesson content**, deep-link to `/roadmaps/<slug>/learn/<lesson-slug>` instead —
  investigate how `RoadmapDetail.jsx` decides a node "has content" (there is a Learn affordance on
  such nodes) and reuse that exact mechanism; do not invent a second mapping. If that mapping is
  only resolvable inside RoadmapDetail, linking to the roadmap is acceptable for v1.
- **New user** (no roadmap progress at all): a **"Start learning"** card listing ONLY roadmaps that
  actually have lesson content. Source of truth: the content folders synced to
  `frontend/public/content/roadmaps/<key>/` (currently `python-swe`, `sql`, `aptitude`, `core-cs`,
  `dsa`). Check whether `sync-content.mjs` emits an index/manifest; if yes consume it, if not have
  it also emit a tiny `index.json` of roadmap keys (keep the script change minimal). Match keys
  against the `slug` field from `GET /api/roadmaps/` and render those roadmaps (title + short
  description) linking to `/roadmaps/<slug>`. Never show a lesson-less roadmap here.

Placement: prominent, near the top of Home — but do not displace the due-reviews call-to-action
when reviews are due (reviews stay the #1 action; learning is #2). Reuse existing Home card styling
and add a matching skeleton while loading.

**Verify:** with a progressed account → Continue card with correct roadmap; with a fresh account
(or mock empty progress) → Start card listing only content roadmaps; links navigate correctly.

---

## Task 3 — Review: make the AI grading state unmistakable

**File:** `frontend/src/Review.jsx`.

Problem: after "Reveal answer", the grade request fires in the background but the UI barely signals
it — the "AI feedback" box with "Grading your recall…" is easy to miss, appears below the fold on
mobile, and when the result lands the "Suggested" ring pops in with no transition, shifting layout
under the user's thumb.

Changes:

1. **Reserve the AI-feedback box from the instant of reveal** whenever a grade call is in flight
   (`grading === true`): render the box immediately with a shimmer/skeleton body (reuse the
   `skeleton` utility) and an animated indicator (pulsing Sparkles icon or equivalent) + label like
   "Checking your recall…". The box must not appear/disappear or change height jarringly when the
   result arrives — reserve approximate space and fade the content in.
2. **Suggested chip:** when the grade lands, animate the "Suggested" ring/badge in (fade/scale, no
   layout shift on the chip row). While grading is in flight, show a subtle inline hint near the
   "How did it go?" heading — e.g. a small muted "AI is checking…" spinner-text — that disappears
   when the result lands or the call fails. The user must never be blocked from rating manually.
3. **Failure path stays silent-ish:** on grade failure keep current behavior (no error banner), but
   collapse the reserved box gracefully instead of leaving a dead shimmer.
4. **Mobile ordering fix (part of this task):** post-reveal, the rating chips must be reachable
   without scrolling past everything. Reorder the post-reveal footer stack to:
   AI feedback box → honesty `Hint` → "How did it go?" + chips → **"Worth exploring next"
   (related subtopics) moves BELOW the chips** (it's post-decision content — it must not delay the
   rating decision). Alternatively render subtopics only after the outcome is submitted, on a brief
   inter-card transition, if that's cleaner — implementer's call, but the chips move up either way.

**Verify:** with the grader live (it IS enabled in prod; locally set `GRADER_ENABLED=true` +
`GROQ_API_KEY` in `backend/.env`), run a review: reveal → shimmer box appears instantly → result
fades in → Suggested badge animates → no layout jump. Kill the backend mid-grade to check the
graceful-collapse path. Check at 375px width that chips are visible without deep scrolling.

---

## Task 4 — Grounded recall questions (stop the generic questions)

Two sub-parts. The complaint: LLM-generated questions feel generic. Lesson-sourced cards already
have a hand-authored question bank we're ignoring.

### 4a — Lesson cards: use the lesson's own `recall_questions` (no LLM for generation)

Lesson content JSONs (`content/roadmaps/<key>/<slug>.json`, synced to
`frontend/public/content/...`) contain `recall_questions: [{q, answer, tier}]` (see
`content/roadmaps/dsa/merge-sort.json:162` for the shape; confirm which `kind`s have it via
`content/validate.py`). Cards created by the lesson "Add to reviews" bridge have
`source_type === 'lesson'` and `activities.node_id` set.

In `Review.jsx`, when the current card is a lesson card:

- **Skip the `POST /api/reviews/{id}/questions` LLM call.** Instead resolve the card's lesson JSON
  and use its `recall_questions` (prefer 2–3: take `tier1` first, then fill from the next tier) as
  the question-mode questions.
- **Resolution path:** you need roadmap key + lesson slug from `node_id`. Investigate how the
  "Add to reviews" button in `LessonView.jsx` and the node→content mapping in `RoadmapDetail.jsx`
  work, and reuse that. If the `/api/reviews/due` payload's eager-loaded activity doesn't carry
  enough to resolve the content file (e.g. it has `node_id` but not the node's slug/roadmap slug),
  extend the **response schema** of `GET /api/reviews/due` (backend: `schemas/` + the route in
  `api/routes/reviews.py`) to include the node's lesson slug + roadmap slug for lesson cards.
  Schema/query change only — no migration.
- **Reveal:** under each question, show the lesson's canonical `answer` (labelled e.g. "Lesson
  answer") alongside the user's attempt — the lesson is ground truth, no LLM needed to reveal.
- **Grading:** still call `POST /api/reviews/{id}/grade-questions` for the advisory recalled/missed
  suggestion, but pass the canonical answers along as reference. Backend: extend the
  `grade-questions` request schema with an optional `reference_answer` per item and, when present,
  have `grade_question_set()` in `backend/app/services/grader.py` grade each answer against its
  reference answer (in addition to `key_memory`). Keep it backward-compatible (field optional).
- **Fallback:** if the content JSON can't be fetched/parsed, fall back to the existing LLM
  question flow, then free recall — never a broken card.

### 4b — Non-lesson cards: sharpen the LLM prompt

In `backend/app/services/grader.py`, `generate_questions()`:

- Include the activity's `notes` and `mistake` (when present) in the prompt alongside `topic` +
  `key_memory` — currently the questions only see the key memory, which is why they feel thin.
- Tighten the instruction toward **retrieval-forcing specificity**: each question must target a
  distinct concrete claim in the captured material ("Why does X…", "What happens when Y…",
  "How would you…"), never a generic "Explain <topic>" or definition-recital. Add: if the captured
  material only supports one good question, return one — do not pad to 3 with filler.
- Keep the existing hard rule: answerable solely from the captured material, no un-captured trivia.
- If there's a prior `mistake`, one question SHOULD probe exactly that failure point (best
  retrieval-practice target we have).

**Verify 4a:** complete a lesson's "Add to reviews", make its review due (locally, update
`scheduled_for` in the DB or temporarily create it due), open Review → the lesson's own questions
appear with no `/questions` network call (check devtools); reveal shows canonical answers; grading
still returns a suggestion. Break the content URL → confirm fallback.
**Verify 4b:** with the grader on, review a hand-logged card that has notes + mistake → questions
reference the specific claims/mistake, not generic topic definitions.

---

## Task 5 — Outcome chips: kill the Easy-vs-Good confusion

**File:** `frontend/src/Review.jsx` (the `OUTCOMES` array + chip grid).

Do NOT reduce to fewer than 4 outcomes — FSRS uses the 1–4 grade (Again/Hard/Good/Easy) and the
Easy/Good distinction affects scheduling. Fix it with meaning, not fewer buttons:

1. **Descriptor line under each label** (small muted text inside the chip):
   - Missed it — "Couldn't recall it"
   - Hard — "Barely pieced it together"
   - Good — "Got it with some effort"
   - Easy — "Instant — no effort"
2. **Visual grouping on the recalled axis:** "Missed it" reads as one group; Hard/Good/Easy read as
   the "got it" group (e.g. a hairline divider or slight gap in the grid — keep it subtle, reuse
   existing colors). The primary mental question becomes "did I get it?", then "how hard was it?".
3. **Frame the consequence, not the feeling:** replace the current honesty `Hint` copy with a
   one-liner that explains the mechanic in scheduling terms, e.g. "Easy = you won't see this for
   weeks · Good = normal spacing · Hard = comes back soon · Missed = back tomorrow." (Wording can
   be tuned; the point is each chip states its scheduling consequence so choosing stops being a
   judgment call about feelings.) You may fold the per-chip consequence into the descriptor line
   instead of the Hint if it reads better at 375px — implementer's call, but don't show the same
   information twice.
4. Keep: keyboard shortcuts 1–4, the AI "Suggested" badge, hover fills, 2×4 / 2×2 grid responsive
   behavior (descriptors must not break the 2-col mobile grid — test at 375px).

**Verify:** at 375px and desktop widths, chips render with descriptors, no overflow/wrap breakage,
suggested badge still positions correctly, ratings still submit and advance the queue.

---

## Done criteria (whole pass)

- `cd frontend && npm run build` passes.
- Backend: `POST /api/reviews/{id}/grade-questions` remains backward-compatible (old request body
  still validates); no Alembic migration created.
- Manually walk the loop once at mobile width: Home → (Start/Continue learning card visible) →
  Review → answer → reveal (visible grading state) → rate (clear chips) → done screen.
- Update `CLAUDE.md`'s status section with one line summarizing what shipped (match its style).
