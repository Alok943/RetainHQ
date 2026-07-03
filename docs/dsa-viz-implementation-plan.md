# DSA Visualization — Full-Scope Implementation Plan

> **Status:** design doc, ready for implementation. Companion to `docs/dsa-architecture.md` —
> that doc is the *why* (events-as-truth, pedagogy, data model); this is the *gap audit + build
> plan*. Written so an implementing model can execute each milestone without further
> architectural judgment calls.
>
> **Scoping stance (explicit, decided):** there is NO MVP/V1 cut. Implementation cost is not the
> constraint; the target is **direct competitive superiority** over VisuAlgo, AlgoExpert,
> NeetCode and Hello Interview on every visualization axis. Milestones below are **dependency
> ordering, not scope cuts** — every feature has a milestone; nothing is deferred indefinitely.
> The real bottleneck is content authoring (Antigravity batches + founder critique time), so the
> plan's job is to keep infrastructure permanently ahead of content.
>
> **Audience for the product:** a beginner CSE student going from "I can't picture this" →
> interview-ready. Sequencing follows the learner's on-ramp (the `seed_dsa.py` phase order).

---

## 1. Problem / goal

The visualizer spine is live and proven for 12 algorithms across phases 1–7: generators → golden
tests → `compile()` → ArrayViz + StateMachine → Player inside `kind:'dsa'` lessons. The roadmap
has **110 nodes across 20 phases**, and the features that make the product *pedagogically and
competitively* different — predict-before-reveal, explain-this-frame, step-synced multi-language
code, pattern graph, operation-level analytics — are designed but unbuilt. Goal: a visualization
system where **every traceable node ships a stepping, predicting, explaining, code-synced
visualization**, and the retention loop measurably closes around it.

## 2. Current-state audit (verified 2026-07-02)

### Built and live
| Piece | State |
|---|---|
| Op vocabulary (`events.js`) | 5 families declared; array/recursion + POINT/SWAP/SET/COUNT/WINDOW/MARK/DONE actually compiled |
| Compiler (`compile.js`) | Array-centric Frame: `array, callStack, regions, sorted, pointers, map, caption, invariant, step_id` |
| Generators (12, golden-tested) | merge-sort, in-place-ops, prefix-sums, frequency-counting, palindromes, two-pointers-on-strings, frequency-arrays, bubble/selection/insertion-sort, linear/binary-search |
| Renderers | **ArrayViz** (numeric bars + char cells), **StateMachine** (call stack / pointers / freq map) |
| Player (`Player.jsx`) | play/pause/step/scrub, commentary-first pacing (READ_DELAY 1400ms → animate), input editor (number + string), invariant display |
| Content | 31/110 lessons (phases 1–7), 12 with `viz`; validator `dsa` branch checks generator keys against `registry.js` |

### Designed but NOT built (all get milestones below)
Predict-before-reveal · explain-this-frame · code panel (`code[lang]` + `lineMap: step_id →
lines`) · pattern graph · Reference mode · operation/pattern-level analytics.

### Holes in shipped content (phases 1–7)
Five live lessons are prose-only with viz pending: **lower-bound, upper-bound,
binary-search-on-the-answer, anagrams, pattern-matching-KMP**. All five get real visualizations
(including a bespoke KMP prefix-function viz — no prose-only tail).

### Not started
Renderers + op families + compiler support for stacks/queues, linked lists, recursion/decision
trees, binary trees/heaps, graphs, DP grids, intervals, bits, boards (N-Queens). Content for
phases 8–20 (~79 nodes) — blocked per-phase on generators landing first (validator dependency).

## 3. Competitive positioning (what "direct competition" means per capability)

| Capability | VisuAlgo | AlgoExpert / NeetCode | **RetainHQ target** |
|---|---|---|---|
| Step-through animation | ✔ | video only | ✔ (trace-driven, scrubbing O(1)) |
| Tweak the input | partial | ✘ | ✔ every lesson (free-form + presets) |
| Predict-before-reveal | ✘ | ✘ | ✔ **trace-derived, survives input edits** |
| Explain any frame (why) | ✘ | ✘ | ✔ derived from op+invariant+decision |
| Code synced to animation | line-highlight, 1 impl | static code | ✔ **multi-language, shared `step_id`s** |
| Invariant-first teaching | ✘ | partial (prose) | ✔ first-class ids, shown per frame |
| Spaced-repetition retention | ✘ | ✘ | ✔ FSRS "Add to reviews" bridge (live) |
| Pattern-level recall/analytics | ✘ | ✘ | ✔ **falls out of events-as-truth — uncopyable** |
| Revision mode (fast scrub) | ✔ | ✘ | ✔ Reference mode |

