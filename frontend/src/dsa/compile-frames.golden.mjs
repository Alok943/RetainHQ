// Frame-snapshot guard: compiles EVERY registered generator with a fixed input and asserts the
// compiled frames are byte-identical to the committed baseline (__snapshots__/compile-frames.json).
// This is the zero-drift contract for refactoring compile.js — the frames are a presentation cache,
// so any change to their shape/content is caught here. Regenerate intentionally with `--update`
// (and say so in the commit). See docs/dsa-viz-implementation-plan.md (M0, D3).
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { GENERATORS } from './registry.js';
import { compile } from './compile.js';

const here = dirname(fileURLToPath(import.meta.url));
const snapPath = join(here, '__snapshots__', 'compile-frames.json');

// Fixed, deterministic input per generator (strings passed as char arrays where the viz is string-mode).
const INPUTS = {
  'merge-sort': [5, 2, 8, 1, 9, 3],
  'in-place-operations': [1, 2, 3, 4, 5],
  'prefix-sums': [2, 4, 1, 5, 3],
  'frequency-counting': [2, 3, 2, 1, 3, 2],
  'palindromes': ['r', 'a', 'c', 'e', 'c', 'a', 'r'],
  'two-pointers-on-strings': ['r', 'a', 'c', 'e', 'c', 'a', 'r'],
  'frequency-arrays': ['l', 'i', 's', 't', 'e', 'n'],
  'bubble-sort': [5, 2, 8, 1, 9],
  'selection-sort': [5, 2, 8, 1, 9],
  'insertion-sort': [5, 2, 8, 1, 9],
  'linear-search': [4, 2, 7, 1, 9, 3],
  'binary-search': [1, 3, 5, 7, 9, 11, 13],
  'two-pointers': [4, 1, 7, 3, 9, 2],
  'fast-slow-pointers': [5, 2, 8, 1, 9, 3],
  'sliding-window-fixed': [2, 4, 1, 5, 3, 6],
  'sliding-window-variable': [2, 4, 1, 5, 3, 6],
  'kadane': [4, -2, 3, -5, 6, -1],
};

function build() {
  const out = {};
  for (const key of Object.keys(GENERATORS).sort()) {
    const input = INPUTS[key];
    if (!input) { console.error(`  [FAIL] no fixed input defined for generator '${key}' — add one to INPUTS`); process.exitCode = 1; continue; }
    const { input: genInput, events } = GENERATORS[key](input);
    out[key] = compile(genInput ?? input, events);
  }
  return out;
}

const current = build();

if (process.argv.includes('--update')) {
  mkdirSync(dirname(snapPath), { recursive: true });
  writeFileSync(snapPath, JSON.stringify(current, null, 2) + '\n');
  console.log(`compile-frames snapshot WRITTEN for ${Object.keys(current).length} generators -> ${snapPath}`);
  process.exit(process.exitCode || 0);
}

let baseline;
try {
  baseline = JSON.parse(readFileSync(snapPath, 'utf8'));
} catch {
  console.error(`compile-frames: no baseline snapshot found. Create it with:\n  node src/dsa/compile-frames.golden.mjs --update`);
  process.exit(1);
}

let failures = 0;
const keys = new Set([...Object.keys(baseline), ...Object.keys(current)]);
for (const key of [...keys].sort()) {
  const a = JSON.stringify(baseline[key]);
  const b = JSON.stringify(current[key]);
  if (a === undefined) { failures++; console.error(`  [FAIL] '${key}' present now but not in baseline (run --update if intended)`); continue; }
  if (b === undefined) { failures++; console.error(`  [FAIL] '${key}' in baseline but not produced now`); continue; }
  if (a !== b) {
    failures++;
    console.error(`  [FAIL] '${key}' frames DRIFTED from baseline (${JSON.parse(a).length} vs ${JSON.parse(b).length} frames)`);
  }
}

console.log(failures === 0
  ? `compile-frames: all ${Object.keys(current).length} generators byte-identical to baseline.`
  : `compile-frames: ${failures} generator(s) DRIFTED.`);
process.exit(failures === 0 ? 0 : 1);
