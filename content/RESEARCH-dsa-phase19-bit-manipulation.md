# DSA deep-research — Phase 19: Bit Manipulation (paste into Gemini)

> **How to run:** In Gemini (Deep Research mode recommended), paste the whole of
> `content/PROMPT-dsa-research.md` from the `ROLE` heading through the `OUTPUT FORMAT`
> section FIRST (the shared contract + JSON schema + field rules). Then paste everything
> below. One phase per chat.
>
> **Two-step (Deep Research):** let it produce the prose report, then send the
> "Convert your research above into a JSON array…" extraction prompt from the contract.
> Save the JSON to `content/research/dsa/phase-19.json` (one object per node, keyed by
> slug). Hand it back to Claude for authoring.

---

## PHASE 19 — BIT MANIPULATION (3 nodes)

Research each node into one JSON object per the schema. Kind tag per node:
**C** = `kind_hint:"concept"` (renderer `none`), **D** = `kind_hint:"trace"` (steppable).

1. **Bitwise operators** — C — `bitwise-operators`
2. **Single number (XOR)** — D — `single-number-xor`
3. **Counting bits** — D — `counting-bits`

## PHASE-SPECIFIC EMPHASIS (do NOT skip)

Smallest phase in the roadmap but easy to make either too shallow (just a table of operators) or
too deep (full two's-complement derivation). Research accordingly:

- **`bitwise-operators` must deliver each operator's use-case, not just its truth table** — AND
  for masking/checking bits, OR for setting bits, XOR for toggling AND (crucially, the fact that
  powers the next node) `x ^ x = 0` and `x ^ 0 = x` with XOR being commutative + associative. NOT
  and two's complement need only a one-paragraph practical gotcha ("why does `~5` print `-6`"),
  not a derivation. Shifts: confirm `<<`/`>>` as multiply/divide by powers of 2, and research the
  arithmetic-vs-logical right-shift distinction for NEGATIVE signed numbers as a named gotcha
  (language-dependent, don't resolve for every language). Also collect the standard idioms:
  `x & 1` (odd/even test), `x & (x-1)` (clear lowest set bit — this feeds `counting-bits`'
  Kernighan-trick forward-pointer), `x & -x` (isolate lowest set bit), `1 << k` (bit-k mask).

- **`single-number-xor` must research the XOR-cancellation proof concretely**, not just state the
  trick: because XOR is commutative + associative, XOR-ing every array element together lets every
  PAIRED value cancel to 0 (`a^a=0`), leaving only the unpaired value. Research and confirm the
  complexity contrast honestly: this is `O(n)` time / `O(1)` space, vs a hash-set approach at
  `O(n)` time / `O(n)` space, or sort-then-scan at `O(n log n)` time / `O(1)` space — the XOR
  trick's specific payoff is BOTH linear time AND constant space together. Also research (to name
  as an explicit "doesn't generalize" boundary, not to solve) that the every-element-appears-THREE-
  times variant needs a different technique.

- **`counting-bits` must research the DP-recurrence formulation as the primary trace**
  (`bits[i] = bits[i>>1] + (i&1)`, reusing the already-computed smaller-index answer) and name
  Brian Kernighan's `x & (x-1)`-loop as a secondary, non-DP alternative in one paragraph, not
  co-taught as the main trace. Make the connection to phase 18's DP thinking (`state-and-
  transition`) explicit if the research surfaces it naturally — this node is a compact real-world
  instance of "reuse a smaller already-solved subproblem."

- **`prediction_checkpoints`**: for `single-number-xor`, pause right before folding in the next
  array element and ask "what will the running XOR value become?" For `counting-bits`, pause right
  before computing `bits[i]` and ask "which earlier index does this reuse, and what's the result?"

- **Renderer hints (`visualization.renderer`):** both trace nodes → `bits` (binary-row display,
  active-column highlighting). Give 2–3 `interactive_inputs` each (a small clean case, an edge
  case like an all-zero or single-element input) with one-line `why`.

- **`failure_signals` / `when_not_to_use`:** bit tricks are powerful but easy to reach for as
  premature micro-optimization — name when a plain hash-set/array approach is just as fast and far
  more readable, and bit-packing only pays off at real scale or in memory-constrained contexts.

Complexity as plain text (`O(n)`, `O(log n)` for shift-counting loops). Cite a reputable bit-
manipulation reference (competitive programming handbook, Wikipedia, or a language's official docs
on integer representation) as primary. Return the JSON array only (plus a short "Sources
consulted" list).
