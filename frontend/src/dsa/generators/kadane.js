// kadaneEvents(input) -> { input, events }
// Kadane's algorithm: maximum subarray sum. Input is used AS-IS — negatives are the whole point
// (they're what force the extend-vs-restart decision). At each index i, the repeated decision is:
// extend the current run (current + v) or restart it fresh at v — whichever is bigger. `current`
// is kept as a live region [runLo..i] via WINDOW so the current run is visible against the bars;
// `best` updates (step_id 'record') whenever current beats it. MARK the best range at the end.
// Pure, deterministic, golden-tested. See docs/dsa-viz-implementation-plan.md M3.

export function kadaneEvents(input) {
  const arr = [...input].slice(0, 12);
  const n = arr.length;
  const events = [];
  const E = (op, args, step_id, invariant, note) => events.push({ op, args, step_id, invariant, note });

  if (n === 0) {
    E('DONE', {}, 'done', 'inv-best', 'empty array — no subarray sum to track');
    return { input: arr, events };
  }

  let current = arr[0];
  let best = arr[0];
  let runLo = 0;
  let bestLo = 0;
  let bestHi = 0;

  E('POINT', { i: 0 }, 'start', 'inv-current',
    `start at index 0 — current run begins here with value ${arr[0]}`);
  E('WINDOW', { lo: 0, hi: 0 }, 'start', 'inv-current', `current run = [0..0]`);
  E('VAR', { current, best }, 'start', 'inv-current', `current=${current}, best=${best}`);

  for (let i = 1; i < n; i++) {
    const v = arr[i];
    const extended = current + v;
    E('POINT', { i }, extended >= v ? 'extend' : 'restart', 'inv-current',
      extended >= v
        ? `current(${current}) + arr[${i}]=${v} = ${extended} >= ${v} — extend the run`
        : `current(${current}) + arr[${i}]=${v} = ${extended} < arr[${i}]=${v} — restart the run here`);
    if (extended >= v) {
      current = extended;
    } else {
      current = v;
      runLo = i;
    }
    E('WINDOW', { lo: runLo, hi: i }, extended >= v ? 'extend' : 'restart', 'inv-current',
      `current run is now [${runLo}..${i}]`);
    E('VAR', { current, best }, extended >= v ? 'extend' : 'restart', 'inv-current',
      `current=${current}, best=${best}`);

    if (current > best) {
      best = current;
      bestLo = runLo;
      bestHi = i;
      E('VAR', { current, best }, 'record', 'inv-best',
        `current(${current}) beats best — best is now ${best}, from [${bestLo}..${bestHi}]`);
    }
  }

  E('MARK', { indices: Array.from({ length: bestHi - bestLo + 1 }, (_, k) => bestLo + k) },
    'done', 'inv-best', `best subarray is [${bestLo}..${bestHi}] with sum ${best}`);
  E('DONE', {}, 'done', 'inv-best', `scanned in O(n) — one pass, no re-summing from every start`);
  return { input: arr, events };
}
