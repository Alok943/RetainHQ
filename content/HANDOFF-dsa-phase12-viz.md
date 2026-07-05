# Antigravity handoff -- DSA phase 12 (Backtracking) VIZ build

Add execution-trace visualizers to the 5 backtracking lessons. **Prose is done + verified; this pass
adds the `viz` layer only.** You already built the renderers (`TreeViz`, `GridViz`) -- this builds the
GENERATORS + compile reducers + `viz` blocks that feed them.

> **Verification is NOT optional and NOT yours to sign off:** goldens catch trace regressions but CANNOT
> catch JSX render crashes. After you finish, hand back to Claude to browser-verify each lesson renders
> at `/roadmaps/dsa/learn/<slug>`. A past renderer change shipped a JSX crash the goldens passed clean.

## The architecture (follow it exactly -- see `docs/dsa-viz-implementation-plan.md` + existing code)
Pure generator `(input) -> {input, events}` (golden-tested, deterministic) -> `compile.js` folds events
into per-step FRAMES -> a renderer draws `frame`. A frame's **`view`** field selects the renderer via
`renderers/index.js` (`array|tree|grid|graph|list|intervals|bits`, default `array`).
- **Study exemplars:** `generators/merge-sort.js` (recursion trace + `merge-sort.golden.mjs`) and any
  registered array generator. Reuse the op vocabulary where it fits; extend `compile.js` consistently.
- Each generator MUST get a `*.golden.mjs` and be added to `GENERATORS` in `registry.js`.

## Renderer targets (you built these -- read their `frame` contracts before emitting events)
- **`GridViz`** consumes `frame.grid = {rows, cols, cells, labels}` + `cellTags` (`queen|attacked|path|max`)
  + `readCells`. Frame `view: "grid"`. Built for the board.
- **`TreeViz`** consumes `frame.tree = {nodes: {id: {x, y, left, right, ...}}}` + `nodeTags`
  (`visited|matched|path|invalid|inserted`) + `nodeReturns` + `cursor`. Frame `view: "tree"`. For the
  state-space / decision tree. NOTE: nodes carry x/y layout -- decide whether the generator emits layout
  or `compile.js` computes it (prefer compile-side layout so generators stay pure data).

## Per-lesson build
| lesson | renderer / view | what the trace shows | default input |
|---|---|---|---|
| `n-queens` | **GridViz** (`grid`) | NxN board; place a queen row by row (`queen` tag), shade its column + both diagonals (`attacked`), backtrack = remove + unshade; mark a full board as solution. | **N=4** (smallest solvable; the lesson's own hand-trace uses it) |
| `backtracking-template` | **TreeViz** (`tree`) | The generic choose/explore/un-choose decision tree growing DFS; tag the current `path`, mark dead-ends `invalid`, mark recorded states `matched`. | small generic, e.g. 2-3 choices deep |
| `subsets` | **TreeViz** (`tree`) | The include/exclude binary tree; every node is a subset (`matched` at record). | `[1,2,3]` |
| `permutations` | **TreeViz** (`tree`) | Per-position branching (shrinking factor); `used[]` reflected by pruned branches; leaves = full perms. | `[1,2,3]` |
| `combination-sum` | **TreeViz** (`tree`) | Target-driven tree; reuse = re-enter same index; prune (`invalid`) when candidate > remaining. | `candidates=[2,3,6,7], target=7` |

## Op vocabulary (reuse existing; add these for the backtracking family, fold in `compile.js`)
- Tree family: `CALL`/`RETURN` (descend/ascend = push/pop a decision-tree node), `CHOOSE`/`UNCHOOSE`
  (apply/undo a choice -> tag path vs backtrack), `RECORD` (a solution -> `matched`), `PRUNE` (dead
  branch -> `invalid`). Each event carries the node id + the choice made.
- Grid family (n-queens): `PLACE`/`REMOVE` (queen at r,c), `ATTACK`/`UNATTACK` (mark/unmark a column +
  diagonals set), `SOLUTION` (full valid board). `compile.js` folds these into `grid.cells` + `cellTags`.
- If `compile.js` already has `view:'tree'`/`'grid'` reducers (you may have added them with the
  renderers), extend them; otherwise add per-family reducers mirroring the existing array/stack ones.

## `viz` block to add to each lesson (schema -- see any registered dsa lesson)
`viz = { generator, default_input, invariants{...}, steps[{id,label}], predictions[]? }`. The lessons are
`dsa`-kind and already have `mental_model.repeated_decision` (required for gated viz). Predictions
(predict-before-reveal) worth adding:
- `subsets`/`permutations`: predict the NEXT choice, or "is this branch a dead-end / a solution?"
- `combination-sum`: predict whether the current candidate gets PRUNED (candidate > remaining).
- `n-queens`: predict whether a given column in the current row is SAFE.
Anchor predictions via `at_op`/`at_step`; use a registered `derive` from `predict.js` (add a new derive
if the backtracking decision needs one -- e.g. `next_choice`/`is_safe` -- keeping it a pure fn of events).

## Gate + process
1. Build 5 generators (+ compile reducers as needed) -> `*.golden.mjs` for each -> `npm run golden` green.
2. Register in `registry.js`. Add the `viz` block to each of the 5 lessons.
3. `python content/validate.py` green (it checks `viz.generator` is registered). `node frontend/scripts/sync-content.mjs`.
4. Do NOT commit. **Hand back to Claude for the browser render-verify pass** (list exactly what you
   changed: generators, golden files, compile.js reducers, registry keys, and which lessons got viz).

> Bonus if quick: `lower-bound` and `upper-bound` lessons have their generators ALREADY registered but
> are missing the `viz` block -- adding those two blocks is a 2-line win (generator=`lower-bound`/
> `upper-bound`, small sorted `default_input`).
