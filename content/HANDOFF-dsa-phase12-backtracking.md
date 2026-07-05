# Antigravity handoff -- DSA phase 12 (Backtracking)

Author 5 NEW **`dsa`-kind** lessons at `content/roadmaps/dsa/<slug>.json`. These are execution-trace-STYLE
lessons authored **WITHOUT a `viz` block** -- the trace generators and the board/tree renderer for
backtracking do not exist yet and are Claude-owned; the viz layer will be added later. Your job is the
complete prose lesson: the teaching body must carry the full mental simulation in text (small hand-traces,
decision trees drawn in ASCII inside `explanation`/`sections`).

Set **`kind: "dsa"`** and do **NOT** include `viz`. Everything else follows the dsa branch of `validate.py`.

**Gate: `python content/validate.py` -- zero errors.** Do NOT run the frontend. Do NOT commit.

## Reference + contract
- **Exemplars (same kind -- study the field usage, IGNORE their `viz` blocks):**
  - `content/roadmaps/dsa/valid-parentheses.json`
  - `content/roadmaps/dsa/next-greater-element.json`
  - `content/roadmaps/dsa/merge-two-sorted-lists.json`
- **Authoring contract:** `content/PROMPT-dsa.md` -- the `kind: "dsa"` section + the QUALITY BAR
  (every recall/oa answer derivable from the body; no unexplained jargon).
- **Prerequisite lessons you may link to (all exist):** `base-case`, `recursive-relation`,
  `the-call-stack`, `recursion-tree` (phase 11). Backtracking is recursion + undo -- lean on them.
- **No deep-research report exists for phase 12.** Author from the inline enrichment below; do not
  invent citations.

## Required fields (dsa branch of `validate.py`)
- `slug`, `title`, `roadmap` ("dsa"), `kind` ("dsa"), `tier`, `metadata` (difficulty, estimated_minutes,
  importance 1-10, interview_frequency, prerequisites[], unlocks[]).
- `mental_model` -- object with non-empty `intuition`. **Also fill `repeated_decision`** (backtracking IS
  a repeated decision; the future viz needs it, and it sharpens the lesson now).
- `why_it_exists` -- object with `problem` + `better_idea` (`naive_solution` optional -- use it: the naive
  alternative to backtracking is "generate everything, then filter," and the contrast teaches pruning).
- `explanation` OR `sections` -- the teaching body. Use `sections` for the problem lessons: one section
  per stage (the decision at each step -> the tree it induces -> the hand-trace -> the pruning).
- `common_mistakes` -- non-empty list of `{title, explanation}`.
- `recall_questions` -- >=3 `{q, answer}`.
- `oa_questions` -- >=2 interview-style `{question, answer}`.
- **Optional but expected here:** `pattern` (name the pattern!), `key_points`, `when_not_to_use`,
  `engineering_examples`, `practice` (`{title, url}` -- LeetCode links below), `related`,
  `failure_signals`.
- **Do NOT** add `viz`, `overview`, `why_learning_this`, `understanding_checks`, `practice_tasks` --
  those belong to the `concept` kind, not `dsa`.

## The 5 nodes (slugs EXACT from `_TODO-dsa.md` section 12) + the misconception each must kill
| slug | title | tier/difficulty | focus + THE misconception |
|---|---|---|---|
| `backtracking-template` | Backtracking template | medium | The universal skeleton: **choose -> explore -> un-choose**. Misconception: backtracking is a new algorithm. No -- it is plain recursion (phase 11) where each frame makes a CHOICE, recurses, then UNDOES the choice so the shared state is clean for the next option. The undo step is the whole trick. |
| `subsets` | Subsets | medium | Include/exclude decision per element -> binary decision tree -> 2^n leaves. Misconception: "I need to generate combinations cleverly." No -- one yes/no decision per element enumerates the power set completely and without duplicates. |
| `permutations` | Permutations | medium | Build arrangements position by position; a `used[]` marker (or in-place swap) prevents reuse. Misconception: same tree as subsets. No -- subsets decide PER ELEMENT (include or not, order fixed); permutations decide PER POSITION (which unused element goes here) -> n! leaves, not 2^n. |
| `combination-sum` | Combination sum | medium | Target-driven search where an element may be REUSED; pass a start index so [2,3] and [3,2] are not both produced. Misconception: allowing reuse means allowing duplicates in the output. No -- reuse means recursing with the SAME index i (not i+1); duplicates are killed by never looking backward (start index), not by a seen-set. Sorted input lets you PRUNE: once candidate > remaining target, stop the loop. |
| `n-queens` | N-Queens | hard | The flagship. Place queens ROW BY ROW; a queen per row kills the "try all 64 squares" explosion. Track attacked columns and both diagonals in O(1) sets: `col`, `row-col` (one diagonal family), `row+col` (the other). Misconception: you must scan the board to check safety. No -- three set lookups. Second misconception: backtracking is brute force. No -- pruning abandons a subtree the moment a partial placement is invalid, which is exactly why it beats generate-and-filter (64-choose-8 boards vs a tiny searched tree). |

## Enrichment (author from this)

**backtracking-template**
- The skeleton, verbatim in the body (Python):
  `def backtrack(state): if goal(state): record(copy); return` / `for choice in options(state):`
  `apply(choice); backtrack(state); undo(choice)`.
- Tie to phase 11: each `backtrack` call is a stack frame; the state-space tree IS the recursion tree
  (`recursion-tree`); un-choose on the way UP is "work during unwinding" (`the-call-stack`).
- THE bug this kind of code always has: appending `state` (a reference) instead of `state.copy()` when
  recording a solution -- every recorded answer later mutates to []. Make this a common_mistake AND an
  oa_question.
