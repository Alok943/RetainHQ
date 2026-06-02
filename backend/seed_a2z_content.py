"""
Content pass for the Striver A2Z roadmap: fills each node's `description`
(the pre-written note shown on right-click) and attaches `subtopics` as
child nodes (shown on double-click) for flagship topics.

Idempotent: re-running updates descriptions and rebuilds subtopic children.
Matched by node title within the DSA roadmap.

Run: ./.venv/Scripts/python.exe seed_a2z_content.py
"""
import asyncio
import uuid
from sqlalchemy import text
from app.core.database import engine

ROADMAP_ID = "22222222-2222-2222-2222-222222222222"

# title -> short explanation (shown on right-click)
DESCRIPTIONS = {
    # Step 1
    "Data types, I/O & operators": "Primitive types, size limits, reading input and arithmetic/relational/logical operators — the absolute basics every program uses.",
    "Conditionals & loops": "if/else, switch, for/while/do-while. Master loop boundaries and early exits before anything harder.",
    "Functions & scope": "Parameters, return values, pass-by-value vs reference, and variable scope/lifetime.",
    "Star & number patterns": "Nested-loop pattern printing — builds intuition for 2D iteration and index math used everywhere later.",
    "Count digits / reverse / palindrome number": "Extract digits with %10 and /10; reverse a number and check if it reads the same backward.",
    "GCD/HCF & Euclidean algorithm": "gcd(a,b)=gcd(b, a%b). O(log min(a,b)) — foundational for number theory and fractions.",
    "Armstrong, divisors, prime check": "Classic number checks; trial division up to sqrt(n) for primes and divisor enumeration.",
    "Print N times / 1..N / N..1": "First taste of recursion: base case + recursive call. Understand the call stack here.",
    "Sum of N, factorial, reverse array": "Parameterized recursion accumulating a result; reverse array with two-pointer recursion.",
    "String palindrome & Fibonacci": "Recursion with two moving indices, and the classic overlapping-subproblem Fibonacci (hint at DP).",
    "Hashing theory (number & character)": "Pre-store counts in an array/map for O(1) lookups — trades space for time.",
    "Count frequencies of elements": "Build a frequency map in one pass; the backbone of countless array/string problems.",
    # Step 2
    "Selection sort": "Repeatedly pick the minimum and place it. O(n^2), minimal swaps.",
    "Bubble sort": "Adjacent swaps bubble the largest to the end each pass. O(n^2); detect early-sorted.",
    "Insertion sort": "Grow a sorted prefix by inserting each element into place. O(n^2) but fast on nearly-sorted data.",
    "Merge sort": "Divide, sort halves, merge. Stable O(n log n) — the template for divide & conquer.",
    "Quick sort": "Partition around a pivot, recurse. Average O(n log n), in-place; worst O(n^2).",
    "Recursive bubble & insertion": "Re-express the basic sorts recursively to cement recursion thinking.",
    # Step 3 Arrays
    "Largest & second largest": "Single pass tracking two maxima — careful with duplicates and the second-largest update.",
    "Check sorted & remove duplicates": "Verify non-decreasing order; remove dups in-place on a sorted array with two pointers.",
    "Left rotate by 1 and by D": "Rotate using the reverse-reverse-reverse trick in O(n) time, O(1) space.",
    "Move zeros to end": "Two-pointer partition keeping non-zeros stable; classic in-place rearrangement.",
    "Union, intersection & missing number": "Merge two sorted arrays without dups; find the missing number via sum or XOR.",
    "Max consecutive ones & single number": "Running count of 1s; XOR all elements to cancel pairs and reveal the unique one.",
    "Longest subarray with sum K": "Prefix-sum + hashmap of earliest prefix; O(n). Foundational sliding/prefix technique.",
    "Two Sum & sort 0s/1s/2s": "Hashmap for Two Sum; Dutch National Flag three-pointer sort for 0/1/2.",
    "Majority element (n/2)": "Boyer-Moore voting: one candidate survives if it appears > n/2 times. O(1) space.",
    "Kadane's max subarray sum": "Carry running sum, reset to 0 when negative. The canonical 1D DP on arrays.",
    "Best time to buy & sell stock": "Track min price so far and best profit in one pass.",
    "Rearrange by sign & next permutation": "Alternate +/- placement; next permutation via the pivot-and-swap algorithm.",
    "Leaders & longest consecutive sequence": "Right-to-left leaders scan; longest consecutive run via a hash set in O(n).",
    "Set matrix zeros, rotate & spiral": "In-place matrix manipulation using first row/col as markers; layer-by-layer traversal.",
    "Pascal's triangle": "Three variants: value at (r,c), a row, or the whole triangle via nCr relations.",
    "Majority (n/3), 3-Sum & 4-Sum": "Extended Boyer-Moore (≤2 candidates); sort + two-pointer for k-sum families.",
    "Largest subarray with 0 sum / XOR K": "Prefix sum/XOR + hashmap of first occurrence — same trick, two flavors.",
    "Merge intervals & merge sorted arrays": "Sort by start and coalesce overlaps; gap method to merge in-place without extra space.",
    "Count inversions & reverse pairs": "Modified merge sort counts cross-pairs in O(n log n).",
    "Max product subarray": "Track running max and min (negatives flip) — prefix/suffix product also works.",
    # Step 4 Binary Search
    "BS theory, lower/upper bound": "Halve the search space each step. Lower/upper bound find first ≥/> target — master these.",
    "Search insert, floor & ceil": "Variations of lower/upper bound returning insertion index or nearest values.",
    "First/last occurrence & count": "Two bounded searches; count = last - first + 1.",
    "Search in rotated array I & II": "Identify the sorted half each step; duplicates (II) force an edge-shrink fallback.",
    "Min in rotated & single element": "Find the rotation pivot; XOR-index parity locates the lone element in O(log n).",
    "Peak element": "Move toward the rising side; any local peak qualifies. O(log n).",
    "Sqrt & Nth root": "Binary search on the answer space [1, n] checking mid^k vs n.",
    "Koko eating bananas": "BS on eating speed; feasibility check = total hours ≤ H. The 'BS on answer' template.",
    "Min days for bouquets & smallest divisor": "BS on the answer with a greedy/count feasibility predicate.",
    "Capacity to ship & Kth missing": "Monotonic predicate over capacity/position — BS on answer.",
    "Aggressive cows & book allocation": "Maximize-minimum / minimize-maximum partitioning via BS on the answer.",
    "Split array / painter's partition": "Same minimize-the-maximum-subarray-sum pattern as book allocation.",
    "Median of two sorted arrays": "Partition both arrays so left halves ≤ right halves; BS on the smaller. O(log min(m,n)).",
    "Search 2D matrix I & II": "I: treat as flattened sorted array; II: staircase search from a corner.",
    "Row with max 1s & peak in 2D": "Per-row lower bound; 2D peak via BS on columns.",
    # Step 5 Strings
    "Reverse words & largest odd number": "Tokenize/trim and reverse order; scan from the right for the largest odd suffix.",
    "Longest common prefix & isomorphic": "Vertical scan for LCP; two-way char mapping for isomorphism.",
    "Anagram & sort characters by frequency": "Compare frequency maps; bucket/heap sort chars by count.",
    "Rotated string check": "s is a rotation of t iff s is a substring of t+t.",
    # Step 6 Linked List
    "Build, insert, delete & length": "Node struct with next; head handling, insert/delete at position, traverse for length.",
    "Insert, delete & reverse": "Doubly linked list with prev/next — careful pointer rewiring on both sides.",
    "Middle node (tortoise–hare)": "Slow/fast pointers: fast moves 2x, slow lands on the middle.",
    "Reverse LL (iterative & recursive)": "Rewire next pointers with prev/curr/next; recursion reverses from the tail back.",
    "Detect & find start of loop": "Floyd's cycle detection; reset one pointer to head to find the loop's entry.",
    "Palindrome & odd-even LL": "Reverse second half and compare; regroup nodes by index parity.",
    "Remove Nth from end & delete middle": "Two pointers N apart; slow/fast to reach the middle for deletion.",
    "Sort LL & sort 0s/1s/2s": "Merge sort on a list; dummy-node bucketing for the 0/1/2 case.",
    "Intersection, add 1, add two numbers": "Length-diff or two-pointer meet; digit addition with carry on reversed lists.",
    "Reverse in K-groups": "Reverse each block of K nodes, stitch blocks together; leftover tail stays as-is.",
    "Rotate & flatten LL": "Rotate by k%len with a circular link; flatten a multilevel/child list via merge.",
    "Clone LL with random pointer": "Interleave copies then split, or use a hashmap old→new. O(n).",
    # Step 7 Recursion
    "Pick / not-pick pattern": "The universal subsequence template: at each index, include or exclude.",
    "Subsequence sum K & count": "Pick/not-pick carrying a running sum; count or print qualifying subsequences.",
    "Combination sum I & II": "I allows reuse (stay on index); II forbids reuse and skips duplicates.",
    "Subsets I & II": "Power set via pick/not-pick; sort + skip-duplicates for the with-dups variant.",
    "Palindrome partitioning": "Backtrack cut points, recursing on the remaining suffix when the prefix is a palindrome.",
    "Word search & rat in a maze": "DFS on a grid with visited marking and backtracking on dead ends.",
    "N-Queens & M-coloring": "Place/colour with constraint checks; backtrack on conflict. Classic CSP backtracking.",
    "Sudoku solver": "Try 1–9 in each empty cell with row/col/box validity, backtracking on failure.",
    # Step 8 Bit
    "Bitwise operators & swap numbers": "AND/OR/XOR/NOT/shifts; XOR swap without a temp variable.",
    "Check/set/clear/toggle ith bit": "Mask with (1<<i) and combine with &, |, ^, and ~ to manipulate single bits.",
    "Count set bits & power of 2": "Brian Kernighan's n&(n-1) drops the lowest set bit; power of 2 ⟺ one set bit.",
    "Single number I, II & III": "XOR cancels pairs (I); bit-count mod 3 (II); split by a differing bit (III).",
    "XOR 1..N & divide without operators": "Closed-form XOR by n%4; division via repeated doubling/subtraction with bits.",
    "Sieve of Eratosthenes & prime factors": "Mark multiples to find all primes ≤ n; smallest-prime-factor sieve for fast factorization.",
    # Step 9 Stacks & Queues
    "Stack & queue via array/LL": "LIFO/FIFO implementations with array indices or linked nodes.",
    "Stack using queue & vice versa": "Simulate one ADT with the other by shuffling elements on push or pop.",
    "Infix → postfix/prefix conversions": "Use an operator stack honoring precedence/associativity to reorder expressions.",
    "Next greater element I & II": "Monotonic decreasing stack scanning right-to-left; II wraps around circularly.",
    "Trapping rainwater & sum of subarray mins": "Two-pointer/monotonic-stack water trapping; contribution technique for subarray minimums.",
    "Largest rectangle in histogram": "Monotonic stack finds the nearest smaller bars on both sides for each bar's width.",
    "Asteroid collision & remove K digits": "Stack resolves collisions/removals greedily while scanning.",
    "Sliding window maximum": "Monotonic deque holds indices of useful candidates; front is the window max. O(n).",
    "Min stack, LRU & LFU cache": "Auxiliary state for O(1) min; hashmap + doubly linked list for LRU/LFU eviction.",
    # Step 10 Sliding window
    "Longest substring without repeat": "Expand right, shrink left past duplicates using a last-seen map. O(n).",
    "Max consecutive ones III & fruit baskets": "Variable window allowing at most K flips / 2 distinct types.",
    "Longest repeating char replacement": "Window valid while (len - maxFreq) ≤ K; track max frequency.",
    "Binary subarray / nice subarrays with sum": "atMost(K) - atMost(K-1) counts exactly-K windows.",
    "Longest substring with K distinct": "Shrink the window when distinct-count exceeds K, using a frequency map.",
    "Minimum window substring": "Expand to cover all needed chars, then contract to the smallest valid window.",
    # Step 11 Heaps
    "Min/max heap, heapify & priority queue": "Complete binary tree in an array; sift-up/down; heapify in O(n).",
    "Kth largest / smallest element": "Maintain a size-K heap of opposite polarity for streaming Kth order statistics.",
    "Merge K sorted lists/arrays": "Min-heap of K heads, repeatedly pop the smallest. O(N log K).",
    "Task scheduler & hands of straights": "Greedy with counts/heap honoring cooldown or consecutive grouping.",
    "Median from data stream": "Two heaps (max-heap low half, min-heap high half) balanced for O(1) median.",
    "Top K frequent elements": "Count then bucket-sort or size-K heap by frequency.",
    # Step 12 Greedy
    "Assign cookies & lemonade change": "Sort and match greedily; track change denominations in order.",
    "Fractional knapsack & min coins": "Sort by value/weight ratio; take largest coins first (canonical systems).",
    "N meetings & job sequencing": "Sort by finish time / by profit with a deadline slot DSU.",
    "Jump game I & II": "Track farthest reachable index; BFS-like level expansion for min jumps.",
    "Min platforms & candy": "Sort arrivals/departures; two-pass left-right for the candy constraint.",
    "Insert/merge & non-overlapping intervals": "Sort by start/end; greedily merge or drop overlapping intervals.",
    # Step 13 Binary Trees
    "Pre / In / Post order (recursive)": "Root-Left-Right, Left-Root-Right, Left-Right-Root — the three DFS orders.",
    "Iterative traversals & level order": "Stack-based DFS and queue-based BFS without recursion.",
    "Morris traversal": "Thread the tree with temporary links for O(1)-space inorder/preorder.",
    "Height, balanced & diameter": "Post-order returns subtree heights; combine for balance and longest path.",
    "Max path sum & same tree": "Post-order gain (drop negatives); structural equality by parallel traversal.",
    "Zigzag, boundary & vertical order": "Level order with direction flip; boundary trace; column-indexed BFS map.",
    "Top/bottom/left/right views": "Vertical/horizontal BFS keeping the first or last node per line.",
    "LCA & max width": "Bottom-up LCA returning the meeting node; index-based width via positions.",
    "Nodes at distance K & burn tree": "Build parent pointers, then BFS outward from the target node.",
    "Construct from inorder + pre/post": "Inorder gives the split; pre/post gives the root each recursion.",
    "Serialize & deserialize": "Encode the tree (with nulls) to a string and rebuild it exactly.",
    # Step 14 BST
    "Search, min/max, ceil & floor": "Exploit the BST ordering to move left/right; leftmost=min, rightmost=max.",
    "Insert & delete a node": "Insert at a leaf; deletion handles 0/1/2 children (successor replacement).",
    "Kth smallest/largest & validate BST": "Inorder yields sorted order; validate with (low, high) bounds.",
    "LCA & construct from preorder": "Walk down splitting on value; build with an upper-bound limit.",
    "Inorder successor & BST iterator": "Next-greater via right subtree or ancestors; controlled inorder with a stack.",
    "Two sum, recover & largest BST": "BST iterator two-pointer; fix two swapped nodes; post-order largest-BST check.",
    # Step 15 Graphs
    "Representation & connected components": "Adjacency list/matrix; count components via repeated DFS/BFS.",
    "BFS & DFS traversal": "Queue-based level expansion and stack/recursion deep traversal — graph fundamentals.",
    "Number of provinces & islands": "Count connected components on a matrix via flood fill.",
    "Rotten oranges & flood fill": "Multi-source BFS spreading in time steps; DFS region recolor.",
    "Detect cycle (undirected & directed)": "Parent-aware BFS/DFS undirected; recursion-stack or Kahn's for directed.",
    "Bipartite & surrounded regions": "2-colour BFS/DFS; border-connected DFS to protect regions.",
    "Word ladder I & II": "BFS over one-letter transformations; track paths for all shortest ladders.",
    "Topological sort (BFS/DFS)": "Kahn's indegree queue or DFS finish-time stack — DAGs only.",
    "Course schedule I & II": "Cycle detection + topo order over prerequisite edges.",
    "Alien dictionary & safe states": "Derive edges from word order then topo sort; reverse-graph topo for safe nodes.",
    "Shortest path in DAG & undirected": "Topo-order relaxation for DAGs; plain BFS for unit-weight graphs.",
    "Dijkstra's algorithm": "Min-heap greedily settles nearest nodes. Non-negative weights, O(E log V).",
    "Bellman-Ford & Floyd-Warshall": "V-1 edge relaxations (detects negative cycles); all-pairs DP in O(V^3).",
    "Cheapest flights within K stops": "Bellman-Ford / BFS bounded by at most K relaxation layers.",
    "Disjoint set (union by rank/size)": "Union-Find with path compression — near-O(1) connectivity queries.",
    "Kruskal's & Prim's MST": "Sort edges + DSU (Kruskal) or grow from a node with a heap (Prim).",
    "Accounts merge & making large island": "DSU to merge groups; flip one 0 and union neighbouring islands.",
    "Bridges & articulation points (Tarjan)": "DFS discovery/low-link times identify critical edges and cut vertices.",
    "Kosaraju's SCC": "Two DFS passes (order, then transpose) to extract strongly connected components.",
    # Step 16 DP
    "Intro, climbing stairs & frog jump": "Recurrence → memo → tabulation. Ways to climb / min cost to jump.",
    "Max non-adjacent sum & house robber": "Pick/skip with a no-two-adjacent constraint; circular variant.",
    "Unique paths I & II": "Grid DP counting paths; obstacles zero out blocked cells.",
    "Min path sum, triangle & falling path": "Grid DP minimizing accumulated cost over allowed moves.",
    "Cherry pickup": "Two traversals at once — 3D/4D DP over both paths.",
    "Subset sum & partition equal subset": "Boolean knapsack DP over achievable sums.",
    "0/1 knapsack & min coins": "Take/skip with capacity; unbounded coin DP for fewest coins.",
    "Target sum & coin change II": "Count ways via +/- assignment / coin combinations.",
    "Unbounded knapsack & rod cutting": "Reuse items; rod cutting is unbounded knapsack in disguise.",
    "LCS & longest common substring": "2D DP on two strings; contiguous reset for substring.",
    "Longest palindromic subsequence": "LCS of the string with its reverse.",
    "Edit distance & wildcard matching": "Insert/delete/replace DP; pattern matching with * and ?.",
    "Distinct subsequences & SCS": "Count subsequence occurrences; shortest common supersequence from LCS.",
    "Buy/sell stock I–VI": "State machine DP over holding/cooldown/transaction-count and fees.",
    "Longest increasing subsequence + print": "O(n^2) DP with parent pointers to reconstruct the sequence.",
    "LIS (binary search) & longest string chain": "Patience sorting O(n log n); LIS-style chain over words.",
    "Longest bitonic & number of LIS": "Combine LIS from both ends; count DP alongside length DP.",
    "Matrix chain multiplication": "Partition DP choosing the split point minimizing multiplications.",
    "Min cost to cut stick & burst balloons": "Interval DP over the order of cuts/bursts.",
    "Palindrome partitioning II": "Front partition DP minimizing cuts using a palindrome table.",
    "Count square submatrices & max rectangle": "DP on min of neighbours; histogram method for max rectangle of 1s.",
    # Step 17 Tries
    "Implement Trie I & II": "Prefix tree with children + end flags; II adds insert/count/erase word counts.",
    "Longest word with all prefixes": "Trie + DFS keeping words whose every prefix is also a word.",
    "Count distinct substrings": "Insert all suffixes into a trie; count created nodes.",
    "Maximum XOR of two numbers / with query": "Bitwise trie; greedily choose the opposite bit to maximize XOR.",
    # Step 18 Strings advanced
    "Z-function": "Z[i] = length of the longest prefix starting at i. Linear pattern matching.",
    "KMP / LPS array": "Longest proper prefix-suffix table enables O(n+m) matching without backtracking.",
    "Rabin-Karp": "Rolling hash compares substrings in O(1) amortized; verify on hash hits.",
    "Longest palindromic substring": "Expand around each center O(n^2), or Manacher's O(n).",
    "Shortest palindrome & longest happy prefix": "KMP/Z on s+#+reverse(s) to find the longest palindromic prefix.",
}

