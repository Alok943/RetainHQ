// Maps a lesson's `viz.generator` key -> its event generator. validate.py checks a lesson's
// key exists here so a lesson can never reference a missing visualizer. Add a line per algorithm.
import { mergeSortEvents } from './generators/merge-sort.js';

export const GENERATORS = {
  'merge-sort': mergeSortEvents,
};

export function getGenerator(key) {
  return GENERATORS[key] || null;
}
