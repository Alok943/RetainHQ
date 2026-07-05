# Antigravity handoff -- DSA phase 11 (Recursion)

Author 4 NEW **`concept`-kind** lessons at `content/roadmaps/dsa/<slug>.json`. These are CONCEPT lessons
(ideas explained with words), NOT `dsa` execution-trace lessons -- so **there is NO `viz` block and NO
trace generator.** Set **`kind: "concept"`** and **`runtime: "none"`**.

**Gate: `python content/validate.py` -- zero errors.** Do NOT run the frontend. Do NOT commit.

## Reference + contract
- **Exemplars (study these 3 -- same shape, same kind):**
  - `content/roadmaps/dsa/what-is-an-algorithm.json`
  - `content/roadmaps/dsa/tracing-state-and-invariants.json`
  - `content/roadmaps/dsa/iteration-and-traversal.json`
- **Authoring contract:** `content/PROMPT-dsa.md`, section **A (`kind: "concept"` + `runtime: "none"`)**
  and the QUALITY BAR (esp. items 6-7: every recall/understanding answer must be derivable from the
  body; no unexplained jargon).
- **Enrichment source:** the phase-11 Recursion deep-research report `~/Downloads/phase11.md`. **Read
  only lines 1-160** (lines 1-104 = the prose; 105-160 = the works-cited/sources). Everything after
  line ~160 is base64-encoded math images -- SKIP it (it's why the file is ~97kb). The concrete
  per-node enrichment + real sources are also inlined below under "RESEARCH-GROUNDED ENRICHMENT" so you
  can author without re-parsing. Name the engineering use, not "Company X uses it."

## Required fields (CONCEPT branch of `validate.py` -- do NOT use the dsa fields)
- `slug`, `title`, `roadmap` ("dsa"), `kind` ("concept"), `tier`, `metadata` (difficulty,
  estimated_minutes, importance 1-10, interview_frequency, prerequisites[], unlocks[]).
- `overview` -- object with **`what`** and **`why`**.
- `why_learning_this` -- list of strings.
- `common_mistakes` -- list of `{title, explanation}` (>=1).
- `recall_questions` -- list of `{q, answer, tier}` (>=3).
- `understanding_checks` -- **>=2**, each `{type, question, answer, why}` where `type` is one of
  `predict-output | predict-result | explain-behavior | find-bug | choose-model | debug-misconception`.
- `practice_tasks` -- list.
- `sources` -- list of real URLs (2-5).
- **Optional (use them -- recursion is perfect for this):** `aha_moment {code, prediction,
  common_guess, why}` -- the `code` is ILLUSTRATIVE ONLY (runtime is `none`, it is NOT executed); great
  as a predict-before-reveal hook. `challenge {title, prompt}`. `glossary [{term, definition}]`.
- **Do NOT** add `viz`, `why_it_exists`, `mental_model`, `oa_questions`, `code_walkthrough`,
  `sections` with images/animation -- those belong to other kinds.

## The 4 nodes (slugs are EXACT from `_TODO-dsa.md`) + the misconception each must inoculate against
| slug | title | tier | focus + THE misconception to kill |
|---|---|---|---|
| `base-case` | Base case | easy | The stopping condition. **Misconception:** "recursion just knows when to stop." No -- without a base case (or if the argument never shrinks toward it) you get infinite recursion -> `RecursionError`/stack overflow. The base case must be REACHABLE and handle the smallest input. |
| `recursive-relation` | Recursive relation | easy | Expressing a problem via a smaller version of itself. **Misconception:** the recursive call restates the SAME problem. No -- it must be a STRICTLY SMALLER subproblem that makes progress toward the base case. Teach the "leap of faith": assume the recursive call correctly solves the smaller case, then just combine. |
| `the-call-stack` | The call stack | easy | How nested calls stack and unwind. **Misconception:** recursion is magic with no cost. No -- each call pushes its OWN stack frame (its own locals/return address); frames unwind LIFO (the last call returns first); Python caps depth (~1000) -> `RecursionError`. Teach the "work on the way DOWN vs work on the way UP" distinction (pre- vs post-recursive-call work). Link to `stack-fundamentals` (LIFO) and `tracing-state-and-invariants`. |
| `recursion-tree` | Recursion tree | medium | Visualizing branching calls; reading complexity off the tree. **Misconception:** cost = depth. No -- total work = SUM over ALL nodes; a branching factor b and depth d means ~b^d calls (naive Fibonacci = O(2^n) because each call spawns two). Overlapping subproblems (fib recomputing f(n-2) everywhere) is exactly what motivates memoization -> link forward to Dynamic Programming. |

## RESEARCH-GROUNDED ENRICHMENT (from phase11.md -- use this concrete material)

**Depth caveat:** these are BEGINNER `concept` lessons (easy/medium). Use the research for INTUITION
and real examples, NOT for heavy math. Mention the Master Theorem exists as the shortcut, but do NOT
derive it; teach the recursion tree at the "sum the work across all nodes" level.

**base-case**
- Two properties of valid recursion: a base case (returns WITHOUT recursing) + a recursive step that
  reduces every case toward it. The line between a CIRCULAR definition and a VALID one: each call must
  operate on input STRICTLY SMALLER in some measurable sense. (Ground the "leap of faith" in induction.)
- Failure: no base case, OR a base case never reached because the argument doesn't shrink -> infinite
  regress -> stack overflow / Python `RecursionError`.
- Engineering use: the base case is the parser's/traversal's terminating token (empty input, null node).

**recursive-relation**
- A recurrence describes runtime via smaller inputs: `T(n) = a*T(n/b) + f(n)` (a = #subproblems,
  n/b = subproblem size, f(n) = divide+combine work). Merge sort = `2T(n/2)+O(n)`; binary search =
  `T(n/2)+O(1)`. Keep the algebra light -- the point is "define the problem in terms of a smaller self."
- Engineering use: **fast exponentiation** Pow(x,n) (LeetCode 50) -- `x^n = (x^(n/2))^2` (even),
  `x*(x^((n-1)/2))^2` (odd), base `x^0=1`; halving the exponent turns O(n) into O(log n). Clean,
  interview-famous illustration of writing a recursive relation + base case.

**the-call-stack**
- Each call's state (locals, params, return address) lives in a stack frame / activation record; a call
  PUSHES a frame (LIFO), the base case returns + POPS, paused callers resume during "unwinding." Naive
  recursion space = O(depth) = number of live frames; overflow the finite stack -> crash.
- Killer teachable fact: **Tail Call Optimization** (reuse the frame when the recursive call is the very
  last action -> O(1) space) exists, but **Python deliberately REJECTS it to keep full stack traces for
  debugging** (Scheme mandates it; Rust/JS don't reliably have it). Great "why does my Python recurse
  limit at ~1000?" hook. (Keep TCO as an aside, not the main thread.)
- Engineering use: **Max Depth of Binary Tree** (LeetCode 104) -- recursive DFS delegates state to the
  call stack (vs iterative BFS needing an explicit queue); base null->0, step `1 + max(L, R)`.

**recursion-tree**
- Root = the non-recursive work; it branches into `a` children of size n/b; sum work across each level,
  then across levels. Intuition to teach: **total work = sum over ALL nodes, not just the depth.**
- BALANCED (merge sort): every level does O(n) work, ~log n levels -> O(n log n). LEAF-HEAVY: work
  explodes toward the leaves -- **naive Fibonacci calls itself twice -> ~2^n nodes -> O(2^n).** That
  explosion is exactly what **memoization** (cache each subproblem, prune repeats) collapses to O(n) --
  the forward link to Dynamic Programming. The Master Theorem is the codified shortcut for reading these
  three profiles (leaf-heavy / balanced / root-heavy) -- name it, don't derive it.
- Engineering use: **recursive-descent parsing** (the flagship) -- a compiler maps each grammar rule to
  a recursive function (`parseExpression -> parseTerm -> parseFactor`, and `parseFactor` recurses back
  to `parseExpression` for parenthesized sub-expressions = MUTUAL RECURSION); the call stack implicitly
  builds the AST. Real: GCC moved to a hand-written recursive-descent parser for C++; Clang uses one for
  C/C++/Objective-C (precise control + better error recovery). Good for `the-call-stack` too.

**Real sources (pick 2-5 per lesson):** Wikipedia (Recursion / Recursion (computer science) / Recursive
definition / Tail call / Mutual recursion); Master Theorem & recurrences (oregonstate huanlian notes,
CLRS 4.4 walkccc.me, Cornell CS3110 Lec 20); Recursion Tree Method (GeeksforGeeks); LeetCode 104 (Max
Depth of Binary Tree) + LeetCode 50 (Pow x,n); NeetCode recursion cheatsheet.

> Full distilled research digest is banked in headroom (hash `697aabba4e0ec4fc55095242`) if a fuller
> reference is needed later.

## Quality bar (the FIVE questions, concept-adapted -- answerable from THIS lesson alone)
1. Why does this exist? (what problem recursion/this piece solves; the iterative pain it removes)
2. How do I mentally simulate it? (trace the calls by hand -- the aha_moment/understanding_checks do this)
3. What is the invariant / repeated decision? (each call moves strictly toward the base case)
4. Where is it used in real systems? (tree/graph traversal, divide-and-conquer sort, backtracking,
   parsing, filesystem walks -- name the engineering situation)
5. How do I recognize when to reach for it? (the problem is self-similar -- a big instance is built from
   smaller instances of the SAME problem)
- `understanding_checks` should lean on recursion's natural aha moments: **predict-output** (trace a
  small recursive function's return value / print order), **find-bug** (a missing or unreachable base
  case), **explain-behavior** (the unwinding order / why work-on-the-way-up differs).
- Cross-link `related`/prereqs sensibly: `base-case` -> `recursive-relation` -> `the-call-stack` ->
  `recursion-tree`; `the-call-stack` prereq `stack-fundamentals`; `recursion-tree` unlocks the
  Backtracking (phase 12) and Memoization (DP) nodes.

## ASCII-only in JSON
Plain ASCII in string values -- `->` not an arrow glyph, `--` not an em-dash, straight quotes.

## Process
1. Read the 3 concept exemplars + PROMPT-dsa.md section A + the research report (if any).
2. Write the 4 files. `kind:"concept"`, `runtime:"none"`, NO `viz`.
3. `python content/validate.py` -> zero errors. Tick the boxes in `_TODO-dsa.md`.
4. Then the standing pipeline: **Sonnet / Gemini-in-Antigravity lesson critic** (separate session,
   `content/PROMPT-lesson-critic.md` or the runbook `content/RUN-lesson-critic-antigravity.md`) ->
   apply fix list -> re-critic. DONE only when a cold beginner can answer every recall/understanding
   question from the body AND the expert finds zero correctness errors.

> No `viz` for these four -- they are concept lessons. (A future call-stack execution-trace could be
> layered onto `the-call-stack`/`recursion-tree` later, but that is NOT part of this packet.)
