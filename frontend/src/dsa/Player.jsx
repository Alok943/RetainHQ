import { useMemo, useState, useEffect } from 'react';
import { Play, Pause, ChevronLeft, ChevronRight, RotateCcw, Lock, ChevronDown } from 'lucide-react';
import { getGenerator } from './registry.js';
import { compile } from './compile.js';
import { evaluateCheckpoint, gradeAnswer } from './predict.js';
import ArrayViz from './renderers/ArrayViz.jsx';
import StateMachine from './renderers/StateMachine.jsx';
import StackQueueViz from './renderers/StackQueueViz.jsx';

// The DSA player shell: computes frames once from the generator (events -> compile), then drives
// step state with controls + scrub. Teaching pacing: the COMMENTARY (on top) updates immediately on
// each step, then we hold READ_DELAY so the learner reads it BEFORE the visual animates to that frame
// (caption uses `step`; the renderers use `animatedStep`, which lags by READ_DELAY).
//
// Predict-before-reveal (M1): `predictions` checkpoints resolve against the LIVE event stream
// (predict.js — answers are derived, never authored, so they survive input tweaks). Reaching a
// gate frame by forward play/step pauses playback and locks Next until the learner commits an
// answer or taps "show me"; stepping onward IS the reveal (the real trace). Scrubbing consumes
// gates silently (never re-gates); editing the input or Replay re-arms every gate.
//
// Explain-this-frame (M1): ALWAYS visible inline (never behind a toggle — the teacher dominates,
// not opt-in), derived client-side from the frame + lesson model — what happened (op + caption),
// why it's correct (invariant), why this choice (repeated_decision), what's next (next frame's
// caption). The "next" row is HIDDEN while a gate is unanswered (no-future-leak: it would answer
// the open prediction). After a missed prediction, the panel flashes a brief highlight — the best
// teaching moment — rather than needing to be opened.
const READ_DELAY = 1400; // ms to read the comment before the animation plays
const DWELL = 950;       // ms to watch the animation before auto-advancing

