# Antigravity handoff — DSA phase 20 (Algorithm Design Patterns)

Phase 20 = **8 nodes** (`_TODO-dsa.md` section 20), **all `concept`** — the capstone recognition phase.
This is the LAST phase in the DSA roadmap. Its entire job is to turn "I know 19 phases of individual
techniques" into "I can look at a NEW, unseen problem and recognize which technique applies" — the
meta-skill every earlier phase was building toward but never named directly.

> **Infra reality check — simplest phase in the roadmap.** Zero runtime, zero viz, for every node.
> `runtime: "none"` across the board — there is nothing to trace step-by-step here; the skill being
> taught is PATTERN RECOGNITION across problems the reader has already learned to trace elsewhere. **No
> Pass 0, no Pass 2. Pure Pass 1 prose, and this doc is the whole handoff.**

**One pass:**
- **Pass 1 — PROSE (Antigravity, THIS packet):** author all 8 lessons' text. `runtime: "none"` for
  every node, no exceptions.

**Gate: `python content/validate.py` — zero errors. Do NOT run the frontend. Do NOT commit.** Tick boxes
in `content/_TODO-dsa.md` as each file lands green.

---

## The 8 nodes (slugs EXACT from `_TODO-dsa.md`; difficulty is Claude's best-first call — `seed_dsa.py`
does not have phase 20 nodes yet, that's separate Claude-side wiring)

| slug | title | kind | difficulty |
|---|---|---|---|
| `brute-force-first` | Brute force first | **C** concept | easy |
| `precomputation` | Precomputation | **C** concept | easy |
| `recognizing-divide-and-conquer` | Recognizing divide & conquer | **C** concept | medium |
| `recognizing-two-pointers` | Recognizing two pointers | **C** concept | medium |
| `recognizing-sliding-window` | Recognizing sliding window | **C** concept | medium |
| `recognizing-greedy-vs-dp` | Recognizing greedy vs DP | **C** concept | hard |
| `recognizing-graph-problems` | Recognizing graph problems | **C** concept | medium |
| `pattern-recognition-drill` | Pattern recognition drill | **C** concept | hard |

**Build order = table order, and it matters more here than in any other phase.** `brute-force-first` and
`precomputation` are the two GENERAL strategies every problem should start with, regardless of pattern —
build these first, they frame everything after. Then the five `recognizing-*` nodes, each keyed to a
family of earlier phases (divide & conquer → phases 13/16 MST; two pointers → phase 8; sliding window →
phase 8; greedy vs DP → phases 17/18; graph problems → phase 16). `pattern-recognition-drill` LAST — it
is the capstone that exercises all five recognition skills together and closes the entire roadmap.

---

## Research source

The phase-20 deep-research paste-ready prompt does not exist yet — write
`content/RESEARCH-dsa-phase20-algorithm-design-patterns.md` following the exact convention of
`content/RESEARCH-dsa-phase17-greedy.md` before running it, if research is wanted at all for this phase.
**This phase is unusually well-served by inlined must-hits below without waiting on research** — the
content is almost entirely "here's how to recognize a pattern you already learned," which is a synthesis
job over the roadmap's own prior content, not new external facts. Research (if run) should focus on
concrete "spot the pattern in this problem statement" examples and interview-signal framing, not new
algorithmic facts.

---

## Pass 1 — the 8 lessons (PROSE only, no `viz` block ever — `runtime: "none"`)

Follow `content/PROMPT-dsa.md` (⛔ no-viz boundary, FIVE questions, QUALITY BAR). Every node copies the
shape of `content/roadmaps/dsa/what-is-an-algorithm.json` and sets **`runtime: "none"`**.

**`concept` branch required fields:** `overview {what, why}`, `why_learning_this`, `common_mistakes`,
`recall_questions`, `practice_tasks`, `understanding_checks` (**≥2**), `sources`.

### Phase-wide rules (what makes this phase land, not just recap)

1. **Every node must give CONCRETE, PROBLEM-STATEMENT-LEVEL signals**, not abstract descriptions of the
   technique. "Look for the phrase 'contiguous subarray' with a size or sum constraint" beats "sliding
   window is used for subarray problems." The whole point of a recognition phase is training the pattern
   match on SURFACE FEATURES of a problem statement, since that's what an interview or a real task
   actually presents.
