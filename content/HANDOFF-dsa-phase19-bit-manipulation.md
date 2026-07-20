# Antigravity handoff — DSA phase 19 (Bit Manipulation)

Phase 19 = **3 nodes** (`_TODO-dsa.md` section 19): 1 `concept` + 2 `dsa` trace. Smallest phase in the
roadmap, but the viz infra behind it is the **most broken pipeline found so far** — worse than phase 16's
graph pipeline (which rendered wrong colors; this one would crash the page).

> **Infra reality check — READ THIS FIRST. It is BROKEN, not just miscolored.** The `bits` op family
> (`BITS_INIT`, `XOR_STEP`, `SET_BIT`) is declared in `events.js`, `bitsReducer` exists in `compile.js`,
> `BitsViz.jsx` exists, and `renderers/index.js` maps `view:'bits' -> BitsViz`. **But the frame shape the
> reducer emits and the shape the renderer reads do not match AT ALL — this would throw a runtime error,
> not just render wrong.** Five concrete defects below. **Pass 0 (Claude) MUST land before Pass 2
> (generators) starts.** Pass 1 (prose) is unblocked and can run in parallel — it doesn't touch this code.

Three passes:
- **Pass 0 — CONTRACT FIX (Claude, BLOCKING for pass 2):** rebuild the bits frame contract from scratch.
  Spec below. **Antigravity: do not do pass 0.**
- **Pass 1 — PROSE (Antigravity):** author all 3 lessons' text. **NO `viz` block.**
- **Pass 2 — VIZ (Antigravity from the Claude spec, per D-015):** 2 generators + goldens. **Claude
  browser-verifies before anything is "done"** — goldens cannot catch a JSX render crash, and this phase
  is exactly the kind of pipeline that crashes rather than misrenders.

**Gate for pass 1: `python content/validate.py` — zero errors. Do NOT run the frontend. Do NOT commit.**
Tick boxes in `content/_TODO-dsa.md` as each file lands green.

---

## The 3 nodes (slugs EXACT from `_TODO-dsa.md`; difficulty is Claude's best-first call — `seed_dsa.py`
does not have phase 19 nodes yet, that's separate Claude-side wiring)

| slug | title | kind | difficulty | generator (pass 2) |
|---|---|---|---|---|
| `bitwise-operators` | Bitwise operators | **C** concept | easy | — (`runtime:"none"`) |
| `single-number-xor` | Single number (XOR) | **D** dsa | medium | `single-number-xor` |
| `counting-bits` | Counting bits | **D** dsa | medium | `counting-bits` |

**Build order:** `bitwise-operators` FIRST and thoroughly — every trace node assumes AND/OR/XOR/shift are
already familiar. Then `single-number-xor` (the XOR-cancellation trick), then `counting-bits` (which can
optionally build on XOR familiarity but is really a DP-shaped bit trick — a nice forward-echo of phase 18).

---

## Research source

The phase-19 deep-research paste-ready prompt does not exist yet — write
`content/RESEARCH-dsa-phase19-bit-manipulation.md` following the exact convention of
`content/RESEARCH-dsa-phase17-greedy.md` before running it. **The per-node must-hits below are the
correctness spine — author from them now; do not wait for the research.** This is bit-twiddling basics,
not contested; use research to enrich real engineering examples (bitmasks, flags, hashing) and sourcing.

---

## Pass 1 — the 3 lessons (PROSE only, NO `viz`)

Follow `content/PROMPT-dsa.md` (⛔ no-viz boundary, FIVE questions, QUALITY BAR). Copy the shape of
`content/roadmaps/dsa/merge-sort.json` (gold `dsa` exemplar) and **OMIT its `viz` block** for the 2 trace
nodes; the concept node copies `content/roadmaps/dsa/what-is-an-algorithm.json` and sets
**`runtime: "none"`**.

**`dsa` branch required fields:** `why_it_exists {problem, better_idea}`, `mental_model {intuition,
repeated_decision, ...}` — **`repeated_decision` REQUIRED**, `explanation` OR `sections` (teaching body
with a hand-trace **on binary strings, not decimal**), `common_mistakes` (≥1), `recall_questions` (≥3),
`oa_questions` (≥2), `sources` (2–5 URLs).

**`concept` branch required fields:** `overview {what, why}`, `why_learning_this`, `common_mistakes`,
`recall_questions`, `practice_tasks`, `understanding_checks` (**≥2**), `sources`.

### Phase-wide rules

