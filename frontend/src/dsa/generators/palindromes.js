// palindromeEvents(input) -> { input, events }
// Two-pointer palindrome check on a char array: compare the ends, mark matched outer pairs, step
// inward until the pointers meet (palindrome) or a pair mismatches (not). Pure function of input,
// deterministic, golden-tested. Renders on the char-cell ArrayViz. See docs/dsa-architecture.md.

export function palindromeEvents(input) {
  const arr = [...input];
  const events = [];
  const E = (op, args, step_id, invariant, note) =>
    events.push({ op, args, step_id, invariant, note });

  let lo = 0;
  let hi = arr.length - 1;

  if (arr.length <= 1) {
    E('DONE', {}, 'done', 'inv-palindrome', 'a single character (or empty) is trivially a palindrome');
    return { input: [...input], events };
  }

  E('POINT', { lo, hi }, 'init', 'inv-bounds', `compare the ends: '${arr[lo]}' vs '${arr[hi]}'`);

  let isPalindrome = true;
  while (lo < hi) {
    if (arr[lo] === arr[hi]) {
      E('MARK', { indices: [lo, hi] }, 'match', 'inv-match',
        `'${arr[lo]}' == '${arr[hi]}' — outer pair matches`);
      lo++; hi--;
      if (lo < hi) {
        E('POINT', { lo, hi }, 'move', 'inv-bounds', `move inward: '${arr[lo]}' vs '${arr[hi]}'`);
      }
    } else {
      E('POINT', { lo, hi }, 'mismatch', 'inv-match',
        `'${arr[lo]}' != '${arr[hi]}' — mismatch, NOT a palindrome`);
      isPalindrome = false;
      break;
    }
  }

  if (isPalindrome) {
    E('DONE', {}, 'done', 'inv-palindrome', 'every pair matched — it IS a palindrome');
  }
  return { input: [...input], events };
}
