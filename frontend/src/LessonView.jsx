import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, BookOpen, Clock, BarChart2, Zap, AlertTriangle, HelpCircle, Code2, Trophy, ExternalLink, ChevronDown, ChevronRight, Eye, EyeOff, Lightbulb, Target, Sparkles, Brain, Bug, GitBranch, Database, Table, Check, Plus } from 'lucide-react';
import { apiFetch } from './lib/api';
import { CONTENT_KEY_BY_TITLE } from './lib/contentRoadmaps';
import CodeTrace from './CodeTrace';
import { prewarmPython } from './lib/pyodideRunner';
import { useAuth } from './lib/AuthContext';
import SqlResult from './SqlResult';
import SqlFlow from './SqlFlow';
import SqlJoinViz from './SqlJoinViz';

const TIER_LABEL = { tier1: 'Tier 1', tier2: 'Tier 2', tier3: 'Tier 3' };
const TIER_COLOR = { tier1: '#0F766E', tier2: '#B45309', tier3: '#B91C1C' };
const DIFF_COLOR = { easy: '#0F766E', medium: '#B45309', hard: '#B91C1C' };

// Understanding-check intents → badge label, colour, icon.
const CHECK_META = {
  'predict-output': { label: 'Predict the output', color: '#7C3AED', icon: <Sparkles size={11} /> },
  'predict-result': { label: 'Predict the result', color: '#0891B2', icon: <Table size={11} /> },
  'find-bug': { label: 'Find the bug', color: '#B91C1C', icon: <Bug size={11} /> },
  'explain-behavior': { label: 'Explain the behaviour', color: '#0891B2', icon: <HelpCircle size={11} /> },
  'choose-model': { label: 'Pick the correct model', color: '#B45309', icon: <GitBranch size={11} /> },
  'debug-misconception': { label: 'Debug the misconception', color: '#0F766E', icon: <Lightbulb size={11} /> },
};

