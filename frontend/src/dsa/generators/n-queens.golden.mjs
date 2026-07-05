import { nQueensEvents } from './n-queens.js';
import { compile } from '../compile.js';

let failures = 0;
const ok = (cond, msg) => { if (!cond) { failures++; console.error('  [FAIL] ' + msg); } };

function check(N) {
  const events = nQueensEvents(N);
  // Grid generators don't use input for array, pass empty array
  const frames = compile([], events);

  // 1) determinism
  const again = nQueensEvents(N);
  ok(JSON.stringify(events) === JSON.stringify(again), 'generator is deterministic');

  // 2) CALL/RETURN balance
  let depth = 0, maxDepth = 0;
  for (const e of events) {
    if (e.op === 'CALL') { depth++; maxDepth = Math.max(maxDepth, depth); }
    if (e.op === 'RETURN') depth--;
    ok(depth >= 0, 'RETURN never precedes its CALL');
  }
  ok(depth === 0, 'every CALL has a matching RETURN');

  // 3) compiled frames
  ok(frames.length === events.length, 'one frame per event');
  ok(frames.every((f) => f.activeOp), 'every frame has an activeOp');

  const ops = events.reduce((m, e) => ((m[e.op] = (m[e.op] || 0) + 1), m), {});
  return { events: events.length, frames: frames.length, maxDepth, ops };
}

console.log('n-queens golden check\n');
for (const N of [1, 2, 4]) {
  const r = check(N);
  console.log(`  input N=${N} -> ${r.events} events, depth ${r.maxDepth}`);
}

const main = check(4);
console.log('\n  fingerprint (default N=4):');
console.log('   ', JSON.stringify(main.ops));

console.log(failures === 0 ? '\nALL GOLDEN CHECKS PASSED' : `\n${failures} CHECK(S) FAILED`);
process.exit(failures === 0 ? 0 : 1);
