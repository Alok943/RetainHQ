# Antigravity handoff -- DSA phase 14 (Trees)

Phase 14 = **8 nodes** (`_TODO-dsa.md` section 14). One is a `concept` node, seven are `dsa`
execution-trace nodes. This is milestone **M6a-Trees** in `docs/dsa-viz-implementation-plan.md`.

> **The good news up front:** the tree visualization infra is ALREADY BUILT (M5 shipped `TreeViz` +
> the `treeReducer` for backtracking). All seven trace nodes render on the EXISTING renderer with the
> EXISTING op vocabulary -- **no new renderer, no new op family required.** See "Viz pass" below for
> the tiny reducer polish that is genuinely new. This is why the phase is unblocked.

Two passes, same split as phases 12-13:
- **Pass 1 -- PROSE (Antigravity, THIS packet):** author all 8 lessons' text. **`dsa` nodes get NO
  `viz` block** (a `dsa` lesson validates clean without one). The `concept` node never gets viz.
- **Pass 2 -- VIZ (Claude, later):** build 7 generators + goldens, add each `viz` block, browser-verify
  render. Spec is in "Viz pass (Claude, pass 2)" below so nothing is lost -- but **do not do pass 2.**

**Gate for this packet: `python content/validate.py` -- zero errors. Do NOT run the frontend. Do NOT
commit.** Tick boxes in `content/_TODO-dsa.md` as each file lands green.

---

## The 8 nodes (slugs EXACT from `_TODO-dsa.md`, titles from `backend/seed_dsa.py`)

| slug | title | kind | tier | difficulty | pass-2 viz? |
|---|---|---|---|---|---|
| `recursive-tree-thinking` | Recursive tree thinking | **concept** | tier1 | medium | no (concept) |
| `binary-tree-and-traversals` | Binary tree & traversals | dsa | tier1 | easy | yes |
| `dfs-pre-in-post` | DFS: pre / in / post | dsa | tier1 | medium | yes |
| `level-order-bfs` | Level-order (BFS) | dsa | tier1 | medium | yes |
| `bst-insert-and-search` | BST: insert & search | dsa | tier1 | medium | yes |
| `validate-a-bst` | Validate a BST | dsa | tier2 | medium | yes |
| `lowest-common-ancestor` | Lowest common ancestor | dsa | tier2 | medium | yes |
| `height-and-diameter` | Height & diameter | dsa | tier2 | medium | yes |

