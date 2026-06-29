# Curation queue — DSA: Algorithms Visualized (`dsa`)

> **For Antigravity.** Generate **one JSON per node** using **`PROMPT-dsa.md`**. Input = the Gemini
> deep-research JSON (from `PROMPT-dsa-research.md`), run one phase at a time. Two kinds, tagged per
> node below: **`C` = `kind:"concept"` + `runtime:"none"`** (idea explained with words — exemplars:
> the 3 finished Foundations files); **`D` = `kind:"dsa"`** (algorithm you step through). Files go in
> `content/roadmaps/dsa/<slug>.json` (filename = slug). Validate with `python content/validate.py`; tick
> a box once saved **and** green.
>
> **⛔ You do NOT author visualization.** No `viz`, no `animation`, no `image`/`illustration`. Claude
> layers all visuals afterward. See the BOUNDARY section in `PROMPT-dsa.md`.

Source of truth for nodes/titles/order: `backend/seed_dsa.py` (110 nodes, 20 phases).
**Build order = phase order** (the curriculum is a beginner on-ramp: Foundations → Complexity →
Arrays first; recursion deferred to phase 11). Do one phase per research run.

Legend: `[x]` done & green · `C` concept · `D` dsa(trace) · slug in `code`.

---

## 1. Foundations  (all `C`)
- [x] What is an algorithm?  · C · `what-is-an-algorithm`
- [x] Tracing state & invariants  · C · `tracing-state-and-invariants`
- [x] Iteration & traversal  · C · `iteration-and-traversal`

## 2. Complexity  (all `C`)
- [x] Counting operations  · C · `counting-operations`
- [x] Big-O notation  · C · `big-o-notation`
- [x] Common complexities  · C · `common-complexities`
- [x] Logarithms & powers of two  · C · `logarithms-and-powers-of-two`
- [x] Amortized analysis  · C · `amortized-analysis`

## 3. Arrays
- [x] Arrays & memory  · C · `arrays-and-memory`
- [x] In-place operations  · D · `in-place-operations`
- [x] Prefix sums  · D · `prefix-sums`
- [x] 2D arrays & matrices  · C · `2d-arrays-and-matrices`

## 4. Hashing
- [ ] Hash tables  · C · `hash-tables`
- [ ] Hash sets vs maps  · C · `hash-sets-vs-maps`
- [ ] Frequency counting  · D · `frequency-counting`
- [ ] Collisions & load factor  · C · `collisions-and-load-factor`

## 5. Strings
- [ ] String traversal  · C · `string-traversal`
- [ ] Frequency arrays  · D · `frequency-arrays`
- [ ] Two pointers on strings  · D · `two-pointers-on-strings`
- [ ] Palindromes  · D · `palindromes`
- [ ] Anagrams  · D · `anagrams`
- [ ] Pattern matching (KMP)  · D · `pattern-matching-kmp`

## 6. Sorting — Basics  (all `D`)
- [ ] Bubble sort  · D · `bubble-sort`
- [ ] Selection sort  · D · `selection-sort`
- [ ] Insertion sort  · D · `insertion-sort`

## 7. Searching  (all `D`)
- [ ] Linear search  · D · `linear-search`
- [ ] Binary search  · D · `binary-search`
- [ ] Lower bound  · D · `lower-bound`
- [ ] Upper bound  · D · `upper-bound`
- [ ] Binary search on the answer  · D · `binary-search-on-the-answer`

## 8. Two Pointers & Windows  (all `D`)
- [ ] Two pointers  · D · `two-pointers`
- [ ] Fast & slow pointers  · D · `fast-and-slow-pointers`
- [ ] Sliding window (fixed)  · D · `sliding-window-fixed`
- [ ] Sliding window (variable)  · D · `sliding-window-variable`
- [ ] Kadane's algorithm  · D · `kadane-s-algorithm`

## 9. Stacks & Queues  (all `D`)
- [ ] Stack fundamentals  · D · `stack-fundamentals`
- [ ] Valid parentheses  · D · `valid-parentheses`
- [ ] Min stack  · D · `min-stack`
- [ ] Monotonic stack  · D · `monotonic-stack`
- [ ] Next greater element  · D · `next-greater-element`
- [ ] Queue & deque  · D · `queue-and-deque`

## 10. Linked Lists  (all `D`)
- [ ] Traversal & reversal  · D · `traversal-and-reversal`
- [ ] Find the middle  · D · `find-the-middle`
- [ ] Floyd's cycle detection  · D · `floyd-s-cycle-detection`
- [ ] Merge two sorted lists  · D · `merge-two-sorted-lists`
- [ ] Reverse in k-groups  · D · `reverse-in-k-groups`

## 11. Recursion  (all `C` — mostly concept)
- [ ] Base case  · C · `base-case`
- [ ] Recursive relation  · C · `recursive-relation`
- [ ] The call stack  · C · `the-call-stack`
- [ ] Recursion tree  · C · `recursion-tree`

## 12. Backtracking  (all `D`)
- [ ] Backtracking template  · D · `backtracking-template`
- [ ] Subsets  · D · `subsets`
- [ ] Permutations  · D · `permutations`
- [ ] Combination sum  · D · `combination-sum`
- [ ] N-Queens  · D · `n-queens`

