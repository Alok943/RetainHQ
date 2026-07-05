# Lesson Critic Report - DSA

LESSON: base-case
VERDICT: PASS
CORRECTNESS ERRORS: []
UNANSWERABLE RECALL/OA (teaching holes): []
FIVE-QUESTIONS GAPS: []
MENTAL-MODEL / ARC / HOOK notes: The overview cleanly motivates why it exists. The countdown/factorial examples work well to ground the concept. A real-world engineering example isn't strictly present (countdown is a toy), but since this is a micro-concept applied to *every* recursive algorithm, it serves its purpose perfectly.
EXAMPLE/SOURCE FLAGS: []
FIX LIST (ranked): []

LESSON: recursive-relation
VERDICT: PASS
CORRECTNESS ERRORS: []
UNANSWERABLE RECALL/OA (teaching holes): []
FIVE-QUESTIONS GAPS: []
MENTAL-MODEL / ARC / HOOK notes: The "leap of faith" concept is explained exceptionally well and builds a strong mental model for how to approach writing recursive logic without getting tangled in the trace.
EXAMPLE/SOURCE FLAGS: []
FIX LIST (ranked): []

LESSON: the-call-stack
VERDICT: PASS
CORRECTNESS ERRORS: []
UNANSWERABLE RECALL/OA (teaching holes): []
FIVE-QUESTIONS GAPS: []
MENTAL-MODEL / ARC / HOOK notes: The explanation of 'on the way down' vs 'on the way up' is a fantastic mental model. Discussing Python's deliberate rejection of TCO is a great "aha" moment that deepens understanding of space complexity.
EXAMPLE/SOURCE FLAGS: []
FIX LIST (ranked): []

LESSON: recursion-tree
VERDICT: NEEDS-WORK
CORRECTNESS ERRORS:
- {field: `practice_tasks[0].solution`, claim: "`fib(2)` is computed twice (once in the left branch of `fib(4)`, and once as the right child of `fib(3)`).", correction: "Because `fib(n) = fib(n-1) + fib(n-2)`, `fib(4)` calls `fib(3)` (left) and `fib(2)` (right). So `fib(2)` is the right child of `fib(4)`. Then `fib(3)` calls `fib(2)` (left) and `fib(1)` (right). So `fib(2)` is the left child of `fib(3)`."}
UNANSWERABLE RECALL/OA (teaching holes): []
FIVE-QUESTIONS GAPS: []
MENTAL-MODEL / ARC / HOOK notes: The contrast between depth (space) and total nodes (time) is extremely clear and completely prevents the common beginner mistake. Excellent.
EXAMPLE/SOURCE FLAGS: []
FIX LIST (ranked):
- {field: `practice_tasks[0].solution`, problem: "Flipped left/right branches for fib calls", concrete_fix: "Change to: `fib(2)` is computed twice (once as the right child of `fib(4)`, and once as the left child of `fib(3)`)."}

LESSON: backtracking-template
VERDICT: NEEDS-WORK
CORRECTNESS ERRORS: []
UNANSWERABLE RECALL/OA (teaching holes): []
FIVE-QUESTIONS GAPS: [4. Where is it used in real systems? (No `engineering_examples` provided in the lesson)]
MENTAL-MODEL / ARC / HOOK notes: The mental model of a maze and string works well. The arc explains the memory issue of brute-force copy effectively. No hook was provided.
EXAMPLE/SOURCE FLAGS: []
FIX LIST (ranked): [
  {
    "field": "engineering_examples",
    "problem": "Missing entirely. The learner cannot answer question 4 (Where is it used in real systems?).",
    "concrete_fix": "Add an engineering_examples block, e.g., describing regex engines or constraint solvers."
  }
]

LESSON: subsets
VERDICT: PASS
CORRECTNESS ERRORS: []
UNANSWERABLE RECALL/OA (teaching holes): []
FIVE-QUESTIONS GAPS: []
MENTAL-MODEL / ARC / HOOK notes: The buffet line intuition is clear. The decision tree ASCII is excellent for simulating the process.
EXAMPLE/SOURCE FLAGS: []
FIX LIST (ranked): []

LESSON: permutations
VERDICT: NEEDS-WORK
CORRECTNESS ERRORS: []
UNANSWERABLE RECALL/OA (teaching holes): [
  {
    "question": "How can you optimize permutation generation to O(1) auxiliary space?",
    "missing_from": "explanation"
  }
]
FIVE-QUESTIONS GAPS: []
MENTAL-MODEL / ARC / HOOK notes: The chairs on a stage intuition is great. The decision tree structure is clear.
EXAMPLE/SOURCE FLAGS: []
FIX LIST (ranked): [
  {
    "field": "explanation",
    "problem": "The second OA question tests the specifics of swap-in-place (Heap's algorithm) implementation ('At depth i, swap nums[i] with every element...'), but the explanation only casually mentions its existence.",
    "concrete_fix": "Expand the mention of Heap's Algorithm in the explanation to explicitly teach the swap mechanism, or simplify the OA question so it doesn't test untaught implementation details."
  }
]

LESSON: combination-sum
VERDICT: NEEDS-WORK
CORRECTNESS ERRORS: []
UNANSWERABLE RECALL/OA (teaching holes): [
  {
    "question": "How can you modify the Combination Sum algorithm to only allow each element to be used once (Combination Sum II)?",
    "missing_from": "explanation"
  }
]
FIVE-QUESTIONS GAPS: []
MENTAL-MODEL / ARC / HOOK notes: The explanation of WHY we don't get permutation duplicates (using start_index) is the highlight here. Very clear.
EXAMPLE/SOURCE FLAGS: []
FIX LIST (ranked): [
  {
    "field": "explanation",
    "problem": "The second OA question expects the learner to know how to handle duplicate elements in the input (Combination Sum II), which involves `i > start and candidates[i] == candidates[i - 1]`. This is never taught in the body.",
    "concrete_fix": "Add a section to the explanation discussing how to handle input duplicates, or replace the OA question with one that can be answered using only what is taught (e.g., asking how sorting affects the pruning)."
  }
]

LESSON: n-queens
VERDICT: NEEDS-WORK
CORRECTNESS ERRORS: []
UNANSWERABLE RECALL/OA (teaching holes): [
  {
    "question": "Is it possible to optimize the space complexity of the attack trackers?",
    "missing_from": "explanation"
  }
]
FIVE-QUESTIONS GAPS: []
MENTAL-MODEL / ARC / HOOK notes: Sudoku analogy is perfect. The explanation of the O(1) diagonal math is a huge 'aha' moment.
EXAMPLE/SOURCE FLAGS: []
FIX LIST (ranked): [
  {
    "field": "explanation",
    "problem": "The second OA question expects the learner to know about integer bitmasks for space optimization. This is never mentioned in the body.",
    "concrete_fix": "Either explain bitmask tracking briefly in the body/key_points, or remove/replace the OA question."
  }
]

SUMMARY: 4 PASS, 5 NEEDS-WORK out of 9. NEEDS-WORK slugs: [recursion-tree, backtracking-template, permutations, combination-sum, n-queens].
SYSTEMIC PATTERNS: The primary issue in Phase 12 is a lack of self-containment for the second OA question across multiple lessons. Advanced techniques (bitmasks, swap-in-place, Combination Sum II deduplication) are tested in the answers but never taught in the lesson body.
