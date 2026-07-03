# DSA deep-research prompt (for Gemini) — enrich nodes BEFORE authoring lessons

> Paste everything from "ROLE" down, then append the topic list for ONE phase (lists at the
> bottom). Run one phase at a time. The output feeds lesson authoring for RetainHQ's
> "DSA — Algorithms Visualized" roadmap (teach computational thinking, not memorization).

---

## ROLE
You are a senior DSA educator + interview coach doing rigorous, citation-backed research. For each
topic I give you, research authoritative sources (CLRS, Wikipedia, GeeksforGeeks, official language
docs, well-regarded engineering blogs, NeetCode/Blind-75 curricula, LeetCode) and produce ONE
structured JSON object. Be accurate and concrete; if something is uncertain or contested, say so
rather than inventing. Do NOT copy problem statements or long source text (summarize + link).

## WRITING RULES — optimize for KNOWLEDGE EXTRACTION, not textbook prose
Your reader is an **AI lesson author**, not a student. Every rule below exists because prose
reports lose information at extraction time:
- **Structured bullets over paragraphs.** Never write flowing textbook chapters or section essays.
- **Compress wording without losing information.** Density is the goal; filler is loss.
- **Explain mechanisms, not definitions.** "The left pointer advances because the sorted order
  guarantees no smaller pair exists" — not "the two-pointer technique is a technique using two pointers."
- **No historical introductions, no company folklore.** Skip "the evolution of…" openers entirely.
  Engineering examples name the *problem*, never "Company X uses it."
- **Distinguish engineering reality from interview convention.** When the real-world answer differs
  from the expected interview answer (e.g. Timsort vs. hand-rolled merge sort), say both, labeled.
- **All math as plain text** — O(n log n), O(1), n/2 — NEVER LaTeX or images (they break on export
  and the complexity claims are lost).

## THE GOAL — every node must let an author answer these FIVE questions
1. **Why does this exist?** (the problem it solves; what was wrong with the naive way)
2. **How do I mentally simulate it?** (the intuition/analogy + the one repeated decision)
3. **What invariant / repeated decision makes it work?** (what stays true each step)
4. **Where is it used in real systems?** (the engineering problem, NOT "Company X uses it")
5. **How do I recognize when to apply it?** (the pattern + recognition cues)

