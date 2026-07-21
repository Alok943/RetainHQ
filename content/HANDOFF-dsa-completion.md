# DSA roadmap — completion handoff (the leftovers)

State as of 2026-07-21, verified against the tree (not against docs):

- **Content:** 95/110 nodes authored. Phases 16-20 are content-complete (41/41, pass 1).
  **All 15 open nodes sit in phases 1-15**, and 5 of them are phase 8.
- **Viz:** 24 generators in use, 5 orphaned, **21 not built**. Four separate pass-0 contract
  defects block the unbuilt ones.
- `validate.py` is clean and has been throughout — none of the below is caught by the gate.

Three tracks. **Order matters: A blocks C. B is independent and can start immediately.**

| track | owner | blocked by | scope |
|---|---|---|---|
| **A** — pass-0 contract fixes | **Claude** | nothing | 4 phases' renderer/compiler defects |
| **B** — phase 8 content + viz | **Antigravity** | nothing | 5 lessons, generators already exist |
| **C** — pass-2 generators | **Antigravity** | **track A** | 21 generators, phases 16-19 |

---

# Track B — Phase 8: Two Pointers & Windows (START HERE)

**Do this first.** It is unblocked, it is the only remaining phase whose viz infra is already
built, and it closes a live defect: phase 20's `recognizing-two-pointers` and
`recognizing-sliding-window` declare these five nodes as prerequisites, so **five prerequisite
edges currently dangle** (validator warns, does not error — it has been passing silently).

## The 5 nodes

Titles/difficulty from `backend/seed_dsa.py` (phase `"Two Pointers & Windows"`) — authoritative,
do not invent. Slugs from `content/_TODO-dsa.md`.

| slug | title | section | difficulty | generator key |
|---|---|---|---|---|
| `two-pointers` | Two pointers | Pointers | easy | `two-pointers` |
| `fast-and-slow-pointers` | Fast & slow pointers | Pointers | medium | **`fast-slow-pointers`** |
| `sliding-window-fixed` | Sliding window (fixed) | Windows | medium | `sliding-window-fixed` |
| `sliding-window-variable` | Sliding window (variable) | Windows | medium | `sliding-window-variable` |
| `kadane-s-algorithm` | Kadane's algorithm | Arrays | medium | **`kadane`** |

> **TRAP — generator key != slug for two of the five.** `viz.generator` must be the **registry
> key**, not the lesson slug: `fast-slow-pointers` (not `fast-and-slow-pointers`) and `kadane`
> (not `kadane-s-algorithm`). `validate.py` checks the key against
> `frontend/src/dsa/registry.js` and will reject the slug form.

All 5 are **`kind: "dsa"`** trace nodes. No concept nodes in this phase.

## This phase ships WITH `viz` blocks — unlike phases 16-20

All five generators already exist in `frontend/src/dsa/generators/` and are registered. They emit
only array-family ops (`POINT`, `MARK`, `WINDOW`, `VAR`, `DONE`) through the long-proven
`arrayReducer` + `ArrayViz` path. **Nothing needs fixing here.** Do not write new generators.

Read each generator before authoring its lesson — the hand-trace in the prose and the generator's
`default_input` must show the SAME walkthrough, or the lesson and the animation contradict.

**Predictions — use only these registered derives** (`validate.py` parses `DERIVES` in
`predict.js` and rejects anything else):

| node | suggested derive | why it fits |
|---|---|---|
| `two-pointers` | `next_op` | does the next move advance left, advance right, or finish? |
| `fast-and-slow-pointers` | `next_op` / `next_step_id` | do the pointers meet on this step? |
| `sliding-window-fixed` | `next_op` | does the window slide, or is the answer recorded? |
| `sliding-window-variable` | **`branch_window`** | purpose-built: reads the WINDOW before/after the gate to decide expand vs shrink |
| `kadane-s-algorithm` | **`next_step_id`** | purpose-built for Kadane's extend-vs-restart (see the comment on it in `predict.js`) |

Copy the `viz` block shape from `content/roadmaps/dsa/two-pointers-on-strings.json` (closest
sibling — same array-family ops, 1 prediction) or `merge-sort.json` (2 predictions). Both verified
to carry a working `viz` block.

## Prose requirements

Follow `content/PROMPT-dsa.md`. Copy the shape of `content/roadmaps/dsa/merge-sort.json` (the gold
`dsa` exemplar) — and unlike the phases 16-20 packets, **keep its `viz` block** this time.

Required `dsa` fields: `why_it_exists {problem, better_idea}`, `mental_model {intuition,
repeated_decision, ...}` (**`repeated_decision` is REQUIRED and validator-enforced once a `viz`
block exists**), `explanation` OR `sections` (teaching body **with a concrete hand-trace**),
`common_mistakes` (>=1), `recall_questions` (>=3), `oa_questions` (>=2), `sources` (2-5 URLs).

