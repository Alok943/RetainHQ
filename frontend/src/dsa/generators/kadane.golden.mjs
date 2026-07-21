import { kadaneEvents } from './kadane.js';
import { compile } from '../compile.js';

let failures = 0;
const ok = (cond, msg) => { if (!cond) { failures++; console.error('  [FAIL] ' + msg); } };

function check(input) {
  const { input: gi, events } = kadaneEvents(input);
  const frames = compile(gi, events);
  const again = kadaneEvents(input);
  ok(JSON.stringify(events) === JSON.stringify(again.events), 'deterministic');
  ok(frames.length === events.length, `one frame per event`);
  ok(frames.every(f => f.activeOp), 'every frame has activeOp');
  const n = gi.length;
  if (n > 0) {
    let bruteBest = -Infinity;
    for (let lo = 0; lo < n; lo++) {
      let s = 0;
      for (let hi = lo; hi < n; hi++) {
        s += gi[hi];
        if (s > bruteBest) bruteBest = s;
      }
    }
    let lastVars;
    for (let i = frames.length - 1; i >= 0; i--) {
      if (frames[i].vars) { lastVars = frames[i].vars; break; }
    }
    ok(lastVars && lastVars.best === bruteBest,
      `best=${lastVars && lastVars.best} matches brute ${bruteBest}`);
  }
  return { events: events.length, frames: frames.length };
}

console.log('kadane golden check\n');
for (const input of [[-2, 1, -3, 4, -1, 2, 1, -5, 4], [-5, -1, -8, -2], [1, 2, 3, 4], [-3], [3, 3, 3], []]) {
  const r = check(input);
  console.log(`  input ${JSON.stringify(input)} -> ${r.events} events`);
}
console.log(failures === 0 ? '\nALL GOLDEN CHECKS PASSED' : `\n${failures} CHECK(S) FAILED`);
process.exit(failures === 0 ? 0 : 1);
