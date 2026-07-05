// upperBoundEvents(input) -> { input, events }
// Upper bound: on a SORTED array, find the FIRST index i where sorted[i] > target (strictly
// greater) — the same binary search on [lo,hi] as lower-bound, but the probe's tie-breaking flips:
// a value EQUAL to target is not the answer, so equal values get pushed left of the window too.
// The teaching point: lower-bound and upper-bound run the identical loop shape; only the
// >= vs > comparison at the probe differs, and that's what makes upper-bound land AFTER a run of
// duplicates instead of AT the first one. Pure, deterministic, golden-tested.

export function upperBoundEvents(input) {
  const arr = [...input].slice(0, 12).sort((a, b) => a - b); // precondition: sorted, capped at 12
  const n = arr.length;
  const events = [];
  const E = (op, args, step_id, invariant, note) => events.push({ op, args, step_id, invariant, note });

  if (n === 0) {
    E('DONE', {}, 'done', 'inv-window', 'empty array — nothing to search, upper bound is index 0');
    return { input: arr, events };
  }

  const target = arr[Math.floor(n / 2)];
  let lo = 0;
  let hi = n; // hi is one-past-the-end: the landing index can be n (nothing strictly greater exists)
  E('WINDOW', { lo, hi: n - 1 }, 'start', 'inv-window', `sorted array — finding the first index > ${target}`);

  while (lo < hi) {
    const mid = Math.floor((lo + hi) / 2);
    E('WINDOW', { lo, hi: Math.min(hi, n - 1) }, 'window', 'inv-window', `the answer index lies in [${lo}..${hi}]`);
    E('POINT', { lo, hi, mid }, 'probe', 'inv-upper', `check the middle: arr[${mid}]=${arr[mid]} vs target ${target}`);
    if (arr[mid] > target) {
      hi = mid;
      E('POINT', { lo, hi, mid }, 'discard', 'inv-upper', `arr[${mid}] > ${target} — this could still be the answer, keep it in range and search left`);
    } else {
      lo = mid + 1;
      E('POINT', { lo, hi, mid }, 'discard', 'inv-upper', `arr[${mid}] <= ${target} — everything left of ${lo} is <= ${target} (equal values get pushed left too), discard it`);
    }
  }

  E('MARK', { indices: lo < n ? [lo] : [] }, 'land', 'inv-land',
    lo < n
      ? `lands at index ${lo}: arr[${lo}]=${arr[lo]} is the FIRST value strictly > ${target} — notice it lands AFTER any run of ${target}s, unlike lower-bound which lands ON the first one`
      : `lands at index ${lo} (past the end) — no element is > ${target}, so the insertion point is at the end`);
  E('DONE', { lo, hi }, 'done', 'inv-window', `search finished at index ${lo}`);
  return { input: arr, events };
}