**The hand-trace is the deliverable, not decoration.** Phase 18 shipped 6 of 8 trace nodes without
one and needed a second pass. Every node below gets a numbered walkthrough on a 5-7 element array
with real values, every intermediate value shown. Verify each by computing it — a wrong cell
teaches a wrong algorithm.

### Per-node must-hits

**`two-pointers`** (easy) — `repeated_decision`: *"is the current pair's sum too big (move right
in) or too small (move left in)?"*
- Opposite-end convergence on a **SORTED** array. State the sortedness precondition loudly — it is
  the entire reason the technique is correct.
- **Why a move is safe:** if `a[lo] + a[hi]` is too large, no pair using `a[hi]` can work (every
  remaining partner is >= `a[lo]`), so the whole column is discarded — that is how `O(n^2)` becomes
  `O(n)`. This safety argument is the lesson.
- `O(n)` time, `O(1)` space. Contrast honestly with the hash-map approach (works unsorted, costs
  `O(n)` space).
- Misconception: applying it to an unsorted array.

**`fast-and-slow-pointers`** (medium) — `repeated_decision`: *"advance slow by one and fast by two
— did they land on the same node?"*
- Floyd's tortoise and hare. Two uses: **cycle detection** and **find the middle** (when fast hits
  the end, slow is at the midpoint). Name both; trace one.
- **Why they must meet inside a cycle:** once both are in the loop, the gap closes by exactly one
  per step, so meeting is guaranteed — it cannot be jumped over. Say this; it is the non-obvious part.
- `O(n)` time, `O(1)` space vs the hash-set alternative's `O(n)` space.
- Misconception: assuming the meeting point is the cycle's START (it is not — finding the entry
  needs the second phase; name it, don't co-teach it).

**`sliding-window-fixed`** (medium) — `repeated_decision`: *"slide the window one step: which
element leaves, which enters, and what does that do to the running total?"*
- Fixed size `k`. The point: **do not recompute the whole window** — subtract the outgoing element,
  add the incoming one. `O(n*k)` becomes `O(n)`.
- Misconception: rebuilding the sum each slide (the exact waste this pattern exists to remove).

**`sliding-window-variable`** (medium) — `repeated_decision`: *"does the window still satisfy the
constraint — expand right if not yet violated, shrink from left if violated?"*
- The window grows and shrinks; both pointers only ever move **forward**, which is why it stays
  `O(n)` despite the nested-looking shape. State that explicitly — it is the part that reads as
  quadratic but is not.
- Cross-link `recognizing-sliding-window` (phase 20) — that node cites this one as a prerequisite.
- Misconception: resetting `left` back to the start after a violation (turns it `O(n^2)`).

**`kadane-s-algorithm`** (medium) — `repeated_decision`: *"extend the current subarray with this
element, or restart the subarray from it?"* -> `current = max(nums[i], current + nums[i])`.
- Maximum subarray sum. Two running values: `current` (best ending HERE) and `best` (best seen
  anywhere). Keep them distinct — conflating them is the classic bug.
- **The DP connection:** this is a 1D DP with the table collapsed to one variable — cross-link
  phase 18's `space-optimization` and `state-and-transition`.
- **The all-negative case is the trap:** initialize `best` to `nums[0]`, not `0`, or an
  all-negative array wrongly returns `0`. Put this in `common_mistakes`.
- Trace an array with negatives, e.g. `[-2, 1, -3, 4, -1, 2, 1, -5, 4]` -> `6`.

### Also required for this track

**Write the 5 missing goldens.** All five generators ship with **no `*.golden.mjs`** — they are the
only registered generators without one. Add `frontend/src/dsa/generators/<key>.golden.mjs` for each,
copying `combination-sum.golden.mjs`'s shape: assert determinism (generating twice is byte-identical),
one frame per event, every frame has an `activeOp`, and the algorithm's final answer matches a
hand-computed value. `npm run golden` green.

### Then

`python content/validate.py` -> zero errors. Tick the 5 boxes in `content/_TODO-dsa.md` **and update
its summary line** (currently "95 done / 15 open" -> becomes 100/10). Confirm the phase-20 dangling
edges resolve: re-run validate and check the `not curated yet` warnings for `two-pointers`,
`sliding-window-fixed`, `sliding-window-variable`, `kadane-s-algorithm`,
`fast-and-slow-pointers` are gone.

**Do NOT commit and do NOT push.** Report back with the changed-file list and validate's final line.

---

# Track A — pass-0 contract fixes (Claude only)

Four phases, all verified present in the current tree. Full per-defect detail lives in each phase's
handoff doc; this is the consolidated worklist and the order to do it in.