# title -> list of (subtopic title, description, tier)  -> become child nodes (double-click)
SUBTOPICS = {
    "BS theory, lower/upper bound": [
        ("Iterative binary search", "Maintain [low, high], compare mid, halve. The base template.", "easy"),
        ("Lower bound", "First index with value ≥ target.", "easy"),
        ("Upper bound", "First index with value > target.", "easy"),
        ("Overflow-safe mid", "Use low + (high-low)/2 to avoid integer overflow.", "easy"),
    ],
    "Kadane's max subarray sum": [
        ("Running sum reset", "Add current; if sum < 0, reset to 0.", "medium"),
        ("Track best so far", "Keep a separate max across all positions.", "medium"),
        ("Print the subarray", "Record start/end indices on each reset/update.", "medium"),
    ],
    "Dijkstra's algorithm": [
        ("Min-heap frontier", "Always expand the currently nearest unsettled node.", "medium"),
        ("Distance relaxation", "If dist[u]+w < dist[v], update and push v.", "medium"),
        ("Why no negatives", "Settled nodes are final — negative edges break that invariant.", "hard"),
    ],
    "Reverse LL (iterative & recursive)": [
        ("Iterative (prev/curr/next)", "Rewire each node's next to prev while walking forward.", "medium"),
        ("Recursive", "Recurse to the tail, then flip pointers on the way back.", "medium"),
    ],
    "0/1 knapsack & min coins": [
        ("Take / not-take recurrence", "Best of skipping the item vs taking it (if it fits).", "medium"),
        ("Tabulation grid", "dp[i][w] over items × capacity.", "medium"),
        ("Space optimization", "Collapse to a single rolling 1D array.", "medium"),
    ],
    "Topological sort (BFS/DFS)": [
        ("Kahn's algorithm (BFS)", "Repeatedly remove zero-indegree nodes.", "medium"),
        ("DFS finish-time stack", "Push nodes after exploring all descendants; reverse.", "medium"),
        ("Cycle ⇒ no ordering", "If not all nodes emitted, a cycle exists.", "medium"),
    ],
}


