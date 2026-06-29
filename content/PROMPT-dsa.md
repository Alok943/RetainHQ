# DSA lesson generation — PROMPT (Antigravity authoring contract)

> **North star (same as every roadmap):** *"Can the learner explain AND apply this in an interview 30
> days later?"* DSA — Algorithms Visualized teaches **computational thinking, not memorization**.
> Every lesson must let the reader answer the **FIVE questions**:
> 1. **Why does this exist?** (the problem; what was wrong with the naive way)
> 2. **How do I mentally simulate it?** (the intuition/analogy + the one repeated decision)
> 3. **What invariant / repeated decision makes it work?** (what stays true each step)
> 4. **Where is it used in real systems?** (the engineering problem — NOT "Company X uses it")
> 5. **How do I recognize when to apply it?** (the pattern + recognition cues)

You author **one JSON per node** for the `dsa` roadmap. Topics, slugs, and the kind of each node are
in **`content/_TODO-dsa.md`**. Your **input** is the Gemini deep-research JSON (one object per topic,
produced from `content/PROMPT-dsa-research.md`) — convert each research object into a shippable lesson.
Write to `content/roadmaps/dsa/<slug>.json` (filename = slug). Validate with
`python content/validate.py`; tick the box in the TODO once saved **and** green.

---

## ⛔ THE BOUNDARY — you do NOT author the visualization

Visualization is **Claude's job**, not yours. For EVERY node:
- **Do NOT write a `viz` field.** (Claude adds it + builds the execution-trace generator in
  `frontend/src/dsa/`. It is optional in the schema, so the lesson validates fine without it.)
- **Do NOT write `animation` blocks** (no `sequence`/`cycle`/`vector-space`), and **no `image` /
  `illustration`** anywhere. Claude layers all visuals afterward.
- If you use `sections` (allowed for `dsa`-kind teaching body), write **text-only** sections
  (`body` + optional `recap`). No `image`, no `animation` inside a section.

Your job is the **prose + recall + questions** — everything that *teaches and tests*. Claude makes it
move.

---

## TWO KINDS in this roadmap (the TODO tells you which per node)

DSA mixes two lesson kinds deliberately. **Use the kind tagged in `_TODO-dsa.md`** — it decides the
required fields.

### A) `kind: "concept"` + `runtime: "none"` — for IDEAS explained with words
The meta/conceptual nodes: *What is an algorithm?, Big-O, Common complexities, Amortized analysis,
Recursive tree thinking, the call stack, Why greedy works/fails, the DP-thinking nodes, Algorithm
Design Patterns recognition*, etc. These are **the same shape as the 3 finished Foundations lessons** —
study them as your exemplars:
- `content/roadmaps/dsa/what-is-an-algorithm.json`
- `content/roadmaps/dsa/tracing-state-and-invariants.json`
- `content/roadmaps/dsa/iteration-and-traversal.json`

Required fields (concept branch of `validate.py`): `overview {what, why}`, `why_learning_this` (list),
`common_mistakes` (list of `{title, explanation}`), `recall_questions` (list of `{q, answer, tier}`),
`practice_tasks` (list), `understanding_checks` (**≥2**, each `{type, question, answer, why}` where
`type` ∈ `predict-output | predict-result | explain-behavior | find-bug | choose-model |
debug-misconception`), `sources` (list of URLs). **Optional** `aha_moment {code, prediction,
common_guess, why}` — its `code` is illustrative only (NOT executed; `runtime` is `none`), great for a
predict-before-reveal hook. Optional `challenge {title, prompt}`. **Set `runtime: "none"`** (no
`code_walkthrough`).

### B) `kind: "dsa"` — for ALGORITHMS you step through
Merge sort, BFS, binary search, sliding window, backtracking, Dijkstra… A trace exists, so Claude will
attach a visualizer. **You still write the full prose lesson; just omit `viz`.**

Required fields (dsa branch of `validate.py`):
- `mental_model` — object with a non-empty **`intuition`** one-liner (+ `description`, `repeated_decision`).
- `why_it_exists` — object with **`problem`** and **`better_idea`** (`naive_solution` optional).
- `sections` **OR** `explanation` — the teaching body (text-only sections, or a multi-paragraph string).
- `common_mistakes` — list of `{title, explanation}` (≥1).
- `recall_questions` — **≥3**, each `{q, answer, tier}`.
- `oa_questions` — **≥2**, each `{question, answer}` (+ `approach`, `company` honest-category).
- `sources` — non-empty list of real URLs.

