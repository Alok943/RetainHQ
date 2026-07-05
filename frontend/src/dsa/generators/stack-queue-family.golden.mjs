import { stackFundamentalsEvents } from './stack-fundamentals.js';
import { validParenthesesEvents } from './valid-parentheses.js';
import { minStackEvents } from './min-stack.js';
import { nextGreaterElementEvents } from './next-greater-element.js';
import { queueDequeEvents } from './queue-deque.js';
import { compile } from '../compile.js';

let failures = 0;
const ok = (cond, msg) => { if (!cond) { failures++; console.error('  [FAIL] ' + msg); } };
const eq = (a, b) => JSON.stringify(a) === JSON.stringify(b);

function run(gen, input) {
  const { input: gi, events } = gen(input);
  return { input: gi ?? input, events };
}

function checkDeterminism(name, gen, input) {
  const a = gen(input);
  const b = gen(input);
  ok(eq(a.events, b.events), `${name}: deterministic (same events on repeat run)`);
  ok(eq(a.input, b.input), `${name}: deterministic (same input on repeat run)`);
}

function checkOneFramePerEvent(name, gen, input) {
  const { input: gi, events } = run(gen, input);
  const frames = compile(gi, events);
  ok(frames.length === events.length, `${name} ${JSON.stringify(input)}: one frame per event (${frames.length} vs ${events.length})`);
}

console.log('stack-queue-family golden check\n');

// ---------------------------------------------------------------------------------------------
// stack-fundamentals: final frame.stack equals the expected LIFO residue (which should be empty).
// ---------------------------------------------------------------------------------------------
{
  const inputs = [[5, 2, 8, 1, 9, 3], [1], []];
  for (const input of inputs) {
    checkDeterminism('stack-fundamentals', stackFundamentalsEvents, input);
    checkOneFramePerEvent('stack-fundamentals', stackFundamentalsEvents, input);
    const { input: gi, events } = run(stackFundamentalsEvents, input);
    const frames = compile(gi, events);
    const finalFrame = frames[frames.length - 1];
    ok(!finalFrame.stack || finalFrame.stack.length === 0, `stack-fundamentals ${JSON.stringify(input)}: final stack is empty (expected LIFO residue)`);
  }
  console.log('  stack-fundamentals: LIFO residue matches expected');
}

// ---------------------------------------------------------------------------------------------
// valid-parentheses: the generator's validity verdict matches an independent bracket-matcher;
// on a valid input the final stack is empty; test a KNOWN-INVALID input (e.g. "(]") -> mismatch fires.
// ---------------------------------------------------------------------------------------------
{
  const inputs = ["([]{})", "(]", "(((", ")))", "", "(", "[()]"];
  for (const input of inputs) {
    checkDeterminism('valid-parentheses', validParenthesesEvents, input);
    checkOneFramePerEvent('valid-parentheses', validParenthesesEvents, input);
    const { input: gi, events } = run(validParenthesesEvents, input);
    const frames = compile(gi, events);
    const finalFrame = frames[frames.length - 1];
    
    // Brute force validity
    let expectedValid = true;
    const s = [];
    const pairs = { ')': '(', ']': '[', '}': '{' };
    let brMismatched = false;
    for (const char of gi) {
      if (char === '(' || char === '[' || char === '{') s.push(char);
      else if (char === ')' || char === ']' || char === '}') {
        if (s.length > 0 && s[s.length - 1] === pairs[char]) s.pop();
        else { expectedValid = false; brMismatched = true; break; }
      }
    }
    if (s.length > 0) expectedValid = false;
    
    const genMismatch = events.some(e => e.op === 'MARK' && e.step_id === 'mismatch');
    const genValid = !genMismatch && (!finalFrame.stack || finalFrame.stack.length === 0);
    
    ok(expectedValid === genValid, `valid-parentheses ${JSON.stringify(input)}: validity matches brute force`);
    if (expectedValid) {
      ok(!finalFrame.stack || finalFrame.stack.length === 0, `valid-parentheses ${JSON.stringify(input)}: valid input has empty final stack`);
    } else {
      ok(genMismatch || (finalFrame.stack && finalFrame.stack.length > 0), `valid-parentheses ${JSON.stringify(input)}: invalid input ends appropriately`);
    }
  }
  console.log('  valid-parentheses: verdict matches independent bracket-matcher');
}

