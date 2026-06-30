# Hover-to-Explain Glossary — Implementation Spec

**Feature:** in a lesson, genuinely-hard words get a subtle dotted underline. Hover (desktop) or
tap (mobile) → a small card pops up with a **plain, beginner-friendly** definition **and an example
taken from THIS lesson's own algorithm/topic** — never a random unrelated example.

**Scope:** **every roadmap, every lesson kind** (`content/roadmaps/**/*.json` — python-swe, sql,
aptitude, core-cs, ai-engineering, dsa, …). The mechanism is roadmap- and kind-agnostic; the authored
entries are per-lesson. **Build + verify the mechanism on the DSA roadmap first, then author entries
across all roadmaps.**

**Audience for the writing:** a first-year student from a tier-3 college with weak vocabulary must be
able to understand every definition. Short sentences, no jargon used to explain jargon.

---

## Division of labour

| Piece | Owner | What |
|---|---|---|
| 1. Schema field | code | add optional `glossary` to a lesson |
| 2. Validator | code | `content/validate.py` accepts + checks `glossary` |
| 3. Popover component + auto-linker | code (frontend) | `GlossaryTerm` + `linkifyGlossary`, wired into `LessonView.jsx` |
| 4. The entries | **authoring (Antigravity)** | write the `glossary` array per DSA lesson |

Build 1–3 first and verify with ONE hand-written glossary, **then** bulk-author 4 across DSA lessons.
(Per project convention the frontend is normally Claude's; if implementing the whole thing via
Antigravity, this doc gives everything needed.)

---

## 1. Data model — the `glossary` field

Add an **optional** top-level array `glossary` to a lesson JSON. Each entry:

```json
"glossary": [
  {
    "term": "pointer",
    "definition": "A variable that holds the POSITION of an item (an index or memory address) instead of the item itself, so you can jump straight to it.",
    "example": "In the merge step we keep one pointer on each sorted half and compare the two values they point at."
  },
  {
    "term": "invariant",
    "definition": "A fact that stays TRUE at every step of the algorithm. If it ever breaks, the algorithm is wrong.",
    "example": "In binary search the invariant is: if the target exists, it is always inside the current [lo, hi] window."
  }
]
```

Field rules:
- **`term`** (required, string): the exact word/phrase to make hoverable. Must appear **verbatim** in
  the lesson's prose (case-insensitive) so it can be matched. Prefer the singular/base form.
- **`definition`** (required, string): plain English, **≤ 240 chars**, 1–2 short sentences. Do NOT use
  the term inside its own definition (no circular definitions).
- **`example`** (optional, string, **≤ 200 chars**): MUST be grounded in **this lesson's topic**. In
  `merge-sort` use the merge step; in `binary-search` use lo/hi/mid; in `prefix-sums` use the running
  total. If a natural topic example doesn't exist, omit `example` rather than invent a generic one.

---

## 2. Validator — `content/validate.py`

`glossary` is **optional**; when present, validate (these are the gate, fail the build on violation):
- it is a list;
- each entry is an object with a **non-empty string `term`** and **non-empty string `definition`**;
- `example`, if present, is a string;
- `term`s are **unique** within a lesson (fail on duplicate term).

