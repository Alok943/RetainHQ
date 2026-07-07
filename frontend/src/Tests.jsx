import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Loader2, AlertCircle, CheckCircle2, XCircle, SkipForward,
  Eye, EyeOff, RotateCcw, Trophy, Lightbulb,
} from 'lucide-react';
import { apiFetch } from './lib/api';
import { useAuth } from './lib/AuthContext';
import { track, EVENTS } from './lib/analytics';
import { useSeo } from './lib/useSeo';
import { sampleSession, gradeQuestion } from './lib/testGrading';

/**
 * Tests — the Tests section (docs/SPEC-test-runtime.md, content/PROMPT-tests.md).
 *
 * Production-format-first test sessions: fillup, numeric, code-output, code-fix,
 * code-write, query-write, and (capped, JEE-grade only) mcq. One pass through a
 * weighted sample, then a redemption lap on anything wrong/missed (practice only —
 * doesn't change the score or the FSRS bridge), then submit.
 *
 * Route: /roadmaps/:roadmapSlug/test/:phaseSlug
 */

const SESSION_TARGET = 8;

function Tests() {
  const { roadmapSlug, phaseSlug } = useParams();
  const navigate = useNavigate();
  const { session } = useAuth();

  useSeo(
    `Test — ${(phaseSlug || '').replace(/-/g, ' ')} | RetainHQ`,
    'A short, active test session — fill-ups, code, and queries, not multiple-choice guessing.'
  );

  const [stage, setStage] = useState('loading'); // loading | error | session | redemption | submitting | done
  const [errorMsg, setErrorMsg] = useState(null);
  const [bank, setBank] = useState(null);
  const [questions, setQuestions] = useState([]);       // main-pass sampled questions
  const [redoQueue, setRedoQueue] = useState([]);        // wrong/missed, for the redemption lap
  const [index, setIndex] = useState(0);
  const [results, setResults] = useState([]);            // first-pass outcomes only (scoring + FSRS)
  const [summary, setSummary] = useState(null);           // {score, max_score, rescheduled_nodes}

  const titleBySlugRef = useRef({});

  useEffect(() => {
    if (!session) { setStage('error'); setErrorMsg('Sign in to take a test.'); return; }
    let cancelled = false;

    (async () => {
      try {
        const [bankRes, manifestRes, weights] = await Promise.all([
          fetch(`/content/roadmaps/${roadmapSlug}/_test/${phaseSlug}.json`),
          fetch('/content/manifest.json'),
          apiFetch(`/api/tests/weights?roadmap_slug=${encodeURIComponent(roadmapSlug)}`),
        ]);
        if (!bankRes.ok) throw new Error('No test yet for this phase.');
        const bankJson = await bankRes.json();
        const manifest = manifestRes.ok ? await manifestRes.json() : {};
        const slugByTitle = manifest[roadmapSlug] || {};
        const titleBySlug = Object.fromEntries(Object.entries(slugByTitle).map(([t, s]) => [s, t]));
        titleBySlugRef.current = titleBySlug;

        const weightsByTitle = Object.fromEntries((weights.nodes || []).map((n) => [n.node_title, n]));
        const sampled = sampleSession(bankJson, weightsByTitle, titleBySlug, SESSION_TARGET);

        if (cancelled) return;
        setBank(bankJson);
        setQuestions(sampled);
        setStage('session');
        track(EVENTS.TEST_STARTED, { roadmap: roadmapSlug, phase: phaseSlug, count: sampled.length });
      } catch (e) {
        if (!cancelled) { setErrorMsg(e.message || 'Could not load this test.'); setStage('error'); }
      }
    })();

    return () => { cancelled = true; };
  }, [roadmapSlug, phaseSlug, session]);

  const activeList = stage === 'redemption' ? redoQueue : questions;
  const current = activeList[index] ?? null;

  const recordResult = useCallback((q, outcome, misconception) => {
    if (stage === 'redemption') return; // practice lap — never touches score/FSRS
    const nodeTitle = titleBySlugRef.current[q.node] || q.node;
    setResults((prev) => [
      ...prev,
      { question_id: q.id, node_title: nodeTitle, type: q.type, outcome, trap: !!q.trap, misconception: misconception || null },
    ]);
  }, [stage]);

  const goNext = useCallback(() => {
    const isLast = index >= activeList.length - 1;
    if (!isLast) { setIndex((i) => i + 1); return; }
    // Last question of this pass. recordResult()'s setResults() above hasn't flushed
    // yet (same tick) — the effect below waits for results.length to catch up before
    // deciding redemption-lap vs submit, rather than reading a stale `results` here.
    setStage(stage === 'session' ? 'awaiting-redemption-check' : 'submitting');
  }, [index, activeList.length, stage]);

  // Once the main pass's last result lands, decide: redemption lap, or straight to submit.
  useEffect(() => {
    if (stage !== 'awaiting-redemption-check') return;
    if (results.length < questions.length) return; // last recordResult hasn't flushed yet
    const weak = results.filter((r) => r.outcome !== 'got');
    if (weak.length === 0) { setStage('submitting'); return; }
    const byId = Object.fromEntries(questions.map((q) => [q.id, q]));
    setRedoQueue(weak.map((r) => byId[r.question_id]).filter(Boolean));
    setIndex(0);
    setStage('redemption');
  }, [stage, results, questions]);

  // Submit once we land on 'submitting'.
  useEffect(() => {
    if (stage !== 'submitting') return;
    let cancelled = false;
    (async () => {
      try {
        const res = await apiFetch('/api/tests/attempts', {
          method: 'POST',
          body: JSON.stringify({ roadmap_slug: roadmapSlug, phase: bank?.phase || phaseSlug, results }),
        });
        if (!cancelled) {
          setSummary(res);
          setStage('done');
          track(EVENTS.TEST_COMPLETED, { roadmap: roadmapSlug, phase: bank?.phase || phaseSlug, score: res.score, max_score: res.max_score });
        }
      } catch (e) {
        if (!cancelled) { setErrorMsg(e.message || 'Could not save this attempt.'); setStage('error'); }
      }
    })();
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stage]);

  if (stage === 'loading') {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 flex items-center justify-center gap-2 text-[#64748B] font-sans text-sm">
        <Loader2 size={18} className="animate-spin" /> Preparing your test…
      </div>
    );
  }

  if (stage === 'error') {
    return (
      <div className="max-w-2xl mx-auto px-4 py-10">
        <button onClick={() => navigate(`/roadmaps/${roadmapSlug}`)} className="inline-flex items-center gap-1.5 font-sans text-sm text-[#0891B2] mb-6">
          <ArrowLeft size={15} /> Back to roadmap
        </button>
        <div className="flex items-center gap-2 rounded-lg border border-[#B91C1C]/20 bg-[#B91C1C]/[0.04] p-4 text-[#B91C1C] font-sans text-sm">
          <AlertCircle size={16} /> {errorMsg}
        </div>
      </div>
    );
  }

  if (stage === 'done' && summary) {
    const pct = summary.max_score > 0 ? Math.round((summary.score / summary.max_score) * 100) : 0;
    return (
      <div className="max-w-lg mx-auto px-4 py-16 text-center">
        <Trophy size={40} className="mx-auto text-[#B45309] mb-4" />
        <h1 className="font-sans text-2xl font-bold text-[#0F172A] mb-2">
          {summary.score} / {summary.max_score} points ({pct}%)
        </h1>
        {summary.rescheduled_nodes?.length > 0 && (
          <p className="font-sans text-sm text-[#64748B] mb-6">
            {summary.rescheduled_nodes.length} concept{summary.rescheduled_nodes.length === 1 ? '' : 's'} pulled forward in your reviews so they don't fade.
          </p>
        )}
        <button onClick={() => navigate(`/roadmaps/${roadmapSlug}`)}
          className="rounded-lg bg-[#0891B2] hover:bg-[#0E7490] text-white font-sans text-sm font-semibold px-5 py-2.5 transition-colors">
          Back to roadmap
        </button>
      </div>
    );
  }

  if (stage === 'submitting' || stage === 'awaiting-redemption-check' || !current) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 flex items-center justify-center gap-2 text-[#64748B] font-sans text-sm">
        <Loader2 size={18} className="animate-spin" /> {stage === 'submitting' ? 'Saving your results…' : 'One moment…'}
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <button onClick={() => navigate(`/roadmaps/${roadmapSlug}`)} className="inline-flex items-center gap-1.5 font-sans text-sm text-[#0891B2] mb-4">
        <ArrowLeft size={15} /> Back to roadmap
      </button>

      <div className="flex items-center justify-between mb-2">
        <p className="font-sans text-[11px] font-semibold uppercase tracking-wide text-[#B45309]">
          {stage === 'redemption' ? 'Redemption lap — practice only' : (bank?.phase || 'Test')}
        </p>
        <p className="font-mono text-xs text-[#64748B]">{index + 1} / {activeList.length}</p>
      </div>
      <div className="w-full h-1 bg-[rgba(15,23,42,0.08)] rounded-full overflow-hidden mb-6">
        <div className="h-full bg-[#0891B2] transition-all duration-300" style={{ width: `${((index) / activeList.length) * 100}%` }} />
      </div>

      <QuestionCard
        key={`${stage}-${current.id}-${index}`}
        q={current}
        onResolved={(outcome, misconception) => { recordResult(current, outcome, misconception); goNext(); }}
      />
    </div>
  );
}

