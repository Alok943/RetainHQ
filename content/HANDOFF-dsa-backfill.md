# Antigravity handoff — DSA viz backfill (11 lessons)

Backfill three viz-related blocks on the 11 live DSA viz lessons (all except `merge-sort.json`,
which is the finished REFERENCE — open it first and copy its shapes exactly).
Files: `content/roadmaps/dsa/<slug>.json`. **The gate is `python content/validate.py` — zero
errors required.** Do not touch any other field, do not reorder keys, do not edit generators/code.

## What to add per lesson

### 1. `viz.steps` — pseudocode panel (array of {id, label})
One row per step_id the generator emits, in logical algorithm order. `label` = a short pseudocode
line a beginner reads (see merge-sort's for tone: code-ish, ≤ ~60 chars, may use ≥ → arrows).
**`id` MUST be from the lesson's step_id list below — never invent ids.**

### 2. `viz.predictions` — 1–3 checkpoints (see merge-sort.json for shape)
`{ "at_step" and/or "at_op", "occurrence": "first"|"last"|N, "prompt", "derive", "level" }`
- **derive MUST be one of:** `next_op` · `next_write` · `next_n_writes(n)` · `next_swap_pair` ·
  `branch_binary` (binary-search family only). The validator rejects anything else.
- **level:** easy | medium | hard | expert. Ship mostly easy/medium (derive-checkable).
- Write prompts as DECISION framing (the repeated decision), not trivia: "Both fronts are visible —
  which value is written next?" not "what is the next op called?".
- Anchor so the gate teaches the misconception: e.g. bubble-sort → `at_step:"compare"` +
  `next_swap_pair` ("which pair swaps next?"); binary-search → `at_op:"WINDOW"` + `branch_binary`
  ("does the search go left or right?"); prefix-sums → `at_step:"build"` + `next_write`.

### 3. `mental_model.repeated_decision` — REQUIRED on every viz lesson
One sentence: the ONE question the algorithm asks every iteration. If the lesson already has it,
leave it; if missing, write it. (Powers the always-visible explain panel.)

## Ground truth per lesson (ids extracted from the generators — the ONLY legal values)

| slug | step_ids (emit order) | invariant ids | family ops |
|---|---|---|---|
| in-place-operations | init, swap, move, done | inv-bounds, inv-swapped, inv-reversed | POINT SWAP DONE |
| prefix-sums | build, query, done | inv-prefix, inv-query | SET WINDOW MARK DONE |
| frequency-counting | count, done | inv-tally, inv-signature | COUNT DONE |
| palindromes | init, match, mismatch, move, done | inv-bounds, inv-match, inv-palindrome | POINT MARK DONE |
| two-pointers-on-strings | init, swap, move, done | inv-bounds, inv-swap, inv-reversed | POINT SWAP DONE |
| frequency-arrays | count, done | inv-tally, inv-signature | COUNT DONE |
| bubble-sort | compare, swap, placed, done | inv-bubble, inv-largest, inv-sorted | POINT SWAP MARK DONE |
| selection-sort | scan, compare, newmin, swap, placed, done | inv-min, inv-prefix, inv-sorted | POINT SWAP MARK DONE |
| insertion-sort | pick, compare, swap, inplace, done | inv-prefix, inv-shift, inv-sorted | POINT SWAP MARK DONE |
| linear-search | start, compare, found, done | inv-scan, inv-found | POINT MARK DONE |
| binary-search | start, window, probe, found, discard, done | inv-window, inv-halve, inv-found | POINT WINDOW MARK DONE |

Notes: `viz.invariants` (id → sentence map) already exists per lesson — reuse those ids, don't
rename (renames are a migration, forbidden). A prediction's `at_step` must be a step_id from the
lesson's row above; `at_op` must be one of the lesson's ops.

## Quality bar (checked by human review, not the validator)
- Each prediction is answerable from what's ON SCREEN at the gate (bars + pointers + pseudocode).
- The prompt names the decision, not the mechanism ("which side is discarded?" ✓, "what does
  branch_binary return?" ✗).
- steps labels teach; ids are anchors. A learner reading only the steps column should grasp the
  algorithm's skeleton.

## Process
1. Read `content/roadmaps/dsa/merge-sort.json` (reference) + this doc.
2. Edit the 11 files. 3. Run `python content/validate.py` → fix until zero errors.
4. Do NOT run the frontend, do NOT commit.
