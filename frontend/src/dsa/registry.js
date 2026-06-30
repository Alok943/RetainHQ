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
};

export function getGenerator(key) {
  return GENERATORS[key] || null;
}
