// bubbleSortEvents(input) -> { input, events }
// Bubble sort: repeatedly compare adjacent pairs and swap out-of-order ones; after each pass the
// largest unsorted element "bubbles" to the end and is marked sorted. Reuses the array-family
// vocab (POINT compare / SWAP / MARK). Pure, deterministic, golden-tested.

export function bubbleSortEvents(input) {
  const arr = [...input];
  const n = arr.length;
  const events = [];
  const E = (op, args, step_id, invariant, note) => events.push({ op, args, step_id, invariant, note });

  for (let i = 0; i < n - 1; i++) {
    for (let j = 0; j < n - 1 - i; j++) {
      E('POINT', { i: j, j: j + 1 }, 'compare', 'inv-bubble',
        `compare arr[${j}]=${arr[j]} and arr[${j + 1}]=${arr[j + 1]}`);
      if (arr[j] > arr[j + 1]) {
        E('SWAP', { i: j, j: j + 1 }, 'swap', 'inv-bubble', `out of order — swap them`);
        const t = arr[j]; arr[j] = arr[j + 1]; arr[j + 1] = t;
      }
    }
    E('MARK', { indices: [n - 1 - i] }, 'placed', 'inv-largest',
      `largest of the unsorted part has bubbled to index ${n - 1 - i} — locked in`);
  }
  if (n > 0) E('MARK', { indices: [0] }, 'placed', 'inv-largest', `index 0 is now sorted too`);
  E('DONE', {}, 'done', 'inv-sorted', `every pass placed one element — the array is sorted`);
  return { input: [...input], events };
}