2. **Every `recognizing-*` node must ALSO give at least one plausible-looking DISTRACTOR** — a problem
   that superficially resembles the pattern but isn't (or needs a different technique). Recognition
   training that never shows a near-miss produces overconfident pattern-matching.
3. **Cross-link back to the ACTUAL phase/nodes that teach the technique being recognized** — this phase
   does not re-teach mechanics, it teaches "which earlier lesson do I need right now."
4. **No new algorithms are introduced in this phase.** If a must-hit below seems to need new mechanism
   explanation, it's out of scope — cross-link the earlier phase instead.

### Per-node must-hits

**`brute-force-first`** (C, easy) — the universal starting strategy, stated as a discipline.
- What: before reaching for any clever technique, state the OBVIOUS, always-correct, usually-slow
  solution first — nested loops, try-everything recursion, whatever requires zero cleverness.
- **Why this is not a waste of time (the actual payoff):** (1) it's a correctness baseline to test faster
  solutions against; (2) its STRUCTURE often reveals exactly which optimization applies — e.g. a brute
  force with two nested loops scanning a range is often crying out for two pointers or a sliding window;
  a brute force that recomputes the same subproblem repeatedly is crying out for DP (cross-link phase 18
  `overlapping-subproblems`).
- **The practical habit to install:** state the brute force's complexity FIRST, then ask "what is this
  complexity wasting?" — that question is what leads to the pattern.
- `understanding_checks` must catch: skipping straight to a remembered "clever trick" without being able
  to state why brute force is too slow for the given constraints (interview signal: if you can't state
  the brute force complexity, you can't justify the optimization either).

**`precomputation`** (C, easy) — trading space/preprocessing time for cheaper per-query answers.
- What: if the SAME kind of question gets asked many times over the same data, do expensive work ONCE
  up front so each individual query becomes cheap. Prefix sums (phase 3) are the canonical example:
  `O(n)` preprocessing turns every range-sum query into `O(1)` instead of `O(n)` each.
- **The recognition signal:** the problem asks for the SAME kind of answer over many different
  ranges/windows/pairs of the same fixed input — a hint that whatever varies per query can be computed
  once and reused.
- Other concrete examples to name (no new mechanism, just naming): a frequency map/hash table built once
  (phase 4) so membership/count queries are `O(1)`; sorting once so later steps can binary-search or
  two-pointer over the sorted order (phase 7/8).
- `understanding_checks` must catch: applying precomputation when there's only ONE query (pure overhead,
  no payoff — the whole technique only wins when the upfront cost is amortized over many queries).

