# Antigravity handoff — DSA phase 18 (Dynamic Programming)

Phase 18 = **14 nodes** (`_TODO-dsa.md` section 18) — the largest phase in the roadmap: 6 `concept`
(the DP *thinking process* itself) + 8 `dsa` trace (the canonical problems that install each piece of it).
Directly follows phase 17's `why-greedy-fails`, which forward-references this phase explicitly.

> **Infra reality check — READ THIS FIRST. The GRID renderer works; the DP-specific plumbing does NOT.**
> Verified against the current tree, and the picture is mixed:
> - **WORKING:** `GridViz` + `gridReducer` (`GRID_INIT`/`FILL_CELL`/`READ_CELL`/`MARK_CELL`) are proven
>   in production — they render the n-queens board (phase 12). The 2D DP tables (knapsack, LCS,
>   edit-distance, grid-DP) can reuse them directly.
> - **WORKING:** 1D DP (fibonacci, house robber, coin change, LIS) reuses `ArrayViz` + `VAR` — the exact
>   pattern `kadane.js` already uses. Predictions work too (`next_write` reads `WRITE`/`SET`).
> - **BROKEN:** a **`dp` op family is declared in `events.js`** — `['MEMO_WRITE','MEMO_HIT','FILL_CELL']`
>   — but **`compile.js` has NO `dp` reducer at all** (`REDUCERS` array does not include one). So
>   `MEMO_WRITE`/`MEMO_HIT` fall through to the unknown-op fallback: a frame with a caption but **zero
>   visual state**. Memoization — a core phase-18 concept — has no working visualization ops.
> - **BROKEN:** **no derive can gate on a DP table cell.** `predict.js`'s registry is
>   `next_op, next_write, next_n_writes, next_swap_pair, branch_binary, next_step_id, branch_window,
>   next_choice, is_safe, is_pruned`. `next_write` matches only `WRITE`/`SET`, never `FILL_CELL`;
>   `is_safe` reads `TEST_CELL` (backtracking-only). `validate.py` **rejects any unregistered derive**,
>   so the 4 grid DP nodes cannot have prediction checkpoints until one is added.
> - **LATENT:** `FILL_CELL` is declared in **both** the `grid` and `dp` families. `OP_TO_FAMILY` is built
>   with `Object.fromEntries`, so last-wins resolves it to `dp`. Harmless today (reducers dispatch on the
>   op name via `switch`, not family), but it's a real ambiguity — resolve it in Pass 0.
>
> **Pass 0 (Claude) must land before Pass 2 (generators) starts.** Pass 1 (prose) is unblocked and can
> run in parallel — it touches none of this code.

Three passes:
- **Pass 0 — CONTRACT FIX (Claude, BLOCKING for pass 2):** add the `dp` reducer + a grid/DP derive +
  resolve the `FILL_CELL` duplicate. Spec below. **Antigravity: do not do pass 0.**
- **Pass 1 — PROSE (Antigravity, THIS packet):** author all 14 lessons' text. **NO `viz` block.**
- **Pass 2 — VIZ (Antigravity from this spec, per D-015):** 8 generators (concept nodes get no
  generator) + goldens. Claude browser-verifies before anything is "done."

**Gate for pass 1: `python content/validate.py` — zero errors. Do NOT run the frontend. Do NOT commit.**
Tick boxes in `content/_TODO-dsa.md` as each file lands green.

---

## The 14 nodes (slugs EXACT from `_TODO-dsa.md`; titles/difficulty from `backend/seed_dsa.py`, which
already defines all 14 under phase `"Dynamic Programming"`, sections `Thinking` (the 6 concept nodes) and
`Examples` (the 8 trace nodes) — do NOT invent difficulties, they are authoritative there)

