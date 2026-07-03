// slidingWindowVariableEvents(input) -> { input, events }
// Variable-size sliding window: shortest contiguous window whose sum >= target. Input is
// transformed to positive integers (Math.max(1, Math.abs(v))) because the expand/shrink monotonic
// argument requires every value to grow the sum — a zero or negative value would break the
// "shrinking never un-qualifies then re-qualifies" guarantee. target = ceil(total/2), so a
// qualifying window always exists. The repeated decision each step is expand-vs-shrink: expand hi
// while sum < target (growing to qualify), shrink lo while sum >= target (tightening, recording
// the best length each time it still qualifies). Pure, deterministic, golden-tested.
// See docs/dsa-viz-implementation-plan.md M3.

export function slidingWindowVariableEvents(input) {
  const arr = [...input].slice(0, 12).map((v) => Math.max(1, Math.abs(v)));
  const n = arr.length;
  const events = [];
  const E = (op, args, step_id, invariant, note) => events.push({ op, args, step_id, invariant, note });

  if (n === 0) {
    E('DONE', {}, 'done', 'inv-monotone-sum', 'empty array — no window to grow');
    return { input: arr, events };
  }

  const total = arr.reduce((a, b) => a + b, 0);
  const target = Math.ceil(total / 2);

  let lo = 0;
  let sum = 0;
  let bestLen = Infinity;
  let bestLo = 0;

  E('VAR', { sum: 0, target, best_len: null }, 'expand', 'inv-monotone-sum',
    `all values are positive — sum only grows as the window expands. Target sum = ${target}`);

  for (let hi = 0; hi < n; hi++) {
    sum += arr[hi];
    E('WINDOW', { lo, hi }, 'expand', 'inv-monotone-sum',
      `sum < target — expand hi to bring in arr[${hi}]=${arr[hi]}: sum = ${sum}`);
    E('VAR', { sum, target, best_len: bestLen === Infinity ? null : bestLen }, 'expand', 'inv-monotone-sum',
      `sum=${sum}, target=${target}`);

    while (sum >= target) {
      const len = hi - lo + 1;
      if (len < bestLen) { bestLen = len; bestLo = lo; }
      E('VAR', { sum, target, best_len: bestLen }, 'record', 'inv-shrink-safe',
        `sum=${sum} >= target=${target} — window [${lo}..${hi}] qualifies at length ${len}, best so far ${bestLen}`);
      sum -= arr[lo];
      lo += 1;
      if (sum >= target) {
        E('WINDOW', { lo, hi }, 'shrink', 'inv-shrink-safe',
          `still >= target after removing arr[${lo - 1}]=${arr[lo - 1]} — shrink lo further: sum = ${sum}`);
      } else {
        E('WINDOW', { lo, hi }, 'shrink', 'inv-shrink-safe',
          `removing arr[${lo - 1}]=${arr[lo - 1]} drops sum to ${sum} < target — stop shrinking, go back to expanding`);
      }
    }
  }

  E('MARK', { indices: Array.from({ length: bestLen === Infinity ? 0 : bestLen }, (_, i) => bestLo + i) },
    'done', 'inv-shrink-safe',
    bestLen === Infinity ? 'no window ever reached the target' : `shortest qualifying window is [${bestLo}..${bestLo + bestLen - 1}], length ${bestLen}`);
  E('DONE', {}, 'done', 'inv-monotone-sum', `scanned in O(n) — lo and hi each move forward only, never backward`);
  return { input: arr, events };
}
