export function queueDequeEvents(input) {
  const arr = Array.isArray(input) ? input.slice(0, 12) : [];
  const events = [];
  const queue = [];
  
  for (let i = 0; i < arr.length; i++) {
    events.push({ op: 'POINT', args: { i }, note: `Reading ${arr[i]}` });
    queue.push(arr[i]);
    events.push({ op: 'ENQUEUE', args: { value: arr[i] }, step_id: 'enqueue', note: `Enqueued ${arr[i]}.`, invariant: 'inv-fifo' });
  }
  
  const dequeues = Math.min(3, queue.length);
  for (let i = 0; i < dequeues; i++) {
    const val = queue.shift();
    events.push({ op: 'DEQUEUE', step_id: 'dequeue', note: `Dequeued ${val}. Notice the FIFO order.`, invariant: 'inv-fifo' });
  }
  
  events.push({ op: 'DONE', step_id: 'done', note: 'Finished.', invariant: 'inv-fifo' });
  return { input: arr, events };
}
