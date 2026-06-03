import React, { useState, useEffect } from 'react';
import { ArrowLeft, CheckCircle2, AlertTriangle, Brain, PartyPopper } from 'lucide-react';
import { apiFetch } from './lib/api';

// Each post-reveal choice carries BOTH signals at once:
//   recalled = objective (did they reconstruct it?)   rating = subjective (how hard it felt)
const OUTCOMES = [
  { key: 'missed', label: 'Missed it', rating: 'hard',   recalled: false, color: '#B91C1C' },
  { key: 'hard',   label: 'Hard',      rating: 'hard',   recalled: true,  color: '#B45309' },
  { key: 'good',   label: 'Good',      rating: 'medium', recalled: true,  color: '#0891B2' },
  { key: 'easy',   label: 'Easy',      rating: 'easy',   recalled: true,  color: '#0F766E' },
];

function Review({ onBack }) {
  const [reviews, setReviews] = useState([]);
  const [index, setIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Per-card state
  const [revealed, setRevealed] = useState(false);
  const [answer, setAnswer] = useState('');
  const [skipped, setSkipped] = useState(false); // user committed "I don't know"
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    apiFetch('/api/reviews/due')
      .then((data) => setReviews(data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const current = reviews[index] ?? null;
  const total = reviews.length;
  const committed = answer.trim().length > 0 || skipped;

  const resetCard = () => {
    setRevealed(false);
    setAnswer('');
    setSkipped(false);
  };

  const handleReveal = () => {
    if (!committed) return;
    setRevealed(true);
  };

  const handleOutcome = async (outcome) => {
    if (!current || submitting) return;
    setSubmitting(true);
    try {
      await apiFetch(`/api/reviews/${current.id}/complete`, {
        method: 'POST',
        body: JSON.stringify({ rating: outcome.rating, recalled: outcome.recalled }),
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

  /* ---------- non-card states ---------- */

  if (loading) {
    return <div className="p-8 text-center text-[#64748B] font-sans">Loading your reviews…</div>;
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
        {done ? <PartyPopper size={32} className="text-[#0F766E]" /> : <CheckCircle2 size={32} className="text-[#0F766E]" />}
        <h2 className="font-sans text-xl font-semibold text-[#0F172A]">
          {done ? 'Reviews complete' : "You're all caught up"}
        </h2>
        <p className="font-sans text-sm text-[#64748B] max-w-xs">
          {done
            ? `You worked through ${total} review${total > 1 ? 's' : ''}. Nice — that's what builds long-term memory.`
            : 'No reviews are due right now. Log a new activity to keep the loop going.'}
        </p>
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
        <div className="w-full h-1 bg-[rgba(15,23,42,0.08)] rounded-full overflow-hidden">
          <div
            className="h-full bg-[#0891B2] transition-all duration-300"
            style={{ width: `${(index / total) * 100}%` }}
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

          {!revealed ? (
            /* ---------- RECALL GATE: commit before reveal ---------- */
            <div className="mt-6 flex flex-col gap-4">
              <p className="font-sans text-sm text-[#64748B]">
                Type what you remember — then check yourself. No peeking.
              </p>
              <textarea
                value={answer}
                onChange={(e) => { setAnswer(e.target.value); if (skipped) setSkipped(false); }}
                disabled={skipped}
                rows={4}
                autoFocus
                placeholder="Write your answer from memory…"
                className="w-full resize-none rounded-lg border border-[rgba(15,23,42,0.15)] bg-white px-4 py-3 font-sans text-sm text-[#0F172A] placeholder:text-[#94a3b8] focus:outline-none focus:border-[#0891B2] focus:ring-2 focus:ring-[#0891B2]/20 disabled:opacity-50"
              />
              {skipped && (
                <p className="font-sans text-xs text-[#64748B] italic">Marked as "didn't recall" — reveal to see the answer.</p>
              )}
            </div>
          ) : (
            /* ---------- REVEAL: their attempt vs the stored answer ---------- */
            <div className="mt-6 flex flex-col gap-5 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <div>
                <div className="font-sans text-[11px] font-bold text-[#64748B] uppercase tracking-widest mb-1.5">Your answer</div>
                <p className="font-sans text-sm text-[#1a1c1b] leading-relaxed bg-[rgba(15,23,42,0.03)] rounded p-3 whitespace-pre-wrap">
                  {skipped || !answer.trim() ? <span className="italic text-[#64748B]">You skipped this one.</span> : answer}
                </p>
              </div>

              <div className="pt-4 border-t border-[rgba(15,23,42,0.08)]">
                <div className="font-sans text-[11px] font-bold text-[#0891B2] uppercase tracking-widest mb-1.5 flex items-center gap-1">
                  <CheckCircle2 size={12} /> Key Memory
                </div>
                <p className="font-sans text-base text-[#1a1c1b] leading-relaxed whitespace-pre-wrap">{activity.key_memory}</p>
              </div>

              {activity.mistake && (
                <div className="bg-[#ba1a1a]/5 border border-[#ba1a1a]/20 rounded p-4">
                  <div className="font-sans text-[11px] font-bold text-[#ba1a1a] uppercase tracking-widest mb-1.5 flex items-center gap-1">
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
              onClick={() => { setSkipped(true); setAnswer(''); }}
              className="kinetic-btn bg-white border border-[rgba(15,23,42,0.15)] text-[#64748B] hover:text-[#0F172A] py-3.5 px-6 text-sm font-medium"
            >
              I don't know
            </button>
            <button
              onClick={handleReveal}
              disabled={!committed}
              className="kinetic-btn kinetic-accent-gradient py-3.5 px-6 md:min-w-[260px] text-base disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Reveal answer
            </button>
          </div>
        ) : (
          <div className="w-full flex flex-col items-center animate-in fade-in slide-in-from-bottom-4 duration-300">
            <h3 className="font-sans text-xs font-semibold text-[#64748B] uppercase tracking-widest mb-4">How did it go?</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 w-full">
              {OUTCOMES.map((o) => (
                <button
                  key={o.key}
                  onClick={() => handleOutcome(o)}
                  disabled={submitting}
                  style={{ borderColor: o.color, color: o.color }}
                  className="kinetic-btn bg-white border py-3 font-semibold text-sm transition-colors disabled:opacity-50"
                  onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = o.color; e.currentTarget.style.color = '#ffffff'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = ''; e.currentTarget.style.color = o.color; }}
                >
                  {o.label}
                </button>
              ))}
            </div>
          </div>
        )}
      </footer>
    </div>
  );
}

export default Review;
