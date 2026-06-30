// selectionSortEvents(input) -> { input, events }
// Selection sort: scan the unsorted suffix for the minimum, swap it to the front of that suffix,
// then mark the front sorted. Reuses POINT (current min vs scan) / SWAP / MARK. Pure, golden-tested.

export function selectionSortEvents(input) {
  const arr = [...input];
  const n = arr.length;
  const events = [];
  const E = (op, args, step_id, invariant, note) => events.push({ op, args, step_id, invariant, note });

  for (let i = 0; i < n - 1; i++) {
    let minIdx = i;
    E('POINT', { i: minIdx }, 'scan', 'inv-min', `find the smallest from index ${i} onward (min so far: arr[${minIdx}]=${arr[minIdx]})`);
    for (let j = i + 1; j < n; j++) {
      E('POINT', { i: minIdx, j }, 'compare', 'inv-min', `is arr[${j}]=${arr[j]} < current min arr[${minIdx}]=${arr[minIdx]}?`);
      if (arr[j] < arr[minIdx]) {
        minIdx = j;
        E('POINT', { i: minIdx }, 'newmin', 'inv-min', `new minimum: arr[${minIdx}]=${arr[minIdx]}`);
      }
    }
    if (minIdx !== i) {
      E('SWAP', { i, j: minIdx }, 'swap', 'inv-min', `swap the minimum into position ${i}`);
      const t = arr[i]; arr[i] = arr[minIdx]; arr[minIdx] = t;
    }
    E('MARK', { indices: [i] }, 'placed', 'inv-prefix', `index ${i} now holds its final value`);
  }
  if (n > 0) E('MARK', { indices: [n - 1] }, 'placed', 'inv-prefix', `the last element is sorted by elimination`);
  E('DONE', {}, 'done', 'inv-sorted', `the sorted prefix has grown to cover the whole array`);
  return { input: [...input], events };
}
