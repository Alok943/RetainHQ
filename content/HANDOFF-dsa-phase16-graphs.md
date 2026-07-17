# Antigravity handoff — DSA phase 16 (Graphs)

Phase 16 = **11 nodes** (`_TODO-dsa.md` section 16) — the largest phase in the roadmap and the
biggest structural jump in it: the first phase with **weighted edges**, the first with a
**directed/undirected split that changes the algorithm**, and the first to feed the **`GraphViz`
renderer** (built long ago, never fed by a single generator).

> **Infra reality check — READ THIS FIRST. It is not like phase 14/15.**
> The graph pipeline exists end-to-end on paper: the `graph` op family is declared in `events.js`,
> `graphReducer` exists in `compile.js`, `GraphViz.jsx` exists, and `renderers/index.js` maps
> `view:'graph' → GraphViz`. **But the pipeline is broken — it has never rendered a real trace, and
> the frame contract does not line up.** Five concrete defects are catalogued in **Pass 0** below.
> Building generators against it today would produce traces where every node is white, no edge ever
> highlights, and any `SET_EDGE` silently flips the frame to the TREE renderer.
> **Pass 0 (Claude) must land before Pass 2 (generators) starts.** Pass 1 (prose) is unblocked and
> can run in parallel.

Three passes:
- **Pass 0 — CONTRACT FIX (Claude, BLOCKING for pass 2):** repair the graph frame contract +
  add graph derives. Spec below. **Antigravity: do not do pass 0.**
- **Pass 1 — PROSE (Antigravity):** author all 11 lessons' text. **NO `viz` block.** Blocked only on
  the phase-16 research (see Research source).
- **Pass 2 — VIZ (Antigravity from the Claude spec, per D-015):** 8 generators + goldens. **Claude
  browser-verifies before anything is "done"** — goldens cannot catch a JSX render crash.

**Gate for pass 1: `python content/validate.py` — zero errors. Do NOT run the frontend. Do NOT
commit.** Tick boxes in `content/_TODO-dsa.md` as each file lands green.

---

## The 11 nodes (slugs EXACT from `_TODO-dsa.md`; titles/difficulty from `backend/seed_dsa.py`)

| slug | title | kind | difficulty | generator (pass 2) |
|---|---|---|---|---|
| `graph-representations` | Graph representations | **C** concept | easy | — (`runtime:"none"`) |
| `weighted-vs-unweighted` | Weighted vs unweighted | **C** concept | medium | — (`runtime:"none"`) |
| `bfs-on-graphs` | BFS on graphs | **D** dsa | medium | `bfs-on-graphs` |
| `dfs-on-graphs` | DFS on graphs | **D** dsa | medium | `dfs-on-graphs` |
| `when-bfs-stops-working` | When BFS stops working | **C** concept | medium | — (`runtime:"none"`) |
| `connected-components` | Connected components | **D** dsa | medium | `connected-components` |
| `cycle-detection` | Cycle detection | **D** dsa | medium | `cycle-detection` |
| `topological-sort` | Topological sort | **D** dsa | hard | `topological-sort` |
| `dijkstra-s-algorithm` | Dijkstra's algorithm | **D** dsa | hard | `dijkstra` |
| `union-find` | Union-Find | **D** dsa | hard | `union-find` |
| `minimum-spanning-tree-kruskal` | Minimum spanning tree (Kruskal) | **D** dsa | hard | `kruskal` |

