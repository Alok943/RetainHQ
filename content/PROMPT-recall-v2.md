# Handover — recall_questions v2 upgrade pass (ALL roadmaps)

> Paste the fenced block below into the agent (Antigravity), one roadmap at a time. This is
> an ENRICH pass, not a regeneration: every existing `q`/`answer`/`tier` stays byte-for-byte
> unless you are explicitly adding a NEW tier the lesson is missing. You are ADDING optional
> fields (`format`, `context`, `hint`, `options`) to existing items and appending new items to
> fill gaps — never deleting or rewording an existing `answer`.
>
> Parent doc: `docs/IMPLEMENTATION-quiz-capture-v2.md` Step 3 (D-075). Validator:
> `content/validate.py` (validates these fields when present — old items are untouched and
> still valid). Coverage: `python content/validate.py --v2-coverage`.

---

## Why this exists

Quiz v2 (the review experience) serves **one question per card**, mostly as **think-first
MCQ** — question shown, options hidden until revealed, auto-graded, no rating buttons. Free
recall works for a typed question; it cannot power an MCQ, because an MCQ needs REAL wrong
answers with real explanations, not typed prose the reviewer used to self-grade. This pass is
what makes that possible: it gives each lesson enough tiered, some-MCQ, some-typed recall
items that Quiz v2 has something real to serve, for every card, without changing what earlier
free-recall reviews already asked.

## The shape (all fields except `q`/`answer`/`tier` are OPTIONAL)

```jsonc
{
  "q": "After partitioning around pivot 3, which is guaranteed?",
  "answer": "3 is at its final sorted index; everything left of it <= 3 <= everything right.",
  "tier": "tier1",                       // tier1 | tier2 | tier3 (unchanged meaning)
  "format": "mcq",                       // "mcq" | "typed" — which suits THIS question
  "context": { "type": "array", "values": [5, 2, 8, 1, 9, 3], "highlight": [5], "labels": {"5": "pivot"} },
  "hint": "Where must the pivot end up for the recursion to work?",
  "options": [                           // required when format = "mcq": EXACTLY 4, exactly 1 correct
    { "text": "3 is at its final index; left <= 3 <= right", "correct": true,  "why": "Partition places the pivot where it belongs in sorted order." },
    { "text": "The array is sorted",                      "correct": false, "why": "Only the pivot is final; both sides are still unsorted." },
    { "text": "The left half is sorted",                  "correct": false, "why": "Left holds smaller values, in any order." },
    { "text": "The pivot moves to index 0",               "correct": false, "why": "That describes a swap step in some schemes, not the guarantee." }
  ]
}
```

Context types (all DATA, no images — rendered by the EXISTING DSA/SQL renderers, never a new
visual system): `code {lang, source}` (keep `source` short — a glance, not a file, cap ~800
chars) · `array {values, highlight?, labels?}` (cap ~30 values) · `table {columns, rows}` or
`table {tables: [{name, columns, rows}, ...]}` for a 2-table join (cap ~12 rows/table, max 2
tables) · `tree {level_order}` · `graph {nodes, edges, directed}`.

## Rules (in priority order)

1. **Never delete or reword an existing `answer`.** You may add `format`/`context`/`hint`/
   `options` to an existing item, and you may APPEND brand-new items. You never remove one.
2. **Distractors come from REAL misconceptions.** The lesson's `common_mistakes` is the FIRST
   source — a common mistake IS a distractor waiting to happen. `understanding_checks` (the
   `find-bug`/`debug-misconception` ones especially) are the second source. Only invent a
   distractor from scratch when neither has enough material, and even then it must be a
   plausible wrong belief a real learner would hold — never a silly/obviously-wrong option.
3. **Exactly one correct option, exactly 4 options, every option gets its own `why`.** A
   distractor's `why` explains why THAT OPTION is wrong (or what it would take for it to be
   right) — it does not just repeat the correct answer. See the gold examples: a distractor's
   `why` names the specific misconception, the same way `common_mistakes[].explanation` does.
4. **`context` only when the question genuinely needs it to be answerable without the lesson
   open.** A question like "what is a race condition?" needs no context. A question like
   "after partitioning, where does the pivot end up?" is unanswerable without seeing the
   array — context is required there. If you add context, dry-run it: compute the actual
   correct answer from the context data yourself before writing the options.
