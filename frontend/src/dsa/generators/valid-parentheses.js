export function validParenthesesEvents(input) {
  // Accept either a string ("([])") or a char array (the Player passes default_input as an array).
  const src = Array.isArray(input) ? input.join('') : (typeof input === 'string' ? input : "([]{})");
  const str = src.slice(0, 12);
  const arr = str.split('');
  const events = [];
  const stack = [];
  const pairs = { ')': '(', ']': '[', '}': '{' };
  
  let mismatch = false;
  for (let i = 0; i < arr.length; i++) {
    const char = arr[i];
    events.push({ op: 'POINT', args: { i }, step_id: 'read', note: `Reading '${char}'.` });
    
    if (char === '(' || char === '[' || char === '{') {
      stack.push(char);
      events.push({ op: 'PUSH', args: { value: char }, step_id: 'push', note: `Pushed opener '${char}'.`, invariant: 'inv-match' });
    } else if (char === ')' || char === ']' || char === '}') {
      if (stack.length > 0 && stack[stack.length - 1] === pairs[char]) {
        const top = stack.pop();
        events.push({ op: 'POP', step_id: 'pop', note: `Matched '${char}' with top '${top}'. Popping it.`, invariant: 'inv-match' });
      } else {
        events.push({ op: 'MARK', args: { indices: [i] }, step_id: 'mismatch', note: `Mismatch! '${char}' doesn't match top of stack.`, invariant: 'inv-valid' });
        mismatch = true;
        break;
      }
    }
  }
  
  if (!mismatch) {
    if (stack.length === 0) {
      events.push({ op: 'DONE', step_id: 'done', note: 'String is valid.', invariant: 'inv-valid' });
    } else {
      events.push({ op: 'DONE', step_id: 'done', note: 'String is invalid (unmatched openers left).', invariant: 'inv-valid' });
    }
  }
  
  return { input: arr, events };
}