// Pseudocode panel — sits above StateMachine in the right column. Uses the lesson's authored
// `steps` ({id, label}) when given; otherwise derives a fallback from the compiled frames (unique
// step_ids in order of first appearance, id-as-label) so untouched lessons still show something.
// Highlights the row matching the CURRENT COMMENTARY frame's step_id (capFrame — the teaching
// voice leads, not the lagged visual).
function PseudoSteps({ steps, frames, activeStepId }) {
  const rows = steps.length ? steps : (() => {
    const seen = new Set();
    const out = [];
    for (const f of frames) {
      if (f.step_id && !seen.has(f.step_id)) { seen.add(f.step_id); out.push({ id: f.step_id, label: f.step_id }); }
    }
    return out;
  })();
  if (!rows.length) return null;
  return (
    <div className="select-none">
      <div className="font-sans text-[10px] font-bold uppercase tracking-wider text-[#64748B] mb-2">Pseudocode</div>
      <div className="flex flex-col gap-1.5">
        {rows.map((s) => {
          const active = s.id === activeStepId;
          return (
            <div key={s.id} className="rounded-md px-2.5 py-1.5 font-mono text-[11.5px] border leading-snug" style={{
              background: active ? 'rgba(124,58,237,0.10)' : 'rgba(15,23,42,0.03)',
              borderColor: active ? '#7C3AED' : 'rgba(15,23,42,0.10)',
              color: active ? '#7C3AED' : '#475569',
              fontWeight: active ? 700 : 500,
            }}>
              {s.label}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// Code panel (M2 / D7) — collapsed-by-default, full-width block below the controls row.
// Schema (lesson `viz.code`, optional):
//   viz.code = { "python": { "src": "<multiline string>", "lineMap": { "<step_id>": [1,2], ... } }, "java": {...}, ... }
// `src` is a full-language snippet; `lineMap` keys are canonical step_ids (§9.4) and values are
// 1-based source line numbers implementing that step. The panel highlights whatever lines
// `code[lang].lineMap[capFrame.step_id]` lists, synced across whichever language tab is active —
// scrubbing/stepping moves the highlight for free because it just reads the current step_id.
// Pure presentation: never derives step state, guards every lookup (missing step_id/lang -> no
// highlight, never a crash). Renders nothing when `code` is null/empty (no header at all).
function CodePanel({ code, activeStepId }) {
  const langs = code ? Object.keys(code) : [];
  const [open, setOpen] = useState(false);
  const [lang, setLang] = useState(langs[0] || '');
  useEffect(() => { if (langs.length && !langs.includes(lang)) setLang(langs[0]); }, [langs.join('|')]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!code || !langs.length) return null;

  const entry = code[lang] || code[langs[0]];
  const src = entry?.src || '';
  const lines = src.split('\n');
  const highlighted = new Set(
    Array.isArray(entry?.lineMap?.[activeStepId]) ? entry.lineMap[activeStepId] : [],
  );

  return (
    <div className="border-t border-[rgba(15,23,42,0.06)]">
      <button
        className="w-full flex items-center gap-2 px-5 py-3 text-left hover:bg-[#f9f9f6] transition-colors"
        onClick={() => setOpen((o) => !o)}
      >
        {open ? <ChevronDown size={15} className="text-[#64748B] shrink-0" /> : <ChevronRight size={15} className="text-[#64748B] shrink-0" />}
        <span className="font-sans text-[13px] font-semibold text-[#475569]">Code</span>
      </button>
      {open && (
        <div className="px-5 pb-4">
          <div className="flex items-center gap-1.5 mb-2">
            {langs.map((l) => (
              <button
                key={l}
                onClick={() => setLang(l)}
                className={`font-mono text-[11px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-md border transition-colors ${
                  l === lang
                    ? 'bg-[#0F172A] text-white border-[#0F172A]'
                    : 'bg-white text-[#64748B] border-[rgba(15,23,42,0.12)] hover:bg-[#f1f5f9]'
                }`}
              >
                {l}
              </button>
            ))}
          </div>
          <div className="rounded-lg overflow-hidden border border-[rgba(15,23,42,0.08)] bg-[#0b1220]">
            <pre className="overflow-x-auto text-[12.5px] leading-[1.6] py-2">
              {lines.map((line, i) => {
                const lineNo = i + 1;
                const isActive = highlighted.has(lineNo);
                return (
                  <div
                    key={lineNo}
                    className={`px-3 flex gap-3 ${isActive ? 'bg-[#0891B2]/30' : ''}`}
                  >
                    <span className="select-none text-[#475569] w-6 text-right shrink-0">{lineNo}</span>
                    <code className="font-mono text-[#e2e8f0] whitespace-pre">{line || ' '}</code>
                  </div>
                );
              })}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}

export default function Player({
  generatorKey,
  defaultInput = [5, 2, 8, 1, 9, 3],
  invariants = {},
  inputMode = 'number',
  predictions = [],
  repeatedDecision = '',
  steps = [],
  code = null,
}) {
  const generator = getGenerator(generatorKey);
  const isString = inputMode === 'string';
  const [input, setInput] = useState(defaultInput);
  const [draft, setDraft] = useState(defaultInput.join(isString ? '' : ', '));
  const [step, setStep] = useState(0);
  const [animatedStep, setAnimatedStep] = useState(0);
  const [playing, setPlaying] = useState(false);

  const { frames, events } = useMemo(() => {
    if (!generator) return { frames: [], events: [] };
    // Use the generator's RETURNED input — some generators transform it (e.g. binary
    // search sorts first), and compile must materialize from that same array.
    const { input: genInput, events: evs } = generator(input);
    return { frames: compile(genInput ?? input, evs), events: evs };
  }, [generator, input]);

  // Gates: checkpoints resolved against the live trace. A checkpoint that doesn't occur for this
  // input evaluates to null and is silently skipped.
  const gates = useMemo(
    () => (predictions || [])
      .map((p) => evaluateCheckpoint(events, p))
      .filter(Boolean)
      .sort((a, b) => a.gateIndex - b.gateIndex),
    [events, predictions],
  );
  const [fired, setFired] = useState(() => new Set()); // gateIndexes answered/shown/consumed
  const [gateResult, setGateResult] = useState(null);  // { gate, correct|null, given? } for the just-resolved gate
  const [answerDraft, setAnswerDraft] = useState('');

  const last = frames.length - 1;
  const capFrame = frames[Math.min(step, last)] || null;          // commentary = current step (immediate)
  const visFrame = frames[Math.min(animatedStep, last)] || null;  // visuals = lagged step (after read pause)
  const reading = step !== animatedStep;
  const nextFrame = frames[Math.min(step, last) + 1] || null;

  const activeGate = gates.find((g) => g.gateIndex === Math.min(step, last) && !fired.has(g.gateIndex)) || null;

  // Hold the comment, THEN animate the visual to the new step.
  useEffect(() => {
    if (animatedStep === step) return;
    const t = setTimeout(() => setAnimatedStep(step), READ_DELAY);
    return () => clearTimeout(t);
  }, [step, animatedStep]);

  // Auto-advance: read pause + dwell per step. An open gate pauses playback (predict-before-reveal).
  useEffect(() => {
    if (!playing) return;
    if (activeGate) { setPlaying(false); return; }
    if (step >= last) { setPlaying(false); return; }
    const t = setTimeout(() => setStep((s) => Math.min(last, s + 1)), READ_DELAY + DWELL);
    return () => clearTimeout(t);
  }, [playing, step, last, activeGate]);

  useEffect(() => { if (step > last) { setStep(Math.max(0, last)); setAnimatedStep(Math.max(0, last)); } }, [last, step]);

  // Any step change clears the just-resolved gate feedback + answer draft.
  useEffect(() => { setGateResult(null); setAnswerDraft(''); }, [step]);

  if (!generator) return <div className="text-[#ba1a1a] text-sm">Unknown visualizer: {generatorKey}</div>;

  const seek = (v) => { // scrub = immediate, no read pause; consumes any gates at/before the target (never re-gates)
    setPlaying(false);
    setFired((prev) => {
      const next = new Set(prev);
      for (const g of gates) if (g.gateIndex <= v) next.add(g.gateIndex);
      return next;
    });
    setStep(v); setAnimatedStep(v);
  };
  const nav = (v) => { setPlaying(false); setStep(Math.max(0, Math.min(last, v))); }; // prev/next = read pause applies
  const replay = () => { setFired(new Set()); setGateResult(null); setStep(0); setAnimatedStep(0); setPlaying(true); }; // re-arms all gates
  const applyInput = () => {
    const vals = isString
      ? draft.replace(/\s+/g, '').split('').slice(0, 14)
      : draft.split(/[\s,]+/).map((x) => parseInt(x, 10)).filter((x) => Number.isFinite(x)).slice(0, 12);
    if (vals.length) {
      setInput(vals); setStep(0); setAnimatedStep(0); setPlaying(false);
      setFired(new Set()); setGateResult(null); // new trace -> gates re-arm + re-derive
    }
  };

  const commitGate = (given) => {
    if (!activeGate) return;
    const correct = gradeAnswer(activeGate.type, activeGate.answer, given);
    setGateResult({ gate: activeGate, correct, given });
    setFired((prev) => new Set(prev).add(activeGate.gateIndex));
  };
  const commitTyped = () => {
    if (!answerDraft.trim()) return;
    const multi = activeGate.type === 'values' || activeGate.type === 'pair';
    commitGate(multi ? answerDraft.split(/[\s,]+/).filter(Boolean) : answerDraft.trim());
  };
  const showMe = () => {
    if (!activeGate) return;
    setGateResult({ gate: activeGate, correct: null });
    setFired((prev) => new Set(prev).add(activeGate.gateIndex));
  };

  const btn = 'inline-flex items-center justify-center gap-1.5 rounded-md px-3 py-1.5 text-[13px] font-semibold border border-[rgba(15,23,42,0.12)] bg-white hover:bg-[#f1f5f9] disabled:opacity-40 transition-colors';
  const invariantText = capFrame?.invariant ? (invariants[capFrame.invariant] || capFrame.invariant) : null;
  // no-future-leak: never reveal upcoming information while a prediction is open
  const gateOpen = !!activeGate && !gateResult;

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
        {invariantText && (
          <p className="font-sans text-[12.5px] text-[#a5b4fc] leading-snug mt-1">
            <span className="font-bold">Invariant: </span>{invariantText}
          </p>
        )}
      </div>

      {/* PREDICTION GATE — commit before the reveal. Stepping onward shows the real trace. */}
      {activeGate && !gateResult && (
        <div className="px-5 py-3.5 bg-[#7C3AED]/[0.06] border-b border-[#7C3AED]/20">
          <div className="flex items-center gap-2 mb-2">
            <Lock size={13} className="text-[#7C3AED] shrink-0" />
            <span className="font-sans text-[10px] font-bold uppercase tracking-wider text-[#7C3AED]">Predict before you reveal</span>
            <span className="font-mono text-[10px] text-[#64748B] ml-auto uppercase">{activeGate.level}</span>
          </div>
          <p className="font-sans text-sm font-semibold text-[#0F172A] leading-snug mb-2.5">{activeGate.prompt}</p>
          {activeGate.type === 'choice' ? (
            <div className="flex flex-wrap items-center gap-2">
              {(activeGate.choices || []).map((c) => (
                <button key={c} className={btn} onClick={() => commitGate(c)}>{c}</button>
              ))}
              <button className="font-sans text-[12px] text-[#64748B] underline ml-auto" onClick={showMe}>show me</button>
            </div>
          ) : (
            <div className="flex flex-wrap items-center gap-2">
              <input
                value={answerDraft}
                onChange={(e) => setAnswerDraft(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && commitTyped()}
                className="flex-1 min-w-[120px] font-mono text-[13px] rounded-md border border-[#7C3AED]/30 px-2.5 py-1.5 bg-white"
                placeholder={activeGate.type === 'values' || activeGate.type === 'pair' ? 'e.g. 3, 7' : 'your answer'}
                autoFocus
              />
              <button className={btn} onClick={commitTyped}>Commit</button>
              <button className="font-sans text-[12px] text-[#64748B] underline" onClick={showMe}>show me</button>
            </div>
          )}
        </div>
      )}

      {/* Gate feedback — after commit/show-me; stepping clears it and reveals the trace. */}
      {gateResult && (
        <div className={`px-5 py-2.5 border-b text-[13px] font-sans font-semibold leading-snug ${
          gateResult.correct === true ? 'bg-[#0F766E]/[0.07] border-[#0F766E]/20 text-[#0F766E]'
          : gateResult.correct === false ? 'bg-[#B91C1C]/[0.06] border-[#B91C1C]/20 text-[#B91C1C]'
          : 'bg-[#f9f9f6] border-[rgba(15,23,42,0.08)] text-[#475569]'}`}>
          {gateResult.correct === true && <>Correct — the trace shows: {gateResult.gate.display}. Step through to watch it happen.</>}
          {gateResult.correct === false && <>Not quite — the trace shows: {gateResult.gate.display}. See the explanation below, then step through it.</>}
          {gateResult.correct === null && <>The trace shows: {gateResult.gate.display}. Step through to watch it happen.</>}
        </div>
      )}

      {/* VISUALIZATION — lags the comment by READ_DELAY */}
      <div className="grid grid-cols-1 md:grid-cols-[minmax(0,1fr)_240px] gap-4 p-5">
        <div><ArrayViz frame={visFrame} /></div>
        <div className="md:border-l md:pl-4 border-[rgba(15,23,42,0.08)]">
          <PseudoSteps steps={steps} frames={frames} activeStepId={capFrame?.step_id} />
          {visFrame && (visFrame.stack || visFrame.queue) && (
            <div className="border-t border-[rgba(15,23,42,0.08)] mt-3 pt-3">
              <StackQueueViz frame={visFrame} />
            </div>
          )}
          <div className="border-t border-[rgba(15,23,42,0.08)] mt-3 pt-3"><StateMachine frame={visFrame} /></div>
        </div>
      </div>

      {/* controls */}
      <div className="px-5 py-3 border-t border-[rgba(15,23,42,0.06)] flex flex-wrap items-center gap-2">
        <button className={btn} onClick={() => nav(step - 1)} disabled={step === 0}><ChevronLeft size={15} /> Prev</button>
        {step >= last
          ? <button className={btn} onClick={replay}><RotateCcw size={15} /> Replay</button>
          : <button className={btn} onClick={() => setPlaying((p) => !p)} disabled={gateOpen}>{playing ? <><Pause size={15} /> Pause</> : <><Play size={15} /> Play</>}</button>}
        <button className={btn} onClick={() => nav(step + 1)} disabled={step >= last || gateOpen} title={gateOpen ? 'Commit your prediction first' : undefined}>Next <ChevronRight size={15} /></button>
        <input type="range" min={0} max={Math.max(0, last)} value={Math.min(step, last)} onChange={(e) => seek(Number(e.target.value))} className="flex-1 min-w-[120px] accent-[#7C3AED]" />
      </div>

      {/* CODE PANEL (M2 / D7) — collapsed by default, full-width, below controls. Line highlight
          syncs to capFrame.step_id (the commentary-leading step), not the lagged visual step. */}
      <CodePanel code={code} activeStepId={capFrame?.step_id} />

      {/* EXPLAIN THIS FRAME — always inline, derived from the frame + lesson model; nothing authored
          per-frame. Post-miss: a brief ring flash draws the eye instead of needing to be opened. */}
      {capFrame && (
        <div className={`px-5 py-3.5 border-t bg-[#f9f9f6] flex flex-col gap-2 transition-shadow ${
          gateResult?.correct === false ? 'border-[#B45309]/30 ring-1 ring-inset ring-[#B45309]/40' : 'border-[rgba(15,23,42,0.06)]'}`}>
          <div className="flex items-start gap-2.5">
            <span className="font-sans text-[10px] font-bold uppercase tracking-wider text-[#0891B2] shrink-0 mt-0.5 w-24">What happened</span>
            <span className="font-sans text-[13px] text-[#0F172A] leading-snug"><span className="font-mono text-[11px] font-bold text-[#7C3AED]">{capFrame.activeOp}</span> — {capFrame.caption}</span>
          </div>
          {invariantText && (
            <div className="flex items-start gap-2.5">
              <span className="font-sans text-[10px] font-bold uppercase tracking-wider text-[#0F766E] shrink-0 mt-0.5 w-24">Why it's correct</span>
              <span className="font-sans text-[13px] text-[#0F172A] leading-snug">{invariantText}</span>
            </div>
          )}
          {repeatedDecision && (
            <div className="flex items-start gap-2.5">
              <span className="font-sans text-[10px] font-bold uppercase tracking-wider text-[#7C3AED] shrink-0 mt-0.5 w-24">The decision</span>
              <span className="font-sans text-[13px] text-[#0F172A] leading-snug">{repeatedDecision}</span>
            </div>
          )}
          {/* no-future-leak: the next row would answer an open prediction — hold it until committed */}
          {nextFrame && !gateOpen && (
            <div className="flex items-start gap-2.5">
              <span className="font-sans text-[10px] font-bold uppercase tracking-wider text-[#B45309] shrink-0 mt-0.5 w-24">Next</span>
              <span className="font-sans text-[13px] text-[#475569] leading-snug">{nextFrame.caption}</span>
            </div>
          )}
          {gateOpen && (
            <div className="flex items-start gap-2.5">
              <span className="font-sans text-[10px] font-bold uppercase tracking-wider text-[#B45309] shrink-0 mt-0.5 w-24">Next</span>
              <span className="font-sans text-[13px] text-[#94a3b8] italic leading-snug">commit your prediction first</span>
            </div>
          )}
        </div>
      )}

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