5. **Per-lesson target:** at least 2 `tier1`, 2 `tier2`, 1 `tier3`, and at least 1 item with
   `format: "typed"` (open-ended questions — comparisons, "why", "what problem does X solve"
   — read as typed; recognition/behavior/data questions read as MCQ). Add NEW items to close
   whichever gap the lesson has; never force-convert everything to MCQ. Check with:
   `python content/validate.py --v2-coverage`.
6. **`hint` is optional and rare** — one line, used only when a question has a genuine "aha"
   nudge worth holding back (not a restatement of the question). Most items need none.
7. **tier3 = the edge case, not just "harder wording."** A good tier3 question changes an
   assumption the tier1/tier2 questions took for granted (duplicate values, an adversarial
   input, a boundary condition) and asks what actually happens — see the binary-search and
   closures gold examples below.

## Gold examples (read these three FIRST — each is a REAL item from a lesson already in the
catalog, already passing `validate.py` and the `mcq_items`/`answerable` evals in
`backend/evals/`)

**DSA** — `content/roadmaps/dsa/binary-search.json`, a tier3 item built on the lesson's own
`common_mistakes` (nothing here is invented — it's the natural next question after teaching
the loop invariant):

```jsonc
{
  "q": "If the array has duplicate values equal to the target, does this standard binary search guarantee finding the FIRST occurrence?",
  "answer": "No — it returns as soon as it hits any matching index, which could be any one of several equal values, not necessarily the leftmost one. Finding the first occurrence needs a modified 'lower bound' search that keeps narrowing right even after a match.",
  "tier": "tier3",
  "format": "mcq",
  "hint": "What does 'if arr[mid] == target: return mid' actually guarantee about WHICH matching index you get?",
  "options": [
    { "text": "No — it returns as soon as it finds any matching value, not necessarily the first one; a lower-bound search is needed for that", "correct": true, "why": "Standard binary search stops at the first match it happens to probe, which depends on the midpoint sequence, not on document order." },
    { "text": "Yes — binary search always finds the leftmost occurrence by definition", "correct": false, "why": "Standard binary search returns immediately on any match; nothing about the algorithm as shown biases it toward the leftmost index." },
    { "text": "Yes, because arrays cannot contain duplicate values", "correct": false, "why": "Nothing in this algorithm assumes distinct values — sortedness allows duplicates just fine." },
    { "text": "No — it will loop forever if duplicates exist", "correct": false, "why": "Duplicates don't break termination; the search window still shrinks by at least one element every iteration." }
  ]
}
```

