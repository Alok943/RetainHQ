import React, { useState, useCallback } from 'react';
import { runSql } from './lib/pgliteRunner';
import { buildStages } from './lib/sqlFlow';
import SqlResult from './SqlResult';
import { Play, Loader2, Database, ChevronLeft, ChevronRight, AlertTriangle } from 'lucide-react';

// Interactive logical-query-flow scrubber: steps through FROM/JOIN -> WHERE ->
// GROUP BY -> HAVING -> result, running each cumulative stage against PGlite so the
// learner watches the REAL row count change. Teaches that SELECT is logically last.
// Falls back to a plain <SqlResult> when the query has no filter/group transform
// (e.g. a pure join) or carries a setup_sql override.

const STAGE_COLOR = {
  from: '#0891B2', where: '#B45309', group_by: '#7C3AED', having: '#B91C1C', result: '#0F766E',
};

export default function SqlFlow({ query, setupSql, focus, flowStages }) {
  const stages = !setupSql ? buildStages(query) : null;

  // No transform to scrub (pure join, projection-only, or a setup override) -> plain table.
  if (!stages) {
    return <SqlResult query={query} setupSql={setupSql} focus={focus} flowStages={flowStages} />;
  }

  return <FlowScrubber query={query} stages={stages} focus={focus} />;
}

