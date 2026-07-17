# Antigravity handoff -- DSA phase 15 (Heaps)

Phase 15 = **3 nodes** (`_TODO-dsa.md` section 15), **all `dsa` execution-trace** (no concept node).
Milestone **M6a-Heaps** in `docs/dsa-viz-implementation-plan.md`. Natural follow-on to phase 14
(Trees) -- a heap reuses the tree renderer.

> **Infra reality check (READ THIS -- differs from phase 14):** phase 14 needed ZERO new viz infra.
> **Phase 15 does need new infra** -- the signature heap visual is **TreeViz + ArrayViz SIDE-BY-SIDE**
> (the array IS the tree -- that's the whole aha) plus a new **`SIFT_SWAP`** op that animates the SAME
> swap in both panels. The Player today renders one main renderer + a StateMachine side panel, not two
> structural renderers stacked. **That build is Claude's pass-2 job (spec below) -- it does NOT block
> this prose packet.** A `dsa` lesson validates clean with no `viz` block; author prose now.

Two passes, same split as phases 12-14:
- **Pass 1 -- PROSE (Antigravity, THIS packet):** author all 3 lessons' text. **NO `viz` block.**
- **Pass 2 -- VIZ (Claude, later):** build the HeapViz composition + `SIFT_SWAP` + 3 generators +
  goldens + viz blocks + browser-verify. Spec is in "Viz pass" below. **Do not do pass 2.**

**Gate for this packet: `python content/validate.py` -- zero errors. Do NOT run the frontend. Do NOT
commit.** Tick boxes in `content/_TODO-dsa.md` as each file lands green.

---

## The 3 nodes (slugs EXACT from `_TODO-dsa.md`, titles/difficulty from `backend/seed_dsa.py`)

| slug | title | kind | tier | difficulty |
|---|---|---|---|---|
| `binary-heap` | Binary heap | dsa | tier1 | medium |
| `heap-sort` | Heap sort | dsa | tier2 | **hard** |
| `top-k-with-a-heap` | Top-K with a heap | dsa | tier1 | medium |

**Build order:** `binary-heap` FIRST and thoroughly -- it defines the array-as-tree model, the heap
property, and sift-up/sift-down that the other two entirely depend on. Then `heap-sort` (build + repeat
extract), then `top-k-with-a-heap` (the size-K trick).

---

## Research source

The phase-15 deep-research file is **in progress**; expected at `~/Downloads/phase15.md` (same
convention as phase-11's `phase11.md` -- prose first, skip any trailing base64 image blocks). **The
concrete per-node material below is inlined so you can author NOW without waiting for it.** When the
research lands, use it to ENRICH intuition + real-world examples, not to add heavy math. If the
research contradicts anything below on a factual point, trust the research and flag it.

---

## Pass 1 -- the 3 `dsa` lessons (PROSE only, NO `viz`)

**DSA branch of `validate.py`.** Copy the shape of `content/roadmaps/dsa/merge-sort.json` (gold `dsa`
exemplar) and **OMIT its `viz` block**; keep every other key.

Required `dsa` fields: `why_it_exists {problem, better_idea}` (naive_solution optional), `mental_model
{intuition, repeated_decision, ...}` -- **`repeated_decision` REQUIRED** (it powers the pass-2 explain
panel + prediction), `explanation` OR `sections` (teaching body WITH a hand-trace), `common_mistakes`
(>=1), `recall_questions` (>=3), `oa_questions` (>=2), `sources` (2-5 URLs). Use too:
`engineering_examples`, `when_not_to_use`, `pattern` ("Heap / Priority Queue"), `key_points`,
`practice` (2-4 LeetCode, LINK ONLY), `related`.

> **Write `mental_model.repeated_decision` as one crisp per-step decision** (given per node) -- it is
> exactly what the pass-2 prediction gates on.

### The FIVE questions (every recall/oa answer derivable from the BODY)
1. Why it exists 2. How to simulate (mental_model + a hand-trace) 3. The invariant 4. A real
engineering use 5. How to recognize it.

### Per-node must-hits

**`binary-heap`** (tier1, medium) -- the foundation; get the array-as-tree model rock solid.
- what: a **complete binary tree** (every level full except possibly the last, filled left-to-right)
  stored in a plain **ARRAY**. Max-heap invariant: **every parent >= both its children** (min-heap:
  parent <= children). Only the ROOT is the extreme; siblings are unordered.
- **the array-as-tree indexing (teach this explicitly, it's the aha):** node at index `i` has children
  at `2i+1` and `2i+2`, parent at `(i-1)//2`. No pointers, no node objects -- the completeness is what
  lets the array encode the tree. This is why heaps are cache-friendly and pointer-free.
- operations, both O(log n) = the tree height:
  - **push:** append at the end of the array, then **sift-UP** (bubble-up) -- while the new node is
    bigger than its parent, swap; stop when it's <= parent or hits the root.
  - **pop-max (extract):** the root is the max; swap root with the LAST element, remove the last,
    then **sift-DOWN** (heapify) the new root -- while it's smaller than its LARGER child, swap with
    that child; stop when it's >= both children or hits a leaf.
  - **peek:** O(1) -- just the root.
  - **build-heap from an arbitrary array: O(n)**, NOT O(n log n) -- sift-down from the last internal
    node `(n//2 - 1)` up to the root. Teach that the tight bound is O(n) (most nodes are near the
    leaves and sift down a tiny distance); state it, don't derive the sum.
- repeated_decision: **"does this element violate the heap property with its parent (going up) or its
  larger child (going down) -- swap, or stop?"**
- invariant: after any sift completes, the sub-heap rooted at the touched node satisfies parent >=
  children everywhere.
- misconceptions (each is a real interview trap): **"a heap is sorted"** (NO -- only the root is
  extreme; an in-order read is meaningless); **"a heap is a BST"** (NO -- there is no left<node<right
  ordering, only the parent-child relation; siblings have NO required order); **"finding an arbitrary
  value is fast"** (NO -- O(n); a heap gives you ONLY the extreme cheaply); mixing up sift-up (push)
  vs sift-down (pop); "pop just removes the root" (you must swap-last-then-sift-down).
- engineering: priority queues -- Dijkstra/Prim/A* frontiers, OS task schedulers, discrete-event
  simulation; Python `heapq` (a min-heap on a list), Java `PriorityQueue`, C++ `priority_queue`.
- practice: LeetCode 703 (Kth largest in a stream), 1046 (Last stone weight), 215.

**`heap-sort`** (tier2, **hard**) -- the O(n log n)-guaranteed, in-place sort.
- what: build a max-heap from the array (O(n)), then repeatedly **swap the root (current max) to the
  end**, shrink the heap by one, and sift-down the new root. When the heap empties, the array is sorted
  ascending, IN PLACE.
- repeated_decision: **"swap the root to the front of the sorted tail, shrink, then sift the new root
  down -- which child does it swap with (the larger one)?"**
- invariant (teach it): after k extractions, the LAST k array slots hold the k largest values in final
  sorted order, and the unsorted prefix is still a valid max-heap.
- complexity + the honest trade (this is the interview signal): **O(n log n) WORST case** -- unlike
  quicksort's O(n^2), heap sort NEVER degrades, and it's **O(1) extra space** (fully in-place). BUT it
  is **NOT stable** and has **poor cache locality** (it jumps around the array by index), which is why
  quicksort usually beats it in practice DESPITE the worse worst case. The build phase is **O(n)**; the
  n extractions are the O(n log n) part.
- misconceptions: "heap sort is stable" (NO); "always faster than quicksort" (NO -- worse constants +
  cache behavior); "building the heap costs O(n log n)" (the build is O(n)); confusing sort DIRECTION
  (a max-heap sorts ASCENDING because maxes go to the end).
- engineering: **introsort** (`std::sort`) uses heap sort as the guaranteed-O(n log n) FALLBACK when
  quicksort's recursion gets too deep -- the anti-adversary safety net; memory-constrained/embedded
  sorts where in-place matters. Cross-link `quick-sort` (its worst-case foil) + `merge-sort` (stable,
  but O(n) space).
- practice: LeetCode 912 (Sort an Array).

**`top-k-with-a-heap`** (tier1, medium) -- the counterintuitive size-K trick.
- what: to find the **K LARGEST**, keep a **size-K MIN-heap**: push each element; whenever the heap
  exceeds K, pop the MIN. After one pass, the heap holds exactly the top K, and its root is the Kth
  largest. (Mirror: K SMALLEST -> size-K MAX-heap.)
- **the counterintuitive spine (make this the core of the lesson):** for the K LARGEST you use a
  MIN-heap, because the cheap operation you need is "evict the SMALLEST of my current top-K" -- and a
  min-heap's root IS that smallest. The heap's root doubles as the **eviction threshold**.
- repeated_decision: **"is this element bigger than the heap's root (the smallest of my current
  top-K)? If yes, pop the root and push it; if no, skip it."**
- invariant: at all times the heap holds the K largest elements seen so far; its root is the current
  Kth largest.
- complexity + when to reach for it: **O(n log K)** time, **O(K)** space. Beats a full sort
  (O(n log n)) when **K << n**, and -- crucially -- works on a **STREAM** where you can't hold or
  random-access all n. Name the alternative honestly: **quickselect is O(n) average for a STATIC
  array** (faster than the heap there), but the heap wins for streams / online data. This "heap vs
  sort vs quickselect" call is the interview payoff.
- misconceptions: **"use a MAX-heap for the K largest"** (NO -- a size-K MIN-heap; this is THE trap);
  "sort then take K is just as good" (only if you can hold + sort all n; fails on streams, wasteful
  when K<<n); forgetting to CAP the heap at K (you lose the O(K) space win and the O(log K) factor).
- engineering: "top N trending"/leaderboards over a stream, K-nearest-neighbors, top-K error types in
  log analysis, DB `ORDER BY x LIMIT k`.
- practice: LeetCode 215 (Kth largest), 347 (Top K frequent), 973 (K closest points), 703.

### Cross-links
`binary-heap` prereq `binary-tree-and-traversals` (phase 14) + `arrays-and-memory` (the array backing)
+ `logarithms-and-powers-of-two` (why O(log n)); it unlocks both `heap-sort` and `top-k-with-a-heap`.
`heap-sort` `related` -> `quick-sort`, `merge-sort` (the sort trio). `top-k-with-a-heap` `related` ->
`bst-insert-and-search` and (forward) quickselect.

## ASCII-only in JSON
`->` not an arrow glyph, `--` not an em-dash, straight quotes, `>=`/`<=` not the glyphs, `2i+1` plain.

## Process (pass 1)
1. Read `merge-sort.json` (shape, MINUS its viz) + `content/PROMPT-dsa.md` (QUALITY BAR items 6-7:
   every answer derivable from the body; no unexplained jargon; mechanism-based mental_model) + the
   inlined research above (or `~/Downloads/phase15.md` once it lands).
2. Write the 3 files -- NO `viz` block; each MUST have `mental_model.repeated_decision`.
3. `python content/validate.py` -> zero errors. Tick `content/_TODO-dsa.md`.
4. Standing pipeline: **Sonnet / Gemini-in-Antigravity lesson critic** (separate session,
   `content/RUN-lesson-critic-antigravity.md`) -> apply fixes -> re-critic. DONE only when a cold
   beginner can answer every recall/oa question from the body AND the expert finds zero errors.

---

## Viz pass (Claude, pass 2 -- SPEC ONLY, do NOT build now)

Unlike phase 14, this pass has a REAL infra step, not just generators. **Antigravity does none of it.**

### What already exists (verified against code, 2026-07-12)
- **`TreeViz.jsx`** renders `frame.tree` (binary nodes with `value`, `left/right`, `x/y`), tags nodes,
  rings `cursor`, prints `nodeReturns` above a node.
- **`treeReducer`** folds `TREE_INIT {nodes, root}` (complete-tree layout works -- it lays out any
  binary tree), `VISIT_NODE`, `MARK_NODE {id, tag}`, `RETURN_NODE`.
- **Every frame ALREADY carries BOTH `array` AND `tree` simultaneously** (`compile.js` emits
  `array:[...state.array]` on every frame and `tree` when present) -- so a single heap frame can hold
  the tree and its backing array at once. The data model is ready; the RENDERING of both together is
  not.
- `ArrayViz.jsx` renders `frame.array` as bars. `predict.js` has `next_swap_pair`, `branch_binary`,
  `next_op`.

### What is genuinely NEW (the pass-2 build)
1. **`SIFT_SWAP {i, j}` op** (add to `events.js` -- a new `heap` family or extend `tree`; additive per
   §9.1, no version bump). Reducer folds it to swap the values at heap positions i and j in **BOTH**
   `state.array[i]<->[j]` AND the two tree nodes' `value` fields, so the identical swap lights up in
   both panels. Also emit `MARK_NODE`/a `sorted` marker for heap-sort's finalized tail.
2. **HeapViz composition -- TreeViz ABOVE ArrayViz, index-aligned.** The Player currently renders one
   `rendererFor(frame)` + `StateMachine`. Add a `view: 'heap'` (or a `frame.dual` flag) that stacks
   TreeViz over ArrayViz sharing one frame, with a faint connector showing "array[i] == the node at
   tree position i." This side-by-side IS the lesson -- build it as its own small renderer
   (`HeapViz.jsx`) that composes the two, keeping each underlying renderer a pure `frame -> UI`
   (§6.1). Do NOT fork TreeViz/ArrayViz.
3. **The tree is derived from the array** (complete-tree indexing i -> 2i+1/2i+2): the generator emits
   one `TREE_INIT` built from the initial array, then only `SIFT_SWAP`/`VISIT_NODE`/`MARK_NODE` -- the
   swaps keep tree values and array in lockstep. (Or rebuild tree values each sift; pick the cleaner
   reducer path at build time -- keep goldens byte-stable per §9.3.)
4. **Derive:** `next_swap_pair` likely reuses for the "which two swap next" prediction if `SIFT_SWAP`
   carries `{i,j}`; if the gate is "swap or stop," reuse `branch_binary`. Add a `sift_target` derive
   only if neither fits -- prefer reuse.

### Per-node viz plan (generator + default_input + prediction)
| slug | trace | default_input | prediction (`derive`) |
|---|---|---|---|
| `binary-heap` | build/heap from array, then demo one `push` (sift-up) + one `pop-max` (sift-down); SIFT_SWAP lights tree+array together | array `[50,30,40,10,20,35]`, then push `45`, then pop | "which child does it swap with / swap-or-stop" (`next_swap_pair` / `branch_binary`) |
| `heap-sort` | build-heap, then extract-loop: swap root to tail, MARK tail sorted, sift-down | `[4,10,3,5,1]` | which child the sifting root swaps with next (`next_swap_pair`) |
| `top-k-with-a-heap` | size-K MIN-heap panel; per element gate evict-vs-skip; root = Kth largest | array `[3,2,1,5,6,4]`, `k=2` | "bigger than the root -> evict?" (`branch_binary`) |

### Pass-2 process (Claude)
1. Build the `SIFT_SWAP` reducer + `HeapViz` composition; frame-snapshot goldens prove no drift on
   existing tree/array frames (§9.3, additive-only §9.5).
2. Build 3 generators (pure `(input)->{input,events}`, TREE_INIT-first), one `*.golden.mjs` each with
   an edge input (single element / already-a-heap / all-equal). Register in `registry.js`. `npm run
   golden` green.
3. Add the `viz` block to each of the 3 lessons. `python content/validate.py` green (checks
   `viz.generator` registered + `derive` names exist). `node frontend/scripts/sync-content.mjs`.
4. **Browser-verify each renders** at `/roadmaps/dsa/learn/<slug>` -- goldens do NOT catch JSX render
   crashes. Do NOT commit; hand back the exact changed-file list (events.js, compile.js, HeapViz.jsx,
   Player wiring, registry keys, generators, goldens, and which lessons got viz).

> After phase 15, Trees + Heaps (M6a) is complete. Next milestone is **M6b Graphs** (GraphViz already
> exists as a stub -- separate, larger packet).
