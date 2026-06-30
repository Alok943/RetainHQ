// insertionSortEvents(input) -> { input, events }
// Insertion sort: grow a sorted prefix; take the next element and shift larger sorted elements
// right (via swaps) until it lands in place. Reuses POINT / SWAP. Pure, deterministic, golden-tested.

export function insertionSortEvents(input) {
  const arr = [...input];
  const n = arr.length;
  const events = [];
  const E = (op, args, step_id, invariant, note) => events.push({ op, args, step_id, invariant, note });

  for (let i = 1; i < n; i++) {
    E('POINT', { i }, 'pick', 'inv-prefix', `arr[0..${i - 1}] is sorted; insert arr[${i}]=${arr[i]} into it`);
    let j = i;
    while (j > 0 && arr[j - 1] > arr[j]) {
      E('POINT', { i: j - 1, j }, 'compare', 'inv-shift', `arr[${j - 1}]=${arr[j - 1]} > arr[${j}]=${arr[j]} — shift it right`);
      E('SWAP', { i: j - 1, j }, 'swap', 'inv-shift', `swap to slide the value left`);
      const t = arr[j - 1]; arr[j - 1] = arr[j]; arr[j] = t;
      j--;
    }
    if (j === i) {
      E('POINT', { i }, 'inplace', 'inv-prefix', `arr[${i}] is already ≥ its left neighbour — stays put`);
    }
  }
  E('DONE', {}, 'done', 'inv-sorted', `each element was inserted into the growing sorted prefix`);
  return { input: [...input], events };
}