function FlowScrubber({ query, stages, focus }) {
  const [data, setData] = useState(null); // [{...stage, count?, rows?, columns?, error?}]
  const [loading, setLoading] = useState(false);
  const [active, setActive] = useState(0);

  const run = useCallback(async () => {
    setLoading(true);
    const out = [];
    for (const s of stages) {
      if (s.isResult) {
        const r = await runSql(s.rowsSql);
        out.push({ ...s, rows: r.rows, columns: r.columns, count: r.rows.length, error: r.error });
      } else {
        const r = await runSql(s.countSql);
        out.push({ ...s, count: r.error ? null : Number(r.rows[0].n), error: r.error });
      }
    }
    setData(out);
    setActive(0);
    setLoading(false);
  }, [stages]);

  const lines = (query || '').replace(/\n$/, '').split('\n');

  return (
    <div className="rounded-lg border border-[rgba(15,23,42,0.12)] overflow-hidden bg-white">
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-[rgba(15,23,42,0.08)] bg-[#f9f9f6]">
        <span className="flex items-center gap-1.5 font-sans text-xs font-semibold text-[#0F172A]">
          <Database size={13} className="text-[#0891B2]" /> Logical query flow
        </span>
        {data && <span className="font-mono text-[11px] text-[#64748B]">step {active + 1}/{data.length}</span>}
      </div>

      <pre className="m-0 p-3 text-[12.5px] leading-relaxed font-mono overflow-x-auto bg-[#0b1220] text-[#e2e8f0] min-w-0 max-w-full whitespace-pre">
        {lines.map((ln, i) => <div key={i}>{ln || ' '}</div>)}
      </pre>

      <div className="p-3 border-t border-[rgba(15,23,42,0.08)]">
        {!data ? (
          <button
            onClick={run}
            disabled={loading}
            className="flex items-center gap-2 text-sm font-semibold text-white bg-[#0891B2] hover:bg-[#0e7490] rounded px-3.5 py-2 transition-colors disabled:opacity-60"
          >
            {loading ? <><Loader2 size={15} className="animate-spin" /> Starting Postgres…</> : <><Play size={15} /> Trace the query</>}
          </button>
        ) : (
          <FlowStages data={data} active={active} />
        )}
      </div>

      {/* scrubber */}
      {data && data.length > 1 && (
        <div className="flex items-center gap-3 px-4 py-2.5 border-t border-[rgba(15,23,42,0.08)] bg-[#f9f9f6]">
          <button onClick={() => setActive((i) => Math.max(0, i - 1))} disabled={active === 0} aria-label="Previous stage" className="text-[#64748B] hover:text-[#0F172A] disabled:opacity-40"><ChevronLeft size={18} /></button>
          <input
            type="range" min={0} max={data.length - 1} value={active}
            onChange={(e) => setActive(Number(e.target.value))} aria-label="Query stage"
            className="flex-1 h-1.5 appearance-none rounded-full cursor-pointer outline-none
              [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:h-3.5 [&::-webkit-slider-thumb]:w-3.5 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-white [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-[#0891B2] [&::-webkit-slider-thumb]:shadow"
            style={{ background: `linear-gradient(to right, #0891B2 ${(active / (data.length - 1)) * 100}%, rgba(15,23,42,0.15) ${(active / (data.length - 1)) * 100}%)` }}
          />
          <button onClick={() => setActive((i) => Math.min(data.length - 1, i + 1))} disabled={active === data.length - 1} aria-label="Next stage" className="text-[#64748B] hover:text-[#0F172A] disabled:opacity-40"><ChevronRight size={18} /></button>
        </div>
      )}

      {focus && (
        <div className="px-4 py-2 text-[11px] text-[#64748B] border-t border-[rgba(15,23,42,0.06)]">
          <span className="font-semibold text-[#0891B2]">Watch:</span> {focus}
        </div>
      )}
    </div>
  );
}

function unit(key, n) {
  const base = key === 'group_by' || key === 'having' ? 'group' : 'row';
  return `${base}${n === 1 ? '' : 's'}`;
}

function delta(data, i) {
  if (i === 0) return null;
  const cur = data[i], prev = data[i - 1];
  if (cur.count == null || prev.count == null) return null;
  if (cur.key === 'group_by') return `collapsed ${prev.count} rows → ${cur.count} ${unit('group_by', cur.count)}`;
  const d = cur.count - prev.count;
  if (d === 0) return 'unchanged';
  return d < 0 ? `dropped ${-d} ${unit(cur.key, -d)}` : `added ${d} ${unit(cur.key, d)}`;
}

function FlowStages({ data, active }) {
  return (
    <div className="flex flex-col gap-2">
      {data.map((s, i) => {
        const on = i <= active;
        const isActive = i === active;
        const color = STAGE_COLOR[s.key] || '#0891B2';
        return (
          <div key={s.key} className={`rounded-lg border p-2.5 transition-all ${isActive ? 'border-[rgba(15,23,42,0.25)] shadow-sm' : 'border-[rgba(15,23,42,0.08)]'} ${on ? 'opacity-100' : 'opacity-40'}`}>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-mono text-[10px] font-bold px-1.5 py-0.5 rounded text-white" style={{ background: color }}>{s.label}</span>
              {s.error ? (
                <span className="flex items-center gap-1 font-mono text-[11px] text-[#B91C1C]"><AlertTriangle size={11} /> {s.error}</span>
              ) : s.isResult ? (
                <span className="font-mono text-[12px] text-[#0F172A] font-semibold">{s.count} row{s.count === 1 ? '' : 's'}</span>
              ) : (
                <span className="font-mono text-[12px] text-[#0F172A] font-semibold">{s.count} {unit(s.key, s.count)}</span>
              )}
              {on && delta(data, i) && <span className="font-sans text-[11px] text-[#64748B]">· {delta(data, i)}</span>}
            </div>
            {isActive && s.isResult && s.columns?.length > 0 && (
              <div className="mt-2"><MiniTable columns={s.columns} rows={s.rows} /></div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function fmt(v) {
  if (v === null || v === undefined) return 'NULL';
  if (v instanceof Date) return v.toISOString().slice(0, 10);
  return String(v);
}

function MiniTable({ columns, rows }) {
  return (
    <div className="overflow-x-auto rounded-md border border-[rgba(15,23,42,0.1)]">
      <table className="w-full border-collapse font-mono text-[12px]">
        <thead><tr className="bg-[#f1f5f9]">
          {columns.map((c) => <th key={c} className="text-left font-semibold text-[#0F766E] px-3 py-1.5 border-b border-[rgba(15,23,42,0.1)] whitespace-nowrap">{c}</th>)}
        </tr></thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className={i % 2 ? 'bg-[rgba(15,23,42,0.02)]' : ''}>
              {columns.map((c) => (
                <td key={c} className="px-3 py-1.5 text-[#0F172A] border-b border-[rgba(15,23,42,0.05)] whitespace-nowrap">
                  {row[c] === null || row[c] === undefined ? <span className="text-[#cbd5e1] italic">NULL</span> : fmt(row[c])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
