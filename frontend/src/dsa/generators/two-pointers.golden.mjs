import { twoPointersEvents } from './two-pointers.js';
import { compile } from '../compile.js';

let failures = 0;
const ok = (cond, msg) => { if (!cond) { failures++; console.error('  [FAIL] ' + msg); } };

function check(input) {
  const { input: sorted, events } = twoPointersEvents(input);
  const frames = compile(sorted, events);

  // 1) determinism
  const again = twoPointersEvents(input);
  ok(JSON.stringify(events) === JSON.stringify(again.events), 'deterministic');

  // 2) one frame per event
  ok(frames.length === events.length, `one frame per event (${frames.length} vs ${events.length})`);

  // 3) every frame has activeOp
  ok(frames.every(f => f.activeOp), 'every frame has activeOp');

  // 4) pair sums to target (brute force verify)
  const n = sorted.length;
  if (n >= 2) {
    const target = sorted[1] + sorted[n - 2];
    const markEvent = events.find(e => e.op === 'MARK');
    if (markEvent) {
      const [i, j] = markEvent.args.indices;
      ok(sorted[i] + sorted[j] === target, `MARK pair sums to target ${target}`);
    }
  }

  return { events: events.length, frames: frames.length };
}

console.log('two-pointers golden check\n');
for (const input of [[4, 1, 7, 3, 9, 2], [5, 5, 5], [1, 2], [1], []]) {
  const r = check(input);
  console.log(`  input ${JSON.stringify(input)} -> ${r.events} events, ${r.frames} frames`);
}
console.log(failures === 0 ? '\nALL GOLDEN CHECKS PASSED' : `\n${failures} CHECK(S) FAILED`);
process.exit(failures === 0 ? 0 : 1);
