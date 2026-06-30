// linearSearchEvents(input) -> { input, events }
// Linear search: scan left to right comparing each element to the target until found. Target is the
// second-to-last value (always present, gives a full-ish scan) and recomputes when the input is
// tweaked. Reuses POINT (scan) / MARK (found). Pure, deterministic, golden-tested.

export function linearSearchEvents(input) {
  const arr = [...input];
  const n = arr.length;
  const events = [];
  const E = (op, args, step_id, invariant, note) => events.push({ op, args, step_id, invariant, note });

  if (n === 0) {
    E('DONE', {}, 'done', 'inv-scan', 'empty array — nothing to search');
    return { input: [...input], events };
  }

  const target = arr[Math.max(0, n - 2)]; // a value that's present
  E('POINT', { i: 0 }, 'start', 'inv-scan', `searching for ${target} — check every element in order`);
  for (let i = 0; i < n; i++) {
    E('POINT', { i }, 'compare', 'inv-scan', `is arr[${i}]=${arr[i]} == ${target}?`);
    if (arr[i] === target) {
      E('MARK', { indices: [i] }, 'found', 'inv-found', `match at index ${i} — found in ${i + 1} checks`);
      return { input: [...input], events };
    }
  }
  E('DONE', {}, 'done', 'inv-scan', `scanned all ${n} — ${target} not present`);
  return { input: [...input], events };
}
