import { slidingWindowVariableEvents } from './sliding-window-variable.js';
import { compile } from '../compile.js';

let failures = 0;
const ok = (cond, msg) => { if (!cond) { failures++; console.error('  [FAIL] ' + msg); } };

function check(input) {
  const { input: gi, events } = slidingWindowVariableEvents(input);
  const frames = compile(gi, events);
  const again = slidingWindowVariableEvents(input);
  ok(JSON.stringify(events) === JSON.stringify(again.events), 'deterministic');
  ok(frames.length === events.length, `one frame per event`);
  ok(frames.every(f => f.activeOp), 'every frame has activeOp');
  const n = gi.length;
  if (n > 0) {
    const total = gi.reduce((a, b) => a + b, 0);
    const target = Math.ceil(total / 2);
    let bruteLen = Infinity;
    for (let lo = 0; lo < n; lo++) {
      let s = 0;
      for (let hi = lo; hi < n; hi++) {
        s += gi[hi];
        if (s >= target) { bruteLen = Math.min(bruteLen, hi - lo + 1); break; }
      }
    }
    let lastVars;
    for (let i = frames.length - 1; i >= 0; i--) {
      if (frames[i].vars) { lastVars = frames[i].vars; break; }
    }
    const got = lastVars ? lastVars.best_len : null;
    ok(got === (bruteLen === Infinity ? null : bruteLen),
      `best_len=${got} matches brute ${bruteLen === Infinity ? null : bruteLen}`);
  }
  return { events: events.length, frames: frames.length };
}

console.log('sliding-window-variable golden check\n');
for (const input of [[2, 4, 1, 5, 3, 6], [1, 1, 1, 1], [-3, 2, -1, 4], [5], []]) {
  const r = check(input);
  console.log(`  input ${JSON.stringify(input)} -> ${r.events} events`);
}
console.log(failures === 0 ? '\nALL GOLDEN CHECKS PASSED' : `\n${failures} CHECK(S) FAILED`);
process.exit(failures === 0 ? 0 : 1);