**3 concept + 8 trace.** Build order = table order; it is a dependency chain. `graph-representations`
FIRST and thoroughly — the adjacency-list model every later node assumes. Then the two traversals,
then the pivot concept (`when-bfs-stops-working`) which motivates Dijkstra. `union-find` MUST land
before `minimum-spanning-tree-kruskal` (Kruskal's cycle check *is* DSU).

---

## Research source

The phase-16 research has **not been run yet**. The paste-ready prompt is
`content/RESEARCH-dsa-phase16-graphs.md` (Gemini Deep Research; prepend the shared contract from
`PROMPT-dsa-research.md`). Output goes to `content/research/dsa/phase-16.json`, one object per node
keyed by slug.

**Do not author pass 1 before that JSON exists** — unlike phase 15, the per-node material here is
not inlined (11 nodes × the full five-questions payload is exactly what the research pass is for).
The per-node must-hits below are the *correctness spine* — the non-negotiable facts the research must
confirm and the lesson must teach. If the research contradicts a factual point below, trust the
research and flag it.

---

## Pass 1 — the 11 lessons (PROSE only, NO `viz`)

Follow `content/PROMPT-dsa.md` (the ⛔ no-viz boundary and the FIVE questions are never overridden).
Copy the shape of `content/roadmaps/dsa/merge-sort.json` (gold `dsa` exemplar) and **OMIT its `viz`
block**; keep every other key. Concept nodes copy `content/roadmaps/dsa/what-is-an-algorithm.json`
and set **`runtime: "none"`**.

**`dsa` branch required fields:** `why_it_exists {problem, better_idea}`, `mental_model {intuition,
repeated_decision, ...}` — **`repeated_decision` REQUIRED** (it powers the pass-2 explain panel +
prediction gate), `explanation` OR `sections` (teaching body **with a hand-trace on a ≤6-node
graph**), `common_mistakes` (≥1), `recall_questions` (≥3), `oa_questions` (≥2), `sources` (2–5 URLs).

**`concept` branch required fields:** `overview {what, why}`, `why_learning_this`, `common_mistakes`,
`recall_questions`, `practice_tasks`, `understanding_checks` (**≥2**), `sources`.

### Phase-wide rules (these are what make graph lessons correct)

1. **State directed-vs-undirected in EVERY node.** Never leave it implied. It changes the algorithm
   outright in `cycle-detection` and is the precondition for `topological-sort`.
2. **The `visited` set is the phase invariant.** For every traversal node, `mental_model.invariant` /
   `invariants[]` centres on *"each node is marked at most once"*, and the violation consequence is
   *"an infinite loop on any cycle"*. This is the single idea phase 16 exists to install.
3. **Hand-traces use a ≤6-node graph given as an adjacency list**, with real small labels (0–5 or
   A–F). The reader must be able to run it on paper — the visualization does not exist yet.
4. **Complexity as plain text** — `O(V+E)`, `O(E log V)`, `O(V^2)`. Never LaTeX.
5. **`repeated_decision` is one crisp per-step decision** (given per node below).

### Per-node must-hits (the correctness spine)

**`graph-representations`** (C, easy) — the model everything else assumes.
- Adjacency **list** vs adjacency **matrix**: list = `O(V+E)` space, neighbour scan `O(deg(v))`,
  edge-lookup `O(deg(v))`; matrix = `O(V^2)` space, edge-lookup `O(1)`.
- **Why the list is the default:** real graphs are *sparse* (`E << V^2`); a matrix burns `O(V^2)` to
  store mostly zeros. Matrix wins only on dense graphs or `O(1)` edge-existence queries.
- Directed vs undirected: an undirected edge is stored **twice** (u→v and v→u). Self-loops,
  multi-edges — name them, don't dwell.
- `understanding_checks`: must catch *"adjacency matrix is just better"*.

**`weighted-vs-unweighted`** (C, medium) — sets up the whole Shortest-Path arc.
- A weight = a real cost (distance, time, price). **Unweighted = every edge costs 1**, so
  fewest-edges *is* cheapest.
- The moment weights exist, **fewest-edges ≠ lowest-cost** — the seed of `when-bfs-stops-working`.
- Do NOT teach Dijkstra here. Motivate and hand off.

**`bfs-on-graphs`** (D, medium) — `repeated_decision`: *"which node comes off the front of the queue
next, and which of its unvisited neighbours get enqueued?"*
- **Queue** + `visited` set. Explores in **layers** (rings of equal edge-distance from the source).
- **Mark visited at ENQUEUE time, not at dequeue time** — the classic bug. Dequeue-time marking lets
  a node be enqueued many times before it's ever processed.
- **The guarantee (state it precisely):** BFS finds the shortest path **in number of edges**, and
  **only on unweighted graphs**. Forward-pointer → `when-bfs-stops-working`.
- Complexity `O(V+E)`, space `O(V)`.

**`dfs-on-graphs`** (D, medium) — `repeated_decision`: *"go deeper into the first unvisited neighbour,
or backtrack?"*
- Recursion (or an explicit stack) + `visited`. Goes **deep before wide**.
- **DFS finds *a* path, NOT the shortest one** — the #1 misconception here; make the lesson prove it
  on the hand-trace.
- Recursion depth = `O(V)` → stack overflow risk on large/deep graphs; mention the iterative form.
- Complexity `O(V+E)`.

**`when-bfs-stops-working`** (C, medium) — **the pivot node of the phase. It exists to break a belief.**
- Give the **crisp counterexample**: a graph where the fewest-edges path is *more expensive* than a
  longer-in-edges path (e.g. `A→B` weight 10 direct, vs `A→C→B` weights 1+1). BFS returns the 1-edge
  path; the true cheapest is the 2-edge path.
- Name the rule: **BFS's shortest-path guarantee is a special case that only holds when every edge
  costs the same.**
- Then motivate Dijkstra in one line: *process nodes in order of cheapest-known-cost, not fewest-edges*
  — which needs a priority queue, i.e. the heap from phase 15.
- `repeated_decision`/`invariants` may be `"N/A"`. `mental_model` + `understanding_checks` carry it.

**`connected-components`** (D, medium) — `repeated_decision`: *"is there any unvisited node left to
start a fresh search from?"*
- Loop over all nodes; every time you meet an **unvisited** one, run one BFS/DFS from it — that whole
  search reaches exactly one component. Count the starts.
- The outer loop is the whole idea; the inner search is phase-16 traversal reused.
- Real framing: "count the islands / groups". `O(V+E)` total — the `visited` set means each node is
  touched once *across all* searches, not once per search.

**`cycle-detection`** (D, medium) — **TWO different algorithms in one node. Do not blur them.**
- `repeated_decision`: *"does this edge lead somewhere already on my current path?"*
- **Undirected:** DFS while tracking each node's **parent**. A visited neighbour that is **not the
  parent** ⇒ cycle. (Without the parent check, the edge you just came in on looks like a cycle.)
  Union-Find is the alternative — forward-pointer to `union-find`.
- **Directed:** a visited neighbour is NOT enough — you need one currently on the **recursion stack**
  (the classic WHITE/GRAY/BLACK marking). A **back edge to a GRAY node** ⇒ cycle. A visited BLACK
  node is just a re-reached finished node, not a cycle.
- The misconception to kill: *"a directed cycle and an undirected cycle are found the same way."*

**`topological-sort`** (D, hard) — `repeated_decision`: *"which node currently has in-degree zero?"*
- **DAG only.** State why: a cycle means each of its nodes depends on the other ⇒ no linear order can
  exist. A topological sort **fails iff the graph has a cycle** — that's also how you detect one.
- **Kahn's (BFS/in-degree)** is the one to teach as the trace: compute in-degrees, enqueue all zeros,
  pop → append to order → decrement neighbours' in-degrees → enqueue any that hit zero. If the output
  is shorter than `V`, a cycle exists.
- Mention the DFS-based variant (push on return, reverse the finish order) in one line — don't
  co-teach it.
- Real framing: build systems, course prerequisites, package managers. `O(V+E)`.

**`dijkstra-s-algorithm`** (D, hard) — `repeated_decision`: *"which unfinalized node has the smallest
known distance?"* (that is exactly the priority-queue pop).
- `learning_graph.must_know` MUST include `binary-heap` (phase 15) and `weighted-vs-unweighted`.
- **Relaxation:** for edge `u→v` with weight `w`, if `dist[u] + w < dist[v]` then `dist[v] = dist[u]+w`.
- **The invariant (the heart):** when a node is popped from the priority queue, its distance is
  **final** — and `why_violation_breaks` = this depends on **non-negative weights**. With a negative
  edge, a later-discovered cheaper path could undercut an already-finalized node.
- **Negative weights ⇒ Dijkstra is wrong.** Name Bellman-Ford as the fix and stop (out of scope).
- Complexity `O(E log V)` with a binary heap. Contrast: BFS is Dijkstra where all weights are 1.

**`union-find`** (D, hard) — `repeated_decision`: *"are these two nodes already in the same set — i.e.
do they share a root?"*
- Disjoint-Set Union: a **forest of parent pointers**; each set is a tree; the **root is the set's id**.
  `find(x)` walks to the root; `union(a,b)` links one root under the other.
- **Both optimizations, and what each buys:**
  - **Union by rank/size** — always hang the *smaller/shallower* tree under the larger. Stops the
    forest degenerating into a linked list (which makes `find` `O(n)`).
  - **Path compression** — during `find`, re-point every node on the path straight at the root,
    flattening it for next time.
- Together: **effectively constant** amortized (inverse-Ackermann — describe it as
  "effectively constant", plain text, no math theatre). `learning_graph.must_know` includes
  `amortized-analysis` (Foundations) — that node is *why* this claim is legitimate.
- Real framing: Kruskal's cycle check, network connectivity, account merging.

**`minimum-spanning-tree-kruskal`** (D, hard) — `repeated_decision`: *"is the next-cheapest edge safe
to take, i.e. does it connect two different components?"*
- MST = cheapest set of edges connecting **all** nodes with **no cycle** (`V-1` edges).
- Kruskal: **sort all edges by weight**, then take each in order **iff** its endpoints are in
  different sets (`find(u) != find(v)`), and `union` them. Skip it otherwise (it would close a cycle).
- **The greedy choice** — forward-pointer to phase 17 `why-greedy-works`; note in `related`. Kruskal
  is the phase's bridge into Greedy.
- Depends on `union-find`. Complexity `O(E log E)` (the sort dominates).
- Mention Prim's in one line as the alternative; do not co-teach.

---

## Pass 0 — CONTRACT FIX (Claude only, blocks pass 2)

Verified against the current tree on 2026-07-12. The `graph` op family
(`GRAPH_INIT, VISIT, MARK_VISITED, RELAX, ENQUEUE_NODE, SET_EDGE, UNION`) is declared and
`renderers/index.js` maps `graph → GraphViz` correctly. These five defects sit between them:

**P0-1 — frame-key mismatch: node tags + cursor never render.**
`compile.js` emits `frame.graphNodeTags` / `graphEdgeTags` / `graphCursor`; `GraphViz.jsx` destructures
`frame.nodeTags` and reads `frame.cursor`. Result: `nodeTags` always defaults to `{}` ⇒ `FILL[tag]` is
always undefined ⇒ **every node renders white**, and the cursor ring never appears.
*Fix in `GraphViz.jsx`, not `compile.js`* — `compile-frames.golden.mjs` is a byte-identical guard on
the frame shape, and `nodeTags`/`cursor` are already the TREE family's keys.

**P0-2 — edge tags never reach the edges.**
`GraphViz` highlights on `e.tag === 'tree' | 'MST' | 'path'`, but `compile` stores tags in a separate
map `graphEdgeTags["u,v"]` and never merges them onto the edge objects ⇒ **no MST / path / tree edge
ever highlights**. Fix: `GraphViz` looks up `graphEdgeTags[`${e.u},${e.v}`]`, falling back to
`` `${e.v},${e.u}` `` for undirected edges.

**P0-3 — `SET_EDGE` reducer collision (the blocker).**
`SET_EDGE` is declared in **both** the `tree` and `graph` families (`events.js`), and `treeReducer`
runs **before** `graphReducer` in `REDUCERS`. `treeReducer`'s `case 'SET_EDGE'` returns
`{view:'tree'}` **unconditionally, without checking `state.tree`** ⇒ any graph trace emitting
`SET_EDGE` flips the frame to the tree renderer and `graphReducer` never sees it. This kills
Kruskal (MST edges), topological sort, and Dijkstra's path edges.
Fix: guard the top of `treeReducer` — `if (!state.tree && op !== 'TREE_INIT') return null;`. Safe:
its `default` already does exactly this, and `CALL`/`RETURN` are claimed earlier by
`recursionMergeReducer`. Same latent collision exists for `MARK_NODE` (tree vs list) — the same guard
fixes it. Re-run `npm run golden` after: the backtracking goldens are the regression net.

**P0-4 — `ENQUEUE_NODE` tag is not in the renderer's vocabulary.**
`compile` sets `graphNodeTags[id] = 'enqueued'`; `GraphViz`'s `FILL` map has no `enqueued` key (its
frontier colour is `frontier`) ⇒ enqueued nodes render white. Fix: emit `args.tag ?? 'frontier'`.
The BFS frontier is the single most important visual in this phase — it must not be white.

