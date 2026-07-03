// Golden-trace checks for the M3 "Two Pointers & Windows" generators against the shared compiler.
// Run: node frontend/src/dsa/generators/windows-family.golden.mjs
// Each check is INDEPENDENT of the generator's own bookkeeping — a brute-force reference recomputes
// the expected answer from the (possibly transformed) input, so a bug in the generator's own
// running totals can't hide behind a self-consistent trace. See docs/dsa-viz-implementation-plan.md M3.

import { twoPointersEvents } from './two-pointers.js';
import { fastSlowPointersEvents } from './fast-slow-pointers.js';
import { slidingWindowFixedEvents } from './sliding-window-fixed.js';
import { slidingWindowVariableEvents } from './sliding-window-variable.js';
import { kadaneEvents } from './kadane.js';
import { compile } from '../compile.js';

let failures = 0;
const ok = (cond, msg) => { if (!cond) { failures++; console.error('  [FAIL] ' + msg); } };
const eq = (a, b) => JSON.stringify(a) === JSON.stringify(b);

function run(gen, input) {
  const { input: gi, events } = gen(input);
  return { input: gi ?? input, events };
}

function checkDeterminism(name, gen, input) {
  const a = gen(input);
  const b = gen(input);
  ok(eq(a.events, b.events), `${name}: deterministic (same events on repeat run)`);
  ok(eq(a.input, b.input), `${name}: deterministic (same input on repeat run)`);
}

function checkOneFramePerEvent(name, gen, input) {
  const { input: gi, events } = run(gen, input);
  const frames = compile(gi, events);
  ok(frames.length === events.length, `${name} ${JSON.stringify(input)}: one frame per event (${frames.length} vs ${events.length})`);
}

function lastVars(gen, input) {
  const { input: gi, events } = run(gen, input);
  const frames = compile(gi, events);
  for (let i = frames.length - 1; i >= 0; i--) {
    if (frames[i].vars) return frames[i].vars;
  }
  return undefined;
}

console.log('windows-family golden check\n');

// ---------------------------------------------------------------------------------------------
// two-pointers: brute-force pair search on the SORTED array must find the same pair the generator
// found (the generator sorts + emits `input` as the sorted array; re-derive target the same way).
// ---------------------------------------------------------------------------------------------
{
  const inputs = [[4, 1, 7, 3, 9, 2], [5, 5, 5], [1], [], [2, 4]];
  for (const input of inputs) {
    checkDeterminism('two-pointers', twoPointersEvents, input);
    checkOneFramePerEvent('two-pointers', twoPointersEvents, input);
    const { input: sorted, events } = run(twoPointersEvents, input);
    const n = sorted.length;
    if (n < 2) continue;
    const target = sorted[1] + sorted[n - 2];
    // brute force: any pair (i<j) summing to target
    let bruteFound = null;
    outer:
    for (let i = 0; i < n; i++) {
      for (let j = i + 1; j < n; j++) {
        if (sorted[i] + sorted[j] === target) { bruteFound = [i, j]; break outer; }
      }
    }
    const markEvent = events.find((e) => e.op === 'MARK');
    ok(!!bruteFound, `two-pointers ${JSON.stringify(input)}: brute force finds a pair for target ${target}`);
    ok(!!markEvent, `two-pointers ${JSON.stringify(input)}: generator found a pair too`);
    if (bruteFound && markEvent) {
      const [gi_, gj_] = markEvent.args.indices;
      ok(sorted[gi_] + sorted[gj_] === target, `two-pointers ${JSON.stringify(input)}: MARK pair sums to target`);
    }
  }
  console.log('  two-pointers: pair-sum matches brute force on all inputs');
}

// ---------------------------------------------------------------------------------------------
// fast-slow-pointers: slow ends at floor((n-1)/2) — this generator's stated convention.
// ---------------------------------------------------------------------------------------------
{
  const inputs = [[5, 2, 8, 1, 9, 3], [1, 2, 3, 4, 5], [1, 2], [1], []];
  for (const input of inputs) {
    checkDeterminism('fast-slow-pointers', fastSlowPointersEvents, input);
    checkOneFramePerEvent('fast-slow-pointers', fastSlowPointersEvents, input);
    const { input: gi, events } = run(fastSlowPointersEvents, input);
    const n = gi.length;
    if (n === 0) continue;
    const expected = Math.floor((n - 1) / 2);
    const markEvent = events.find((e) => e.op === 'MARK');
    ok(!!markEvent && eq(markEvent.args.indices, [expected]),
      `fast-slow-pointers ${JSON.stringify(input)}: slow lands at floor((n-1)/2)=${expected} (got ${markEvent && JSON.stringify(markEvent.args.indices)})`);
  }
  console.log('  fast-slow-pointers: middle matches floor((n-1)/2) convention');
}

