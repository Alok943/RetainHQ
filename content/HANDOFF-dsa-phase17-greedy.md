# Antigravity handoff — DSA phase 17 (Greedy)

Phase 17 = **5 nodes** (`_TODO-dsa.md` section 17): 2 `concept` + 3 `dsa` trace. Follows directly from
phase 16's `minimum-spanning-tree-kruskal` (Kruskal's cycle check IS a greedy choice — cross-linked).

> **Infra reality check — READ THIS FIRST.** Unlike phase 16 (graph pipeline badly broken), the interval
> pipeline is **almost right**: `INTERVAL_INIT`/`SELECT`/`SKIP`/`MERGE_INTERVAL` are declared, `IntervalViz`
> exists and renders bars on a number line. **One real defect:**
>
> **P0-1 — tag frame-key mismatch.** `intervalsReducer` (compile.js) tags an interval by mutating
> `intv.state` directly on the interval object (`intv.state = 'selected' | 'skipped' | 'merged'`). But
> `IntervalViz.jsx` reads a separate map, `frame.intervalTags[inv.id]`, which `compile.js` **never emits**
> (only `frame.intervals` is emitted; there is no `intervalTags` key at all). Result: every interval
> renders `idle` (blue) forever — select/skip/merge never shows a color change.
> **Fix (pick ONE, do not do both):** (a) simplest — `IntervalViz` reads `inv.state` directly instead of
> a separate tags map (`const tag = inv.state;`), since the reducer already writes it onto the interval
> object that IS in the frame; or (b) make `intervalsReducer` also populate `state.intervalTags[id] = tag`
> and have `compile.js` emit it (mirrors the tree/graph/grid convention). **Prefer (a) — it's a one-line
> renderer fix, no compile.js/events.js change, and the golden frame shape doesn't move.**
> `jump-game` needs no fix — it uses the already-solid `ArrayViz` + `vars` (same pattern as `kadane`).
> **Pass 0 (Claude) is tiny and does NOT block Pass 1 prose** — author now; Claude lands the one-line fix
> before Pass 2 generators.

Three passes:
- **Pass 1 — PROSE (Antigravity, THIS packet):** author all 5 lessons' text. **NO `viz` block.**
- **Pass 0 — ONE-LINE FIX (Claude, before Pass 2 only):** `IntervalViz.jsx` reads `inv.state` not
  `intervalTags[inv.id]`. Trivial; not a prose blocker.
- **Pass 2 — VIZ (Antigravity from this spec, per D-015):** 3 generators + goldens. Claude
  browser-verifies before anything is "done."

**Gate for pass 1: `python content/validate.py` — zero errors. Do NOT run the frontend. Do NOT commit.**
Tick boxes in `content/_TODO-dsa.md` as each file lands green.

---

## The 5 nodes (slugs EXACT from `_TODO-dsa.md`; titles/difficulty from `backend/seed_dsa.py`, which
already defines all 5 under phase `"Greedy"` — do NOT invent difficulties, they are authoritative there)

| slug | title | kind | difficulty | generator (pass 2) |
|---|---|---|---|---|
| `why-greedy-works` | Why greedy works | **C** concept | medium | — (`runtime:"none"`) |
| `why-greedy-fails` | Why greedy fails | **C** concept | medium | — (`runtime:"none"`) |
| `interval-scheduling` | Interval scheduling | **D** dsa | medium | `interval-scheduling` |
| `merge-intervals` | Merge intervals | **D** dsa | medium | `merge-intervals` |
| `jump-game` | Jump game | **D** dsa | medium | `jump-game` |

