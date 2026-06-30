// binarySearchEvents(input) -> { input, events }
// Binary search: on a SORTED array, probe the middle of the active [lo,hi] window and discard the
// half that can't contain the target. The input is sorted first (binary search's precondition), so
// the viz is always valid even when the user tweaks it. WINDOW shrinks the cyan active range; `mid`
// is the purple probe; MARK on hit. Pure, deterministic, golden-tested.

export function binarySearchEvents(input) {
  const arr = [...input].sort((a, b) => a - b); // precondition: sorted
  const n = arr.length;
  const events = [];
  const E = (op, args, step_id, invariant, note) => events.push({ op, args, step_id, invariant, note });

  if (n === 0) {
    E('DONE', {}, 'done', 'inv-window', 'empty array — nothing to search');
    return { input: arr, events };
  }

  const target = arr[Math.max(0, n - 2)]; // a value that's present
  let lo = 0;
  let hi = n - 1;
  E('WINDOW', { lo, hi }, 'start', 'inv-window', `sorted array — searching for ${target} in the whole range`);

  while (lo <= hi) {
    const mid = Math.floor((lo + hi) / 2);
    E('WINDOW', { lo, hi }, 'window', 'inv-window', `the answer, if any, lies in [${lo}..${hi}]`);
    E('POINT', { lo, hi, mid }, 'probe', 'inv-halve', `check the middle: arr[${mid}]=${arr[mid]} vs ${target}`);
    if (arr[mid] === target) {
      E('MARK', { indices: [mid] }, 'found', 'inv-found', `arr[${mid}] == ${target} — found in ~log₂n steps`);
      return { input: arr, events };
    } else if (arr[mid] < target) {
      lo = mid + 1;
      E('POINT', { lo, hi: hi, mid }, 'discard', 'inv-halve', `arr[${mid}] < ${target} — discard the left half, go right`);
    } else {
      hi = mid - 1;
      E('POINT', { lo, hi, mid }, 'discard', 'inv-halve', `arr[${mid}] > ${target} — discard the right half, go left`);
    }
  }
  E('DONE', {}, 'done', 'inv-window', `window is empty — ${target} not present`);
  return { input: arr, events };
}
