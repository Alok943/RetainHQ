import React, { useState, useEffect, useCallback } from 'react';
import { runSql } from './lib/pgliteRunner';
import { Database, Loader2, Play, ArrowRight } from 'lucide-react';

// JOIN visualizer: shows the two source tables side by side and, as the learner
// toggles INNER / LEFT / RIGHT / FULL, colours which rows SURVIVE into the result
// vs. which get NULL-padded vs. which are dropped. Truth comes from PGlite — we
// fetch both tables and compute matches by set membership (equality-join semantics),
// and run the real join for the result-row count. Opt-in via:
//   query_walkthrough: { visualization: "join-diagram",
//     join: { left:{table,label,show[]}, right:{table,label,show[]},
//             on:{left,right}, type:"left" } }

const TYPES = [
  { key: 'inner', label: 'INNER' },
  { key: 'left', label: 'LEFT' },
  { key: 'right', label: 'RIGHT' },
  { key: 'full', label: 'FULL' },
];

// Is a row from `side` present in the result for join `type`?
function inResult(side, matched, type) {
  if (matched) return true;
  if (type === 'full') return true;
  if (type === 'left') return side === 'left';
  if (type === 'right') return side === 'right';
  return false; // inner: unmatched rows are dropped
}

export default function SqlJoinViz({ spec, focus }) {
  const [data, setData] = useState(null); // { left:[], right:[], matchedL:Set, matchedR:Set }
  const [loading, setLoading] = useState(false);
  const [type, setType] = useState(spec?.type || 'left');
  const [resultCount, setResultCount] = useState(null);

  const onL = spec.on.left, onR = spec.on.right;
  const L = spec.left, R = spec.right;

  const load = useCallback(async () => {
    setLoading(true);
    const lq = await runSql(`SELECT * FROM ${L.table} ORDER BY 1`);
    const rq = await runSql(`SELECT * FROM ${R.table} ORDER BY 1`);
    if (lq.error || rq.error) { setData({ error: lq.error || rq.error }); setLoading(false); return; }
    const rightKeys = new Set(rq.rows.map((r) => r[onR]));
    const leftKeys = new Set(lq.rows.map((r) => r[onL]));
    const matchedL = new Set(lq.rows.filter((r) => rightKeys.has(r[onL])).map((r) => r[onL]));
    const matchedR = new Set(rq.rows.filter((r) => leftKeys.has(r[onR])).map((r) => r[onR]));
    setData({ left: lq.rows, right: rq.rows, matchedL, matchedR });
    setLoading(false);
  }, [L.table, R.table, onL, onR]);

  // Real result-row count for the active join type (truth from PGlite).
  useEffect(() => {
    if (!data || data.error) return;
    let cancelled = false;
    const kw = type === 'inner' ? 'INNER JOIN' : type === 'full' ? 'FULL OUTER JOIN' : `${type.toUpperCase()} JOIN`;
    runSql(`SELECT count(*) AS n FROM ${L.table} l ${kw} ${R.table} r ON l.${onL} = r.${onR}`)
      .then((res) => { if (!cancelled) setResultCount(res.error ? null : Number(res.rows[0].n)); });
    return () => { cancelled = true; };
  }, [type, data, L.table, R.table, onL, onR]);

  if (!data) {
    return (
      <div className="rounded-lg border border-[rgba(15,23,42,0.12)] bg-white p-4">
        <button onClick={load} disabled={loading}
          className="flex items-center gap-2 text-sm font-semibold text-white bg-[#0891B2] hover:bg-[#0e7490] rounded px-3.5 py-2 transition-colors disabled:opacity-60">
          {loading ? <><Loader2 size={15} className="animate-spin" /> Starting Postgres…</> : <><Play size={15} /> Visualize the join</>}
        </button>
      </div>
    );
  }
  if (data.error) {
    return <div className="rounded-lg border border-[#B91C1C]/20 bg-[#B91C1C]/[0.05] p-3 font-mono text-[12px] text-[#B91C1C]">{data.error}</div>;
  }

  const matchedCount = data.left.filter((r) => data.matchedL.has(r[onL])).length;
  const leftOnly = data.left.length - matchedCount;
  const rightOnly = data.right.filter((r) => !data.matchedR.has(r[onR])).length;

  return (
    <div className="rounded-lg border border-[rgba(15,23,42,0.12)] overflow-hidden bg-white">
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-[rgba(15,23,42,0.08)] bg-[#f9f9f6]">
        <span className="flex items-center gap-1.5 font-sans text-xs font-semibold text-[#0F172A]"><Database size={13} className="text-[#0891B2]" /> Join visualizer</span>
        {resultCount != null && <span className="font-mono text-[11px] text-[#64748B]">{resultCount} result row{resultCount === 1 ? '' : 's'}</span>}
      </div>

      {/* join-type toggle */}
      <div className="flex items-center gap-1.5 px-4 py-2.5 border-b border-[rgba(15,23,42,0.06)]">
        {TYPES.map((t) => (
          <button key={t.key} onClick={() => setType(t.key)}
            className={`font-mono text-[11px] font-bold px-2.5 py-1 rounded transition-colors ${type === t.key ? 'bg-[#0891B2] text-white' : 'bg-[rgba(15,23,42,0.05)] text-[#64748B] hover:bg-[rgba(15,23,42,0.1)]'}`}>
            {t.label}
          </button>
        ))}
        <span className="ml-1 font-mono text-[11px] text-[#94a3b8]">JOIN ON {L.label?.toLowerCase() || L.table}.{onL} = {R.label?.toLowerCase() || R.table}.{onR}</span>
      </div>

      {/* two tables side by side */}
      <div className="grid md:grid-cols-2 gap-3 p-3">
        <JoinTable title={L.label || L.table} rows={data.left} cols={L.show} keyCol={onL} matched={data.matchedL} side="left" type={type} />
        <JoinTable title={R.label || R.table} rows={data.right} cols={R.show} keyCol={onR} matched={data.matchedR} side="right" type={type} />
      </div>

      {/* legend + summary */}
      <div className="px-4 py-2.5 border-t border-[rgba(15,23,42,0.06)] flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] font-sans">
        <span className="flex items-center gap-1.5"><Dot c="#0F766E" /> matched</span>
        <span className="flex items-center gap-1.5"><Dot c="#B45309" /> preserved (NULL-padded)</span>
        <span className="flex items-center gap-1.5"><Dot c="#94a3b8" /> dropped</span>
        <span className="ml-auto text-[#64748B]">{matchedCount} matched · {leftOnly} left-only · {rightOnly} right-only</span>
      </div>

      {focus && (
        <div className="px-4 py-2 text-[11px] text-[#64748B] border-t border-[rgba(15,23,42,0.06)]">
          <span className="font-semibold text-[#0891B2]">Watch:</span> {focus}
        </div>
      )}
    </div>
  );
}

function Dot({ c }) { return <span className="inline-block w-2.5 h-2.5 rounded-full" style={{ background: c }} />; }

function JoinTable({ title, rows, cols, keyCol, matched, side, type }) {
  const columns = cols && cols.length ? cols : Object.keys(rows[0] || {});
  return (
    <div>
      <div className="font-sans text-[11px] font-bold uppercase tracking-wider text-[#0891B2] mb-1.5">{title}</div>
      <div className="overflow-x-auto rounded-md border border-[rgba(15,23,42,0.1)]">
        <table className="w-full border-collapse font-mono text-[12px]">
          <thead><tr className="bg-[#f1f5f9]">
            {columns.map((c) => <th key={c} className="text-left font-semibold text-[#475569] px-2.5 py-1 border-b border-[rgba(15,23,42,0.1)] whitespace-nowrap">{c}</th>)}
          </tr></thead>
          <tbody>
            {rows.map((row, i) => {
              const isMatched = matched.has(row[keyCol]);
              const present = inResult(side, isMatched, type);
              const color = !present ? '#94a3b8' : isMatched ? '#0F766E' : '#B45309';
              const faded = !present;
              return (
                <tr key={i} style={{ background: present ? color + '12' : 'transparent' }} className={faded ? 'opacity-45' : ''}>
                  {columns.map((c) => (
                    <td key={c} className="px-2.5 py-1 border-b border-[rgba(15,23,42,0.05)] whitespace-nowrap" style={{ color }}>
                      {row[c] === null || row[c] === undefined ? <span className="italic text-[#cbd5e1]">NULL</span> : String(row[c])}
                      {c === keyCol && present && !isMatched && <ArrowRight size={10} className="inline ml-1 -mt-0.5 text-[#B45309]" />}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