The last two rows are the moat: no competitor has an event-level trace as canonical truth, so
none can grade predictions per-operation or recommend pattern-level review. Rows 3–5 are where we
exceed; rows 1–2 and 9 are parity we must not miss.

## 4. Design decisions (with rationale)

**D0 — Core architectural principle: every educational behavior derives from canonical data,
never authored separately.** Predictions, explain-this-frame, analytics, pattern recall,
Reference mode, and future AI features all derive from the same canonical event trace (+ the
lesson model). No feature maintains its own parallel model of the algorithm. This is the
single rule that keeps the system coherent as it grows: if a proposed feature needs information
the trace + model don't carry, the fix is to enrich the *canonical* artifacts — not to author a
side-channel. Any PR that hardcodes an answer, duplicates state a frame already carries, or
teaches from something other than the trace violates this principle.

**D1 — Pedagogy before new renderers.** Predictions + explain-this-frame build first: they
upgrade all 12 live visualizations at once, and they are the anti-VisuAlgo differentiator
(retrieval practice vs. passive watching). Not a scope call — a leverage call.

**D2 — Renderer order follows the learner's path, just-in-time per phase.** Iteration before
recursion, recursion before trees — already encoded in seed order. Building all renderers up
front was considered and rejected: unproven renderers built speculatively risk rework, and
content is phase-batched anyway, so just-in-time loses nothing.

**D3 — Refactor `compile.js` into per-family reducers before adding new families.** One switch
at 3 families is fine; at 9 it's a state-leak hazard. Each family exports
`(state, event) → partial-frame-slice`; `compile()` composes. Existing output must stay
byte-identical (frame-snapshot goldens lock this).

**D4 — One Frame type with optional family slices.** Frame grows optional keys: `stack`, `queue`,
`list`, `tree`, `graph`, `grid`, `bits`, `intervals`, `board`, `vars` (named scalars — Kadane's
running best, min-stack's min). Rationale: side-by-side renderer composition (heap = TreeViz +
backing array; recursion = StateMachine + ArrayViz) requires one frame both renderers index.

**D5 — Predictions are trace-derived, never hardcoded.** Checkpoint = `{ at_step, occurrence,
prompt, derive, level }`; answers computed from the live event stream at gate time, so they
survive input tweaking. Derive functions are a shared library (§7), not per-lesson code.

**D6 — Explain-this-frame is pure client-side derivation, no LLM.** Frame + lesson model already
carry everything: `activeOp` (what), `invariant` (why correct), `repeated_decision` (why this
choice), next frame's caption (what's next). Zero latency/cost, works for guests. An LLM-backed
"ask anything about this frame" layers on the same derived context later (M8) — the derivation is
its grounding either way.

**D7 — Code panel ships early (M2), multi-language from the start.** Python/Java/C++/JS authored
per lesson, all keyed to shared `step_id`s via `lineMap`, so the animation highlights the right
lines in whatever language is selected. Step-synced multi-language is a headline competitive
feature — no competitor has it. Placement honors the teaching philosophy: the panel is
collapsed-by-default below the viz (code is step ~9-adjacent, never the centerpiece), but it
exists on every lesson. Code is **authored and reviewed, never generated from the model**
(architecture-doc decision, restated because Antigravity will be tempted).

**D8 — Inputs: free-form wherever parseable, presets alongside everywhere.** Arrays/strings keep
free text (live). Linked lists take arrays. Trees take level-order arrays with `null`s. Grids
take rows of numbers. Graphs take an edge-list mini-grammar (`A-B, B-C, C-A` / `A-B:4` for
weights) — validated with inline errors, never silent failure. Every complex structure *also*
ships 3–4 curated preset buttons (best case / worst case / edge case), because for a beginner the
point of tweaking is "does my mental model survive a different input", and presets guarantee
instructive ones. Size caps keep traces readable, with a visible "input capped" note: bars ≤12,
string ≤14 (both live today), stack/queue ops ≤20, list ≤10 nodes, tree ≤15 nodes, graph ≤10
nodes/16 edges, grid ≤8×8, board ≤8×8.

