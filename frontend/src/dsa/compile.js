// compile(input, events) -> frames.
// Events are the SOURCE OF TRUTH (a pure function of input). This folds that event stream into
// a materialized state snapshot per step, so the renderer can index O(1) into any step for
// scrubbing / predict-before-reveal / "explain this frame". Frames are a presentation cache,
// never authored directly. See docs/dsa-architecture.md.
//
// Structure (M0/D3): op handling is split into per-FAMILY reducers. Each reducer takes the shared
// `state` + the event's op/args, mutates state, and RETURNS the per-frame transient bits
// ({ pointers?, mapActive? }) — or `null` meaning "not my op". compile() tries reducers in order,
// takes the first non-null, and assembles the identical frame shape. Adding a new data-structure
// family (stack, list, tree, graph, grid...) = add a reducer + additive frame keys, never edit a
// giant switch. An UNKNOWN op falls through all reducers -> still a frame with caption + invariant
// (graceful fallback). compile()'s signature and frame shape are a stable contract — see
// compile-frames.golden.mjs (byte-identical guard).

// --- recursion / merge family: CALL SPLIT COMPARE WRITE MERGE_DONE RETURN ---
function recursionMergeReducer(state, op, args) {
  const top = () => state.callStack[state.callStack.length - 1];
  switch (op) {
    case 'CALL':
      state.callStack.push({ lo: args.lo, hi: args.hi });
      state.regions = [{ lo: args.lo, hi: args.hi, label: 'sorting' }];
      return {};
    case 'SPLIT':
      state.regions = [
        { lo: args.lo, hi: args.mid, label: 'left' },
        { lo: args.mid + 1, hi: args.hi, label: 'right' },
      ];
      return {};
    case 'COMPARE': {
      const t = top();
      if (t) state.regions = [{ lo: t.lo, hi: t.hi, label: 'merging' }];
      return { pointers: { write: args.writeIndex } };
    }
    case 'WRITE': {
      state.array[args.index] = args.value;
      const t = top();
      if (t) state.regions = [{ lo: t.lo, hi: t.hi, label: 'merging' }];
      return { pointers: { write: args.index } };
    }
    case 'MERGE_DONE':
      for (let x = args.lo; x <= args.hi; x++) state.sorted.add(x);
      state.regions = [{ lo: args.lo, hi: args.hi, label: 'sorted' }];
      return {};
    case 'RETURN':
      state.callStack.pop();
      return {};
    default:
      return null;
  }
}

// --- array family: two-pointers, in-place ops, prefix sums, binary search ---
function arrayReducer(state, op, args) {
  switch (op) {
    case 'POINT': // set/move named pointers (lo, hi, i, j); persists across frames
      state.ptrs = { ...state.ptrs, ...args };
      return { pointers: { ...state.ptrs } };
    case 'SWAP': { // swap two indices in place
      const { i, j } = args;
      const tmp = state.array[i]; state.array[i] = state.array[j]; state.array[j] = tmp;
      state.ptrs = { ...state.ptrs, i, j };
      return { pointers: { ...state.ptrs } };
    }
    case 'SET': // overwrite one cell and mark it finalized (e.g. a built prefix value)
      if (typeof args.index === 'number') { state.array[args.index] = args.value; state.sorted.add(args.index); }
      return { pointers: { ...state.ptrs, write: args.index } };
    case 'WINDOW': // set the active sub-range (e.g. binary-search [lo,hi]); cells outside go idle
      state.regions = [{ lo: args.lo, hi: args.hi, label: 'merging' }];
      return { pointers: { ...state.ptrs } };
    case 'MARK': // mark specific indices as confirmed/matched (no value change)
      for (const x of args.indices || []) state.sorted.add(x);
      return { pointers: { ...state.ptrs } };
    case 'DONE': // finalize a range (or the whole array when no bounds given)
      if (typeof args.lo === 'number' && typeof args.hi === 'number') {
        for (let x = args.lo; x <= args.hi; x++) state.sorted.add(x);
      } else {
        for (let x = 0; x < state.array.length; x++) state.sorted.add(x);
      }
      return { pointers: { ...state.ptrs } };
    default:
      return null;
  }
}

