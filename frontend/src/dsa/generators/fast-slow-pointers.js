// fastSlowPointersEvents(input) -> { input, events }
// Fast/slow pointers (Floyd's tortoise-and-hare, linear form): slow advances 1 step, fast advances
// 2 steps, each iteration, as long as fast can take a full 2-step hop without passing the last
// index. Convention used here (matches the golden reference): for length n, slow ends at
// floor((n-1)/2) — the lower-middle for even-length inputs. Pure, deterministic, golden-tested.
// See docs/dsa-viz-implementation-plan.md M3.

export function fastSlowPointersEvents(input) {
  const arr = [...input].slice(0, 12);
  const n = arr.length;
  const events = [];
  const E = (op, args, step_id, invariant, note) => events.push({ op, args, step_id, invariant, note });

  if (n === 0) {
    E('DONE', {}, 'done', 'inv-middle', 'empty array — no middle to find');
    return { input: arr, events };
  }

  let slow = 0;
  let fast = 0;
  E('POINT', { slow, fast }, 'start', 'inv-two-speeds',
    `slow and fast both start at index 0 — fast will move twice as fast as slow`);

  while (fast + 2 <= n - 1) {
    slow += 1;
    fast += 2;
    E('POINT', { slow, fast }, 'advance', 'inv-two-speeds',
      `slow -> ${slow} (+1), fast -> ${fast} (+2) — when fast can't take a full hop, slow is at the middle`);
  }

  E('MARK', { indices: [slow] }, 'middle', 'inv-middle',
    `fast reached the end — slow is sitting on the middle, index ${slow}`);
  E('DONE', {}, 'done', 'inv-middle', `middle found at index ${slow} in one pass, O(1) space`);
  return { input: arr, events };
}