Optional (author when the research supports it — these carry the five-questions depth):
`when_not_to_use [{scenario, reason}]`, `failure_signals [str]`, `engineering_examples [{title,
problem?, why_this_algorithm}]`, `pattern {name, recognition_cues?}`, `related [slug]`,
`interesting_facts [str]`, `practice [{title, url, difficulty?, why?}]`, `key_points [{title, detail}]`,
`hook {scenario, question?}`.

---

## RESEARCH → LESSON field mapping (kind `dsa`)

The Gemini research object maps almost 1:1. Synthesize, don't copy:

| research field | → lesson field |
|---|---|
| `slug`, `title` | `slug`, `title` (must match the TODO + filename) |
| `why_it_exists` | `why_it_exists` (keep `problem` + `better_idea`) |
| `mental_model` | `mental_model` (intuition + description + repeated_decision) |
| `invariants` | fold into `mental_model.description` or a `key_points` entry |
| `complexity` | a `key_points` entry, or a line in the teaching body |
| `common_mistakes` | `common_mistakes` |
| `when_not_to_use` / `failure_signals` | same names |
| `engineering_examples` | `engineering_examples` |
| `pattern` | `pattern` |
| `related` | `related` |
| `interesting_facts` | `interesting_facts` |
| `practice` | `practice` (link only — never paste problem text) |
| `interview_questions` | seed `oa_questions` (≥2) |
| (write fresh) | `recall_questions` (≥3 — the spaced-repetition probes) + the `sections`/`explanation` body |
| `visualization` | **ignore — Claude's input, not a lesson field** |
| `sources` | flatten `{primary, secondary}` → one `sources` URL list |

---

## `kind: "dsa"` template (emit these fields, viz OMITTED)

```json
{
  "slug": "binary-search",
  "title": "Binary Search",
  "roadmap": "dsa",
  "kind": "dsa",
  "tier": "tier1",
  "metadata": {
    "difficulty": "easy",
    "estimated_minutes": 15,
    "importance": 10,
    "interview_frequency": "high",
    "prerequisites": ["common-complexities"],
    "unlocks": ["lower-bound", "upper-bound", "binary-search-on-the-answer"]
  },
  "hook": {
    "scenario": "You're guessing a number 1-100 and each guess returns 'higher' or 'lower'. Guessing 1, 2, 3... could take 100 tries.",
    "question": "What's the fewest guesses that ALWAYS works, no matter the number?"
  },
  "why_it_exists": {
    "problem": "Finding a value in a sorted array by scanning is O(n) — wasteful when the data is already ordered.",
    "naive_solution": "Linear search checks every element left to right.",
    "better_idea": "Use the sortedness: check the middle, then throw away the half that can't contain the target. Each step halves the search space, so it finishes in O(log n)."
  },
  "mental_model": {
    "intuition": "Halve the haystack every guess: look in the middle, discard the impossible half.",
    "description": "Keep a [lo, hi] window that always contains the answer if it exists. Compare the middle to the target; move lo or hi so the window shrinks but the invariant holds. When the window is empty, the target wasn't there.",
    "repeated_decision": "Is the middle element less than, greater than, or equal to the target?"
  },
  "key_points": [
    { "title": "Invariant", "detail": "If the target exists, it is always inside [lo, hi]. Every step preserves this while shrinking the window." },
    { "title": "Complexity", "detail": "O(log n) time, O(1) space. log2(n) halvings to reach a single element." },
    { "title": "Precondition", "detail": "The array MUST be sorted on the key you search." }
  ],
  "common_mistakes": [
    { "title": "Overflow in mid = (lo + hi) / 2", "explanation": "In fixed-width integer languages lo + hi can overflow; use lo + (hi - lo) / 2." },
    { "title": "Wrong loop boundary", "explanation": "Mixing up while (lo < hi) vs while (lo <= hi) and the matching hi = mid vs hi = mid - 1 causes off-by-one or infinite loops. Pick one convention and keep the invariant consistent." }
  ],
  "when_not_to_use": [
    { "scenario": "Unsorted data", "reason": "Sorting first is O(n log n) — for a single lookup, a linear scan is cheaper." },
    { "scenario": "Linked lists", "reason": "No O(1) random access to the middle, so the log-n advantage disappears." }
  ],
  "failure_signals": [
    "You're scanning a SORTED array element by element.",
    "The problem says 'find the minimum X such that condition(X) is true' over a monotonic range."
  ],
  "engineering_examples": [
    { "title": "Database B-tree lookups", "problem": "Find a row by key among millions on disk.", "why_this_algorithm": "B-trees are a multiway generalization of binary search — each node read discards most of the remaining keys." }
  ],
  "pattern": { "name": "Binary search / halving", "recognition_cues": ["sorted input", "monotonic predicate", "O(log n) target hinted by constraints up to 1e9"] },
  "recall_questions": [
    { "q": "What precondition does binary search require?", "answer": "The array must be sorted on the search key.", "tier": "tier1" },
    { "q": "Why is binary search O(log n)?", "answer": "Each comparison discards half the remaining elements, so it takes log2(n) steps to narrow to one.", "tier": "tier1" },
    { "q": "State the loop invariant that makes it correct.", "answer": "If the target exists, it always lies within the current [lo, hi] window; each step shrinks the window while keeping that true.", "tier": "tier2" }
  ],
  "oa_questions": [
    { "question": "Find the first index where a value could be inserted to keep an array sorted.", "company": "SDE interview", "answer": "A lower-bound binary search: shrink toward the first element not less than the target.", "approach": "Recognize it as binary search on a monotonic predicate, not exact-match search." },
    { "question": "Search a rotated sorted array in O(log n).", "company": "SDE interview", "answer": "At each step one half is still sorted; decide which half can contain the target and recurse there.", "approach": "Adapt the invariant: the answer is in the provably-sorted half." }
  ],
  "practice": [
    { "title": "Binary Search", "url": "https://leetcode.com/problems/binary-search/", "difficulty": "easy", "why": "the bare mechanic" },
    { "title": "Search Insert Position", "url": "https://leetcode.com/problems/search-insert-position/", "difficulty": "easy", "why": "lower-bound variant" },
    { "title": "Find Minimum in Rotated Sorted Array", "url": "https://leetcode.com/problems/find-minimum-in-rotated-sorted-array/", "difficulty": "medium", "why": "invariant transfer" }
  ],
  "related": ["lower-bound", "upper-bound", "binary-search-on-the-answer", "merge-sort"],
  "interesting_facts": ["Knuth noted that although the idea is simple, the first bug-free binary search wasn't published until years after the algorithm — boundary handling is genuinely tricky."],
  "sources": [
    "https://en.wikipedia.org/wiki/Binary_search_algorithm",
    "https://www.geeksforgeeks.org/binary-search/"
  ]
}
```

