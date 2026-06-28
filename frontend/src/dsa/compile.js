// compile(input, events) -> frames.
// Events are the SOURCE OF TRUTH (a pure function of input). This folds that event stream into
// a materialized state snapshot per step, so the renderer can index O(1) into any step for
// scrubbing / predict-before-reveal / "explain this frame". Frames are a presentation cache,
// never authored directly. See docs/dsa-architecture.md.

export function compile(input, events) {
  const array = [...input];
  const callStack = [];       // for the StateMachine renderer (recursion / call stack)
  let regions = [];           // brackets under the array: left/right/merging/sorted
  const sorted = new Set();   // indices known sorted (filled on MERGE_DONE)
  const frames = [];

  const top = () => callStack[callStack.length - 1];

  for (const ev of events) {
    const { op, args = {}, step_id = null, invariant = null, note } = ev;
    let pointers = {};
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
      default:
        break; // graceful fallback: unknown op -> still a frame with caption/invariant
    }

    frames.push({
      array: [...array],
      callStack: callStack.map((f) => ({ ...f })),
      regions: regions.map((r) => ({ ...r })),
      sorted: [...sorted].sort((a, b) => a - b),
      pointers,
      activeOp: op,
      caption,
      invariant,
      step_id,
    });
  }
  return frames;
}
