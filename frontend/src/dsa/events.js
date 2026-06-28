// DSA operation vocabulary — the language-independent verbs of an execution trace.
// Grouped by data-structure FAMILY so new algorithm classes add ops without touching the
// compiler or renderers. An UNKNOWN op is not an error: the compiler still emits a frame and
// the renderer shows its caption + invariant (graceful fallback). See docs/dsa-architecture.md.

export const OP_FAMILIES = {
  array:     ['COMPARE', 'SWAP', 'MOVE', 'WRITE', 'SPLIT', 'MERGE_DONE'],
  recursion: ['CALL', 'RETURN', 'CHOOSE', 'UNDO'],
  stack:     ['PUSH', 'POP', 'ENQUEUE', 'DEQUEUE'],
  graph:     ['VISIT', 'MARK_VISITED', 'RELAX', 'ENQUEUE_NODE'],
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
