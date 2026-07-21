# Antigravity re-prompt — DSA phase 18, pass 1b (hand-traces)

Phase 18 pass 1 is **accepted with one systematic gap**. `validate.py` is clean, sources are good, no
leaked authoring instructions, and 13/14 per-node correctness must-hits landed. Two mechanical defects
(an unbalanced paren in the LCS recurrence, 5 non-ASCII characters) were already fixed by Claude in
commit `7115649` — **pull before editing** so you don't revert them.

**The gap: 6 of the 8 trace nodes ship without a concrete hand-trace.** The handoff required one per
trace node, and it is the single most load-bearing artifact in a `dsa` lesson — the phase teaches
mentally simulating a table being filled, and prose describing that a table gets filled is not a
substitute for watching it fill. `0-1-knapsack`'s "Imagine tracing 3 items on a small grid" is exactly
the thing to fix: it asks the reader to do the work the lesson exists to do for them.

**Do not touch anything else.** Prose, sources, recurrences, complexity, and all 6 concept nodes are
accepted as-is. This is an additive pass: append a hand-trace to the `explanation` of each node below
(and, where noted, add the one missing fact). No `viz` block. No new files.

## The two nodes that got it right — copy their shape

- **`coin-change`** — the gold standard for this phase. It states the greedy callback, then walks
  `dp[0]` through `dp[6]` with a value and a justification per cell, then shows the three relaxation
  candidates being compared at `dp[6]` and the minimum being taken, then handles the unreachable
  sentinel. Do this, for every node below.
- **`house-robber`** — also has a real trace. Fine as-is.

## What each node needs

| node | needs |
|---|---|
| `climbing-stairs-fibonacci` | A numeric trace of `n=5`, filling `dp[0]..dp[5]`. **Also missing: the base cases are never stated.** Pick an indexing convention (`dp[0]=1, dp[1]=1` or `dp[1]=1, dp[2]=2`) and state it explicitly — right now the lesson gives the recurrence with nothing to bottom out on. |
| `0-1-knapsack` | **The most under-specified node in the phase — needs the most work.** (1) State what `dp[i][w]` MEANS in one sentence ("best value using the first `i` items with capacity `w`"). (2) Write the recurrence out: `dp[i][w] = max(dp[i-1][w], value[i] + dp[i-1][w-weight[i]])` when `weight[i] <= w`, else `dp[i][w] = dp[i-1][w]`. (3) Hand-trace 3-4 items and a small `W` (e.g. items `(w=1,v=1), (w=3,v=4), (w=4,v=5)`, `W=6`) filling the grid row by row, showing which two cells each entry reads. (4) Add the one-line contrast with **fractional** knapsack (greedy works there, fails here) — the only must-hit that did not land. |
| `longest-common-subsequence` | Hand-trace two short strings, 4-5 chars each (e.g. `"ABCB"` / `"BDCB"`), filling the full `(m+1) x (n+1)` grid. Label each cell as a diagonal-match step or an up/left max step — the diagonal-vs-orthogonal move is the visual this node exists to install. |
| `edit-distance` | Hand-trace two short strings on the full grid, and for each filled cell name **which of the 3 neighbours it read and which operation that corresponds to** (up = delete, left = insert, diagonal = replace-or-free-match). The neighbour-to-operation mapping is the thing students invert; a trace that only shows numbers will not fix it. |
| `longest-increasing-subsequence` | Hand-trace the `O(n^2)` version fully on a 6-7 element array, showing the inner scan-back at each `i` (which earlier smaller elements were considered, which won). End by taking `max(dp)` across the whole array and say explicitly that the answer is NOT `dp[n-1]` — the lesson already states `dp[i]` means "ending at i", so the trace must land the consequence. |
| `grid-dp-unique-paths-min-path-sum` | Everything else is right (state, recurrence, base cases, both variants, space optimization). Only needs a numeric trace: a 3x3 grid filled for **both** variants, so the reader sees the same traversal produce a count vs a cost with only the combining operation changed. |

## Rules (unchanged)

- Append to `explanation` (or add a `sections` entry) — **no `viz` block**, this is still pass 1.
- **ASCII only.** Use `--` not an em-dash, `*` not a multiplication sign, `->` not an arrow. Five files
  in this batch broke this; it has already been fixed once, do not reintroduce it.
- Every number in a trace must be correct. These get read by someone learning the algorithm for the
  first time — a wrong cell teaches a wrong recurrence. Verify each trace by computing it, not by
  pattern-matching a remembered example.
- Traces must be small enough to follow on paper: 5-7 array elements, 3x3 or 3x4 grids, 4-5 char
  strings. Anything bigger stops being traceable and becomes a wall of numbers.
- Gate: `python content/validate.py` -> zero errors. Do NOT run the frontend.
- **Do NOT commit and do NOT push.** The previous batch was committed and pushed to `main` despite the
  handoff forbidding it. Leave the working tree dirty and report back; Claude reviews, then commits.

## Then report

State which nodes you touched and paste the final line of `validate.py`. Claude re-reviews the traces
for numerical correctness before anything is committed.
