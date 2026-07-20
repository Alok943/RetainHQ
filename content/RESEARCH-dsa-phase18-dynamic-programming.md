# DSA deep-research — Phase 18: Dynamic Programming (paste into Gemini)

> **How to run:** In Gemini (Deep Research mode recommended), paste the whole of
> `content/PROMPT-dsa-research.md` from the `ROLE` heading through the `OUTPUT FORMAT`
> section FIRST (the shared contract + JSON schema + field rules). Then paste everything
> below. One phase per chat.
>
> **Two-step (Deep Research):** let it produce the prose report, then send the
> "Convert your research above into a JSON array…" extraction prompt from the contract.
> Save the JSON to `content/research/dsa/phase-18.json` (one object per node, keyed by
> slug). Hand it back to Claude for authoring.

---

## PHASE 18 — DYNAMIC PROGRAMMING (14 nodes)

Research each node into one JSON object per the schema. Kind tag per node:
**C** = `kind_hint:"concept"` (renderer `none`), **D** = `kind_hint:"trace"` (steppable).

1. **Overlapping subproblems** — C — `overlapping-subproblems`
2. **Optimal substructure** — C — `optimal-substructure`
3. **State & transition** — C — `state-and-transition`
4. **Memoization (top-down)** — C — `memoization-top-down`
5. **Tabulation (bottom-up)** — C — `tabulation-bottom-up`
6. **Space optimization** — C — `space-optimization`
7. **Climbing stairs / Fibonacci** — D — `climbing-stairs-fibonacci`
8. **House robber** — D — `house-robber`
9. **Coin change** — D — `coin-change`
10. **0/1 Knapsack** — D — `0-1-knapsack`
11. **Longest common subsequence** — D — `longest-common-subsequence`
12. **Edit distance** — D — `edit-distance`
13. **Longest increasing subsequence** — D — `longest-increasing-subsequence`
14. **Grid DP (unique paths / min path sum)** — D — `grid-dp-unique-paths-min-path-sum`

## PHASE-SPECIFIC EMPHASIS (do NOT skip)

DP is the largest, most feared phase in most DSA curricula because it's usually taught as 14
unrelated tricks. Research to counter that directly:

- **The 6 concept nodes are a PROCESS, not background theory** — `overlapping-subproblems` +
  `optimal-substructure` are the two-part DIAGNOSTIC ("is this a DP problem at all?"),
  `state-and-transition` is the DESIGN skill ("how do I start solving one?"),
  `memoization-top-down`/`tabulation-bottom-up` are the two IMPLEMENTATION strategies, and
  `space-optimization` is the follow-up refinement. Research each with this role in mind, not
  as an isolated definition.

- **Every trace node needs its state defined in one precise sentence** ("what does `dp[i]`
  represent?") BEFORE the recurrence — this is the single highest-leverage fact to extract per
  node. Also extract: the recurrence in plain-text form, the base case(s) and why they're the
  base case, time AND space complexity separately, and whether space can be rolled to O(1) or
  O(n) (name which prior/adjacent states the recurrence actually reads).

- **`coin-change` must explicitly research the classic greedy-fails counterexample**
  (denominations `{1,3,4}`, target `6`) and confirm DP gets `3+3`=2 coins where greedy gets
  `4+1+1`=3 — this is the phase's explicit callback to phase 17's `why-greedy-fails`. Make sure
  the research captures WHY greedy fails here (no exchange argument exists once a locally-best
  coin can block a better combination).

- **`0-1-knapsack` must research the 0/1 vs UNBOUNDED vs FRACTIONAL distinction precisely** —
  which variant does greedy solve correctly (fractional only) and why (splittable items admit an
  exchange argument on value/weight ratio; 0/1 does not). Also research why the DP recurrence
  must read the PREVIOUS row (`dp[i-1][...]`), not the current row, to enforce "each item once."

- **`longest-common-subsequence` and `edit-distance` should be researched together** — same 2D
  grid shape, LCS is match-or-skip (binary), edit-distance adds a cost to the skip case and 3
  named operations (insert/delete/replace). Research the exact recurrence and base-case indexing
  convention for both (the `(m+1) x (n+1)` grid holding the empty-prefix base case).

- **`longest-increasing-subsequence` should research BOTH the O(n^2) DP formulation (`dp[i]` =
  LIS ending AT i) and name (without fully deriving) the O(n log n) patience-sorting/binary-search
  improvement** as a forward-pointer, not the primary trace.

- **`grid-dp-unique-paths-min-path-sum` should research both named variants as the SAME shape**
  (sum-of-neighbors vs min-of-neighbors) — this is meant to be the phase's clearest "these are a
  small family of reusable recurrence shapes" demonstration.

- **`prediction_checkpoints`** should pause right before a cell is filled and ask "what value goes
  here, and which neighbor(s) does it read?" — the reader holding the wrong recurrence answers
  wrong. For the 6 concept nodes, prediction is not applicable (`runtime:"none"`).

- **Renderer hints (`visualization.renderer`):** the 4 two-dimensional nodes (`0-1-knapsack`,
  `longest-common-subsequence`, `edit-distance`, `grid-dp-unique-paths-min-path-sum`) → `grid`
  (a filled DP table, already proven working infra — reuse the n-queens-style grid renderer). The
  4 one-dimensional nodes (`climbing-stairs-fibonacci`, `house-robber`, `coin-change`,
  `longest-increasing-subsequence`) → `array` (cells filling left to right, rolling-variable
  callouts for the space-optimized versions). Give 2–3 `interactive_inputs` each (a clean case, an
  edge case like an empty/minimal input, a case that exercises the trickiest branch) with one-line
  `why`.

- **`failure_signals` / `when_not_to_use`:** name when a problem LOOKS like DP but a simpler
  technique dominates (e.g. a problem with no overlapping subproblems doesn't need memoization at
  all — plain recursion or a single pass suffices).

Complexity as plain text (`O(n)`, `O(n*W)`, `O(m*n)`, state time AND space separately for every
trace node). Cite CLRS (DP chapter) / Wikipedia / a reputable competitive-programming reference as
primary. Return the JSON array only (plus a short "Sources consulted" list).
