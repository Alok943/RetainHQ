// compile(input, events) -> frames.
// Events are the SOURCE OF TRUTH (a pure function of input). This folds that event stream into
// a materialized state snapshot per step, so the renderer can index O(1) into any step for
// scrubbing / predict-before-reveal / "explain this frame". Frames are a presentation cache,
// never authored directly. See docs/dsa-architecture.md.
//
// Structure (M0/D3): op handling is split into per-FAMILY reducers. Each reducer takes the shared
// `state` + the event's op/args, mutates state, and RETURNS the per-frame transient bits
// ({ pointers?, mapActive? }) — or `null` meaning "not my op". compile() tries reducers in order,
// takes the first non-null, and assembles the identical frame shape. Adding a new data-structure
// family (stack, list, tree, graph, grid...) = add a reducer + additive frame keys, never edit a
// giant switch. An UNKNOWN op falls through all reducers -> still a frame with caption + invariant
// (graceful fallback). compile()'s signature and frame shape are a stable contract — see
// compile-frames.golden.mjs (byte-identical guard).

// --- recursion / merge family: CALL SPLIT COMPARE WRITE MERGE_DONE RETURN ---
function recursionMergeReducer(state, op, args) {
  const top = () => state.callStack[state.callStack.length - 1];
  switch (op) {
    case 'CALL':
      state.callStack.push({ lo: args.lo, hi: args.hi });
      state.regions = [{ lo: args.lo, hi: args.hi, label: 'sorting' }];
      return {};
    case 'SPLIT':
      state.regions = [
        { lo: args.lo, hi: args.mid, label: 'left' },
        { lo: args.mid + 1, hi: args.hi, label: 'right' },
      ];
      return {};
    case 'COMPARE': {
      const t = top();
      if (t) state.regions = [{ lo: t.lo, hi: t.hi, label: 'merging' }];
      return { pointers: { write: args.writeIndex } };
    }
    case 'WRITE': {
      state.array[args.index] = args.value;
      const t = top();
      if (t) state.regions = [{ lo: t.lo, hi: t.hi, label: 'merging' }];
      return { pointers: { write: args.index } };
    }
    case 'MERGE_DONE':
      for (let x = args.lo; x <= args.hi; x++) state.sorted.add(x);
      state.regions = [{ lo: args.lo, hi: args.hi, label: 'sorted' }];
      return {};
    case 'RETURN':
      state.callStack.pop();
      return {};
    default:
      return null;
  }
}

// --- array family: two-pointers, in-place ops, prefix sums, binary search ---
function arrayReducer(state, op, args) {
  switch (op) {
    case 'POINT': // set/move named pointers (lo, hi, i, j); persists across frames
      state.ptrs = { ...state.ptrs, ...args };
      return { pointers: { ...state.ptrs } };
    case 'SWAP': { // swap two indices in place
      const { i, j } = args;
      const tmp = state.array[i]; state.array[i] = state.array[j]; state.array[j] = tmp;
      state.ptrs = { ...state.ptrs, i, j };
      return { pointers: { ...state.ptrs } };
    }
    case 'SET': // overwrite one cell and mark it finalized (e.g. a built prefix value)
      if (typeof args.index === 'number') { state.array[args.index] = args.value; state.sorted.add(args.index); }
      return { pointers: { ...state.ptrs, write: args.index } };
    case 'WINDOW': // set the active sub-range (e.g. binary-search [lo,hi]); cells outside go idle
      state.regions = [{ lo: args.lo, hi: args.hi, label: 'merging' }];
      return { pointers: { ...state.ptrs } };
    case 'MARK': // mark specific indices as confirmed/matched (no value change)
      for (const x of args.indices || []) state.sorted.add(x);
      return { pointers: { ...state.ptrs } };
    case 'DONE': // finalize a range (or the whole array when no bounds given)
      if (typeof args.lo === 'number' && typeof args.hi === 'number') {
        for (let x = args.lo; x <= args.hi; x++) state.sorted.add(x);
      } else {
        for (let x = 0; x < state.array.length; x++) state.sorted.add(x);
      }
      return { pointers: { ...state.ptrs } };
    default:
      return null;
  }
}

// --- hashing family: frequency counting ---
function hashingReducer(state, op, args) {
  switch (op) {
    case 'COUNT': { // tally one element into the frequency map
      const { value, index } = args;
      if (state.freq === null) state.freq = {};
      state.freq[value] = (state.freq[value] || 0) + 1;
      return { pointers: { ...state.ptrs, i: index }, mapActive: value };
    }
    default:
      return null;
  }
}

const REDUCERS = [recursionMergeReducer, arrayReducer, hashingReducer];

export function compile(input, events) {
  const state = {
    array: [...input],       // mutated by WRITE / SWAP / SET
    callStack: [],           // for the StateMachine renderer (recursion / call stack)
    regions: [],             // brackets under the array: left/right/merging/sorted
    sorted: new Set(),       // indices known sorted/finalized (MERGE_DONE / DONE / SET / MARK)
    ptrs: {},                // persistent named pointers for array-family traces (lo/hi/i/j)
    freq: null,              // frequency map for COUNT traces; null until first COUNT
  };
  const frames = [];

  for (const ev of events) {
    const { op, args = {}, step_id = null, invariant = null, note } = ev;

    let result = null;
    for (const reducer of REDUCERS) {
      result = reducer(state, op, args);
      if (result) break;
    }
    if (!result) result = {}; // graceful fallback: unknown op -> still a frame with caption/invariant

    frames.push({
      array: [...state.array],
      callStack: state.callStack.map((f) => ({ ...f })),
      regions: state.regions.map((r) => ({ ...r })),
      sorted: [...state.sorted].sort((a, b) => a - b),
      pointers: result.pointers || {},
      map: state.freq ? { ...state.freq } : undefined,
      mapActive: result.mapActive ?? null,
      activeOp: op,
      caption: note || op,
      invariant,
      step_id,
    });
  }
  return frames;
}
