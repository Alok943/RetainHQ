import ArrayViz from './ArrayViz.jsx';
import TreeViz from './TreeViz.jsx';
import GraphViz from './GraphViz.jsx';
import GridViz from './GridViz.jsx';
import ListViz from './ListViz.jsx';
import IntervalViz from './IntervalViz.jsx';
import BitsViz from './BitsViz.jsx';

export const MAIN_RENDERERS = {
  array: ArrayViz,
  tree: TreeViz,
  graph: GraphViz,
  grid: GridViz,
  list: ListViz,
  intervals: IntervalViz,
  bits: BitsViz,
};

export const rendererFor = (frame) => MAIN_RENDERERS[frame?.view] || ArrayViz;
