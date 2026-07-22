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

Source of truth for nodes/titles/order: `backend/seed_dsa.py` (124 nodes, 21 phases).
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
- [x] Hash tables  · C · `hash-tables`
- [x] Hash sets vs maps  · C · `hash-sets-vs-maps`
- [x] Frequency counting  · D · `frequency-counting`
- [x] Collisions & load factor  · C · `collisions-and-load-factor`

## 5. Strings
- [x] String traversal  · C · `string-traversal`
- [x] Frequency arrays  · D · `frequency-arrays`
- [x] Two pointers on strings  · D · `two-pointers-on-strings`
- [x] Palindromes  · D · `palindromes`
- [x] Anagrams  · D · `anagrams`
- [x] Pattern matching (KMP)  · D · `pattern-matching-kmp`

## 6. Sorting — Basics  (all `D`)
- [x] Bubble sort  · D · `bubble-sort`
- [x] Selection sort  · D · `selection-sort`
- [x] Insertion sort  · D · `insertion-sort`

## 7. Searching  (all `D`)
- [x] Linear search  · D · `linear-search`
- [x] Binary search  · D · `binary-search`
- [x] Lower bound  · D · `lower-bound`
- [x] Upper bound  · D · `upper-bound`
- [x] Binary search on the answer  · D · `binary-search-on-the-answer`

## 8. Two Pointers & Windows  (all `D`)
- [x] Two pointers  · D · `two-pointers`
- [x] Fast & slow pointers  · D · `fast-and-slow-pointers`
- [x] Sliding window (fixed)  · D · `sliding-window-fixed`
- [x] Sliding window (variable)  · D · `sliding-window-variable`
- [x] Kadane's algorithm  · D · `kadane-s-algorithm`

## 9. Stacks & Queues  (all `D`)
- [x] Stack fundamentals  · D · `stack-fundamentals`
- [x] Valid parentheses  · D · `valid-parentheses`
- [x] Min stack  · D · `min-stack`
- [x] Monotonic stack  · D · `monotonic-stack`
- [x] Next greater element  · D · `next-greater-element`
- [x] Queue & deque  · D · `queue-and-deque`

## 10. Linked Lists  (all `D`)
- [x] Traversal & reversal  · D · `traversal-and-reversal`
- [x] Find the middle  · D · `find-the-middle`
- [x] Floyd's cycle detection  · D · `floyd-s-cycle-detection`
- [x] Merge two sorted lists  · D · `merge-two-sorted-lists`
- [x] Reverse in k-groups  · D · `reverse-in-k-groups`

## 11. Recursion  (all `C` — mostly concept)
- [x] Base case  · C · `base-case`
- [x] Recursive relation  · C · `recursive-relation`
- [x] The call stack  · C · `the-call-stack`
- [x] Recursion tree  · C · `recursion-tree`

## 12. Backtracking  (all `D`)
- [x] Backtracking template  · D · `backtracking-template`
- [x] Subsets  · D · `subsets`
- [x] Permutations  · D · `permutations`
- [x] Combination sum  · D · `combination-sum`
- [x] N-Queens  · D · `n-queens`

## 13. Sorting — Divide & Conquer
- [x] Merge sort  · D · `merge-sort` — authored by Claude as the gold exemplar
- [ ] Non-comparison sorts  · D · `non-comparison-sorts`
- [ ] Quicksort & partition  · D · `quicksort-and-partition`

## 14. Trees
- [x] Recursive tree thinking  · C · `recursive-tree-thinking`
- [x] Binary tree & traversals  · D · `binary-tree-and-traversals`
- [x] DFS: pre / in / post  · D · `dfs-pre-in-post`
- [x] Level-order (BFS)  · D · `level-order-bfs`
- [x] BST: insert & search  · D · `bst-insert-and-search`
- [x] Validate a BST  · D · `validate-a-bst`
- [x] Lowest common ancestor  · D · `lowest-common-ancestor`
- [x] Height & diameter  · D · `height-and-diameter`

## 15. Heaps  (all `D`)
- [x] Binary heap  · D · `binary-heap`
- [x] Heap sort  · D · `heap-sort`
- [x] Top-K with a heap  · D · `top-k-with-a-heap`