**Build order:** `recursive-tree-thinking` first (it's the mental spine every other node leans on),
then top-to-bottom. `binary-tree-and-traversals` before the three traversal-detail nodes; `bst-insert-
and-search` before `validate-a-bst`.

---

## Pass 1a -- the CONCEPT node (`recursive-tree-thinking`)

**CONCEPT branch of `validate.py`** -- `kind: "concept"`, `runtime: "none"`, **NO `viz`, NO
`why_it_exists`, NO `mental_model`, NO `oa_questions`.** Use the exact shape/fields of the phase-11
recursion concept lessons.

- **Exemplars (copy the shape):** `content/roadmaps/dsa/base-case.json`,
  `recursion-tree.json`, `the-call-stack.json`.
- **Required fields:** `overview {what, why}`, `why_learning_this[]`, `common_mistakes[{title,
  explanation}]` (>=1), `recall_questions[{q,answer,tier}]` (>=3), `understanding_checks` (>=2, typed:
  `predict-output|explain-behavior|find-bug|...`), `practice_tasks[]`, `sources[]` (2-5 real URLs).
  Optional and encouraged here: `aha_moment {code, prediction, common_guess, why}` (code is
  ILLUSTRATIVE only -- runtime is none, never executed), `glossary`, `challenge`.
- **The one idea to install:** a tree IS "a node plus two (smaller) subtrees" -- the same
  self-similar shape recursion was built for. Almost every tree algorithm is: do something with the
  node, recurse left, recurse right, combine. **Misconception to kill:** "I need to manage the whole
  tree at once / track which node I'm on with a loop." No -- you reason about ONE node assuming the
  recursive calls correctly handle the subtrees (the phase-11 "leap of faith"), and the call stack
  tracks position for you. Prereq `recursion-tree` + `the-call-stack`; unlocks the seven trace nodes.
- Good `understanding_checks`: predict the return of a 4-line recursive `countNodes(node)`;
  find-the-bug on a traversal missing its null base case (infinite recursion / crash).

---

## Pass 1b -- the SEVEN `dsa` trace nodes (PROSE only, NO `viz`)

**DSA branch of `validate.py`.** Copy the shape of `content/roadmaps/dsa/merge-sort.json` (the gold
`dsa` exemplar) and **OMIT its `viz` block**; keep every other key.

Required `dsa` fields (validator-enforced): `why_it_exists {problem, better_idea}` (naive_solution
optional), `mental_model {intuition, repeated_decision, ...}` -- **`repeated_decision` is REQUIRED**
(it powers the pass-2 explain-panel and the prediction), `explanation` OR `sections` (the teaching
body with a hand-trace), `common_mistakes` (>=1), `recall_questions` (>=3), `oa_questions` (>=2),
`sources` (2-5 URLs). Optional-but-use-them: `engineering_examples`, `when_not_to_use`, `pattern`,
`key_points`, `practice` (2-4 LeetCode, link only), `related` cross-links, `key_terms`.

> **Author `mental_model.repeated_decision` precisely** -- it is the exact question the pass-2
> prediction gates on, so make it a single crisp per-step decision (given below per node). A vague
> repeated_decision produces an ungradeable prediction later.

### The FIVE questions (every recall/oa answer must be derivable from the BODY)
1. Why it exists 2. How to simulate (mental_model + a hand-trace in `explanation`) 3. The invariant
4. A real engineering use 5. How to recognize it.

### Per-node must-hits

**`binary-tree-and-traversals`** (tier1, easy) -- the foundation node.
- what: a binary tree = nodes each with up to two children (left/right); terms to define plainly:
  root, leaf, parent/child, depth vs height, subtree, complete vs full vs balanced (define, don't
  belabor). The four traversal ORDERS named here (pre / in / post / level) -- this node introduces
  them; `dfs-pre-in-post` and `level-order-bfs` go deep.
- mental_model: "a node plus a left subtree plus a right subtree, all the way down." repeated_decision:
  **"at this node, which do I do -- visit it, go left, or go right?"** (the shared spine of all DFS).
- invariant: every node is reached exactly once; a traversal is a total order over all N nodes.
- misconceptions: "a binary tree is sorted" (NO -- that's a BST, a special case; general binary trees
  have no ordering); "traversal order = insertion order"; confusing depth (root-down) with height
  (leaf-up).
- engineering: the DOM, file-system directory trees, expression/AST trees in compilers, decision trees.
- practice: LeetCode 144/94/145 (pre/in/post-order), 102 (level-order).

**`dfs-pre-in-post`** (tier1, medium).
- what: three DFS orders differ ONLY by WHEN you "visit" the node relative to recursing:
  **pre** = node, L, R · **in** = L, node, R · **post** = L, R, node. Same three lines, one reordered.
- mental_model: repeated_decision: **"do I record this node BEFORE, BETWEEN, or AFTER its two
  recursive calls?"** -- that single placement choice is the whole topic.
- invariant + the payoff (teach it, it's the "why each is for"): **in-order of a BST yields sorted
  order** (the headline use); **post-order frees/computes children before the parent** (deletion,
  height, expression evaluation -- you need child results first); **pre-order serializes/clones a tree
  top-down** (copy the root before its subtrees). This "which order for which job" IS the interview
  signal.
- misconceptions: "in-order works on any tree to sort" (only a BST); "the orders visit different
  nodes" (NO -- same nodes, same count, different sequence); forgetting the null base case.
- engineering: in-order -> sorted BST iteration; post-order -> `rm -rf` / freeing a tree / evaluating
  `(2+3)*4`; pre-order -> tree serialization (LeetCode 297).
- practice: 94, 144, 145, 230 (kth-smallest in BST via in-order).

**`level-order-bfs`** (tier1, medium) -- the one DFS-vs-BFS contrast node.
- what: visit the tree level by level, left-to-right, using a **QUEUE** (not recursion/the call
  stack). Enqueue root; loop: dequeue a node, visit it, enqueue its non-null children.
- mental_model: repeated_decision: **"dequeue the front node -- which of its children do I enqueue
  (both, one, none)?"** Cross-link `queue-and-deque` (phase 9) hard: BFS is the canonical queue use.
- invariant: the queue always holds nodes in non-decreasing depth order; a node's children are always
  enqueued behind every node of its own level -> level-by-level ordering falls out for free.
- the DFS-vs-BFS distinction (the point of the node): DFS uses the CALL STACK (implicit) and goes
  deep; BFS uses an EXPLICIT QUEUE and goes wide. "Process by depth / find the shallowest thing" ->
  BFS. Grouping output per level = snapshot `queue.length` at the top of each loop iteration.
- misconceptions: "BFS uses a stack" (NO -- queue; a stack gives you DFS); "recursion can't do
  level-order" (it can with a level param, but the queue is the natural tool); enqueuing null children.
- engineering: shortest-path-in-unweighted (foreshadow graph BFS, phase 16), UI tree rendering by
  level, org-chart / "print each management layer."
- practice: 102, 103 (zigzag), 199 (right-side view), 111 (min depth).

**`bst-insert-and-search`** (tier1, medium).
- what: a **Binary Search TREE** -- for every node, all left-subtree keys < node < all right-subtree
  keys. Search/insert: compare target to node, go left if smaller, right if bigger, done if equal;
  insert lands at the first empty (null) child slot you reach.
- mental_model: repeated_decision: **"target vs this node -- go LEFT (smaller) or RIGHT (larger)?"**
  This is binary-search-over-a-tree; cross-link `binary-search` (phase 7) -- same halving idea, tree
  shape instead of array indices.
- invariant + the honest caveat: each comparison discards one whole subtree, so a BALANCED BST gives
  O(log n). **But a BST can degrade to O(n)** -- inserting sorted data builds a linked-list-shaped
  "spindly" tree. Teach this explicitly (it's the setup for why AVL/red-black exist, deferred to V2).
- misconceptions: "BST operations are always O(log n)" (only if balanced; worst case O(n));
  "insert can go anywhere" (no -- exactly one legal null slot by the ordering); "duplicates are fine"
  (pick and STATE a convention -- reject, or go-right).
- engineering: ordered maps/sets (`std::map`, Java `TreeMap` are balanced BSTs), DB range indexes
  (conceptually; real ones are B-trees -- name the link), autocomplete over sorted keys.
- practice: 700 (search), 701 (insert), 235 (LCA in a BST), 98 (validate -> next node).

**`validate-a-bst`** (tier2, medium) -- the classic "obvious-but-wrong" node.
- what: verify the WHOLE tree obeys the BST ordering, not just each parent-vs-child pair.
- mental_model: repeated_decision: **"is this node's value inside its allowed (low, high) range?"** --
  recurse carrying bounds: left child inherits `(low, node.val)`, right child inherits `(node.val,
  high)`, root starts `(-inf, +inf)`. INVARIANT to teach: **a node is valid iff low < val < high**;
  the bounds TIGHTEN as you descend.
- the killer misconception (make this the spine of the lesson): **checking only `left.val < node.val
  < right.val` is WRONG.** A node deep in the left subtree can be larger than an ancestor while still
  being a valid immediate child of its parent. Give the concrete counterexample tree:
  `[5,1,7,null,null,6,8]` -- 6 < 7 locally looks fine, but 6 < 5 is violated because 6 sits in 5's
  right... spell the exact failing tree out in `explanation`. (Alternative correct method: an in-order
  traversal must be strictly increasing -- mention it as the second valid approach and WHY it works,
  linking back to `dfs-pre-in-post`.)
- misconceptions: the local-compare bug above; using `<=` and mishandling duplicates; integer
  overflow with literal INT_MIN/MAX bounds (use nullable bounds).
- engineering: invariant/health checks on a tree index; property-based testing of a BST implementation.
- practice: 98 (validate), 530 (min abs diff via in-order), 501.

**`lowest-common-ancestor`** (tier2, medium).
- what: the LCA of nodes p and q = the DEEPEST node that has both as descendants (a node is its own
  ancestor). Cover BOTH: (a) the simple **BST** version -- walk from root, if both p,q < node go left,
  if both > go right, else this node is the split point = LCA; and (b) the **general binary tree**
  version -- post-order recursion returning "did I find p or q in my subtree"; the node where the two
  finds meet is the LCA.
- mental_model: repeated_decision (BST framing, the one to gate on later): **"are p and q both on the
  same side of this node, or does this node split them?"** Split -> this is the LCA.
- invariant: in the general version, a node returns non-null iff its subtree contains p or q; the
  first node whose LEFT and RIGHT both return non-null is the LCA.
- misconceptions: "LCA must be a leaf / must not be p or q" (NO -- if p is an ancestor of q, LCA = p);
  applying the O(log n) BST shortcut to a non-BST (it needs the ordering); assuming parent pointers
  exist.
- engineering: version-control merge-base (`git merge-base` = LCA in the commit DAG -- name it),
  taxonomy/category common-ancestor, routing in hierarchical networks.
- practice: 235 (LCA in BST), 236 (LCA general), 1650.

**`height-and-diameter`** (tier2, medium) -- the "return more than you're asked" node.
- what: **height** of a node = longest downward path to a leaf (`1 + max(leftH, rightH)`, null = -1 or
  0 -- pick and state). **Diameter** = longest path between ANY two nodes (may not pass through the
  root), measured in edges.
- mental_model: repeated_decision: **"at this node, combine left and right subtree HEIGHTS -- update
  the best diameter, then return the node's own height."** The aha: **one post-order pass returns the
  height while side-effecting the running max diameter** -- you compute a global answer without a
  separate traversal per node (the naive O(n^2) trap).
- invariant: diameter-through-a-node = leftHeight + rightHeight; the true diameter = max of that over
  all nodes -- so track a running max as post-order unwinds.
- misconceptions: "diameter always passes through the root" (NO -- give a tree where it doesn't);
  "recompute height for every node" (O(n^2) -- the whole point is the single-pass return+update);
  off-by-one confusion between counting NODES vs EDGES on the path (state which).
- engineering: balance checks (height-balanced test, LeetCode 110), network/tree latency = longest
  path, rendering/layout depth budgets.
- practice: 104 (max depth), 543 (diameter), 110 (balanced), 124 (max path sum -- the same
  return-value-vs-global-answer pattern, harder).

### Cross-links (`related` / prereqs / unlocks)
`recursive-tree-thinking` -> everything; `binary-tree-and-traversals` -> `dfs-pre-in-post`,
`level-order-bfs`; `dfs-pre-in-post` <-> `validate-a-bst` (in-order method) and `height-and-diameter`
(post-order); `level-order-bfs` prereq `queue-and-deque`; `bst-insert-and-search` prereq
`binary-search` -> `validate-a-bst` -> `lowest-common-ancestor`. Prereq all seven on
`recursion-tree`/`the-call-stack`.

## ASCII-only in JSON
`->` not an arrow glyph, `--` not an em-dash, straight quotes, `-inf`/`+inf` not the symbol.

## Process (pass 1)
1. Read the exemplars (`base-case.json` for concept shape; `merge-sort.json` for dsa shape, MINUS its
   viz) + `content/PROMPT-dsa.md` (QUALITY BAR items 6-7: every answer derivable from the body; no
   unexplained jargon; mental_model analogy must be mechanism-based).
2. Write the 8 files -- concept node has NO viz/why_it_exists/mental_model; the 7 dsa nodes have NO
   `viz` block but MUST have `mental_model.repeated_decision`.
3. `python content/validate.py` -> zero errors. Tick `content/_TODO-dsa.md`.
4. Standing pipeline: **Sonnet / Gemini-in-Antigravity lesson critic** (separate session,
   `content/RUN-lesson-critic-antigravity.md`) -> apply fixes -> re-critic. DONE only when a cold
   beginner can answer every recall/oa question from the body AND the expert finds zero errors.

---

## Viz pass (Claude, pass 2 -- SPEC ONLY, do NOT build now)

Recorded here so the design isn't re-derived later. **Antigravity does none of this.**

### Infra audit -- what already exists (verified against the code, 2026-07-12)
- **`TreeViz.jsx`** renders a binary tree from `frame.tree = { nodes: Map<id,{id,value,left,right,
  x,y}>, root }`, colors nodes via `nodeTags` (`visited | matched | path | invalid | inserted`), rings
  the `cursor` node, and prints a `nodeReturns[id]` annotation ABOVE a node (currently `up-arrow +
  value`). It already handles binary (`left`/`right`) AND n-ary (`children`) nodes.
- **`treeReducer` in `compile.js`** already folds: `TREE_INIT {nodes, root}` (computes in-order x/y
  layout ONCE + centers it), `VISIT_NODE {id}` (set cursor), `MARK_NODE {id, tag}`, `RETURN_NODE
  {id, value}` (set nodeReturns + cursor), plus the backtracking ops (`CHOOSE/UNCHOOSE/RECORD/PRUNE`).
- **`events.js`** `tree` family = `TREE_INIT, VISIT_NODE, MARK_NODE, COMPARE_NODE, SET_EDGE,
  RETURN_NODE`. `COMPARE_NODE`/`SET_EDGE` are declared but currently no-op in the reducer.
- **`predict.js`** already has `branch_binary` (left/right), `next_step_id`, `next_op` -- enough to
  gate BST-descent and traversal predictions with ZERO new derives.

=> **No new renderer. No new op family. No new derive strictly required.** All 7 nodes are
TREE_INIT-then-traverse: the generator parses the lesson's level-order-array `default_input` into
`{nodes,root}`, emits `TREE_INIT`, then emits `VISIT_NODE`/`MARK_NODE`/`RETURN_NODE` as it walks.

### Small ADDITIVE polish (optional, do at build time; keep §9.5 additive-only)
- **Traversal-order badges** (`dfs-pre-in-post`, `binary-tree-and-traversals`): reuse `nodeReturns[id]
  = visitIndex` to stamp the order number -- OR add a dedicated `nodeBadges` slice if the up-arrow
  glyph reads wrong for an order number. Prefer reuse first.
- **Validate-BST bounds** (`validate-a-bst`): show each node's `(low, high)` window. Cheapest: emit
  `RETURN_NODE {id, value: "(low, high)"}` (renders as-is). Cleaner: add a `nodeAnnotations[id]` string
  channel to the reducer + a small `<text>` under the node in TreeViz. Decide at build time.
- **LCA path pair** (`lowest-common-ancestor`): two root->p and root->q paths. v1 = tag both `path`
  and tag the LCA `matched`. A second path color is a nice-to-have, not required.
- Wire `COMPARE_NODE` in the reducer (currently no-op) IF a distinct "comparing" highlight beats
  reusing `cursor` for BST search -- otherwise leave it.

### Per-node viz plan (generator + `default_input` + the prediction to gate)
| slug | trace | default_input (level-order, `null` = missing) | prediction (`derive`) |
|---|---|---|---|
| `binary-tree-and-traversals` | build tree; VISIT each node in one chosen order, badge order # | `[1,2,3,4,5,null,6]` | next node visited (`next_step_id`/`next_op`) |
| `dfs-pre-in-post` | same tree, three runs (or toggle) showing pre/in/post visit sequence | `[4,2,6,1,3,5,7]` (a BST so in-order = sorted, the aha) | "before/between/after?" -> `branch_binary` on record-placement, or self-graded |
| `level-order-bfs` | queue side-panel (StackQueueViz reuse) + VISIT per dequeue | `[1,2,3,4,5,6,7]` | which child enqueues next (`next_op`) |
| `bst-insert-and-search` | descend comparing; MARK path; insert lands at null slot | tree `[8,3,10,1,6,null,14]`, target `7` | **go LEFT or RIGHT?** (`branch_binary`) -- the headline gate |
| `validate-a-bst` | descend carrying (low,high); MARK invalid on violation | valid `[5,1,7,null,null,6,8]` VS the classic-bug tree | "in range -> valid?" (self-graded / `branch_binary`) |
| `lowest-common-ancestor` | BST split-walk; MARK both paths; matched at split | tree `[6,2,8,0,4,7,9]`, p=`2`, q=`8` | same side or split? (`branch_binary`) |
| `height-and-diameter` | post-order RETURN_NODE heights; running-max diameter in `vars` | `[1,2,3,4,5]` (skewed so diameter dodges the root) | next node's returned height (`next_step_id`) |

### Pass-2 process (Claude)
1. Build 7 generators, each pure `(input) -> {input, events}`, TREE_INIT-first; one `*.golden.mjs`
   each (include an edge input: single node / empty / skewed). Register in `registry.js`. `npm run
   golden` green.
2. Add the `viz` block to each of the 7 lessons (`generator`, `default_input`, `invariants`,
   `steps[{id,label}]`, `predictions[]`, optional `code`). `python content/validate.py` green (it
   checks `viz.generator` is registered + `derive` names exist). `node frontend/scripts/sync-content.mjs`.
3. **Browser-verify each renders** at `/roadmaps/dsa/learn/<slug>` -- goldens catch trace regressions
   but NOT JSX render crashes (a past renderer change shipped a crash the goldens passed). Do NOT
   commit; hand back the exact list of changed files.

### Follow-on (NOT phase 14): Heaps (phase 15, 3 nodes)
`binary-heap`/`heap-sort`/`top-k-with-a-heap` are the natural next viz: heap = TreeViz + ArrayViz
SIDE-BY-SIDE (the array IS the tree -- that's the aha), ops `SIFT_SWAP`. Reuses everything here plus
the existing ArrayViz. Separate packet.