## OUTPUT — one JSON object per topic, in this exact shape
```json
{
  "slug": "merge-sort",
  "title": "Merge Sort",
  "kind_hint": "trace",
  "confidence": { "overall": "high", "reason": "Canonical, well-documented algorithm.", "low_confidence_fields": [] },
  "why_it_exists": {
    "problem": "Sorting n items; we need better than O(n^2).",
    "naive_solution": "Bubble/insertion sort compare-and-swap neighbours — O(n^2), too slow at scale.",
    "better_idea": "Split the array, sort halves independently, then merge two sorted lists in O(n)."
  },
  "mental_model": {
    "intuition": "Split until trivially sorted (size 1), then zipper sorted halves back together.",
    "description": "2-3 sentences expanding the analogy a beginner can picture.",
    "repeated_decision": "At each merge step: which half has the smaller current front element?"
  },
  "invariants": [
    { "statement": "After merging a range, that range is fully sorted.",
      "why_violation_breaks": "Later merges assume both halves are sorted; one out-of-order element propagates upward and the final array is unsorted." },
    { "statement": "A single element is sorted by definition (base case).",
      "why_violation_breaks": "Without a trivially-true base case the recursion never terminates." }
  ],
  "complexity": { "time": "O(n log n)", "space": "O(n)", "note": "log n levels, O(n) work per level; stable; not in-place." },
  "when_not_to_use": [
    { "scenario": "Tiny arrays", "reason": "Insertion sort is faster due to low overhead and cache locality." },
    { "scenario": "Memory-constrained in-place sorting", "reason": "Merge sort needs O(n) auxiliary space; prefer quicksort/heapsort." }
  ],
  "common_mistakes": [
    { "title": "Off-by-one in merge bounds", "explanation": "Mishandling the mid split or the leftover tail." },
    { "title": "Thinking it's in-place", "explanation": "Standard merge sort needs O(n) auxiliary space." }
  ],
  "misconceptions": [
    { "false_belief": "Merging compares whole halves at once.",
      "reality": "Merge compares only the two FRONT elements of each half, one pair at a time.",
      "would_be_caught_by": "predicting the next written value during a merge step" },
    { "false_belief": "Splitting does the sorting work.",
      "reality": "Splitting is bookkeeping; ALL ordering work happens in the merge.",
      "would_be_caught_by": "asking which phase changes the array contents" }
  ],
  "failure_signals": [
    "An O(n^2) sort is too slow on your input size.",
    "You need a STABLE, predictable O(n log n) sort regardless of input order.",
    "Data is too big for RAM and must be sorted in streamed runs."
  ],
  "engineering_examples": [
    { "title": "External sorting", "problem": "Sorting data far larger than RAM.", "why_this_algorithm": "Merge naturally combines sorted runs streamed from disk — the basis of external merge sort in databases." },
    { "title": "Stable sorting in libraries", "problem": "Sort records without disturbing equal keys' order.", "why_this_algorithm": "Merge sort is stable; Timsort (Python/Java) is a merge-sort hybrid." }
  ],
  "pattern": { "name": "Divide & Conquer", "recognition_cues": ["problem splits into independent subproblems", "results combine cheaply", "natural recurrence T(n)=2T(n/2)+O(n)"] },
  "related": ["quick-sort", "binary-search", "merge-two-sorted-lists", "recursion-tree"],
  "learning_graph": {
    "must_know": ["recursion-tree", "the-call-stack", "iteration-and-traversal"],
    "helpful": ["binary-search"],
    "unlocks": ["quick-sort", "counting-sort", "merge-two-sorted-lists"]
  },
  "visualization": {
    "renderer": "array",
    "difficulty": "medium",
    "key_animation": "merge two sorted halves; secondary: recursion call stack",
    "interactive_inputs": [
      { "input": "[5,2,8,1,9,3]", "why": "default — mixed order, two uneven merge patterns" },
      { "input": "[9,8,7,6,5,4]", "why": "reverse-sorted — every comparison flips sides" },
      { "input": "[1,2,3,4]", "why": "already sorted — shows merge still runs (no early exit)" }
    ],
    "prediction_checkpoints": [
      { "at": "last merge step", "prompt_idea": "which two values are written next?", "level": "medium",
        "misconception_caught": "merging compares whole halves at once" },
      { "at": "first split", "prompt_idea": "does the array change during splitting?", "level": "easy",
        "misconception_caught": "splitting does the sorting work" }
    ]
  },
  "interesting_facts": [
    "Quicksort is O(n^2) worst case yet often beats merge sort in practice due to cache locality and no extra array.",
    "Python's and Java's default sorts (Timsort) are merge-sort hybrids tuned for partially-ordered data."
  ],
  "interview_frequency": { "level": "high", "evidence": "core sorting topic on virtually every DSA list (NeetCode, Blind-75); merge step is a frequent sub-question." },
  "practice": [
    { "platform": "LeetCode", "id": 912, "title": "Sort an Array", "difficulty": "medium", "url": "https://leetcode.com/problems/sort-an-array/", "why": "implement merge sort directly" },
    { "platform": "LeetCode", "id": 88, "title": "Merge Sorted Array", "difficulty": "easy", "url": "https://leetcode.com/problems/merge-sorted-array/", "why": "isolates the merge step" },
    { "platform": "LeetCode", "id": 315, "title": "Count of Smaller Numbers After Self", "difficulty": "hard", "url": "https://leetcode.com/problems/count-of-smaller-numbers-after-self/", "why": "merge-sort-based counting — pattern transfer" }
  ],
  "interview_questions": [
    { "q": "Why is merge sort O(n log n) but quicksort can degrade to O(n^2)?", "answer": "Merge always splits in half (balanced); quicksort's split depends on the pivot and can be lopsided.", "approach": "Tie complexity to the recursion-tree balance." },
    { "q": "When would you pick merge sort over quicksort?", "answer": "When stability matters or for linked lists / external sorting; quicksort wins on in-memory arrays for cache/space.", "approach": "Contrast stability, space, and access pattern." }
  ],
  "interview_thinking": {
    "recognition_strategy": "Stable O(n log n) required, linked-list sorting, or 'merge K sorted X' phrasing -> reach for merge/divide-and-conquer.",
    "common_followups": ["make it in-place (and why that's hard)", "merge K lists instead of 2", "sort a linked list in O(1) extra space"],
    "beginner_mistake": "Re-deriving the merge logic under pressure instead of knowing the two-front-pointers pattern cold.",
    "experienced_mistake": "Jumping to 'use the library sort' without demonstrating they can reason about the merge invariant."
  },
  "author_notes": {
    "lesson_focus": "The merge step (the repeated 'smaller front' decision) and why splitting yields log n levels — the 80/20 of this lesson.",
    "avoid_teaching": "Don't spend half the lesson on recursion syntax — recursion has its own phase.",
    "student_confusion": "Students conflate the split phase with sorting work; the visualization must make the merge visibly do ALL the reordering."
  },
  "sources": {
    "primary": ["https://en.wikipedia.org/wiki/Merge_sort"],
    "secondary": ["https://www.geeksforgeeks.org/merge-sort/"]
  }
}
```

