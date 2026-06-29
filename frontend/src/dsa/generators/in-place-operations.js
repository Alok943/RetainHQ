// inPlaceReverseEvents(input) -> { input, events }
// Canonical execution trace for reversing an array IN PLACE with two pointers — the archetypal
// O(1)-extra-space operation. lo starts at the front, hi at the back; swap and step both inward
// until they meet. Pure function of input, deterministic, golden-tested. `invariant` ids index the
// lesson model's invariants[]. See docs/dsa-architecture.md.

export function inPlaceReverseEvents(input) {
  const arr = [...input];
  const events = [];
  const E = (op, args, step_id, invariant, note) =>
    events.push({ op, args, step_id, invariant, note });

  let lo = 0;
  let hi = arr.length - 1;

  if (arr.length <= 1) {
    E('DONE', {}, 'done', 'inv-reversed', 'nothing to do — 0 or 1 element is already reversed');
    return { input: [...input], events };
  }

  E('POINT', { lo, hi }, 'init', 'inv-bounds',
    `start two pointers: lo=${lo} (front), hi=${hi} (back)`);

  while (lo < hi) {
    E('SWAP', { i: lo, j: hi }, 'swap', 'inv-swapped',
      `swap arr[${lo}]=${arr[lo]} with arr[${hi}]=${arr[hi]}`);
    const tmp = arr[lo]; arr[lo] = arr[hi]; arr[hi] = tmp;
    lo++; hi--;
    if (lo < hi) {
      E('POINT', { lo, hi }, 'move', 'inv-bounds',
        `step both inward: lo=${lo}, hi=${hi} — everything outside is already reversed`);
    }
  }

  E('DONE', {}, 'done', 'inv-reversed',
    'pointers met — array fully reversed using O(1) extra space');
  return { input: [...input], events };
}
