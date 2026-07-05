// lowerBoundEvents(input) -> { input, events }
// Lower bound: on a SORTED array, find the FIRST index i where sorted[i] >= target — binary
// search on the [lo,hi] window, but unlike plain binary search it ALWAYS lands somewhere (the
// insertion point) even when target isn't present. The teaching point: it never checks for
// equality to stop early — it keeps narrowing until lo==hi, landing on the first index that is
// not-less-than target. Pure, deterministic, golden-tested.

export function lowerBoundEvents(input) {
  const arr = [...input].slice(0, 12).sort((a, b) => a - b); // precondition: sorted, capped at 12
  const n = arr.length;
  const events = [];
  const E = (op, args, step_id, invariant, note) => events.push({ op, args, step_id, invariant, note });

  if (n === 0) {
    E('DONE', {}, 'done', 'inv-window', 'empty array — nothing to search, lower bound is index 0');
    return { input: arr, events };
  }

  const target = arr[Math.floor(n / 2)];
  let lo = 0;
  let hi = n; // hi is one-past-the-end: the landing index can be n (target bigger than everything)
  E('WINDOW', { lo, hi: n - 1 }, 'start', 'inv-window', `sorted array — finding the first index >= ${target}`);

  while (lo < hi) {
    const mid = Math.floor((lo + hi) / 2);
    E('WINDOW', { lo, hi: Math.min(hi, n - 1) }, 'window', 'inv-window', `the answer index lies in [${lo}..${hi}]`);
    E('POINT', { lo, hi, mid }, 'probe', 'inv-lower', `check the middle: arr[${mid}]=${arr[mid]} vs target ${target}`);
    if (arr[mid] >= target) {
      hi = mid;
      E('POINT', { lo, hi, mid }, 'discard', 'inv-lower', `arr[${mid}] >= ${target} — this could still be the answer, keep it in range and search left`);
    } else {
      lo = mid + 1;
      E('POINT', { lo, hi, mid }, 'discard', 'inv-lower', `arr[${mid}] < ${target} — everything left of ${lo} is strictly less than ${target}, discard it`);
    }
  }

  E('MARK', { indices: lo < n ? [lo] : [] }, 'land', 'inv-land',
    lo < n
      ? `lands at index ${lo}: arr[${lo}]=${arr[lo]} is the FIRST value >= ${target} (it lands here even without an equality check — that's the lower-bound rule)`
      : `lands at index ${lo} (past the end) — every element is < ${target}, so the insertion point is at the end`);
  E('DONE', { lo, hi }, 'done', 'inv-window', `search finished at index ${lo}`);
  return { input: arr, events };
}
