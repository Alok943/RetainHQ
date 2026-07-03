// twoPointersEvents(input) -> { input, events }
// Two pointers, converging from both ends: find a pair that sums to a target on a SORTED array.
// lo starts at 0, hi at the end; each step compares sum vs target and moves the pointer that can
// only move the sum in the right direction (lo++ if too small, hi-- if too big) — the classic
// "why does this work" is inv-sorted-halves. The input is sorted first (precondition), so the viz
// stays valid across input edits, and the target is chosen from the sorted array so a pair is
// always findable. Pure, deterministic, golden-tested. See docs/dsa-viz-implementation-plan.md M3.

export function twoPointersEvents(input) {
  const arr = [...input].slice(0, 12).sort((a, b) => a - b); // precondition: sorted; cap 12
  const n = arr.length;
  const events = [];
  const E = (op, args, step_id, invariant, note) => events.push({ op, args, step_id, invariant, note });

  if (n < 2) {
    E('DONE', {}, 'done', 'inv-converge', 'too few elements — no pair to find');
    return { input: arr, events };
  }

  const target = arr[1] + arr[n - 2]; // guaranteed findable
  let lo = 0;
  let hi = n - 1;
  E('POINT', { lo, hi }, 'start', 'inv-sorted-halves',
    `sorted array — lo and hi start at the ends, looking for a pair that sums to ${target}`);

  while (lo < hi) {
    const sum = arr[lo] + arr[hi];
    E('POINT', { lo, hi }, 'compare', 'inv-sorted-halves',
      `arr[${lo}]=${arr[lo]} + arr[${hi}]=${arr[hi]} = ${sum} vs target ${target}`);
    if (sum === target) {
      E('MARK', { indices: [lo, hi] }, 'found', 'inv-found',
        `sum == ${target} — found the pair at (${lo}, ${hi})`);
      return { input: arr, events };
    } else if (sum < target) {
      lo++;
      E('POINT', { lo, hi }, 'move', 'inv-converge',
        `${sum} < ${target} — everything left of lo paired with hi is too small, move lo forward`);
    } else {
      hi--;
      E('POINT', { lo, hi }, 'move', 'inv-converge',
        `${sum} > ${target} — everything right of hi paired with lo is too big, move hi backward`);
    }
  }
  E('DONE', {}, 'done', 'inv-converge', 'pointers met — no pair found');
  return { input: arr, events };
}
