import { backtrackingTemplateEvents } from './backtracking-template.js';
import { compile } from '../compile.js';

let failures = 0;
const ok = (cond, msg) => { if (!cond) { failures++; console.error('  [FAIL] ' + msg); } };

function check(depth) {
  const events = backtrackingTemplateEvents(depth);
  const frames = compile([], events);

  // 1) determinism
  const again = backtrackingTemplateEvents(depth);
  ok(JSON.stringify(events) === JSON.stringify(again), 'generator is deterministic');

  // 2) CALL/RETURN balance
  let d = 0, maxDepth = 0;
  for (const e of events) {
    if (e.op === 'CALL') { d++; maxDepth = Math.max(maxDepth, d); }
    if (e.op === 'RETURN') d--;
    ok(d >= 0, 'RETURN never precedes its CALL');
  }
  ok(d === 0, 'every CALL has a matching RETURN');

  // 3) compiled frames
  ok(frames.length === events.length, 'one frame per event');
  ok(frames.every((f) => f.activeOp), 'every frame has an activeOp');

  const ops = events.reduce((m, e) => ((m[e.op] = (m[e.op] || 0) + 1), m), {});
  return { events: events.length, frames: frames.length, maxDepth, ops };
}

console.log('backtracking-template golden check\n');
for (const depth of [2, 3]) {
  const r = check(depth);
  console.log(`  input depth=${depth} -> ${r.events} events, depth ${r.maxDepth}`);
}

const main = check(3);
console.log('\n  fingerprint (default depth=3):');
console.log('   ', JSON.stringify(main.ops));

console.log(failures === 0 ? '\nALL GOLDEN CHECKS PASSED' : `\n${failures} CHECK(S) FAILED`);
process.exit(failures === 0 ? 0 : 1);