**P0-5 — `RELAX` convention is unresolved.**
`graphReducer` does `state.graph.nodes.find(n => n.id === args.u)` with a literal comment
*"// or v, depending on convention"*. Relaxation updates the **neighbour**'s distance.
**Pin it:** `RELAX { u, v, dist }` sets node **`v`**'s `dist` to `dist` (`dist[u] + w`). Fix the
reducer and write the convention into the generator spec. (`node.dist` already flows to the renderer
and prints above the node — Dijkstra's distance labels work once this is right.)

**P0-6 — no graph derives for prediction checkpoints.**
`predict.js`'s `DERIVES` has nothing graph-shaped, and `validate.py` rejects any `viz.predictions[].derive`
not registered there. Add at minimum:
- `next_visited` — the id of the next `MARK_VISITED`/`VISIT` node (gates "which node does BFS reach next?").
- `next_dequeued` — the next node popped (BFS/Kahn/Dijkstra order — the highest-value gate in the phase).
- `is_relaxed` — whether the next `RELAX` actually lowers `dist` (`choice: relaxed | unchanged`).
- `edge_accepted` — whether Kruskal's next edge is taken or skipped (`choice: taken | cycle`).

Also decide **`UNION`** (currently a no-op stub returning `{view:'graph'}`): model the DSU forest as
graph edges — `UNION {child, root}` adds a directed parent edge tagged `tree` — so `GraphViz` shows
the forest merging and path compression re-pointing. If that reads badly in the browser pass, the
fallback is a dedicated DSU panel (new work — flag it, don't improvise).

---

## Pass 2 — the 8 generators (Antigravity, from this spec, per D-015)

**Do not start until Pass 0 has landed.** One file per algorithm in
`frontend/src/dsa/generators/<key>.js`, exporting a named `*Events(input)` function, registered in
`frontend/src/dsa/registry.js` (`validate.py` checks a lesson's `viz.generator` key exists there).
Pattern to copy: `frontend/src/dsa/generators/combination-sum.js` + `combination-sum.golden.mjs`.

**Hard rules (same as every prior phase):**
- The generator is a **pure, deterministic** function of `input` — no `Math.random`, no `Date.now`.
- Events are the source of truth; **never author frames**. `{ op, args, step_id, note }`, `step_id`
  monotonic from 1, `note` = the human caption.
- Emit `GRAPH_INIT { nodes, edges }` first. `nodes`: `[{id, value?, x?, y?}]` — **omit x/y** and the
  compiler lays out a circle (fine for ≤8 nodes). `edges`: `[{u, v, w?, directed?}]`.
- Default inputs are **small and hand-traceable (5–7 nodes)** and must match the lesson's hand-trace.
- Use the pinned `RELAX {u, v, dist}` convention from P0-5.
- Mark visited at **enqueue** time in BFS (mirrors the lesson's stated rule — the trace must not
  teach the bug the prose warns about).

| generator key | algorithm | ops used | the moment the viz must sell |
|---|---|---|---|
| `bfs-on-graphs` | BFS, unweighted | `GRAPH_INIT`, `ENQUEUE_NODE`, `VISIT`, `MARK_VISITED`, `ENQUEUE`/`DEQUEUE` | the frontier expanding ring-by-ring + the queue panel draining |
| `dfs-on-graphs` | DFS, recursive | `GRAPH_INIT`, `VISIT`, `MARK_VISITED`, `CALL`/`RETURN` | going deep, then **backtracking** (the call stack panel) |
| `connected-components` | repeated traversal | above + `MARK_VISITED {tag}` | each restart painting a *new* component; the outer loop skipping visited |
| `cycle-detection` | directed (3-colour) | `GRAPH_INIT`, `VISIT`, `MARK_VISITED {tag:'frontier'\|'visited'}`, `SET_EDGE {tag:'path'}` | the **back edge** hitting a node still on the stack |
| `topological-sort` | Kahn's | `GRAPH_INIT`, `ENQUEUE_NODE`, `DEQUEUE`, `MARK_VISITED`, `VAR {order}` | in-degrees ticking to zero → node unlocks and joins the order |
| `dijkstra` | binary-heap PQ | `GRAPH_INIT`, `ENQUEUE_NODE`, `RELAX`, `MARK_VISITED`, `SET_EDGE {tag:'path'}` | `dist` labels dropping on **relaxation**; a popped node never revisited |
| `union-find` | DSU + compression | `GRAPH_INIT`, `VISIT`, `UNION`, `SET_EDGE {tag:'tree'}` | `find` walking to the root, then **path compression flattening it** |
| `kruskal` | sort + DSU | `GRAPH_INIT`, `SET_EDGE {tag:'MST'}`, `UNION`, `MARK_VISITED {tag:'invalid'}` | each edge in sorted order **accepted or rejected** by the cycle check |

**Goldens (one `<key>.golden.mjs` per generator, `npm run golden` green):** assert (1) determinism —
generating twice is byte-identical; (2) one frame per event via `compile(input, events)`; (3) every
frame has an `activeOp`; (4) the **phase-16 invariant: no node is MARK_VISITED twice**; (5) per
algorithm — BFS/Kahn emit a correct order; Dijkstra's final `dist` matches a hand-computed answer;
Kruskal accepts exactly `V-1` edges and its total weight matches the known MST; `CALL`/`RETURN`
balance for DFS. Print an op-count fingerprint like the existing goldens.

**Then STOP and report.** Claude runs the browser pass (each lesson renders; frontier/visited colours
actually appear; MST/path edges highlight; `dist` labels update; predict gates fire; no console
errors) — goldens cannot catch a JSX crash (D-015).

---

## Boundaries

- Pass 1: touch only `content/roadmaps/dsa/*.json` + `content/_TODO-dsa.md`. **No `viz` block, no
  `animation`, no `image`** (`PROMPT-dsa.md` ⛔ boundary).
- Pass 2: touch only `frontend/src/dsa/generators/*` + `registry.js`. **Do not edit `compile.js`,
  `events.js`, `predict.js`, or any renderer** — that is Pass 0, Claude-owned shared contract.
- No commits, no pushes, no DB/seed changes. `seed_dsa.py` already defines all 11 nodes.
- If the spec fights reality, implement the closest faithful version and **FLAG it** in
  `content/REPORT-dsa-phase16.md` — do not silently redesign.
