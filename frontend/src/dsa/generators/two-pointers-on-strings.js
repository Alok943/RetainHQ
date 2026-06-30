// twoPointerStringEvents(input) -> { input, events }
// The archetypal two-pointers-on-a-string move: reverse a char array in place by swapping the ends
// and stepping inward. Same engine that powers reverse-vowels / valid-palindrome variants. Pure
// function of input, deterministic, golden-tested. Renders on the char-cell ArrayViz.

export function twoPointerStringEvents(input) {
  const arr = [...input];
  const events = [];
  const E = (op, args, step_id, invariant, note) =>
    events.push({ op, args, step_id, invariant, note });

  let lo = 0;
  let hi = arr.length - 1;

  if (arr.length <= 1) {
    E('DONE', {}, 'done', 'inv-reversed', '0 or 1 character — already reversed');
    return { input: [...input], events };
  }

  E('POINT', { lo, hi }, 'init', 'inv-bounds', `two pointers at the ends: '${arr[lo]}' and '${arr[hi]}'`);

  while (lo < hi) {
    E('SWAP', { i: lo, j: hi }, 'swap', 'inv-swap', `swap '${arr[lo]}' and '${arr[hi]}'`);
    const tmp = arr[lo]; arr[lo] = arr[hi]; arr[hi] = tmp;
    lo++; hi--;
    if (lo < hi) {
      E('POINT', { lo, hi }, 'move', 'inv-bounds', `step inward: '${arr[lo]}' and '${arr[hi]}'`);
    }
  }

  E('DONE', {}, 'done', 'inv-reversed', 'pointers met — string reversed using O(1) extra space');
  return { input: [...input], events };
}
