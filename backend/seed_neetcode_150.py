"""
Seed script: NeetCode 150 as a RetainHQ roadmap.

Each node is a single problem. The node's `description` holds the canonical
neetcode.io problem URL so the UI can link straight to it.
  - phase   = NeetCode category (becomes a step in the flowchart spine)
  - section = same category (kept for consistency with the node schema)
  - title   = problem name
  - tier    = difficulty (easy | medium | hard) -> drives the colored dot
  - description = neetcode.io problem link

Idempotent — deletes and recreates the NeetCode roadmap each run.
Run: ./.venv/Scripts/python.exe seed_neetcode_150.py
"""
import asyncio
import uuid
from sqlalchemy import text
from app.core.database import engine

ROADMAP_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")
TITLE = "DSA — NeetCode 150"
DESCRIPTION = "The 150 essential problems (Blind 75 + 75 more) covering every core DSA pattern. Each topic links straight to its neetcode.io problem."

NC = "https://neetcode.io/problems/"

# (category, problem title, difficulty, neetcode.io slug)
PROBLEMS = [
    # ---------------- Arrays & Hashing (9) ----------------
    ("Arrays & Hashing", "Contains Duplicate", "easy", "duplicate-integer"),
    ("Arrays & Hashing", "Valid Anagram", "easy", "is-anagram"),
    ("Arrays & Hashing", "Two Sum", "easy", "two-integer-sum"),
    ("Arrays & Hashing", "Group Anagrams", "medium", "anagram-groups"),
    ("Arrays & Hashing", "Top K Frequent Elements", "medium", "top-k-elements-in-list"),
    ("Arrays & Hashing", "Encode and Decode Strings", "medium", "string-encode-and-decode"),
    ("Arrays & Hashing", "Product of Array Except Self", "medium", "products-of-array-discluding-self"),
    ("Arrays & Hashing", "Valid Sudoku", "medium", "valid-sudoku"),
    ("Arrays & Hashing", "Longest Consecutive Sequence", "medium", "longest-consecutive-sequence"),

    # ---------------- Two Pointers (5) ----------------
    ("Two Pointers", "Valid Palindrome", "easy", "is-palindrome"),
    ("Two Pointers", "Two Sum II - Input Array Is Sorted", "medium", "two-integer-sum-ii"),
    ("Two Pointers", "3Sum", "medium", "three-integer-sum"),
    ("Two Pointers", "Container With Most Water", "medium", "max-water-container"),
    ("Two Pointers", "Trapping Rain Water", "hard", "trapping-rain-water"),

    # ---------------- Sliding Window (6) ----------------
    ("Sliding Window", "Best Time to Buy and Sell Stock", "easy", "buy-and-sell-crypto"),
    ("Sliding Window", "Longest Substring Without Repeating Characters", "medium", "longest-substring-without-duplicates"),
    ("Sliding Window", "Longest Repeating Character Replacement", "medium", "longest-repeating-substring-with-replacement"),
    ("Sliding Window", "Permutation in String", "medium", "permutation-string"),
    ("Sliding Window", "Minimum Window Substring", "hard", "minimum-window-with-characters"),
    ("Sliding Window", "Sliding Window Maximum", "hard", "sliding-window-maximum"),

    # ---------------- Stack (6) ----------------
    ("Stack", "Valid Parentheses", "easy", "validate-parentheses"),
    ("Stack", "Min Stack", "medium", "minimum-stack"),
    ("Stack", "Evaluate Reverse Polish Notation", "medium", "evaluate-reverse-polish-notation"),
    ("Stack", "Generate Parentheses", "medium", "generate-parentheses"),
    ("Stack", "Daily Temperatures", "medium", "daily-temperatures"),
    ("Stack", "Car Fleet", "medium", "car-fleet"),
    ("Stack", "Largest Rectangle in Histogram", "hard", "largest-rectangle-in-histogram"),

    # ---------------- Binary Search (7) ----------------
    ("Binary Search", "Binary Search", "easy", "binary-search"),
    ("Binary Search", "Search a 2D Matrix", "medium", "search-2d-matrix"),
    ("Binary Search", "Koko Eating Bananas", "medium", "eating-bananas"),
    ("Binary Search", "Find Minimum in Rotated Sorted Array", "medium", "find-minimum-in-rotated-sorted-array"),
    ("Binary Search", "Search in Rotated Sorted Array", "medium", "find-target-in-rotated-sorted-array"),
    ("Binary Search", "Time Based Key-Value Store", "medium", "time-based-key-value-store"),
    ("Binary Search", "Median of Two Sorted Arrays", "hard", "median-of-two-sorted-arrays"),

    # ---------------- Linked List (11) ----------------
    ("Linked List", "Reverse Linked List", "easy", "reverse-a-linked-list"),
    ("Linked List", "Merge Two Sorted Lists", "easy", "merge-two-sorted-linked-lists"),
    ("Linked List", "Linked List Cycle", "easy", "linked-list-cycle-detection"),
    ("Linked List", "Reorder List", "medium", "reorder-linked-list"),
    ("Linked List", "Remove Nth Node From End of List", "medium", "remove-node-from-end-of-linked-list"),
    ("Linked List", "Copy List With Random Pointer", "medium", "copy-linked-list-with-random-pointer"),
    ("Linked List", "Add Two Numbers", "medium", "add-two-numbers"),
    ("Linked List", "Find the Duplicate Number", "medium", "find-duplicate-integer"),
    ("Linked List", "LRU Cache", "medium", "lru-cache"),
    ("Linked List", "Merge K Sorted Lists", "hard", "merge-k-sorted-linked-lists"),
    ("Linked List", "Reverse Nodes in K-Group", "hard", "reverse-nodes-in-k-group"),

    # ---------------- Trees (15) ----------------
    ("Trees", "Invert Binary Tree", "easy", "invert-a-binary-tree"),
    ("Trees", "Maximum Depth of Binary Tree", "easy", "depth-of-binary-tree"),
    ("Trees", "Diameter of Binary Tree", "easy", "binary-tree-diameter"),
    ("Trees", "Balanced Binary Tree", "easy", "balanced-binary-tree"),
    ("Trees", "Same Tree", "easy", "same-binary-tree"),
    ("Trees", "Subtree of Another Tree", "easy", "subtree-of-a-binary-tree"),
    ("Trees", "Lowest Common Ancestor of a BST", "medium", "lowest-common-ancestor-in-binary-search-tree"),
    ("Trees", "Binary Tree Level Order Traversal", "medium", "level-order-traversal-of-binary-tree"),
    ("Trees", "Binary Tree Right Side View", "medium", "binary-tree-right-side-view"),
    ("Trees", "Count Good Nodes in Binary Tree", "medium", "count-good-nodes-in-binary-tree"),
    ("Trees", "Validate Binary Search Tree", "medium", "valid-binary-search-tree"),
    ("Trees", "Kth Smallest Element in a BST", "medium", "kth-smallest-integer-in-bst"),
    ("Trees", "Construct Binary Tree from Preorder and Inorder Traversal", "medium", "binary-tree-from-preorder-and-inorder-traversal"),
    ("Trees", "Binary Tree Maximum Path Sum", "hard", "binary-tree-maximum-path-sum"),
    ("Trees", "Serialize and Deserialize Binary Tree", "hard", "serialize-and-deserialize-binary-tree"),

    # ---------------- Heap / Priority Queue (7) ----------------
    ("Heap / Priority Queue", "Kth Largest Element in a Stream", "easy", "kth-largest-integer-in-a-stream"),
    ("Heap / Priority Queue", "Last Stone Weight", "easy", "last-stone-weight"),
    ("Heap / Priority Queue", "K Closest Points to Origin", "medium", "k-closest-points-to-origin"),
    ("Heap / Priority Queue", "Kth Largest Element in an Array", "medium", "kth-largest-element-in-an-array"),
    ("Heap / Priority Queue", "Task Scheduler", "medium", "task-scheduling"),
    ("Heap / Priority Queue", "Design Twitter", "medium", "design-twitter-feed"),
    ("Heap / Priority Queue", "Find Median from Data Stream", "hard", "find-median-in-a-data-stream"),

    # ---------------- Backtracking (9) ----------------
    ("Backtracking", "Subsets", "medium", "subsets"),
    ("Backtracking", "Combination Sum", "medium", "combination-target-sum"),
    ("Backtracking", "Combination Sum II", "medium", "combination-target-sum-ii"),
    ("Backtracking", "Permutations", "medium", "permutations"),
    ("Backtracking", "Subsets II", "medium", "subsets-ii"),
    ("Backtracking", "Word Search", "medium", "search-for-word"),
    ("Backtracking", "Palindrome Partitioning", "medium", "palindrome-partitioning"),
    ("Backtracking", "Letter Combinations of a Phone Number", "medium", "combinations-of-a-phone-number"),
    ("Backtracking", "N-Queens", "hard", "n-queens"),

    # ---------------- Tries (3) ----------------
    ("Tries", "Implement Trie (Prefix Tree)", "medium", "implement-prefix-tree"),
    ("Tries", "Design Add and Search Words Data Structure", "medium", "design-word-search-data-structure"),
    ("Tries", "Word Search II", "hard", "search-for-word-ii"),

    # ---------------- Graphs (13) ----------------
    ("Graphs", "Number of Islands", "medium", "count-number-of-islands"),
    ("Graphs", "Max Area of Island", "medium", "max-area-of-island"),
    ("Graphs", "Clone Graph", "medium", "clone-graph"),
    ("Graphs", "Walls and Gates", "medium", "islands-and-treasure"),
    ("Graphs", "Rotting Oranges", "medium", "rotting-fruit"),
    ("Graphs", "Pacific Atlantic Water Flow", "medium", "pacific-atlantic-water-flow"),
    ("Graphs", "Surrounded Regions", "medium", "surrounded-regions"),
    ("Graphs", "Course Schedule", "medium", "course-schedule"),
    ("Graphs", "Course Schedule II", "medium", "course-schedule-ii"),
    ("Graphs", "Graph Valid Tree", "medium", "valid-tree"),
    ("Graphs", "Number of Connected Components in an Undirected Graph", "medium", "count-connected-components"),
    ("Graphs", "Redundant Connection", "medium", "redundant-connection"),
    ("Graphs", "Word Ladder", "hard", "word-ladder"),

    # ---------------- Advanced Graphs (6) ----------------
    ("Advanced Graphs", "Network Delay Time", "medium", "network-delay-time"),
    ("Advanced Graphs", "Reconstruct Itinerary", "hard", "reconstruct-flight-path"),
    ("Advanced Graphs", "Min Cost to Connect All Points", "medium", "min-cost-to-connect-points"),
    ("Advanced Graphs", "Swim in Rising Water", "hard", "swim-in-rising-water"),
    ("Advanced Graphs", "Alien Dictionary", "hard", "foreign-dictionary"),
    ("Advanced Graphs", "Cheapest Flights Within K Stops", "medium", "cheapest-flight-path"),

    # ---------------- 1-D Dynamic Programming (12) ----------------
    ("1-D Dynamic Programming", "Climbing Stairs", "easy", "climbing-stairs"),
    ("1-D Dynamic Programming", "Min Cost Climbing Stairs", "easy", "min-cost-climbing-stairs"),
    ("1-D Dynamic Programming", "House Robber", "medium", "house-robber"),
    ("1-D Dynamic Programming", "House Robber II", "medium", "house-robber-ii"),
    ("1-D Dynamic Programming", "Longest Palindromic Substring", "medium", "longest-palindromic-substring"),
    ("1-D Dynamic Programming", "Palindromic Substrings", "medium", "palindromic-substrings"),
    ("1-D Dynamic Programming", "Decode Ways", "medium", "decode-ways"),
    ("1-D Dynamic Programming", "Coin Change", "medium", "coin-change"),
    ("1-D Dynamic Programming", "Maximum Product Subarray", "medium", "maximum-product-subarray"),
    ("1-D Dynamic Programming", "Word Break", "medium", "word-break"),
    ("1-D Dynamic Programming", "Longest Increasing Subsequence", "medium", "longest-increasing-subsequence"),
    ("1-D Dynamic Programming", "Partition Equal Subset Sum", "medium", "partition-equal-subset-sum"),

    # ---------------- 2-D Dynamic Programming (11) ----------------
    ("2-D Dynamic Programming", "Unique Paths", "medium", "count-paths"),
    ("2-D Dynamic Programming", "Longest Common Subsequence", "medium", "longest-common-subsequence"),
    ("2-D Dynamic Programming", "Best Time to Buy and Sell Stock With Cooldown", "medium", "buy-and-sell-crypto-with-cooldown"),
    ("2-D Dynamic Programming", "Coin Change II", "medium", "coin-change-ii"),
    ("2-D Dynamic Programming", "Target Sum", "medium", "target-sum"),
    ("2-D Dynamic Programming", "Interleaving String", "medium", "interleaving-string"),
    ("2-D Dynamic Programming", "Longest Increasing Path in a Matrix", "hard", "longest-increasing-path-in-matrix"),
    ("2-D Dynamic Programming", "Distinct Subsequences", "hard", "count-subsequences"),
    ("2-D Dynamic Programming", "Edit Distance", "medium", "edit-distance"),
    ("2-D Dynamic Programming", "Burst Balloons", "hard", "burst-balloons"),
    ("2-D Dynamic Programming", "Regular Expression Matching", "hard", "regular-expression-matching"),

    # ---------------- Greedy (8) ----------------
    ("Greedy", "Maximum Subarray", "medium", "maximum-subarray"),
    ("Greedy", "Jump Game", "medium", "jump-game"),
    ("Greedy", "Jump Game II", "medium", "jump-game-ii"),
    ("Greedy", "Gas Station", "medium", "gas-station"),
    ("Greedy", "Hand of Straights", "medium", "hand-of-straights"),
    ("Greedy", "Merge Triplets to Form Target Triplet", "medium", "merge-triplets-to-form-target"),
    ("Greedy", "Partition Labels", "medium", "partition-labels"),
    ("Greedy", "Valid Parenthesis String", "medium", "valid-parenthesis-string"),

    # ---------------- Intervals (6) ----------------
    ("Intervals", "Insert Interval", "medium", "insert-new-interval"),
    ("Intervals", "Merge Intervals", "medium", "merge-intervals"),
    ("Intervals", "Non-Overlapping Intervals", "medium", "non-overlapping-intervals"),
    ("Intervals", "Meeting Rooms", "easy", "meeting-schedule"),
    ("Intervals", "Meeting Rooms II", "medium", "meeting-schedule-ii"),
    ("Intervals", "Minimum Interval to Include Each Query", "hard", "minimum-interval-including-query"),

    # ---------------- Math & Geometry (8) ----------------
    ("Math & Geometry", "Rotate Image", "medium", "rotate-matrix"),
    ("Math & Geometry", "Spiral Matrix", "medium", "spiral-matrix"),
    ("Math & Geometry", "Set Matrix Zeroes", "medium", "set-zeroes-in-matrix"),
    ("Math & Geometry", "Happy Number", "easy", "non-cyclical-number"),
    ("Math & Geometry", "Plus One", "easy", "plus-one"),
    ("Math & Geometry", "Pow(x, n)", "medium", "pow-x-n"),
    ("Math & Geometry", "Multiply Strings", "medium", "multiply-strings"),
    ("Math & Geometry", "Detect Squares", "medium", "count-squares"),

    # ---------------- Bit Manipulation (7) ----------------
    ("Bit Manipulation", "Single Number", "easy", "single-number"),
    ("Bit Manipulation", "Number of 1 Bits", "easy", "number-of-one-bits"),
    ("Bit Manipulation", "Counting Bits", "easy", "counting-bits"),
    ("Bit Manipulation", "Reverse Bits", "easy", "reverse-bits"),
    ("Bit Manipulation", "Missing Number", "easy", "missing-number"),
    ("Bit Manipulation", "Sum of Two Integers", "medium", "sum-of-two-integers"),
    ("Bit Manipulation", "Reverse Integer", "medium", "reverse-integer"),
]


async def main():
    async with engine.begin() as conn:
        # Idempotent: wipe existing NeetCode roadmap + its nodes (progress cascades via FK)
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

        for i, (category, title, tier, slug) in enumerate(PROBLEMS):
            await conn.execute(
                text("INSERT INTO roadmap_nodes "
                     "(id, roadmap_id, phase, section, title, tier, order_index, description) "
                     "VALUES (:id, :rid, :phase, :section, :title, :tier, :idx, :desc)"),
                {
                    "id": str(uuid.uuid4()),
                    "rid": str(ROADMAP_ID),
                    "phase": category,
                    "section": category,
                    "title": title,
                    "tier": tier,
                    "idx": i,
                    "desc": f"{NC}{slug}",
                },
            )

    print(f"Seeded '{TITLE}' with {len(PROBLEMS)} problems.")


if __name__ == "__main__":
    asyncio.run(main())
