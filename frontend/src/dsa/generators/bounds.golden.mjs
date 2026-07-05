// Golden-trace checks for the lower-bound / upper-bound generators against the shared compiler.
// Run: node frontend/src/dsa/generators/bounds.golden.mjs

import { lowerBoundEvents } from './lower-bound.js';
import { upperBoundEvents } from './upper-bound.js';
import { compile } from '../compile.js';

let failures = 0;
const ok = (cond, msg) => { if (!cond) { failures++; console.error('  [FAIL] ' + msg); } };
const eq = (a, b) => JSON.stringify(a) === JSON.stringify(b);

function landingIndex(events) {
  const land = events.find((e) => e.step_id === 'land');
  if (!land) return undefined;
  const idx = land.args.indices;
  return idx && idx.length ? idx[0] : undefined; // undefined means "landed past the end"
}

function checkDeterminism(name, gen, input) {
  const a = gen(input);
  const b = gen(input);
  ok(eq(a.events, b.events), `${name} ${JSON.stringify(input)}: deterministic (same events on repeat run)`);
  ok(eq(a.input, b.input), `${name} ${JSON.stringify(input)}: deterministic (same sorted input on repeat run)`);
}

function checkFrames(name, gen, input) {
  const { input: gi, events } = gen(input);
  const frames = compile(gi ?? input, events);
  ok(frames.length === events.length, `${name} ${JSON.stringify(input)}: one frame per event`);
  return { gi: gi ?? input, events, frames };
}

function checkLanding(name, gen, input, refFn) {
  const { input: sorted, events } = gen(input);
  const n = sorted.length;
  const target = sorted[Math.floor(n / 2)];
  const refIdx = refFn(sorted, target); // n means "past the end"
  const landed = landingIndex(events);
  const landedIdx = landed === undefined ? n : landed;
  ok(landedIdx === refIdx, `${name} ${JSON.stringify(input)} target=${target}: MARK landed at ${landedIdx}, reference says ${refIdx}`);
  return { target, refIdx, landedIdx };
}

const lowerRef = (sorted, target) => {
  const i = sorted.findIndex((x) => x >= target);
  return i === -1 ? sorted.length : i;
};
const upperRef = (sorted, target) => {
  const i = sorted.findIndex((x) => x > target);
  return i === -1 ? sorted.length : i;
};

console.log('lower-bound / upper-bound golden check\n');

const inputs = [[1, 3, 5, 7, 9, 11, 13], [4, 2, 7, 1, 9, 3], [5, 5, 5, 1, 9], [2], []];

for (const input of inputs) {
  checkDeterminism('lower-bound', lowerBoundEvents, input);
  checkDeterminism('upper-bound', upperBoundEvents, input);
  checkFrames('lower-bound', lowerBoundEvents, input);
  checkFrames('upper-bound', upperBoundEvents, input);
  if (input.length === 0) continue; // landing/reference asserts skip the empty case
  const lb = checkLanding('lower-bound', lowerBoundEvents, input, lowerRef);
  const ub = checkLanding('upper-bound', upperBoundEvents, input, upperRef);
  console.log(`  ${JSON.stringify(input)} target=${lb.target}: lower-bound -> ${lb.landedIdx}, upper-bound -> ${ub.landedIdx}`);
}

// Explicit edge cases (the whole teaching point): target beyond all elements, and duplicates.
{
  // duplicates: lower-bound lands on the FIRST dup, upper-bound lands AFTER the last dup
  const input = [5, 5, 5, 1, 9];
  const sorted = [...input].sort((a, b) => a - b); // [1,5,5,5,9], target = sorted[2] = 5
  const { events: lbEvents } = lowerBoundEvents(input);
  const { events: ubEvents } = upperBoundEvents(input);
  const lbIdx = landingIndex(lbEvents);
  const ubIdx = landingIndex(ubEvents);
  ok(sorted[lbIdx] === 5 && lbIdx === sorted.indexOf(5), `duplicates: lower-bound lands on FIRST dup (idx ${lbIdx}, expected ${sorted.indexOf(5)})`);
  ok(sorted[ubIdx - 1] === 5 && (ubIdx === sorted.length || sorted[ubIdx] !== 5), `duplicates: upper-bound lands AFTER last dup (idx ${ubIdx})`);
  ok(lbIdx < ubIdx, `duplicates: lower-bound index (${lbIdx}) < upper-bound index (${ubIdx})`);
}
{
  // target exceeds every element -> lands at n (past the end) for both
  // sorted[floor(n/2)] is always <= max, so force it by using a single-element array where the
  // generator's own target equals the only (and thus max) element, then upper-bound must land at n.
  const input = [7];
  const { events: ubEvents } = upperBoundEvents(input);
  const idx = landingIndex(ubEvents);
  ok(idx === undefined, `single element [7], target=7: upper-bound lands past the end (n=1)`);
  const { events: lbEvents } = lowerBoundEvents(input);
  const lidx = landingIndex(lbEvents);
  ok(lidx === 0, `single element [7], target=7: lower-bound lands AT index 0`);
}

console.log(failures === 0 ? '\nALL GOLDEN CHECKS PASSED' : `\n${failures} CHECK(S) FAILED`);
process.exit(failures === 0 ? 0 : 1);