## FIELD RULES
- **`kind_hint`**: `"trace"` for algorithms you step through (Merge Sort, BFS, Dijkstra, sliding
  window…) or `"concept"` for ideas you explain with a diagram (Big-O, Amortized analysis, Recursive
  tree thinking, Why greedy works/fails, the DP-thinking nodes, Algorithm Design Patterns,
  What is an algorithm?). For `"concept"` nodes, `repeated_decision` and `invariants` may be `"N/A"`;
  instead make `why_it_exists`, `mental_model`, `common_mistakes` (misconceptions), and `pattern`
  (recognition cues / where it applies) carry the lesson. `practice` may be fewer or empty for concepts.
- **`interview_frequency`**: high/med/low judged from AGGREGATE evidence — inclusion on curated lists
  (NeetCode 150, Blind 75, Striver), LeetCode tag frequency, standard-curriculum status. **NOT company
  folklore.** Do not assert "Asked at Google/Amazon" unless you cite a specific, datable source.
- **`real_world`**: the ENGINEERING problem and why this algorithm solves it (external sorting,
  routers, schedulers, package managers, autocomplete…). Avoid "Company X uses it" trivia.
- **`practice`**: 2-4 problems tied to the PATTERN (so the learner transfers), tiered easy→hard, each
  with a one-line `why`. Link only — never paste the problem text.
- **`sources`**: 2-5 real, authoritative URLs actually consulted. No fabricated links.
- Keep prose tight and beginner-true. Prefer the explanation that makes it *click*.
- **`mental_model`**: the analogy must be **mechanism-based** — every part of the analogy maps to a
  part of the algorithm (zipper teeth = front elements, zipping = comparing fronts). Decorative
  analogies that only share a vibe ("it's like organizing a bookshelf") are rejected: if you can't
  say what each analogy part corresponds to, find a better analogy.
- **`invariants`**: `[{statement, why_violation_breaks}]` — one sentence each. The violation
  consequence is what makes the invariant teachable (and predictable in the visualizer).
- **`misconceptions`**: distinct from `common_mistakes` (bugs). These are FALSE BELIEFS:
  `{false_belief, reality, would_be_caught_by}` — the last field names the observation/question
  that would expose the belief; it directly seeds prediction-checkpoint placement.
