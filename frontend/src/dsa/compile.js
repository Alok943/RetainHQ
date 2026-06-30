// compile(input, events) -> frames.
// Events are the SOURCE OF TRUTH (a pure function of input). This folds that event stream into
// a materialized state snapshot per step, so the renderer can index O(1) into any step for
// scrubbing / predict-before-reveal / "explain this frame". Frames are a presentation cache,
// never authored directly. See docs/dsa-architecture.md.

export function compile(input, events) {
  const array = [...input];
  const callStack = [];       // for the StateMachine renderer (recursion / call stack)
  let regions = [];           // brackets under the array: left/right/merging/sorted
  const sorted = new Set();   // indices known sorted/finalized (filled on MERGE_DONE / DONE / SET)
  const frames = [];
  let ptrs = {};              // persistent named pointers for array-family traces (lo/hi/i/j)
  let freq = null;            // frequency map for COUNT traces (hashing family); null until first COUNT

  const top = () => callStack[callStack.length - 1];

  for (const ev of events) {
    const { op, args = {}, step_id = null, invariant = null, note } = ev;
    let pointers = {};
    let mapActive = null;      // the key updated this frame (highlighted in the map panel)
    const caption = note || op;

    switch (op) {
      case 'CALL':
        callStack.push({ lo: args.lo, hi: args.hi });
        regions = [{ lo: args.lo, hi: args.hi, label: 'sorting' }];
        break;
      case 'SPLIT':
        regions = [
          { lo: args.lo, hi: args.mid, label: 'left' },
          { lo: args.mid + 1, hi: args.hi, label: 'right' },
        ];
        break;
      case 'COMPARE': {
        const t = top();
        if (t) regions = [{ lo: t.lo, hi: t.hi, label: 'merging' }];
        pointers = { write: args.writeIndex };
        break;
      }
      case 'WRITE': {
        array[args.index] = args.value;
        const t = top();
        if (t) regions = [{ lo: t.lo, hi: t.hi, label: 'merging' }];
        pointers = { write: args.index };
        break;
      }
      case 'MERGE_DONE':
        for (let x = args.lo; x <= args.hi; x++) sorted.add(x);
        regions = [{ lo: args.lo, hi: args.hi, label: 'sorted' }];
        break;
      case 'RETURN':
        callStack.pop();
        break;

      // --- array family (two-pointers, in-place ops, prefix sums) ---
      case 'POINT': // set/move named pointers (lo, hi, i, j); persists across frames
        ptrs = { ...ptrs, ...args };
        pointers = { ...ptrs };
        break;
      case 'SWAP': { // swap two indices in place
        const { i, j } = args;
        const tmp = array[i]; array[i] = array[j]; array[j] = tmp;
        ptrs = { ...ptrs, i, j };
        pointers = { ...ptrs };
        break;
      }
      case 'SET': // overwrite one cell and mark it finalized (e.g. a built prefix value)
        if (typeof args.index === 'number') { array[args.index] = args.value; sorted.add(args.index); }
        pointers = { ...ptrs, write: args.index };
        break;
      case 'COUNT': { // tally one element into the frequency map (hashing family)
        const { value, index } = args;
        if (freq === null) freq = {};
        freq[value] = (freq[value] || 0) + 1;
        mapActive = value;
        pointers = { ...ptrs, i: index };
        break;
      }
      case 'DONE': // finalize a range (or the whole array when no bounds given)
        if (typeof args.lo === 'number' && typeof args.hi === 'number') {
          for (let x = args.lo; x <= args.hi; x++) sorted.add(x);
        } else {
          for (let x = 0; x < array.length; x++) sorted.add(x);
        }
        pointers = { ...ptrs };
        break;

      default:
        break; // graceful fallback: unknown op -> still a frame with caption/invariant
    }

    frames.push({
      array: [...array],
      callStack: callStack.map((f) => ({ ...f })),
      regions: regions.map((r) => ({ ...r })),
      sorted: [...sorted].sort((a, b) => a - b),
      pointers,
      map: freq ? { ...freq } : undefined,
      mapActive,
      activeOp: op,
      caption,
      invariant,
      step_id,
    });
  }
  return frames;
}