// --- hashing family: frequency counting ---
function hashingReducer(state, op, args) {
  switch (op) {
    case 'COUNT': { // tally one element into the frequency map
      const { value, index } = args;
      if (state.freq === null) state.freq = {};
      state.freq[value] = (state.freq[value] || 0) + 1;
      return { pointers: { ...state.ptrs, i: index }, mapActive: value };
    }
    default:
      return null;
  }
}

// --- scalar family: named running variables (Kadane's current/best, window sum, etc.) ---
function scalarReducer(state, op, args) {
  switch (op) {
    case 'VAR': // merge named scalars into persistent state.vars (e.g. { current, best })
      state.vars = { ...state.vars, ...args };
      return { pointers: { ...state.ptrs } };
    default:
      return null;
  }
}


// --- stack/queue family ---
function stackQueueReducer(state, op, args) {
  switch (op) {
    case 'PUSH':
      state.stack.push(args.value);
      return { pointers: { ...state.ptrs }, structActive: state.stack.length - 1 };
    case 'POP':
      state.stack.pop();
      return { pointers: { ...state.ptrs }, structActive: 'pop' };
    case 'ENQUEUE':
      state.queue.push(args.value);
      return { pointers: { ...state.ptrs }, structActive: state.queue.length - 1 };
    case 'DEQUEUE':
      state.queue.shift();
      return { pointers: { ...state.ptrs }, structActive: 'shift' };
    default:
      return null;
  }
}

function treeReducer(state, op, args) {
  switch (op) {
    case 'TREE_INIT': {
      // layout once: in-order positioning
      const { nodes, root } = args;
      const nodeMap = new Map();
      nodes.forEach(n => nodeMap.set(n.id, { ...n }));
      
      let index = 0;
      const traverse = (id, depth) => {
        if (id == null || !nodeMap.has(id)) return;
        const node = nodeMap.get(id);
        traverse(node.left, depth + 1);
        node.x = index * 40; // pitch
        node.y = depth * 50; // levelHeight
        index++;
        traverse(node.right, depth + 1);
      };
      traverse(root, 0);
      
      // Center the layout
      if (index > 0) {
        const offset = ((index - 1) * 40) / 2;
        for (const n of nodeMap.values()) {
          n.x -= offset;
        }
      }
      
      state.tree = { nodes: nodeMap, root };
      state.nodeTags = {};
      state.nodeReturns = {};
      state.cursor = null;
      return { view: 'tree' };
    }
    case 'VISIT_NODE':
      state.cursor = args.id;
      return { view: 'tree' };
    case 'MARK_NODE':
      state.nodeTags[args.id] = args.tag;
      return { view: 'tree' };
    case 'COMPARE_NODE':
      // could use tags or a specific compare overlay
      return { view: 'tree' };
    case 'SET_EDGE':
      // optional, if edges need coloring
      return { view: 'tree' };
    case 'RETURN_NODE':
      if (args.value !== undefined) state.nodeReturns[args.id] = args.value;
      return { view: 'tree' };
    default:
      if (state.tree) return { view: 'tree' };
      return null;
  }
}
function gridReducer(state, op, args) {
  switch (op) {
    case 'GRID_INIT':
      state.grid = {
        rows: args.rows, cols: args.cols,
        cells: args.values ? args.values.map(r => [...r]) : Array.from({length: args.rows}, () => Array(args.cols).fill(null)),
        labels: args.labels || null,
      };
      state.cellTags = {};
      return { view: 'grid' };
    case 'FILL_CELL':
      if (state.grid) state.grid.cells[args.r][args.c] = args.value;
      return { view: 'grid' };
    case 'READ_CELL':
      return { view: 'grid', readCells: new Set([{ r: args.r, c: args.c }]) }; // in practice, might receive multiple
    case 'MARK_CELL':
      state.cellTags[`${args.r},${args.c}`] = args.tag;
      return { view: 'grid' };
    case 'PLACE':
      if (state.grid) state.grid.cells[args.r][args.c] = 'Q'; // Example for N-Queens
      return { view: 'grid' };
    case 'REMOVE':
      if (state.grid) state.grid.cells[args.r][args.c] = null;
      return { view: 'grid' };
    default:
      if (state.grid) return { view: 'grid' };
      return null;
  }
}