| slug | title | kind | difficulty | generator (pass 2) |
|---|---|---|---|---|
| `overlapping-subproblems` | Overlapping subproblems | **C** concept | medium | — (`runtime:"none"`) |
| `optimal-substructure` | Optimal substructure | **C** concept | medium | — (`runtime:"none"`) |
| `state-and-transition` | State & transition | **C** concept | medium | — (`runtime:"none"`) |
| `memoization-top-down` | Memoization (top-down) | **C** concept | medium | — (`runtime:"none"`) |
| `tabulation-bottom-up` | Tabulation (bottom-up) | **C** concept | medium | — (`runtime:"none"`) |
| `space-optimization` | Space optimization | **C** concept | **hard** | — (`runtime:"none"`) |
| `climbing-stairs-fibonacci` | Climbing stairs / Fibonacci | **D** dsa | easy | `climbing-stairs-fibonacci` |
| `house-robber` | House robber | **D** dsa | medium | `house-robber` |
| `coin-change` | Coin change | **D** dsa | medium | `coin-change` |
| `0-1-knapsack` | 0/1 Knapsack | **D** dsa | hard | `0-1-knapsack` |
| `longest-common-subsequence` | Longest common subsequence | **D** dsa | hard | `longest-common-subsequence` |
| `edit-distance` | Edit distance | **D** dsa | hard | `edit-distance` |
| `longest-increasing-subsequence` | Longest increasing subsequence | **D** dsa | hard | `longest-increasing-subsequence` |
| `grid-dp-unique-paths-min-path-sum` | Grid DP (unique paths / min path sum) | **D** dsa | medium | `grid-dp-unique-paths-min-path-sum` |

**6 concept + 8 trace.** Build order = table order; it is a deliberate dependency chain: the 6 concept
nodes install the DP *thinking process* first (why it works → how to name a state → the two
implementation strategies → the memory optimization), THEN the 8 trace nodes apply it in increasing
structural complexity (1D single-array → 1D with a choice → 1D with unbounded reuse → 2D 0/1 choice → 2D
string-alignment ×2 → 1D-with-search → 2D grid). `climbing-stairs-fibonacci` FIRST among trace nodes —
the simplest possible recurrence, and every later node's `mental_model` should reference it as "the same
shape as climbing stairs, but now the transition also depends on \_\_\_."

---

## Research source

The phase-18 deep-research paste-ready prompt does not exist yet — write
`content/RESEARCH-dsa-phase18-dynamic-programming.md` following the exact convention of
`content/RESEARCH-dsa-phase17-greedy.md` (shared contract from `PROMPT-dsa-research.md`, JSON schema,
one object per node keyed by slug, output to `content/research/dsa/phase-18.json`) before running it.
**The per-node must-hits below are the correctness spine — author from them now; do not wait for the
research.** This is standard CLRS/algorithms-course material, not contested; use research to enrich real
engineering examples and sourcing.

---

## Pass 1 — the 14 lessons (PROSE only, NO `viz`)

Follow `content/PROMPT-dsa.md` (⛔ no-viz boundary, FIVE questions, QUALITY BAR). Copy the shape of
`content/roadmaps/dsa/merge-sort.json` (gold `dsa` exemplar) and **OMIT its `viz` block** for the 8 trace
nodes; concept nodes copy `content/roadmaps/dsa/what-is-an-algorithm.json` and set **`runtime: "none"`**.

**`dsa` branch required fields:** `why_it_exists {problem, better_idea}`, `mental_model {intuition,
repeated_decision, ...}` — **`repeated_decision` REQUIRED**, `explanation` OR `sections` (teaching body
with a hand-trace), `common_mistakes` (≥1), `recall_questions` (≥3), `oa_questions` (≥2), `sources` (2–5
URLs).

**`concept` branch required fields:** `overview {what, why}`, `why_learning_this`, `common_mistakes`,
`recall_questions`, `practice_tasks`, `understanding_checks` (**≥2**), `sources`.

### Phase-wide rules (these are what make DP lessons correct, not just "recursion with a cache")

1. **Every trace node states its recurrence in plain text before any code/table.** e.g. `dp[i] =
   dp[i-1] + dp[i-2]`. Never introduce the table before the reader knows what each cell MEANS.
2. **State the DP state precisely: "what does `dp[i]` (or `dp[i][j]`) represent?"** This is the single
   highest-leverage sentence in every trace lesson — most DP confusion is not knowing what a cell means.
3. **Always give the base case(s) explicitly and say why they're the base case** (the recursion/table has
   to bottom out somewhere real, not just "0").
4. **Distinguish top-down (memoization) from bottom-up (tabulation) in EVERY trace node**, even if only
   one is hand-traced — name both, say which this lesson traces, and why (usually: table is simpler to
   trace on paper; recursion mirrors the "obvious" brute-force more directly).
