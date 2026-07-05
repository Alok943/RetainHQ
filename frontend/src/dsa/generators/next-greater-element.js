export function nextGreaterElementEvents(input) {
  const arr = Array.isArray(input) ? input.slice(0, 12) : [];
  const events = [];
  const stack = [];
  
  for (let i = 0; i < arr.length; i++) {
    events.push({ op: 'POINT', args: { i }, step_id: 'read', note: `Reading element ${arr[i]} at index ${i}` });
    
    while (stack.length > 0 && arr[stack[stack.length - 1]] < arr[i]) {
      const top = stack.pop();
      events.push({ 
        op: 'POP', 
        step_id: 'resolve', 
        note: `Popped index ${top} (value ${arr[top]}). Next greater is ${arr[i]}.`, 
        invariant: 'inv-monotonic' 
      });
      events.push({ op: 'MARK', args: { indices: [top] }, note: `Index ${top} resolved.` });
    }
    
    stack.push(i);
    events.push({ op: 'PUSH', args: { value: i }, step_id: 'push', note: `Pushed index ${i}.`, invariant: 'inv-monotonic' });
  }
  
  events.push({ op: 'DONE', step_id: 'done', note: 'All elements processed.', invariant: 'inv-monotonic' });
  return { input: arr, events };
}
