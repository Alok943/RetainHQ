"""
Seed script: DSA — Blind 75 / Top Patterns roadmap for RetainHQ.
Pattern-first (not topic-first) — ideal for "I have 4 weeks" interview prep.
Idempotent — deletes and recreates the roadmap each run.
Run: ./.venv/Scripts/python.exe seed_blind75.py
"""
import asyncio
import uuid
from sqlalchemy import text
from app.core.database import engine

ROADMAP_ID = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
TITLE = "DSA — Blind 75 / Top Patterns"
DESCRIPTION = "Pattern-first interview prep: master the 15 core patterns behind every Blind 75 / NeetCode problem. Best for 4-week crunch before interviews."

# (phase, section, title, tier)
NODES = [
    # ---------------- Pattern 1: Arrays & Hashing ----------------
    ("Pattern 1: Arrays & Hashing", "Core Pattern", "HashMap / frequency count pattern", "easy"),
    ("Pattern 1: Arrays & Hashing", "Problems", "Contains Duplicate", "easy"),
    ("Pattern 1: Arrays & Hashing", "Problems", "Valid Anagram", "easy"),
    ("Pattern 1: Arrays & Hashing", "Problems", "Two Sum", "easy"),
    ("Pattern 1: Arrays & Hashing", "Problems", "Group Anagrams", "medium"),
    ("Pattern 1: Arrays & Hashing", "Problems", "Top K Frequent Elements", "medium"),
    ("Pattern 1: Arrays & Hashing", "Problems", "Product of Array Except Self", "medium"),
    ("Pattern 1: Arrays & Hashing", "Problems", "Longest Consecutive Sequence", "medium"),

    # ---------------- Pattern 2: Two Pointers ----------------
    ("Pattern 2: Two Pointers", "Core Pattern", "Opposite-end & same-direction pointers", "easy"),
    ("Pattern 2: Two Pointers", "Problems", "Valid Palindrome", "easy"),
    ("Pattern 2: Two Pointers", "Problems", "Two Sum II — sorted input", "easy"),
    ("Pattern 2: Two Pointers", "Problems", "3Sum", "medium"),
    ("Pattern 2: Two Pointers", "Problems", "Container With Most Water", "medium"),
    ("Pattern 2: Two Pointers", "Problems", "Trapping Rain Water", "hard"),

    # ---------------- Pattern 3: Sliding Window ----------------
    ("Pattern 3: Sliding Window", "Core Pattern", "Fixed & variable-size window pattern", "easy"),
    ("Pattern 3: Sliding Window", "Problems", "Best Time to Buy & Sell Stock", "easy"),
    ("Pattern 3: Sliding Window", "Problems", "Longest Substring Without Repeating Chars", "medium"),
    ("Pattern 3: Sliding Window", "Problems", "Longest Repeating Character Replacement", "medium"),
    ("Pattern 3: Sliding Window", "Problems", "Minimum Window Substring", "hard"),
    ("Pattern 3: Sliding Window", "Problems", "Sliding Window Maximum", "hard"),

    # ---------------- Pattern 4: Stack ----------------
    ("Pattern 4: Stack", "Core Pattern", "Monotonic stack & parenthesis patterns", "easy"),
    ("Pattern 4: Stack", "Problems", "Valid Parentheses", "easy"),
    ("Pattern 4: Stack", "Problems", "Min Stack", "medium"),
    ("Pattern 4: Stack", "Problems", "Evaluate Reverse Polish Notation", "medium"),
    ("Pattern 4: Stack", "Problems", "Generate Parentheses", "medium"),
    ("Pattern 4: Stack", "Problems", "Daily Temperatures", "medium"),
    ("Pattern 4: Stack", "Problems", "Largest Rectangle in Histogram", "hard"),

    # ---------------- Pattern 5: Binary Search ----------------
    ("Pattern 5: Binary Search", "Core Pattern", "Binary search on sorted array & on answer", "easy"),
    ("Pattern 5: Binary Search", "Problems", "Binary Search (classic)", "easy"),
    ("Pattern 5: Binary Search", "Problems", "Search a 2D Matrix", "medium"),
    ("Pattern 5: Binary Search", "Problems", "Koko Eating Bananas", "medium"),
    ("Pattern 5: Binary Search", "Problems", "Find Minimum in Rotated Sorted Array", "medium"),
    ("Pattern 5: Binary Search", "Problems", "Search in Rotated Sorted Array", "medium"),
    ("Pattern 5: Binary Search", "Problems", "Median of Two Sorted Arrays", "hard"),

    # ---------------- Pattern 6: Linked Lists ----------------
    ("Pattern 6: Linked Lists", "Core Pattern", "Fast/slow pointer (Floyd's cycle)", "easy"),
    ("Pattern 6: Linked Lists", "Problems", "Reverse a Linked List", "easy"),
    ("Pattern 6: Linked Lists", "Problems", "Merge Two Sorted Lists", "easy"),
    ("Pattern 6: Linked Lists", "Problems", "Linked List Cycle", "easy"),
    ("Pattern 6: Linked Lists", "Problems", "Remove Nth Node From End", "medium"),
    ("Pattern 6: Linked Lists", "Problems", "Reorder List", "medium"),
    ("Pattern 6: Linked Lists", "Problems", "Merge K Sorted Lists", "hard"),
    ("Pattern 6: Linked Lists", "Problems", "Reverse Nodes in K-Group", "hard"),

    # ---------------- Pattern 7: Trees ----------------
    ("Pattern 7: Trees", "Core Pattern", "DFS (pre/in/post) & BFS (level order)", "easy"),
    ("Pattern 7: Trees", "Problems", "Invert Binary Tree", "easy"),
    ("Pattern 7: Trees", "Problems", "Maximum Depth of Binary Tree", "easy"),
    ("Pattern 7: Trees", "Problems", "Same Tree & Subtree of Another", "easy"),
    ("Pattern 7: Trees", "Problems", "Lowest Common Ancestor of BST", "medium"),
    ("Pattern 7: Trees", "Problems", "Binary Tree Level Order Traversal", "medium"),
    ("Pattern 7: Trees", "Problems", "Validate Binary Search Tree", "medium"),
    ("Pattern 7: Trees", "Problems", "Kth Smallest Element in BST", "medium"),
    ("Pattern 7: Trees", "Problems", "Construct BT from Preorder + Inorder", "hard"),
    ("Pattern 7: Trees", "Problems", "Binary Tree Max Path Sum", "hard"),
    ("Pattern 7: Trees", "Problems", "Serialize & Deserialize Binary Tree", "hard"),

    # ---------------- Pattern 8: Tries ----------------
    ("Pattern 8: Tries", "Core Pattern", "Prefix tree — insert, search, startsWith", "medium"),
    ("Pattern 8: Tries", "Problems", "Implement Trie", "medium"),
    ("Pattern 8: Tries", "Problems", "Design Add & Search Words Data Structure", "medium"),
    ("Pattern 8: Tries", "Problems", "Word Search II", "hard"),

    # ---------------- Pattern 9: Heap / Priority Queue ----------------
    ("Pattern 9: Heap / Priority Queue", "Core Pattern", "Min-heap, max-heap & K-th element pattern", "medium"),
    ("Pattern 9: Heap / Priority Queue", "Problems", "Kth Largest Element in a Stream", "medium"),
    ("Pattern 9: Heap / Priority Queue", "Problems", "Last Stone Weight", "easy"),
    ("Pattern 9: Heap / Priority Queue", "Problems", "K Closest Points to Origin", "medium"),
    ("Pattern 9: Heap / Priority Queue", "Problems", "Task Scheduler", "medium"),
    ("Pattern 9: Heap / Priority Queue", "Problems", "Find Median from Data Stream", "hard"),

    # ---------------- Pattern 10: Backtracking ----------------
    ("Pattern 10: Backtracking", "Core Pattern", "Choose / explore / unchoose template", "medium"),
    ("Pattern 10: Backtracking", "Problems", "Subsets", "medium"),
    ("Pattern 10: Backtracking", "Problems", "Combination Sum", "medium"),
    ("Pattern 10: Backtracking", "Problems", "Permutations", "medium"),
    ("Pattern 10: Backtracking", "Problems", "Word Search", "medium"),
    ("Pattern 10: Backtracking", "Problems", "N-Queens", "hard"),
    ("Pattern 10: Backtracking", "Problems", "Palindrome Partitioning", "medium"),

    # ---------------- Pattern 11: Graphs ----------------
    ("Pattern 11: Graphs", "Core Pattern", "BFS, DFS & Union-Find templates", "medium"),
    ("Pattern 11: Graphs", "Problems", "Number of Islands", "medium"),
    ("Pattern 11: Graphs", "Problems", "Clone Graph", "medium"),
    ("Pattern 11: Graphs", "Problems", "Pacific Atlantic Water Flow", "medium"),
    ("Pattern 11: Graphs", "Problems", "Course Schedule I & II (topo sort)", "medium"),
    ("Pattern 11: Graphs", "Problems", "Number of Connected Components (Union-Find)", "medium"),
    ("Pattern 11: Graphs", "Problems", "Redundant Connection", "medium"),
    ("Pattern 11: Graphs", "Problems", "Word Ladder", "hard"),

    # ---------------- Pattern 12: 1D Dynamic Programming ----------------
    ("Pattern 12: 1D Dynamic Programming", "Core Pattern", "Top-down memoization & bottom-up tabulation", "medium"),
    ("Pattern 12: 1D Dynamic Programming", "Problems", "Climbing Stairs", "easy"),
    ("Pattern 12: 1D Dynamic Programming", "Problems", "House Robber I & II", "medium"),
    ("Pattern 12: 1D Dynamic Programming", "Problems", "Longest Palindromic Substring", "medium"),
    ("Pattern 12: 1D Dynamic Programming", "Problems", "Palindromic Substrings", "medium"),
    ("Pattern 12: 1D Dynamic Programming", "Problems", "Decode Ways", "medium"),
    ("Pattern 12: 1D Dynamic Programming", "Problems", "Coin Change", "medium"),
    ("Pattern 12: 1D Dynamic Programming", "Problems", "Word Break", "medium"),
    ("Pattern 12: 1D Dynamic Programming", "Problems", "Longest Increasing Subsequence", "medium"),

    # ---------------- Pattern 13: 2D Dynamic Programming ----------------
    ("Pattern 13: 2D Dynamic Programming", "Core Pattern", "Grid DP & string DP templates", "hard"),
    ("Pattern 13: 2D Dynamic Programming", "Problems", "Unique Paths", "medium"),
    ("Pattern 13: 2D Dynamic Programming", "Problems", "Longest Common Subsequence", "medium"),
    ("Pattern 13: 2D Dynamic Programming", "Problems", "Best Time to Buy/Sell Stock with Cooldown", "medium"),
    ("Pattern 13: 2D Dynamic Programming", "Problems", "Coin Change II", "medium"),
    ("Pattern 13: 2D Dynamic Programming", "Problems", "Target Sum", "medium"),
    ("Pattern 13: 2D Dynamic Programming", "Problems", "Edit Distance", "hard"),
    ("Pattern 13: 2D Dynamic Programming", "Problems", "Distinct Subsequences", "hard"),
    ("Pattern 13: 2D Dynamic Programming", "Problems", "Burst Balloons", "hard"),
    ("Pattern 13: 2D Dynamic Programming", "Problems", "Regular Expression Matching", "hard"),

    # ---------------- Pattern 14: Greedy & Intervals ----------------
    ("Pattern 14: Greedy & Intervals", "Core Pattern", "Sort + greedy & interval overlap detection", "medium"),
    ("Pattern 14: Greedy & Intervals", "Problems", "Jump Game I & II", "medium"),
    ("Pattern 14: Greedy & Intervals", "Problems", "Insert Interval", "medium"),
    ("Pattern 14: Greedy & Intervals", "Problems", "Merge Intervals", "medium"),
    ("Pattern 14: Greedy & Intervals", "Problems", "Non-overlapping Intervals", "medium"),
    ("Pattern 14: Greedy & Intervals", "Problems", "Meeting Rooms I & II", "medium"),

    # ---------------- Pattern 15: Bit Manipulation & Math ----------------
    ("Pattern 15: Bit Manipulation & Math", "Core Pattern", "XOR, bit masking & power-of-2 tricks", "medium"),
    ("Pattern 15: Bit Manipulation & Math", "Problems", "Number of 1 Bits & Reverse Bits", "easy"),
    ("Pattern 15: Bit Manipulation & Math", "Problems", "Missing Number (XOR trick)", "easy"),
    ("Pattern 15: Bit Manipulation & Math", "Problems", "Sum of Two Integers (no + operator)", "medium"),
    ("Pattern 15: Bit Manipulation & Math", "Problems", "Counting Bits", "easy"),
    ("Pattern 15: Bit Manipulation & Math", "Problems", "Rotate Image", "medium"),
    ("Pattern 15: Bit Manipulation & Math", "Problems", "Spiral Matrix", "medium"),
    ("Pattern 15: Bit Manipulation & Math", "Problems", "Set Matrix Zeroes", "medium"),
]


async def main():
    async with engine.begin() as conn:
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