1. **Every hand-trace shows the actual binary representation**, not just decimal values with a verbal
   description — this phase is fundamentally about bit patterns, and a trace that stays in decimal the
   whole time defeats the point. Use small numbers (4–8 bits is plenty).
2. **Name the language-specific gotchas honestly** (fixed-width overflow, signed vs unsigned shift
   behavior) without going deep into any one language's semantics — one clear paragraph, not a spec.
3. **Complexity as plain text** — `O(n)`, `O(log n)` for shift-counting loops. Never LaTeX.

### Per-node must-hits (the correctness spine)

**`bitwise-operators`** (C, easy) — the vocabulary every trace node assumes.
- **AND (`&`):** 1 only where BOTH bits are 1 — used to check/clear specific bits, and to mask ("keep
  only these bits").
- **OR (`|`):** 1 where EITHER bit is 1 — used to set specific bits (turn a flag on).
- **XOR (`^`):** 1 where the bits DIFFER — used to toggle bits, and (the property that powers
  `single-number-xor`) **`x ^ x = 0`** and **`x ^ 0 = x`**, and XOR is commutative + associative (order
  and grouping don't matter — teach this explicitly, it's the entire proof behind the next lesson).
- **NOT (`~`):** flips every bit — mention two's-complement briefly (`~x = -x - 1` for signed integers) as
  a "why does `~5` print `-6`" gotcha, don't derive two's complement from scratch.
- **Shifts (`<<`, `>>`):** left shift by `k` multiplies by `2^k`; right shift by `k` divides by `2^k`
  (floor division). Name the trap: right-shifting a NEGATIVE signed number can behave differently
  (arithmetic vs logical shift) depending on language — flag it, don't resolve it for every language.
- **Common idioms to name (not derive in depth):** `x & 1` tests the lowest bit (odd/even); `x & (x-1)`
  clears the lowest set bit (used in `counting-bits`' Brian Kernighan trick — forward-pointer);
  `x & -x` isolates the lowest set bit; `1 << k` builds a mask for bit `k`.
- `understanding_checks` must catch: confusing AND/OR's use-cases (masking vs setting) and mixing up
  which shift direction multiplies vs divides.

**`single-number-xor`** (D, medium) — `repeated_decision`: *"XOR this number into my running result — for
any value that appears twice, its two XORs will cancel to 0, so whatever survives at the end is the
answer."*
- what: given an array where every element appears TWICE except one, find the one that appears once, in
  `O(n)` time and `O(1)` space.
- **The trick, stated as a direct consequence of `bitwise-operators`' XOR facts:** XOR every element
  together. Because XOR is commutative and associative, pairs can be reordered to cancel: `a ^ a ^ b = 0
  ^ b = b`. Whatever is left after all cancellations IS the unpaired element.
- Hand-trace on a small array (e.g. `[4, 1, 2, 1, 2]`) showing the running XOR value bit-by-bit at each
  step, ending at `4`.
- **Name why sorting-then-scanning or a hash-set approach also work but cost more** (`O(n log n)` time or
  `O(n)` EXTRA space respectively) — the XOR trick's whole payoff is `O(1)` space, make that the explicit
  sell.
- misconceptions: trying to use a running SUM instead of XOR (sum doesn't cancel, and can overflow);
  assuming this generalizes to "every element appears THREE times except one" without modification (it
  doesn't — that's a different, harder trick; name the gap, don't solve it).

**`counting-bits`** (D, medium) — `repeated_decision`: *"can I reuse the bit-count I already computed for
a smaller number that this one is built from, instead of recounting from scratch?"*
- what: given `n`, compute the number of set bits (1s) in the binary representation of every integer from
  `0` to `n`. Naive: count bits of each number independently, `O(n log n)` total (each count costs
  `O(log n)`).
- **The DP-shaped trick (this is `bitwise-operators` meeting phase 18's thinking, make the cross-link
  explicit):** `bits[i] = bits[i >> 1] + (i & 1)` — the number of set bits in `i` equals the set bits in
  `i` with its last bit dropped, plus whether that last bit was 1. This is `state-and-transition` applied
  to bit counting: state = "bit count of `i`," transition = "reuse the answer for `i >> 1`." `O(n)` total,
  `O(1)` extra work per number.
- Alternative worth naming in one line: **Brian Kernighan's trick**, `x & (x-1)` clears the lowest set
  bit — looping this until `x` is `0` counts bits in `O(popcount)` per number rather than `O(log n)`; useful
  standalone but doesn't reuse PREVIOUS answers the way the DP recurrence does, so it's not the primary
  trace here.
- Hand-trace `n=7` fully, building the `bits[]` array from `0` to `7`, showing the `i>>1` lookup and
  `i&1` addition at each step.
- misconceptions: recomputing each count independently (misses the whole point — this node exists
  specifically to demonstrate reusing smaller subproblem answers, i.e. it's a mini phase-18 example in
  disguise); getting the recurrence direction backwards (`i >> 1` must be a SMALLER, already-computed
  index).

### Cross-links
`bitwise-operators` unlocks both trace nodes. `single-number-xor` `related` → forward-pointer to a future
"single number II/III" (every-element-appears-3-times, or two-unique-elements) if ever added — name the
gap. `counting-bits` `related` → phase 18 `state-and-transition` (explicit "this is a 1D DP in disguise"
cross-link) and forward-pointer to `hash-set-membership`-style problems (phase 4) as the space-cost
alternative for `single-number-xor`.

## ASCII-only in JSON
`->` not an arrow glyph, `--` not an em-dash, straight quotes, `>=`/`<=`/`<<`/`>>` as plain ASCII
operators (never render actual binary literals with unicode).

## Process (pass 1)
1. Write `content/RESEARCH-dsa-phase19-bit-manipulation.md` (paste-ready prompt) — can run in parallel
   with prose authoring, not a blocker.
2. Read `merge-sort.json` (shape, minus viz) + `content/PROMPT-dsa.md` (QUALITY BAR items 6–7) + the
   inlined must-hits above.
3. Write the 3 files — no `viz` block; each `dsa` node MUST have `mental_model.repeated_decision`.
4. `python content/validate.py` → zero errors. Tick `content/_TODO-dsa.md`.
5. Standing pipeline: Sonnet/Gemini lesson critic → apply fixes → re-critic.

---

## Pass 0 — CONTRACT REBUILD (Claude only, blocks pass 2)

Verified against the current tree. Five concrete defects — this pipeline has never rendered a real trace:

**P0-1 — `frame.bits` is an OBJECT; `BitsViz` reads it as an ARRAY. This crashes, not misrenders.**
`bitsReducer`'s `BITS_INIT` sets `state.bits = { numbers: args.numbers || [] }` — a single object with a
`numbers` key. `compile.js` emits `frame.bits = { ...state.bits }` (still the same object shape).
`BitsViz.jsx` destructures `const { bits = [] } = frame` and immediately calls `bits.map(...)` and reads
`bits.length` — since `frame.bits` is a defined OBJECT (not `undefined`), the `= []` default never
applies, `bits.length` is `undefined` (not `0`, so the empty-check doesn't short-circuit), and
`bits.map` throws `TypeError: bits.map is not a function`. **Any lesson that reaches this renderer
crashes the page.**
Fix: `BITS_INIT` should build `state.bits` as an ARRAY of row objects directly:
`state.bits = (args.numbers || []).map((value, idx) => ({ id: idx, value, label: args.labels?.[idx] }))`
— matching the `{id, value, label}` shape `BitsViz` already expects per-row (confirmed by its
`b.id`/`b.value`/`b.label` usage).

**P0-2 — prop-name mismatch: `bitsActiveCol` vs `activeCol`.**
`compile.js` emits the frame key `bitsActiveCol`. `BitsViz.jsx` destructures `frame.activeCol` (no
`bits`-prefix). Result: the active-column highlight NEVER appears, even once P0-1 is fixed. Fix in
`BitsViz.jsx` (matches every other family's naming — `nodeTags` not `treeNodeTags`, etc., so renaming the
frame key to plain `activeCol` in `compile.js` is the more consistent fix; either side works, pick one).
**Prefer fixing `compile.js` to emit `activeCol`** — it's the renderer-facing name and matches how every
other renderer's frame keys read (unprefixed from the renderer's point of view).

**P0-3 — `bitTags` is read by the renderer but never emitted anywhere.**
`BitsViz` destructures `frame.bitTags = {}` and looks up `bitTags[b.id]` to decide whether a row renders
as `result` (teal) or `active` (purple). `compile.js`'s frame object has no `bitTags` key at all — same
class of bug as phase 16's P0-6 (a derive/tag map the renderer wants but the compiler never produces).
Fix: add `state.bitTags = {}` to the reducer's local state, a `MARK_BIT { id, tag }` case (or reuse
`SET_BIT` for this — see P0-4) that sets it, and emit `bitTags: state.bits ? { ...state.bitTags } :
undefined` in `compile.js`'s frame object (same pattern as `cellTags`/`nodeTags`).

**P0-4 — `SET_BIT` is a complete no-op stub.**
`bitsReducer`'s `case 'SET_BIT': // modify bits if needed` does literally nothing — no state mutation at
all. Any generator emitting `SET_BIT` to show an individual bit toggling (needed for `counting-bits`'
per-row highlight, and useful for `single-number-xor` to mark which row is the running-XOR accumulator)
produces zero visual change. Fix: give `SET_BIT { id, tag }` a real body —
`state.bitTags[args.id] = args.tag` (reusing the P0-3 tag map — one op covers both "mark this row's
purpose" and "which row is currently active" depending on whether the generator also emits
`XOR_STEP`/an active-column pointer alongside it).

**P0-5 — no bits derive for prediction checkpoints.**
`predict.js`'s `DERIVES` has nothing bits-shaped, and `validate.py` rejects any `viz.predictions[].derive`
not registered there. Add at minimum:
- `next_xor_result` — the running XOR value after the next `XOR_STEP` (gates "what does XOR-ing this
  value in produce?" for `single-number-xor`).
- `next_bit_count` — the value `bits[i]` will be set to next, derived from `bits[i>>1] + (i&1)` (gates
  the recurrence-application step for `counting-bits`).

**After P0-1 through P0-5, re-verify by hand:** a minimal generator emitting `BITS_INIT { numbers: [4, 1,
2] }` then `XOR_STEP { col: 2 }` then `SET_BIT { id: 0, tag: 'result' }` should render 3 binary rows, the
correct column highlighted, and row 0 colored teal — with zero console errors. There is currently no
golden covering this family; add one covering just the reducer/frame shape (not a full algorithm) as part
of Pass 0 so Pass 2's generators have a regression net from day one.

---

## Pass 2 — the 2 generators (Antigravity, from this spec, per D-015)

**Do not start until Pass 0 has landed — the CURRENT pipeline crashes on first render.** One file per
algorithm in `frontend/src/dsa/generators/<key>.js`, exporting a named `*Events(input)` function,
registered in `frontend/src/dsa/registry.js`. Pattern to copy for the general shape:
`frontend/src/dsa/generators/kadane.js` (running-accumulator style, close to `single-number-xor`'s
running-XOR); `content/roadmaps/dsa/climbing-stairs-fibonacci` generator (phase 18, once it lands) for
`counting-bits`' index-reuse recurrence shape.

**Hard rules (same as every prior phase):** pure deterministic generator; events are the source of
truth, never author frames; `{ op, args, step_id, note }`, `step_id` monotonic; default inputs small
(4–6 numbers, 4–8 bit width) and hand-traceable, matching each lesson's hand-trace exactly.

| generator key | ops used | the moment the viz must sell |
|---|---|---|
| `single-number-xor` | `BITS_INIT`, `XOR_STEP`, `SET_BIT {tag:'result'}` | the running-XOR row updating bit-by-bit as each array element is folded in, ending on the lone survivor tagged `result` |
| `counting-bits` | `BITS_INIT`, `SET_BIT {tag:'computed'}` per index | each row `i` visibly reusing row `i>>1`'s already-computed value, plus the `i&1` addition |

**Goldens:** determinism; one frame per event; per-algorithm — `single-number-xor`'s final result matches
a hand-computed answer; `counting-bits`' full output array matches `Python's bin(i).count('1')` for a
small range. Print an op-count fingerprint like existing goldens.

**Then STOP and report.** Claude runs the browser pass (bit rows render as an array without crashing —
this is the phase where a render crash is the LIKELY failure mode, not colors-only; active column
highlights correctly; result/computed tags show distinct colors; no console errors).

---

## Boundaries
- Pass 1: touch only `content/roadmaps/dsa/*.json`, `content/_TODO-dsa.md`, and the new
  `content/RESEARCH-dsa-phase19-bit-manipulation.md`. No `viz`/`animation`/`image`.
- Pass 2: touch only `frontend/src/dsa/generators/*` + `registry.js`. Do not edit `compile.js`,
  `events.js`, `predict.js`, or any renderer — that is Pass 0, Claude-owned shared contract.
- No commits, no pushes, no DB/seed changes.
- If the spec fights reality, implement the closest faithful version and FLAG it in
  `content/REPORT-dsa-phase19.md` — do not silently redesign.