export default function LessonView() {
  const { id, slug } = useParams();
  const navigate = useNavigate();
  const location = useLocation();

  const [lesson, setLesson] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Track which recall answers are revealed
  const [revealed, setRevealed] = useState(new Set());
  const toggleReveal = useCallback((i) => {
    setRevealed((s) => {
      const ns = new Set(s);
      ns.has(i) ? ns.delete(i) : ns.add(i);
      return ns;
    });
  }, []);

  // Predict-before-reveal gate for the aha_moment block.
  const [ahaRevealed, setAhaRevealed] = useState(false);

  // Per-check predict-before-reveal gates for understanding_checks.
  const [checksRevealed, setChecksRevealed] = useState(new Set());
  const toggleCheck = useCallback((i) => {
    setChecksRevealed((s) => {
      const ns = new Set(s);
      ns.has(i) ? ns.delete(i) : ns.add(i);
      return ns;
    });
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      setAhaRevealed(false);
      setRevealed(new Set());
      setChecksRevealed(new Set());
      try {
        // Content key resolution: router state (fastest) → the :id param itself when
        // it's a slug (the slug IS the content key) → a meta fetch for old UUID links.
        let contentKey = location.state?.contentKey;
        if (!contentKey) {
          const isUuid = /^[0-9a-f]{8}-[0-9a-f]{4}-/i.test(id);
          if (!isUuid) {
            contentKey = id;
          } else {
            const meta = await apiFetch(`/api/roadmaps/${id}`, { optionalAuth: true });
            contentKey = meta.slug || CONTENT_KEY_BY_TITLE[meta.title];
          }
        }
        if (!contentKey) throw new Error('no-content-key');

        const res = await fetch(`/content/roadmaps/${contentKey}/${slug}.json`);
        if (!res.ok) throw new Error('not-found');
        const data = await res.json();
        if (!cancelled) {
          setLesson(data);
          // Warm the Python runtime in the background for lessons that use the
          // CodeTrace step-scrubber (code_walkthrough / aha_moment), so the first
          // "Visualize execution" is instant. SQL (PGlite) and aptitude (no runtime)
          // lessons skip this — nothing to prewarm.
          const usesPython = data.runtime !== 'sql' && (data.code_walkthrough || data.aha_moment);
          if (usesPython) prewarmPython();
        }
      } catch (err) {
        if (!cancelled) setError(err.message === 'not-found' || err.message === 'no-content-key' ? 'not-found' : 'error');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, [id, slug, location.state?.contentKey]);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-[#0891B2] border-t-transparent rounded-full animate-spin" />
          <span className="font-sans text-sm text-[#64748B]">Loading lesson…</span>
        </div>
      </div>
    );
  }

  if (error || !lesson) {
    return (
      <div className="max-w-3xl mx-auto px-4 md:px-8 py-12 text-center">
        <div className="glass-card p-8 flex flex-col items-center gap-4">
          <BookOpen size={32} className="text-[#94a3b8]" />
          <h2 className="font-sans text-lg font-semibold text-[#0F172A]">Lesson not available yet</h2>
          <p className="font-sans text-sm text-[#64748B]">We haven't published content for this topic yet. Check back soon!</p>
          <button
            onClick={() => navigate(`/roadmaps/${id}`)}
            className="flex items-center gap-2 font-sans text-sm font-semibold text-[#0891B2] hover:text-[#0F172A] transition-colors"
          >
            <ArrowLeft size={16} /> Back to roadmap
          </button>
        </div>
      </div>
    );
  }

  const tierColor = TIER_COLOR[lesson.tier] || '#0891B2';
  const diffColor = DIFF_COLOR[lesson.metadata?.difficulty] || '#64748B';

  // Shared header chrome (title + meta badges) — reused by the standard and
  // aptitude/reasoning render paths.
  const header = (
    <>
      <button
        onClick={() => navigate(`/roadmaps/${id}`)}
        className="flex items-center gap-2 text-[#64748B] hover:text-[#0F172A] font-sans text-sm font-medium mb-4 transition-colors"
      >
        <ArrowLeft size={16} /> Back to roadmap
      </button>

      <div className="mb-6">
        <div className="flex items-start justify-between gap-3 mb-3">
          <h1 className="font-sans text-2xl md:text-3xl font-semibold text-[#0F172A] leading-tight">
            {lesson.title}
          </h1>
          {location.state?.nodeId && <AddToReviews lesson={lesson} nodeId={location.state.nodeId} />}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {lesson.tier && (
            <span
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full font-sans text-[11px] font-bold border"
              style={{ color: tierColor, borderColor: tierColor + '40' }}
            >
              <Target size={11} /> {TIER_LABEL[lesson.tier] || lesson.tier}
            </span>
          )}
          {lesson.metadata?.difficulty && (
            <span
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full font-sans text-[11px] font-bold border"
              style={{ color: diffColor, borderColor: diffColor + '40' }}
            >
              <BarChart2 size={11} /> {lesson.metadata.difficulty.charAt(0).toUpperCase() + lesson.metadata.difficulty.slice(1)}
            </span>
          )}
          {lesson.metadata?.estimated_minutes && (
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full font-sans text-[11px] font-semibold text-[#64748B] border border-[rgba(15,23,42,0.12)]">
              <Clock size={11} /> {lesson.metadata.estimated_minutes} min
            </span>
          )}
          {lesson.metadata?.interview_frequency && lesson.metadata.interview_frequency !== 'low' && (
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full font-sans text-[11px] font-semibold text-[#B45309] border border-[#B45309]/30">
              <Zap size={11} /> Interview: {lesson.metadata.interview_frequency}
            </span>
          )}
        </div>
      </div>
    </>
  );

  // Aptitude (quant) + Reasoning (logical/verbal) are thin, method/intuition-first
  // lessons — a completely different shape from python/sql. Render them here and
  // return early, before the overview/walkthrough code that assumes those fields.
  if (lesson.kind === 'aptitude' || lesson.kind === 'reasoning' || lesson.kind === 'theory') {
    return (
      <div className="max-w-3xl mx-auto w-full px-4 md:px-8 py-6 pb-24">
        {header}
        <AptitudeReasoningBody
          lesson={lesson}
          revealed={revealed}
          toggleReveal={toggleReveal}
          ahaRevealed={ahaRevealed}
          setAhaRevealed={setAhaRevealed}
          oaRevealed={checksRevealed}
          toggleOa={toggleCheck}
        />
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto w-full px-4 md:px-8 py-6 pb-24">
      {header}

      {/* --- §1 Overview --- */}
      <Section icon={<BookOpen size={16} />} title="Overview">
        <RichText text={lesson.overview.what} />
        <div className="mt-3"><RichText text={lesson.overview.why} tone="muted" /></div>
        {lesson.overview.where_used?.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-3">
            {lesson.overview.where_used.map((tag) => (
              <span key={tag} className="px-2.5 py-1 rounded-full bg-[#0891B2]/10 font-sans text-[11px] font-semibold text-[#0891B2]">
                {tag}
              </span>
            ))}
          </div>
        )}
      </Section>

      {/* --- Predict & reveal (the aha moment) --- */}
      {lesson.aha_moment && (
        <Section icon={<Sparkles size={16} />} title="Predict the output" accent="#7C3AED">
          <p className="font-sans text-sm font-medium text-[#0F172A] leading-relaxed mb-3">{lesson.aha_moment.prediction}</p>
          <pre className="m-0 p-3 rounded-md bg-[#0b1220] text-[#e2e8f0] font-mono text-[12.5px] leading-relaxed overflow-x-auto whitespace-pre min-w-0 mb-3">{lesson.aha_moment.code}</pre>
          {!ahaRevealed ? (
            <button
              onClick={() => setAhaRevealed(true)}
              className="flex items-center gap-2 text-sm font-semibold text-white bg-[#7C3AED] hover:bg-[#6D28D9] rounded px-3.5 py-2 transition-colors"
            >
              <Eye size={15} /> Reveal what actually happens
            </button>
          ) : (
            <div className="flex flex-col gap-3 animate-in fade-in duration-200">
              <div className="rounded-lg border border-[#B45309]/20 bg-[#B45309]/[0.04] p-3">
                <div className="font-sans text-[10px] font-bold uppercase tracking-wider text-[#B45309] mb-1">Most people guess</div>
                <pre className="m-0 font-mono text-[13px] text-[#0F172A] whitespace-pre-wrap">{lesson.aha_moment.common_guess}</pre>
              </div>
              <CodeTrace code={lesson.aha_moment.code} />
              <div className="rounded-lg border border-[#0F766E]/20 bg-[#0F766E]/[0.05] p-3">
                <div className="font-sans text-[10px] font-bold uppercase tracking-wider text-[#0F766E] mb-1">Why</div>
                <p className="font-sans text-sm text-[#0F172A] leading-relaxed">{lesson.aha_moment.why}</p>
              </div>
            </div>
          )}
        </Section>
      )}

      {/* --- §2 Why learn this --- */}
      {lesson.why_learning_this?.length > 0 && (
        <Section icon={<Lightbulb size={16} />} title="Why learn this">
          <ul className="flex flex-col gap-2">
            {lesson.why_learning_this.map((item, i) => (
              <li key={i} className="flex items-start gap-2.5">
                <span className="shrink-0 w-5 h-5 rounded-full bg-[#0891B2]/10 text-[#0891B2] font-mono text-[10px] font-bold flex items-center justify-center mt-0.5">
                  {i + 1}
                </span>
                <span className="font-sans text-sm text-[#0F172A] leading-relaxed">{item}</span>
              </li>
            ))}
          </ul>
        </Section>
      )}

      {/* --- §3 Watch it run — SQL (query result table) or Python (CodeTrace) --- */}
      {lesson.runtime === 'sql' && lesson.query_walkthrough ? (
        <Section icon={<Database size={16} />} title="Run the query" accent="#0891B2">
          {lesson.query_walkthrough.visualization === 'join-diagram' && lesson.query_walkthrough.join ? (
            <SqlJoinViz spec={lesson.query_walkthrough.join} focus={lesson.query_walkthrough.focus} />
          ) : (
            <SqlFlow
              query={lesson.query_walkthrough.query}
              setupSql={lesson.query_walkthrough.setup_sql}
              focus={lesson.query_walkthrough.focus}
              flowStages={lesson.query_walkthrough.flow_stages}
            />
          )}
        </Section>
      ) : lesson.code_walkthrough ? (
        <Section icon={<Code2 size={16} />} title="Watch it run">
          <CodeTrace code={lesson.code_walkthrough.code} focus={lesson.code_walkthrough.focus} />
        </Section>
      ) : null}

      {/* --- §4 Common mistakes --- */}
      {lesson.common_mistakes?.length > 0 && (
        <Section icon={<AlertTriangle size={16} />} title="Common mistakes">
          <div className="flex flex-col gap-3">
            {lesson.common_mistakes.map((m, i) => (
              <div key={i} className="rounded-lg border border-[#B91C1C]/15 bg-[#B91C1C]/[0.03] p-3.5">
                <div className="font-sans text-sm font-semibold text-[#B91C1C] mb-1.5 flex items-center gap-2">
                  <AlertTriangle size={13} /> {m.title}
                </div>
                <p className="font-sans text-sm text-[#475569] leading-relaxed">{m.explanation}</p>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* --- §5 Recall questions --- */}
      {lesson.recall_questions?.length > 0 && (
        <Section icon={<HelpCircle size={16} />} title="Recall questions">
          <div className="flex flex-col gap-3">
            {lesson.recall_questions.map((rq, i) => (
              <div key={i} className="rounded-lg border border-[rgba(15,23,42,0.1)] p-3.5">
                <div className="font-sans text-sm font-semibold text-[#0F172A] mb-2">{rq.q}</div>
                <button
                  onClick={() => toggleReveal(i)}
                  className="flex items-center gap-1.5 font-sans text-xs font-semibold text-[#0891B2] hover:text-[#0F172A] transition-colors"
                >
                  {revealed.has(i) ? <EyeOff size={13} /> : <Eye size={13} />}
                  {revealed.has(i) ? 'Hide answer' : 'Reveal answer'}
                </button>
                {revealed.has(i) && (
                  <div className="mt-2 pt-2 border-t border-[rgba(15,23,42,0.06)]">
                    <p className="font-sans text-sm text-[#0F766E] leading-relaxed">{rq.answer}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* --- §5b Understanding checks (mental-model probes) --- */}
      {lesson.understanding_checks?.length > 0 && (
        <Section icon={<Brain size={16} />} title="Check your understanding" accent="#7C3AED">
          <p className="font-sans text-xs text-[#64748B] mb-3">Predict before you reveal — a correct prediction proves you understand the model.</p>
          <div className="flex flex-col gap-3">
            {lesson.understanding_checks.map((c, i) => {
              const meta = CHECK_META[c.type] || CHECK_META['explain-behavior'];
              const open = checksRevealed.has(i);
              const snippet = c.code || c.query;
              const tracePython = (c.type === 'predict-output' || c.type === 'find-bug') && c.code;
              const runSqlCheck = c.type === 'predict-result' && c.query;
              return (
                <div key={i} className="rounded-lg border border-[rgba(15,23,42,0.1)] p-3.5">
                  <div className="flex items-center gap-1.5 mb-2">
                    <span
                      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-sans text-[10px] font-bold uppercase tracking-wider border"
                      style={{ color: meta.color, borderColor: meta.color + '40', background: meta.color + '0d' }}
                    >
                      {meta.icon} {meta.label}
                    </span>
                  </div>
                  <div className="font-sans text-sm font-semibold text-[#0F172A] mb-2 leading-relaxed">{c.question}</div>
                  {snippet && (
                    <pre className="m-0 mb-3 p-3 rounded-md bg-[#0b1220] text-[#e2e8f0] font-mono text-[12.5px] leading-relaxed overflow-x-auto whitespace-pre min-w-0">{snippet}</pre>
                  )}
                  <button
                    onClick={() => toggleCheck(i)}
                    className="flex items-center gap-1.5 font-sans text-xs font-semibold text-[#7C3AED] hover:text-[#0F172A] transition-colors"
                  >
                    {open ? <EyeOff size={13} /> : <Eye size={13} />}
                    {open ? 'Hide answer' : 'Reveal answer'}
                  </button>
                  {open && (
                    <div className="mt-3 flex flex-col gap-3 animate-in fade-in duration-200">
                      <div className="rounded-lg border border-[#0F766E]/20 bg-[#0F766E]/[0.05] p-3">
                        <div className="font-sans text-[10px] font-bold uppercase tracking-wider text-[#0F766E] mb-1">Answer</div>
                        <pre className="m-0 font-mono text-[13px] text-[#0F172A] whitespace-pre-wrap leading-relaxed">{c.answer}</pre>
                      </div>
                      <div className="rounded-lg border border-[#7C3AED]/20 bg-[#7C3AED]/[0.05] p-3">
                        <div className="font-sans text-[10px] font-bold uppercase tracking-wider text-[#7C3AED] mb-1">Why</div>
                        <p className="font-sans text-sm text-[#0F172A] leading-relaxed">{c.why}</p>
                      </div>
                      {tracePython && <CodeTrace code={c.code} />}
                      {runSqlCheck && <SqlResult query={c.query} autoRunLabel="Run to confirm" />}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </Section>
      )}

      {/* --- §6 Practice tasks --- */}
      {lesson.practice_tasks?.length > 0 && (
        <Section icon={<Code2 size={16} />} title="Practice">
          <div className="flex flex-col gap-4">
            {lesson.practice_tasks.map((task, i) => (
              <div key={i} className="rounded-lg border border-[rgba(15,23,42,0.1)] p-4">
                <div className="font-sans text-sm font-semibold text-[#0F172A] mb-2">{task.title}</div>
                <p className="font-sans text-sm text-[#475569] leading-relaxed mb-3">{task.prompt}</p>
                {task.starter_code && (
                  <details className="group mb-2">
                    <summary className="flex items-center gap-1.5 font-sans text-xs font-semibold text-[#0891B2] cursor-pointer hover:text-[#0F172A] transition-colors select-none">
                      <ChevronRight size={13} className="group-open:rotate-90 transition-transform" />
                      Starter code
                    </summary>
                    <pre className="mt-2 p-3 rounded-md bg-[#131b2e] text-[#e2e8f0] font-mono text-xs leading-relaxed overflow-x-auto whitespace-pre-wrap">{task.starter_code}</pre>
                  </details>
                )}
                {task.solution && (
                  <details className="group">
                    <summary className="flex items-center gap-1.5 font-sans text-xs font-semibold text-[#0F766E] cursor-pointer hover:text-[#0F172A] transition-colors select-none">
                      <ChevronRight size={13} className="group-open:rotate-90 transition-transform" />
                      Solution
                    </summary>
                    <pre className="mt-2 p-3 rounded-md bg-[#131b2e] text-[#e2e8f0] font-mono text-xs leading-relaxed overflow-x-auto whitespace-pre-wrap">{task.solution}</pre>
                  </details>
                )}
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* --- §7 Challenge --- */}
      {lesson.challenge && (
        <Section icon={<Trophy size={16} />} title="Challenge" accent="#B45309">
          <div className="rounded-lg border border-[#B45309]/20 bg-[#B45309]/[0.03] p-4">
            <div className="font-sans text-sm font-semibold text-[#B45309] mb-2">{lesson.challenge.title}</div>
            <p className="font-sans text-sm text-[#475569] leading-relaxed mb-3">{lesson.challenge.prompt}</p>
            {lesson.challenge.solution && (
              <details className="group">
                <summary className="flex items-center gap-1.5 font-sans text-xs font-semibold text-[#B45309] cursor-pointer hover:text-[#0F172A] transition-colors select-none">
                  <ChevronRight size={13} className="group-open:rotate-90 transition-transform" />
                  Solution
                </summary>
                <pre className="mt-2 p-3 rounded-md bg-[#131b2e] text-[#e2e8f0] font-mono text-xs leading-relaxed overflow-x-auto whitespace-pre-wrap">{lesson.challenge.solution}</pre>
              </details>
            )}
          </div>
        </Section>
      )}

      {/* --- §8 Sources --- */}
      {lesson.sources?.length > 0 && (
        <Section icon={<ExternalLink size={16} />} title="Sources">
          <ul className="flex flex-col gap-2">
            {lesson.sources.map((url, i) => (
              <li key={i}>
                <a
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 font-sans text-sm text-[#0891B2] hover:text-[#0F172A] font-medium transition-colors break-all"
                >
                  <ExternalLink size={13} className="shrink-0" />
                  {url}
                </a>
              </li>
            ))}
          </ul>
        </Section>
      )}
    </div>
  );
}

/** Distil a lesson into one ~500-char "key memory" for the review card, by kind. */
function deriveKeyMemory(lesson) {
  if (lesson.mental_model) {
    const parts = [lesson.mental_model.intuition, lesson.formula?.statement];
    return parts.filter(Boolean).join(' — ').slice(0, 500);
  }
  if (lesson.aha_moment?.why) return lesson.aha_moment.why.slice(0, 500);
  if (lesson.overview?.what) return lesson.overview.what.split('\n')[0].slice(0, 500);
  return lesson.title.slice(0, 500);
}

/** "Add to reviews" — turns a lesson into an FSRS card (the content→review bridge).
 *  Idempotent server-side (one card per node), so re-taps are safe. */
function AddToReviews({ lesson, nodeId }) {
  const { requireAuth } = useAuth();
  const [state, setState] = useState('idle'); // idle | adding | added | error
  const add = () => requireAuth(async () => {
    setState('adding');
    try {
      await apiFetch('/api/activities/', {
        method: 'POST',
        body: JSON.stringify({
          topic: lesson.title,
          key_memory: deriveKeyMemory(lesson),
          difficulty: 3,
          needed_hint: false,
          source_type: 'lesson',
          node_id: nodeId,
        }),
      });
      setState('added');
    } catch (e) {
      setState('error');
    }
  });
  if (state === 'added') {
    return (
      <span className="shrink-0 inline-flex items-center gap-1.5 rounded-lg bg-[#0F766E]/10 text-[#0F766E] font-sans text-sm font-semibold px-3 py-1.5">
        <Check size={15} /> In your reviews
      </span>
    );
  }
  return (
    <button onClick={add} disabled={state === 'adding'}
      className="shrink-0 inline-flex items-center gap-1.5 rounded-lg bg-[#0891B2] hover:bg-[#0e7490] text-white font-sans text-sm font-semibold px-3 py-1.5 transition-colors disabled:opacity-60">
      <Plus size={15} /> {state === 'adding' ? 'Adding…' : state === 'error' ? 'Retry' : 'Add to reviews'}
    </button>
  );
}

/** Process animation (theory, optional). Renders {actors, steps} as a row of boxes
 *  with a flowing arrow stepping from→to, auto-advancing. Pure SVG — no dependency.
 *  The per-step `term` chip IS the "map the animation to CS terminology" layer. */
function ProcessAnimation({ animation }) {
  const { actors = [], steps = [] } = animation || {};
  const [step, setStep] = useState(0);
  const [playing, setPlaying] = useState(true);

  useEffect(() => {
    if (!playing || step >= steps.length - 1) return;
    const t = setTimeout(() => setStep((s) => s + 1), 1700);
    return () => clearTimeout(t);
  }, [playing, step, steps.length]);

  if (!actors.length || !steps.length) return null;

  const W = 540, pad = 64;
  const gap = actors.length > 1 ? (W - 2 * pad) / (actors.length - 1) : 0;
  const xOf = (i) => pad + i * gap;
  const y = 44;
  const idx = (id) => actors.findIndex((a) => a.id === id);
  const cur = steps[step] || {};
  const fI = idx(cur.from), tI = idx(cur.to);
  const active = new Set([cur.from, cur.to]);
  const done = step >= steps.length - 1;

  return (
    <div className="rounded-lg border border-[rgba(15,23,42,0.12)] bg-white overflow-hidden">
      <style>{`@keyframes pa-flow{to{stroke-dashoffset:-20}}`}</style>
      <svg viewBox={`0 0 ${W} 88`} className="w-full">
        {fI >= 0 && tI >= 0 && (
          <line x1={xOf(fI)} y1={y} x2={xOf(tI)} y2={y} stroke="#0891B2" strokeWidth="2.5"
            strokeDasharray="6 4" markerEnd="url(#pa-arr)"
            style={{ animation: 'pa-flow 0.7s linear infinite' }} />
        )}
        {actors.map((a, i) => {
          const on = active.has(a.id);
          return (
            <g key={a.id}>
              <rect x={xOf(i) - 36} y={y - 15} width="72" height="30" rx="7"
                fill={on ? '#0891B2' : '#f1f5f9'} stroke={on ? '#0891B2' : '#cbd5e1'} strokeWidth="1.5" />
              <text x={xOf(i)} y={y + 4} textAnchor="middle" fontSize="10.5"
                fontFamily="ui-sans-serif, system-ui" fontWeight="600" fill={on ? '#fff' : '#475569'}>{a.label}</text>
            </g>
          );
        })}
        <defs><marker id="pa-arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
          <path d="M0,0 L7,3 L0,6 Z" fill="#0891B2" /></marker></defs>
      </svg>
      <div className="flex items-center gap-2 px-3 py-2.5 border-t border-[rgba(15,23,42,0.06)] bg-[#f9f9f6]">
        <span className="font-mono text-[11px] text-[#64748B] shrink-0">{step + 1}/{steps.length}</span>
        <span className="font-sans text-[13px] text-[#0F172A] flex-1 leading-snug">
          <strong className="font-semibold">{actors[fI]?.label}</strong> {cur.label} <strong className="font-semibold">{actors[tI]?.label}</strong>
          {cur.term && <span className="ml-2 inline-block rounded bg-[#0891B2]/10 text-[#0891B2] font-medium text-[11px] px-1.5 py-0.5">{cur.term}</span>}
        </span>
        {done
          ? <button onClick={() => { setStep(0); setPlaying(true); }} className="shrink-0 text-[12px] font-semibold text-[#0891B2] hover:underline">↻ Replay</button>
          : <button onClick={() => setPlaying((p) => !p)} className="shrink-0 text-[12px] font-semibold text-[#0891B2] hover:underline">{playing ? 'Pause' : 'Play'}</button>}
      </div>
    </div>
  );
}

/** Renders a content string as structured blocks: paragraphs separated by blank
 *  lines, with indented blocks rendered as real code. Overviews embed code examples
 *  this way, and a plain <p> would collapse the newlines into one run-on blob. */
function RichText({ text, tone = 'ink' }) {
  const color = tone === 'muted' ? 'text-[#475569]' : 'text-[#0F172A]';
  const blocks = String(text || '').split(/\n[ \t]*\n/).filter((b) => b.trim() !== '');
  return (
    <div className="flex flex-col gap-3">
      {blocks.map((block, i) => {
        const lines = block.replace(/\n+$/, '').split('\n');
        const isCode = lines.some((l) => l.trim()) && lines.every((l) => l.trim() === '' || /^[ \t]/.test(l));
        if (isCode) {
          const indents = lines.filter((l) => l.trim()).map((l) => l.match(/^[ \t]*/)[0].length);
          const min = indents.length ? Math.min(...indents) : 0;
          const code = lines.map((l) => l.slice(min)).join('\n').trim();
          return (
            <pre key={i} className="m-0 p-3 rounded-md bg-[#0b1220] text-[#e2e8f0] font-mono text-[12.5px] leading-relaxed overflow-x-auto whitespace-pre min-w-0">{code}</pre>
          );
        }
        return (
          <p key={i} className={`font-sans text-sm ${color} leading-relaxed`}>{block.trim()}</p>
        );
      })}
    </div>
  );
}

/** Thin, intuition-first lesson body for aptitude (quant) + reasoning (logical/verbal).
 *  Field order mirrors the teaching order in PROMPT-aptitude.md / PROMPT-reasoning.md. */
function AptitudeReasoningBody({ lesson, revealed, toggleReveal, ahaRevealed, setAhaRevealed, oaRevealed, toggleOa }) {
  const mm = lesson.mental_model || {};
  const pd = lesson.pattern_discovery;
  const we = lesson.worked_example;
  return (
    <>
      {/* Hook (optional) */}
      {lesson.hook?.scenario && (
        <Section icon={<Lightbulb size={16} />} title="The setup" accent="#B45309">
          <p className="font-sans text-sm text-[#0F172A] leading-relaxed">{lesson.hook.scenario}</p>
          {lesson.hook.question && (
            <p className="font-sans text-sm font-semibold text-[#B45309] leading-relaxed mt-2">{lesson.hook.question}</p>
          )}
        </Section>
      )}

      {/* Mental model (required) — the intuition anchor */}
      <Section icon={<Brain size={16} />} title="Mental model" accent="#7C3AED">
        <p className="font-sans text-base font-semibold text-[#0F172A] leading-snug">{mm.intuition}</p>
        {mm.description && <div className="mt-2"><RichText text={mm.description} tone="muted" /></div>}
      </Section>

      {/* Process animation (theory, optional) — watch the process before reading it */}
      {lesson.animation && (
        <Section icon={<Sparkles size={16} />} title="Watch it work" accent="#0891B2">
          <ProcessAnimation animation={lesson.animation} />
        </Section>
      )}

      {/* Explanation (theory, required) — the concept, plainly */}
      {lesson.explanation && (
        <Section icon={<BookOpen size={16} />} title="The concept" accent="#0891B2">
          <RichText text={lesson.explanation} />
        </Section>
      )}

      {/* Key points (theory, optional) — the component breakdown */}
      {Array.isArray(lesson.key_points) && lesson.key_points.length > 0 && (
        <Section icon={<Target size={16} />} title="Key points" accent="#0F766E">
          <div className="flex flex-col gap-2.5">
            {lesson.key_points.map((p, i) => (
              <div key={i} className="flex items-start gap-2.5">
                <span className="shrink-0 w-5 h-5 rounded-full bg-[#0F766E]/10 text-[#0F766E] font-mono text-[10px] font-bold flex items-center justify-center mt-0.5">{i + 1}</span>
                <span className="font-sans text-sm text-[#0F172A] leading-relaxed"><strong className="font-semibold">{p.title}:</strong> {p.detail}</span>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Pattern discovery (aptitude, optional) — discover the rule, THEN reveal it */}
      {pd && (
        <Section icon={<Sparkles size={16} />} title="Spot the pattern" accent="#0891B2">
          {pd.setup && <p className="font-sans text-sm text-[#475569] leading-relaxed mb-3">{pd.setup}</p>}
          {Array.isArray(pd.cases) && (
            <div className="flex flex-col gap-1.5 mb-3">
              {pd.cases.map((c, i) => (
                <div key={i} className="font-mono text-[12.5px] text-[#0F172A] bg-[#0891B2]/[0.06] rounded px-3 py-1.5">{c}</div>
              ))}
            </div>
          )}
          {pd.prompt && <p className="font-sans text-sm font-semibold text-[#0F172A] leading-relaxed mb-3">{pd.prompt}</p>}
          {!ahaRevealed ? (
            <button onClick={() => setAhaRevealed(true)} className="flex items-center gap-2 text-sm font-semibold text-white bg-[#0891B2] hover:bg-[#0e7490] rounded px-3.5 py-2 transition-colors">
              <Eye size={15} /> Reveal the rule
            </button>
          ) : (
            <div className="rounded-lg border border-[#0F766E]/20 bg-[#0F766E]/[0.05] p-3 animate-in fade-in duration-200">
              <div className="font-sans text-[10px] font-bold uppercase tracking-wider text-[#0F766E] mb-1">The rule</div>
              <p className="font-sans text-sm text-[#0F172A] leading-relaxed">{pd.rule}</p>
            </div>
          )}
        </Section>
      )}

      {/* Method (reasoning, required) — the transferable procedure */}
      {Array.isArray(lesson.method) && lesson.method.length > 0 && (
        <Section icon={<Target size={16} />} title="The method" accent="#0891B2">
          <ol className="flex flex-col gap-2">
            {lesson.method.map((step, i) => (
              <li key={i} className="flex items-start gap-2.5">
                <span className="shrink-0 w-5 h-5 rounded-full bg-[#0891B2]/10 text-[#0891B2] font-mono text-[10px] font-bold flex items-center justify-center mt-0.5">{i + 1}</span>
                <span className="font-sans text-sm text-[#0F172A] leading-relaxed">{step}</span>
              </li>
            ))}
          </ol>
        </Section>
      )}

      {/* Formula (aptitude, required) */}
      {lesson.formula?.statement && (
        <Section icon={<Target size={16} />} title="The rule" accent="#0F766E">
          <p className="font-mono text-[13px] text-[#0F172A] bg-[#0F766E]/[0.06] rounded px-3 py-2 leading-relaxed">{lesson.formula.statement}</p>
          {lesson.formula.explain && <p className="font-sans text-sm text-[#475569] leading-relaxed mt-2">{lesson.formula.explain}</p>}
        </Section>
      )}

      {/* Worked example (reasoning, required) — method applied; reveal the solution */}
      {we?.problem && (
        <Section icon={<Sparkles size={16} />} title="Worked example" accent="#7C3AED">
          <p className="font-sans text-sm font-medium text-[#0F172A] leading-relaxed mb-3">{we.problem}</p>
          {!ahaRevealed ? (
            <button onClick={() => setAhaRevealed(true)} className="flex items-center gap-2 text-sm font-semibold text-white bg-[#7C3AED] hover:bg-[#6D28D9] rounded px-3.5 py-2 transition-colors">
              <Eye size={15} /> Reveal the solution
            </button>
          ) : (
            <div className="animate-in fade-in duration-200">
              {Array.isArray(we.steps) && (
                <ol className="flex flex-col gap-2 mb-3">
                  {we.steps.map((step, i) => (
                    <li key={i} className="flex items-start gap-2.5">
                      <span className="shrink-0 w-5 h-5 rounded-full bg-[#7C3AED]/10 text-[#7C3AED] font-mono text-[10px] font-bold flex items-center justify-center mt-0.5">{i + 1}</span>
                      <span className="font-sans text-sm text-[#0F172A] leading-relaxed">{step}</span>
                    </li>
                  ))}
                </ol>
              )}
              <div className="rounded-lg border border-[#0F766E]/20 bg-[#0F766E]/[0.05] p-3">
                <div className="font-sans text-[10px] font-bold uppercase tracking-wider text-[#0F766E] mb-1">Answer</div>
                <p className="font-sans text-sm font-semibold text-[#0F172A] leading-relaxed">{we.answer}</p>
              </div>
            </div>
          )}
        </Section>
      )}

      {/* Shortcuts (optional) */}
      {Array.isArray(lesson.shortcuts) && lesson.shortcuts.length > 0 && (
        <Section icon={<Zap size={16} />} title="Fast tricks" accent="#B45309">
          <div className="flex flex-col gap-3">
            {lesson.shortcuts.map((s, i) => (
              <div key={i} className="rounded-lg border border-[#B45309]/20 bg-[#B45309]/[0.03] p-3">
                <div className="font-sans text-sm font-semibold text-[#B45309] mb-1">{s.title}</div>
                <p className="font-sans text-sm text-[#0F172A] leading-relaxed">{s.trick}</p>
                {s.example && <p className="font-mono text-[12px] text-[#475569] mt-1.5">{s.example}</p>}
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Common mistakes (required) */}
      {Array.isArray(lesson.common_mistakes) && lesson.common_mistakes.length > 0 && (
        <Section icon={<AlertTriangle size={16} />} title="Common mistakes" accent="#B91C1C">
          <div className="flex flex-col gap-3">
            {lesson.common_mistakes.map((m, i) => (
              <div key={i} className="rounded-lg border border-[#B91C1C]/15 bg-[#B91C1C]/[0.03] p-3">
                <div className="font-sans text-sm font-semibold text-[#B91C1C] mb-1">{m.title}</div>
                <p className="font-sans text-sm text-[#0F172A] leading-relaxed">{m.explanation}</p>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Recall (required) — predict-before-reveal */}
      {Array.isArray(lesson.recall_questions) && lesson.recall_questions.length > 0 && (
        <Section icon={<HelpCircle size={16} />} title="Active recall" accent="#0891B2">
          <div className="flex flex-col gap-2.5">
            {lesson.recall_questions.map((rq, i) => (
              <div key={i} className="rounded-lg border border-[rgba(15,23,42,0.1)] p-3">
                <p className="font-sans text-sm font-medium text-[#0F172A] leading-relaxed">{rq.q}</p>
                {revealed.has(i) ? (
                  <p className="font-sans text-sm text-[#0F766E] leading-relaxed mt-2">{rq.answer}</p>
                ) : (
                  <button onClick={() => toggleReveal(i)} className="flex items-center gap-1.5 font-sans text-xs font-semibold text-[#0891B2] hover:text-[#0F172A] mt-2 transition-colors">
                    <Eye size={13} /> Show answer
                  </button>
                )}
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* OA / interview questions (required) — reveal the 10-second approach */}
      {Array.isArray(lesson.oa_questions) && lesson.oa_questions.length > 0 && (
        <Section icon={<Trophy size={16} />} title="Interview / OA questions" accent="#B45309">
          <div className="flex flex-col gap-3">
            {lesson.oa_questions.map((q, i) => (
              <div key={i} className="rounded-lg border border-[rgba(15,23,42,0.1)] p-3">
                <div className="flex items-start justify-between gap-2">
                  <p className="font-sans text-sm font-medium text-[#0F172A] leading-relaxed">{q.question}</p>
                  {q.company && <span className="shrink-0 px-2 py-0.5 rounded-full bg-[#B45309]/10 font-sans text-[10px] font-semibold text-[#B45309]">{q.company}</span>}
                </div>
                {oaRevealed.has(i) ? (
                  <div className="mt-2">
                    <p className="font-sans text-sm font-semibold text-[#0F766E] leading-relaxed">{q.answer}</p>
                    {q.approach && <p className="font-sans text-sm text-[#475569] leading-relaxed mt-1">{q.approach}</p>}
                  </div>
                ) : (
                  <button onClick={() => toggleOa(i)} className="flex items-center gap-1.5 font-sans text-xs font-semibold text-[#B45309] hover:text-[#0F172A] mt-2 transition-colors">
                    <Eye size={13} /> Show answer & approach
                  </button>
                )}
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Sources */}
      {lesson.sources?.length > 0 && (
        <Section icon={<ExternalLink size={16} />} title="Sources">
          <ul className="flex flex-col gap-2">
            {lesson.sources.map((url, i) => (
              <li key={i}>
                <a href={url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 font-sans text-sm text-[#0891B2] hover:text-[#0F172A] font-medium transition-colors break-all">
                  <ExternalLink size={13} className="shrink-0" /> {url}
                </a>
              </li>
            ))}
          </ul>
        </Section>
      )}
    </>
  );
}

/** Consistent section card with icon + title. */
function Section({ icon, title, accent, children }) {
  const color = accent || '#0891B2';
  return (
    <section className="glass-card mb-4 p-5">
      <div className="flex items-center gap-2 mb-3 pb-2 border-b border-[rgba(15,23,42,0.06)]">
        <span style={{ color }}>{icon}</span>
        <h2 className="font-sans text-sm font-bold text-[#0F172A] uppercase tracking-wider">{title}</h2>
      </div>
      {children}
    </section>
  );
}