> **Note:** `merge-sort` is the canonical `dsa` gold exemplar and is authored by **Claude** (it's the
> reference the trace generator is keyed to). **Skip `merge-sort` in the TODO** — don't author it.

---

## FIELD RULES (both kinds)
- **`slug` must equal the TODO slug AND the filename.** They are derived from the node title by the
  frontend `slugifyTitle` (`&`→`and`, `/`→space, drop other punctuation, kebab-case). Don't invent new
  slugs — copy from the TODO.
- **`metadata.importance`** = int 1–10. **`interview_frequency`** ∈ `low|medium|high`, judged from
  AGGREGATE evidence (NeetCode/Blind-75/Striver inclusion, LeetCode tag frequency) — **not** company
  folklore. **`prerequisites`/`unlocks`** = slugs of OTHER dsa nodes (use the TODO slugs; unresolved
  refs are warnings, not errors, while curating).
- **`recall_questions`** = the spaced-repetition probes — short, one-fact each, an interviewer's
  phrasing. tier1 = state it, tier2 = apply/compare.
- **`practice` / `practice_tasks`** = tie to the PATTERN so skills transfer; **link only, never paste
  problem statements.**
- **`sources`** = 2–5 real authoritative URLs actually consulted (Wikipedia/CLRS/official docs +
  GfG/quality blogs). No fabricated links.
- **NEVER copy** sentences from GfG/Wikipedia/any source — read, understand, write ORIGINAL prose.
  Cite in `sources`.
- Blank-line-separate paragraphs inside long strings; use single quotes inside strings so they nest in
  JSON.

## QUALITY BAR (check before saving each node)
1. Could a beginner answer all **FIVE questions** from this lesson alone?
2. Does `mental_model.intuition` make it feel **obvious** (a picture, not a definition)?
3. Are `recall_questions` what an **interviewer** actually asks — and answerable from the lesson?
4. For `dsa` nodes: is `why_it_exists` a real *naive-was-slow → better-idea* story, not a restatement?
5. No `viz`, no `animation`, no `image` anywhere. (Claude's layer.)

## RUN
```
python content/validate.py          # must end "All content valid. [OK]"
cd frontend && node scripts/sync-content.mjs
```
Then a node renders at `/roadmaps/dsa/learn/<slug>` (the static lesson page renders without the backend;
the roadmap detail page needs `seed_dsa.py` run on the DB to link nodes → lessons).
