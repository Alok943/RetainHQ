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

Dynamic Programming is about identifying overlapping subproblems and optimal substructure, then caching results to avoid exponential blowup. The 6 concept nodes are the thinking process; the 8 trace nodes are proof-by-example.

- **`overlapping-subproblems`**: Define it, show Fibonacci recursion tree, contrast with Merge Sort.
- **`optimal-substructure`**: Define it, contrast with longest simple path.
- **`state-and-transition`**: How to name a state and find the recurrence.
- **`memoization-top-down`**: Recursion + cache. Top-down approach.
- **`tabulation-bottom-up`**: Fill table in dependency order. Iterative approach.
- **`space-optimization`**: Sliding window of variables. When we only need the last few states.

**Trace nodes repeated decisions:**
- `climbing-stairs-fibonacci`: "to reach step i, did I just take one step from i-1, or two steps from i-2?"
- `house-robber`: "do I rob this house (skip prev) or skip it (keep prev)?"
- `coin-change`: "does using this coin beat what I had for this amount?"
- `0-1-knapsack`: "does taking this item beat leaving it out?"
- `longest-common-subsequence`: "do chars match (diagonal) or not (skip one from either)?"
- `edit-distance`: "match (free) or which of insert/delete/replace gives cheapest path?"
- `longest-increasing-subsequence`: "which earlier smaller element gives longest chain, or start fresh?"
- `grid-dp-unique-paths-min-path-sum`: "arrive by moving right or down, which is cheaper/how many ways?"

Complexity as plain text (e.g. O(n*W), O(m*n), O(n)). Cite CLRS / Wikipedia as primary. Return the JSON array only (plus a short "Sources consulted" list).
