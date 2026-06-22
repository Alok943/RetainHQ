// Logical-query-flow decomposition. Given a single-block SELECT, produce the
// cumulative row-set AFTER each logical processing stage so the learner sees the
// row count change FROM/JOIN -> WHERE -> GROUP BY -> HAVING -> final result.
// This is the teachable model (logical clause order), NOT physical execution.
//
// We only decompose the canonical single-block SELECT. Anything with a CTE,
// a top-level set operation, or a leading parenthesis returns null, and the UI
// falls back to a plain result table — graceful degradation over a fragile parser.

const TOP_KEYWORDS = ['select', 'from', 'where', 'group by', 'having', 'order by', 'limit', 'offset'];
const SETOPS = ['union', 'intersect', 'except'];

// Scan char-by-char tracking string literals and paren depth, recording the
// byte offset of each TOP-LEVEL (depth 0) clause keyword in order of appearance.
function findTopLevelClauses(sql) {
  const lower = sql.toLowerCase();
  const marks = [];
  let depth = 0;
  let inStr = false;
  for (let i = 0; i < sql.length; i++) {
    const ch = sql[i];
    if (inStr) {
      if (ch === "'") inStr = false;
      continue;
    }
    if (ch === "'") { inStr = true; continue; }
    if (ch === '(') { depth++; continue; }
    if (ch === ')') { depth--; continue; }
    if (depth !== 0) continue;

    // word boundary?
    const prev = i === 0 ? ' ' : sql[i - 1];
    if (/[a-z0-9_]/i.test(prev)) continue;

    for (const op of SETOPS) {
      if (lower.startsWith(op, i) && !/[a-z0-9_]/i.test(sql[i + op.length] || ' ')) {
        return { setop: true };
      }
    }
    for (const kw of TOP_KEYWORDS) {
      if (lower.startsWith(kw, i) && !/[a-z0-9_]/i.test(sql[i + kw.length] || ' ')) {
        marks.push({ kw, start: i, end: i + kw.length });
      }
    }
  }
  return { marks };
}

/**
 * Split a single-block SELECT into its clause bodies.
 * @returns {null | {select, from, where, groupBy, having, orderBy, limit}}  (bodies are raw strings, or undefined)
 */
export function splitSelect(sql) {
  const trimmed = sql.trim().replace(/;\s*$/, '');
  const lower = trimmed.toLowerCase();
  if (lower.startsWith('with') || lower.startsWith('(')) return null; // CTE / wrapped — bail
  if (!lower.startsWith('select')) return null;

  const { marks, setop } = findTopLevelClauses(trimmed);
  if (setop || !marks) return null;

  // Keep only the first occurrence of each clause, in canonical order.
  const firstFrom = marks.find((m) => m.kw === 'from');
  if (!firstFrom) return null; // need a FROM to have a row-set to trace

  const body = (kw) => {
    const idx = marks.findIndex((m) => m.kw === kw);
    if (idx === -1) return undefined;
    const startPos = marks[idx].end;
    // next top-level clause after this one ends the body
    let endPos = trimmed.length;
    for (let j = idx + 1; j < marks.length; j++) {
      if (marks[j].start > marks[idx].start) { endPos = marks[j].start; break; }
    }
    return trimmed.slice(startPos, endPos).trim();
  };

  return {
    select: body('select'),
    from: body('from'),
    where: body('where'),
    groupBy: body('group by'),
    having: body('having'),
    orderBy: body('order by'),
    limit: body('limit'),
  };
}

/**
 * Build the cumulative stages to run. Each stage has a count query and a label.
 * The final stage carries the full query (to render the actual projected rows).
 * @returns {null | Array<{key, label, countSql, rowsSql?}>}
 */
export function buildStages(sql) {
  const p = splitSelect(sql);
  if (!p || !p.from) return null;

  const stages = [];
  const base = `FROM ${p.from}`;

  // Stage 1: FROM (+ JOINs) — the row-set before any filtering.
  stages.push({ key: 'from', label: 'FROM + JOIN', countSql: `SELECT count(*) AS n ${base}` });

  // Stage 2: WHERE — row filter.
  if (p.where) {
    stages.push({ key: 'where', label: 'WHERE', countSql: `SELECT count(*) AS n ${base} WHERE ${p.where}` });
  }

  // Stage 3: GROUP BY — collapse rows into groups (count = number of groups).
  if (p.groupBy) {
    const inner = `SELECT 1 ${base}${p.where ? ` WHERE ${p.where}` : ''} GROUP BY ${p.groupBy}`;
    stages.push({ key: 'group_by', label: 'GROUP BY', countSql: `SELECT count(*) AS n FROM (${inner}) _g` });

    // Stage 4: HAVING — filter the groups.
    if (p.having) {
      const inner2 = `${inner} HAVING ${p.having}`;
      stages.push({ key: 'having', label: 'HAVING', countSql: `SELECT count(*) AS n FROM (${inner2}) _h` });
    }
  }

  // Final stage: the real projected result (SELECT list + ORDER BY + LIMIT applied).
  stages.push({ key: 'result', label: p.groupBy ? 'SELECT' : 'SELECT + ORDER BY', isResult: true, rowsSql: `${sql.trim().replace(/;\s*$/, '')}` });

  // Only worth a scrubber if there's an actual transformation to watch.
  const hasTransform = stages.some((s) => s.key === 'where' || s.key === 'group_by');
  if (!hasTransform) return null;

  return stages;
}

export default buildStages;
