# DSA deep-research — Phase 17: Greedy (paste into Gemini)

> **How to run:** In Gemini (Deep Research mode recommended), paste the whole of
> `content/PROMPT-dsa-research.md` from the `ROLE` heading through the `OUTPUT FORMAT`
> section FIRST (the shared contract + JSON schema + field rules). Then paste everything
> below. One phase per chat.
>
> **Two-step (Deep Research):** let it produce the prose report, then send the
> "Convert your research above into a JSON array…" extraction prompt from the contract.
> Save the JSON to `content/research/dsa/phase-17.json` (one object per node, keyed by
> slug). Hand it back to Claude for authoring.

---

## PHASE 17 — GREEDY (5 nodes)

Research each node into one JSON object per the schema. Kind tag per node:
**C** = `kind_hint:"concept"` (renderer `none`), **D** = `kind_hint:"trace"` (steppable).

1. **Why greedy works** — C — `why-greedy-works`
2. **Why greedy fails** — C — `why-greedy-fails`
3. **Interval scheduling** — D — `interval-scheduling`
4. **Merge intervals** — D — `merge-intervals`
5. **Jump game** — D — `jump-game`

## PHASE-SPECIFIC EMPHASIS (do NOT skip)

Greedy is a THINKING pattern, not an algorithm — the two concept nodes are the heart of
the phase and the trace nodes are proof-by-example. Research accordingly:

- **`why-greedy-works` must deliver the two formal ingredients in plain words:**
  (1) the **greedy-choice property** (a globally optimal solution can be reached by a
  locally optimal choice at each step) and (2) **optimal substructure**. Explain the
  **exchange argument** concretely — how you prove a greedy choice is safe by showing any
  optimal solution can be transformed to include it without getting worse. Do NOT leave
  this abstract; anchor it to interval scheduling (the cleanest exchange-argument proof).

- **`why-greedy-fails` must carry a crisp, memorable counterexample** — this is the aha
  node. The canonical pair: **coin change** where greedy fails (e.g. coins {1, 3, 4},
  target 6 → greedy 4+1+1 = 3 coins, optimal 3+3 = 2 coins) and **0/1 knapsack** (greedy
  by value/weight ratio is not optimal). Explicitly forward-reference DP (phase 18):
  "when greedy fails, you usually need dynamic programming." Put the counterexample in
  `interesting_facts` / `mental_model` — it's the retention hook. `repeated_decision` /
  `invariants` may be "N/A" for both concept nodes.

- **"Sort by WHAT?" is the repeated decision, and it differs per problem** — make this
  explicit in every trace node's `repeated_decision` and `author_notes`:
  - `interval-scheduling` (activity selection): sort by **earliest END time**, greedily
    take each interval compatible with the last chosen. State WHY end-time (not start,
    not shortest) is the correct key — this is the exchange-argument payoff.
  - `merge-intervals`: sort by **START time**, then sweep merging any overlap into the
    running interval. Contrast it with scheduling — same "sort intervals" family,
    DIFFERENT key and DIFFERENT goal (merge/coalesce vs select-max-count). Students
    conflate these two; the `misconceptions` field should call it out.
  - `jump-game`: greedy **reachability** — track the farthest index reachable so far;
    if the current index ever exceeds it, you're stuck. (Jump Game II = min jumps via a
    BFS-like layer count.) The invariant: "farthest-reach never needs recomputation."

- **Renderer hints (`visualization.renderer`):** `interval-scheduling` and
  `merge-intervals` → `number-line` (intervals as bars on a timeline; animate the sort,
  then the accept/reject or merge sweep). `jump-game` → `array` (animate the moving
  farthest-reach pointer). Give 2–3 `interactive_inputs` each (a clean case, an
  all-overlapping case, an unreachable/edge case) with one-line `why`.

- **`prediction_checkpoints`** should pause right before a greedy choice and ask "which
  interval does it pick next, and why that one?" — the student holding the wrong sort-key
  belief answers wrong. That's the ideal gate.

- **`failure_signals` / `when_not_to_use`:** greedy is tempting but WRONG when a locally
  best choice can block a better global outcome (0/1 knapsack, coin change with arbitrary
  denominations, longest path). Naming when NOT to be greedy is half the lesson.

Complexity as plain text (O(n log n) dominated by the sort, O(n) for jump game). Cite
CLRS (greedy chapter) / Wikipedia as primary. Return the JSON array only (plus a short
"Sources consulted" list).
