import React, { useState, useEffect } from 'react';
import { ArrowLeft, CheckCircle2, AlertTriangle, Brain, Sparkles, Lightbulb } from 'lucide-react';
import { apiFetch } from './lib/api';
import { useAuth } from './lib/AuthContext';
import { track, EVENTS } from './lib/analytics';
import Hint from './Hint';
import { CONTENT_KEY_BY_TITLE } from './lib/contentRoadmaps';

const slugifyTitle = (t) => (t || '').toLowerCase().replace(/&/g, 'and').replace(/\//g, ' ').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
function lessonSlugForNode(slugByTitle, title) {
  if (slugByTitle[title]) return slugByTitle[title];
  const s = slugifyTitle(title);
  return Object.values(slugByTitle).includes(s) ? s : null;
}

// "Why this card today" — one honest sentence so the schedule never feels like a
// black box (the #1 trust-killer for adaptive systems). Derived from data already
// in the due payload; no extra fetch.
function whyDueLine(activity) {
  if (!activity?.last_reviewed_at) {
    return 'First review — new memories fade fastest in the first days, so we check early.';
  }
  const days = Math.max(1, Math.round((Date.now() - new Date(activity.last_reviewed_at)) / 86400000));
  return `Last recalled ${days} day${days === 1 ? '' : 's'} ago — due now so it sticks before it fades.`;
}

// Each post-reveal choice carries BOTH signals at once:
//   recalled = objective (did they reconstruct it?)   rating = subjective (how hard it felt)
const OUTCOMES = [
  { key: 'missed', label: 'Missed it', desc: "Couldn't recall it", rating: 'hard',   recalled: false, color: '#334155', border: 'rgba(15,23,42,0.2)' },
  { key: 'hard',   label: 'Hard',      desc: "Took serious effort", rating: 'hard',   recalled: true,  color: '#B45309' },
  { key: 'good',   label: 'Good',      desc: "Recalled with minor effort", rating: 'medium', recalled: true,  color: '#0891B2' },
  { key: 'easy',   label: 'Easy',      desc: "Instantly knew it", rating: 'easy',   recalled: true,  color: '#0F766E' },
];

// Map the AI grader's verdict to a suggested outcome chip. Advisory only —
// the user still clicks to confirm, so a wrong grade never auto-submits.
// The AI can judge correctness (recalled vs not), but NOT how hard it felt —
// that's the user's subjective call. So we only suggest the recalled/missed axis
// and default any successful recall to "Good"; the user nudges to Hard/Easy by feel.
function suggestedKeyFromAi(ai) {
  if (!ai) return null;
  if (!ai.recalled || ai.verdict === 'incorrect') return 'missed';
  return 'good'; // correct or partial that was still recalled
}

function Review({ onBack }) {
  const [reviews, setReviews] = useState([]);
  const [index, setIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { session } = useAuth();

  // Per-card state
  const [revealed, setRevealed] = useState(false);
  const [answer, setAnswer] = useState('');
  const [skipped, setSkipped] = useState(false); // user committed "I don't know"
  const [submitting, setSubmitting] = useState(false);
  const [aiResult, setAiResult] = useState(null); // {verdict, recalled, feedback} | null
  const [grading, setGrading] = useState(false);

  // Question mode (PROTOTYPE, gated server-side on GRADER_ENABLED). Populated only
  // when /questions returns; otherwise we stay on the single free-recall box.
  const [questions, setQuestions] = useState(null);    // string[] | null
  const [qAnswers, setQAnswers] = useState([]);        // parallel to questions
  const [canonicalAnswers, setCanonicalAnswers] = useState([]); // parallel to questions, for grounded grading
  const [qResult, setQResult] = useState(null);        // grade-questions response | null
  const [loadingQuestions, setLoadingQuestions] = useState(false);
  const [questionModeOff, setQuestionModeOff] = useState(false); // session: grader disabled

  useEffect(() => {
    if (!session) {
      setLoading(false);
      return;
    }
    apiFetch('/api/reviews/due')
      .then((data) => {
        setReviews(data);
        if (Array.isArray(data) && data.length > 0) {
          track(EVENTS.REVIEW_STARTED, { due_count: data.length });
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const current = reviews[index] ?? null;
  const total = reviews.length;
  const questionMode = Array.isArray(questions) && questions.length > 0;
  const committed = questionMode
    ? (skipped || qAnswers.some((a) => a.trim().length > 0))
    : (answer.trim().length > 0 || skipped);

  const resetCard = () => {
    setRevealed(false);
    setAnswer('');
    setSkipped(false);
    setAiResult(null);
    setGrading(false);
    setQuestions(null);
    setQAnswers([]);
    setCanonicalAnswers([]);
    setQResult(null);
    setLoadingQuestions(false);
  };

  // Question mode: when a new card surfaces, try to fetch grounded questions.
  // Gated server-side on GRADER_ENABLED — a "disabled" 404 means it's off, so we
  // stop trying for the rest of the session (the live free-recall path stays
  // pristine after the first card). Any other failure falls back for this card.
  useEffect(() => {
    if (!current || questionModeOff || revealed) return;
    let cancelled = false;
    setLoadingQuestions(true);

    const loadQuestions = async () => {
      try {
        if (current.activity.source_type === 'lesson' && current.roadmap_slug && current.node_title) {
          const contentKey = current.roadmap_slug || CONTENT_KEY_BY_TITLE[current.roadmap_slug];
          const manifestRes = await fetch('/content/manifest.json');
          if (!manifestRes.ok) throw new Error('manifest fail');
          const manifest = await manifestRes.json();
          const slugByTitle = manifest[contentKey] || {};
          const lessonSlug = lessonSlugForNode(slugByTitle, current.node_title);
          
          if (lessonSlug) {
            const lessonRes = await fetch(`/content/roadmaps/${contentKey}/${lessonSlug}.json`);
            if (!lessonRes.ok) throw new Error('lesson fail');
            const lesson = await lessonRes.json();
            
            if (lesson.recall_questions) {
               // Use tier1 if available, otherwise fallback
               const questionsPool = lesson.recall_questions.tier1 || lesson.recall_questions;
               const qs = Array.isArray(questionsPool) ? questionsPool : [];
               
               if (qs.length > 0) {
                 if (cancelled) return;
                 // Slice to 3 max to match LLM output length
                 const limited = qs.slice(0, 3);
                 setQuestions(limited.map(x => x.q));
                 setQAnswers(limited.map(() => ''));
                 // Lesson JSON uses {q, answer, tier} across all kinds ('a' kept as a legacy fallback).
                 setCanonicalAnswers(limited.map(x => x.answer ?? x.a ?? null));
                 setLoadingQuestions(false);
                 return;
               }
            }
          }
        }
        
        // Fallback to LLM questions if not a lesson or fetching failed
        const res = await apiFetch(`/api/reviews/${current.id}/questions`, { method: 'POST' });
        if (cancelled) return;
        const qs = res?.questions ?? [];
        if (qs.length) {
          setQuestions(qs);
          setQAnswers(qs.map(() => ''));
          setCanonicalAnswers([]); // reset
        }
      } catch (err) {
        if (cancelled) return;
        if (typeof err?.message === 'string' && err.message.includes('disabled')) {
          setQuestionModeOff(true);
        }
      } finally {
        if (!cancelled) setLoadingQuestions(false);
      }
    };
    
    loadQuestions();
    return () => { cancelled = true; };
  }, [current?.id]);

  // "I don't know" is a committed answer — reveal in one click, don't make the
  // failure path cost an extra tap.
  const handleSkip = () => {
    setSkipped(true);
    setAnswer('');
    setRevealed(true);
  };

  const handleReveal = () => {
    if (!committed) return;
    setRevealed(true);

    // Question mode: grade the whole answer set in one call. Advisory only.
    if (questionMode) {
      const pairs = questions.map((q, i) => ({ 
        question: q, 
        answer: (qAnswers[i] || '').trim(),
        reference_answer: canonicalAnswers[i] || null
      }));
      if (pairs.some((p) => p.answer) && current) {
        setGrading(true);
        apiFetch(`/api/reviews/${current.id}/grade-questions`, {
          method: 'POST',
          body: JSON.stringify({ answers: pairs }),
        })
          .then((res) => setQResult(res))
          .catch(() => setQResult(null))
          .finally(() => setGrading(false));
      }
      return;
    }

    // Free recall: non-blocking AI grade of the attempt. Advisory only — any
    // failure (grader disabled / unavailable) silently falls back to manual rating.
    if (answer.trim() && current) {
      setGrading(true);
      apiFetch(`/api/reviews/${current.id}/grade`, {
        method: 'POST',
        body: JSON.stringify({ answer: answer.trim() }),
      })
        .then((res) => setAiResult(res))
        .catch(() => setAiResult(null))
        .finally(() => setGrading(false));
    }
  };

  const suggestedKey = questionMode
    ? (qResult ? (qResult.recalled ? 'good' : 'missed') : null)
    : suggestedKeyFromAi(aiResult);

  // Adjacent topics the LLM suggests learning next — surfaced (highlighted) after
  // reveal in either mode. Purely a suggestion; never affects the grade.
  const relatedSubtopics =
    (questionMode ? qResult?.related_subtopics : aiResult?.related_subtopics) ?? [];

  const handleOutcome = async (outcome) => {
    if (!current || submitting) return;
    setSubmitting(true);
    try {
      await apiFetch(`/api/reviews/${current.id}/complete`, {
        method: 'POST',
        body: JSON.stringify({ rating: outcome.rating, recalled: outcome.recalled }),
      });
      track(EVENTS.REVIEW_COMPLETED, {
        outcome: outcome.key,
        rating: outcome.rating,
        recalled: outcome.recalled,
        mode: questionMode ? 'question' : 'free',
        ai_assisted: !!aiResult || questionMode,
      });
      if (index < total - 1) {
        setIndex((i) => i + 1);
        resetCard();
      } else {
        setIndex((i) => i + 1); // pushes past the end → done screen
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  // Flashcard keyboard shortcuts: Ctrl/Cmd+Enter reveals; after reveal, 1–4 pick
  // Missed / Hard / Good / Easy. 1–4 are safe post-reveal — no text input is
  // focused once the answer box is gone.
  useEffect(() => {
    const onKeyDown = (e) => {
      if (!current) return;
      if (!revealed) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter' && committed) {
          e.preventDefault();
          handleReveal();
        }
        return;
      }
      const n = parseInt(e.key, 10);
      if (n >= 1 && n <= OUTCOMES.length && !submitting) {
        e.preventDefault();
        handleOutcome(OUTCOMES[n - 1]);
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  });

  /* ---------- non-card states ---------- */

  if (loading) {
    return (
      <div className="flex flex-col h-full w-full max-w-3xl mx-auto p-4 md:p-8 bg-[#f9f9f6]">
        <header className="flex flex-col gap-4 mb-8">
          <div className="flex items-center justify-between">
            <div className="skeleton h-4 w-36" />
            <div className="skeleton h-3.5 w-10" />
          </div>
          <div className="skeleton h-3 w-48" />
          <div className="skeleton h-1 w-full rounded-full" />
        </header>
        <main className="flex-1 flex flex-col justify-center gap-8 mb-8">
          <div className="kinetic-card min-h-[300px] flex flex-col px-6 md:px-10 py-10 relative shadow-sm border-[rgba(15,23,42,0.12)]">
            <div className="skeleton h-3 w-16 mb-4" />
            <div className="skeleton h-8 w-2/3 mb-6" />
            <div className="skeleton h-3 w-full mb-2" />
            <div className="skeleton h-24 w-full rounded-lg mt-2" />
          </div>
        </main>
        <footer className="w-full flex justify-center pb-8">
          <div className="w-full flex flex-col sm:flex-row gap-3 justify-center">
            <div className="skeleton h-12 flex-1 max-w-[180px] rounded-lg" />
            <div className="skeleton h-12 flex-1 md:max-w-[260px] rounded-lg" />
          </div>
        </footer>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4 p-8 text-center">
        <AlertTriangle size={28} className="text-[#ba1a1a]" />
        <p className="font-sans text-sm text-[#ba1a1a]">Couldn't load reviews: {error}</p>
        <button onClick={onBack} className="kinetic-btn bg-white border border-[#0F172A] text-[#0F172A] px-5 py-2 text-sm">
          Back to Dashboard
        </button>
      </div>
    );
  }

  // Empty queue, or finished the whole queue
  if (total === 0 || index >= total) {
    const done = total > 0;
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4 p-8 text-center animate-in fade-in duration-300">
        <CheckCircle2 size={32} className="text-[#0F766E]" />
        <h2 className="font-sans text-xl font-semibold text-[#0F172A]">
          {done ? 'Reviews complete' : "You're all caught up"}
        </h2>
        <p className="font-sans text-sm text-[#64748B] max-w-xs">
          {done
            ? `You worked through ${total} review${total > 1 ? 's' : ''}. Nice — that's what builds long-term memory.`
            : 'No reviews are due right now. Log a new activity to keep the loop going.'}
        </p>
        {done && (
          <div className="max-w-sm w-full">
            <Hint id="review_loop_scheduled">
              Each one is rescheduled based on how you did — the next pass lands right
              before you'd forget. Come back when Home shows reviews due; that's the
              whole loop.
            </Hint>
          </div>
        )}
        <button onClick={onBack} className="kinetic-btn kinetic-accent-gradient px-6 py-2.5 text-sm mt-2">
          Back to Dashboard
        </button>
      </div>
    );
  }

  const activity = current.activity;

  return (
    <div className="flex flex-col h-full w-full max-w-3xl mx-auto p-4 md:p-8 bg-[#f9f9f6]">

      {/* Header & Progress */}
      <header className="flex flex-col gap-4 mb-8">
        <div className="flex items-center justify-between">
          <button
            onClick={onBack}
            className="flex items-center gap-2 text-[#64748B] hover:text-[#0F172A] font-sans text-sm font-medium transition-colors"
          >
            <ArrowLeft size={16} /> Back to Dashboard
          </button>
          <div className="font-mono text-xs font-semibold text-[#0F172A]">
            {index + 1} / {total}
          </div>
        </div>
        {/* Frame the queue as progress underway, not a debt count (Zeigarnik). */}
        <p className="font-sans text-xs text-[#64748B]">
          Today's review · {index} of {total} done · ~{Math.max(1, Math.round((total - index) * 0.7))} min
        </p>
        <div className="w-full h-1 bg-[rgba(15,23,42,0.08)] rounded-full overflow-hidden">
          {/* Counts the revealed card as progress so the bar reaches 100% on the
              last card instead of stalling just short of full. */}
          <div
            className="h-full bg-[#0891B2] transition-all duration-300"
            style={{ width: `${((index + (revealed ? 1 : 0)) / total) * 100}%` }}
          />
        </div>
      </header>

      {/* Card */}
      <main className="flex-1 flex flex-col justify-center gap-8 mb-8">
        <div className="kinetic-card min-h-[300px] flex flex-col px-6 md:px-10 py-10 relative shadow-sm border-[rgba(15,23,42,0.12)]">
          <div className="font-sans text-[11px] font-bold text-[#0891B2] uppercase tracking-widest mb-4 flex items-center gap-1.5">
            <Brain size={13} /> Recall
          </div>

          {/* Cue = the topic */}
          <h2 className="font-sans text-2xl md:text-3xl font-semibold text-[#0F172A] leading-tight">
            {activity.topic}
          </h2>

          {/* Why this card today — the schedule must never feel like a black box. */}
          <p className="font-sans text-xs text-[#64748B] mt-2">{whyDueLine(activity)}</p>

          {!revealed ? (
            /* ---------- RECALL GATE: commit before reveal ---------- */
            <div className="mt-6 flex flex-col gap-4">
              <Hint id="review_recall_gate">
                Pulling it from memory is the workout — write what you remember before
                you peek, even if it's rough. That effort is what makes it stick.
              </Hint>

              {questionMode ? (
                /* Question mode: answer each grounded question from memory. */
                <div className="flex flex-col gap-5">
                  {questions.map((q, i) => (
                    <div key={i} className="flex flex-col gap-2">
                      <label className="font-sans text-sm font-medium text-[#0F172A]">
                        <span className="font-mono text-xs text-[#0891B2] mr-2">{i + 1}.</span>
                        {q}
                      </label>
                      <textarea
                        value={qAnswers[i] ?? ''}
                        onChange={(e) =>
                          setQAnswers((prev) => prev.map((a, j) => (j === i ? e.target.value : a)))
                        }
                        rows={2}
                        autoFocus={i === 0}
                        placeholder="Your answer from memory…"
                        className="w-full resize-none rounded-lg border border-[rgba(15,23,42,0.15)] bg-white px-4 py-3 font-sans text-sm text-[#0F172A] placeholder:text-[#94a3b8] focus:outline-none focus:border-[#0891B2] focus:ring-2 focus:ring-[#0891B2]/20"
                      />
                    </div>
                  ))}
                </div>
              ) : loadingQuestions && !questionModeOff ? (
                /* Brief while we check for question mode (only stalls the first card
                   of a session when the grader is off; then falls back below). */
                <p className="font-sans text-sm text-[#64748B] italic">Preparing your recall…</p>
              ) : (
                <>
                  <p className="font-sans text-sm text-[#64748B]">
                    Type what you remember — then check yourself. No peeking.
                  </p>
                  <textarea
                    value={answer}
                    onChange={(e) => setAnswer(e.target.value)}
                    rows={4}
                    autoFocus
                    placeholder="Write your answer from memory…"
                    className="w-full resize-none rounded-lg border border-[rgba(15,23,42,0.15)] bg-white px-4 py-3 font-sans text-sm text-[#0F172A] placeholder:text-[#94a3b8] focus:outline-none focus:border-[#0891B2] focus:ring-2 focus:ring-[#0891B2]/20"
                  />
                </>
              )}
            </div>
          ) : (
            /* ---------- REVEAL: their attempt vs the stored answer ---------- */
            <div className="mt-6 flex flex-col gap-5 animate-in fade-in slide-in-from-bottom-2 duration-300">
              {questionMode ? (
                <div className="flex flex-col gap-3">
                  <div className="font-sans text-[11px] font-bold text-[#64748B] uppercase tracking-widest">Your answers</div>
                  {questions.map((q, i) => {
                    const item = qResult?.items?.find((it) => it.question === q) ?? null;
                    return (
                      <div key={i} className="bg-[rgba(15,23,42,0.03)] rounded p-3">
                        <p className="font-sans text-sm font-medium text-[#0F172A] flex items-start gap-2">
                          <span className="font-mono text-xs text-[#0891B2] mt-0.5">{i + 1}.</span>
                          <span className="flex-1">{q}</span>
                          {item && (
                            <span className={`shrink-0 font-sans text-[10px] font-bold uppercase tracking-wide px-1.5 py-0.5 rounded-full ${item.correct ? 'bg-[#0F766E]/10 text-[#0F766E]' : 'bg-[rgba(15,23,42,0.08)] text-[#334155]'}`}>
                              {item.correct ? 'Got it' : 'Missed'}
                            </span>
                          )}
                        </p>
                        <p className="font-sans text-sm text-[#1a1c1b] leading-relaxed mt-1.5 whitespace-pre-wrap">
                          {qAnswers[i]?.trim() ? qAnswers[i] : <span className="italic text-[#64748B]">No answer.</span>}
                        </p>
                        {/* Canonical answer from the lesson — deterministic, shown whether or not
                            the AI grader is available. The student must always see the right answer. */}
                        {canonicalAnswers[i] && (
                          <p className="font-sans text-sm text-[#0F766E] leading-relaxed mt-1.5">
                            <span className="font-semibold">Answer:</span> {canonicalAnswers[i]}
                          </p>
                        )}
                        {item?.note && (
                          <p className="font-sans text-xs text-[#64748B] mt-1.5">{item.note}</p>
                        )}
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div>
                  <div className="font-sans text-[11px] font-bold text-[#64748B] uppercase tracking-widest mb-1.5">Your answer</div>
                  <p className="font-sans text-sm text-[#1a1c1b] leading-relaxed bg-[rgba(15,23,42,0.03)] rounded p-3 whitespace-pre-wrap">
                    {skipped || !answer.trim() ? <span className="italic text-[#64748B]">You skipped this one.</span> : answer}
                  </p>
                </div>
              )}

              <div className="pt-4 border-t border-[rgba(15,23,42,0.08)]">
                <div className="font-sans text-[11px] font-bold text-[#0891B2] uppercase tracking-widest mb-1.5 flex items-center gap-1">
                  <CheckCircle2 size={12} /> Key Memory
                </div>
                <p className="font-sans text-base text-[#1a1c1b] leading-relaxed whitespace-pre-wrap">{activity.key_memory}</p>
              </div>

              {activity.mistake && (
                <div className="bg-[rgba(180,83,9,0.06)] border border-[#B45309]/20 rounded p-4">
                  <div className="font-sans text-[11px] font-bold text-[#B45309] uppercase tracking-widest mb-1.5 flex items-center gap-1">
                    <AlertTriangle size={12} /> Previous Mistake
                  </div>
                  <p className="font-sans text-sm text-[#0F172A] italic">"{activity.mistake}"</p>
                </div>
              )}
            </div>
          )}
        </div>
      </main>

      {/* Controls */}
      <footer className="w-full flex justify-center pb-8">
        {!revealed ? (
          <div className="w-full flex flex-col sm:flex-row gap-3 justify-center">
            <button
              onClick={handleSkip}
              className="kinetic-btn bg-white border border-[rgba(15,23,42,0.15)] text-[#64748B] hover:text-[#0F172A] py-3.5 px-6 text-sm font-medium"
            >
              I don't know
            </button>
            <button
              onClick={handleReveal}
              disabled={!committed}
              title="Ctrl+Enter"
              className="kinetic-btn kinetic-accent-gradient py-3.5 px-6 md:min-w-[260px] text-base disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Reveal answer
              <span className="hidden md:inline font-mono text-[10px] opacity-70 ml-2">Ctrl+↵</span>
            </button>
          </div>
        ) : (
          <div className="w-full flex flex-col items-center animate-in fade-in slide-in-from-bottom-4 duration-300">
            {/* AI grade proposal — instantly reserves space with a minimum height. */}
            {(grading || aiResult || qResult) && (
              <div className="w-full mb-4 rounded-xl border border-[#0891B2]/30 border-l-4 border-l-[#0891B2] bg-[#0891B2]/[0.07] p-4 shadow-sm min-h-[96px]">
                <div className="flex items-center gap-1.5 font-sans text-[11px] font-bold text-[#0891B2] uppercase tracking-widest mb-1.5">
                  <Sparkles size={12} /> AI feedback
                </div>
                {grading ? (
                  <div className="flex flex-col gap-2.5 mt-3">
                    <div className="skeleton h-3 w-4/5" />
                    <div className="skeleton h-3 w-2/3" />
                  </div>
                ) : questionMode && qResult ? (
                  <p className="font-sans text-sm text-[#1a1c1b] leading-relaxed">{qResult.feedback}</p>
                ) : aiResult ? (
                  <>
                    <p className="font-sans text-sm text-[#1a1c1b] leading-relaxed">{aiResult.feedback}</p>
                    {aiResult.revision_note && (
                      <div className="mt-3 pt-3 border-t border-[#0891B2]/15">
                        <div className="font-sans text-[10px] font-bold text-[#0891B2] uppercase tracking-widest mb-1.5">
                          Revision note
                        </div>
                        <p className="font-sans text-sm text-[#1a1c1b] leading-relaxed whitespace-pre-line">
                          {aiResult.revision_note}
                        </p>
                      </div>
                    )}
                  </>
                ) : null}
              </div>
            )}

            <div className="w-full mb-4 mt-2">
              <Hint id="review_honest_rating">
                Easy = you won't see this for weeks · Good = normal spacing · Hard = comes back soon · Missed = back tomorrow.
              </Hint>
            </div>
            
            <h3 className="font-sans text-xs font-semibold text-[#64748B] uppercase tracking-widest mb-4">How did it go?</h3>
            <div className="flex flex-col md:flex-row gap-4 w-full mb-6">
              <div className="flex-1 flex flex-col md:border-r border-[rgba(15,23,42,0.08)] md:pr-4">
                {(() => {
                  const o = OUTCOMES[0]; // Missed it
                  const isSuggested = o.key === suggestedKey;
                  return (
                    <button
                      key={o.key}
                      onClick={() => handleOutcome(o)}
                      disabled={submitting}
                      title="Press 1"
                      style={{ borderColor: o.border ?? o.color, color: o.color }}
                      className={`kinetic-btn relative bg-white border p-3 flex flex-col items-center justify-center transition-colors disabled:opacity-50 h-full ${isSuggested ? 'ring-2 ring-[#0891B2] ring-offset-1' : ''}`}
                      onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = o.color; e.currentTarget.style.color = '#ffffff'; e.currentTarget.querySelector('p').style.color = 'rgba(255,255,255,0.8)'; }}
                      onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = ''; e.currentTarget.style.color = o.color; e.currentTarget.querySelector('p').style.color = '#64748B'; }}
                    >
                      {isSuggested && (
                        <span className="absolute -top-2 left-1/2 -translate-x-1/2 bg-[#0891B2] text-white font-sans text-[9px] font-bold uppercase tracking-wide px-1.5 py-0.5 rounded-full whitespace-nowrap animate-in fade-in zoom-in duration-300">
                          Suggested
                        </span>
                      )}
                      <div className="font-semibold text-sm flex items-center gap-1.5 mb-0.5">
                        <span className="hidden md:inline font-mono text-[10px] opacity-50">1</span>
                        {o.label}
                      </div>
                      <p className="font-sans text-[10px] font-medium text-[#64748B] transition-colors">{o.desc}</p>
                    </button>
                  );
                })()}
              </div>
              <div className="flex-[3] grid grid-cols-1 sm:grid-cols-3 gap-3">
                {OUTCOMES.slice(1).map((o, i) => {
                  const isSuggested = o.key === suggestedKey;
                  return (
                    <button
                      key={o.key}
                      onClick={() => handleOutcome(o)}
                      disabled={submitting}
                      title={`Press ${i + 2}`}
                      style={{ borderColor: o.border ?? o.color, color: o.color }}
                      className={`kinetic-btn relative bg-white border p-3 flex flex-col items-center justify-center transition-colors disabled:opacity-50 h-full ${isSuggested ? 'ring-2 ring-[#0891B2] ring-offset-1' : ''}`}
                      onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = o.color; e.currentTarget.style.color = '#ffffff'; e.currentTarget.querySelector('p').style.color = 'rgba(255,255,255,0.8)'; }}
                      onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = ''; e.currentTarget.style.color = o.color; e.currentTarget.querySelector('p').style.color = '#64748B'; }}
                    >
                      {isSuggested && (
                        <span className="absolute -top-2 left-1/2 -translate-x-1/2 bg-[#0891B2] text-white font-sans text-[9px] font-bold uppercase tracking-wide px-1.5 py-0.5 rounded-full whitespace-nowrap animate-in fade-in zoom-in duration-300">
                          Suggested
                        </span>
                      )}
                      <div className="font-semibold text-sm flex items-center gap-1.5 mb-0.5">
                        <span className="hidden md:inline font-mono text-[10px] opacity-50">{i + 2}</span>
                        {o.label}
                      </div>
                      <p className="font-sans text-[10px] font-medium text-[#64748B] transition-colors">{o.desc}</p>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Suggested adjacent topics — distinct accent so they stand out from the
                feedback above. A nudge to capture these next, never part of the grade. */}
            {relatedSubtopics.length > 0 && (
              <div className="w-full rounded-xl border border-[#8B5CF6]/30 border-l-4 border-l-[#8B5CF6] bg-[#8B5CF6]/[0.06] p-4 mt-2">
                <div className="flex items-center gap-1.5 font-sans text-[11px] font-bold text-[#8B5CF6] uppercase tracking-widest mb-2.5">
                  <Lightbulb size={12} /> Worth exploring next
                </div>
                <div className="flex flex-col gap-2.5">
                  {relatedSubtopics.map((s, i) => (
                    <div key={i} className="flex flex-col">
                      <span className="font-sans text-sm font-semibold text-[#0F172A]">{s.title}</span>
                      {s.explainer && (
                        <span className="font-sans text-xs text-[#64748B] leading-relaxed">{s.explainer}</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </footer>
    </div>
  );
}

export default Review;
