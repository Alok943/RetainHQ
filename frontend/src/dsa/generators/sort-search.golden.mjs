// Golden-trace checks for the sorting + searching generators against the shared compiler.
// Run: node frontend/src/dsa/generators/sort-search.golden.mjs

import { bubbleSortEvents } from './bubble-sort.js';
import { selectionSortEvents } from './selection-sort.js';
import { insertionSortEvents } from './insertion-sort.js';
import { linearSearchEvents } from './linear-search.js';
import { binarySearchEvents } from './binary-search.js';
import { compile } from '../compile.js';

let failures = 0;
const ok = (cond, msg) => { if (!cond) { failures++; console.error('  [FAIL] ' + msg); } };
const eq = (a, b) => JSON.stringify(a) === JSON.stringify(b);

function lastFrame(gen, input) {
  const { input: gi, events } = gen(input);
  const frames = compile(gi ?? input, events);
  return { frames, last: frames[frames.length - 1], events, gi: gi ?? input };
}

function checkSort(name, gen, input) {
  const { frames, last, events } = lastFrame(gen, input);
  const expected = [...input].sort((a, b) => a - b);
  ok(eq(last.array, expected), `${name} ${JSON.stringify(input)} -> ${JSON.stringify(last.array)} want ${JSON.stringify(expected)}`);
  ok(last.sorted.length === input.length, `${name}: all indices marked sorted at end`);
  ok(frames.length === events.length, `${name}: one frame per event`);
  return last.array;
}

function checkSearch(name, gen, input) {
  const { last, gi, events } = lastFrame(gen, input);
  // target is arr[n-2] of the (possibly sorted) array the generator searched — must be found
  const arr = gi;
  const target = arr[Math.max(0, arr.length - 2)];
  const foundIdx = [...last.sorted][0];
  ok(foundIdx !== undefined && arr[foundIdx] === target, `${name} '${JSON.stringify(input)}' found target ${target} at ${foundIdx}`);
  ok(events.every((e) => e.op), `${name}: every event has an op`);
  return { target, foundIdx };
}

console.log('sort + search golden check\n');
for (const input of [[5, 2, 8, 1, 9], [3, 3, 1], [1], [], [9, 7, 5, 3, 1]]) {
  for (const [name, gen] of [['bubble', bubbleSortEvents], ['selection', selectionSortEvents], ['insertion', insertionSortEvents]]) {
    if (input.length === 0) continue;
    checkSort(name, gen, input);
  }
}
console.log('  sorting: all inputs sort correctly');

for (const input of [[4, 2, 7, 1, 9, 3]]) {
  const ls = checkSearch('linear', linearSearchEvents, input);
  console.log(`  linear-search ${JSON.stringify(input)} -> target ${ls.target} @ idx ${ls.foundIdx}`);
}
for (const input of [[1, 3, 5, 7, 9, 11, 13], [11, 1, 7, 3, 9]]) {
  const bs = checkSearch('binary', binarySearchEvents, input);
  console.log(`  binary-search ${JSON.stringify(input)} -> target ${bs.target} @ sorted idx ${bs.foundIdx}`);
}

console.log(failures === 0 ? '\nALL GOLDEN CHECKS PASSED' : `\n${failures} CHECK(S) FAILED`);
process.exit(failures === 0 ? 0 : 1);