## 16. Graphs
- [x] Graph representations  · C · `graph-representations`
- [x] Weighted vs unweighted  · C · `weighted-vs-unweighted`
- [x] BFS on graphs  · D · `bfs-on-graphs`
- [x] DFS on graphs  · D · `dfs-on-graphs`
- [x] When BFS stops working  · C · `when-bfs-stops-working`
- [x] Connected components  · D · `connected-components`
- [x] Cycle detection  · D · `cycle-detection`
- [x] Topological sort  · D · `topological-sort`
- [x] Dijkstra's algorithm  · D · `dijkstra-s-algorithm`
- [x] Union-Find  · D · `union-find`
- [x] Minimum spanning tree (Kruskal)  · D · `minimum-spanning-tree-kruskal`

## 17. Greedy
- [x] Why greedy works  · C · `why-greedy-works`
- [x] Why greedy fails  · C · `why-greedy-fails`
- [x] Interval scheduling  · D · `interval-scheduling`
- [x] Merge intervals  · D · `merge-intervals`
- [x] Jump game  · D · `jump-game`

## 18. Dynamic Programming
- [x] Overlapping subproblems  · C · `overlapping-subproblems`
- [x] Optimal substructure  · C · `optimal-substructure`
- [x] State & transition  · C · `state-and-transition`
- [x] Memoization (top-down)  · C · `memoization-top-down`
- [x] Tabulation (bottom-up)  · C · `tabulation-bottom-up`
- [x] Space optimization  · C · `space-optimization`
- [x] Climbing stairs / Fibonacci  · D · `climbing-stairs-fibonacci`
- [x] House robber  · D · `house-robber`
- [x] Coin change  · D · `coin-change`
- [x] 0/1 Knapsack  · D · `0-1-knapsack`
- [x] Longest common subsequence  · D · `longest-common-subsequence`
- [x] Edit distance  · D · `edit-distance`
- [x] Longest increasing subsequence  · D · `longest-increasing-subsequence`
- [x] Grid DP (unique paths / min path sum)  · D · `grid-dp-unique-paths-min-path-sum`

## 19. Bit Manipulation
- [x] Bitwise operators  · C · `bitwise-operators`
- [x] Single number (XOR)  · D · `single-number-xor`
- [x] Counting bits  · D · `counting-bits`

## 20. Algorithm Design Patterns  (all `C` — recognition capstone)
- [x] Brute force first  · C · `brute-force-first`
- [x] Precomputation  · C · `precomputation`
- [x] Recognizing divide & conquer  · C · `recognizing-divide-and-conquer`
- [x] Recognizing two pointers  · C · `recognizing-two-pointers`
- [x] Recognizing sliding window  · C · `recognizing-sliding-window`
- [x] Recognizing greedy vs DP  · C · `recognizing-greedy-vs-dp`
- [x] Recognizing graph problems  · C · `recognizing-graph-problems`
- [x] Pattern recognition drill  · C · `pattern-recognition-drill`

## 21. Advanced (14 nodes)
- [ ] Quickselect  · D · `quickselect`
- [ ] Trie (prefix tree)  · D · `trie-prefix-tree`
- [ ] Designing data structures  · C · `designing-data-structures`
- [ ] GCD, LCM & modular arithmetic  · C · `gcd-lcm-and-modular-arithmetic`
- [ ] Tree DP  · D · `tree-dp`
- [ ] Linked list rewiring  · D · `linked-list-rewiring`
- [ ] Difference array  · D · `difference-array`
- [ ] Segment tree  · D · `segment-tree`
- [ ] Fenwick tree (BIT)  · D · `fenwick-tree-bit`
- [ ] Ordered sets & sorted containers  · C · `ordered-sets-and-sorted-containers`
- [ ] Combinatorics & counting  · C · `combinatorics-and-counting`
- [ ] Bitmask DP  · D · `bitmask-dp`
- [ ] Monotonic deque  · D · `monotonic-deque`
- [ ] Rolling hash (Rabin-Karp)  · D · `rolling-hash-rabin-karp`

---

**124 nodes total · 108 done · 16 open.** Split: ~44 `C` (concept) · ~82 `D` (dsa).
