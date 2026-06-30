// Maps a lesson's `viz.generator` key -> its event generator. validate.py checks a lesson's
// key exists here so a lesson can never reference a missing visualizer. Add a line per algorithm.
import { mergeSortEvents } from './generators/merge-sort.js';
import { inPlaceReverseEvents } from './generators/in-place-operations.js';
import { prefixSumsEvents } from './generators/prefix-sums.js';
import { frequencyCountEvents } from './generators/frequency-counting.js';
import { palindromeEvents } from './generators/palindromes.js';
import { twoPointerStringEvents } from './generators/two-pointers-on-strings.js';
import { frequencyArrayEvents } from './generators/frequency-arrays.js';

export const GENERATORS = {
  'merge-sort': mergeSortEvents,
  'in-place-operations': inPlaceReverseEvents,
  'prefix-sums': prefixSumsEvents,
  'frequency-counting': frequencyCountEvents,
  'palindromes': palindromeEvents,
  'two-pointers-on-strings': twoPointerStringEvents,
  'frequency-arrays': frequencyArrayEvents,
};

export function getGenerator(key) {
  return GENERATORS[key] || null;
}
