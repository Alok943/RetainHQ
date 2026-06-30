import { useMemo, useState, useEffect } from 'react';
import { Play, Pause, ChevronLeft, ChevronRight, RotateCcw } from 'lucide-react';
import { getGenerator } from './registry.js';
import { compile } from './compile.js';
import ArrayViz from './renderers/ArrayViz.jsx';
import StateMachine from './renderers/StateMachine.jsx';

// The DSA player shell: computes frames once from the generator (events -> compile), then drives
// step state with controls + scrub. Teaching pacing: the COMMENTARY (on top) updates immediately on
// each step, then we hold READ_DELAY so the learner reads it BEFORE the visual animates to that frame
// (caption uses `step`; the renderers use `animatedStep`, which lags by READ_DELAY). Framer Motion
// loads with this lazy chunk. Predict-before-reveal gate lands next.
const READ_DELAY = 1400; // ms to read the comment before the animation plays
const DWELL = 950;       // ms to watch the animation before auto-advancing

export default function Player({ generatorKey, defaultInput = [5, 2, 8, 1, 9, 3], invariants = {}, inputMode = 'number' }) {
  const generator = getGenerator(generatorKey);
  const isString = inputMode === 'string';
  const [input, setInput] = useState(defaultInput);
  const [draft, setDraft] = useState(defaultInput.join(isString ? '' : ', '));
  const [step, setStep] = useState(0);
  const [animatedStep, setAnimatedStep] = useState(0);
  const [playing, setPlaying] = useState(false);

  const frames = useMemo(() => {
    if (!generator) return [];
    const { events } = generator(input);
    return compile(input, events);
  }, [generator, input]);

  const last = frames.length - 1;
  const capFrame = frames[Math.min(step, last)] || null;          // commentary = current step (immediate)
  const visFrame = frames[Math.min(animatedStep, last)] || null;  // visuals = lagged step (after read pause)
  const reading = step !== animatedStep;

  // Hold the comment, THEN animate the visual to the new step.
  useEffect(() => {
    if (animatedStep === step) return;
    const t = setTimeout(() => setAnimatedStep(step), READ_DELAY);
    return () => clearTimeout(t);
  }, [step, animatedStep]);

  // Auto-advance: read pause + dwell per step.
  useEffect(() => {
    if (!playing) return;
    if (step >= last) { setPlaying(false); return; }
    const t = setTimeout(() => setStep((s) => Math.min(last, s + 1)), READ_DELAY + DWELL);
    return () => clearTimeout(t);
  }, [playing, step, last]);

  useEffect(() => { if (step > last) { setStep(Math.max(0, last)); setAnimatedStep(Math.max(0, last)); } }, [last, step]);

  if (!generator) return <div className="text-[#ba1a1a] text-sm">Unknown visualizer: {generatorKey}</div>;

  const seek = (v) => { setPlaying(false); setStep(v); setAnimatedStep(v); }; // scrub = immediate, no read pause
  const nav = (v) => { setPlaying(false); setStep(Math.max(0, Math.min(last, v))); }; // prev/next = read pause applies
  const applyInput = () => {
    const vals = isString
      ? draft.replace(/\s+/g, '').split('').slice(0, 14)
      : draft.split(/[\s,]+/).map((x) => parseInt(x, 10)).filter((x) => Number.isFinite(x)).slice(0, 12);
    if (vals.length) { setInput(vals); setStep(0); setAnimatedStep(0); setPlaying(false); }
  };

  const btn = 'inline-flex items-center justify-center gap-1.5 rounded-md px-3 py-1.5 text-[13px] font-semibold border border-[rgba(15,23,42,0.12)] bg-white hover:bg-[#f1f5f9] disabled:opacity-40 transition-colors';
  const legend = [
    ['#0891B2', 'left'], ['#B45309', 'right'], ['#7C3AED', 'writing'], ['#0F766E', 'sorted'],
  ];

  return (
    <div className="rounded-xl border border-[rgba(15,23,42,0.12)] bg-white overflow-hidden">
      {/* COMMENTARY — on top. Updates immediately; visual animates after the read pause. */}
      <div className="px-5 py-3 bg-[#0F172A] text-white">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-mono text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-[#7C3AED] text-white shrink-0">{capFrame?.activeOp}</span>
          {reading && <span className="font-sans text-[10px] text-[#94a3b8] animate-pulse">reading…</span>}
          <span className="font-mono text-[11px] text-[#64748B] ml-auto shrink-0">{Math.min(step, last) + 1}/{frames.length}</span>
        </div>
        <p className="font-sans text-[15px] font-semibold leading-snug">{capFrame?.caption}</p>
        {capFrame?.invariant && (
          <p className="font-sans text-[12.5px] text-[#a5b4fc] leading-snug mt-1">
            <span className="font-bold">Invariant: </span>{invariants[capFrame.invariant] || capFrame.invariant}
          </p>
        )}
      </div>

      {/* VISUALIZATION — lags the comment by READ_DELAY */}
      <div className="grid grid-cols-1 md:grid-cols-[1fr_180px] gap-4 p-5">
        <div><ArrayViz frame={visFrame} /></div>
        <div className="md:border-l md:pl-4 border-[rgba(15,23,42,0.08)]"><StateMachine frame={visFrame} /></div>
      </div>

      {/* legend */}
      <div className="px-5 pb-3 flex flex-wrap items-center gap-x-4 gap-y-1">
        {legend.map(([c, l]) => (
          <span key={l} className="inline-flex items-center gap-1.5 font-sans text-[11px] text-[#64748B]">
            <span className="w-3 h-3 rounded-sm" style={{ backgroundColor: c }} /> {l}
          </span>
        ))}
      </div>

      {/* controls */}
      <div className="px-5 py-3 border-t border-[rgba(15,23,42,0.06)] flex flex-wrap items-center gap-2">
        <button className={btn} onClick={() => nav(step - 1)} disabled={step === 0}><ChevronLeft size={15} /> Prev</button>
        {step >= last
          ? <button className={btn} onClick={() => { seek(0); setPlaying(true); }}><RotateCcw size={15} /> Replay</button>
          : <button className={btn} onClick={() => setPlaying((p) => !p)}>{playing ? <><Pause size={15} /> Pause</> : <><Play size={15} /> Play</>}</button>}
        <button className={btn} onClick={() => nav(step + 1)} disabled={step >= last}>Next <ChevronRight size={15} /></button>
        <input type="range" min={0} max={Math.max(0, last)} value={Math.min(step, last)} onChange={(e) => seek(Number(e.target.value))} className="flex-1 min-w-[120px] accent-[#7C3AED]" />
      </div>

      {/* tweak the values */}
      <div className="px-5 py-3 border-t border-[rgba(15,23,42,0.06)] bg-[#f9f9f6] flex items-center gap-2">
        <span className="font-sans text-[12px] font-semibold text-[#475569] shrink-0">{isString ? 'Try a word:' : 'Tweak input:'}</span>
        <input value={draft} onChange={(e) => setDraft(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && applyInput()}
          className="flex-1 min-w-[120px] font-mono text-[13px] rounded-md border border-[rgba(15,23,42,0.15)] px-2.5 py-1.5 bg-white" placeholder={isString ? 'racecar' : '5, 2, 8, 1, 9, 3'} />
        <button className={btn} onClick={applyInput}>Run</button>
      </div>
    </div>
  );
}
