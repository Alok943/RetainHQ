# DSA Visualizations — Implementation Plan for Phases 12–19

Claude-owned engineering design for the renderers the remaining DSA phases need. Grounded in the
existing `frontend/src/dsa/` pipeline (events -> compile -> frames -> renderers -> Player). This is a
build plan, not a contract — read it, then implement in the order in §7.

---

## 0. Why not 3D (the question that started this)

3D (three.js / WebGL / rendered boards) is the **wrong** investment for every visualization below,
and it's worth being precise about why, because it looks impressive in a demo:

1. **Every DSA structure here is intrinsically 2D or 1D.** An array is a row. A tree is a 2D
   node-link layout. A graph is a planar-ish node-link layout. A DP table is a matrix. N-Queens is an
   8x8 grid. The *information* — pointers, visited-sets, the recursion frontier, the invariant — lives
   in position and color, not depth. A third axis adds occlusion, camera state, and lighting that
   actively **hide** the thing being taught (a queen behind another queen; a graph node rotated out of
   view). The pedagogy gets *worse*, not better.
2. **It breaks the architecture.** The whole system's value is that the **event trace is the single
   source of truth** and renderers are pure `frame -> SVG/DOM`. A 3D scene graph is stateful, imperative,
   and can't be scrubbed frame-accurately without reimplementing the compile/frame model inside the GPU
   layer. You'd fork the moat to get a worse teacher.
3. **Cost profile is all downside.** New heavy dependency, mobile GPU/perf problems, accessibility loss
   (no DOM to read), larger bundles, and a rendering path that shares nothing with the 30 generators
   already shipped.
4. **It's the "AI-slop demo" aesthetic** the design direction explicitly rejects. Flat, precise,
   Bloomberg-terminal-for-memory — motion where motion *means* something (a value landing, a frame
   popping), not spectacle.

The one legitimate use of depth — showing the *call stack growing* in recursion/backtracking — is
already handled better in 2D by the `StateMachine` call-stack panel. **Verdict: build the 2D renderers
below. Spend the effort on layout quality and animation of the *right* transitions.**

---

## 1. Current architecture (recap — what you're extending)

```
lesson JSON  viz.generator ─────────────┐
                                         ▼
generators/<algo>.js   input ─► { input, events[] }      ← PURE. golden-tested. source of truth.
                                         │  event = { op, args, step_id?, invariant?, note? }
                                         ▼
compile.js             (input, events) ─► frames[]        ← folds events into per-step state snapshots
                                         │                   via per-FAMILY reducers. Frame shape is a
                                         │                   STABLE, byte-golden contract.
                                         ▼
renderers/*.jsx        frame ─► SVG/DOM                   ← pure presentation. ArrayViz, StackQueueViz,
                                         │                   StateMachine.
                                         ▼
Player.jsx             shell: scrub, predict-gate, explain-this-frame, code panel.
```

Key facts that shape everything below:

- **Ops are grouped by family in `events.js`.** Adding a family = add its ops there + a reducer in
  `compile.js`. An **unknown op still produces a frame** (caption + invariant) — graceful degradation.
- **`compile.js` reducers** each take `(state, op, args)`, mutate `state`, return per-frame transient
  bits or `null` ("not my op"). `REDUCERS` is tried in order, first non-null wins.
- **The frame** is a flat snapshot object. Renderers read only from it. New structures = **new additive
  frame keys** (never repurpose existing ones — the golden test guards byte-shape).
- **`registry.js`** maps `viz.generator` -> generator fn. `validate.py` checks the key exists, so a
  lesson can never point at a missing visualizer.

## 2. The ONE architectural gap that blocks everything

`Player.jsx` line 317 **hardcodes `<ArrayViz frame={visFrame} />`** as the main visual. There is no
way to show a tree, graph, grid, or linked list in the primary area today. Stack/queue and the call
stack are only *side-panel* additions (lines 320–325).

**Fix first (enabler for all of §3): a renderer registry + a `view` selector on the frame.**

### 2.1 Add a `view` tag to frames

In `compile.js`, each reducer already knows its family. Add an optional `view` to the returned transient
bits (or infer from the winning reducer). Materialize it on the frame:

