"""
Seed script: Striver's A2Z DSA Sheet as a RetainHQ roadmap.
Idempotent — deletes and recreates the DSA roadmap each run.
Run: ./.venv/Scripts/python.exe seed_striver_a2z.py
"""
import asyncio
import uuid
from sqlalchemy import text
from app.core.database import engine

ROADMAP_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
TITLE = "DSA — Striver's A2Z Sheet"
DESCRIPTION = "Complete A-to-Z DSA path: basics through advanced graphs, DP, and tries. Comprehensive placement & interview prep."

# (phase/step, section, title, tier)  tier in: easy | medium | hard
NODES = [
    # ---------------- Step 1: Basics ----------------
    ("Step 1: Basics", "Fundamentals", "Data types, I/O & operators", "easy"),
    ("Step 1: Basics", "Fundamentals", "Conditionals & loops", "easy"),
    ("Step 1: Basics", "Fundamentals", "Functions & scope", "easy"),
    ("Step 1: Basics", "Patterns", "Star & number patterns", "easy"),
    ("Step 1: Basics", "Maths", "Count digits / reverse / palindrome number", "easy"),
    ("Step 1: Basics", "Maths", "GCD/HCF & Euclidean algorithm", "easy"),
    ("Step 1: Basics", "Maths", "Armstrong, divisors, prime check", "easy"),
    ("Step 1: Basics", "Recursion", "Print N times / 1..N / N..1", "easy"),
    ("Step 1: Basics", "Recursion", "Sum of N, factorial, reverse array", "easy"),
    ("Step 1: Basics", "Recursion", "String palindrome & Fibonacci", "easy"),
    ("Step 1: Basics", "Hashing", "Hashing theory (number & character)", "easy"),
    ("Step 1: Basics", "Hashing", "Count frequencies of elements", "easy"),

    # ---------------- Step 2: Sorting ----------------
    ("Step 2: Sorting", "Basic Sorts", "Selection sort", "easy"),
    ("Step 2: Sorting", "Basic Sorts", "Bubble sort", "easy"),
    ("Step 2: Sorting", "Basic Sorts", "Insertion sort", "easy"),
    ("Step 2: Sorting", "Advanced Sorts", "Merge sort", "medium"),
    ("Step 2: Sorting", "Advanced Sorts", "Quick sort", "medium"),
    ("Step 2: Sorting", "Advanced Sorts", "Recursive bubble & insertion", "easy"),

    # ---------------- Step 3: Arrays ----------------
    ("Step 3: Arrays", "Easy", "Largest & second largest", "easy"),
    ("Step 3: Arrays", "Easy", "Check sorted & remove duplicates", "easy"),
    ("Step 3: Arrays", "Easy", "Left rotate by 1 and by D", "easy"),
    ("Step 3: Arrays", "Easy", "Move zeros to end", "easy"),
    ("Step 3: Arrays", "Easy", "Union, intersection & missing number", "easy"),
    ("Step 3: Arrays", "Easy", "Max consecutive ones & single number", "easy"),
    ("Step 3: Arrays", "Easy", "Longest subarray with sum K", "medium"),
    ("Step 3: Arrays", "Medium", "Two Sum & sort 0s/1s/2s", "medium"),
    ("Step 3: Arrays", "Medium", "Majority element (n/2)", "medium"),
    ("Step 3: Arrays", "Medium", "Kadane's max subarray sum", "medium"),
    ("Step 3: Arrays", "Medium", "Best time to buy & sell stock", "medium"),
    ("Step 3: Arrays", "Medium", "Rearrange by sign & next permutation", "medium"),
    ("Step 3: Arrays", "Medium", "Leaders & longest consecutive sequence", "medium"),
    ("Step 3: Arrays", "Medium", "Set matrix zeros, rotate & spiral", "medium"),
    ("Step 3: Arrays", "Hard", "Pascal's triangle", "hard"),
    ("Step 3: Arrays", "Hard", "Majority (n/3), 3-Sum & 4-Sum", "hard"),
    ("Step 3: Arrays", "Hard", "Largest subarray with 0 sum / XOR K", "hard"),
    ("Step 3: Arrays", "Hard", "Merge intervals & merge sorted arrays", "hard"),
    ("Step 3: Arrays", "Hard", "Count inversions & reverse pairs", "hard"),
    ("Step 3: Arrays", "Hard", "Max product subarray", "medium"),

    # ---------------- Step 4: Binary Search ----------------
    ("Step 4: Binary Search", "On 1D Arrays", "BS theory, lower/upper bound", "easy"),
    ("Step 4: Binary Search", "On 1D Arrays", "Search insert, floor & ceil", "easy"),
    ("Step 4: Binary Search", "On 1D Arrays", "First/last occurrence & count", "medium"),
    ("Step 4: Binary Search", "On 1D Arrays", "Search in rotated array I & II", "medium"),
    ("Step 4: Binary Search", "On 1D Arrays", "Min in rotated & single element", "medium"),
    ("Step 4: Binary Search", "On 1D Arrays", "Peak element", "medium"),
    ("Step 4: Binary Search", "On Answers", "Sqrt & Nth root", "medium"),
    ("Step 4: Binary Search", "On Answers", "Koko eating bananas", "medium"),
    ("Step 4: Binary Search", "On Answers", "Min days for bouquets & smallest divisor", "medium"),
    ("Step 4: Binary Search", "On Answers", "Capacity to ship & Kth missing", "medium"),
    ("Step 4: Binary Search", "On Answers", "Aggressive cows & book allocation", "hard"),
    ("Step 4: Binary Search", "On Answers", "Split array / painter's partition", "hard"),
    ("Step 4: Binary Search", "On Answers", "Median of two sorted arrays", "hard"),
    ("Step 4: Binary Search", "On 2D", "Search 2D matrix I & II", "medium"),
    ("Step 4: Binary Search", "On 2D", "Row with max 1s & peak in 2D", "medium"),

    # ---------------- Step 5: Strings ----------------
    ("Step 5: Strings", "Basic", "Reverse words & largest odd number", "easy"),
    ("Step 5: Strings", "Basic", "Longest common prefix & isomorphic", "easy"),
    ("Step 5: Strings", "Basic", "Anagram & sort characters by frequency", "medium"),
    ("Step 5: Strings", "Basic", "Rotated string check", "easy"),

    # ---------------- Step 6: Linked List ----------------
    ("Step 6: Linked List", "Singly LL", "Build, insert, delete & length", "easy"),
    ("Step 6: Linked List", "Doubly LL", "Insert, delete & reverse", "easy"),
    ("Step 6: Linked List", "Medium", "Middle node (tortoise–hare)", "easy"),
    ("Step 6: Linked List", "Medium", "Reverse LL (iterative & recursive)", "medium"),
    ("Step 6: Linked List", "Medium", "Detect & find start of loop", "medium"),
    ("Step 6: Linked List", "Medium", "Palindrome & odd-even LL", "medium"),
    ("Step 6: Linked List", "Medium", "Remove Nth from end & delete middle", "medium"),
    ("Step 6: Linked List", "Medium", "Sort LL & sort 0s/1s/2s", "medium"),
    ("Step 6: Linked List", "Medium", "Intersection, add 1, add two numbers", "medium"),
    ("Step 6: Linked List", "Hard", "Reverse in K-groups", "hard"),
    ("Step 6: Linked List", "Hard", "Rotate & flatten LL", "hard"),
    ("Step 6: Linked List", "Hard", "Clone LL with random pointer", "hard"),

    # ---------------- Step 7: Recursion & Backtracking ----------------
    ("Step 7: Recursion & Backtracking", "Subsequences", "Pick / not-pick pattern", "medium"),
    ("Step 7: Recursion & Backtracking", "Subsequences", "Subsequence sum K & count", "medium"),
    ("Step 7: Recursion & Backtracking", "Subsequences", "Combination sum I & II", "medium"),
    ("Step 7: Recursion & Backtracking", "Subsequences", "Subsets I & II", "medium"),
    ("Step 7: Recursion & Backtracking", "Hard", "Palindrome partitioning", "hard"),
    ("Step 7: Recursion & Backtracking", "Hard", "Word search & rat in a maze", "hard"),
    ("Step 7: Recursion & Backtracking", "Hard", "N-Queens & M-coloring", "hard"),
    ("Step 7: Recursion & Backtracking", "Hard", "Sudoku solver", "hard"),

    # ---------------- Step 8: Bit Manipulation ----------------
    ("Step 8: Bit Manipulation", "Basics", "Bitwise operators & swap numbers", "easy"),
    ("Step 8: Bit Manipulation", "Basics", "Check/set/clear/toggle ith bit", "easy"),
    ("Step 8: Bit Manipulation", "Basics", "Count set bits & power of 2", "easy"),
    ("Step 8: Bit Manipulation", "Problems", "Single number I, II & III", "medium"),
    ("Step 8: Bit Manipulation", "Problems", "XOR 1..N & divide without operators", "medium"),
    ("Step 8: Bit Manipulation", "Problems", "Sieve of Eratosthenes & prime factors", "medium"),

    # ---------------- Step 9: Stacks & Queues ----------------
    ("Step 9: Stacks & Queues", "Learning", "Stack & queue via array/LL", "easy"),
    ("Step 9: Stacks & Queues", "Learning", "Stack using queue & vice versa", "medium"),
    ("Step 9: Stacks & Queues", "Expressions", "Infix → postfix/prefix conversions", "medium"),
    ("Step 9: Stacks & Queues", "Monotonic", "Next greater element I & II", "medium"),
    ("Step 9: Stacks & Queues", "Monotonic", "Trapping rainwater & sum of subarray mins", "hard"),
    ("Step 9: Stacks & Queues", "Monotonic", "Largest rectangle in histogram", "hard"),
    ("Step 9: Stacks & Queues", "Monotonic", "Asteroid collision & remove K digits", "medium"),
    ("Step 9: Stacks & Queues", "Monotonic", "Sliding window maximum", "hard"),
    ("Step 9: Stacks & Queues", "Design", "Min stack, LRU & LFU cache", "hard"),

    # ---------------- Step 10: Sliding Window & Two Pointer ----------------
    ("Step 10: Sliding Window & Two Pointer", "Patterns", "Longest substring without repeat", "medium"),
    ("Step 10: Sliding Window & Two Pointer", "Patterns", "Max consecutive ones III & fruit baskets", "medium"),
    ("Step 10: Sliding Window & Two Pointer", "Patterns", "Longest repeating char replacement", "medium"),
    ("Step 10: Sliding Window & Two Pointer", "Patterns", "Binary subarray / nice subarrays with sum", "medium"),
    ("Step 10: Sliding Window & Two Pointer", "Patterns", "Longest substring with K distinct", "medium"),
    ("Step 10: Sliding Window & Two Pointer", "Hard", "Minimum window substring", "hard"),

    # ---------------- Step 11: Heaps ----------------
    ("Step 11: Heaps", "Learning", "Min/max heap, heapify & priority queue", "medium"),
    ("Step 11: Heaps", "Problems", "Kth largest / smallest element", "medium"),
    ("Step 11: Heaps", "Problems", "Merge K sorted lists/arrays", "hard"),
    ("Step 11: Heaps", "Problems", "Task scheduler & hands of straights", "medium"),
    ("Step 11: Heaps", "Hard", "Median from data stream", "hard"),
    ("Step 11: Heaps", "Hard", "Top K frequent elements", "medium"),

    # ---------------- Step 12: Greedy ----------------
    ("Step 12: Greedy", "Easy", "Assign cookies & lemonade change", "easy"),
    ("Step 12: Greedy", "Easy", "Fractional knapsack & min coins", "medium"),
    ("Step 12: Greedy", "Medium/Hard", "N meetings & job sequencing", "medium"),
    ("Step 12: Greedy", "Medium/Hard", "Jump game I & II", "medium"),
    ("Step 12: Greedy", "Medium/Hard", "Min platforms & candy", "hard"),
    ("Step 12: Greedy", "Medium/Hard", "Insert/merge & non-overlapping intervals", "medium"),

    # ---------------- Step 13: Binary Trees ----------------
    ("Step 13: Binary Trees", "Traversals", "Pre / In / Post order (recursive)", "easy"),
    ("Step 13: Binary Trees", "Traversals", "Iterative traversals & level order", "medium"),
    ("Step 13: Binary Trees", "Traversals", "Morris traversal", "hard"),
    ("Step 13: Binary Trees", "Medium", "Height, balanced & diameter", "medium"),
    ("Step 13: Binary Trees", "Medium", "Max path sum & same tree", "hard"),
    ("Step 13: Binary Trees", "Medium", "Zigzag, boundary & vertical order", "medium"),
    ("Step 13: Binary Trees", "Medium", "Top/bottom/left/right views", "medium"),
    ("Step 13: Binary Trees", "Hard", "LCA & max width", "medium"),
    ("Step 13: Binary Trees", "Hard", "Nodes at distance K & burn tree", "hard"),
    ("Step 13: Binary Trees", "Hard", "Construct from inorder + pre/post", "hard"),
    ("Step 13: Binary Trees", "Hard", "Serialize & deserialize", "hard"),

    # ---------------- Step 14: Binary Search Trees ----------------
    ("Step 14: Binary Search Trees", "Basics", "Search, min/max, ceil & floor", "easy"),
    ("Step 14: Binary Search Trees", "Basics", "Insert & delete a node", "medium"),
    ("Step 14: Binary Search Trees", "Problems", "Kth smallest/largest & validate BST", "medium"),
    ("Step 14: Binary Search Trees", "Problems", "LCA & construct from preorder", "medium"),
    ("Step 14: Binary Search Trees", "Problems", "Inorder successor & BST iterator", "medium"),
    ("Step 14: Binary Search Trees", "Hard", "Two sum, recover & largest BST", "hard"),

    # ---------------- Step 15: Graphs ----------------
    ("Step 15: Graphs", "Basics", "Representation & connected components", "easy"),
    ("Step 15: Graphs", "Basics", "BFS & DFS traversal", "medium"),
    ("Step 15: Graphs", "Problems", "Number of provinces & islands", "medium"),
    ("Step 15: Graphs", "Problems", "Rotten oranges & flood fill", "medium"),
    ("Step 15: Graphs", "Problems", "Detect cycle (undirected & directed)", "medium"),
    ("Step 15: Graphs", "Problems", "Bipartite & surrounded regions", "medium"),
    ("Step 15: Graphs", "Problems", "Word ladder I & II", "hard"),
    ("Step 15: Graphs", "Topo Sort", "Topological sort (BFS/DFS)", "medium"),
    ("Step 15: Graphs", "Topo Sort", "Course schedule I & II", "medium"),
    ("Step 15: Graphs", "Topo Sort", "Alien dictionary & safe states", "hard"),
    ("Step 15: Graphs", "Shortest Path", "Shortest path in DAG & undirected", "medium"),
    ("Step 15: Graphs", "Shortest Path", "Dijkstra's algorithm", "medium"),
    ("Step 15: Graphs", "Shortest Path", "Bellman-Ford & Floyd-Warshall", "hard"),
    ("Step 15: Graphs", "Shortest Path", "Cheapest flights within K stops", "medium"),
    ("Step 15: Graphs", "MST & DSU", "Disjoint set (union by rank/size)", "medium"),
    ("Step 15: Graphs", "MST & DSU", "Kruskal's & Prim's MST", "hard"),
    ("Step 15: Graphs", "MST & DSU", "Accounts merge & making large island", "hard"),
    ("Step 15: Graphs", "Advanced", "Bridges & articulation points (Tarjan)", "hard"),
    ("Step 15: Graphs", "Advanced", "Kosaraju's SCC", "hard"),

    # ---------------- Step 16: Dynamic Programming ----------------
    ("Step 16: Dynamic Programming", "1D", "Intro, climbing stairs & frog jump", "easy"),
    ("Step 16: Dynamic Programming", "1D", "Max non-adjacent sum & house robber", "medium"),
    ("Step 16: Dynamic Programming", "Grids", "Unique paths I & II", "medium"),
    ("Step 16: Dynamic Programming", "Grids", "Min path sum, triangle & falling path", "medium"),
    ("Step 16: Dynamic Programming", "Grids", "Cherry pickup", "hard"),
    ("Step 16: Dynamic Programming", "Subsequences", "Subset sum & partition equal subset", "medium"),
    ("Step 16: Dynamic Programming", "Subsequences", "0/1 knapsack & min coins", "medium"),
    ("Step 16: Dynamic Programming", "Subsequences", "Target sum & coin change II", "medium"),
    ("Step 16: Dynamic Programming", "Subsequences", "Unbounded knapsack & rod cutting", "medium"),
    ("Step 16: Dynamic Programming", "Strings", "LCS & longest common substring", "medium"),
    ("Step 16: Dynamic Programming", "Strings", "Longest palindromic subsequence", "medium"),
    ("Step 16: Dynamic Programming", "Strings", "Edit distance & wildcard matching", "hard"),
    ("Step 16: Dynamic Programming", "Strings", "Distinct subsequences & SCS", "hard"),
    ("Step 16: Dynamic Programming", "Stocks", "Buy/sell stock I–VI", "hard"),
    ("Step 16: Dynamic Programming", "LIS", "Longest increasing subsequence + print", "medium"),
    ("Step 16: Dynamic Programming", "LIS", "LIS (binary search) & longest string chain", "hard"),
    ("Step 16: Dynamic Programming", "LIS", "Longest bitonic & number of LIS", "hard"),
    ("Step 16: Dynamic Programming", "Partition DP", "Matrix chain multiplication", "hard"),
    ("Step 16: Dynamic Programming", "Partition DP", "Min cost to cut stick & burst balloons", "hard"),
    ("Step 16: Dynamic Programming", "Partition DP", "Palindrome partitioning II", "hard"),
    ("Step 16: Dynamic Programming", "Squares", "Count square submatrices & max rectangle", "hard"),

    # ---------------- Step 17: Tries ----------------
    ("Step 17: Tries", "Implementation", "Implement Trie I & II", "medium"),
    ("Step 17: Tries", "Problems", "Longest word with all prefixes", "medium"),
    ("Step 17: Tries", "Problems", "Count distinct substrings", "hard"),
    ("Step 17: Tries", "Problems", "Maximum XOR of two numbers / with query", "hard"),

    # ---------------- Step 18: Strings (Advanced) ----------------
    ("Step 18: Strings (Advanced)", "Pattern Matching", "Z-function", "hard"),
    ("Step 18: Strings (Advanced)", "Pattern Matching", "KMP / LPS array", "hard"),
    ("Step 18: Strings (Advanced)", "Pattern Matching", "Rabin-Karp", "hard"),
    ("Step 18: Strings (Advanced)", "Problems", "Longest palindromic substring", "medium"),
    ("Step 18: Strings (Advanced)", "Problems", "Shortest palindrome & longest happy prefix", "hard"),
]


