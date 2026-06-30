// frequencyCountEvents(input) -> { input, events }
// Canonical execution trace for frequency counting: one O(n) pass tallies each element into a hash
// map (key -> count). The array scan animates with a pointer; the growing map renders in the side
// panel (the "canonical signature" that makes anagram/occurrence problems O(n) instead of O(n log n)).
// Pure function of input, deterministic, golden-tested. See docs/dsa-architecture.md.

export function frequencyCountEvents(input) {
  const arr = [...input];
  const events = [];
  const E = (op, args, step_id, invariant, note) =>
    events.push({ op, args, step_id, invariant, note });

  const freq = {};
  for (let i = 0; i < arr.length; i++) {
    const v = arr[i];
    const before = freq[v] || 0;
    freq[v] = before + 1;
    E('COUNT', { index: i, value: v }, 'count', 'inv-tally',
      `see ${v} → count[${v}] = ${before} + 1 = ${freq[v]}`);
  }

  E('DONE', {}, 'done', 'inv-signature',
    'one O(n) pass builds the full map — an order-independent signature (anagrams match here)');
  return { input: [...input], events };
}