```js
// compile.js — in the frame push:
view: result.view || 'array',   // 'array' | 'tree' | 'graph' | 'grid' | 'list' | 'intervals' | 'bits'
```

Default `'array'` keeps every existing lesson byte-identical **except** the new key — so update
`compile-frames.golden.mjs` once (add `view: 'array'` to the snapshot) and it's locked again.

### 2.2 Renderer registry

New file `renderers/index.js`:

```js
import ArrayViz from './ArrayViz.jsx';
import TreeViz from './TreeViz.jsx';
import GraphViz from './GraphViz.jsx';
import GridViz from './GridViz.jsx';
import ListViz from './ListViz.jsx';
import IntervalViz from './IntervalViz.jsx';
import BitsViz from './BitsViz.jsx';

export const MAIN_RENDERERS = {
  array: ArrayViz, tree: TreeViz, graph: GraphViz,
  grid: GridViz, list: ListViz, intervals: IntervalViz, bits: BitsViz,
};
export const rendererFor = (frame) => MAIN_RENDERERS[frame?.view] || ArrayViz;
```

### 2.3 Player picks the renderer

```jsx
// Player.jsx, replacing the hardcoded <ArrayViz .../>:
const MainViz = rendererFor(visFrame);
...
<div><MainViz frame={visFrame} invariants={invariants} /></div>
```

The side panels (`StateMachine`, `StackQueueViz`, `PseudoSteps`, code panel, explain-this-frame) stay
**exactly as-is** — they're structure-agnostic and complement every view. That's the elegance: the call
stack, pointers, and frequency map already work for trees/graphs/DP for free.

**Effort: ~half a day. Do this before any renderer below.**

---

## 3. The renderers, by data structure

Each subsection: the phases it unlocks, the ops, the `compile` state + frame additions, the reducer
sketch, the renderer sketch, and the layout approach. All SVG, all pure `frame -> markup`, all themed
via the existing color constants (steal `C` from `ArrayViz`).

### 3.1 TreeViz — binary trees  ⭐ highest leverage

**Unlocks:** Phase 14 Trees (8 lessons: traversals, BST, validate, LCA, height/diameter), Phase 15
Heaps (binary heap as a tree), Phase 12 backtracking decision trees (subsets/permutations tree), and
Phase 11 `recursion-tree` retrofit. **This single renderer serves ~15 lessons — build it first.**

**Ops (add a `tree` family to `events.js`):**
```
tree: ['TREE_INIT', 'VISIT_NODE', 'MARK_NODE', 'COMPARE_NODE', 'SET_EDGE', 'RETURN_NODE']
```
- `TREE_INIT { nodes:[{id, value, left?, right?, parent?}], root }` — declare the tree once, up front.
- `VISIT_NODE { id }` — the traversal cursor lands here (the "current" node).
- `MARK_NODE { id, tag }` — tag a node `visited | matched | path | invalid | inserted` (color class).
- `COMPARE_NODE { id, against }` — highlight a comparison (BST search: value vs node).
- `RETURN_NODE { id, value? }` — post-order/unwind: annotate the value bubbling up (height, diameter).

**compile state additions:**
```js
tree: null,          // { nodes: Map<id,{value,left,right,parent,x,y}>, root }
nodeTags: {},        // id -> 'visited'|'matched'|'path'|'invalid'|'inserted'
nodeReturns: {},     // id -> value bubbling up (for height/diameter/aggregate lessons)
cursor: null,        // currently-visited node id
```

**Reducer:** `TREE_INIT` builds the node map and runs **layout once** (see below), storing `x,y` per
node. `VISIT_NODE` sets `cursor`. `MARK_NODE`/`RETURN_NODE` update the maps. Frame carries
`{ view:'tree', tree, nodeTags, nodeReturns, cursor }`.

**Layout — the only non-trivial bit.** Use a **classic in-order-position binary layout** (deterministic,
no external dep): x = in-order traversal index * pitch; y = depth * levelHeight. This gives the canonical
"BSTs look sorted left-to-right" property, which is itself pedagogical. ~30 lines, computed once in the
reducer at `TREE_INIT` so the renderer is pure lookup. (Reingold–Tilford is nicer but overkill for the
node counts here, ≤~15 nodes.)

