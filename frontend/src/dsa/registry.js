// Maps a lesson's `viz.generator` key -> its event generator. validate.py checks a lesson's
// key exists here so a lesson can never reference a missing visualizer. Add a line per algorithm.
import { mergeSortEvents } from './generators/merge-sort.js';
import { inPlaceReverseEvents } from './generators/in-place-operations.js';
import { prefixSumsEvents } from './generators/prefix-sums.js';
import { frequencyCountEvents } from './generators/frequency-counting.js';
import { palindromeEvents } from './generators/palindromes.js';
import { twoPointerStringEvents } from './generators/two-pointers-on-strings.js';
import { frequencyArrayEvents } from './generators/frequency-arrays.js';
import { bubbleSortEvents } from './generators/bubble-sort.js';
import { selectionSortEvents } from './generators/selection-sort.js';
import { insertionSortEvents } from './generators/insertion-sort.js';
import { linearSearchEvents } from './generators/linear-search.js';
import { binarySearchEvents } from './generators/binary-search.js';
import { twoPointersEvents } from './generators/two-pointers.js';
import { fastSlowPointersEvents } from './generators/fast-slow-pointers.js';
import { slidingWindowFixedEvents } from './generators/sliding-window-fixed.js';
import { slidingWindowVariableEvents } from './generators/sliding-window-variable.js';
import { kadaneEvents } from './generators/kadane.js';
import { lowerBoundEvents } from './generators/lower-bound.js';
import { upperBoundEvents } from './generators/upper-bound.js';
import { stackFundamentalsEvents } from './generators/stack-fundamentals.js';
import { validParenthesesEvents } from './generators/valid-parentheses.js';
import { minStackEvents } from './generators/min-stack.js';
import { nextGreaterElementEvents } from './generators/next-greater-element.js';
import { queueDequeEvents } from './generators/queue-deque.js';

export const GENERATORS = {
  'merge-sort': mergeSortEvents,
  'in-place-operations': inPlaceReverseEvents,
  'prefix-sums': prefixSumsEvents,
  'frequency-counting': frequencyCountEvents,
  'palindromes': palindromeEvents,
  'two-pointers-on-strings': twoPointerStringEvents,
  'frequency-arrays': frequencyArrayEvents,
  'bubble-sort': bubbleSortEvents,
  'selection-sort': selectionSortEvents,
  'insertion-sort': insertionSortEvents,
  'linear-search': linearSearchEvents,
  'binary-search': binarySearchEvents,
  'two-pointers': twoPointersEvents,
  'fast-slow-pointers': fastSlowPointersEvents,
  'sliding-window-fixed': slidingWindowFixedEvents,
  'sliding-window-variable': slidingWindowVariableEvents,
  'kadane': kadaneEvents,
  'lower-bound': lowerBoundEvents,
  'upper-bound': upperBoundEvents,
  'stack-fundamentals': stackFundamentalsEvents,
  'valid-parentheses': validParenthesesEvents,
  'min-stack': minStackEvents,
  'next-greater-element': nextGreaterElementEvents,
  'queue-deque': queueDequeEvents,
};

export function getGenerator(key) {
  return GENERATORS[key] || null;
}
