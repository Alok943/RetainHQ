import { slidingWindowFixedEvents } from './sliding-window-fixed.js';
import { compile } from '../compile.js';

let failures = 0;
const ok = (cond, msg) => { if (!cond) { failures++; console.error('  [FAIL] ' + msg); } };

function check(input) {
  const { input: gi, events } = slidingWindowFixedEvents(input);
  const frames = compile(gi, events);
  const again = slidingWindowFixedEvents(input);
  ok(JSON.stringify(events) === JSON.stringify(again.events), 'deterministic');
  ok(frames.length === events.length, `one frame per event`);
  ok(frames.every(f => f.activeOp), 'every frame has activeOp');
  const n = gi.length;
  if (n > 0) {
    const k = Math.min(3, n);
    let bruteBest = -Infinity;
    for (let lo = 0; lo + k <= n; lo++) {
      let s = 0;
      for (let x = lo; x < lo + k; x++) s += gi[x];
      if (s > bruteBest) bruteBest = s;
    }
    let lastVars;
    for (let i = frames.length - 1; i >= 0; i--) {
      if (frames[i].vars) { lastVars = frames[i].vars; break; }
    }
    ok(lastVars && lastVars.best === bruteBest, `best=${lastVars && lastVars.best} matches brute ${bruteBest}`);
  }
  return { events: events.length, frames: frames.length };
}

console.log('sliding-window-fixed golden check\n');
for (const input of [[2, 4, 1, 5, 3, 6], [1, 1, 1], [7, -1], [4], []]) {
  const r = check(input);
  console.log(`  input ${JSON.stringify(input)} -> ${r.events} events`);
}
console.log(failures === 0 ? '\nALL GOLDEN CHECKS PASSED' : `\n${failures} CHECK(S) FAILED`);
process.exit(failures === 0 ? 0 : 1);
