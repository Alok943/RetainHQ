import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, BookOpen, Clock, BarChart2, Zap, AlertTriangle, HelpCircle, Code2, Trophy, ExternalLink, ChevronDown, ChevronRight, Eye, EyeOff, Lightbulb, Target, Sparkles } from 'lucide-react';
import { apiFetch } from './lib/api';
import { CONTENT_KEY_BY_TITLE } from './lib/contentRoadmaps';
import CodeTrace from './CodeTrace';

const TIER_LABEL = { tier1: 'Tier 1', tier2: 'Tier 2', tier3: 'Tier 3' };
const TIER_COLOR = { tier1: '#0F766E', tier2: '#B45309', tier3: '#B91C1C' };
const DIFF_COLOR = { easy: '#0F766E', medium: '#B45309', hard: '#B91C1C' };

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

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      setAhaRevealed(false);
      try {
        // Get the content key — prefer router state if passed, else fetch roadmap meta
        let contentKey = location.state?.contentKey;
        if (!contentKey) {
          const meta = await apiFetch(`/api/roadmaps/${id}`, { optionalAuth: true });
          contentKey = CONTENT_KEY_BY_TITLE[meta.title];
        }
        if (!contentKey) throw new Error('no-content-key');

        const res = await fetch(`/content/roadmaps/${contentKey}/${slug}.json`);
        if (!res.ok) throw new Error('not-found');
        const data = await res.json();
        if (!cancelled) setLesson(data);
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

  return (
    <div className="max-w-3xl mx-auto w-full px-4 md:px-8 py-6 pb-24">
      {/* --- Header --- */}
      <button
        onClick={() => navigate(`/roadmaps/${id}`)}
        className="flex items-center gap-2 text-[#64748B] hover:text-[#0F172A] font-sans text-sm font-medium mb-4 transition-colors"
      >
        <ArrowLeft size={16} /> Back to roadmap
      </button>

      <div className="mb-6">
        <h1 className="font-sans text-2xl md:text-3xl font-semibold text-[#0F172A] leading-tight mb-3">
          {lesson.title}
        </h1>
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

      {/* --- §3 Watch it run (CodeTrace) --- */}
      {lesson.code_walkthrough && (
        <Section icon={<Code2 size={16} />} title="Watch it run">
          <CodeTrace code={lesson.code_walkthrough.code} focus={lesson.code_walkthrough.focus} />
        </Section>
      )}

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
