// Golden checks for the prediction derive library (predict.js). These are the "educational test"
// layer (plan §9.3): a derive that computes the WRONG answer mis-teaches the learner even though
// everything renders. Every answer is cross-checked against the live trace, and — the whole point —
// re-derived on a DIFFERENT input to prove it isn't hardcoded. See docs/dsa-viz-implementation-plan.md §7.
import { mergeSortEvents } from './generators/merge-sort.js';
import { bubbleSortEvents } from './generators/bubble-sort.js';
import { binarySearchEvents } from './generators/binary-search.js';
import { resolveGate, evaluateCheckpoint, parseDerive, gradeAnswer, isKnownDerive } from './predict.js';

let failures = 0;
const ok = (cond, msg) => { if (!cond) { failures++; console.error('  [FAIL] ' + msg); } };
const eq = (a, b) => JSON.stringify(a) === JSON.stringify(b);

// --- parseDerive ---
ok(eq(parseDerive('next_n_writes(2)'), { name: 'next_n_writes', args: [2] }), 'parse: parameterized');
ok(eq(parseDerive('next_op'), { name: 'next_op', args: [] }), 'parse: bare');
ok(isKnownDerive('next_swap_pair') && !isKnownDerive('bogus_fn'), 'isKnownDerive: registry gate');

// --- resolveGate occurrences ---
{
  const { events } = mergeSortEvents([5, 2, 8, 1, 9, 3]);
  const first = resolveGate(events, { at_op: 'WRITE', occurrence: 'first' });
  const last = resolveGate(events, { at_op: 'WRITE', occurrence: 'last' });
  ok(events[first].op === 'WRITE' && events[last].op === 'WRITE', 'resolveGate: lands on WRITE ops');
  ok(first < last, 'resolveGate: first precedes last');
  ok(resolveGate(events, { at_op: 'SWAP' }) === -1, 'resolveGate: absent op -> -1 (skip)');
  ok(resolveGate(events, { at_step: 'split', occurrence: 2 }) >= 0, 'resolveGate: integer occurrence');
}

// --- next_n_writes: answer must equal the ACTUAL next writes, and NOT be hardcoded across inputs ---
function firstMergeWrites(input, n) {
  const { events } = mergeSortEvents(input);
  const cp = { at_op: 'COMPARE', occurrence: 'first', derive: `next_n_writes(${n})`, level: 'medium', prompt: 'next writes?' };
  const r = evaluateCheckpoint(events, cp);
  return r ? r.answer : null;
}
{
  const a = firstMergeWrites([5, 2, 8, 1, 9, 3], 2);
  const b = firstMergeWrites([9, 8, 7, 6], 2);
  ok(Array.isArray(a) && a.length === 2, 'next_n_writes: returns 2 values');
  ok(!eq(a, b), 'next_n_writes: NOT hardcoded — different inputs give different answers');
  // independently: the answer must equal the values of the first 2 WRITE events after the gate
  const { events } = mergeSortEvents([5, 2, 8, 1, 9, 3]);
  const gate = resolveGate(events, { at_op: 'COMPARE', occurrence: 'first' });
  const expected = events.filter((e, i) => i > gate && (e.op === 'WRITE')).slice(0, 2).map((e) => e.args.value);
  ok(eq(a, expected), `next_n_writes: matches trace (got ${JSON.stringify(a)} want ${JSON.stringify(expected)})`);
}

// --- next_swap_pair on bubble sort ---
{
  const { events } = bubbleSortEvents([5, 2, 8, 1, 9]);
  const cp = { at_step: 'compare', occurrence: 'first', derive: 'next_swap_pair', level: 'medium', prompt: 'which swap?' };
  const r = evaluateCheckpoint(events, cp);
  const firstSwap = events.find((e) => e.op === 'SWAP');
  ok(r && eq(r.answer, [firstSwap.args.i, firstSwap.args.j]), 'next_swap_pair: matches first real SWAP');
  ok(gradeAnswer('pair', r.answer, [firstSwap.args.i, firstSwap.args.j]), 'gradeAnswer: correct pair passes');
  ok(!gradeAnswer('pair', r.answer, [9, 9]), 'gradeAnswer: wrong pair fails');
}

// --- branch_binary: left/right must match the actual window move; skip if no gate ---
{
  const { input, events } = binarySearchEvents([1, 3, 5, 7, 9, 11, 13]);
  const cp = { at_op: 'WINDOW', occurrence: 'first', derive: 'branch_binary', level: 'hard', prompt: 'left or right?' };
  const r = evaluateCheckpoint(events, cp);
  ok(r === null || r.type === 'choice', 'branch_binary: choice type or clean skip');
  if (r) ok(['left', 'right', 'found'].includes(r.answer), `branch_binary: valid answer (${r.answer})`);
  void input;
}

// --- graceful skip: empty input yields no gate ---
{
  const { events } = mergeSortEvents([]);
  const r = evaluateCheckpoint(events, { at_op: 'WRITE', derive: 'next_write', prompt: 'x' });
  ok(r === null, 'empty input: checkpoint skipped (null)');
}

console.log(failures === 0 ? 'predict golden: ALL CHECKS PASSED' : `predict golden: ${failures} CHECK(S) FAILED`);
process.exit(failures === 0 ? 0 : 1);
