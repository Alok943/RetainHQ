// Golden-trace checks for the string-family generators (palindrome / two-pointer reverse / freq
// array) against the shared compiler. Run: node frontend/src/dsa/generators/string-family.golden.mjs

import { palindromeEvents } from './palindromes.js';
import { twoPointerStringEvents } from './two-pointers-on-strings.js';
import { frequencyArrayEvents } from './frequency-arrays.js';
import { compile } from '../compile.js';

let failures = 0;
const ok = (cond, msg) => { if (!cond) { failures++; console.error('  [FAIL] ' + msg); } };
const eq = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const chars = (s) => s.split('');

function checkPalindrome(word, expectPal) {
  const input = chars(word);
  const { events } = palindromeEvents(input);
  const frames = compile(input, events);
  ok(eq(events, palindromeEvents(input).events), `pal '${word}': deterministic`);
  const last = frames[frames.length - 1];
  // a true palindrome ends fully marked; a non-palindrome stops early (not all marked)
  const allMarked = last.sorted.length === input.length;
  ok(allMarked === expectPal, `pal '${word}': palindrome=${expectPal} (got allMarked=${allMarked})`);
  return last.sorted.length;
}

function checkReverse(word) {
  const input = chars(word);
  const { events } = twoPointerStringEvents(input);
  const frames = compile(input, events);
  const last = frames[frames.length - 1];
  ok(eq(last.array, chars(word).reverse()), `reverse '${word}' -> ${JSON.stringify(last.array)}`);
  return last.array.join('');
}

function checkFreq(word) {
  const input = chars(word);
  const { events } = frequencyArrayEvents(input);
  const frames = compile(input, events);
  const last = frames[frames.length - 1];
  const expected = {};
  for (const c of input) expected[c] = (expected[c] || 0) + 1;
  ok(eq(last.map || {}, expected), `freq '${word}' -> ${JSON.stringify(last.map)}`);
  return last.map;
}

console.log('string-family golden check\n');
for (const [w, p] of [['racecar', true], ['noon', true], ['hello', false], ['a', true], ['ab', false]]) {
  const marked = checkPalindrome(w, p);
  console.log(`  palindrome '${w}'`.padEnd(26) + ` -> palindrome=${p}, marked ${marked}`);
}
console.log('');
for (const w of ['hello', 'ab', 'racecar']) {
  console.log(`  reverse '${w}'`.padEnd(26) + ` -> '${checkReverse(w)}'`);
}
console.log('');
for (const w of ['banana', 'aaa', 'abc']) {
  console.log(`  freq '${w}'`.padEnd(26) + ` -> ${JSON.stringify(checkFreq(w))}`);
}

console.log(failures === 0 ? '\nALL GOLDEN CHECKS PASSED' : `\n${failures} CHECK(S) FAILED`);
process.exit(failures === 0 ? 0 : 1);