Soft **warning** (don't fail): a `term` that does not appear (case-insensitive, word-boundary) in any
of the lesson's text fields — it would never render, so flag it. Reuse the existing `[warn]` style.

Applies to every `kind` (the field is generic); for this rollout only DSA lessons will carry it.

---

## 3. Frontend

### 3a. `GlossaryTerm.jsx` (the popover)
A small, accessible popover trigger.

- Renders its children (the matched word) with a **dotted underline** + a faint accent colour, cursor
  help.
- **Desktop:** show the card on `mouseenter` / `focus`, hide on `mouseleave` / `blur`.
- **Mobile / touch:** tap toggles the card; tapping elsewhere (outside click) or `Esc` closes it.
- **Accessibility:** the trigger is a `<button type="button">` (focusable, keyboard-openable);
  `aria-expanded`; the card has `role="tooltip"`.
- **The card:** a light, rounded, shadowed box (match `kinetic-card` / the existing app card style),
  max-width ~320px, positioned above the word by default and flipped below if it would clip the top.
  Contents: the **definition**, then (if present) an **Example** line, visually separated and labelled.
  No layout shift — the card is absolutely positioned / portaled, not inline-flow.

Props: `{ term, definition, example, children }`.

### 3b. `linkifyGlossary(text, terms, used)` (the auto-linker)
Given a plain string and the lesson's glossary, return an array of strings + `<GlossaryTerm>` nodes:
- Match the **first occurrence only** of each term across the whole lesson (track matched terms in a
  shared `used` Set passed across fields, so a term is linked once per lesson, not in every paragraph).
- Match **case-insensitively** on a **word boundary** (`\b` + escaped term) so `pointer` doesn't match
  inside `pointers`/`endpoint`. Preserve the original casing of the matched text in the output.
- Sort terms **longest-first** so multi-word terms (e.g. "load factor") win over a contained word.
- Return plain strings untouched where there's no match (so React renders them normally).

Provide a thin wrapper component `GlossaryText({ children, terms, used })` that runs `linkifyGlossary`
on the string child, for ergonomic use in JSX.

### 3c. Wire into `LessonView.jsx`
- Read `lesson.glossary` (default `[]`); create one `used = new Set()` per render and thread it through
  so each term links once across the whole lesson.
- Wrap the **teaching prose** wherever it renders, across **all kinds**: `overview.what|why`,
  `why_it_exists.*`, `why_learning_this[]`, `mental_model.intuition|description`, `analogy`,
  `explanation`, `method`, `formula` (its text), `worked_example` prose, `sections[].body`,
  `key_points[].detail`, `common_mistakes[].explanation`. (Some fields only exist on some kinds —
  apply where present.)
- **Do NOT** linkify: code blocks / `CodeTrace` / `code_walkthrough` / `query_walkthrough` /
  `viz` captions / `recall_questions` & `oa_questions` answers / `understanding_checks` answers.
- **Principle:** linkify the parts that **teach**, never the parts that **test** or **run**.
- If `glossary` is empty, output is byte-for-byte the current behaviour.

---

## 4. Authoring contract (Antigravity) — the `glossary` entries

For **every lesson in every roadmap** (`content/roadmaps/<roadmap>/<slug>.json`), add a `glossary`
array. The example must come from **that lesson's own topic** — a `pointer` in a Python lesson uses a
Python example, in SQL a SQL example, in DSA the algorithm at hand:
1. Pick **3–8 genuinely hard words** a beginner wouldn't know — real jargon: *pointer, invariant,
   in-place, amortized, recursion, pivot, stable sort, auxiliary space, load factor, prefix, monotonic*,
   etc. **Do not** gloss everyday words.
2. **Definition:** simple, short, concrete. Explain like the reader has never coded. No circular
   definitions; no jargon-to-explain-jargon.
3. **Example:** from **this lesson's own algorithm/topic only.** This is the whole point — a `pointer`
   example in `merge-sort` is the finger walking each sorted half; in `linked-list` it's the address of
   the next node; in `binary-search` it's lo/hi/mid. Never paste a generic example from elsewhere.
4. The `term` must appear **verbatim** in the lesson prose (otherwise it won't render — the validator
   warns).
5. Validate: `python content/validate.py` must end `All content valid. [OK]`, then
   `cd frontend && node scripts/sync-content.mjs`.

---

## 5. Acceptance criteria
- A DSA lesson with a `glossary` shows dotted-underlined terms in the prose; hover/tap shows a card
  with the definition + (where given) a topic-specific example.
- Each term is linked **once** per lesson (first occurrence), never inside code or recall answers.
- Keyboard-accessible (Tab to focus, Enter/Space opens, Esc closes); works on touch; no layout shift.
- Lessons **without** `glossary` are visually unchanged.
- `validate.py` passes; duplicate terms fail; missing-in-text terms warn.

---

## 6. Suggested build order
1. Add `glossary` to `validate.py` (+ the soft warning).
2. Build `GlossaryTerm.jsx` + `linkifyGlossary`.
3. Wire into `LessonView.jsx` for the prose fields.
4. Hand-author a `glossary` on **one** lesson (e.g. `merge-sort.json`), sync, verify the popover on
   `/roadmaps/dsa/learn/merge-sort`. Spot-check one lesson of a **different kind** (e.g. a `concept`
   python lesson, an `aptitude` lesson) so the prose-field wiring is confirmed across kinds.
5. Bulk-author `glossary` across **all DSA lessons, then all other roadmaps** (Antigravity).
