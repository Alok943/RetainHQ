# LeetCode mapping report

Model: gemini-3.5-flash-lite  |  API calls: 101  |  in_tokens: 453985  out_tokens: 259605  |  wall: 43.6s

## Authenticity checks
- reason diversity: 2991 distinct / 3337 rows (89.6%), max repeat 70x -> FAIL
- alternatives: 33 distinct combos, 3.8% of rows carry one -> FAIL
- call accounting: 101 calls for 3337 problems

### spot check (5 random rows)
- #2926 primary=fenwick-tree-bit conf=high :: fenwick tree efficiently queries prefix maximums for subsequence sums.
- #1316 primary=rolling-hash-rabin-karp conf=high :: Rolling hash detects duplicate substrings efficiently.
- #3735 primary=rolling-hash-rabin-karp conf=low :: rolling hash checks string equality efficiently
- #466 primary=state-and-transition conf=low :: repeating pattern cycles across large string bounds
- #77 primary=combination-sum conf=high :: backtracking generates all combinations of k numbers

## Distributional health checks
- max primary share: 18.0% (cap 8%) -> FAIL
- low+medium share: 36.7% (floor 8%) -> OK
- gcd-lcm-and-modular-arithmetic: 97 problems
- combinatorics-and-counting: 80 problems
- bitmask-dp: 80 problems
- pattern-matching-kmp: 9 problems
- rolling-hash-rabin-karp: 19 problems
- ordered-sets-and-sorted-containers: 11 problems

### top 15 / bottom (zero-usage) slugs
    599  out_of_scope
    151  prefix-sums
    141  frequency-counting
    125  two-pointers
    113  dfs-on-graphs
    106  hash-tables
     97  binary-search-on-the-answer
     97  gcd-lcm-and-modular-arithmetic
     86  sliding-window-variable
     80  combinatorics-and-counting
     80  bitmask-dp
     78  2d-arrays-and-matrices
     73  bfs-on-graphs
     68  binary-search
     68  tabulation-bottom-up

parked batches: 0