- Complexity honesty: backtracking does not change worst-case exponential bounds; pruning changes the
  PRACTICAL size of the searched tree. Signal phrases for interviews: "all combinations/permutations/
  ways", "generate all", "exists a path/assignment".
- when_not_to_use: counting-only questions (DP counts without enumerating); optimization with
  overlapping subproblems (DP); single feasible answer in a monotone space (binary search on answer).

**subsets** (LeetCode 78)
- Two equivalent framings -- teach include/exclude as primary: at element i, branch "take it" / "skip
  it"; depth n, 2 branches -> 2^n leaves, each leaf one subset. ASCII the tree for [1,2] fully (4 leaves).
- Record at EVERY node vs only at leaves (both idioms exist; pick leaves-with-index==n and mention the
  for-loop idiom). Complexity O(n * 2^n) (copying costs n per subset).
- Engineering example: feature-flag/config combinations in testing; power-set expansion in query
  planners.

**permutations** (LeetCode 46)
- Decision at each POSITION: which still-unused element to place. `used[i]` boolean array; choose ->
  mark -> recurse -> unmark. Tree: n branches, then n-1, ... -> n! leaves. Hand-trace [1,2,3] to depth 2.
- Contrast table subsets-vs-permutations (decision, branching, leaf count, needs used[]?) -- this
  contrast is a classic interview probe; put it in key_points and an oa_question.
- Complexity O(n * n!). Mention the swap-in-place variant exists as a space optimization, one line, no
  full treatment.

**combination-sum** (LeetCode 39)
- State = (start index, remaining target, current path). Loop i from start: skip if candidates[i] >
  remaining (works only because input SORTED -- say so); choose; recurse with the SAME i (reuse allowed);
  un-choose. Base: remaining == 0 -> record copy; remaining < 0 or i exhausted -> dead end.
- WHY same-index recursion kills permutation-duplicates: the path can never contain a smaller index
  after a larger one, so each multiset is produced exactly once, in one canonical order. This is the
  lesson's aha -- spell it out.
- Hand-trace candidates=[2,3,6,7], target=7 -> [[2,2,3],[7]] compactly.

**n-queens** (LeetCode 51)
- Structure the body: (1) why row-by-row placement (one queen per row is FORCED, so a row is one
  decision -> N branches per level, depth N); (2) the three constant-time attack sets and WHY the
  diagonal keys are row-col and row+col (walk one diagonal and show the invariant number); (3) the
  choose/mark-3-sets/recurse/unmark loop; (4) a 4x4 hand-trace in ASCII boards showing the FIRST dead
  end and the backtrack that recovers -- 4x4 is the smallest interesting case (N=2,3 have no solution;
  say so, it is a great recall question); (5) generate-and-filter vs backtracking numbers to make
  pruning visceral.
- Pattern generalization: N-Queens = constraint-satisfaction template (Sudoku solvers, register
  allocation, exam timetabling) -- engineering_examples.
- failure_signals: recursion that never un-marks the sets; checking safety by rescanning the whole
  board (O(N) per check when O(1) is available); confusing the two diagonal families.

**practice links:** LC 78 Subsets, LC 46 Permutations, LC 39 Combination Sum, LC 51 N-Queens,
LC 22 Generate Parentheses (template practice), LC 79 Word Search (grid backtracking, stretch).
**sources to cite (real URLs only):** the LeetCode problem pages, Wikipedia "Backtracking",
GeeksforGeeks backtracking intro, NeetCode backtracking pattern page.

## Quality bar (the FIVE questions, per lesson, answerable from THIS lesson alone)
1. Why does this exist? (what explodes without it -- the naive generate-everything alternative)
2. How do I mentally simulate it? (the hand-trace: tree + choose/undo, in the body, small N)
3. What is the invariant / repeated decision? (state is IDENTICAL before and after exploring a branch --
   that is what un-choose guarantees; name each lesson's decision explicitly in mental_model)
4. Where is it used in real systems? (solvers, schedulers, parsers, config search -- name the situation)
5. How do I recognize it in an interview? ("all/every/generate" wording; constraints n <= ~20)
- Cross-link: `backtracking-template` prereqs `recursion-tree` + `the-call-stack`; the four problems
  prereq `backtracking-template`; `n-queens` unlocks nothing yet (phase 13+ not authored).
- `subsets`/`combination-sum` unlock forward references to DP (subset-sum family) -- mention, don't teach.

## ASCII-only in JSON
Plain ASCII in string values -- `->` not an arrow glyph, `--` not an em-dash, straight quotes. ASCII
trees/boards in the body are encouraged (they stand in for the deferred viz).

## Process
1. Read the 3 dsa exemplars + PROMPT-dsa.md dsa section.
2. Write the 5 files, `backtracking-template` FIRST (the other four cite its skeleton verbatim -- same
   naming, so the pattern visibly repeats across all five).
3. `python content/validate.py` -> zero errors. Tick the five boxes in `_TODO-dsa.md` section 12.
4. Standing pipeline: lesson critic in a SEPARATE session (`content/PROMPT-lesson-critic.md` or
   `content/RUN-lesson-critic-antigravity.md`) -> apply fix list -> re-critic. DONE only when a cold
   beginner can answer every recall/oa question from the body AND the expert finds zero correctness
   errors.

> NO `viz` in this packet. The N-Queens board renderer + trace generators (CHOOSE/PLACE/PRUNE/UNDO op
> vocabulary, 2D board + tree panel) are Claude-owned and will be layered on afterward -- write the
> prose so a viz can attach later without rewording (explicit steps, consistent variable names:
> `cols`, `diag1` (row-col), `diag2` (row+col), `path`, `used`).
