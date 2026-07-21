import { fastSlowPointersEvents } from './fast-slow-pointers.js';
import { compile } from '../compile.js';

let failures = 0;
const ok = (cond, msg) => { if (!cond) { failures++; console.error('  [FAIL] ' + msg); } };

function check(input) {
  const { input: gi, events } = fastSlowPointersEvents(input);
  const frames = compile(gi, events);
  const again = fastSlowPointersEvents(input);
  ok(JSON.stringify(events) === JSON.stringify(again.events), 'deterministic');
  ok(frames.length === events.length, `one frame per event`);
  ok(frames.every(f => f.activeOp), 'every frame has activeOp');
  const n = gi.length;
  if (n > 0) {
    const expected = Math.floor((n - 1) / 2);
    const mark = events.find(e => e.op === 'MARK');
    ok(mark && JSON.stringify(mark.args.indices) === JSON.stringify([expected]),
      `middle at floor((n-1)/2)=${expected}`);
  }
  return { events: events.length, frames: frames.length };
}

console.log('fast-slow-pointers golden check\n');
for (const input of [[10, 20, 30, 40, 50, 60], [1, 2, 3, 4, 5], [1, 2], [1], []]) {
  const r = check(input);
  console.log(`  input ${JSON.stringify(input)} -> ${r.events} events`);
}
console.log(failures === 0 ? '\nALL GOLDEN CHECKS PASSED' : `\n${failures} CHECK(S) FAILED`);
process.exit(failures === 0 ? 0 : 1);
