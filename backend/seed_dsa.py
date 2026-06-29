"""
Seed script: DSA — Algorithms Visualized roadmap.

The "where algorithms finally click" track — distinct from the Striver/NeetCode/Blind-75
PROBLEM lists. Teaches computational THINKING beginner -> interview-ready: mentally simulate
recursion, pointers, state and invariants by watching each algorithm execute step-by-step
(execution-trace visualizer), predict-before-reveal, then practice on LeetCode.

Beginner on-ramp ordering: Foundations + Complexity + Arrays first; Hashing/Strings early (they
gate most interview problems); recursion only AFTER iteration is solid; recursive algorithms
(merge/quick sort, trees, heaps, DP) after recursion. Ends with an Algorithm Design Patterns
capstone (pattern RECOGNITION across everything learned).

NOTE on lesson kind (mix deliberately): most nodes are `dsa`-kind execution-trace visualizations
(Merge Sort, BFS, Dijkstra...), but the meta/conceptual nodes (What is an algorithm?, Big-O,
Amortized analysis, Recursive tree thinking, Why greedy works/fails, the DP-thinking nodes,
Algorithm Design Patterns) are CONCEPTUAL lessons (diagram + explanation, the theory/engineering
kinds). Don't force a trace onto them. See docs/dsa-architecture.md.

Every lesson must answer the FIVE questions: (1) why does this exist? (2) how do I mentally
simulate it? (3) what invariant / repeated decision makes it work? (4) where is it used in real
systems? (5) how do I recognize when to apply it? Enrich via deep research BEFORE authoring.

V2 (deferred — don't fit "algorithms finally click" yet): AVL / Red-Black trees, Segment /
Fenwick trees, Tries, Suffix arrays/automata, Heavy-Light decomposition.

Idempotent (delete + recreate). Run: ./.venv/Scripts/python.exe seed_dsa.py
"""
import asyncio
import uuid
from sqlalchemy import text
from app.core.database import engine

ROADMAP_ID = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
SLUG = "dsa"  # content folder key + URL id; content/roadmaps/dsa/
TITLE = "DSA — Algorithms Visualized"
DESCRIPTION = (
    "Computational thinking, made visual — beginner to interview-ready. Mentally simulate "
    "recursion, pointers, state and invariants; watch every algorithm execute step by step, "
    "predict before the reveal, learn why it exists and when to reach for it, then drill the "
    "pattern on LeetCode. Not another problem list: the place where algorithms click."
)