**`recognizing-divide-and-conquer`** (C, medium) — the surface signal for "split, solve independently,
combine."
- **Recognition signals:** the problem can be split into independent (or nearly independent) halves whose
  answers combine cheaply into the whole answer; a naive solution's recurrence looks like `T(n) =
  2T(n/2) + O(n)` or similar. Cross-link `merge-sort` (phase 13) as the canonical shape.
- **The distractor to include:** a problem that LOOKS splittable but whose halves are NOT independent
  (e.g. depend on a running value that crosses the split point) — name one concretely, and note that this
  is often where D&C fails and a different technique (often DP, or a single linear scan like `kadane`)
  wins instead.
- `understanding_checks` must catch conflating "any recursive solution" with "divide and conquer
  specifically" (recursion is the mechanism, but D&C specifically requires the INDEPENDENT-halves
  structure).

**`recognizing-two-pointers`** (C, medium) — the surface signal for the two-pointer family (phase 8).
- **Recognition signals:** the input is a SORTED array (or can cheaply be sorted) and the problem asks
  about PAIRS or a RANGE satisfying some condition (sum, difference, count) — one pointer from each end,
  moving based on a comparison.
- **The distractor to include:** an unsorted-input problem where sorting would destroy needed
  information (e.g. original indices matter and aren't preserved) — two pointers doesn't directly apply
  without extra bookkeeping.
- Also name the fast/slow-pointer variant (phase 8 `fast-slow-pointers`) as a DIFFERENT recognition
  signal: cycle detection or "find the middle" on a linked structure, not a sorted-array condition — don't
  conflate the two variants under one signal.
- `understanding_checks` must catch mixing up two-pointers-from-both-ends with sliding-window's
  same-direction pointers (the next node) — these are genuinely different signals and techniques.

**`recognizing-sliding-window`** (C, medium) — the surface signal for the sliding-window family (phase
8), and the sharpest contrast pair with two-pointers in the whole phase.
- **Recognition signals:** the problem asks about a CONTIGUOUS subarray/substring with a size constraint
  (fixed-size window) or an optimality constraint (longest/shortest satisfying some condition) — both
  pointers move in the SAME direction, the window only grows/shrinks, never resets to scan from scratch.
- **The distractor to include:** a "contiguous subarray" problem where the optimal answer does NOT have
  the monotonic growth/shrink property sliding window depends on (e.g. needs signed/negative numbers where
  a window's sum isn't monotonic as it grows — this is exactly why `kadane`'s DP approach exists instead
  for max-subarray-sum with negatives, cross-link phase 8 `kadane`).
- **The explicit two-pointers-vs-sliding-window contrast (make this the spine of the lesson):** two
  pointers typically move from OPPOSITE ends toward each other over a SORTED, static structure; sliding
  window moves both pointers in the SAME direction over a CONTIGUOUS range, and the "window" itself is the
  answer's shape, not just a search mechanism.
- `understanding_checks` must catch applying sliding window to a NON-contiguous subsequence problem
  (windows are contiguous by definition — a subsequence-with-gaps problem needs a different technique,
  often DP, cross-link phase 18 `longest-increasing-subsequence`).

**`recognizing-greedy-vs-dp`** (C, hard) — the single highest-value discrimination in the entire
roadmap; directly operationalizes phase 17's `why-greedy-works`/`why-greedy-fails`.
- **The decision procedure to teach, explicitly, as a checklist (this IS the lesson):** (1) can you find
  an exchange argument — does making the locally-best choice now NEVER foreclose a better global outcome?
  If yes, greedy. (2) If a locally-best choice CAN foreclose a better outcome, does the problem have
  overlapping subproblems + optimal substructure (phase 18)? If yes, DP. (3) If neither holds cleanly,
  the problem may need brute force / backtracking, or isn't in this family at all.
- **Concrete worked pairs (reuse, don't reinvent):** `interval-scheduling` (greedy — earliest-end-time
  exchange argument holds) vs `0-1-knapsack` (DP — greedy-by-ratio provably fails, no exchange argument
  exists once items can't be split). Walk through WHY the exchange argument holds for one and not the
  other — this is the payoff of the whole node.
- **The distractor to include:** FRACTIONAL knapsack (greedy DOES work there, unlike 0/1) — a single
  changed constraint (splittable vs not) flips the right technique entirely; this is the sharpest possible
  demonstration that recognition requires looking at the PRECISE constraints, not the problem's vibe.
- `understanding_checks` must catch: assuming "sounds greedy" is sufficient justification (it never is
  without the exchange argument); giving up on greedy and jumping to DP without checking if a proof of
  the greedy choice actually exists first.

**`recognizing-graph-problems`** (C, medium) — the surface signal for "this is secretly a graph problem"
even when the input isn't drawn as one (phase 16).
- **Recognition signals:** entities with RELATIONSHIPS or DEPENDENCIES between them (not just a flat
  list) — "is A reachable from B," "what's the minimum number of steps/cost between two states," "is
  there a valid ORDER given dependency constraints" (→ `topological-sort`), "are these all connected /
  in the same group" (→ `connected-components`/`union-find`).
- **The disguised-graph skill (the actual payoff):** many problems don't LOOK like graphs on the surface
  — a grid of cells where you can move to adjacent cells IS a graph (nodes = cells, edges = valid moves);
  a set of words where you can transform one into another by one edit IS a graph (word ladder-style,
  nodes = words, edges = one-edit-apart pairs); state transitions in a puzzle ARE a graph. Name 2–3 such
  disguised cases explicitly.
- **The distractor to include:** a problem with entities and pairwise relationships that's actually
  better solved with union-find alone (no need for full BFS/DFS) vs one that genuinely needs shortest-path
  — both "look like graphs," the constraint (weighted? need actual path, or just connectivity?) decides
  which phase-16 tool applies.
- `understanding_checks` must catch failing to recognize a grid-traversal or state-transition problem as
  a graph problem because it wasn't given as an explicit adjacency list.

**`pattern-recognition-drill`** (C, hard) — the capstone; exercises all five `recognizing-*` skills
together, closes the roadmap.
- **Format: a set of SHORT problem statements (no full solutions), each requiring the reader to identify
  which pattern applies and WHY** — not to solve them. This is a diagnostic/practice node, not a new
  teaching node.
- Include at least one problem per pattern family covered in this phase (D&C, two pointers, sliding
  window, greedy-vs-DP, graph) PLUS at least 2 explicit DISTRACTOR problems that look like one pattern but
  are actually another (reuse the distractors named in the individual `recognizing-*` nodes above, or add
  fresh ones in the same spirit).
- For each problem, the "answer" the lesson body gives should be the RECOGNITION REASONING ("this is
  sliding window because X, Y" ), not a full trace or code — cross-link to the actual phase/node that
  teaches the mechanism for anyone who needs to re-learn it.
- **`recall_questions`/`oa_questions` here should be pattern-identification questions on NEW short problem
  statements** (not ones already used in the body) — this is the one node in the roadmap where testing
  transfer, not recall of the lesson's own examples, is the entire point.
- `understanding_checks`/`practice_tasks`: point at 3–5 real LeetCode-style problems (link only) spanning
  different patterns, framed as "which pattern, and why" rather than "solve this."

### Cross-links
Every node in this phase links BACKWARD to the phase(s) whose mechanics it's asking the reader to
recognize: `recognizing-divide-and-conquer` → phase 13; `recognizing-two-pointers`/
`recognizing-sliding-window` → phase 8; `recognizing-greedy-vs-dp` → phases 17/18 (both directions);
`recognizing-graph-problems` → phase 16. `pattern-recognition-drill` links to all of the above plus
itself is the terminal node of the roadmap (`related` should be empty or point back up only — nothing
forward).

## ASCII-only in JSON
`->` not an arrow glyph, `--` not an em-dash, straight quotes, `>=`/`<=` not the glyphs.

## Process (pass 1)
1. Write `content/RESEARCH-dsa-phase20-algorithm-design-patterns.md` if research is wanted (optional per
   Research source above — the must-hits below are likely sufficient on their own).
2. Read `what-is-an-algorithm.json` (shape) + `content/PROMPT-dsa.md` (QUALITY BAR items 6–7) + the
   inlined must-hits above.
3. Write the 8 files — `runtime: "none"` for every node, no exceptions; every `recognizing-*` node MUST
   include at least one distractor example (rule 2 above).
4. `python content/validate.py` → zero errors. Tick `content/_TODO-dsa.md`.
5. Standing pipeline: Sonnet/Gemini lesson critic → apply fixes → re-critic. DONE only when a cold
   beginner can answer every recall/oa question from the body AND correctly classify the drill node's
   NEW (not-in-body) example problems.

---

## Boundaries
- Touch only `content/roadmaps/dsa/*.json`, `content/_TODO-dsa.md`, and (optionally) the new
  `content/RESEARCH-dsa-phase20-algorithm-design-patterns.md`. No `viz`/`animation`/`image` — this phase
  has no runtime at all.
- No commits, no pushes, no DB/seed changes.
- If the spec fights reality, implement the closest faithful version and FLAG it in
  `content/REPORT-dsa-phase20.md` — do not silently redesign.

---

> **After phase 20, the DSA roadmap's content is complete (110 nodes across 20 phases).** Remaining work
> at that point is entirely Claude-side viz/infra (any Pass 0/Pass 2 items still open across phases
> 14-19) and the standing `seed_dsa.py` wiring gap noted in every phase 17-20 table above (none of these
> phases' nodes are in `seed_dsa.py` yet — a batch Claude-side task, not per-phase).
