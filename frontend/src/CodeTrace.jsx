import React, { useState, useCallback } from 'react';
import { tracePython } from './lib/pyodideRunner';
import { Play, ChevronLeft, ChevronRight, Loader2 } from 'lucide-react';

/**
 * Step-through visualizer for a Python snippet (a lesson's `code_walkthrough.code`).
 * Lazily boots Pyodide on first "Visualize execution" click, traces the run, and
 * lets the learner scrub line-by-line watching variables + stdout evolve.
 */
export default function CodeTrace({ code, focus }) {
  const [steps, setSteps] = useState(null);
  const [idx, setIdx] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [truncated, setTruncated] = useState(false);

  const lines = (code || '').replace(/\n$/, '').split('\n');

  const run = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await tracePython(code);
      setSteps(res.steps || []);
      setTruncated(Boolean(res.truncated));
      setIdx(0);
    } catch (e) {
      setError('Could not start the Python runtime — check your connection and try again.');
    } finally {
      setLoading(false);
    }
  }, [code]);

  const cur = steps && steps[idx];
  const localsEntries = cur ? Object.entries(cur.locals || {}) : [];

  return (
    <div className="rounded-lg border border-[rgba(15,23,42,0.12)] overflow-hidden bg-white">
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-[rgba(15,23,42,0.08)] bg-[#f9f9f6]">
        <span className="font-sans text-xs font-semibold text-[#0F172A]">Watch it run</span>
        {steps && (
          <span className="font-mono text-[11px] text-[#64748B]">
            step {idx + 1}/{steps.length}
          </span>
        )}
      </div>

      <div className="grid md:grid-cols-2">
        {/* code with active-line highlight */}
        <pre className="m-0 p-3 text-[12.5px] leading-relaxed font-mono overflow-x-auto bg-[#0b1220] text-[#e2e8f0] min-w-0 max-w-full">
          {lines.map((ln, i) => {
            const active = cur && cur.line === i + 1;
            return (
              <div key={i} className={`px-1 rounded ${active ? 'bg-[#0891B2]/30' : ''}`}>
                <span className="inline-block w-6 text-right mr-3 text-[#475569] select-none">{i + 1}</span>
                {ln || ' '}
              </div>
            );
          })}
        </pre>

        {/* runtime state */}
        <div className="p-3 border-t md:border-t-0 md:border-l border-[rgba(15,23,42,0.08)] flex flex-col gap-3 min-h-[150px] min-w-0">
          {!steps ? (
            <div className="flex-1 flex items-center justify-center">
              <button
                onClick={run}
                disabled={loading}
                className="flex items-center gap-2 text-sm font-semibold text-white bg-[#0891B2] hover:bg-[#0e7490] rounded px-3.5 py-2 transition-colors disabled:opacity-60"
              >
                {loading ? (
                  <><Loader2 size={15} className="animate-spin" /> Starting Python…</>
                ) : (
                  <><Play size={15} /> Visualize execution</>
                )}
              </button>
            </div>
          ) : (
            <>
              <div>
                <div className="font-sans text-[10px] font-bold uppercase tracking-wider text-[#0891B2] mb-1.5">Variables</div>
                {localsEntries.length === 0 ? (
                  <div className="font-mono text-[12px] text-[#94a3b8]">— none yet —</div>
                ) : (
                  <div className="flex flex-col gap-1">
                    {localsEntries.map(([k, v]) => (
                      <div key={k} className="font-mono text-[12px] flex gap-2">
                        <span className="text-[#0F766E] font-semibold shrink-0">{k}</span>
                        <span className="text-[#94a3b8]">=</span>
                        <span className="text-[#0F172A] truncate min-w-0">{v}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              {cur && cur.stdout ? (
                <div>
                  <div className="font-sans text-[10px] font-bold uppercase tracking-wider text-[#64748B] mb-1.5">Output</div>
                  <pre className="m-0 font-mono text-[12px] text-[#0F172A] whitespace-pre-wrap bg-[rgba(15,23,42,0.04)] rounded p-2">{cur.stdout}</pre>
                </div>
              ) : null}
            </>
          )}
        </div>
      </div>

      {/* scrubber */}
      {steps && steps.length > 1 && (
        <div className="flex items-center gap-3 px-4 py-2.5 border-t border-[rgba(15,23,42,0.08)] bg-[#f9f9f6]">
          <button
            onClick={() => setIdx((i) => Math.max(0, i - 1))}
            disabled={idx === 0}
            aria-label="Previous step"
            className="text-[#64748B] hover:text-[#0F172A] disabled:opacity-40"
          >
            <ChevronLeft size={18} />
          </button>
          <input
            type="range"
            min={0}
            max={steps.length - 1}
            value={idx}
            onChange={(e) => setIdx(Number(e.target.value))}
            aria-label="Execution step"
            className="flex-1 h-1.5 appearance-none rounded-full cursor-pointer outline-none
              [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:h-3.5 [&::-webkit-slider-thumb]:w-3.5 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-white [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-[#0891B2] [&::-webkit-slider-thumb]:shadow [&::-webkit-slider-thumb]:transition-transform [&::-webkit-slider-thumb]:hover:scale-110
              [&::-moz-range-thumb]:h-3.5 [&::-moz-range-thumb]:w-3.5 [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:bg-white [&::-moz-range-thumb]:border-2 [&::-moz-range-thumb]:border-[#0891B2] [&::-moz-range-thumb]:border-solid
              [&::-moz-range-track]:h-1.5 [&::-moz-range-track]:rounded-full [&::-moz-range-track]:bg-transparent"
            style={{ background: `linear-gradient(to right, #0891B2 ${(idx / (steps.length - 1)) * 100}%, rgba(15,23,42,0.15) ${(idx / (steps.length - 1)) * 100}%)` }}
          />
          <button
            onClick={() => setIdx((i) => Math.min(steps.length - 1, i + 1))}
            disabled={idx === steps.length - 1}
            aria-label="Next step"
            className="text-[#64748B] hover:text-[#0F172A] disabled:opacity-40"
          >
            <ChevronRight size={18} />
          </button>
        </div>
      )}

      {focus && (
        <div className="px-4 py-2 text-[11px] text-[#64748B] border-t border-[rgba(15,23,42,0.06)]">
          <span className="font-semibold text-[#0891B2]">Watch:</span> {focus}
        </div>
      )}
      {truncated && (
        <div className="px-4 py-2 text-[11px] text-[#B45309] bg-[#B45309]/5">
          Stopped after the step limit (long-running snippet).
        </div>
      )}
      {cur && cur.error && (
        <div className="px-4 py-2 text-[11px] text-[#B91C1C] bg-[#B91C1C]/5 font-mono">{cur.error}</div>
      )}
      {error && <div className="px-4 py-3 text-[12px] text-[#B91C1C]">{error}</div>}
    </div>
  );
}
