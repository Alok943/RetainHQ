# Curation queue — Aptitude Phase 2: Logical Reasoning + Verbal (`aptitude`, `kind: "reasoning"`)

> **For Antigravity.** Generate **one JSON per node** using **`PROMPT-reasoning.md`** (NOT the quant
> or python/sql prompt). `kind: "reasoning"`, method + worked-example shape — **no formula, no
> discovery**. Files go in `content/roadmaps/aptitude/<slug>.json` (same folder as quant; only `kind`
> differs). Reference exemplar: `content/roadmaps/aptitude/blood-relations.json` (validated).
> Validate with `python content/validate.py`; tick a box once saved **and** green.

Source of truth for topics: `backend/seed_aptitude.py` (Logical Reasoning + Verbal Ability nodes).

---

## Priority order (evidence-led — generate top-down)
The JD research (`docs/jd-research-run1.md`) backs **Logical Reasoning** as part of the round-1 OA
screen ("Quants & Logical"). **Verbal is weakly evidenced** for the target roles (DA/SDE/Backend) —
it's a mass-recruiter English-section thing. So: **Logical Reasoning first; Verbal second; Vocabulary
last (and optional).** Don't sink effort into verbal before logical is done.

## Batch A — Logical Reasoning (11) — BUILD FIRST
- [x] Syllogisms  →  `syllogisms`
- [ ] Blood relations  →  `blood-relations`  *(exemplar — already done; skip)*
- [x] Coding–decoding  →  `coding-decoding`
- [x] Analogy & classification  →  `analogy-classification`
- [x] Direction sense  →  `direction-sense`
- [x] Linear & circular seating  →  `seating-arrangements`
- [x] Puzzles (floors / boxes / scheduling)  →  `puzzles`
- [x] Clocks & calendars  →  `clocks-calendars`
- [x] Number & letter series  →  `series-reasoning`  *(NOT `series-progressions` — that's the quant one)*
- [x] Statements: assumptions & conclusions  →  `assumptions-conclusions`
- [x] Data sufficiency  →  `data-sufficiency`

## Batch B — Verbal Ability strategy (5) — SECOND
- [x] Reading comprehension  →  `reading-comprehension`
- [x] Sentence correction & grammar  →  `sentence-correction`
- [x] Error spotting  →  `error-spotting`
- [x] Para jumbles  →  `para-jumbles`
- [x] Critical reasoning  →  `critical-reasoning`

## Batch C — Vocabulary (3) — LAST / optional (recall-heavy; weak as standalone lessons)
- [ ] Synonyms & antonyms  →  `synonyms-antonyms`
- [ ] Idioms & phrases  →  `idioms-phrases`
- [ ] Fill in the blanks  →  `fill-in-the-blanks`

---

## Notes
- **Slug collision resolved:** the quant "Number & letter series" is `series-progressions`
  (`kind: "aptitude"`); the logical one here is `series-reasoning` (`kind: "reasoning"`). Both live in
  the `aptitude` folder — distinct slugs, no clash.
- **Prereqs:** reasoning topics are largely independent (no DAG spine like quant). Leave
  `prerequisites: []` unless a topic genuinely builds on another (e.g. `puzzles` after
  `seating-arrangements`).
- **Renderer:** the `LessonView` `kind: "reasoning"` renderer is a Claude-side task (same as the
  aptitude renderer). Lessons validate & store before it exists; they just won't display until it ships.
- **`company` tags = honest exam categories**, never fabricated specific-company sourcing.
