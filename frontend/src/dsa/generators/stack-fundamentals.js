export function stackFundamentalsEvents(input) {
  const arr = Array.isArray(input) ? input.slice(0, 12) : [];
  const events = [];
  
  for (let i = 0; i < arr.length; i++) {
    events.push({ op: 'POINT', args: { i }, note: `Reading element ${arr[i]}` });
    events.push({ op: 'PUSH', args: { value: arr[i] }, step_id: 'push', note: `Pushing ${arr[i]} onto the stack.`, invariant: 'inv-lifo' });
  }
  
  for (let i = arr.length - 1; i >= 0; i--) {
    events.push({ op: 'POP', step_id: 'pop', note: `Popped ${arr[i]} from the top. Notice the LIFO order.`, invariant: 'inv-lifo' });
  }
  
  events.push({ op: 'DONE', step_id: 'done', note: 'All elements processed.', invariant: 'inv-lifo' });
  return { input: arr, events };
}