**Renderer sketch:**
```jsx
export default function TreeViz({ frame }) {
  const { tree, nodeTags = {}, nodeReturns = {}, cursor } = frame;
  if (!tree) return null;
  const nodes = [...tree.nodes.values()];
  return (
    <svg viewBox={viewBoxFrom(nodes)} className="w-full">
      {/* edges first (parent -> child lines) */}
      {nodes.flatMap(n => ['left','right'].filter(s=>n[s]!=null).map(s => {
        const c = tree.nodes.get(n[s]);
        return <line key={`${n.id}-${s}`} x1={n.x} y1={n.y} x2={c.x} y2={c.y}
                 stroke="#cbd5e1" strokeWidth={2}/>;
      }))}
      {/* nodes: circle + value; color by tag; ring on cursor */}
      {nodes.map(n => (
        <g key={n.id} transform={`translate(${n.x},${n.y})`}>
          <motion.circle r={18} layout
            fill={FILL[nodeTags[n.id]] || '#fff'}
            stroke={n.id===cursor ? '#7C3AED' : '#94a3b8'}
            strokeWidth={n.id===cursor ? 3 : 1.5}/>
          <text textAnchor="middle" dy="0.35em" className="font-mono text-[13px]">{n.value}</text>
          {nodeReturns[n.id]!=null &&
            <text y={-26} textAnchor="middle" className="fill-[#0F766E] text-[11px]">↑{nodeReturns[n.id]}</text>}
        </g>
      ))}
    </svg>
  );
}
```

Generators to write against it (phase 14): `binary-tree-and-traversals`, `dfs-pre-in-post` (three passes,
`step_id` distinguishes pre/in/post — the code panel + pseudocode already sync), `level-order-bfs` (pair
with the `queue` side-panel — ENQUEUE/DEQUEUE ops already exist!), `bst-insert-and-search`, `validate-a-bst`
(MARK invalid on violation — great predict gate), `lowest-common-ancestor`, `height-and-diameter`
(RETURN_NODE values bubbling up is the whole lesson).

### 3.2 GridViz — 2D matrices / boards  ⭐ second highest

**Unlocks:** Phase 18 DP tables (grid-dp, knapsack, LCS, edit-distance, coin-change table — ~8 lessons),
Phase 12 **N-Queens board**, Phase 3 `2d-arrays-and-matrices` retrofit. ~10 lessons.

**Ops (`grid` / `dp` family — `dp` ops already sketched in events.js):**
```
grid: ['GRID_INIT', 'FILL_CELL', 'READ_CELL', 'MARK_CELL', 'PLACE', 'REMOVE']
```
- `GRID_INIT { rows, cols, values?, labels? }` — dims + optional row/col headers (LCS chars, weights).
- `FILL_CELL { r, c, value }` — DP: write a computed cell (animate it landing).
- `READ_CELL { r, c }` — DP: highlight the dependency cells (i-1,j / i,j-1) being read — teaches the
  recurrence *visually*.
- `MARK_CELL { r, c, tag }` — path reconstruction / attacked squares (`queen | attacked | path | max`).
- `PLACE`/`REMOVE { r, c }` — N-Queens choose/undo (pairs with CHOOSE/UNDO recursion ops for the stack).

**compile state:** `grid: { rows, cols, cells: value[][], labels }`, `cellTags: Map<'r,c', tag>`,
`readCells: Set` (transient per frame — the dependency highlight). Frame: `{ view:'grid', grid, cellTags, readCells }`.

**Renderer:** CSS grid or SVG `<rect>` matrix. Cell color by tag; `readCells` get a dashed outline;
the freshly `FILL_CELL`'d cell animates (framer `layout`/opacity). For N-Queens, `MARK_CELL attacked`
shades the ray squares so pruning is *visible* — this is the aha the 3D board would have destroyed.

For **1D DP** (climbing-stairs, house-robber, coin-change-1d) reuse **ArrayViz** with a second "table"
row, or just render a 1-row grid — don't build a separate renderer.

### 3.3 GraphViz — general graphs

**Unlocks:** Phase 16 Graphs entirely (BFS, DFS, components, cycle detect, topo sort, Dijkstra,
Union-Find, MST — ~9 D-lessons). The `graph` family ops (`VISIT/MARK_VISITED/RELAX/ENQUEUE_NODE`) are
**already stubbed in events.js** — this was anticipated.

