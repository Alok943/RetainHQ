# Implementation spec — M4 phase 9: StackQueueViz + stack/queue generators

**For Antigravity (Gemini 3.1 Pro) to implement. Claude authored this; Claude verifies the result
against the golden tests + a live browser pass — NOT against your walkthrough.** Repo:
`C:\Users\aloks\Desktop\RetainHQ`. Read `docs/dsa-viz-implementation-plan.md` §5 (M4), §6 (layer
contracts), §9 (governance) FIRST — they are binding. Read these files before writing:
`frontend/src/dsa/events.js`, `compile.js` (per-family reducers), `renderers/StateMachine.jsx`,
`renderers/ArrayViz.jsx`, `Player.jsx`, `registry.js`, `generators/binary-search.js` +
`generators/windows-family.golden.mjs` (style templates), `compile-frames.golden.mjs`.

## Non-negotiable contracts (from §6/§9)
- **Frames are a stable contract.** New frame keys are ADDITIVE and ONLY present when non-empty
  (like `vars` today: `Object.keys(x).length ? {...x} : undefined`). NEVER rename/remove existing
  keys — the byte-identical guard (`compile-frames.golden.mjs`) must show only ADDED generator keys.
- **Generators are pure, deterministic, golden-tested.** Minimal event stream, stable step_ids,
  cap input length, graceful on empty/tiny input.
- **Renderer contract:** `frame → UI`, pure, renders empty state (never crashes) when its slice is
  absent, no algorithm logic. **Guard every lookup** (the M3 `VariablesSection` crashed all lessons
  from a missing null-guard — do not repeat it).
- **Unknown ops still render** (caption + invariant). Do not break graceful fallback.

## Part A — compiler + frame slices

`events.js` already declares `stack: ['PUSH','POP','ENQUEUE','DEQUEUE']`. Compile them.

