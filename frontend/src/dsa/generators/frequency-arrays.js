// frequencyArrayEvents(input) -> { input, events }
// Counts characters into a frequency signature in one O(n) pass (the "26 mailboxes" idea). Same
// COUNT engine as frequency-counting, on a char array — the growing key->count map renders in the
// side panel. Pure function of input, deterministic, golden-tested.

export function frequencyArrayEvents(input) {
  const arr = [...input];
  const events = [];
  const E = (op, args, step_id, invariant, note) =>
    events.push({ op, args, step_id, invariant, note });

  if (arr.length === 0) {
    E('DONE', {}, 'done', 'inv-tally', 'empty string — nothing to count');
    return { input: [...input], events };
  }

  const seen = {};
  for (let i = 0; i < arr.length; i++) {
    const c = arr[i];
    const before = seen[c] || 0;
    seen[c] = before + 1;
    E('COUNT', { index: i, value: c }, 'count', 'inv-tally',
      `'${c}' → count['${c}'] = ${before} + 1 = ${seen[c]}`);
  }

  E('DONE', {}, 'done', 'inv-signature',
    "this count signature is order-independent — two anagrams produce the identical counts");
  return { input: [...input], events };
}
