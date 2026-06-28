// mergeSortEvents(input) -> { input, events }
// The CANONICAL execution trace for top-down merge sort. Pure function of input (so "tweak the
// values" just re-runs it), deterministic, and golden-tested (merge-sort.golden.mjs) because a
// wrong event mis-teaches everywhere downstream. `invariant` fields are ids into the lesson
// model's invariants[]. See docs/dsa-architecture.md.

export function mergeSortEvents(input) {
  const arr = [...input];
  const events = [];
  const E = (op, args, step_id, invariant, note) =>
    events.push({ op, args, step_id, invariant, note });

  function sort(lo, hi) {
    E('CALL', { lo, hi }, 'recurse', 'inv-subarray', `mergeSort([${lo}..${hi}])`);
    if (lo >= hi) {
      E('MERGE_DONE', { lo, hi }, 'base', 'inv-sorted', `[${lo}] is one element — already sorted`);
      E('RETURN', { lo, hi }, 'recurse', null, 'return');
      return;
    }
    const mid = Math.floor((lo + hi) / 2);
    E('SPLIT', { lo, mid, hi }, 'split', 'inv-divide',
      `split into [${lo}..${mid}] and [${mid + 1}..${hi}]`);
    sort(lo, mid);
    sort(mid + 1, hi);
    merge(lo, mid, hi);
    E('RETURN', { lo, hi }, 'recurse', 'inv-sorted', `[${lo}..${hi}] now sorted`);
  }

  function merge(lo, mid, hi) {
    const left = arr.slice(lo, mid + 1);   // copies — reading them is safe while we overwrite arr
    const right = arr.slice(mid + 1, hi + 1);
    let i = 0, j = 0, k = lo;
    while (i < left.length && j < right.length) {
      E('COMPARE', { leftVal: left[i], rightVal: right[j], writeIndex: k }, 'merge', 'inv-merge',
        `compare ${left[i]} (left) vs ${right[j]} (right)`);
      if (left[i] <= right[j]) {
        E('WRITE', { index: k, value: left[i], from: 'left' }, 'merge', 'inv-merge',
          `write ${left[i]} → position ${k}`);
        arr[k++] = left[i++];
      } else {
        E('WRITE', { index: k, value: right[j], from: 'right' }, 'merge', 'inv-merge',
          `write ${right[j]} → position ${k}`);
        arr[k++] = right[j++];
      }
    }
    while (i < left.length) {
      E('WRITE', { index: k, value: left[i], from: 'left' }, 'merge', 'inv-merge',
        `drain left ${left[i]} → position ${k}`);
      arr[k++] = left[i++];
    }
    while (j < right.length) {
      E('WRITE', { index: k, value: right[j], from: 'right' }, 'merge', 'inv-merge',
        `drain right ${right[j]} → position ${k}`);
      arr[k++] = right[j++];
    }
    E('MERGE_DONE', { lo, hi }, 'merge', 'inv-sorted', `merged [${lo}..${hi}]`);
  }

  if (arr.length > 0) sort(0, arr.length - 1);
  return { input: [...input], events };
}
