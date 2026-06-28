// Golden-trace check for the merge-sort generator + compiler (the canonical-artifact guarantee).
// Run: node frontend/src/dsa/generators/merge-sort.golden.mjs
// Asserts the structural invariants a correct trace MUST satisfy; prints a fingerprint so the
// exact event sequence can be frozen into a real test later (vitest).

import { mergeSortEvents } from './merge-sort.js';
import { compile } from '../compile.js';

let failures = 0;
const ok = (cond, msg) => { if (!cond) { failures++; console.error('  [FAIL] ' + msg); } };

function check(input) {
  const { input: inp, events } = mergeSortEvents(input);
  const frames = compile(inp, events);

  // 1) determinism — same input twice yields identical event stream
  const again = mergeSortEvents(input).events;
  ok(JSON.stringify(events) === JSON.stringify(again), 'generator is deterministic');

  // empty input: nothing to sort -> no events/frames. Assert that and return early.
  if (input.length === 0) {
    ok(events.length === 0 && frames.length === 0, 'empty input yields no events/frames');
    return { events: 0, frames: 0, maxDepth: 0, ops: {}, output: [] };
  }

  const last = frames[frames.length - 1];

  // 2) CALL/RETURN balance (the recursion is well-formed; call stack returns to empty)
  let depth = 0, maxDepth = 0;
  for (const e of events) {
    if (e.op === 'CALL') { depth++; maxDepth = Math.max(maxDepth, depth); }
    if (e.op === 'RETURN') depth--;
    ok(depth >= 0, 'RETURN never precedes its CALL');
  }
  ok(depth === 0, 'every CALL has a matching RETURN');
  ok(last.callStack.length === 0, 'call stack empty at end');

  // 3) correctness — final materialized array equals the sorted input
  const expected = [...input].sort((a, b) => a - b);
  ok(JSON.stringify(last.array) === JSON.stringify(expected),
    `final array sorted: got ${JSON.stringify(last.array)} want ${JSON.stringify(expected)}`);

  // 4) every index is marked sorted at the end
  ok(last.sorted.length === input.length, 'all indices marked sorted at end');

  // 5) every event compiled to a frame, every frame carries a step_id-or-op
  ok(frames.length === events.length, 'one frame per event');
  ok(frames.every((f) => f.activeOp), 'every frame has an activeOp');

  const ops = events.reduce((m, e) => ((m[e.op] = (m[e.op] || 0) + 1), m), {});
  return { events: events.length, frames: frames.length, maxDepth, ops, output: last.array };
}

console.log('merge-sort golden check\n');
for (const input of [[5, 2, 8, 1, 9, 3], [1], [], [3, 3, 1, 2], [9, 8, 7, 6, 5, 4, 3, 2, 1]]) {
  const r = check(input);
  console.log(`  input ${JSON.stringify(input).padEnd(26)} -> ${r.events} events, depth ${r.maxDepth}, out ${JSON.stringify(r.output)}`);
}

const main = check([5, 2, 8, 1, 9, 3]);
console.log('\n  fingerprint (default input [5,2,8,1,9,3]):');
console.log('   ', JSON.stringify(main.ops));

console.log(failures === 0 ? '\nALL GOLDEN CHECKS PASSED' : `\n${failures} CHECK(S) FAILED`);
process.exit(failures === 0 ? 0 : 1);