async def main():
    async with engine.begin() as conn:
        # Map title -> node id for this roadmap's TOP-LEVEL nodes
        rows = (await conn.execute(
            text("SELECT id, title FROM roadmap_nodes WHERE roadmap_id = :rid AND parent_id IS NULL"),
            {"rid": ROADMAP_ID},
        )).all()
        id_by_title = {title: str(nid) for nid, title in rows}

        # 1) descriptions
        updated = 0
        for title, desc in DESCRIPTIONS.items():
            if title in id_by_title:
                await conn.execute(
                    text("UPDATE roadmap_nodes SET description = :d WHERE id = :id"),
                    {"d": desc, "id": id_by_title[title]},
                )
                updated += 1

        # 2) subtopics (rebuild children idempotently)
        child_count = 0
        for parent_title, kids in SUBTOPICS.items():
            pid = id_by_title.get(parent_title)
            if not pid:
                continue
            await conn.execute(
                text("DELETE FROM roadmap_nodes WHERE parent_id = :pid"), {"pid": pid}
            )
            parent = (await conn.execute(
                text("SELECT phase, section, order_index FROM roadmap_nodes WHERE id = :id"),
                {"id": pid},
            )).first()
            for j, (ctitle, cdesc, ctier) in enumerate(kids):
                await conn.execute(
                    text("INSERT INTO roadmap_nodes "
                         "(id, roadmap_id, phase, section, title, tier, order_index, description, parent_id) "
                         "VALUES (:id, :rid, :phase, :section, :title, :tier, :idx, :desc, :pid)"),
                    {
                        "id": str(uuid.uuid4()),
                        "rid": ROADMAP_ID,
                        "phase": parent.phase,
                        "section": parent.section,
                        "title": ctitle,
                        "tier": ctier,
                        "idx": parent.order_index * 100 + j,
                        "desc": cdesc,
                        "pid": pid,
                    },
                )
                child_count += 1

    print(f"Descriptions set: {updated}/{len(DESCRIPTIONS)}  |  Subtopic nodes: {child_count}")


if __name__ == "__main__":
    asyncio.run(main())
