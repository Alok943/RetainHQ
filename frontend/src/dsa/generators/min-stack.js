export function minStackEvents(input) {
  const arr = Array.isArray(input) ? input.slice(0, 12) : [];
  const events = [];
  const stack = [];
  const minStack = [];
  
  for (let i = 0; i < arr.length; i++) {
    events.push({ op: 'POINT', args: { i }, note: `Reading ${arr[i]}` });
    const val = arr[i];
    const newMin = minStack.length === 0 ? val : Math.min(val, minStack[minStack.length - 1]);
    stack.push(val);
    minStack.push(newMin);
    
    events.push({ op: 'PUSH', args: { value: val }, step_id: 'push', note: `Pushed ${val}.`, invariant: 'inv-min-tracks' });
    events.push({ op: 'VAR', args: { min: newMin }, note: `Running min is now ${newMin}.` });
  }
  
  const pops = Math.min(2, stack.length);
  for (let i = 0; i < pops; i++) {
    stack.pop();
    minStack.pop();
    const currentMin = minStack.length > 0 ? minStack[minStack.length - 1] : 'none';
    events.push({ op: 'POP', step_id: 'pop', note: `Popped top element.`, invariant: 'inv-min-tracks' });
    if (currentMin !== 'none') {
        events.push({ op: 'VAR', args: { min: currentMin }, note: `Running min is restored to ${currentMin}.` });
    } else {
        events.push({ op: 'VAR', args: { min: null }, note: `Stack is empty.` });
    }
  }
  
  events.push({ op: 'DONE', step_id: 'done', note: 'Finished.', invariant: 'inv-min-tracks' });
  return { input: arr, events };
}
