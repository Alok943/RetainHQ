// prefixSumsEvents(input) -> { input, events }
// Canonical execution trace for building a PREFIX-SUM array. We build it in place: arr[i] becomes
// the running total of arr[0..i]. Each SET finalizes a cell, so the bars visibly staircase upward —
// the signature of cumulative sums — and the closing frame states the O(1) range-query payoff.
// Pure function of input, deterministic, golden-tested. See docs/dsa-architecture.md.

export function prefixSumsEvents(input) {
  const arr = [...input];
  const n = arr.length;
  const events = [];
  const E = (op, args, step_id, invariant, note) =>
    events.push({ op, args, step_id, invariant, note });

  if (n === 0) {
    E('DONE', {}, 'done', 'inv-prefix', 'empty array — nothing to accumulate');
    return { input: [...input], events };
  }

  let running = 0;
  for (let i = 0; i < n; i++) {
    const orig = arr[i];
    const prev = running; // prefix[i-1]
    running += orig;
    E('SET', { index: i, value: running }, 'build', 'inv-prefix',
      i === 0
        ? `prefix[0] = arr[0] = ${running}`
        : `prefix[${i}] = prefix[${i - 1}] + arr[${i}] = ${prev} + ${orig} = ${running}`);
    arr[i] = running;
  }

  E('DONE', {}, 'query', 'inv-query',
    'built in O(n). Now any range sum is prefix[j] − prefix[i−1] in O(1) — no re-looping.');
  return { input: [...input], events };
}