function graphReducer(state, op, args) {
  switch (op) {
    case 'GRAPH_INIT':
      // Basic circular layout if x,y not provided
      const nodes = args.nodes.map((n, i) => {
        if (n.x != null && n.y != null) return { ...n };
        const angle = (i / args.nodes.length) * Math.PI * 2;
        return { ...n, x: Math.cos(angle) * 100, y: Math.sin(angle) * 100 };
      });
      state.graph = { nodes, edges: args.edges.map(e => ({ ...e })) };
      state.graphNodeTags = {};
      state.graphEdgeTags = {};
      state.graphCursor = null;
      return { view: 'graph' };
    case 'VISIT':
      state.graphCursor = args.id;
      return { view: 'graph' };
    case 'MARK_VISITED':
      state.graphNodeTags[args.id] = args.tag || 'visited';
      return { view: 'graph' };
    case 'RELAX':
      const node = state.graph.nodes.find(n => n.id === args.u); // or v, depending on convention
      if (node) node.dist = args.dist;
      return { view: 'graph' };
    case 'ENQUEUE_NODE':
      // often relies on stackQueueReducer for the queue panel, but can also color the node
      state.graphNodeTags[args.id] = 'enqueued';
      return { view: 'graph' };
    case 'SET_EDGE':
      state.graphEdgeTags[`${args.u},${args.v}`] = args.tag;
      return { view: 'graph' };
    case 'UNION':
      // merge visual component logic
      return { view: 'graph' };
    default:
      if (state.graph) return { view: 'graph' };
      return null;
  }
}
function listReducer(state, op, args) {
  switch (op) {
    case 'LIST_INIT':
      state.list = { nodes: args.nodes.map(n => ({ ...n })), head: args.head };
      state.listPtrs = {};
      state.listNodeTags = {};
      return { view: 'list' };
    case 'POINT_NODE':
      state.listPtrs[args.name] = args.id;
      return { view: 'list' };
    case 'SET_NEXT':
      const node = state.list.nodes.find(n => n.id === args.from);
      if (node) node.next = args.to;
      return { view: 'list' };
    case 'MARK_NODE':
      state.listNodeTags[args.id] = args.tag;
      return { view: 'list' };
    default:
      if (state.list) return { view: 'list' };
      return null;
  }
}

function intervalsReducer(state, op, args) {
  switch (op) {
    case 'INTERVAL_INIT':
      state.intervals = args.intervals ? args.intervals.map(i => ({ ...i })) : [];
      return { view: 'intervals' };
    case 'SELECT':
    case 'SKIP':
    case 'MERGE_INTERVAL':
      // Simplified: Just pass args through or mark specific intervals
      if (args.id != null) {
        const intv = state.intervals.find(i => i.id === args.id);
        if (intv) intv.state = op === 'SELECT' ? 'selected' : (op === 'SKIP' ? 'skipped' : 'merged');
      }
      return { view: 'intervals' };
    default:
      if (state.intervals) return { view: 'intervals' };
      return null;
  }
}

function bitsReducer(state, op, args) {
  switch (op) {
    case 'BITS_INIT':
      state.bits = { numbers: args.numbers || [] };
      state.bitsActiveCol = null;
      return { view: 'bits' };
    case 'XOR_STEP':
      state.bitsActiveCol = args.col;
      return { view: 'bits' };
    case 'SET_BIT':
      // modify bits if needed
      return { view: 'bits' };
    default:
      if (state.bits) return { view: 'bits' };
      return null;
  }
}

