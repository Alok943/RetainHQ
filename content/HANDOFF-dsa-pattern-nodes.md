# DSA pattern-node gap audit — step 0 of the LeetCode retention spec

**Method:** the 108 existing `content/roadmaps/dsa/*.json` lessons diffed against the 72
LeetCode topic tags weighted by volume across the **3,224 free problems** in
`content/leetcode-catalog/catalog.v1.json` (v1 pull, 2026-07-21), plus patterns that carry
no distinct LeetCode tag but are real interview units.

**Why this is blocking** (`docs/SPEC-leetcode-retention.md` §2, §8 step 0): the concept
vocabulary is closed and hand-authored; LLMs may only classify onto it. Every gap here is a
problem set the mapper would otherwise be forced to mis-map or discard.

**Verdict: coverage is strong.** All ten highest-volume tags are covered, most of them
several times over. The gaps are a long tail plus one glaring omission (quicksort).

---

## P0 — author first (blocks mapping quality)

| Proposed slug | Drives | LC tags (free-problem count) | Why it's a gap |
|---|---|---|---|
| `quicksort-and-partition` | sorting, in-place | `sorting` (453) | **Glaring.** bubble/insertion/selection/merge/heap sort all exist; the most-asked sort does not. Lyapunov of the whole sorting section. |
| `quickselect` | top-k without a heap | `quickselect` (8) + `sorting` | Follows directly from partition; the standard "kth largest" answer alongside `top-k-with-a-heap`. |
| `trie-prefix-tree` | string structures | `trie` (46) | Classic interview structure, zero coverage. |
| `designing-data-structures` | design round | `design` (99), `data-stream` (16) | LRU/LFU/insert-delete-getRandom. `min-stack` is the only design lesson; "design" is an entire interview round. |
| `gcd-lcm-and-modular-arithmetic` | number theory | `number-theory` (93), `math` (598) | No lesson touches GCD, primes, or mod arithmetic. |
| `tree-dp` | postorder state propagation | (untagged; sits under `tree` 198 / `dynamic-programming` 584) | The return value is not the answer — rob/skip pairs, height-and-sum. Covers 124, 337, 543, 968. **Found by owner review of the golden set, not by tag diff.** |
| `linked-list-rewiring` | pointer surgery | `linked-list` (66) | Dummy head, building a new list, digit arithmetic. Covers 2, 445, 86, 143, 328. `traversal-and-reversal` does not fit problems where nothing is reversed. **Found by owner review.** |
| `difference-array` | range updates | (untagged; sits under `prefix-sum` 236) | `prefix-sums` exists without its inverse. Also the exact confusable-pair example the product vision uses — §6 needs both nodes to author a discriminating card. |

> Node count: **16** (14 from the tag diff + 2 from golden-set review, 2026-07-21).
> Vocabulary is now 124 concepts.

## P1 — author next

| Proposed slug | LC tags (count) | Note |
|---|---|---|
| `segment-tree` | `segment-tree` (69) | Highest-volume uncovered structure. |
| `fenwick-tree-bit` | `binary-indexed-tree` (35) | Pairs with segment-tree; teach after prefix-sums. |
| `ordered-sets-and-sorted-containers` | `ordered-set` (64) | TreeMap/`SortedList` idioms; partly language-specific, still a real pattern. |
| `combinatorics-and-counting` | `combinatorics` (55), `counting` (184) | nCr, pigeonhole, counting arguments. |
| `bitmask-dp` | `bitmask` (47) | `bitwise-operators` teaches ops, not subset-state DP. |
| `monotonic-deque` | `monotonic-queue` (23) | Sliding-window maximum. `monotonic-stack` exists; the deque variant doesn't. |
| `rolling-hash-rabin-karp` | `rolling-hash` (26), `hash-function` (33) | Complements `pattern-matching-kmp`. |
| `non-comparison-sorts` | `counting-sort` (9), `bucket-sort` (6), `radix-sort` (3) | Low volume, high conceptual value: beating the O(n log n) bound. |

## P2 — defer, revisit after first mapping pass

`game-theory` (26) · `geometry` (40, low placement value) · `line-sweep` (6) ·
`reservoir-sampling` (4) + `randomized` (12) · `cyclic-sort` (untagged pattern) ·
`strongly-connected-components` (2) · `eulerian-circuit` (3) · `suffix-array` (5)

## Explicitly OUT of the DSA vocabulary → `role='out_of_scope'` (spec §3.2.0)

`database` (94 — belongs to the `sql` roadmap) · `concurrency` (6) · `shell` (4) ·
`javascript`/pandas study-plan sets (the 91 untagged free problems) · `interactive` (5) ·
`iterator` (5) · `brainteaser` (18)

Tags that are **not patterns** and must never become nodes — they describe "just implement
it", and the mapper should fall through to the real underlying pattern:
`simulation` (193) · `enumeration` (146) · `array` (1879) · `string` (758) · `math` (598)
as a bare tag.

---

## Coverage confirmed (no action)

All of: `hash-table` (5 lessons) · `dynamic-programming` (14) · `two-pointers` (3) ·
`sliding-window` (3) · `binary-search` (4) · `dfs`/`bfs`/`graph` (7) · `stack` (5) ·
`linked-list` (7) · `backtracking` (5) · `heap` (3) · `tree`/`binary-tree`/`bst` (6) ·
`recursion` (5) · `greedy` (4) · `union-find` · `topological-sort` · `divide-and-conquer` ·
`string-matching` · `prefix-sum` · `bit-manipulation` (3) · `minimum-spanning-tree` ·
`shortest-path`.

---

## Authoring

Lessons for these nodes are **ordinary dsa lessons** — `content/PROMPT-dsa.md` is the
contract, `content/PROMPT-dsa-research.md` feeds it, `python content/validate.py` is the
gate, Claude adds `viz` afterward (the ⛔ boundary in PROMPT-dsa.md applies unchanged).
Add them to `content/_TODO-dsa.md` with kind + phase before generation.

**Sequencing note:** P0 must exist as *nodes* (seeded, with prerequisite edges) before the
problem→concept mapping packet runs. The lesson bodies can lag; the mapper needs the
vocabulary, not the prose.