**SQL** — `content/roadmaps/sql/inner-join.json`, a tier2 item that NEEDS context (the
question is meaningless without seeing the two tables), using a small self-contained table
pair instead of the shared `_dataset.sql` (so it's answerable standalone):

```jsonc
{
  "q": "Given these two tables, how many rows does an INNER JOIN on students.id = enrollments.student_id produce?",
  "answer": "3 rows — Ann matches twice (Math, Physics), Ben matches once (Math), and Cid has no enrollments so is dropped entirely.",
  "tier": "tier2",
  "format": "mcq",
  "context": { "type": "table", "tables": [ { "name": "students", "columns": ["id", "name"], "rows": [[1, "Ann"], [2, "Ben"], [3, "Cid"]] }, { "name": "enrollments", "columns": ["student_id", "course"], "rows": [[1, "Math"], [1, "Physics"], [2, "Math"]] } ] },
  "options": [
    { "text": "3", "correct": true, "why": "Ann contributes 2 matching rows (Math, Physics), Ben contributes 1 (Math), and Cid contributes 0 since he has no enrollments." },
    { "text": "2", "correct": false, "why": "That undercounts — Ann alone contributes 2 matching rows before Ben's row is even added." },
    { "text": "4", "correct": false, "why": "That would only be right if Cid's unmatched row were kept — INNER JOIN drops it entirely." },
    { "text": "6", "correct": false, "why": "That's closer to the full Cartesian product size, not the count of rows that actually satisfy the join condition." }
  ]
}
```

**Python** — `content/roadmaps/python-swe/closures.json`, a tier3 item whose distractors are
each a specific, real misconception about closures (shared state, shared scope, reset-on-call
— the exact family of bugs a learner who half-understands closures actually writes):

```jsonc
{
  "q": "Two counters are made with `c1 = make_counter()` and `c2 = make_counter()`. After calling `c1()` three times and `c2()` once, what does `c2()` return next?",
  "answer": "2 — each call to make_counter() creates its own independent `count` in its own closure. c1's three calls never touch c2's count, so c2's own count is just 1 (from its first call) before this next call, making the next result 2.",
  "tier": "tier3",
  "format": "mcq",
  "hint": "Does count live inside make_counter's scope (shared by all counters) or inside each counter's own call to make_counter?",
  "options": [
    { "text": "2 — each make_counter() call creates its own independent closure state, so c1's calls never affect c2's count", "correct": true, "why": "Every call to make_counter() sets up a brand-new `count` variable in a brand-new scope — the two counters never share state." },
    { "text": "5 — because count is shared across all counters created by make_counter", "correct": false, "why": "count is NOT shared — it lives inside each individual closure created by its own call to make_counter(), independent of any other." },
    { "text": "4 — because the closures share the same enclosing scope", "correct": false, "why": "Each invocation of make_counter() creates a brand-new scope with its own count; they don't share one enclosing scope." },
    { "text": "1 — because count resets every time c2 is called", "correct": false, "why": "count persists across calls to the SAME counter — it only starts fresh when make_counter() is called again to create a new counter." }
  ]
}
```

---

## THE GENERIC PASS (paste this block, substituting `{{ROADMAP_DIR}}`)

```
You are upgrading the `recall_questions` array of EXISTING lesson JSON files in
content/roadmaps/{{ROADMAP_DIR}}/ to the v2 recall-question contract. This is an ENRICH pass:
every existing q/answer/tier is preserved byte-for-byte. You are adding optional fields
(format, context, hint, options) to existing items and APPENDING new items to close tier/
format gaps — you never delete or reword an existing answer.

CONTRACT: content/PROMPT-recall-v2.md — read it in full, especially the three gold examples,
before touching any file. Where this block and that contract disagree, the contract wins.

PER-FILE TASKS:
1. Read the lesson's common_mistakes and understanding_checks first — they are your primary
   source for distractor material. A common mistake IS a distractor waiting to happen.
2. For each EXISTING recall_questions item: decide format. Open-ended "why"/"compare"/
   "what problem does X solve" questions become format: "typed" (no options needed). Concrete
   recognition/behavior/data questions become format: "mcq" — write 4 options, exactly one
   correct, every option gets a one-line why grounded in a real (mis)understanding.
3. Add context ONLY when the question is unanswerable without seeing data (an array/table/
   tree/graph/short code snippet). Dry-run the data yourself — compute the real answer before
   writing options. Keep context small (see size caps in the contract).
4. Check per-lesson coverage: >=2 tier1, >=2 tier2, >=1 tier3, >=1 typed. If the lesson is
   short a tier, APPEND a new item at that tier (never relabel an existing item's tier to
   fake coverage) — tier3 must be a genuine edge case (see the contract's rule 7), not just
   harder wording of an existing question.
5. hint is optional and rare — add one only where a question has a real "aha" nudge.

HARD CONSTRAINTS:
- Never change: slug, title, roadmap, kind, tier (the LESSON-level tier field, not a
  question's own tier), prerequisites, unlocks, sources.
- Never delete or reword an existing recall_questions[].answer. Appending is always fine.
- Exactly 4 options when format is "mcq"; exactly one "correct": true; every option has a
  non-empty "why". No option may be a joke/nonsense filler — every distractor must be a
  plausible wrong belief.
- Valid JSON after every edit. \n for newlines inside strings, quotes escaped.

VALIDATE after every batch (from repo root):
  python content/validate.py
  python content/validate.py --v2-coverage

WORK ORDER: alphabetical, batches of ~10 files. After each batch, report: files done, which
tier/format gap each file closed, files where you were unsure about a distractor's
plausibility. Do not commit — leave the working tree for review.

DEFINITION OF DONE per file: validate.py green; --v2-coverage shows this lesson meeting the
target (>=2 tier1, >=2 tier2, >=1 tier3, >=1 typed); every MCQ distractor traces to a real
misconception (common_mistakes, an understanding_check, or a clearly plausible wrong belief).
```