const REDUCERS = [recursionMergeReducer, arrayReducer, hashingReducer, scalarReducer, stackQueueReducer, treeReducer, gridReducer, graphReducer, listReducer, intervalsReducer, bitsReducer];

export function compile(input, events) {
  const state = {
    array: [...input],       // mutated by WRITE / SWAP / SET
    callStack: [],           // for the StateMachine renderer (recursion / call stack)
    regions: [],             // brackets under the array: left/right/merging/sorted
    sorted: new Set(),       // indices known sorted/finalized (MERGE_DONE / DONE / SET / MARK)
    ptrs: {},                // persistent named pointers for array-family traces (lo/hi/i/j)
    freq: null,              // frequency map for COUNT traces; null until first COUNT
    vars: {},                // persistent named scalars for VAR traces (Kadane's current/best, etc.)
    stack: [],
    queue: [],
    stackTop: null,
    queueEnd: null,
    
    // Extensible state for new structures
    tree: null,
    nodeTags: {},
    nodeReturns: {},
    cursor: null,
    
    grid: null,
    cellTags: {},
    
    graph: null,
    graphNodeTags: {},
    graphEdgeTags: {},
    graphCursor: null,
    
    list: null,
    listPtrs: {},
    listNodeTags: {},
    
    intervals: null,
    
    bits: null,
    bitsActiveCol: null,
  };
  const frames = [];

  for (const ev of events) {
    const { op, args = {}, step_id = null, invariant = null, note } = ev;

    let result = null;
    for (const reducer of REDUCERS) {
      result = reducer(state, op, args);
      if (result) break;
    }
    if (!result) result = {}; // graceful fallback: unknown op -> still a frame with caption/invariant

    frames.push({
      array: [...state.array],
      callStack: state.callStack.map((f) => ({ ...f })),
      regions: state.regions.map((r) => ({ ...r })),
      sorted: [...state.sorted].sort((a, b) => a - b),
      pointers: result.pointers || {},
      map: state.freq ? { ...state.freq } : undefined,
      mapActive: result.mapActive ?? null,
      vars: Object.keys(state.vars).length ? { ...state.vars } : undefined,
      stack: state.stack && state.stack.length ? [...state.stack] : undefined,
      queue: state.queue && state.queue.length ? [...state.queue] : undefined,
      structActive: result.structActive !== undefined && result.structActive !== null ? result.structActive : undefined,
      tree: state.tree ? { nodes: new Map(state.tree.nodes), root: state.tree.root } : undefined,
      nodeTags: state.tree ? { ...state.nodeTags } : undefined,
      nodeReturns: state.tree ? { ...state.nodeReturns } : undefined,
      cursor: state.tree ? state.cursor : undefined,
      
      grid: state.grid ? { ...state.grid, cells: state.grid.cells.map(r => [...r]) } : undefined,
      cellTags: state.grid ? { ...state.cellTags } : undefined,
      readCells: result.readCells || undefined,
      
      graph: state.graph ? { nodes: state.graph.nodes.map(n => ({...n})), edges: state.graph.edges.map(e => ({...e})) } : undefined,
      graphNodeTags: state.graph ? { ...state.graphNodeTags } : undefined,
      graphEdgeTags: state.graph ? { ...state.graphEdgeTags } : undefined,
      graphCursor: state.graph ? state.graphCursor : undefined,
      
      list: state.list ? { nodes: state.list.nodes.map(n => ({...n})), head: state.list.head } : undefined,
      listPtrs: state.list ? { ...state.listPtrs } : undefined,
      listNodeTags: state.list ? { ...state.listNodeTags } : undefined,
      
      intervals: state.intervals ? state.intervals.map(i => ({...i})) : undefined,
      
      bits: state.bits ? { ...state.bits } : undefined,
      bitsActiveCol: state.bits ? state.bitsActiveCol : undefined,
      
      view: result.view || 'array',
      activeOp: op,
      caption: note || op,
      invariant,
      step_id,
    });
  }
  return frames;
}