- **`interview_thinking`**: `{recognition_strategy, common_followups[], beginner_mistake,
  experienced_mistake}` — how an interviewee should THINK, not just Q&A pairs (those stay in
  `interview_questions`).
- **`learning_graph`**: `{must_know[], helpful[], unlocks[]}` — kebab-case slugs from the topic
  list. `must_know` = lesson assumes it; `helpful` = enriches but not blocking; `unlocks` = what
  this enables next. Feeds the prerequisite/pattern graph — be conservative in `must_know`.
- **`confidence`**: `{overall: high|medium|low, reason, low_confidence_fields: []}` — additionally
  NAME the specific fields you're least sure of (typically `engineering_examples` and
  `interview_frequency`); those get manual verification before authoring.
- **`when_not_to_use`**: `[{scenario, reason}]` — where this is the WRONG choice. Understanding via contrast.
- **`failure_signals`**: cues that you NEED this algorithm — "you keep recomputing the same subproblem", "you're re-scanning the array". Distinct from `common_mistakes` (bugs); these are *why-you-reach-for-it* signals.
- **`engineering_examples`** (renamed from "real world"): production uses as `{title, problem, why_this_algorithm}`.
- **`related`**: 2-5 kebab-case slugs of adjacent topics (powers "learn these next").
- **`visualization`**: `{renderer: array|tree|grid|graph|stack|linked-list|number-line|board|state-machine|none,
  difficulty, key_animation, interactive_inputs[], prediction_checkpoints[]}` (`renderer:"none"` for
  concept nodes, then the other viz fields may be omitted).
  - `interactive_inputs`: 2-4 inputs worth trying, each with a one-line `why` (best case, worst
    case, edge case) — these become the lesson's default input + preset buttons.
  - `prediction_checkpoints`: 1-3 `{at, prompt_idea, level: easy|medium|hard|expert,
    misconception_caught?}` — WHERE to pause the animation and WHAT to ask. Tie each to a
    misconception when possible; the best gate is one a student holding the false belief answers wrong.
- **`interesting_facts`**: 1-3 SURPRISING truths that make memorable hooks (not trivia).
- **`author_notes`**: `{lesson_focus, avoid_teaching}` — what to center on, and what NOT to over-explain.
- **`sources`**: `{primary: [...], secondary: [...]}` — primary = authoritative (CLRS, official docs, Wikipedia); secondary = explainer sites (GeeksforGeeks, blogs).

## NEVER COPY — SYNTHESIZE
Never copy explanations, sentences, or phrasing from GeeksforGeeks, Wikipedia, or any source. Read,
understand, and write ORIGINAL wording. Cite sources in `sources`, but the prose must be entirely your own.

## QUALITY BAR
Before returning a node, check: could an author write a lesson that answers all FIVE questions from
this alone? If a field is thin, dig deeper. Flag anything you're unsure about with a short `"note"`.

## OUTPUT FORMAT
Return a JSON array — one object per topic in the phase I paste — and nothing else but a short
"Sources consulted" list after it. Do one phase per run.

### If using Gemini DEEP RESEARCH (two-step — recommended)
Deep Research returns a prose report, not JSON. Don't fight it — run it for depth, then in the SAME
chat send this to extract the structured data:
> Convert your research above into a JSON array — one object per topic you covered — EXACTLY matching
> the schema above. Output ONLY the JSON (no prose before/after). Write complexities as PLAIN TEXT
> (O(n log n), O(1), O(n^2)) — never images/LaTeX. Synthesize in your own words; keep every field; use
> "N/A" where a field doesn't apply to a concept node (e.g. repeated_decision/invariants,
> visualization.renderer="none"). Split sources into primary (CLRS/docs/Wikipedia) vs secondary (GfG/blogs).

(If using plain Gemini 3 Pro instead of Deep Research, the single structured prompt works directly —
less browsing depth, but JSON out of the box.)