Add a `stackReducer` in `compile.js` (new reducer in the REDUCERS array, after scalarReducer):
- state init gains: `stack: []`, `queue: []`, `stackTop: null` (index of the just-changed cell), `queueEnd: null`.
- `PUSH {value}` → `state.stack.push(value)`; return `{ pointers: {...state.ptrs} }`, and set a transient `stackActive: state.stack.length-1`.
- `POP` → `const v = state.stack.pop()`; transient `stackActive: 'pop'` (the top was removed); put the popped value in the note via the generator (compiler just mutates).
- `ENQUEUE {value}` → `state.queue.push(value)`; transient `queueActive: state.queue.length-1`.
- `DEQUEUE` → `state.queue.shift()`; transient `queueActive: 'shift'`.
- Frame gains: `stack: state.stack.length ? [...state.stack] : undefined`,
  `queue: state.queue.length ? [...state.queue] : undefined`,
  and a transient `structActive` (the reducer's returned active marker) — mirror how `mapActive`
  is carried (returned from the reducer, defaulted null in the frame push).
- Reducer returns `{ pointers, structActive }` shape; extend the frame assembly to include
  `structActive: result.structActive ?? null` (additive, like mapActive). Existing generators
  return no structActive → null → additive, byte-identical for them.

## Part B — StackQueueViz renderer

New `frontend/src/dsa/renderers/StackQueueViz.jsx`, props `{ frame }`:
- If `frame.stack` present: render a VERTICAL stack — cells stacked bottom→top, the TOP cell (last)
  emphasized (border/color `#7C3AED`), a small "top" label on it. Heading `STACK` (style matches
  StateMachine headings: `font-sans text-[10px] font-bold uppercase tracking-wider text-[#64748B] mb-2`).
  Empty stack → an "— empty —" row (italic `#94a3b8`), like StateMachine's empty states.
- If `frame.queue` present: render a HORIZONTAL queue — cells left(front)→right(back), front labeled
  "front", back "back". Heading `QUEUE`.
- If neither present: return null.
- Animate with framer-motion `layout` + AnimatePresence (copy the pattern from StateMachine's call-stack
  pills so push/pop/enqueue/dequeue animate in/out). Key cells stably (by index+value).
- Colors: reuse the palette (`#7C3AED` active, `#0F766E` resolved/done, `rgba(15,23,42,0.03)` idle
  fill, `rgba(15,23,42,0.10)` borders). Dark mode: use the same hex-literal classes that are already
  remapped in index.css where possible; flag any NEW hex you introduce so Claude adds the dark override.

## Part C — Player integration (additive only)

In `Player.jsx` right column (currently `PseudoSteps` then `StateMachine`), insert `<StackQueueViz frame={visFrame} />`
BETWEEN them, wrapped so it only adds a divider when it renders content. Import it. Do NOT change
the main `<ArrayViz>` (it stays the primary viz — for these lessons it shows the input array/string
via existing char-cell mode + POINT highlighting). Do NOT touch pacing, gate, controls, explain panel.

## Part D — Generators (frontend/src/dsa/generators/), each `<name>Events(input) -> {input, events}`

Pure, deterministic, cap to 12 elements. Reuse ops: PUSH/POP/ENQUEUE/DEQUEUE + POINT (highlight the
current input index) + MARK (finalize) + DONE + VAR (min-stack's running min). Human `note` per event.

1. **stack-fundamentals.js** — input = number array; PUSH each (POINT i, then PUSH), then POP all
   while noting LIFO order. step_ids: `push, pop, done`. invariants: `inv-lifo`.
2. **valid-parentheses.js** — input = a bracket STRING (chars, e.g. default "([]{})"); generator
   RETURNS the char array as `input`. For each char: POINT i; if opener → PUSH it (step `push`); if
   closer → if it matches stack top → POP (step `pop`) else MARK i + step `mismatch` (invalid, stop).
   End: step `done`, note valid iff stack empty AND no mismatch. step_ids: `read, push, pop, mismatch, done`.
   invariants: `inv-match` ("the top of the stack is the most recent unmatched opener"), `inv-valid`.
3. **min-stack.js** — input = number array; PUSH each to the stack AND track running min in `vars`
   (`VAR {min}` after each push), then POP a couple showing min updates. step_ids: `push, pop, done`.
   invariants: `inv-min-tracks` ("vars.min always equals the minimum of the current stack").
4. **next-greater-element.js** — input = number array; monotonic-decreasing stack of INDICES. For
   each i: POINT i; while stack non-empty and arr[top] < arr[i] → POP + MARK top resolved (its next
   greater = arr[i]) (step `resolve`); PUSH i (step `push`). End step `done`. step_ids:
   `read, resolve, push, done`. invariants: `inv-monotonic` ("the stack holds indices whose answer
   is still unknown, in decreasing value order"). (This IS the monotonic-stack technique — the
   `monotonic-stack` lesson reuses this same generator key or a near-clone; author ONE generator
   `next-greater-element` and let both lessons point their viz at it.)
5. **queue-deque.js** — input = number array; ENQUEUE each (step `enqueue`), then DEQUEUE a few
   (step `dequeue`) showing FIFO. step_ids: `enqueue, dequeue, done`. invariants: `inv-fifo`.

Register all in `registry.js`: `stack-fundamentals`, `valid-parentheses`, `min-stack`,
`next-greater-element`, `queue-deque`.

## Part E — Golden tests + snapshot

- New `frontend/src/dsa/generators/stack-queue-family.golden.mjs` (style = windows-family.golden.mjs).
  For each generator: determinism (twice-identical), one-frame-per-event via compile, and an
  INDEPENDENT reference check:
  - stack-fundamentals: final `frame.stack` equals the expected LIFO residue.
  - valid-parentheses: the generator's validity verdict matches an independent bracket-matcher; on a
    valid input the final stack is empty; test a KNOWN-INVALID input (e.g. "(]") → mismatch fires.
  - min-stack: at every frame, `frame.vars.min === Math.min(...frame.stack)` (when stack non-empty).
  - next-greater-element: the resolved answers match a brute-force next-greater array.
  - queue-deque: final queue equals the expected FIFO residue.
  - Edge inputs: `[]`, single element, and (parens) an unbalanced string.
- `compile-frames.golden.mjs`: FIRST run `cd frontend && npm run golden` (must be green pre-change).
  Add INPUTS for the 5 new keys (pick instructive fixed inputs; parens use a string char array).
  Regenerate: `node src/dsa/compile-frames.golden.mjs --update`. Then PROVE via parsed-JSON compare
  that the pre-existing generator keys are byte-identical and only the 5 new keys were added.

## DO NOT
- Author any lesson content / `viz` blocks (that's a separate Antigravity content pass).
- Add predictions (content pass). Just emit clean step_ids that support later "push or pop?" gates.
- Touch validate.py, LessonView.jsx, or any content/*.json.
- Run the dev server or commit.

## REQUIRED verification report (your walkthrough must contain ALL of this — Claude checks each)
1. Every file created/edited, one line each.
2. Full `cd frontend && npm run golden` output (all suites must PASS, incl. the new one).
3. Snapshot proof: the parsed-JSON comparison result — "existing N keys byte-identical, only these 5
   added" (not a raw git diff, which reshuffles key order and looks huge).
4. `npx eslint src/dsa` — confirm no NEW errors vs baseline.
5. Each generator's **step_id list and invariant id list, VERBATIM** (Claude needs these for the
   phase-9 viz content packet).
6. **Explicitly state: "StackQueueViz is NOT runtime-verified — needs the lead's live browser pass."**
   (Goldens cannot catch a JSX render crash; do not claim the renderer works.)
7. Any deviation from this spec, with the reason.
