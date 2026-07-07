// Client-side deterministic grading for the Tests section (docs/SPEC-test-runtime.md).
// Every question type grades in-browser except 'fillup', which is the ONE LLM call
// (POST /api/tests/grade-fillup) — everything here is a pure function, no network.
//
// Each grade*(question, studentInput) returns:
//   { outcome: 'got' | 'wrong', detail?: string }
// 'missed' (skipped / no attempt) is decided by the caller (Tests.jsx), not here —
// these functions only run once the student has actually submitted something.

import { tracePython } from './pyodideRunner';
import { runIsolatedSql } from './pgliteRunner';

export function gradeNumeric(q, studentAnswer) {
  const val = parseFloat(studentAnswer);
  if (Number.isNaN(val)) return { outcome: 'wrong', detail: 'Not a number.' };
  const tolerance = q.tolerance ?? 0;
  const ok = Math.abs(val - q.answer) <= tolerance;
  return { outcome: ok ? 'got' : 'wrong' };
}

export function gradeCodeOutput(q, studentAnswer) {
  const norm = (s) => (s || '').replace(/\r\n/g, '\n').trim();
  const ok = norm(studentAnswer) === norm(q.answer);
  return { outcome: ok ? 'got' : 'wrong' };
}

export function gradeMcq(q, selectedIndex) {
  const ok = selectedIndex === q.answer;
  const misconception = ok ? null : (q.misconceptions || [])[selectedIndex] || null;
  return { outcome: ok ? 'got' : 'wrong', misconception };
}

// code-fix / code-write: exec the student's code, then run the bank's asserts against
// the SAME globals — a pass means every assert ran without raising. Uses the existing
// lazy-loaded Pyodide singleton (frontend/src/lib/pyodideRunner.js) — no new WASM cost,
// no server sandbox (matches the "no sandbox costs" constraint).
export async function gradeCode(q, studentCode) {
  try {
    const combined = `${studentCode}\n\n${q.asserts}`;
    const result = await tracePython(combined, 500);
    if (result.error) {
      return { outcome: 'wrong', detail: result.error };
    }
    return { outcome: 'got' };
  } catch (e) {
    return { outcome: 'wrong', detail: (e && e.message) || 'Could not run the code.' };
  }
}

// query-write: run the student's query and the bank's canonical_query against the SAME
// seed (q.schema_sql), then diff the result sets. Uses runIsolatedSql — a bare PGlite
// instance with ONLY q.schema_sql loaded, no canonical SQL-lessons dataset — so a
// bank's own table names (e.g. 'orders') never collide with the shared lessons dataset.
export async function gradeQuery(q, studentQuery) {
  const [studentRes, canonicalRes] = await Promise.all([
    runIsolatedSql(studentQuery, q.schema_sql),
    runIsolatedSql(q.canonical_query, q.schema_sql),
  ]);
  if (studentRes.error) {
    return { outcome: 'wrong', detail: studentRes.error };
  }
  const rowsMatch = (a, b) => {
    const norm = (rows) => rows.map((r) => JSON.stringify(r));
    if (q.order_matters) {
      const na = norm(a), nb = norm(b);
      return na.length === nb.length && na.every((v, i) => v === nb[i]);
    }
    const sa = norm(a).sort(), sb = norm(b).sort();
    return sa.length === sb.length && sa.every((v, i) => v === sb[i]);
  };
  const ok = rowsMatch(studentRes.rows, canonicalRes.rows);
  return { outcome: ok ? 'got' : 'wrong' };
}

// Dispatch by question type. 'fillup' is handled separately by the caller (it needs
// the async /grade-fillup network call + the disabled-grader fallback UI).
export async function gradeQuestion(q, studentInput) {
  switch (q.type) {
    case 'numeric': return gradeNumeric(q, studentInput);
    case 'code-output': return gradeCodeOutput(q, studentInput);
    case 'mcq': return gradeMcq(q, studentInput);
    case 'code-fix':
    case 'code-write': return gradeCode(q, studentInput);
    case 'query-write': return gradeQuery(q, studentInput);
    default: throw new Error(`gradeQuestion: unhandled type '${q.type}'`);
  }
}

// --- Session sampling ------------------------------------------------------- //

function shuffle(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

/**
 * Sample ~targetCount questions from a bank, weighted toward nodes that are
 * due/overdue or have low recent accuracy (per SPEC-test-runtime.md). `weights`
 * is the /api/tests/weights response (array of {node_title, due, overdue_days,
 * accuracy_recent, attempts_recent}) — questions are matched to a node by the
 * caller-supplied `nodeTitleBySlug` map (bank `node` is a content slug).
 */
export function sampleSession(bank, weightsByTitle, nodeTitleBySlug, targetCount = 8) {
  const questions = bank.questions || [];
  const weightOf = (q) => {
    const title = nodeTitleBySlug[q.node];
    const w = title && weightsByTitle[title];
    if (!w) return 1; // untested node — neutral weight
    let weight = 1;
    if (w.due) weight += 2 + Math.min(w.overdue_days, 10) * 0.2;
    if (typeof w.accuracy_recent === 'number') weight += (1 - w.accuracy_recent) * 3;
    return weight;
  };

  // Weighted sample without replacement (simple: score + shuffle-by-score-noise).
  const scored = questions.map((q) => ({ q, score: weightOf(q) * (0.5 + Math.random()) }));
  scored.sort((a, b) => b.score - a.score);
  const picked = scored.slice(0, Math.min(targetCount, scored.length)).map((s) => s.q);

  // Shuffle question order, and shuffle each MCQ's option order (tracking the new answer index).
  return shuffle(picked).map((q) => {
    if (q.type !== 'mcq' || !Array.isArray(q.options)) return q;
    const order = shuffle(q.options.map((_, i) => i));
    return {
      ...q,
      options: order.map((i) => q.options[i]),
      answer: order.indexOf(q.answer),
      misconceptions: order.map((i) => q.misconceptions[i]),
    };
  });
}
