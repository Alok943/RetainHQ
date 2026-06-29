# DSA Learning Architecture — RetainHQ

> **Status:** design, not yet built. Queued **after AI-Engineering content + images wrap.**
> **Principle:** *Don't teach algorithms — teach computational thinking.* Students don't fail because
> they can't memorize merge sort; they fail because they can't mentally simulate **state, invariants,
> recursion, pointers, and repeated decisions.** Every decision below optimizes for that.
>
> **North Star:** *a student should be able to mentally execute the algorithm on a NEW input without
> looking at code.* Every feature is judged against this.
>
> **Pattern vs Mental Model are distinct** (don't conflate): **Pattern** = the algorithm *family*
> (Divide & Conquer, BFS, Sliding Window). **Mental Model** = the *operating image* (Split→Solve→Merge,
> Expanding Frontier, Two Walls Closing). One pattern hosts many mental models.

Positioning: RetainHQ is **"where algorithms finally click,"** not another Striver/NeetCode. We own
*understanding + retention*; we link out to Striver/NeetCode for deliberate practice. New `dsa` roadmap —
do **not** attach to the existing problem-list roadmaps.

---

## Canonical pipeline

```
Algorithm Model  (the spine — language-independent)
   ├── mental_model      (Split→Solve→Merge, Expanding Frontier, …)
   ├── pattern[]         (Divide & Conquer, Sliding Window, BFS, …)  ← first-class, cross-linked
   ├── steps[]           ({ id, label })   ← step_id is the shared anchor
   ├── invariants[]      ({ id, statement })
   ├── complexity        ({ time, space, note })
   ├── failure_modes[]
   ├── why_it_exists     ({ problem, naive_solution, better_idea })
   ├── real_world[]      ({ title, explanation })   ← the engineering problem, NOT "Google uses X"
   └── code              ({ [lang]: { src, lineMap: step_id → [lines] } })  ← AUTHORED, never generated
        ↓
Execution Trace  (THE SOURCE OF TRUTH — golden-tested)
   { input, events:[ Event { op, args, step_id, invariant?, note? } ] }
        ↓  compile(input, events)   — run ONCE per input
Frames  (presentation cache, O(1) scrub)
   [ Frame { before, after, pointers, regions, caption, invariant, step_id } ]
        ↓
Renderer   Array · Tree · Grid · Graph(ReactFlow) · StateMachine   (dispatch by viz type; degrade on unknown op)
        ↓
Teaching Mode  |  Reference Mode  |  Recall (FSRS)
```

**The one-sentence architecture:** *the canonical artifact is the execution trace (events); animation,
pseudocode, every language's code, narration, accessibility, and analytics are all derived from it.*
Frames are a compiled presentation cache, not truth. Code is authored per language, keyed to `step_id`.

---

## Data model

```ts
// THE SPINE — one per algorithm, language-independent
AlgorithmModel {
  mental_model: { intuition, description }   // the operating image (Split→Solve→Merge)
  pattern: string[]                          // algorithm family ids (Divide & Conquer) — pattern graph
  repeated_decision: string                  // the ONE choice repeated every iteration —
                                             //   Merge Sort: "which side has the smaller next element?"
                                             //   Binary Search: "discard left or right half?"
                                             //   Sliding Window: "expand or shrink?"
  steps: { id: string, label: string }[]
  invariants: { id: string, statement: string }[]
  complexity: { time: string, space: string, note?: string }
  failure_modes: { title, explanation }[]
  when_not: { case, why }[]                  // contrast learning — Merge Sort: small arrays (extra memory);
                                             //   Binary Search: unsorted data
  why_it_exists: { problem, naive_solution, better_idea }
  real_world: { title, problem, why_this_algorithm }[]   // the ENGINEERING problem, not "Google uses X"
  practice: { platform, id, title, url, difficulty, why }[]   // 2–4 problems, tied to the pattern, tiered
  code: { [lang: string]: { src: string, lineMap: { [step_id]: number[] } } }
}

// THE TRUTH — pure function of input, golden-tested
Trace { input: any, events: Event[] }
Event { op: string, args: any, step_id: string, invariant?: string /* invariant id */, note?: string }

// DERIVED — materialized once by compile(input, events); renderer indexes into it for O(1) scrub
Frame { before, after, pointers, regions, caption, invariant, step_id }
```

### Key decisions
- **Execution trace is the source of truth**, not frames or code. `compile(input, events) → frames` runs
  once per input; scrubbing/seek is an array index. "Tweak values" = `algoEvents(newInput)` → recompile.
- **Events are language-independent.** They carry `step_id`, never a line number. Each language maps its
  own lines to the shared `step_id`s (`code[lang].lineMap`), so the code panel highlights correctly in
  whatever language is shown. **Code is authored & reviewed — never auto-generated from the model.**
- **Event `invariant` is an id** referencing `model.invariants[].id` — no free-text duplication.
- **Operation vocabulary is extensible by family**, with graceful fallback:
  - Array: `COMPARE, SWAP, MOVE, WRITE, SPLIT, MERGE`
  - Stack/Queue: `PUSH, POP, ENQUEUE, DEQUEUE`
  - Graph: `VISIT, MARK_VISITED, RELAX, ENQUEUE_NODE`
  - DP: `MEMO_WRITE, MEMO_HIT, FILL_CELL`
  - Recursion: `CALL, RETURN, CHOOSE, UNDO`
  - An **unknown op still renders** its `caption` + `invariant` (just no bespoke visual). New algorithm
    classes never force a core-enum edit.
- **Golden-trace tests** validate every generator: known input → expected `events[]`. Since the trace is
  now canonical, a wrong event mis-teaches everywhere downstream — this is the one place we add real test
  discipline.

### Predictions (the moat) — derived from the trace, not hardcoded
A prediction anchors to a `step_id` and is **templated against the live trace**, so it survives input
tweaking (a hardcoded *"merge [2,5] & [1,8] → ?"* is wrong the moment the student edits the array).
```json
"predictions": [
  { "at_step": "merge", "occurrence": "last",
    "prompt": "The next TWO values written during this merge?",
    "derive": "next_n_writes(2)" }   // answer computed from the actual events at that step
]
```
Player pauses at the step, student commits, then steps to reveal — **output is the real trace, never stored.**

**Prediction difficulty is progressive** (a `level` per checkpoint): `easy` = next step · `medium` =
pointer/state after this op · `hard` = state the invariant · `expert` = a what-if ("if this value were
larger, which branch?"). Climbs the learner from simulating *output* to simulating *reasoning*.

---

## Lesson flow (Teaching mode)
1. **Real-world problem** — why this algorithm exists (`why_it_exists.problem`).
2. **Mental model / analogy** (`mental_model`).
3. **Interactive visualization** — narrate the *data transformation* first (`[5 2 8 1] → split → … → merge
   → sorted`), NOT `def merge_sort`. Code comes at step… see below.
4. **Predict-before-reveal** (the superpower).
5. **Invariant** — the statement that makes it correct ("everything left of `i` is sorted").
6. **Complexity** — and *why*.
7. **Pattern** — "where else does this idea appear?" via the pattern graph (Divide & Conquer → binary
   search, closest-pair, segment trees…).
8. **Real-world engineering examples** (`real_world`) — the engineering problem, not trivia.
9. **Recall (FSRS)** — invariant, complexity, "trace one step," pattern. Enters spaced repetition.

**Code is step ~9-adjacent, never the centerpiece.** Order within code: data-transformation narration →
pseudocode (the Model's `steps`) → only then Python / Java / C++ / JS (all keyed to the same `step_id`s).
Leading with `def merge_sort(...)` flips students into syntax mode; we defer it deliberately.

---

## Renderers (dispatch by viz type; one per *data structure*, not per algorithm)
- **ArrayViz** (Framer Motion `layout`) — sorts, binary search, two-pointer, sliding window, Kadane…
- **TreeViz** (d3-hierarchy) — BST, traversals, heaps.
- **GridViz** — DP tables, matrices.
- **GraphViz** (**reuse ReactFlow**) — BFS/DFS/Dijkstra/topo-sort/union-find.
- **StateMachine** — recursion / call stack / backtracking / DP memoization / FSM. *Often the real "aha"
  for recursion — boxes-and-arrows beats bars.* Frequently shown **side-by-side with ArrayViz**.

Lazy-loaded (Framer Motion + viz) on DSA lesson pages only — zero bundle cost elsewhere.

## Modes
- **Teaching** — pauses, predictions, invariants, slow. The default learning path.
- **Reference** — scrub, ×8 speed, no interruptions. For revision. (Deferred past the pilot.)

## Retention
Recall targets the **model** (invariant, complexity, trace-a-step, pattern), not the animation. Feeds FSRS
via the existing **"Add to reviews"** bridge (`source_type='lesson'`, `node_id`). **Pattern** is first-class
and reuses the existing **prereq/unlock graph** tables, enabling cross-instance pattern recall.

## "Explain this frame" (every renderer must support it)
At any step the learner can ask *explain*, and the Player answers from the trace + model: **current
operation · current invariant · why this decision (the `repeated_decision`) · what changes next.** No
extra authoring — it's all derived from the event + model. This is the in-the-moment "why," the
counterpart to predict's "what."

## Analytics at the operation/pattern level (only the trace makes this possible)
Because the trace is canonical, log misses at the **operation** and **pattern** grain, not just per
algorithm. If a student repeatedly fails `MERGE` predictions across *multiple* Divide-&-Conquer algorithms,
recommend reviewing the **merge operation** (or the pattern) — not just "redo Merge Sort." This is a
retention feature no code-or-animation platform can offer, and it falls straight out of events-as-truth.

## Author exit criteria (a lesson isn't done until a learner can…)
1. Predict the next step. 2. State the invariant. 3. Explain the complexity. 4. Name the pattern.
5. Give one real-world engineering use. 6. Say when NOT to use it.
If the lesson can't get a learner to all six, it's incomplete — these map 1:1 to the model fields above.

## Validation
- `validate.py` gets a `dsa` branch: requires `mental_model`, `steps`, `invariants`, `complexity`,
  `why_it_exists`, `real_world`, `pattern[]`, `viz.generator` (must be a registered key), `viz.default_input`,
  `code` (≥1 language), recall≥3, oa≥2, sources; optional `predictions` (validate shape + `at_step` resolves
  to a real `step_id`).
- **Golden-trace tests** (JS) per generator — the canonical-artifact guarantee.

## File / code layout
```
content/roadmaps/dsa/merge-sort.json          # prose + model + code + viz ref + predictions
frontend/src/dsa/
  events.js            # Event/op families + the op registry (graceful fallback)
  compile.js           # compile(input, events) -> frames
  registry.js          # generator key -> events fn   (validate.py checks keys exist)
  generators/merge-sort.js     # mergeSortEvents(input) -> {input, events}   (golden-tested)
  generators/__tests__/merge-sort.golden.test.js
  renderers/ArrayViz.jsx, StateMachine.jsx, TreeViz.jsx, GridViz.jsx, GraphViz.jsx
  Player.jsx           # controls + predict gate + input editor + renderer dispatch + mode
LessonView.jsx         # kind:'dsa' -> <Player .../>
```

---

## The five questions (every lesson must answer these)
A DSA lesson isn't done until a learner can answer all five — they map onto the model fields:
1. **Why does this exist?** — `why_it_exists` (problem → naive → better idea).
2. **How do I mentally simulate it?** — the trace/visualizer + predict-before-reveal.
3. **What invariant / repeated decision makes it work?** — `invariants`, `repeated_decision`.
4. **Where is it used in real systems?** — `real_world` (the engineering problem, not "Google uses X").
5. **How do I recognize when to apply it?** — `pattern` + the Algorithm Design Patterns capstone.
If a node can't get a learner to all five, it's incomplete. This is the north-star quality bar — it's
what makes RetainHQ teach computational *thinking* rather than algorithm memorization.

## Mixed lesson kinds (deliberate)
This roadmap intentionally combines two kinds — don't force one shape on every node:
- **`dsa` (execution-trace)** — Merge Sort, BFS, Dijkstra, sliding window… anything you step through.
- **conceptual (`theory`/`engineering` kind)** — *What is an algorithm?, Big-O, Amortized analysis,
  Recursive tree thinking, Why greedy works/fails, the DP-thinking nodes, Algorithm Design Patterns.*
  These are diagram + explanation, NOT traces. `seed_dsa.py` flags which nodes are conceptual.

## Content workflow: deep research BEFORE authoring
Enrich every node via deep research first, then author. Per node, gather:
- real engineering use cases (problem → why this algorithm solves it),
- **`interview_frequency`** (high/med/low from aggregate sources) — NOT company folklore; there is **no
  per-node "Asked by" field** (it ages badly and is anecdotal; company data only from cited deep research),
- common mistakes / misconceptions, pattern-recognition cues, and high-quality interview + OA questions.
Run it in BATCHES per phase (not all 110 nodes at once); prioritize the teaching dimensions. The run-1/
run-2 JD research already covers the META (that DSA gates ML/GenAI/DE roles).

## Pilot scope (validate the spine, not the breadth)
- **Merge sort only.**
- `mergeSortEvents()` — **golden-tested.**
- Event → Frame **compiler.**
- **ArrayViz + StateMachine** side-by-side (recursion/call-stack is the aha).
- **Teaching mode** only.
- **One** prediction checkpoint (trace-derived).
- **One** pattern: `divide-and-conquer` (with a stubbed "appears in…" list).
- **Python only** (Java/C++/JS later, keyed to the same `step_id`s).
- `why_it_exists` + `real_world` authored for merge sort.

Goal: prove **events-as-truth + compiler + two cooperating renderers + predict + pattern hook** on the
canonical "I can't picture this" algorithm — same role `embed-and-retrieve` played for the engineering kind.
The pilot front-loads the infra on purpose; the **second** algorithm is just a new golden-tested generator.

## Decided / open
- **Decided:** trace = source of truth; Python-first; reuse prereq/unlock graph for patterns; Teaching mode
  only in pilot; code authored not generated; new `dsa` roadmap (not attached to Striver).
- **Open (defer to build time):** exact op-family enums per data structure; whether `lineMap` is authored
  inline or in a sidecar; Reference-mode UX; how many algorithms seed the v1 roadmap.

## Dependencies / sequencing
New deps: **Framer Motion** (lazy). Reuse: ReactFlow, lesson shell + recall + FSRS + add-to-reviews,
predict-before-reveal, content sync. **This is a multi-week build and is queued behind finishing
AI-Engineering (content batches 2–6 + images).** Don't start until AI-Eng wraps.
