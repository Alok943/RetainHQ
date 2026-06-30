// Golden-trace checks for the array-family generators (in-place reverse + prefix sums) against the
// shared compiler. Run: node frontend/src/dsa/generators/array-family.golden.mjs
// A wrong event stream mis-teaches everywhere downstream, so we assert the compiled final state
// matches an independent reference computation, plus structural invariants.

import { inPlaceReverseEvents } from './in-place-operations.js';
import { prefixSumsEvents } from './prefix-sums.js';
import { frequencyCountEvents } from './frequency-counting.js';
import { compile } from '../compile.js';

let failures = 0;
const ok = (cond, msg) => { if (!cond) { failures++; console.error('  [FAIL] ' + msg); } };
const eq = (a, b) => JSON.stringify(a) === JSON.stringify(b);

function checkReverse(input) {
  const { input: inp, events } = inPlaceReverseEvents(input);
  const frames = compile(inp, events);
  ok(eq(events, inPlaceReverseEvents(input).events), 'reverse: deterministic');
  const last = frames[frames.length - 1];
  const expected = [...input].reverse();
  ok(eq(last.array, expected), `reverse ${JSON.stringify(input)} -> got ${JSON.stringify(last.array)} want ${JSON.stringify(expected)}`);
  ok(frames.length === events.length, 'reverse: one frame per event');
  ok(frames.every((f) => f.activeOp), 'reverse: every frame has an activeOp');
  // every SWAP must move two in-bounds indices
  for (const e of events.filter((e) => e.op === 'SWAP')) {
    ok(e.args.i >= 0 && e.args.j < input.length && e.args.i < e.args.j, 'reverse: swap indices in bounds & ordered');
  }
  return last.array;
}

function checkPrefix(input) {
  const { input: inp, events } = prefixSumsEvents(input);
  const frames = compile(inp, events);
  ok(eq(events, prefixSumsEvents(input).events), 'prefix: deterministic');
  const last = frames[frames.length - 1];
  // independent reference: running cumulative sum
  const expected = [];
  let run = 0;
  for (const v of input) { run += v; expected.push(run); }
  ok(eq(last.array, expected), `prefix ${JSON.stringify(input)} -> got ${JSON.stringify(last.array)} want ${JSON.stringify(expected)}`);
  ok(last.sorted.length === input.length, 'prefix: every cell finalized at end');
  ok(frames.length === events.length, 'prefix: one frame per event');
  return last.array;
}

function checkFreq(input) {
  const { input: inp, events } = frequencyCountEvents(input);
  const frames = compile(inp, events);
  ok(eq(events, frequencyCountEvents(input).events), 'freq: deterministic');
  const last = frames[frames.length - 1];
  // independent reference frequency map
  const expected = {};
  for (const v of input) expected[v] = (expected[v] || 0) + 1;
  ok(eq(last.map || {}, expected), `freq ${JSON.stringify(input)} -> got ${JSON.stringify(last.map)} want ${JSON.stringify(expected)}`);
  // input array is never mutated by counting
  ok(eq(last.array, input), 'freq: input array untouched');
  ok(frames.length === events.length, 'freq: one frame per event');
  return last.map;
}

console.log('array-family golden check\n');
for (const input of [[1, 2, 3, 4, 5], [1], [], [9, 7], [3, 8, 1, 6, 2, 4]]) {
  const out = checkReverse(input);
  console.log(`  reverse ${JSON.stringify(input).padEnd(22)} -> ${JSON.stringify(out)}`);
}
console.log('');
for (const input of [[2, 4, 1, 5, 3], [10], [], [5, -2, 7], [1, 1, 1, 1]]) {
  const out = checkPrefix(input);
  console.log(`  prefix  ${JSON.stringify(input).padEnd(22)} -> ${JSON.stringify(out)}`);
}
console.log('');
for (const input of [[2, 3, 2, 1, 3, 2], [7], [], [4, 4, 4], [1, 2, 3, 4]]) {
  const out = checkFreq(input);
  console.log(`  freq    ${JSON.stringify(input).padEnd(22)} -> ${JSON.stringify(out)}`);
}

console.log(failures === 0 ? '\nALL GOLDEN CHECKS PASSED' : `\n${failures} CHECK(S) FAILED`);
process.exit(failures === 0 ? 0 : 1);