**Ops (extend the stub):**
```
graph: ['GRAPH_INIT','VISIT','MARK_VISITED','RELAX','ENQUEUE_NODE','SET_EDGE','UNION']
```
- `GRAPH_INIT { nodes:[{id,value,x?,y?}], edges:[{u,v,w?,directed?}] }` — declare once.
- `VISIT {id}` cursor; `MARK_VISITED {id}`; `ENQUEUE_NODE {id}` (pairs with queue panel for BFS);
  `RELAX {u,v,dist}` (Dijkstra — update a distance label on the node); `SET_EDGE {u,v,tag}` (tree edge /
  cross edge / MST edge coloring); `UNION {a,b}` (Union-Find — recolor the merged component).

**Layout — the hard part.** Two options, pick per-lesson via `GRAPH_INIT`:
1. **Authored coordinates** (`x,y` in the generator) — best for teaching. You *want* the classic
   textbook graph shape for a given lesson, not a random force layout. Recommend this as default: the
   generator author places 6–10 nodes deliberately.
2. **Deterministic circular/grid fallback** when coords omitted (nodes on a circle) — fine for
   Union-Find where topology matters less than component color.

Do **not** ship a live force-directed sim (nondeterministic, breaks scrubbing, jitters). If you want
force layout, run it **once at GRAPH_INIT** with a fixed seed and freeze the coordinates into state —
same discipline as the tree layout.

**Renderer:** SVG. Edges as `<line>` (arrowhead marker if `directed`); weight labels at midpoints;
distance labels above nodes for Dijkstra; node fill by visited/frontier/current; edge stroke by tag
(MST/tree edges highlighted). Distance/frontier readouts go in the existing `StateMachine` pointer panel
(reuse `vars` for "dist" table).

### 3.4 ListViz — linked lists

**Unlocks:** Phase 10 (traversal-and-reversal, find-the-middle, floyd-cycle, merge-two-sorted,
reverse-in-k) — content is authored & the generators exist, but they currently render as **arrays**.
A proper node-arrow chain makes reversal and Floyd's cycle legible. Medium priority — the array
rendering is *serviceable*, so this is an upgrade, not a blocker.

**Ops:** `list: ['LIST_INIT','POINT_NODE','SET_NEXT','MARK_NODE']`. `POINT_NODE {name,id}` for named
pointers (slow/fast/prev/curr — the two-pointer labels already exist in the color scheme); `SET_NEXT
{from,to}` animates a pointer rewiring (the crux of reversal). Frame `{ view:'list', list:{nodes,head},
listPtrs, nodeTags }`.

**Renderer:** horizontal chain of boxes + `→` arrows; a rewired `SET_NEXT` bends the arrow (curved path)
so reversal is a *visible* re-pointing. Floyd's = two labeled cursors (S/F) chasing on the chain, cycle
edge drawn as a back-arc. Layout is trivial (linear), so this is cheap once the box/arrow primitives
exist — and those primitives are shared with GraphViz (reuse the arrowhead marker + node component).

### 3.5 IntervalViz — timelines (small)

**Unlocks:** Phase 17 greedy — `interval-scheduling`, `merge-intervals`. Low effort.

Render intervals as horizontal bars on a shared time axis; sort/select animates; merged intervals fuse.
Ops: `intervals: ['INTERVAL_INIT','SELECT','SKIP','MERGE_INTERVAL']`. This is basically ArrayViz turned
sideways with start/end extents — ~half a day.

### 3.6 BitsViz — binary representation (small)

**Unlocks:** Phase 19 — `single-number-xor`, `counting-bits`. Low effort, high clarity.

Render each number as a row of 0/1 bit-cells; XOR highlights the toggling column across the sequence
(the "pairs cancel" aha). Ops: `bits: ['BITS_INIT','XOR_STEP','SET_BIT']`. ~half a day. Could even be a
specialized mode of GridViz (1 row per number) rather than a new renderer — decide when you get there.

---

## 4. What does NOT need a new renderer

- **Phase 13 Sorting D&C** — `quick-sort` (partition = array + a pivot pointer; add `pivot` to
  `PTR_LABELS`), `counting-sort` (array + a count-bucket row = reuse the frequency-map panel). No new
  renderer. `merge-sort` is the shipped gold exemplar.
