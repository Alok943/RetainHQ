import React, { useState, useCallback } from 'react';
import { runSql } from './lib/pgliteRunner';
import { Play, Loader2, Database, AlertTriangle } from 'lucide-react';

/**
 * Runs a SQL query against the shared roadmap dataset (PGlite = real Postgres in
 * the browser) and renders the result set as a table. This is the SQL counterpart
 * to <CodeTrace> — runtime is truth, so the learner predicts then runs to confirm.
 *
 * Props: { query, setupSql?, focus?, flowStages?, autoRunLabel? }
 */
const STAGE_LABEL = {
  from: 'FROM', join: 'JOIN', where: 'WHERE', group_by: 'GROUP BY',
  having: 'HAVING', select: 'SELECT', distinct: 'DISTINCT', order_by: 'ORDER BY', limit: 'LIMIT',
};

export default function SqlResult({ query, setupSql, focus, flowStages, autoRunLabel = 'Run query' }) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const run = useCallback(async () => {
    setLoading(true);
    const res = await runSql(query, setupSql);
    setResult(res);
    setLoading(false);
  }, [query, setupSql]);

  const lines = (query || '').replace(/\n$/, '').split('\n');

  return (
    <div className="rounded-lg border border-[rgba(15,23,42,0.12)] overflow-hidden bg-white">
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-[rgba(15,23,42,0.08)] bg-[#f9f9f6]">
        <span className="flex items-center gap-1.5 font-sans text-xs font-semibold text-[#0F172A]">
          <Database size={13} className="text-[#0891B2]" /> SQL
        </span>
        {result && !result.error && (
          <span className="font-mono text-[11px] text-[#64748B]">
            {result.rows.length} row{result.rows.length === 1 ? '' : 's'}
          </span>
        )}
      </div>

      {/* Logical query flow chips (the P2 scrubber starts here as a static teaser) */}
      {flowStages?.length > 0 && (
        <div className="flex flex-wrap items-center gap-1 px-4 py-2 border-b border-[rgba(15,23,42,0.06)] bg-white">
          {flowStages.map((s, i) => (
            <React.Fragment key={s + i}>
              <span className="font-mono text-[10px] font-bold px-1.5 py-0.5 rounded bg-[#0891B2]/10 text-[#0891B2]">
                {STAGE_LABEL[s] || s.toUpperCase()}
              </span>
              {i < flowStages.length - 1 && <span className="text-[#cbd5e1] text-[10px]">→</span>}
            </React.Fragment>
          ))}
          <span className="ml-1 font-sans text-[10px] text-[#94a3b8]">logical query flow</span>
        </div>
      )}

      {/* query */}
      <pre className="m-0 p-3 text-[12.5px] leading-relaxed font-mono overflow-x-auto bg-[#0b1220] text-[#e2e8f0] min-w-0 max-w-full whitespace-pre">
        {lines.map((ln, i) => (
          <div key={i}>{ln || ' '}</div>
        ))}
      </pre>

      {/* run / result */}
      <div className="p-3 border-t border-[rgba(15,23,42,0.08)]">
        {!result ? (
          <button
            onClick={run}
            disabled={loading}
            className="flex items-center gap-2 text-sm font-semibold text-white bg-[#0891B2] hover:bg-[#0e7490] rounded px-3.5 py-2 transition-colors disabled:opacity-60"
          >
            {loading ? (
              <><Loader2 size={15} className="animate-spin" /> Starting Postgres…</>
            ) : (
              <><Play size={15} /> {autoRunLabel}</>
            )}
          </button>
        ) : result.error ? (
          <div className="flex items-start gap-2 rounded-md bg-[#B91C1C]/[0.05] border border-[#B91C1C]/20 p-2.5">
            <AlertTriangle size={14} className="text-[#B91C1C] shrink-0 mt-0.5" />
            <pre className="m-0 font-mono text-[12px] text-[#B91C1C] whitespace-pre-wrap">{result.error}</pre>
          </div>
        ) : result.columns.length === 0 ? (
          <div className="font-mono text-[12px] text-[#64748B]">
            {result.affectedRows != null ? `${result.affectedRows} row(s) affected.` : 'Done.'}
          </div>
        ) : (
          <ResultTable columns={result.columns} rows={result.rows} />
        )}
      </div>

      {focus && (
        <div className="px-4 py-2 text-[11px] text-[#64748B] border-t border-[rgba(15,23,42,0.06)]">
          <span className="font-semibold text-[#0891B2]">Watch:</span> {focus}
        </div>
      )}
    </div>
  );
}

function cell(v) {
  if (v === null || v === undefined) return <span className="text-[#cbd5e1] italic">NULL</span>;
  if (typeof v === 'boolean') return v ? 'true' : 'false';
  if (v instanceof Date) return v.toISOString().slice(0, 10);
  return String(v);
}

function ResultTable({ columns, rows }) {
  return (
    <div className="overflow-x-auto rounded-md border border-[rgba(15,23,42,0.1)]">
      <table className="w-full border-collapse font-mono text-[12px]">
        <thead>
          <tr className="bg-[#f1f5f9]">
            {columns.map((c) => (
              <th key={c} className="text-left font-semibold text-[#0F766E] px-3 py-1.5 border-b border-[rgba(15,23,42,0.1)] whitespace-nowrap">
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className={i % 2 ? 'bg-[rgba(15,23,42,0.02)]' : ''}>
              {columns.map((c) => (
                <td key={c} className="px-3 py-1.5 text-[#0F172A] border-b border-[rgba(15,23,42,0.05)] whitespace-nowrap">
                  {cell(row[c])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