# (phase, section, title, tier, description)
NODES = [
    # ---------------- Foundations ----------------
    ("Foundations", "Thinking", "What is an algorithm?", "easy", "Step-by-step instructions; correctness and efficiency as the two goals."),
    ("Foundations", "Thinking", "Tracing state & invariants", "easy", "Mentally simulate variables changing; spot what stays true — the core skill."),
    ("Foundations", "Control", "Iteration & traversal", "easy", "Loops, accumulators, and walking through data."),

    # ---------------- Complexity ----------------
    ("Complexity", "Counting", "Counting operations", "easy", "Count the steps an algorithm takes — the gateway to Big-O."),
    ("Complexity", "Big-O", "Big-O notation", "medium", "Describe how cost grows with input size, ignoring constants."),
    ("Complexity", "Big-O", "Common complexities", "medium", "From O(1) to O(n!): visualize the growth curves and pick by scale."),
    ("Complexity", "Math", "Logarithms & powers of two", "easy", "Why halving gives log n — the math behind binary search and trees."),
    ("Complexity", "Amortized", "Amortized analysis", "medium", "Why a dynamic array's append is O(1) on average despite occasional resizes."),

    # ---------------- Arrays ----------------
    ("Arrays", "Memory", "Arrays & memory", "easy", "Contiguous memory and why indexing is O(1)."),
    ("Arrays", "Operations", "In-place operations", "easy", "Modify an array without extra space; the swap/overwrite mindset."),
    ("Arrays", "Prefix", "Prefix sums", "easy", "Precompute cumulative sums for O(1) range queries."),
    ("Arrays", "2D", "2D arrays & matrices", "medium", "Row-major layout; traversing grids."),

    # ---------------- Hashing ----------------
    ("Hashing", "Core", "Hash tables", "easy", "key -> hash -> bucket: O(1) average lookup, insert, delete."),
    ("Hashing", "Core", "Hash sets vs maps", "easy", "Membership vs key->value; when to use each."),
    ("Hashing", "Patterns", "Frequency counting", "easy", "Count occurrences with a map — the most common interview opener."),
    ("Hashing", "Internals", "Collisions & load factor", "medium", "What happens when two keys hash the same; why resizing keeps it fast."),

    # ---------------- Strings ----------------
    ("Strings", "Basics", "String traversal", "easy", "Strings as character arrays; immutability gotchas."),
    ("Strings", "Counting", "Frequency arrays", "easy", "Fixed-size count arrays for anagrams and character problems."),
    ("Strings", "Pointers", "Two pointers on strings", "easy", "Converge from both ends or scan together."),
    ("Strings", "Problems", "Palindromes", "easy", "Check by expanding around centers with two pointers."),
    ("Strings", "Problems", "Anagrams", "easy", "Compare character frequencies."),
    ("Strings", "Advanced", "Pattern matching (KMP)", "hard", "Skip redundant comparisons using the prefix function."),

    # ---------------- Sorting — Basics (iterative; great for Big-O intuition) ----------------
    ("Sorting — Basics", "Quadratic", "Bubble sort", "easy", "Repeatedly swap adjacent out-of-order pairs; the largest bubbles up."),
    ("Sorting — Basics", "Quadratic", "Selection sort", "easy", "Each pass selects the minimum and places it."),
    ("Sorting — Basics", "Quadratic", "Insertion sort", "easy", "Insert each element into the sorted prefix."),

    # ---------------- Searching ----------------
    ("Searching", "Linear", "Linear search", "easy", "Scan element by element — the O(n) baseline."),
    ("Searching", "Binary", "Binary search", "easy", "Halve the search space each step on sorted data."),
    ("Searching", "Binary", "Lower bound", "medium", "First index not less than the target — a distinct BS mental model."),
    ("Searching", "Binary", "Upper bound", "medium", "First index strictly greater than the target."),
    ("Searching", "Binary", "Binary search on the answer", "hard", "Search the answer space when the array isn't what you binary-search."),

    # ---------------- Two Pointers & Windows ----------------
    ("Two Pointers & Windows", "Pointers", "Two pointers", "easy", "Two indices moving toward each other or together."),
    ("Two Pointers & Windows", "Pointers", "Fast & slow pointers", "medium", "Different speeds to find cycles, middles, nth-from-end."),
    ("Two Pointers & Windows", "Windows", "Sliding window (fixed)", "medium", "A fixed-size window sliding across the array."),
    ("Two Pointers & Windows", "Windows", "Sliding window (variable)", "medium", "Grow and shrink the window to satisfy a constraint."),
    ("Two Pointers & Windows", "Arrays", "Kadane's algorithm", "medium", "Maximum subarray sum via a running best."),

    # ---------------- Stacks & Queues ----------------
    ("Stacks & Queues", "Stack", "Stack fundamentals", "easy", "LIFO; push/pop; the call-stack analogy."),
    ("Stacks & Queues", "Stack", "Valid parentheses", "easy", "Match brackets using a stack."),
    ("Stacks & Queues", "Stack", "Min stack", "medium", "Track the minimum in O(1) alongside the stack."),
    ("Stacks & Queues", "Stack", "Monotonic stack", "hard", "Keep a sorted stack to answer next-greater queries fast."),
    ("Stacks & Queues", "Stack", "Next greater element", "medium", "For each element, the next larger one to its right."),
    ("Stacks & Queues", "Queue", "Queue & deque", "easy", "FIFO and double-ended queues."),

    # ---------------- Linked Lists ----------------
    ("Linked Lists", "Basics", "Traversal & reversal", "easy", "Walk a list; reverse pointers iteratively."),
    ("Linked Lists", "Pointers", "Find the middle", "easy", "Fast/slow pointers to reach the midpoint."),
    ("Linked Lists", "Pointers", "Floyd's cycle detection", "medium", "Tortoise and hare to detect a loop."),
    ("Linked Lists", "Merge", "Merge two sorted lists", "easy", "Splice two sorted lists into one."),
    ("Linked Lists", "Hard", "Reverse in k-groups", "hard", "Reverse every k nodes, carefully relinking."),

    # ---------------- Recursion (now that iteration is solid; split into small concepts) ----------------
    ("Recursion", "Foundations", "Base case", "easy", "The stopping condition — without it, infinite recursion."),
    ("Recursion", "Foundations", "Recursive relation", "easy", "Express a problem in terms of a smaller version of itself."),
    ("Recursion", "Foundations", "The call stack", "easy", "How nested calls stack up and unwind."),
    ("Recursion", "Foundations", "Recursion tree", "medium", "Visualize branching calls; read time complexity off the tree."),

    # ---------------- Backtracking ----------------
    ("Backtracking", "Template", "Backtracking template", "medium", "Choose, explore, un-choose — the universal loop."),
    ("Backtracking", "Problems", "Subsets", "medium", "Generate all subsets via include/exclude decisions."),
    ("Backtracking", "Problems", "Permutations", "medium", "Build arrangements by marking used elements."),
    ("Backtracking", "Problems", "Combination sum", "medium", "Pick numbers (with reuse) that hit a target."),
    ("Backtracking", "Problems", "N-Queens", "hard", "Place queens row by row, pruning attacked columns and diagonals."),

    # ---------------- Sorting — Divide & Conquer (needs recursion) ----------------
    ("Sorting — Divide & Conquer", "Efficient", "Merge sort", "medium", "Split to single elements, then merge sorted halves."),
    ("Sorting — Divide & Conquer", "Efficient", "Quick sort", "medium", "Partition around a pivot, recurse on each side."),
    ("Sorting — Divide & Conquer", "Non-comparison", "Counting sort", "medium", "Count occurrences, reconstruct in order. O(n+k)."),

    # ---------------- Trees ----------------
    ("Trees", "Thinking", "Recursive tree thinking", "medium", "See a tree as a node plus two smaller subtrees — solve it recursively."),
    ("Trees", "Basics", "Binary tree & traversals", "easy", "Nodes and children; pre/in/post/level order."),
    ("Trees", "DFS", "DFS: pre / in / post", "medium", "Recursive depth-first orders and what each is for."),
    ("Trees", "BFS", "Level-order (BFS)", "medium", "Queue-based level-by-level traversal."),
    ("Trees", "BST", "BST: insert & search", "medium", "Ordered tree; go left/right by comparison."),
    ("Trees", "BST", "Validate a BST", "medium", "Check the ordering invariant with bounds."),
    ("Trees", "Queries", "Lowest common ancestor", "medium", "The deepest node that is an ancestor of both."),
    ("Trees", "Metrics", "Height & diameter", "medium", "Recursive depth; longest path between leaves."),

    # ---------------- Heaps ----------------
    ("Heaps", "Core", "Binary heap", "medium", "Array-backed complete tree; sift up/down for O(log n) priority."),
    ("Heaps", "Use", "Heap sort", "hard", "Build a heap, repeatedly extract the max."),
    ("Heaps", "Use", "Top-K with a heap", "medium", "Keep a size-K heap to find the K largest/smallest."),

    # ---------------- Graphs ----------------
    ("Graphs", "Basics", "Graph representations", "easy", "Adjacency list vs matrix; directed vs undirected."),
    ("Graphs", "Intuition", "Weighted vs unweighted", "medium", "Why edge weights change which algorithm you reach for."),
    ("Graphs", "Traversal", "BFS on graphs", "medium", "Explore by distance using a queue."),
    ("Graphs", "Traversal", "DFS on graphs", "medium", "Explore deep using recursion or a stack."),
    ("Graphs", "Shortest Path", "When BFS stops working", "medium", "BFS gives shortest paths only on unweighted graphs — here's why."),
    ("Graphs", "Components", "Connected components", "medium", "Count islands / groups via flood fill."),
    ("Graphs", "Cycles", "Cycle detection", "medium", "Detect cycles in directed and undirected graphs."),
    ("Graphs", "Ordering", "Topological sort", "hard", "Linear order of a DAG respecting dependencies."),
    ("Graphs", "Shortest Path", "Dijkstra's algorithm", "hard", "Shortest paths with non-negative weights via a heap."),
    ("Graphs", "DSU", "Union-Find", "hard", "Disjoint sets with union-by-rank + path compression."),
    ("Graphs", "MST", "Minimum spanning tree (Kruskal)", "hard", "Cheapest tree connecting all nodes."),

    # ---------------- Greedy ----------------
    ("Greedy", "Foundations", "Why greedy works", "medium", "Exchange argument and the greedy-choice property."),
    ("Greedy", "Foundations", "Why greedy fails", "medium", "Counterexamples where the locally-best choice loses — and how to spot them."),
    ("Greedy", "Intervals", "Interval scheduling", "medium", "Pick the most non-overlapping intervals."),
    ("Greedy", "Intervals", "Merge intervals", "medium", "Combine overlapping ranges."),
    ("Greedy", "Arrays", "Jump game", "medium", "Reach the end via furthest-reachable greedy."),

    # ---------------- Dynamic Programming (organized by THINKING, not problems) ----------------
    ("Dynamic Programming", "Thinking", "Overlapping subproblems", "medium", "The same subproblem recomputed many times — the first DP signal."),
    ("Dynamic Programming", "Thinking", "Optimal substructure", "medium", "The optimum is built from optima of subproblems."),
    ("Dynamic Programming", "Thinking", "State & transition", "medium", "Define what a subproblem IS and how it builds from smaller ones."),
    ("Dynamic Programming", "Thinking", "Memoization (top-down)", "medium", "Recursion plus a cache to kill repeated work."),
    ("Dynamic Programming", "Thinking", "Tabulation (bottom-up)", "medium", "Fill a table from base cases upward."),
    ("Dynamic Programming", "Thinking", "Space optimization", "hard", "Drop the table to a few rolling variables."),
    ("Dynamic Programming", "Examples", "Climbing stairs / Fibonacci", "easy", "The canonical first DP — overlapping subproblems made concrete."),
    ("Dynamic Programming", "Examples", "House robber", "medium", "Take-or-skip with a recurrence."),
    ("Dynamic Programming", "Examples", "Coin change", "medium", "Fewest coins to make an amount."),
    ("Dynamic Programming", "Examples", "0/1 Knapsack", "hard", "Pick items under a weight budget."),
    ("Dynamic Programming", "Examples", "Longest common subsequence", "hard", "Match two sequences via a 2D table."),
    ("Dynamic Programming", "Examples", "Edit distance", "hard", "Min insert/delete/replace to transform a string."),
    ("Dynamic Programming", "Examples", "Longest increasing subsequence", "hard", "Longest rising run; O(n log n) with binary search."),
    ("Dynamic Programming", "Examples", "Grid DP (unique paths / min path sum)", "medium", "Count paths / cheapest path through a grid."),

    # ---------------- Bit Manipulation ----------------
    ("Bit Manipulation", "Basics", "Bitwise operators", "easy", "AND/OR/XOR/shift and what they compute."),
    ("Bit Manipulation", "Tricks", "Single number (XOR)", "easy", "XOR cancels pairs to find the lone element."),
    ("Bit Manipulation", "Tricks", "Counting bits", "medium", "Count set bits with DP / Brian Kernighan."),

    # ---------------- Algorithm Design Patterns (capstone: RECOGNITION, ties everything together) ----------------
    ("Algorithm Design Patterns", "Approach", "Brute force first", "easy", "Always start with the obvious solution; it defines correctness and the baseline."),
    ("Algorithm Design Patterns", "Approach", "Precomputation", "medium", "Sort, hash, or prefix the input up front to unlock a faster solution."),
    ("Algorithm Design Patterns", "Recognize", "Recognizing divide & conquer", "medium", "Signals a problem splits into independent subproblems."),
    ("Algorithm Design Patterns", "Recognize", "Recognizing two pointers", "medium", "Signals a converging/scanning two-index solution fits."),
    ("Algorithm Design Patterns", "Recognize", "Recognizing sliding window", "medium", "Spot contiguous-subarray/substring constraints."),
    ("Algorithm Design Patterns", "Recognize", "Recognizing greedy vs DP", "hard", "Tell when local choices suffice vs when you must explore states."),
    ("Algorithm Design Patterns", "Recognize", "Recognizing graph problems", "medium", "Spot the hidden graph (states/edges) in a word problem."),
    ("Algorithm Design Patterns", "Capstone", "Pattern recognition drill", "hard", "Given a problem, name the pattern before coding — the interview superpower."),
]


async def main():
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM roadmap_nodes WHERE roadmap_id = :rid"), {"rid": str(ROADMAP_ID)})
        await conn.execute(text("DELETE FROM roadmaps WHERE id = :rid"), {"rid": str(ROADMAP_ID)})
        await conn.execute(
            text("INSERT INTO roadmaps (id, slug, title, description, created_at) VALUES (:id, :slug, :title, :desc, now())"),
            {"id": str(ROADMAP_ID), "slug": SLUG, "title": TITLE, "desc": DESCRIPTION},
        )
        for i, (phase, section, title, tier, desc) in enumerate(NODES):
            await conn.execute(
                text("INSERT INTO roadmap_nodes "
                     "(id, roadmap_id, phase, section, title, tier, order_index, description) "
                     "VALUES (:id, :rid, :phase, :section, :title, :tier, :idx, :desc)"),
                {"id": str(uuid.uuid4()), "rid": str(ROADMAP_ID), "phase": phase,
                 "section": section, "title": title, "tier": tier, "idx": i, "desc": desc})
    print(f"Seeded '{TITLE}' with {len(NODES)} nodes.")


if __name__ == "__main__":
    asyncio.run(main())