**D9 — The Player becomes the core learning surface for DSA, but stays a component.** Two
permanent boundaries: it never owns retention (recall targets the model — invariant, complexity,
trace-a-step, pattern — and flows through the existing FSRS bridge), and it never owns prose
(`LessonView` owns the five-questions lesson shape; the Player mounts inside it, and lessons
without `viz` must render forever — that's what lets content lead visuals).

**D10 — Pattern graph = a pattern-recognition aid backed by a dependency data structure, NOT a
roadmap visualization.** Pattern (algorithm family: Divide & Conquer, Sliding Window) is distinct
from mental model. Three jobs, in priority order: (1) "where else does this idea appear?"
cross-links on every lesson; (2) pattern-level FSRS recall ("which pattern fits this problem?" —
what the phase-20 capstone trains); (3) pattern-level analytics (miss MERGE predictions across
multiple D&C algorithms → recommend the pattern, not "redo merge sort"). Reuses the existing
`roadmap_node_prerequisites` tables; pattern nodes become first-class with edges to instances. A
ReactFlow "constellation view" is possible later; jobs 1–3 need only lesson sections + review
cards + the miss log.
What it is **NOT**: not roadmap sequencing, not a prerequisite hierarchy (patterns don't gate
progress), and not recommendation logic (analytics *consumes* it; the graph itself is inert
data). It is only the transferable-pattern layer — edges say "same idea appears here", nothing
more. Keeping it inert is what lets three different features share it without coupling.

## 5. Milestone plan

Each milestone = infra (generators/renderer/compiler/Player, Claude-owned) followed by that
phase's content batch (Antigravity-authored against the contracts, Claude-critiqued). Milestones
are sequential dependencies; within one, workstreams parallelize.

**Every milestone has two exits, and both must pass:** an *implementation exit* (renders, gates,
goldens green) and an *educational exit* (a learner-can statement, verified by actually walking
the lesson — proof of teaching quality, not just rendering correctness). A milestone whose viz
renders perfectly but whose predictions nobody can reason about is not done.

### M0 — Hygiene (hours, do first)
- `npm run golden` in `frontend/package.json` running every `generators/*.golden.mjs` (the files
  exist; no runner entry does).
- Family-reducer refactor of `compile.js` (D3) with frame-snapshot goldens proving zero drift.
- Verify dark-mode: the Player uses hex-literal Tailwind utilities (`bg-[#0F172A]`) — confirm the
  `index.css` override layer remaps them under `html.dark`; if not, tokenize the Player palette now.
- **Exit:** goldens green via one command; frames byte-identical pre/post refactor; Player correct
  in dark mode.

### M1 — The retrieval gate
- **Predict-before-reveal** (§7): schema, derive library, gate UI (choice buttons + short typed
  answers for derive-checkable levels; self-graded reveal for invariant/what-if prompts), graceful
  skip when a step doesn't occur for the current input.
- **Explain-this-frame** (§8) on every renderer via the Player shell.
- Content pass on the 12 live lessons: add `predictions` (1–3 each, mixed levels) +
  `repeated_decision`. Validator: predictions shape, `at_step` resolves to a real `step_id`,
  `derive` ∈ library registry; `repeated_decision` required on viz lessons.
- **Exit:** all 12 lessons gate ≥1 prediction; tweaking input changes expected answers; explain
  panel renders op/invariant/decision/next on every frame.
- **Educational exit:** a learner who missed a prediction can, from the explain panel alone, say
  *why* the actual step happened (invariant + repeated decision) without re-reading the lesson.

### M2 — Code panel + close phases 1–7 completely
- **Code panel** (D7): collapsed-by-default section under the viz; language tabs
  (Python/Java/C++/JS); current step's lines highlighted via `lineMap`; scrubbing moves the
  highlight. Schema: `code: { [lang]: { src, lineMap: { [step_id]: [lines] } } }`; validator
  checks lineMap keys ⊆ the generator's step_ids and ≥1 language present. Content pass: author
  code for the 12 live lessons (Python first, other languages may trail within the milestone).
- Generators: **lower-bound**, **upper-bound** (binary-search variants: same WINDOW/POINT ops,
  different invariant + landing rule), **binary-search-on-the-answer** (two synced rows: candidate
  answer space + monotone true/false predicate row — ArrayViz twice), **anagrams** (StateMachine
  map panel gains two-maps-side-by-side; COUNT gets a `map_id` arg), **pattern-matching-KMP**
  (bespoke: pattern row sliding under text row + prefix-function table; new ops
  `SHIFT_PATTERN, TABLE_FILL, TABLE_LOOKUP`; the aha = *watching the pattern jump instead of
  restart*).
- **Exit:** every phase 1–7 lesson has golden-tested viz + predictions + code; KMP's shift-jump
  gates an "how far does the pattern slide?" prediction.
- **Educational exit:** a learner can state the lower-bound vs upper-bound landing rule in their
  own words, and can predict the KMP slide distance from the prefix table on a fresh input.

### M3 — Phase 8: Two Pointers & Windows (zero new renderers)
- Generators: two-pointers (pair-sum converge), fast-slow-pointers (two speeds on a sequence;
  cycle version returns in M4 on lists), sliding-window-fixed, sliding-window-variable
  (WINDOW op exists; window-sum/constraint into `vars`), kadane (running best in `vars`).
- Compiler: `vars` slice → StateMachine renders named scalars as labeled boxes.
- Content batch: phase 8 (5 nodes).
- **Exit:** 5 golden-tested generators; Kadane's running best updates against the bars;
  variable-window gates an "expand or shrink?" prediction (the `repeated_decision` itself).
- **Educational exit:** learner correctly predicts at least one Kadane keep-or-restart decision
  and one expand-or-shrink window decision on an input they typed themselves.

### M4 — Phases 9–10: Stacks & Queues + Linked Lists
- **StackQueueViz**: vertical stack (push/pop animate at the top) + horizontal queue (enqueue
  right, dequeue left) + deque. Compile the declared `PUSH/POP/ENQUEUE/DEQUEUE` into
  `stack`/`queue` slices. Generators: valid-parentheses (stack + input string side-by-side),
  min-stack (two stacks), monotonic-stack, next-greater-element, queue-deque.
- **LinkedListViz**: boxes with arrow pointers; the aha = *watching an arrow retarget*. New
  family `list: [L_POINT, SET_NEXT, DETACH, ATTACH]` → slice `{ nodes:[{id,value}],
  next:{id→id|null}, pointers:{name→id|null} }`. Generators: traversal+reversal, find-middle,
  floyd-cycle-detection (cycle drawn as a loop-back arrow), merge-two-sorted-lists,
  **reverse-in-k-groups** (full viz — the relink choreography is exactly what beginners can't
  picture; that's the argument *for* building it, not against).
- Content batches: phases 9–10 (11 nodes).
- **Exit:** reversal shows arrows flipping one at a time under the three-pointer invariant;
  parentheses gates "push or pop?"; k-group reversal scrubs cleanly at ≤10 nodes.
- **Educational exit:** learner can name the three pointers in list reversal and predict which
  arrow retargets next; can predict push-vs-pop for any bracket in a fresh string.

### M5 — Phases 11–13: Recursion, Backtracking, D&C sorts (make-or-break for the audience)
- **TreeViz v1** (one renderer, many clients): generic node-edge tree, tidy autolayout
  (d3-hierarchy acceptable — lazy chunk only), per-node highlight + annotation. First client:
  the **recursion tree** (CALL adds a child; RETURN annotates the node with its value — read
  complexity off the shape). Generators: call-stack demo (factorial/sum), recursion-tree
  (fib — deliberately shows overlapping-subproblem duplication that DP later kills).
- Backtracking: compile declared `CHOOSE/UNDO` → decision-path highlight + prune marks in
  TreeViz. Generators: subsets (include/exclude tree), permutations (used-set in `vars`),
  combination-sum, **n-queens** with a **BoardViz** (n×n grid; queens placed, attacked squares
  shaded, backtrack un-places — the single most shareable/demo-able visual in the roadmap;
  ops `PLACE, REMOVE, ATTACK_MARK` → `board` slice).
- D&C sorts: quick-sort (partition dance = ArrayViz + pointers), counting-sort (counts array +
  output array — ArrayViz twice).
- Content batches: phases 11–13 (12 nodes).
- **Exit:** fib tree visibly duplicates subtrees; "which call returns next?" gates; N-Queens
  backtrack visibly un-places and re-tries; quick-sort partition gates a pointer prediction.
- **Educational exit:** learner can point at the duplicated fib subtree and say why it motivates
  memoization; can predict the next choose/undo in subsets; can say which queen gets removed on
  a dead-end row before the backtrack plays.

### M6 — Phases 14–19: Trees, Heaps, Graphs, Greedy, DP, Bits (three sub-batches)
- **M6a Trees + Heaps:** TreeViz v2 — BST insert/search path highlight, traversal-order badges,
  bounds annotations (validate-BST), LCA path pair, height/diameter annotations. Heap = TreeViz +
  ArrayViz side-by-side (the array IS the tree — the aha). Ops: `T_VISIT, T_ATTACH, T_ANNOTATE,
  SIFT_SWAP`. Generators: all 8 tree nodes + binary-heap, heap-sort, top-k.
- **M6b Graphs:** **GraphViz reusing ReactFlow** (already a dep — no new graph lib). Compile
  declared `VISIT/MARK_VISITED/RELAX/ENQUEUE_NODE` → `graph` slice (visited set, frontier,
  dist/parent tables); queue/stack/PQ side panel = StackQueueViz reuse; dist table = `vars`.
  Edge-list input grammar + presets (D8). Generators: BFS, DFS, when-BFS-stops-working (weighted
  counterexample), connected-components (grid flood-fill variant welcome), cycle-detection
  (directed + undirected), topo-sort, Dijkstra (PQ panel is the teaching core), union-find
  (forest → TreeViz reuse; path compression animates the re-parent), Kruskal (union-find + edge
  list sorted by weight).
- **M6c Greedy + DP + Bits:** **GridViz** (`FILL_CELL/MEMO_WRITE/MEMO_HIT` → `grid` slice;
  **cell-dependency arrows on fill** — the most valuable DP visual). Memoization lesson = M5's
  fib recursion tree + memo table side-by-side, `MEMO_HIT` visibly pruning subtrees — the payoff
  of the M5 setup. Generators: all 6 DP-thinking nodes + the 8 example problems (climbing-stairs,
  house-robber, coin-change, knapsack, LCS, edit-distance, LIS, grid-DP). Greedy: jump-game
  (ArrayViz furthest-reach), **NumberLineViz** for interval-scheduling + merge-intervals
  (ranges on an axis; select/merge animations); why-greedy-works/fails = conceptual lessons with
  a counterexample trace each (greedy path vs optimal path, side by side — traces make the
  failure *visible*, which prose can't). Bits: **BitViz** = ArrayViz char-cell mode rendering
  fixed-width 0/1 cells; XOR cancellation + shift + Kernighan as cell ops.
- Content batches: phases 14–19 (~44 nodes).
- **Exit per sub-batch:** BST insert gates "left or right?"; Dijkstra gates "which node pops
  next?"; DP tabulation gates "what value fills this cell?"; memoization shows subtree pruning.
- **Educational exit per sub-batch:** learner can predict the BST descent path for a value they
  chose; can predict Dijkstra's next popped node from the PQ panel; can fill one DP cell from its
  dependency arrows before the reveal and state the transition in words.

### M7 — Capstone + the moat features
- Phase 20 content (Algorithm Design Patterns — mostly conceptual + the pattern-recognition
  drill, which reuses predictions machinery: show a problem statement, gate on "name the
  pattern", reveal the mapping).
- **Pattern graph** (D10): pattern nodes + edges in `roadmap_node_prerequisites`; "this pattern
  appears in…" section on every viz lesson; pattern-level recall cards through the existing
  add-to-reviews bridge.
- **Reference mode**: fast scrub, no READ_DELAY, no gates — a toggle in the Player. For
  pre-interview revision (parity with VisuAlgo's replay value).
- **Operation/pattern-level analytics**: log prediction outcomes `{lesson, step_id, op, pattern,
  level, committed, correct}` (client-side first; a small backend endpoint + table when the
  funnel design lands). Recommendation: repeated misses on an op family across pattern instances
  → surface "review the pattern" on Home.
- **Exit:** capstone drill live; a learner who misses merge predictions in merge-sort AND
  binary-search sees a Divide & Conquer review suggestion.
- **Educational exit:** given a fresh problem statement in the capstone drill, learner names the
  correct pattern before seeing code — the interview superpower, verified end-to-end.

### M8 — Beyond parity (queued, not speculative)
LLM "ask anything about this frame" grounded in the derived explain context (Groq, same gating
pattern as the grader) · shareable frame permalinks (`?step=n`) for social/SEO · mobile-tuned
layouts for TreeViz/GraphViz (scale-down + pan) · additional languages in the code panel.

## 6. Layer contracts (what each layer may and may not do)

The pipeline stays honest only if each layer refuses to do the next layer's job. These contracts
exist to be cited in review when a change blurs them.

### 6.1 Renderer contract
A renderer is a **pure, deterministic function `frame → UI`**. It must never:
- derive algorithm state (that's the generator's job),
- interpret raw events or reach past its frame (that's `compile()`'s job),
- mutate frames or hold algorithm state across renders,
- contain teaching or business logic (predictions, gating, explain, analytics — all Player).

Mechanics: props = `{ frame }` only; renders an empty state (never crashes) when its slice is
absent; stable visuals per frame index; lazy DSA chunk only — zero bundle cost elsewhere. If a
renderer "needs" information the frame doesn't carry, the frame slice is wrong — fix the reducer,
don't compute in the renderer.

### 6.2 Generator quality contract
A generator is where teaching quality is won or lost — the trace IS the lesson's spine. A good
generator emits:
- a **minimal** event stream: every event teaches something (a decision, a state change worth
  seeing); no cosmetic or noisy events (loop-counter increments, redundant repaints),
- **stable `step_id`s**: they are the anchor for predictions, lineMaps, and analytics — renaming
  one silently breaks all three,
- **deterministic** output: a pure function of input, no randomness, no clock,
- correct traces for **arbitrary valid inputs** within its declared caps (not just the default
  input — goldens should include an edge input: empty/single-element/duplicates/already-sorted),
- **recoverable invariants**: at every event, the lesson's invariants must actually hold on the
  materialized state — an invariant the trace violates mid-stream is a generator bug, not a
  content bug.

### 6.3 Compiler philosophy
`compile()` **only translates semantic events into renderer-ready state.** It must never:
- invent information not present in the event stream,
- infer decisions the generator didn't emit (if a visual needs a decision, the generator emits it
  as an event),
- repair incomplete or inconsistent event streams (a broken trace should look broken — silent
  repair hides generator bugs and mis-teaches).

Unknown ops degrade gracefully (caption + invariant frame) — that is fallback *presentation*, not
repair.

### 6.4 Renderer inventory

| Renderer | Frame slice | Milestone | Notes |
|---|---|---|---|
| StackQueueViz | `stack` / `queue` | M4 | Also the queue/PQ side panel for graphs |
| LinkedListViz | `list` | M4 | Arrow retargeting is the point; cycles draw loop-back |
| TreeViz | `tree` | M5 | Recursion tree, backtracking, BST, heap, union-find forest |
| BoardViz | `board` | M5 | N-Queens (and future grid-placement problems) |
| GraphViz | `graph` | M6b | ReactFlow reuse; edge-list grammar + presets |
| GridViz | `grid` | M6c | DP tables; dependency arrows on fill |
| NumberLineViz | `intervals` | M6c | Greedy intervals |
| BitViz | via char cells | M6c | ArrayViz mode, not a new component |

## 7. Prediction system (spec)

Lesson schema addition (inside `viz`):
```json
"predictions": [
  { "at_step": "merge", "occurrence": "last",
    "prompt": "The next TWO values written during this merge?",
    "derive": "next_n_writes(2)", "level": "medium" }
]
```
- **Derive library** — pure functions over `(events, gateIndex)`, answers computed at gate time
  from the live trace: `next_n_writes(n)`, `next_op()`, `pointer_after(name)`,
  `next_swap_pair()`, `branch_taken()` (left/right, push/pop, take/skip, expand/shrink),
  `value_at(index)`, `cell_value(r,c)`, `next_node_popped()`. Grow per milestone; each function
  registers itself so the validator can check `derive` references.
- **Gate behavior:** Player pauses when playback first reaches the checkpoint; learner commits
  (choice buttons or short typed answer per derive type) or taps "show me"; stepping reveals —
  the reveal IS the real trace, never stored. Scrubbing/stepping backwards never re-gates; gates
  fire once per (input, checkpoint), re-arming on input change or Replay.
- **Levels** (progressive): easy = next step · medium = pointer/state after the op · hard = state
  the invariant · expert = what-if. Easy/medium are derive-checked; hard/expert render as
  commit-then-compare (self-graded reveal). All four levels ship — self-graded commitment is
  still retrieval practice.
- **Edge cases:** `at_step` absent for the current input → skip silently; `occurrence:"last"`
  with zero occurrences → skip; input tweak → recompute gates; guests → fully client-side.
- **Post-miss hook:** a wrong prediction surfaces the explain-this-frame panel automatically —
  the highest-value teaching moment.

## 8. Explain-this-frame (spec)

**Inline by default — NOT behind a "Why?" button.** Hiding the teacher behind a click contradicts
the philosophy (the teacher should dominate, not be opt-in). The explanation of the CURRENT frame
is always visible in/under the commentary, derived entirely from existing data:
1. **What just happened** — `activeOp` + caption.
2. **What changed** — a one-line frame diff vs. the previous frame (pointer moved, value written,
   range finalized) — the "reflection" beat, derived from consecutive frames.
3. **Why it's allowed/correct** — resolved invariant text.
4. **Why this choice** — the lesson's `repeated_decision` (required field from M1 on).
5. **What happens next** — next frame's caption, phrased as "next: …".

No authoring beyond `repeated_decision`; no network. The ONLY gated line is #5 "what happens next":
it stays hidden while a prediction gate is open (it would spoil the commit) and reveals after the
learner commits or steps. #1–4 are always shown. After a missed prediction, the panel draws
attention (highlight) rather than needing to be opened — nothing to open, it's already inline.

**Rule: never reveal future information except inside the explicit "What happens next" section.**
Rows 1–3 must be computable from the current frame + model alone. This matters because explain
coexists with prediction gates — an explain panel that leaks the upcoming write or branch answers
the open prediction and destroys the retrieval effect. (Corollary: while a gate is open, the
"next" row is hidden or replaced with "commit your prediction first".)

## 9. Governance (protecting the canon as contributors and features grow)

The trace is a public API inside the project. These rules exist so that growth (new generators,
new features, Antigravity batches, future AI) cannot silently corrupt it.

### 9.1 Event schema versioning
`events.js` exports `EVENT_SCHEMA_VERSION` (integer, starts at 1). Rules:
- **Additive changes** (new op in a family, new op family, new optional arg) do NOT bump the
  version — graceful-fallback already absorbs them.
- **Semantic changes** (an existing op's meaning, required args, or state effect changes) REQUIRE
  a version bump + a migration note in this doc + regeneration of every golden that emits the op.
  Goldens record the version they were generated under; a version mismatch is a test failure, not
  a silent pass.
- Never reuse an op name with different semantics — add a new op and retire the old one.

### 9.2 Lesson compatibility contract (Generator ↔ Lesson ↔ Player ↔ Renderer)
When a generator changes, this table says what must be regenerated. CI/validator should enforce
the mechanical rows; the rest is review discipline.

| Generator change | Must regenerate / re-verify |
|---|---|
| `step_id` renamed or removed | goldens · lesson `predictions.at_step` · `code[lang].lineMap` keys · analytics keys (breaks history — see 9.4; avoid) |
| Event semantics changed | version bump (9.1) · goldens · re-walk affected lessons' predictions + explain output |
| Events added (additive) | goldens updated · downstream unaffected (fallback guarantees) |
| Emitted invariant ids changed | lesson `viz.invariants` map · explain panel re-verified |
| Input caps / transforms changed | goldens · lesson `default_input` re-validated · preset buttons re-checked |

### 9.3 Testing pyramid (localize failures by layer)
1. **Generator tests** (golden `.mjs`) — event correctness: known input → exact event stream,
   including one edge input. A failure here means the algorithm trace is wrong.
2. **Compiler/frame tests** — frame snapshots per family reducer: events → exact frames. A
   failure here means translation is wrong, not the algorithm.
3. **Renderer snapshot tests** — frame → stable UI (component snapshots on representative
   frames incl. the empty-slice state). A failure here is presentation-only.
4. **Educational tests** — prediction derive functions (trace + gate → expected answer) and
   explain derivation (frame + model → the four rows, incl. the no-future-leak rule while a gate
   is open). A failure here means the teaching layer is wrong even though everything renders.

### 9.4 Canonical IDs (immutable — treat as public API)
`step_id` · invariant ids · pattern ids · op names · generator keys. These are load-bearing
across goldens, predictions, lineMaps, review cards, and analytics history. Renaming one is a
*migration*, not an edit: it requires touching every consumer in 9.2 AND accepts breaking
analytics continuity. Default answer to "can I rename this id?" is no.

### 9.5 Backward compatibility (frames and lessons)
New renderer/frame slices are **additive only**: never rename or remove existing Frame keys,
never change an existing slice's shape. Existing lessons must keep working without modification
when infra ships — a milestone that requires editing shipped lessons (beyond adding new optional
fields like `predictions`) has broken this rule and needs a stated migration.

### 9.6 Analytics contract (consumers only)
Analytics reads traces, prediction outcomes, and pattern edges. It must never influence playback,
gate placement, prediction difficulty, explain output, or lesson behavior. Recommendations it
produces surface *outside* the Player (Home, review queue). Rationale: the teaching engine must
stay deterministic and inspectable — a feedback loop from analytics into playback makes lessons
irreproducible and bugs undiagnosable.

### 9.7 Future AI boundary (M8)
AI features explain or synthesize **from** canonical data (trace + model + derived explain
context); they never generate alternative traces, never simulate the algorithm themselves, and
never become a second source of truth. If AI output disagrees with the trace, **the trace wins**
and the disagreement is a prompt bug. AI output is advisory and labeled as such — same
convention as the live recall grader.

## 10. Edge cases & failure modes (system-wide)

- **Event explosion:** quadratic sorts at 12 elements ≈ 140 events (fine); D8 caps bound the
  rest. Generators assert caps and show "input capped" rather than silently mis-tracing.
- **Renderer/slice mismatch** (lesson names a renderer whose slice its generator never emits):
  renderer shows its empty state; validator addition — generators declare their families,
  validator cross-checks the lesson. Cheap insurance against authoring typos.
- **Unknown ops** degrade gracefully today (caption + invariant frame) — the reducer refactor
  must preserve this; it's what lets content occasionally lead bespoke visuals.
- **Pacing:** predictions add pauses on top of READ_DELAY/DWELL. If a 40-event trace + 3 gates
  exceeds ~4 minutes of forced pacing, cut events (narrate *decisions*, not increments) rather
  than shortening READ_DELAY. Reference mode (M7) is the pressure valve for returning users.
- **Input grammar errors** (graphs): inline, specific error messages ("`B-` is missing a target
  node") — a beginner must never conclude the tool is broken.
- **Mobile:** TreeViz ≥15 nodes and GraphViz need scale-down/pan — design at M5/M6 build time
  with real layouts; full mobile tuning is M8.
- **Dark mode:** hex-literal utilities in the Player — verified/fixed at M0.

## 11. Success metrics

1. **Learning-loop conversion (primary):** viz-lesson completion → "Add to reviews" rate vs
   prose-only DSA lessons. The direct test of the thesis that visualization drives the retention
   loop. Measurable today.
2. **Prediction funnel (created by M1):** gate shown → committed (vs "show me") → correct.
   Target >60% commit rate; a collapse on one lesson indicts that trace/prompt, per-lesson
   diagnosable.
3. **Learning outcomes:** FSRS recall accuracy on lesson-sourced cards (`recalled`/`quality`
   already persisted), read against the author exit criteria (predict a step, state the
   invariant, explain complexity, name the pattern, one real use, when not to use).
4. **Coverage as pace, not goal:** % of traceable nodes with golden-tested viz (12/~75 ≈ 16%
   today → 100% at M6, including the bespoke tail: KMP, N-Queens, BS-on-answer, k-groups).

Explicitly not metrics: DAU, streaks, time-in-app (per the motivation pillar), phase-completion
counts (completion is what competitors measure; we measure retention).

## 12. Implementation notes (for the implementing model)

1. **Never author or hand-edit frames** — fix the generator or reducer; frames are a cache.
   Golden tests are the contract: update goldens only when events intentionally change, and say
   so in the commit.
2. The M0 reducer refactor keeps `compile(input, events)`'s signature and output shape —
   `Player.jsx` and the renderers depend on it. Add slices; never rename existing frame keys.
3. Register every generator in `registry.js` AND land its golden `.mjs` in the same commit. A
   registered, untested generator fails *silently in the classroom* — golden-first.
4. Content batches go to Antigravity only after that phase's generators + renderers merge
   (validator dependency). Hand Antigravity: generator keys, emitted `step_id`s, available derive
   functions, invariant ids, and the code-authoring rules (D7) — it must not invent any of these.
5. Code is authored per language and reviewed — never generated from the model, never left to
   Antigravity without critique of the `lineMap` (a wrong line highlight mis-teaches silently).
6. New viz deps (d3-hierarchy for TreeViz layout, if used) stay inside the lazy DSA chunk;
   GraphViz reuses ReactFlow — do not add a graph library.
7. `LessonView.jsx` must keep rendering lessons without `viz` forever (prose leads bespoke
   visuals during a phase's build window).
8. When touching `Player.jsx`, preserve commentary-before-animation pacing (read → then watch) —
   deliberate teaching design, not an artifact. Reference mode toggles it off; Teaching mode
   never loses it.
9. Commits are authored solely by the user — no `Co-Authored-By` trailer (project convention).
10. Review checklist for any DSA PR: does it violate D0 (educational behavior not derived from
    the trace)? Does it blur a §6 layer contract (renderer computing state, compiler inventing
    information, generator emitting noise)? Does it touch a canonical ID or event semantics
    without following §9? Cite the section when rejecting — these boundaries are the
    architecture; the roadmap is just the schedule.
