// DSA operation vocabulary — the language-independent verbs of an execution trace.
// Grouped by data-structure FAMILY so new algorithm classes add ops without touching the
// compiler or renderers. An UNKNOWN op is not an error: the compiler still emits a frame and
// the renderer shows its caption + invariant (graceful fallback). See docs/dsa-architecture.md.

export const OP_FAMILIES = {
  array:     ['COMPARE','SWAP','MOVE','WRITE','SPLIT','MERGE_DONE','POINT','SET','WINDOW','MARK','DONE'],
  recursion: ['CALL','RETURN','CHOOSE','UNDO'],
  stack:     ['PUSH','POP','ENQUEUE','DEQUEUE'],
  hashing:   ['COUNT'],
  scalar:    ['VAR'],
  tree:      ['TREE_INIT','VISIT_NODE','MARK_NODE','COMPARE_NODE','SET_EDGE','RETURN_NODE'],
  grid:      ['GRID_INIT','FILL_CELL','READ_CELL','MARK_CELL','PLACE','REMOVE'],
  graph:     ['GRAPH_INIT','VISIT','MARK_VISITED','RELAX','ENQUEUE_NODE','SET_EDGE','UNION'],
  list:      ['LIST_INIT','POINT_NODE','SET_NEXT','MARK_NODE'],
  intervals: ['INTERVAL_INIT','SELECT','SKIP','MERGE_INTERVAL'],
  bits:      ['BITS_INIT','XOR_STEP','SET_BIT'],
  dp:        ['MEMO_WRITE', 'MEMO_HIT', 'FILL_CELL'],
};

const OP_TO_FAMILY = Object.fromEntries(
  Object.entries(OP_FAMILIES).flatMap(([fam, ops]) => ops.map((op) => [op, fam])),
);

/** The family an op belongs to, or 'unknown' (still renders via caption/invariant). */
export function familyOf(op) {
  return OP_TO_FAMILY[op] || 'unknown';
}

/** An Event is the canonical truth: { op, args, step_id, invariant?, note? }.
 *  `invariant` is an id into the lesson model's invariants[], not free text. */
export function isKnownOp(op) {
  return op in OP_TO_FAMILY;
}
