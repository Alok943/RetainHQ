// slidingWindowFixedEvents(input) -> { input, events }
// Fixed-size sliding window: max sum of any window of size k (k = min(3, n)). Maintain a running
// `sum` in vars, updating it by subtracting the value leaving the window and adding the value
// entering it as the window slides — never re-summing from scratch. Track `best` alongside; MARK
// the best window's indices at the end. Pure, deterministic, golden-tested.
// See docs/dsa-viz-implementation-plan.md M3.

export function slidingWindowFixedEvents(input) {
  const arr = [...input].slice(0, 12);
  const n = arr.length;
  const events = [];
  const E = (op, args, step_id, invariant, note) => events.push({ op, args, step_id, invariant, note });

  if (n === 0) {
    E('DONE', {}, 'done', 'inv-window-sum', 'empty array — no window to slide');
    return { input: arr, events };
  }

  const k = Math.min(3, n);
  let sum = 0;
  for (let x = 0; x < k; x++) sum += arr[x];
  let best = sum;
  let bestLo = 0;

  E('WINDOW', { lo: 0, hi: k - 1 }, 'init', 'inv-window-sum',
    `first window [0..${k - 1}] — sum = ${sum}`);
  E('VAR', { sum, best }, 'init', 'inv-window-sum', `sum=${sum}, best=${best}`);

  for (let hi = k; hi < n; hi++) {
    const lo = hi - k;
    const leaving = arr[lo];
    const entering = arr[hi];
    sum = sum - leaving + entering;
    E('WINDOW', { lo: lo + 1, hi }, 'slide', 'inv-window-sum',
      `slide right — subtract leaving arr[${lo}]=${leaving}, add entering arr[${hi}]=${entering}: sum = ${sum}`);
    if (sum > best) {
      best = sum;
      bestLo = lo + 1;
    }
    E('VAR', { sum, best }, 'slide', 'inv-window-sum', `sum=${sum}, best=${best}`);
  }

  E('MARK', { indices: Array.from({ length: k }, (_, i) => bestLo + i) }, 'done', 'inv-window-sum',
    `best window is [${bestLo}..${bestLo + k - 1}] with sum ${best}`);
  E('DONE', {}, 'done', 'inv-window-sum', `scanned in O(n) — no window re-summed from scratch`);
  return { input: arr, events };
}