- **Phase 8 Two-pointers/windows, Phase 9 Stacks/queues** — already have ArrayViz + StackQueueViz +
  StateMachine. These are content-only now.
- **1D DP** (climbing-stairs, house-robber, coin-change 1D) — ArrayViz with a table row.

## 5. Op-vocabulary summary (add to `events.js`)

```js
export const OP_FAMILIES = {
  array:     ['COMPARE','SWAP','MOVE','WRITE','SPLIT','MERGE_DONE','POINT','SET','WINDOW','MARK','DONE'],
  recursion: ['CALL','RETURN','CHOOSE','UNDO'],                         // backtracking uses CHOOSE/UNDO
  stack:     ['PUSH','POP','ENQUEUE','DEQUEUE'],
  hashing:   ['COUNT'],
  scalar:    ['VAR'],
  tree:      ['TREE_INIT','VISIT_NODE','MARK_NODE','COMPARE_NODE','SET_EDGE','RETURN_NODE'],   // NEW §3.1
  grid:      ['GRID_INIT','FILL_CELL','READ_CELL','MARK_CELL','PLACE','REMOVE'],               // NEW §3.2
  graph:     ['GRAPH_INIT','VISIT','MARK_VISITED','RELAX','ENQUEUE_NODE','SET_EDGE','UNION'],  // NEW §3.3
  list:      ['LIST_INIT','POINT_NODE','SET_NEXT','MARK_NODE'],                                // NEW §3.4
  intervals: ['INTERVAL_INIT','SELECT','SKIP','MERGE_INTERVAL'],                               // NEW §3.5
  bits:      ['BITS_INIT','XOR_STEP','SET_BIT'],                                               // NEW §3.6
};
```
(Note: the existing file has a leaner `array` list because POINT/SET/WINDOW/MARK/DONE were added in the
`arrayReducer` without being registered as "known" — harmless due to graceful fallback, but worth
tidying while you're in there.)

## 6. Testing discipline (keep the moat trustworthy)

Every new generator gets a **golden file** (`*.golden.mjs`) exactly like `merge-sort.golden.mjs` /
`array-family.golden.mjs`: run the generator on a fixed input, snapshot the event array, byte-compare.
Every new compile family: extend `compile-frames.golden.mjs` with one representative trace so the
frame shape is locked. **The generator is the source of truth; the golden test is the proof it's
deterministic.** Renderers are pure and visually reviewed (no snapshot needed, but they must never
throw on a missing key — guard every lookup like the existing ones do).

## 7. Build order (dependency-sequenced, highest leverage first)

1. **Renderer registry + `view` frame key** (§2) — enabler, ~0.5 day. Nothing else ships without it.
2. **TreeViz** (§3.1) — unlocks ~15 lessons across phases 14, 15, 12, 11. Biggest single win.
3. **GridViz** (§3.2) — unlocks phase 18 DP (~8) + N-Queens board + 2D-array retrofit.
4. **GraphViz** (§3.3) — unlocks phase 16 (~9). Hardest layout; do after Tree/Grid warm you up.
5. **ListViz** (§3.4) — upgrades phase 10 from arrays to real chains. Shares primitives with GraphViz.
6. **IntervalViz** (§3.5) + **BitsViz** (§3.6) — small, phases 17 & 19. Batch them last.
7. Backfill: `pivot` pointer for quicksort, count-bucket reuse for counting-sort (no new renderer).

After step 3 you can visualize the entire high-frequency interview core (trees + DP + backtracking).
Steps 4–6 complete the long tail.

## 8. Backtracking (phase 12) note — how N-Queens actually renders

Once §2 + TreeViz + GridViz exist, N-Queens is **two synchronized views**: the `GridViz` board
(PLACE/REMOVE/MARK_CELL attacked) as the main area, and the recursion `StateMachine` call stack
(CHOOSE/UNDO -> CALL/RETURN frames) in the side panel — the learner watches a queen get placed, the
attacked rays light up, a dead-end get pruned, and the stack **pop** on backtrack, all frame-synced.
Subsets/permutations use TreeViz as the main area (the decision tree) with the same stack panel. That
combination — flat board + live stack + decision tree — teaches backtracking better than any 3D scene,
and it's all 2D SVG driven by the one event trace.
```