**1. Phase 17 — one line.** `IntervalViz.jsx:9,26` destructures `frame.intervalTags` and looks up
`intervalTags[inv.id]`; `compile.js` never emits that key. `intervalsReducer` already writes the tag
onto the interval object itself (`intv.state`), and `compile.js:454` copies intervals onto every
frame. Fix: read `inv.state`. Details: `HANDOFF-dsa-phase17-greedy.md` "Pass 0".

**2. Phase 16 — six defects, the graph pipeline has never rendered.** Frame-key mismatches
(`GraphViz.jsx:15` reads `nodeTags`, `:102` reads `frame.cursor`; compile emits `graphNodeTags` /
`graphCursor`), edge tags never merged onto edges, the `SET_EDGE` reducer collision (`treeReducer`
claims it unconditionally with no guard — confirmed, its switch opens straight on `TREE_INIT`),
`ENQUEUE_NODE`'s tag missing from the renderer's colour map, the unresolved `RELAX` convention, and
no graph derives. Details: `HANDOFF-dsa-phase16-graphs.md` "Pass 0".

**3. Phase 19 — five defects, this one CRASHES.** `compile.js:358` sets `state.bits = { numbers: [...] }`
(an object) while `BitsViz.jsx:9` destructures it as an array and calls `.map()` — a defined object
defeats the `= []` default, so this throws `TypeError`, it does not merely misrender. Plus the
`bitsActiveCol`/`activeCol` name mismatch, `bitTags` never emitted, `SET_BIT` a no-op stub, and no
derives. Details: `HANDOFF-dsa-phase19-bit-manipulation.md` "Pass 0".

**4. Phase 18 — four items.** No `dpReducer` exists at all (`REDUCERS` has no entry; `MEMO_WRITE` /
`MEMO_HIT` are declared in `events.js` but dead), no derive can read a `FILL_CELL` so the 4 grid DP
nodes cannot have prediction checkpoints, `FILL_CELL` is double-declared in both the `grid` and `dp`
families, and no golden covers either family. Details:
`HANDOFF-dsa-phase18-dynamic-programming.md` "Pass 0".

Each phase: fix, then `npm run golden` (the backtracking goldens are the regression net for the
`treeReducer` and `gridReducer` changes), then browser-verify one lesson actually renders — goldens
cannot catch a JSX crash, which is precisely phase 19's failure mode.

---

# Track C — pass-2 generators (Antigravity, blocked on Track A)

**21 generators, none started.** Do not begin a phase until its Track-A fix has landed — several
would produce traces that are silently wrong (phase 16: every node white, no edge highlights) or
that crash on first render (phase 19).

| phase | count | keys |
|---|---|---|
| 16 | 8 | `bfs-on-graphs`, `dfs-on-graphs`, `connected-components`, `cycle-detection`, `topological-sort`, `dijkstra`, `union-find`, `kruskal` |
| 17 | 3 | `interval-scheduling`, `merge-intervals`, `jump-game` |
| 18 | 8 | `climbing-stairs-fibonacci`, `house-robber`, `coin-change`, `0-1-knapsack`, `longest-common-subsequence`, `edit-distance`, `longest-increasing-subsequence`, `grid-dp-unique-paths-min-path-sum` |
| 19 | 2 | `single-number-xor`, `counting-bits` |

Per-generator ops, default inputs, the moment each viz must sell, and golden requirements are
already specced in each phase's handoff doc under "Pass 2". Follow those; this table is only the
index and the ordering constraint.

**Recommended order:** 17 (3 generators, one-line pass-0, lowest risk — use it to shake out the
workflow) -> 18 (8, infra mostly proven) -> 16 (8, hardest) -> 19 (2, needs the most pass-0 work).

---

# Standing rules (all tracks)

- **Do not commit. Do not push.** This was violated on the phase-17 batch (committed and pushed to
  `main`) — Claude reviews before anything lands.
- **ASCII only in lesson JSON.** `--` not an em-dash, `*` not a multiplication sign, `->` not an
  arrow. This has now regressed twice (phase 18: 5 files; phase 19: 2 files).
- **Sources: primary first.** Wikipedia / CLRS / university course pages / official language docs.
  Not medium.com, dev.to, or content-marketing blogs. Phase 20 initially shipped citing an
  AI-copilot marketing page on its capstone node. **Every URL must be opened and checked** for
  relevant coverage before citing — a plausible-looking Wikipedia URL was found returning 404
  during the last review.
- Generator boundaries: touch only `frontend/src/dsa/generators/*` + `registry.js`. `compile.js`,
  `events.js`, `predict.js` and the renderers are Claude-owned shared contract (Track A).
- If the spec fights reality, implement the closest faithful version and **FLAG it** in
  `content/REPORT-dsa-<track>.md` — do not silently redesign.