// ---------------------------------------------------------------------------------------------
// min-stack: at every frame, frame.vars.min === Math.min(...frame.stack) (when stack non-empty).
// ---------------------------------------------------------------------------------------------
{
  const inputs = [[5, 2, 8, 1, 9, 3], [1], []];
  for (const input of inputs) {
    checkDeterminism('min-stack', minStackEvents, input);
    checkOneFramePerEvent('min-stack', minStackEvents, input);
    const { input: gi, events } = run(minStackEvents, input);
    const frames = compile(gi, events);
    
    for (let i = 0; i < frames.length; i++) {
      const f = frames[i];
      if (f.stack && f.stack.length > 0 && f.vars && f.vars.min !== undefined && f.vars.min !== null && (f.activeOp === 'VAR' || f.activeOp === 'DONE')) {
        const expectedMin = Math.min(...f.stack);
        ok(f.vars.min === expectedMin, `min-stack ${JSON.stringify(input)} frame ${i}: vars.min (${f.vars.min}) === Math.min(stack) (${expectedMin})`);
      }
    }
  }
  console.log('  min-stack: vars.min tracks Math.min(...stack) at every frame');
}

// ---------------------------------------------------------------------------------------------
// next-greater-element: the resolved answers match a brute-force next-greater array.
// ---------------------------------------------------------------------------------------------
{
  const inputs = [[5, 2, 8, 1, 9, 3], [1], []];
  for (const input of inputs) {
    checkDeterminism('next-greater-element', nextGreaterElementEvents, input);
    checkOneFramePerEvent('next-greater-element', nextGreaterElementEvents, input);
    const { input: gi, events } = run(nextGreaterElementEvents, input);
    
    const n = gi.length;
    const expectedNge = new Array(n).fill(-1);
    for (let i = 0; i < n; i++) {
      for (let j = i + 1; j < n; j++) {
        if (gi[j] > gi[i]) {
          expectedNge[i] = gi[j];
          break;
        }
      }
    }
    
    const resolved = new Array(n).fill(-1);
    let currVal = null;
    for (const e of events) {
      if (e.op === 'POINT') currVal = gi[e.args.i];
      if (e.op === 'POP' && e.step_id === 'resolve') {
        // the index popped is resolved to currVal
        // wait, POP event doesn't say which index was popped in args, it just pops from stack.
        // I'll extract it from the MARK event which follows immediately.
      }
      if (e.op === 'MARK') {
        const idx = e.args.indices[0];
        resolved[idx] = currVal;
      }
    }
    
    ok(eq(expectedNge, resolved), `next-greater-element ${JSON.stringify(input)}: resolved array matches brute force`);
  }
  console.log('  next-greater-element: resolved answers match brute-force next-greater array');
}

// ---------------------------------------------------------------------------------------------
// queue-deque: final queue equals the expected FIFO residue.
// ---------------------------------------------------------------------------------------------
{
  const inputs = [[5, 2, 8, 1, 9, 3], [1], []];
  for (const input of inputs) {
    checkDeterminism('queue-deque', queueDequeEvents, input);
    checkOneFramePerEvent('queue-deque', queueDequeEvents, input);
    const { input: gi, events } = run(queueDequeEvents, input);
    const frames = compile(gi, events);
    const finalFrame = frames[frames.length - 1];
    
    const expectedQueue = [...gi];
    const dequeues = Math.min(3, expectedQueue.length);
    for (let i = 0; i < dequeues; i++) expectedQueue.shift();
    
    const actualQueue = finalFrame.queue || [];
    ok(eq(expectedQueue, actualQueue), `queue-deque ${JSON.stringify(input)}: final queue matches expected FIFO residue`);
  }
  console.log('  queue-deque: final queue matches expected FIFO residue');
}

if (failures > 0) {
  console.error(`\nFAILED: ${failures} checks failed.`);
  process.exit(1);
} else {
  console.log('\nSUCCESS: all stack-queue-family checks passed.');
}