async def main():
    async with engine.begin() as conn:
        # Idempotent: wipe existing DSA roadmap + its nodes (progress cascades via FK)
        await conn.execute(
            text("DELETE FROM roadmap_nodes WHERE roadmap_id = :rid"), {"rid": str(ROADMAP_ID)}
        )
        await conn.execute(
            text("DELETE FROM roadmaps WHERE id = :rid"), {"rid": str(ROADMAP_ID)}
        )

        await conn.execute(
            text("INSERT INTO roadmaps (id, title, description, created_at) "
                 "VALUES (:id, :title, :desc, now())"),
            {"id": str(ROADMAP_ID), "title": TITLE, "desc": DESCRIPTION},
        )

        for i, (phase, section, title, tier) in enumerate(NODES):
            await conn.execute(
                text("INSERT INTO roadmap_nodes "
                     "(id, roadmap_id, phase, section, title, tier, order_index) "
                     "VALUES (:id, :rid, :phase, :section, :title, :tier, :idx)"),
                {
                    "id": str(uuid.uuid4()),
                    "rid": str(ROADMAP_ID),
                    "phase": phase,
                    "section": section,
                    "title": title,
                    "tier": tier,
                    "idx": i,
                },
            )

    print(f"Seeded '{TITLE}' with {len(NODES)} nodes.")


if __name__ == "__main__":
    asyncio.run(main())