// ---------------------------------------------------------------------------------------------
// sliding-window-fixed: brute-force max window sum (k = min(3,n)) must equal the final VAR best.
// ---------------------------------------------------------------------------------------------
{
  const inputs = [[2, 4, 1, 5, 3, 6], [1, 1, 1], [7, -1], [4], []];
  for (const input of inputs) {
    checkDeterminism('sliding-window-fixed', slidingWindowFixedEvents, input);
    checkOneFramePerEvent('sliding-window-fixed', slidingWindowFixedEvents, input);
    const { input: gi } = run(slidingWindowFixedEvents, input);
    const n = gi.length;
    if (n === 0) continue;
    const k = Math.min(3, n);
    let bruteBest = -Infinity;
    for (let lo = 0; lo + k <= n; lo++) {
      let s = 0;
      for (let x = lo; x < lo + k; x++) s += gi[x];
      if (s > bruteBest) bruteBest = s;
    }
    const vars = lastVars(slidingWindowFixedEvents, input);
    ok(!!vars && vars.best === bruteBest,
      `sliding-window-fixed ${JSON.stringify(input)}: best=${vars && vars.best} matches brute force ${bruteBest}`);
  }
  console.log('  sliding-window-fixed: max window sum matches brute force');
}

// ---------------------------------------------------------------------------------------------
// sliding-window-variable: brute-force shortest qualifying window length (on the TRANSFORMED
// positive-int input + generator's own target derivation) must equal the final best_len.
// ---------------------------------------------------------------------------------------------
{
  const inputs = [[2, 4, 1, 5, 3, 6], [1, 1, 1, 1], [-3, 2, -1, 4], [5], []];
  for (const input of inputs) {
    checkDeterminism('sliding-window-variable', slidingWindowVariableEvents, input);
    checkOneFramePerEvent('sliding-window-variable', slidingWindowVariableEvents, input);
    const { input: gi } = run(slidingWindowVariableEvents, input);
    const n = gi.length;
    if (n === 0) continue;
    const total = gi.reduce((a, b) => a + b, 0);
    const target = Math.ceil(total / 2);
    let bruteLen = Infinity;
    for (let lo = 0; lo < n; lo++) {
      let s = 0;
      for (let hi = lo; hi < n; hi++) {
        s += gi[hi];
        if (s >= target) { bruteLen = Math.min(bruteLen, hi - lo + 1); break; }
      }
    }
    const vars = lastVars(slidingWindowVariableEvents, input);
    const gotLen = vars ? vars.best_len : null;
    ok(gotLen === (bruteLen === Infinity ? null : bruteLen),
      `sliding-window-variable ${JSON.stringify(input)}: best_len=${gotLen} matches brute force ${bruteLen === Infinity ? 'null' : bruteLen}`);
  }
  console.log('  sliding-window-variable: shortest qualifying window matches brute force');
}

// ---------------------------------------------------------------------------------------------
// kadane: brute-force max subarray sum (O(n^2)) must equal the final VAR best. Includes
// all-negative and already-sorted edge inputs — Kadane must NOT clip to 0 (no empty subarray).
// ---------------------------------------------------------------------------------------------
{
  const inputs = [[4, -2, 3, -5, 6, -1], [-5, -1, -8, -2], [1, 2, 3, 4], [-3], [3, 3, 3], []];
  for (const input of inputs) {
    checkDeterminism('kadane', kadaneEvents, input);
    checkOneFramePerEvent('kadane', kadaneEvents, input);
    const { input: gi } = run(kadaneEvents, input);
    const n = gi.length;
    if (n === 0) continue;
    let bruteBest = -Infinity;
    for (let lo = 0; lo < n; lo++) {
      let s = 0;
      for (let hi = lo; hi < n; hi++) {
        s += gi[hi];
        if (s > bruteBest) bruteBest = s;
      }
    }
    const vars = lastVars(kadaneEvents, input);
    ok(!!vars && vars.best === bruteBest,
      `kadane ${JSON.stringify(input)}: best=${vars && vars.best} matches brute force ${bruteBest}`);
  }
  console.log('  kadane: max subarray sum matches brute force (incl. all-negative)');
}

console.log(failures === 0 ? '\nALL GOLDEN CHECKS PASSED' : `\n${failures} CHECK(S) FAILED`);
process.exit(failures === 0 ? 0 : 1);
