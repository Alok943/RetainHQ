# DSA deep-research — Phase 20: Algorithm Design Patterns (paste into Gemini)

> **How to run:** In Gemini (Deep Research mode recommended), paste the whole of
> `content/PROMPT-dsa-research.md` from the `ROLE` heading through the `OUTPUT FORMAT`
> section FIRST (the shared contract + JSON schema + field rules). Then paste everything
> below. One phase per chat.
>
> **Optional for this phase** — see note in `content/HANDOFF-dsa-phase20-algorithm-design-
> patterns.md`'s "Research source" section: this phase is mostly a synthesis of the roadmap's
> own prior content, and the HANDOFF's inlined must-hits may be sufficient without running this
> at all. Run it if you want extra concrete "spot the pattern" example problems beyond what's
> inlined there.
>
> **Two-step (Deep Research):** let it produce the prose report, then send the
> "Convert your research above into a JSON array…" extraction prompt from the contract.
> Save the JSON to `content/research/dsa/phase-20.json` (one object per node, keyed by
> slug). Hand it back to Claude for authoring.

---

## PHASE 20 — ALGORITHM DESIGN PATTERNS (8 nodes, all concept, all `runtime:"none"`)

Research each node into one JSON object per the schema. All nodes are **C** =
`kind_hint:"concept"` (renderer `none`) — this phase has no traceable execution, it teaches
recognition of patterns taught elsewhere in the roadmap.

1. **Brute force first** — `brute-force-first`
2. **Precomputation** — `precomputation`
3. **Recognizing divide & conquer** — `recognizing-divide-and-conquer`
4. **Recognizing two pointers** — `recognizing-two-pointers`
5. **Recognizing sliding window** — `recognizing-sliding-window`
6. **Recognizing greedy vs DP** — `recognizing-greedy-vs-dp`
7. **Recognizing graph problems** — `recognizing-graph-problems`
8. **Pattern recognition drill** — `pattern-recognition-drill`

## PHASE-SPECIFIC EMPHASIS (do NOT skip)

This is the roadmap's capstone — its entire value is teaching the reader to recognize, from a
problem STATEMENT (not a pre-labeled category), which earlier phase's technique applies. Research
accordingly, and treat this as fundamentally different from every other phase's research pass:

- **Do NOT research new algorithms.** Every mechanism referenced here (two pointers, sliding
  window, D&C, greedy, DP, graphs) is already taught in an earlier phase. This research pass
  should surface CONCRETE PROBLEM STATEMENTS and their SURFACE-LEVEL recognition signals — the
  specific words/phrasing/constraints that hint at each pattern — not re-derive the techniques.

- **For each `recognizing-*` node, research at least one genuine DISTRACTOR** — a problem that
  superficially resembles the pattern's signal but actually needs a different technique (or a
  modified version of the same one). This is the highest-value thing this research pass can add:
  real near-miss examples are hard to invent from scratch and easy to get wrong if fabricated
  rather than sourced from real problem sets.

- **`recognizing-greedy-vs-dp` is the single highest-value node in the phase.** Research should
  focus on finding (or confirming) the cleanest possible worked contrast pair where a SINGLE
  changed constraint flips the correct technique — the canonical one is fractional knapsack
  (greedy works, exchange argument holds) vs 0/1 knapsack (greedy fails, no exchange argument once
  items are indivisible). Confirm this pair holds up and find the clearest plain-language framing
  of WHY the constraint change matters.

- **`recognizing-graph-problems` should research 2-3 well-known "disguised graph" problems** —
  problems that don't present as a graph on the surface (a grid where adjacent cells are edges; a
  word-transformation problem where one-edit-apart words are edges; a state-transition puzzle) —
  concrete, sourceable examples beat invented ones here.

- **`pattern-recognition-drill` should research a SET of short, real problem statements (not full
  solutions)** spanning all five recognition families in this phase, plus at least 2 explicit
  distractors, suitable for a "name the pattern and why" exercise. Prefer well-known problems
  (LeetCode-style, name only, link don't reproduce full statements if the source is
  copyright-sensitive) over invented ones.

- **`prediction_checkpoints` do not apply** (`runtime:"none"` for every node in this phase) —
  leave `visualization`/`viz` fields absent from the JSON entirely.

Return the JSON array only (plus a short "Sources consulted" list). Prefer primary sources that
are collections of real interview/competitive problems (a well-known problem-pattern guide,
Wikipedia's algorithm-design-technique overview pages) over generic blog summaries.