## WHERE OUTPUT LIVES + RESCUING OLD PROSE REPORTS
- **Extracted JSON is the artifact; the prose report is a byproduct.** Save each phase's JSON to
  `content/research/dsa/phase-<N>.json` in the repo — research left as loose .md files in Downloads
  is invisible to the authoring pipeline and to lesson handoff packets.
- **Retro-extraction:** prose reports already produced (phases 3-8, Foundations) still contain the
  knowledge — run the extraction prompt above against each report's text to recover structured JSON.
  Two known losses to repair during extraction: (1) complexity expressions exported as broken
  `![][imageN]` placeholders — re-derive them as plain text from context (the claims are standard);
  (2) fields the old prompt didn't ask for (`learning_graph`, `misconceptions`,
  `prediction_checkpoints`, `interactive_inputs`, `interview_thinking`, `why_violation_breaks`) —
  fill them from the report where the knowledge exists, and mark them in
  `confidence.low_confidence_fields` where it doesn't (they were not researched).
- One JSON object **per roadmap node**, keyed by `slug` — never one blob per phase — so authoring
  handoffs can reference exactly one node's research.

---

## TOPICS BY PHASE (paste one phase's list after the prompt)

**1. Foundations** (concept): What is an algorithm?; Tracing state & invariants; Iteration & traversal
**2. Complexity** (concept): Counting operations; Big-O notation; Common complexities; Logarithms & powers of two; Amortized analysis
**3. Arrays**: Arrays & memory; In-place operations; Prefix sums; 2D arrays & matrices
**4. Hashing**: Hash tables; Hash sets vs maps; Frequency counting; Collisions & load factor
**5. Strings**: String traversal; Frequency arrays; Two pointers on strings; Palindromes; Anagrams; Pattern matching (KMP)
**6. Sorting — Basics**: Bubble sort; Selection sort; Insertion sort
**7. Searching**: Linear search; Binary search; Lower bound; Upper bound; Binary search on the answer
**8. Two Pointers & Windows**: Two pointers; Fast & slow pointers; Sliding window (fixed); Sliding window (variable); Kadane's algorithm
**9. Stacks & Queues**: Stack fundamentals; Valid parentheses; Min stack; Monotonic stack; Next greater element; Queue & deque
**10. Linked Lists**: Traversal & reversal; Find the middle; Floyd's cycle detection; Merge two sorted lists; Reverse in k-groups
**11. Recursion** (mostly concept): Base case; Recursive relation; The call stack; Recursion tree
**12. Backtracking**: Backtracking template; Subsets; Permutations; Combination sum; N-Queens
**13. Sorting — Divide & Conquer**: Merge sort; Quick sort; Counting sort
**14. Trees**: Recursive tree thinking (concept); Binary tree & traversals; DFS: pre/in/post; Level-order (BFS); BST: insert & search; Validate a BST; Lowest common ancestor; Height & diameter
**15. Heaps**: Binary heap; Heap sort; Top-K with a heap
**16. Graphs**: Graph representations; Weighted vs unweighted (concept); BFS on graphs; DFS on graphs; When BFS stops working (concept); Connected components; Cycle detection; Topological sort; Dijkstra's algorithm; Union-Find; Minimum spanning tree (Kruskal)
**17. Greedy**: Why greedy works (concept); Why greedy fails (concept); Interval scheduling; Merge intervals; Jump game
**18. Dynamic Programming** (thinking nodes = concept): Overlapping subproblems; Optimal substructure; State & transition; Memoization (top-down); Tabulation (bottom-up); Space optimization; Climbing stairs / Fibonacci; House robber; Coin change; 0/1 Knapsack; Longest common subsequence; Edit distance; Longest increasing subsequence; Grid DP (unique paths / min path sum)
**19. Bit Manipulation**: Bitwise operators; Single number (XOR); Counting bits
**20. Algorithm Design Patterns** (concept): Brute force first; Precomputation; Recognizing divide & conquer; Recognizing two pointers; Recognizing sliding window; Recognizing greedy vs DP; Recognizing graph problems; Pattern recognition drill