**Build order = table order.** `why-greedy-works` first (the exchange-argument proof — everything else
is proof-by-example of it). `interval-scheduling` next (the cleanest exchange-argument instance, and the
node `why-greedy-works` should forward-reference). Then `merge-intervals` (same "sort intervals" family,
different key/goal — build it right after scheduling so the contrast is fresh). `why-greedy-fails` can
land any time after `why-greedy-works` (it's the counter-lesson). `jump-game` last — a different flavor
of greedy (reachability, not sort-then-scan).

---

## Research source

The phase-17 deep-research paste-ready prompt is `content/RESEARCH-dsa-phase17-greedy.md` (Gemini Deep
Research; prepend the shared contract from `PROMPT-dsa-research.md`). **It has not been run yet.** Output
goes to `content/research/dsa/phase-17.json`, one object per node keyed by slug.

**The per-node must-hits below are the correctness spine — author from them now; do not wait for the
research.** When the research lands, use it to enrich real-world examples and sourcing, not to change the
core facts below (they are standard CLRS greedy-chapter material, not contested).

---

## Pass 1 — the 5 lessons (PROSE only, NO `viz`)

Follow `content/PROMPT-dsa.md` (⛔ no-viz boundary, FIVE questions, QUALITY BAR). Copy the shape of
`content/roadmaps/dsa/merge-sort.json` (gold `dsa` exemplar) and **OMIT its `viz` block** for the 3 trace
nodes; concept nodes copy `content/roadmaps/dsa/what-is-an-algorithm.json` and set **`runtime: "none"`**.

**`dsa` branch required fields:** `why_it_exists {problem, better_idea}`, `mental_model {intuition,
repeated_decision, ...}` — **`repeated_decision` REQUIRED**, `explanation` OR `sections` (teaching body
with a hand-trace), `common_mistakes` (≥1), `recall_questions` (≥3), `oa_questions` (≥2), `sources` (2–5
URLs).

**`concept` branch required fields:** `overview {what, why}`, `why_learning_this`, `common_mistakes`,
`recall_questions`, `practice_tasks`, `understanding_checks` (**≥2**), `sources`.

**Exact shapes `validate.py` enforces (get these wrong and it errors):**
- `why_learning_this` / `common_mistakes` / `recall_questions` / `practice_tasks` / `sources` must each
  be a **non-empty list**. Every `sources[i]` must be a string starting with `http`.
- `recall_questions[i]` must be an object with **both `q` and `answer`** non-empty.
- `understanding_checks[i]` must have **all four** of `type`, `question`, `answer`, `why` non-empty, and
  **`type` must be one of exactly:** `predict-output`, `predict-result`, `explain-behavior`, `find-bug`,
  `choose-model`, `debug-misconception`. No other value validates.
- `runtime: "none"` on concept nodes skips the `code_walkthrough` requirement — that's why concept nodes
  don't need one.

### Phase-wide rules

1. **Greedy is a THINKING PATTERN, not a single algorithm.** Every lesson should name the two
   ingredients that make it valid — the **greedy-choice property** (a locally optimal choice extends to
   a globally optimal solution) and **optimal substructure** — even the trace nodes, briefly.
2. **"Sort by WHAT?" is the repeated decision, and it's different per problem.** Never let the reader
   walk away thinking "greedy = sort and scan" without also knowing *which key* and *why that key*.
3. **State the correctness argument, not just the algorithm.** A greedy lesson that only shows "sort,
   then loop" without the exchange-argument intuition teaches memorization, not understanding.
4. **Complexity as plain text** — `O(n log n)`, `O(n)`. Never LaTeX.

### Per-node must-hits (the correctness spine)

**`why-greedy-works`** (C, medium) — the two formal ingredients, made concrete.
- **Greedy-choice property:** a globally optimal solution can be reached by making the choice that
  looks best *right now*, without reconsidering it later.
- **Optimal substructure:** after the greedy choice, what's left is a smaller instance of the *same*
  problem — solving it optimally + the greedy choice = optimal overall.
- **The exchange argument (teach this concretely, it's the actual proof technique):** to show a greedy
  choice is safe, take ANY optimal solution that doesn't include it, and show you can swap it in without
  making the solution worse. Anchor it to `interval-scheduling`: if an optimal schedule doesn't pick the
  interval with the earliest end time, swap it in for whatever it does pick first — the swap can only
  free up more room, never less. Forward-reference the actual proof to `interval-scheduling`'s hand-trace.
- `repeated_decision` / `invariants` may be `"N/A"` — this node is the theory anchor.

**`why-greedy-fails`** (C, medium) — **the aha-node; a crisp, memorable counterexample.**
- **Coin change with arbitrary denominations:** coins `{1, 3, 4}`, target `6`. Greedy (always take the
  largest coin ≤ remaining) picks `4 + 1 + 1` = 3 coins. Optimal is `3 + 3` = 2 coins. Greedy is WRONG
  here because taking the biggest coin now can block a better combination later — no exchange argument
  exists for this key.
- **0/1 Knapsack:** greedy by value/weight ratio is NOT optimal (unlike the *fractional* knapsack, where
  it is) — because items can't be split, a locally-best ratio pick can leave awkward leftover capacity
  that a different combination would have used better.
- **The diagnostic rule to teach:** greedy fails exactly when NO exchange argument holds — when today's
  locally-best choice can foreclose a better global outcome. **Forward-reference phase 18 explicitly:**
  "when greedy fails, you usually need dynamic programming to explore the choices greedy throws away."
  Put the coin-change counterexample in `mental_model`/`interesting_facts` — it IS the retention hook.
- `repeated_decision` / `invariants` may be `"N/A"`.

**`interval-scheduling`** (D, medium) — `repeated_decision`: *"is this next interval (sorted by end
time) compatible with the last one I picked — does it start at or after the last one's end?"*
- Classic **activity selection**: given intervals, pick the MAXIMUM number of non-overlapping ones.
- **Sort by EARLIEST END TIME** (not start time, not shortest duration — state and reject both wrong
  keys explicitly). Then scan once: greedily take any interval whose start ≥ the last taken interval's
  end.
- **Why end-time is correct (the exchange-argument payoff from `why-greedy-works`):** finishing earliest
  leaves the most room for everything that comes after — any optimal solution can be rearranged to start
  with the earliest-ending interval without losing count.
- Hand-trace on ≤6 intervals showing the sort, then the accept/reject scan.
- Complexity `O(n log n)` (the sort dominates; the scan is `O(n)`).
- misconceptions: sorting by start time (fails — a long early interval blocks later short ones);
  sorting by duration/shortest-first (fails — a classic counterexample: two short overlapping intervals
  vs one long one that doesn't overlap either).

**`merge-intervals`** (D, medium) — `repeated_decision`: *"does this next interval (sorted by start
time) overlap the one I'm currently building — if so, extend it; if not, close it and start a new one."*
- **Different goal from scheduling: COALESCE overlapping intervals into their union**, not select a
  max-count subset. **Sort by START time** (different key from scheduling — call this contrast out
  explicitly, it's the #1 conflation students make between these two nodes).
- Sweep once: keep a "current merged interval"; if the next interval's start ≤ current's end, extend
  current's end to `max(current.end, next.end)`; otherwise push current and start a new one from next.
- Hand-trace on ≤6 intervals with at least one triple-overlap.
- Complexity `O(n log n)`.
- misconceptions: **conflating this with `interval-scheduling`** ("it's the same sort-intervals
  problem") — same family, different key AND different goal; forgetting `max(current.end, next.end)`
  when extending (a fully-nested interval can have an end EARLIER than the current one).

**`jump-game`** (D, medium) — `repeated_decision`: *"has the farthest index I can reach fallen behind
the index I'm currently standing on? If yes, I'm stuck; if no, can this index's jump extend my reach?"*
- Given an array where `nums[i]` = max jump length from index `i`, can you reach the last index?
- **Greedy reachability**, not sort-then-scan (name this as a different flavor of greedy from the two
  interval nodes above). Track `farthest_reachable`, updated as `max(farthest_reachable, i + nums[i])`
  while scanning left to right; if at any point `i > farthest_reachable`, return false (stuck).
- **The invariant:** `farthest_reachable` never needs to be recomputed from scratch — it only grows,
  monotonically, as you scan. One pass, no backtracking.
- Mention the variant in one line: Jump Game II (minimum number of jumps) is a BFS-like layer count over
  the same reachability idea — don't co-teach it, just name it as the natural extension.
- Complexity `O(n)`, `O(1)` space.
- misconceptions: trying to track "the best single jump" instead of the running farthest-reach frontier;
  forgetting to check `i > farthest_reachable` mid-scan (checking only at the end misses getting stuck
  partway through).

### Cross-links
`why-greedy-works` → forward `interval-scheduling`; `why-greedy-fails` → forward `dynamic-programming`
(phase 18 `overlapping-subproblems`). `interval-scheduling`/`merge-intervals` `related` → each other
(contrast pair) and back to `minimum-spanning-tree-kruskal` (phase 16 — same greedy family). `jump-game`
`related` → `sliding-window-variable` (phase 8 — same "moving frontier" invariant shape).

## ASCII-only in JSON
`->` not an arrow glyph, `--` not an em-dash, straight quotes, `>=`/`<=` not the glyphs.

## Process (pass 1)
1. Read `merge-sort.json` (shape, minus viz) + `content/PROMPT-dsa.md` (QUALITY BAR items 6–7) + the
   inlined must-hits above.
2. Write the 5 files — no `viz` block; each `dsa` node MUST have `mental_model.repeated_decision`.
3. `python content/validate.py` → zero errors. Tick `content/_TODO-dsa.md`.
4. Standing pipeline: Sonnet/Gemini lesson critic (`content/RUN-lesson-critic-antigravity.md`) → apply
   fixes → re-critic.

---

## Pass 0 — the one-line fix (Claude only, before Pass 2)

In `frontend/src/dsa/renderers/IntervalViz.jsx`, replace:
```js
const { intervals = [], intervalTags = {} } = frame;
...
const tag = intervalTags[inv.id];
```
with:
```js
const { intervals = [] } = frame;
...
const tag = inv.state;
```
No `compile.js` / `events.js` change — `state.intervals.map(i => ({...i}))` already carries `.state`
onto every frame (compile.js line ~454). Re-run `npm run golden` after (should be a no-op — no golden
currently exercises intervals). Verify by hand: any trace emitting `SELECT`/`SKIP`/`MERGE_INTERVAL`
should now show the interval bar changing color.

---

## Pass 2 — the 3 generators (Antigravity, from this spec, per D-015)

**Do not start until Pass 0's one-line fix has landed.** One file per algorithm in
`frontend/src/dsa/generators/<key>.js`, exporting a named `*Events(input)` function, registered in
`frontend/src/dsa/registry.js`. Pattern to copy: `frontend/src/dsa/generators/kadane.js` (for
`jump-game`'s `vars`-based running pointer) and `frontend/src/dsa/generators/combination-sum.js`
(general shape).

**Hard rules (same as every prior phase):** pure deterministic generator, no `Math.random`/`Date.now`;
events are the source of truth, never author frames; `{ op, args, step_id, note }`, `step_id` monotonic;
default inputs small and hand-traceable (5–7 intervals / a 6–10 element jump array) and must match the
lesson's hand-trace.

| generator key | ops used | the moment the viz must sell |
|---|---|---|
| `interval-scheduling` | `INTERVAL_INIT`, `SELECT`, `SKIP` | the sorted-by-end-time order, then each interval accepted (green) or skipped (grey) against the last-accepted end |
| `merge-intervals` | `INTERVAL_INIT`, `MERGE_INTERVAL` | the sorted-by-start-time sweep, overlapping bars visually coalescing into one wider merged bar |
| `jump-game` | array family (`POINT`, `WRITE`, `MARK`, `DONE`) + `VAR` for `farthest_reachable` | the farthest-reach pointer creeping forward, then freezing (stuck) if the scan index ever passes it |

> **There is NO `ARRAY_INIT` op** — the array family is
> `['COMPARE','SWAP','MOVE','WRITE','SPLIT','MERGE_DONE','POINT','SET','WINDOW','MARK','DONE']`, and
> `compile(input, events)` seeds `state.array` from its `input` argument directly. A generator returns
> `{ input, events }`; the initial array comes from `input`, not from an init event. (Interval and bits
> generators DO need their `INTERVAL_INIT` / `BITS_INIT` first event — only the array family is seeded
> from `input`.)

`INTERVAL_INIT { intervals: [{id, start, end}] }` first for both interval generators. `jump-game` reuses
the ArrayViz + `vars` pattern from `kadane.js` — emit a `VAR { name:'farthest', value }` each step so the
frontier is visible as a live number, plus a pointer/cursor on the current scan index.

**Goldens:** determinism; one frame per event; per-algorithm — `interval-scheduling`'s accepted count
matches a hand-computed max; `merge-intervals`'s output list matches a hand-computed merge; `jump-game`'s
final reachability matches a hand-computed true/false. Print an op-count fingerprint like existing
goldens.

**Then STOP and report.** Claude runs the browser pass (colors actually change on select/skip/merge, the
jump-game frontier number updates live, no console errors) — goldens cannot catch a JSX/prop-shape bug
(the same class of bug this phase's Pass 0 exists to fix).

---

## Boundaries
- Pass 1: touch only `content/roadmaps/dsa/*.json` + `content/_TODO-dsa.md`. No `viz`/`animation`/`image`.
- Pass 2: touch only `frontend/src/dsa/generators/*` + `registry.js`. Do not edit `compile.js`,
  `events.js`, `predict.js`, or any renderer (Pass 0 is Claude-owned, already scoped above).
- No commits, no pushes, no DB/seed changes.
- If the spec fights reality, implement the closest faithful version and FLAG it in
  `content/REPORT-dsa-phase17.md` — do not silently redesign.
