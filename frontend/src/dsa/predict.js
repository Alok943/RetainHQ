// predict.js — the prediction derive library (M1). A lesson's viz.predictions[] holds checkpoints
// { at_step?, at_op?, occurrence, prompt, derive, level }. This module (1) resolves a checkpoint to
// the event index where it fires, and (2) computes the ANSWER from the LIVE event stream at that
// point — never hardcoded — so a prediction survives input tweaking (edit the array → the expected
// answer recomputes). Pure + golden-tested (predict.golden.mjs). See docs/dsa-viz-implementation-plan.md §7.
//
// Derives are trace-derived, D0: everything the gate asks is computed from events, not authored.

// ---- gate resolution ---------------------------------------------------------------------------
// Find the event index a checkpoint fires on. Matches events by step_id (at_step) AND/OR op (at_op);
// `occurrence` picks which match: 'first' | 'last' | 1-based integer. Returns -1 when it never
// occurs for this input (caller SKIPS the gate silently — e.g. a 1-element array has no SWAP).
export function resolveGate(events, { at_step = null, at_op = null, occurrence = 'first' } = {}) {
  const matches = [];
  events.forEach((e, i) => {
    if (at_step != null && e.step_id !== at_step) return;
    if (at_op != null && e.op !== at_op) return;
    if (at_step == null && at_op == null) return; // a checkpoint must anchor to something
    matches.push(i);
  });
  if (!matches.length) return -1;
  if (occurrence === 'first') return matches[0];
  if (occurrence === 'last') return matches[matches.length - 1];
  const n = Number(occurrence);
  return Number.isInteger(n) && n >= 1 && n <= matches.length ? matches[n - 1] : -1;
}

// ---- derive registry ---------------------------------------------------------------------------
// Each derive is (events, gateIndex, args) -> { type, answer, display } | null.
//   type: 'op' | 'value' | 'values' | 'pair' | 'choice'  (hints the gate UI input widget)
//   answer: canonical answer used to grade the learner's commit
//   display: human-readable reveal string
// Derives scan FORWARD from just after the gate — the gate pauses before the reveal; the learner
// predicts what the upcoming events show.
const DERIVES = {
  // the op of the very next event
  next_op(events, i) {
    const e = events[i + 1];
    if (!e) return null;
    return { type: 'op', answer: e.op, display: e.op };
  },

  // the next event that writes a value (WRITE or SET) — its value
  next_write(events, i) {
    for (let k = i + 1; k < events.length; k++) {
      const e = events[k];
      if ((e.op === 'WRITE' || e.op === 'SET') && e.args && e.args.value != null) {
        return { type: 'value', answer: e.args.value, display: String(e.args.value) };
      }
    }
    return null;
  },

  // the next n written values (WRITE/SET), in order
  next_n_writes(events, i, [n = 2]) {
    const vals = [];
    for (let k = i + 1; k < events.length && vals.length < n; k++) {
      const e = events[k];
      if ((e.op === 'WRITE' || e.op === 'SET') && e.args && e.args.value != null) vals.push(e.args.value);
    }
    if (!vals.length) return null;
    return { type: 'values', answer: vals, display: vals.join(', ') };
  },

  // the index pair of the next SWAP
  next_swap_pair(events, i) {
    for (let k = i + 1; k < events.length; k++) {
      const e = events[k];
      if (e.op === 'SWAP' && e.args) {
        const pair = [e.args.i, e.args.j];
        return { type: 'pair', answer: pair, display: `swap indices ${pair[0]} and ${pair[1]}` };
      }
    }
    return null;
  },

  // whether the search window next moves toward the RIGHT half (lo rises) or LEFT half (hi falls).
  // Reads the current WINDOW at/before the gate and the next WINDOW after it. binary-search family.
  branch_binary(events, i) {
    const windowAt = (from, dir) => {
      for (let k = from; dir > 0 ? k < events.length : k >= 0; k += dir) {
        if (events[k].op === 'WINDOW') return events[k].args;
      }
      return null;
    };
    const cur = windowAt(i, -1);
    const next = windowAt(i + 1, +1);
    if (!cur || !next) return null;
    const answer = next.lo > cur.lo ? 'right' : next.hi < cur.hi ? 'left' : 'found';
    return { type: 'choice', answer, display: answer, choices: ['left', 'right'] };
  },

  // the step_id of the very next event — used for gates like Kadane's "extend or restart?" where
  // the decision itself IS the step_id (anchor the gate at_op:'POINT', the answer is what the
  // generator emits next: 'extend' | 'restart' | 'record' | 'done').
  next_step_id(events, i) {
    const e = events[i + 1];
    if (!e || !e.step_id) return null;
    return { type: 'value', answer: e.step_id, display: e.step_id };
  },

  // whether a sliding window next EXPANDS (hi grows) or SHRINKS (lo grows). Reads the current
  // WINDOW at/before the gate and the next WINDOW after it — mirrors branch_binary's shape for the
  // window family. sliding-window-variable (and any future variable-window generator).
  branch_window(events, i) {
    const windowAt = (from, dir) => {
      for (let k = from; dir > 0 ? k < events.length : k >= 0; k += dir) {
        if (events[k].op === 'WINDOW') return events[k].args;
      }
      return null;
    };
    const cur = windowAt(i, -1);
    const next = windowAt(i + 1, +1);
    if (!cur || !next) return null;
    const answer = next.hi > cur.hi ? 'expand' : next.lo > cur.lo ? 'shrink' : 'done';
    return { type: 'choice', answer, display: answer, choices: ['expand', 'shrink'] };
  },
};

// Parse "next_n_writes(2)" -> { name:'next_n_writes', args:[2] }.
export function parseDerive(spec) {
  const m = /^\s*(\w+)\s*(?:\(([^)]*)\))?\s*$/.exec(spec || '');
  if (!m) return null;
  const args = m[2]
    ? m[2].split(',').map((s) => s.trim()).map((s) => (/^-?\d+$/.test(s) ? Number(s) : s.replace(/^['"]|['"]$/g, '')))
    : [];
  return { name: m[1], args };
}

export function isKnownDerive(spec) {
  const p = parseDerive(spec);
  return !!(p && DERIVES[p.name]);
}

// Resolve + evaluate a checkpoint against a trace. Returns null when the gate doesn't apply to this
// input (skip silently) or the derive can't produce an answer. Otherwise:
//   { gateIndex, level, prompt, type, answer, display, choices? }
export function evaluateCheckpoint(events, checkpoint) {
  if (!checkpoint) return null;
  const gateIndex = resolveGate(events, checkpoint);
  if (gateIndex < 0) return null;
  const parsed = parseDerive(checkpoint.derive);
  if (!parsed || !DERIVES[parsed.name]) return null;
  const derived = DERIVES[parsed.name](events, gateIndex, parsed.args);
  if (!derived) return null;
  return {
    gateIndex,
    level: checkpoint.level || 'medium',
    prompt: checkpoint.prompt || '',
    ...derived,
  };
}

// Grade a learner's committed answer against the derived answer. Loose equality by type.
export function gradeAnswer(type, expected, given) {
  if (given == null) return false;
  if (type === 'values' || type === 'pair') {
    if (!Array.isArray(given) || given.length !== expected.length) return false;
    return expected.every((v, idx) => String(v).trim() === String(given[idx]).trim());
  }
  return String(expected).trim().toLowerCase() === String(given).trim().toLowerCase();
}

export const DERIVE_NAMES = Object.keys(DERIVES);
