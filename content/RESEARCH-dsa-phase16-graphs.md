# DSA deep-research — Phase 16: Graphs (paste into Gemini)

> **How to run:** In Gemini (Deep Research mode recommended), paste the whole of
> `content/PROMPT-dsa-research.md` from the `ROLE` heading through the `OUTPUT FORMAT`
> section FIRST (that's the shared contract + JSON schema + field rules). Then paste
> everything below. It replaces the generic phase-16 line with the same 11 nodes PLUS
> the phase-specific emphasis Claude needs. One phase per chat.
>
> **Two-step (Deep Research):** let it produce the prose report, then in the same chat
> send the "Convert your research above into a JSON array…" extraction prompt from the
> contract. Save the JSON to `content/research/dsa/phase-16.json` (one object per node,
> keyed by slug). Then hand it back to Claude for authoring + the graph renderer.

---

## PHASE 16 — GRAPHS (11 nodes)

Research each node below into one JSON object per the schema. Kind tag per node:
**C** = `kind_hint:"concept"` (renderer `none`), **D** = `kind_hint:"trace"`
(steppable, needs a `graph` renderer).

1. **Graph representations** — C — `graph-representations`
2. **Weighted vs unweighted** — C — `weighted-vs-unweighted`
3. **BFS on graphs** — D — `bfs-on-graphs`
4. **DFS on graphs** — D — `dfs-on-graphs`
5. **When BFS stops working** — C — `when-bfs-stops-working`
6. **Connected components** — D — `connected-components`
7. **Cycle detection** — D — `cycle-detection`
8. **Topological sort** — D — `topological-sort`
9. **Dijkstra's algorithm** — D — `dijkstra-s-algorithm`
10. **Union-Find (Disjoint Set Union)** — D — `union-find`
11. **Minimum spanning tree (Kruskal)** — D — `minimum-spanning-tree-kruskal`

## PHASE-SPECIFIC EMPHASIS (do NOT skip — this is what makes graph research usable)

This is the first phase with a real `graph` renderer and the first with weighted edges.
Be maximally explicit on these, or the lessons can't be built:

- **Directed vs undirected is a per-node fact, not a footnote.** State for EVERY node
  which it assumes. `cycle-detection` in particular has TWO different algorithms —
  undirected (DFS with parent-tracking, or Union-Find) vs directed (DFS with a
  recursion-stack / 3-color WHITE-GRAY-BLACK marking). Research BOTH as separate
  mechanisms in that one node; do not blur them. `topological-sort` is DAG-only (state
  why a cycle makes it impossible).

- **The `visited` set is the graph invariant.** For BFS/DFS/components, the
  `invariants` field must center on "a node is enqueued/marked at most once" and
  `why_violation_breaks` = infinite loops on cycles. `prediction_checkpoints` should
  pause where a student wrongly re-visits a node.

- **`visualization.renderer` = `graph` for all D nodes.** In `key_animation` be concrete
  about what moves: BFS = the frontier expanding ring by ring + the queue contents;
  DFS = the deep path + backtrack + the recursion stack; Dijkstra = the priority-queue
  order + each edge RELAXATION (dist update) + why a finalized node is never revisited;
  Union-Find = the tree/forest merging + path compression flattening; Kruskal = edges
  considered in sorted order, each accepted or rejected by the cycle check.
  `interactive_inputs` = give 2–3 small graphs as adjacency lists (best case, a graph
  with a cycle, a disconnected graph) with a one-line `why` each.

- **`when-bfs-stops-working` is the pivot concept node.** Its whole job: plain BFS gives
  the shortest path ONLY on unweighted graphs; add edge weights and the fewest-edges
  path is no longer the lowest-cost path. Give the crisp 3–4 node counterexample where
  BFS picks the wrong path, and let that MOTIVATE Dijkstra. Treat it like the
  "why greedy fails" contrast nodes. `mental_model` + `interesting_facts` carry this
  one; `repeated_decision`/`invariants` may be "N/A".

- **Cross-phase dependencies — fill `learning_graph.must_know` honestly:**
  - `dijkstra-s-algorithm` MUST list `binary-heap` (priority queue, just finished in
    phase 15) and `weighted-vs-unweighted`. Explain the relaxation invariant (once a
    node is popped with the min distance, that distance is final — and WHY that needs
    non-negative weights).
  - `union-find` MUST tie its near-O(1) amortized cost back to `amortized-analysis`
    (foundations). Cover path compression AND union by rank/size — both, and what each
    buys. Inverse-Ackermann as plain text, framed as "effectively constant".
  - `minimum-spanning-tree-kruskal` depends on BOTH `union-find` (the cycle check) and
    the greedy idea (forward-ref to phase 17 `why-greedy-works`) — note this in
    `related`/`learning_graph`. State the greedy-choice: take the cheapest edge that
    doesn't form a cycle.

- **Misconceptions to actively hunt** (seed `misconceptions` + prediction checkpoints):
  BFS finds shortest path even with weights (false); DFS finds shortest path (false —
  it finds *a* path); you can run Dijkstra with negative weights (false → Bellman-Ford,
  which is out of scope — just name it); adjacency matrix is "better" (false — O(V^2)
  space, wasteful for sparse graphs); a directed cycle and an undirected cycle are
  detected the same way (false).

- **`when_not_to_use` / `failure_signals` matter here:** Dijkstra with negative edges,
  BFS on weighted graphs, adjacency matrix on huge sparse graphs. These contrasts are
  where graph understanding actually lives.

Keep all complexity as plain text (O(V+E), O(E log V), O(V^2)). Cite CLRS / Wikipedia as
primary. Return the JSON array only (plus a short "Sources consulted" list).