5. **Complexity as plain text** — `O(n)`, `O(n*W)`, `O(m*n)`. Always state TIME and SPACE separately, and
   call out when space can be optimized (rolling array) — this is what `space-optimization` exists to
   generalize.
6. **`repeated_decision` is one crisp per-cell decision** (given per node below) — it is exactly what the
   pass-2 prediction gates on.

### Per-node must-hits (the correctness spine)

**`overlapping-subproblems`** (C, easy) — the FIRST diagnostic: does naive recursion redo work?
- What: a problem has overlapping subproblems if a naive recursive solution calls the SAME subproblem
  with the SAME arguments more than once. Fibonacci is the canonical example: `fib(5)` calls `fib(3)`
  twice, `fib(2)` three times — the call tree is exponential (`O(2^n)`) even though there are only `n`
  DISTINCT subproblems.
- **The diagnostic test to teach:** draw (or describe) the recursion tree; if the same `(args)` pair
  appears at more than one node, you have overlap, and caching the result the first time pays off on
  every repeat.
- Contrast with a problem that does NOT overlap (e.g. plain merge sort's recursive calls — each `(lo,
  hi)` pair is visited exactly once) — DP buys nothing there.
- `understanding_checks` must catch: "does DP help EVERY recursive problem?" (no — only overlapping ones).

**`optimal-substructure`** (C, easy) — the SECOND diagnostic: can the optimal answer be built from
optimal sub-answers?
- What: a problem has optimal substructure if an optimal solution to it CONTAINS optimal solutions to
  its subproblems. Shortest path is the textbook example (a shortest path's every sub-path is itself
  shortest); this is also the property that makes Dijkstra's greedy choice safe (cross-link phase 16).
- **Contrast with a problem that lacks it** (name one honestly, e.g. LONGEST simple path in a general
  graph does NOT have optimal substructure the same way — out of scope to prove, just name the boundary).
- **Both diagnostics together = "is this a DP problem?"** State plainly: overlapping subproblems tells
  you CACHING will help; optimal substructure tells you the cached sub-answers can be COMBINED correctly
  into the final answer. Neither alone is sufficient.
- `understanding_checks` must catch conflating the two properties.

**`state-and-transition`** (C, medium) — how to actually START solving a DP problem (the practical skill).
- What: **the state** is the minimal set of parameters that uniquely determines a subproblem's answer
  (e.g. "how many stairs remain" — one number is enough for climbing-stairs; "which item am I deciding on
  AND how much capacity is left" — two numbers for knapsack). **The transition** is the recurrence: how
  the answer for a state is built from the answers to smaller states.
- **The practical process to teach, as a checklist:** (1) define `dp[state] = ` in one sentence, (2)
  write the recurrence relating `dp[state]` to smaller states, (3) identify the base case(s), (4) decide
  the order of computation (which states must be known before which).
- The #1 skill gap this node exists to close: students can trace a GIVEN table but freeze when asked to
  DESIGN the state for a new problem. Give 2–3 mini state-naming examples across different problems.
- `understanding_checks` must catch: choosing a state that's too coarse (loses information needed for the
  recurrence) or too fine (blows up the state space unnecessarily).

**`memoization-top-down`** (C, medium) — DP as "recursion + a cache."
- What: write the NATURAL recursive solution (top-down, exactly as you'd think of it without DP), then
  add a cache (dict/array) keyed by the state; before recursing, check the cache; after computing, store
  in the cache.
- **Mechanically minimal change from brute-force recursion** — this is the pedagogical point: memoization
  is not a different algorithm, it's the SAME recursion with one guard clause added.
- Complexity: time drops from exponential to `O(number of distinct states × work per state)` because each
  state is computed once. Space: the cache PLUS the recursion call stack (`O(depth)`).
- misconceptions: forgetting to check the cache BEFORE recursing (defeats the purpose); forgetting to
  populate the cache AFTER computing (recomputes every time); using a mutable default argument as the
  cache in Python (classic bug, name it if the reader's example is Python-flavored).

**`tabulation-bottom-up`** (C, medium) — DP as "fill a table in dependency order."
- What: build the table iteratively from the base case UP to the final answer, in an order that
  guarantees every cell's dependencies are already filled when you reach it (usually just "increasing
  index order," but state this explicitly rather than assume it).
- **Trade-off vs top-down (state both directions honestly):** tabulation avoids recursion-call overhead
  and stack-depth limits (no risk of stack overflow on large `n`); but it computes EVERY state in the
  table, even ones the top-down version might skip if not all are reachable from the actual query.
  Top-down is often easier to derive FROM the recurrence; bottom-up is often easier to TRACE on paper and
  easier to space-optimize.
- Hand-trace filling a small table (reuse climbing-stairs or a similarly small example) left-to-right,
  showing each cell read only from already-filled cells.
- misconceptions: filling the table in the WRONG order (reading a cell before its dependency is filled —
  the #1 tabulation bug); assuming bottom-up is always faster than top-down (same asymptotic complexity;
  the win is constant-factor + no stack risk).

**`space-optimization`** (C, medium) — the "do I need the whole table?" follow-up.
- What: if `dp[i]`'s transition only reads a FIXED small window of previous states (e.g. `dp[i-1]` and
  `dp[i-2]` for Fibonacci-shaped recurrences), you don't need to keep the whole table — a few rolling
  variables suffice.
- **The generalizable rule to teach:** look at the recurrence's dependencies. If `dp[i]` depends only on
  `dp[i-1]` (and maybe `dp[i-2]`, a fixed constant back), collapse the array to O(1) variables. For 2D
  tables where `dp[i][j]` depends only on row `i-1` (not further back), collapse to TWO rows instead of
  the whole grid — `O(n)` instead of `O(m*n)`.
- **The real trade-off to name honestly:** you lose the ability to RECONSTRUCT the actual solution path
  (e.g. which items went into the knapsack, not just the max value) unless you keep extra bookkeeping —
  space optimization is a pure space/reconstructability trade.
- Cross-link forward to `climbing-stairs-fibonacci` and `house-robber` as the canonical 1D-rolling
  examples; `grid-dp-unique-paths-min-path-sum` as the 2D-to-1D-row example.
- `understanding_checks` must catch: applying this blindly to a table where a cell depends on a value
  from ARBITRARILY far back (can't be collapsed to a fixed window).

**`climbing-stairs-fibonacci`** (D, easy) — the simplest possible recurrence; the template every later
node echoes. `repeated_decision`: *"to reach step `i`, did I just take one step from `i-1`, or two steps
from `i-2` — so `dp[i] = dp[i-1] + dp[i-2]`?"*
- what: count ways to climb `n` stairs taking 1 or 2 steps at a time. `dp[i] = dp[i-1] + dp[i-2]`, base
  cases `dp[0]=1, dp[1]=1` (or equivalently `dp[1]=1, dp[2]=2` depending on indexing — pick one and state
  it precisely).
- Explicitly: **this is literally Fibonacci** — name the connection so the reader recognizes the shape
  everywhere it recurs.
- Hand-trace `n=5` fully, both top-down-with-cache AND the bottom-up table, side by side if space allows.
- Space-optimize to two rolling variables in the lesson itself (a live application of the `C` node just
  covered) — `O(n)` time, `O(1)` space.
- misconceptions: solving with plain unmemoized recursion and being surprised by exponential blowup at
  larger `n` (tie back to `overlapping-subproblems`).

**`house-robber`** (D, medium) — the first "should I include this or not" 1D choice. `repeated_decision`:
*"do I rob this house (skip the previous one, take its money plus what I had 2 houses ago) or skip it
(keep whatever I had at the previous house)?"* → `dp[i] = max(dp[i-1], dp[i-2] + nums[i])`.
- what: maximize sum of a subsequence with NO TWO ADJACENT elements chosen. Base cases `dp[0]=nums[0]`,
  `dp[1]=max(nums[0],nums[1])`.
- **The core insight to make explicit:** at each house, you're not deciding "is this a good house" in
  isolation — you're comparing two ENTIRE strategies (rob-through-here vs skip-here) and the recurrence
  encodes both.
- Hand-trace a 5–6 element array. Space-optimize to two rolling variables (same shape as
  climbing-stairs — say so).
- misconceptions: greedily picking every-other or the biggest values first (fails — this is exactly why
  it's DP and not greedy; forward-reference `why-greedy-fails` if useful); off-by-one on the adjacency
  check.

**`coin-change`** (D, medium) — the first UNBOUNDED-reuse 1D DP (each coin usable many times).
`repeated_decision`: *"for this amount, does using this coin (1 + the best answer for amount-coin) beat
what I already had for this amount?"* → `dp[amt] = min(dp[amt], 1 + dp[amt - coin])` for each coin ≤ amt.
- what: minimum number of coins to make a target amount, given unlimited coins of each denomination.
  `dp[0] = 0` (base case: zero coins for zero amount). `dp[amt] = infinity` (unreachable) if no coin
  combination works.
- **Explicitly revisit the `why-greedy-fails` counterexample** (`{1,3,4}`, target `6`) and show DP getting
  it right (`3+3`) where greedy got it wrong (`4+1+1`) — this is the single clearest "here's WHY we needed
  all that DP machinery" payoff in the whole phase. Use it.
- Hand-trace building the `dp[]` array from `0` up to a small target (e.g. `6`) with coins `{1,3,4}`.
- Complexity `O(amount × number of coins)`.
- misconceptions: trying to apply greedy here at all (the whole point); forgetting the "unreachable"
  sentinel and its handling at the end (if `dp[target]` is still infinity, return -1/"impossible").

**`0-1-knapsack`** (D, hard) — the first 2D "choice + constraint" DP; `GridViz`.
`repeated_decision`: *"for this item, does taking it (its value + the best answer for the remaining
capacity, EXCLUDING this item from future consideration) beat leaving it out?"*
- what: given items with `(weight, value)` and a capacity `W`, maximize total value without exceeding
  `W`, each item usable AT MOST ONCE (the "0/1" — take it or don't, no fractions, no repeats — contrast
  explicitly with `coin-change`'s unbounded reuse and the earlier-mentioned fractional knapsack where
  greedy DOES work).
- State: `dp[i][w]` = best value using the first `i` items with capacity `w`. Recurrence:
  `dp[i][w] = max(dp[i-1][w], value[i] + dp[i-1][w-weight[i]])` if `weight[i] <= w`, else `dp[i][w] =
  dp[i-1][w]`.
- **Why the ROW index matters (the 0/1 constraint's mechanism):** using `dp[i-1][...]` (the PREVIOUS
  row), not `dp[i][...]`, is exactly what enforces "this item can be used at most once" — reusing the
  current row would allow the item to be taken multiple times (that would be unbounded knapsack, a
  different problem — name it in one line).
  Hand-trace a small grid (3–4 items, small `W`).
- Complexity `O(n*W)` time and space; name the space-optimization to two rows (or one row scanned
  RIGHT-TO-LEFT — explain why right-to-left specifically: it prevents reading an already-updated
  current-row value that should still be the previous row's).
- misconceptions: iterating capacity left-to-right when space-optimized to one row (double-counts an
  item); confusing 0/1 with unbounded knapsack (reusing the same row).

**`longest-common-subsequence`** (D, hard) — the first 2D string-ALIGNMENT DP; `GridViz`.
`repeated_decision`: *"do these two characters (one from each string, at the current row/col) match — if
so extend the diagonal by 1; if not, take the best of skipping one character from either string?"*
- what: length of the longest subsequence (not necessarily contiguous, order-preserved) common to two
  strings. State: `dp[i][j]` = LCS length of the first `i` chars of string A and first `j` chars of B.
  Recurrence: if `A[i-1]==B[j-1]`: `dp[i][j] = dp[i-1][j-1] + 1`; else `dp[i][j] = max(dp[i-1][j],
  dp[i][j-1])`. Base case: `dp[0][*] = dp[*][0] = 0` (empty string has LCS 0 with anything).
- **The diagonal-vs-orthogonal move is the visual/mental hook** — match = step diagonally and grow;
  mismatch = look up or left and take the better one. State this explicitly, it's what the grid trace
  must sell visually in pass 2.
- Hand-trace two short strings (4–5 chars each) filling the full grid.
- Complexity `O(m*n)` time and space.
- misconceptions: confusing "subsequence" (order-preserved, gaps allowed) with "substring" (contiguous)
  — say this explicitly, it's the most common LCS mix-up; off-by-one on the `i-1`/`j-1` indexing (the
  `dp` grid is `(m+1) x (n+1)`, one bigger than the strings, to hold the empty-prefix base case).

**`edit-distance`** (D, hard) — the natural extension of LCS: three operations instead of a binary
match/no-match. `repeated_decision`: *"do these two characters match (free, move diagonally) — if not,
which of insert/delete/replace (each costing 1) gives the cheapest path here?"*
- what: minimum operations (insert, delete, replace) to turn string A into string B. State: `dp[i][j]` =
  edit distance between the first `i` chars of A and first `j` chars of B. Recurrence: if
  `A[i-1]==B[j-1]`: `dp[i][j] = dp[i-1][j-1]` (free — no operation needed); else `dp[i][j] = 1 +
  min(dp[i-1][j-1] [replace], dp[i-1][j] [delete from A], dp[i][j-1] [insert into A])`. Base case:
  `dp[i][0] = i`, `dp[0][j] = j` (turning a string into empty, or vice versa, costs one op per character).
- **Explicitly name this as "LCS's grid shape, plus a cost on mismatch instead of just skipping"** — the
  cross-link is the fastest way to make this node click for someone who just did LCS.
- Hand-trace two short strings on the full grid, labeling which of the 3 neighbor cells each step reads.
- Complexity `O(m*n)` time and space.
- misconceptions: forgetting the base-case ROW/COLUMN (turning "" into a j-length string always costs
  `j` inserts — students often initialize these to 0); picking the wrong neighbor to minimize (each of
  the 3 corresponds to a specific operation — get the mapping backwards and the trace is wrong even
  though the NUMBER might accidentally look plausible).

**`longest-increasing-subsequence`** (D, hard) — the first 1D DP where the recurrence needs a SEARCH
over all previous states, not a fixed-width lookback. `repeated_decision`: *"for this element, which
earlier element (with a smaller value) gives the longest chain I can extend, or do I start fresh here?"*
→ `dp[i] = 1 + max(dp[j] for all j < i where nums[j] < nums[i])`, else `dp[i] = 1`.
- what: length of the longest strictly increasing subsequence. `dp[i]` = length of the LIS ENDING AT
  index `i` (state this precisely — NOT "LIS using the first i elements," a common misstatement). Answer
  = `max(dp)` over all `i`.
- Naive DP is `O(n^2)` (for each `i`, scan all `j < i`) — hand-trace this version fully on a 6–7 element
  array.
- **Name the `O(n log n)` patience-sorting/binary-search improvement in one paragraph, do not co-teach
  it as the primary trace** — the mechanism (maintain a "tails" array of smallest possible tail for each
  length, binary-search where each new element belongs) is a distinct enough technique that it deserves
  its own future node; here it's a forward-pointer, not the lesson.
- misconceptions: assuming `dp[i]` means "answer using first i elements" (it specifically means "ending
  AT i" — the final answer needs a max over the whole array, not just `dp[n-1]`); forgetting subsequences
  need not be contiguous (mixing this up with a "longest increasing RUN" problem, which is a much easier
  single-pass problem).

**`grid-dp-unique-paths-min-path-sum`** (D, medium) — the direct 2D-grid application; `GridViz`, the
most literal use of the grid renderer in the phase (the DP table IS the visual grid, not an abstraction
on top of one). `repeated_decision`: *"for this cell, do I arrive by moving right (from the cell to my
left) or down (from the cell above) — and for min-path-sum, which of those two gives the cheaper total?"*
- **Unique Paths:** count paths from top-left to bottom-right of a grid moving only right/down.
  `dp[r][c] = dp[r-1][c] + dp[r][c-1]`. Base case: `dp[0][*] = dp[*][0] = 1` (only one way to stay along
  an edge).
- **Min Path Sum:** minimum sum along a right/down-only path, given a cost at every cell.
  `dp[r][c] = grid[r][c] + min(dp[r-1][c], dp[r][c-1])`. Base case: first row/column accumulate along the
  single available direction.
- **Teach both as the SAME shape** (sum-of-two-neighbors vs min-of-two-neighbors — a one-word change in
  the recurrence) — this is the phase's clearest demonstration that DP recurrences are a small family of
  reusable shapes, not 14 unrelated tricks.
- Hand-trace a small grid (e.g. 3x3 or 3x4) for both variants.
- Complexity `O(rows*cols)` time and space; name the space-optimization to one rolling row (this node is
  the natural home for a concrete "2D collapses to 1D" worked example, cross-linking `space-optimization`).
- misconceptions: allowing up/left moves (breaks the DAG structure the recurrence depends on — the
  problem is only a DP in the FIRST place because moves are one-directional, no cycles); forgetting the
  first-row/first-column base case and reading an out-of-bounds neighbor.

### Cross-links
The 6 concept nodes chain into each other in table order; `state-and-transition` is the hub every trace
node's `mental_model` should reference ("this node's state is..."). `coin-change` explicitly cross-links
back to `why-greedy-fails` (phase 17). `edit-distance` cross-links `longest-common-subsequence` (same
grid shape). `grid-dp-unique-paths-min-path-sum` cross-links `space-optimization`. `0-1-knapsack`
`related` → forward-pointer to a future "unbounded knapsack" node if one gets added (name the gap, don't
build it).

## ASCII-only in JSON
`->` not an arrow glyph, `--` not an em-dash, straight quotes, `>=`/`<=` not the glyphs, `dp[i][j]` plain.

## Process (pass 1)
1. Write `content/RESEARCH-dsa-phase18-dynamic-programming.md` (paste-ready prompt, see Research source
   above) — can be done in parallel with prose authoring, not a blocker.
2. Read `merge-sort.json` (shape, minus viz) + `content/PROMPT-dsa.md` (QUALITY BAR items 6–7) + the
   inlined must-hits above.
3. Write the 14 files — no `viz` block; each `dsa` node MUST have `mental_model.repeated_decision` AND
   state precisely what `dp[state]` means (rule 2 above).
4. `python content/validate.py` → zero errors. Tick `content/_TODO-dsa.md`.
5. Standing pipeline: Sonnet/Gemini lesson critic → apply fixes → re-critic.

---

## Pass 0 — CONTRACT FIX (Claude only, blocks pass 2)

Verified against the current tree. Four items:

**P0-1 — the `dp` op family has no reducer.** `events.js` declares
`dp: ['MEMO_WRITE','MEMO_HIT','FILL_CELL']`, but `compile.js`'s `REDUCERS` array is
`[recursionMergeReducer, arrayReducer, hashingReducer, scalarReducer, stackQueueReducer, treeReducer,
gridReducer, graphReducer, listReducer, intervalsReducer, bitsReducer]` — no `dpReducer`. `MEMO_WRITE`
and `MEMO_HIT` therefore produce a caption-only frame with no state change.
Fix: add a `dpReducer` holding a memo table (`state.memo = {}`, `state.memoActive = null`), where
`MEMO_WRITE {key, value}` sets `state.memo[key] = value` and `MEMO_HIT {key}` flags
`state.memoActive = key` (the "cache hit — skipped the whole subtree" moment, which is the single most
important visual in `memoization-top-down`). Emit `memo` / `memoActive` on the frame alongside the
existing keys. Decide whether the memo renders as its own small panel (like `StateMachine`) or as a
side table next to the recursion tree — a panel is the cheaper path and matches the existing
side-panel precedent.

**P0-2 — no derive can gate on a DP cell.** Add at minimum:
- `next_cell_value` — the `value` of the next `FILL_CELL` (gates "what number goes in this cell?" — the
  core prediction for all 4 grid DP nodes).
- `next_memo_event` — whether the next memo-family event is a `MEMO_HIT` or a `MEMO_WRITE`
  (`choice: hit | write`; gates "have we already solved this subproblem?" for `memoization-top-down`).
Both must be added to `DERIVES` in `predict.js` — `validate.py` parses that object's source directly
(`re.findall(r"^  (\w+)\(events", ...)`), so the two-space-indented `name(events, i) {` shape is
mandatory or the validator won't see the new derive.

**P0-3 — `FILL_CELL` is double-declared** in both the `grid` and `dp` families in `events.js`.
`OP_TO_FAMILY` last-wins resolves it to `dp`. Harmless today (reducers `switch` on op name, not family),
but ambiguous. Fix: remove `FILL_CELL` from the `dp` family declaration and leave it in `grid` (the grid
reducer is the one that actually implements it), OR keep it in `dp` and have the new `dpReducer` claim it
— **do not leave it in both.** Prefer leaving it in `grid`, since `gridReducer` already handles it and
`gridReducer` runs before any appended `dpReducer` would.

**P0-4 — no golden covers the grid or dp families.** Add one minimal golden asserting the reducer/frame
shape for `GRID_INIT` + `FILL_CELL` (+ the new memo ops) so Pass 2's generators have a regression net
from day one. Re-run `npm run golden` after all of the above — the backtracking goldens (which use
`gridReducer` via n-queens) are the existing regression net for P0-3.

---

## Pass 2 — the 8 generators (Antigravity, from this spec, per D-015)

**Do not start until Pass 0 has landed** — the 4 grid nodes cannot have prediction checkpoints until
P0-2's derives exist (`validate.py` will reject them), and `memoization-top-down`'s ops are dead until
P0-1.

One file per algorithm in `frontend/src/dsa/generators/<key>.js`, exporting a named `*Events(input)`
function, registered in `frontend/src/dsa/registry.js`. Patterns to copy: `frontend/src/dsa/generators/
kadane.js` (1D rolling-vars DP-shaped trace) for the four 1D nodes; `frontend/src/dsa/generators/
n-queens.js` (GRID_INIT/FILL_CELL/MARK_CELL usage) for the four 2D/grid nodes.

**Hard rules (same as every prior phase):** pure deterministic generator; events are the source of
truth, never author frames; `{ op, args, step_id, note }`, `step_id` monotonic; default inputs small and
hand-traceable, matching each lesson's hand-trace exactly.

| generator key | shape | ops used | the moment the viz must sell |
|---|---|---|---|
| `climbing-stairs-fibonacci` | 1D array | array family (`WRITE`, `POINT`, `MARK`), or `VAR` rolling pair | each `dp[i]` filled as the sum of the two cells behind it |
| `house-robber` | 1D array | array family + `VAR` for the two rolling candidates | the max() comparison at each index — which branch wins |
| `coin-change` | 1D array | array family, one pass per coin | the array progressively filling with smaller counts as cheaper coins get considered |
| `0-1-knapsack` | 2D grid | `GRID_INIT`, `FILL_CELL`, `READ_CELL`, `MARK_CELL` | each cell reading its ROW-ABOVE neighbor + the diagonal-minus-weight cell, taking the max |
| `longest-common-subsequence` | 2D grid | `GRID_INIT`, `FILL_CELL`, `READ_CELL`, `MARK_CELL {tag:'match'\|'skip'}` | the diagonal step on a match vs the up/left step on a mismatch |
| `edit-distance` | 2D grid | same as LCS + `MARK_CELL {tag:'insert'\|'delete'\|'replace'\|'match'}` | which of the 3 neighbor cells + the operation each step took |
| `longest-increasing-subsequence` | 1D array | array family, `READ_CELL`-equivalent scan-back per index | the O(n^2) inner scan checking each earlier smaller element, then the max update |
| `grid-dp-unique-paths-min-path-sum` | 2D grid | `GRID_INIT`, `FILL_CELL`, `READ_CELL` | each cell built from its up-neighbor + left-neighbor, filling row by row |

`GRID_INIT { rows, cols, values? }` first for all 4 grid generators (2D DP nodes reuse the exact
n-queens infra — no new ops needed, confirmed working). 1D nodes reuse `ARRAY_INIT`/`WRITE`/`VAR` (the
array family already proven by `kadane.js`).

**Goldens:** determinism; one frame per event; per-algorithm — final `dp` value/table matches a
hand-computed answer for each of the 8; knapsack/LCS/edit-distance grids match a hand-filled table
exactly, cell by cell. Print an op-count fingerprint like existing goldens.

**Then STOP and report.** Claude runs the browser pass (grid cells fill correctly, match/mismatch/insert/
delete/replace tags render distinct colors, 1D rolling values update live, no console errors).

---

## Boundaries
- Pass 1: touch only `content/roadmaps/dsa/*.json`, `content/_TODO-dsa.md`, and the new
  `content/RESEARCH-dsa-phase18-dynamic-programming.md`. No `viz`/`animation`/`image` in lesson JSON.
- Pass 2: touch only `frontend/src/dsa/generators/*` + `registry.js`. Do not edit `compile.js`,
  `events.js`, `predict.js`, or any renderer — this phase needs none of that (confirmed working infra).
- No commits, no pushes, no DB/seed changes.
- If the spec fights reality, implement the closest faithful version and FLAG it in
  `content/REPORT-dsa-phase18.md` — do not silently redesign.