// --- Per-question card: input UI + grade + reveal, per type -------------- //

function QuestionCard({ q, onResolved }) {
  const [input, setInput] = useState(q.type === 'code-fix' || q.type === 'code-write' ? q.starter : '');
  const [checked, setChecked] = useState(false);
  const [grading, setGrading] = useState(false);
  const [outcome, setOutcome] = useState(null);   // 'got' | 'wrong'
  const [misconception, setMisconception] = useState(null);
  const [fillupVerdict, setFillupVerdict] = useState(null); // {verdict, feedback} | null
  const [fillupFallback, setFillupFallback] = useState(false); // grader disabled/unavailable

  const commit = async () => {
    setGrading(true);
    try {
      if (q.type === 'fillup') {
        try {
          const res = await apiFetch('/api/tests/grade-fillup', {
            method: 'POST',
            body: JSON.stringify({ question: q.prompt, reference_answer: q.answer, student_answer: input }),
          });
          setFillupVerdict(res);
          setOutcome(res.verdict === 'incorrect' ? 'wrong' : 'got');
          setChecked(true);
        } catch {
          // Grader disabled/unavailable: hand off to the self-mark fallback panel
          // instead — that panel (not this one) owns the reveal until the student
          // clicks Got it/Missed it, so `checked` stays false here.
          setFillupFallback(true);
        }
      } else {
        const r = await gradeQuestion(q, input);
        setOutcome(r.outcome);
        setMisconception(r.misconception);
        setChecked(true);
      }
    } finally {
      setGrading(false);
    }
  };

  const skip = () => onResolved('missed');

  const selfMark = (ok) => { setOutcome(ok ? 'got' : 'wrong'); onResolved(ok ? 'got' : 'wrong'); };

  return (
    <div className="kinetic-card min-h-[260px] flex flex-col px-6 py-8 rounded-xl border border-[rgba(15,23,42,0.12)] bg-white shadow-sm">
      <div className="font-sans text-[11px] font-bold text-[#0891B2] uppercase tracking-widest mb-3">
        {TYPE_LABEL[q.type] || q.type}
      </div>

      <p className="font-sans text-base font-medium text-[#0F172A] leading-relaxed whitespace-pre-wrap mb-4">{q.prompt}</p>

      {(q.type === 'code-output' && q.code) && (
        <pre className="mb-4 rounded-md bg-[#0b1220] text-[#e2e8f0] font-mono text-[12.5px] leading-relaxed overflow-x-auto p-3 whitespace-pre">{q.code}</pre>
      )}
      {(q.type === 'query-write' && q.schema_sql) && (
        <details className="mb-4">
          <summary className="font-sans text-xs text-[#64748B] cursor-pointer">Schema</summary>
          <pre className="mt-1.5 rounded-md bg-[#0b1220] text-[#e2e8f0] font-mono text-[11.5px] leading-relaxed overflow-x-auto p-3 whitespace-pre">{q.schema_sql}</pre>
        </details>
      )}

      {!checked && !fillupFallback && (
        <div className="flex flex-col gap-3">
          <InputForType q={q} value={input} onChange={setInput} />
          <div className="flex gap-2">
            <button onClick={commit} disabled={grading || (!input && q.type !== 'mcq') || (q.type === 'mcq' && input === '')}
              className="rounded-lg bg-[#0891B2] hover:bg-[#0E7490] disabled:opacity-50 text-white font-sans text-sm font-semibold px-4 py-2 transition-colors">
              {grading ? 'Checking…' : 'Check answer'}
            </button>
            <button onClick={skip} disabled={grading}
              className="inline-flex items-center gap-1.5 rounded-lg border border-[rgba(15,23,42,0.15)] text-[#64748B] hover:text-[#0F172A] font-sans text-sm px-3 py-2 transition-colors">
              <SkipForward size={14} /> Skip
            </button>
          </div>
        </div>
      )}

      {fillupFallback && (
        <div className="flex flex-col gap-3">
          <p className="font-sans text-xs text-[#64748B]">Grader unavailable — compare your answer yourself.</p>
          <div className="rounded-lg bg-[#f9f9f6] border border-[rgba(15,23,42,0.08)] p-3">
            <p className="font-sans text-xs font-semibold text-[#64748B] mb-1">Your answer</p>
            <p className="font-sans text-sm text-[#0F172A] mb-2 whitespace-pre-wrap">{input || <span className="italic">blank</span>}</p>
            <p className="font-sans text-xs font-semibold text-[#0F766E] mb-1">Reference answer</p>
            <p className="font-sans text-sm text-[#0F172A] whitespace-pre-wrap">{q.answer}</p>
          </div>
          <div className="flex gap-2">
            <button onClick={() => selfMark(true)} className="rounded-lg bg-[#0F766E] hover:bg-[#0d6a63] text-white font-sans text-sm font-semibold px-3.5 py-2">Got it</button>
            <button onClick={() => selfMark(false)} className="rounded-lg border border-[rgba(15,23,42,0.15)] text-[#64748B] font-sans text-sm px-3.5 py-2">Missed it</button>
          </div>
        </div>
      )}

      {checked && (
        <div className="flex flex-col gap-3 animate-in fade-in duration-200">
          <div className={`flex items-center gap-2 rounded-lg px-3 py-2 font-sans text-sm font-semibold ${
            outcome === 'got' ? 'bg-[#0F766E]/10 text-[#0F766E]' : 'bg-[#B91C1C]/10 text-[#B91C1C]'
          }`}>
            {outcome === 'got' ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
            {outcome === 'got' ? 'Got it' : 'Not quite'}
          </div>

          {q.type === 'fillup' && fillupVerdict && (
            <p className="font-sans text-sm text-[#334155]">{fillupVerdict.feedback}</p>
          )}
          {q.type === 'fillup' && (
            <div className="rounded-lg bg-[#f9f9f6] border border-[rgba(15,23,42,0.08)] p-3">
              <p className="font-sans text-xs font-semibold text-[#0F766E] mb-1">Reference answer</p>
              <p className="font-sans text-sm text-[#0F172A] whitespace-pre-wrap">{q.answer}</p>
            </div>
          )}

          {outcome === 'wrong' && q.trap && q.trap_note && (
            <div className="flex items-start gap-2 rounded-lg bg-[#FEF3C7]/50 border border-[#F59E0B]/25 px-3 py-2">
              <Lightbulb size={14} className="text-[#B45309] shrink-0 mt-0.5" />
              <span className="font-sans text-[13px] text-[#92400E] leading-snug"><strong>The trap:</strong> {q.trap_note}</span>
            </div>
          )}
          {outcome === 'wrong' && misconception && (
            <p className="font-sans text-[13px] text-[#B91C1C]"><strong>Why that's wrong:</strong> {misconception}</p>
          )}

          <p className="font-sans text-sm text-[#334155] leading-relaxed">{q.explain}</p>

          <button onClick={() => onResolved(outcome, misconception)}
            className="self-start rounded-lg bg-[#0F172A] hover:bg-[#1e293b] text-white font-sans text-sm font-semibold px-4 py-2 transition-colors mt-1">
            Next
          </button>
        </div>
      )}
    </div>
  );
}

const TYPE_LABEL = {
  fillup: 'Fill in the blank',
  numeric: 'Compute the answer',
  'code-output': 'Predict the output',
  'code-fix': 'Fix the bug',
  'code-write': 'Write the code',
  'query-write': 'Write the query',
  mcq: 'Choose the correct answer',
};

function InputForType({ q, value, onChange }) {
  if (q.type === 'mcq') {
    return (
      <div className="flex flex-col gap-2">
        {(q.options || []).map((opt, i) => (
          <button key={i} type="button" onClick={() => onChange(i)}
            className={`text-left rounded-lg border px-3.5 py-2.5 font-sans text-sm transition-colors ${
              value === i ? 'border-[#0891B2] bg-[#0891B2]/[0.06] text-[#0F172A]' : 'border-[rgba(15,23,42,0.15)] text-[#334155] hover:border-[#0891B2]/50'
            }`}>
            {opt}
          </button>
        ))}
      </div>
    );
  }
  if (q.type === 'numeric') {
    return (
      <div className="flex items-center gap-2">
        <input type="number" value={value} onChange={(e) => onChange(e.target.value)} autoFocus
          className="w-40 rounded-lg border border-[rgba(15,23,42,0.15)] px-3 py-2 font-mono text-sm focus:outline-none focus:border-[#0891B2] focus:ring-2 focus:ring-[#0891B2]/20" />
        {q.unit && <span className="font-sans text-sm text-[#64748B]">{q.unit}</span>}
      </div>
    );
  }
  if (q.type === 'code-fix' || q.type === 'code-write' || q.type === 'query-write') {
    return (
      <textarea value={value} onChange={(e) => onChange(e.target.value)} rows={q.type === 'query-write' ? 3 : 6} autoFocus spellCheck={false}
        className="w-full resize-y rounded-lg border border-[rgba(15,23,42,0.15)] bg-[#0b1220] text-[#e2e8f0] px-3 py-2.5 font-mono text-[13px] leading-relaxed focus:outline-none focus:border-[#0891B2]" />
    );
  }
  // fillup, code-output: plain text
  return (
    <textarea value={value} onChange={(e) => onChange(e.target.value)} rows={q.type === 'code-output' ? 3 : 2} autoFocus
      placeholder="Your answer…"
      className="w-full resize-none rounded-lg border border-[rgba(15,23,42,0.15)] px-3.5 py-2.5 font-sans text-sm focus:outline-none focus:border-[#0891B2] focus:ring-2 focus:ring-[#0891B2]/20" />
  );
}

export default Tests;