## 13. Sorting — Divide & Conquer
- [ ] ~~Merge sort~~  · D · `merge-sort` — **SKIP: Claude authors as the gold exemplar**
- [ ] Quick sort  · D · `quick-sort`
- [ ] Counting sort  · D · `counting-sort`

## 14. Trees
- [ ] Recursive tree thinking  · C · `recursive-tree-thinking`
- [ ] Binary tree & traversals  · D · `binary-tree-and-traversals`
- [ ] DFS: pre / in / post  · D · `dfs-pre-in-post`
- [ ] Level-order (BFS)  · D · `level-order-bfs`
- [ ] BST: insert & search  · D · `bst-insert-and-search`
- [ ] Validate a BST  · D · `validate-a-bst`
- [ ] Lowest common ancestor  · D · `lowest-common-ancestor`
- [ ] Height & diameter  · D · `height-and-diameter`

## 15. Heaps  (all `D`)
- [ ] Binary heap  · D · `binary-heap`
- [ ] Heap sort  · D · `heap-sort`
- [ ] Top-K with a heap  · D · `top-k-with-a-heap`

## 16. Graphs
- [ ] Graph representations  · C · `graph-representations`
- [ ] Weighted vs unweighted  · C · `weighted-vs-unweighted`
- [ ] BFS on graphs  · D · `bfs-on-graphs`
- [ ] DFS on graphs  · D · `dfs-on-graphs`
- [ ] When BFS stops working  · C · `when-bfs-stops-working`
- [ ] Connected components  · D · `connected-components`
- [ ] Cycle detection  · D · `cycle-detection`
- [ ] Topological sort  · D · `topological-sort`
- [ ] Dijkstra's algorithm  · D · `dijkstra-s-algorithm`
- [ ] Union-Find  · D · `union-find`
- [ ] Minimum spanning tree (Kruskal)  · D · `minimum-spanning-tree-kruskal`

## 17. Greedy
- [ ] Why greedy works  · C · `why-greedy-works`
- [ ] Why greedy fails  · C · `why-greedy-fails`
- [ ] Interval scheduling  · D · `interval-scheduling`
- [ ] Merge intervals  · D · `merge-intervals`
- [ ] Jump game  · D · `jump-game`

## 18. Dynamic Programming
- [ ] Overlapping subproblems  · C · `overlapping-subproblems`
- [ ] Optimal substructure  · C · `optimal-substructure`
- [ ] State & transition  · C · `state-and-transition`
- [ ] Memoization (top-down)  · C · `memoization-top-down`
- [ ] Tabulation (bottom-up)  · C · `tabulation-bottom-up`
- [ ] Space optimization  · C · `space-optimization`
- [ ] Climbing stairs / Fibonacci  · D · `climbing-stairs-fibonacci`
- [ ] House robber  · D · `house-robber`
- [ ] Coin change  · D · `coin-change`
- [ ] 0/1 Knapsack  · D · `0-1-knapsack`
- [ ] Longest common subsequence  · D · `longest-common-subsequence`
- [ ] Edit distance  · D · `edit-distance`
- [ ] Longest increasing subsequence  · D · `longest-increasing-subsequence`
- [ ] Grid DP (unique paths / min path sum)  · D · `grid-dp-unique-paths-min-path-sum`

## 19. Bit Manipulation
- [ ] Bitwise operators  · C · `bitwise-operators`
- [ ] Single number (XOR)  · D · `single-number-xor`
- [ ] Counting bits  · D · `counting-bits`

## 20. Algorithm Design Patterns  (all `C` — recognition capstone)
- [ ] Brute force first  · C · `brute-force-first`
- [ ] Precomputation  · C · `precomputation`
- [ ] Recognizing divide & conquer  · C · `recognizing-divide-and-conquer`
- [ ] Recognizing two pointers  · C · `recognizing-two-pointers`
- [ ] Recognizing sliding window  · C · `recognizing-sliding-window`
- [ ] Recognizing greedy vs DP  · C · `recognizing-greedy-vs-dp`
- [ ] Recognizing graph problems  · C · `recognizing-graph-problems`
- [ ] Pattern recognition drill  · C · `pattern-recognition-drill`

---

**110 nodes total · 3 done · 1 skip (merge-sort = Claude).** Split: ~40 `C` (concept) · ~67 `D` (dsa).
Kind tags are a best-first call — if a `D` node has no real trace to step through (pure idea), flag it
and treat it as `C`; if a `C` node clearly wants a step-through, flag it for Claude.

## Wiring (Claude-side, not Antigravity)
- The `kind:"dsa"` render path in `LessonView.jsx` (five-questions blocks + lazy execution-trace Player)
  — **in progress.** Concept render path already works.
- `viz` generators per trace node in `frontend/src/dsa/` (events → compile → renderers) — Claude.
- `seed_dsa.py` must be run on the DB (user hand-off) for roadmap nodes to link to these lessons.
- `sync-content.mjs` copies `content/roadmaps/dsa/` → `frontend/public/content/`; live on next push.
