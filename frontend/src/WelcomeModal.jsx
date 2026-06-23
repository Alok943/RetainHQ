import React, { useState, useEffect } from 'react';
import { X, ChevronLeft, ChevronRight, Sparkles, PenLine, Brain, TrendingUp } from 'lucide-react';

// Shown once per browser, wherever the visitor first lands (marketing landing
// OR the in-app dashboard) — a guest who clicks "Get Started" hits an empty app
// with no context otherwise. Self-contained dark styling so it looks native on
// the always-dark Login page and clean as a dark modal over the themed app.
const SEEN_KEY = 'retainhq_intro_seen';

const STEPS = [
  {
    icon: Sparkles,
    accent: '#22D3EE',
    eyebrow: 'What is RetainHQ?',
    title: 'Remember what you learn — not just what you finished',
    body: 'Most study tools track what you completed. RetainHQ tracks what you actually remember, and brings each topic back right before you\'d forget it. Built for DSA, system design, and anything you need to stick.',
  },
  {
    icon: PenLine,
    accent: '#8B5CF6',
    eyebrow: 'Step 1 · Capture',
    title: 'Log what you learn in seconds',
    body: 'After you read, watch, or solve something, jot down the one key memory worth keeping — a single sentence. That becomes a card RetainHQ schedules for you.',
  },
  {
    icon: Brain,
    accent: '#F59E0B',
    eyebrow: 'Step 2 · Recall',
    title: 'Pull it back from memory later',
    body: 'Reviews land on a spaced schedule — the next day, then wider apart as it sticks. You type what you remember before the answer is revealed: real recall, not re-reading.',
  },
  {
    icon: TrendingUp,
    accent: '#10B981',
    eyebrow: 'Step 3 · Retain',
    title: 'Watch knowledge actually stick',
    body: 'Every topic lives in your Knowledge Vault with its next review date. Over time you stop relearning what you already studied — that\'s the whole point.',
  },
];

export default function WelcomeModal({ onDone, ctaLabel = 'Got it — let\'s go' }) {
  const [visible, setVisible] = useState(false); // default hidden to avoid flash
  const [step, setStep] = useState(0);

  useEffect(() => {
    try {
      if (!localStorage.getItem(SEEN_KEY)) setVisible(true);
    } catch (e) {
      /* private mode etc. — just don't show */
    }
  }, []);

  const close = () => {
    setVisible(false);
    try {
      localStorage.setItem(SEEN_KEY, '1');
    } catch (e) {}
    if (onDone) onDone();
  };

  if (!visible) return null;

  const s = STEPS[step];
  const Icon = s.icon;
  const isLast = step === STEPS.length - 1;
  const progress = ((step + 1) / STEPS.length) * 100;

  return (
    <div
      className="fixed inset-0 z-[70] flex items-center justify-center p-4 welcome-fade"
      style={{ backgroundColor: 'rgba(2, 6, 16, 0.78)', backdropFilter: 'blur(6px)' }}
      onClick={close}
      role="dialog"
      aria-modal="true"
      aria-label="Welcome to RetainHQ"
    >
      <div
        className="relative w-full max-w-md rounded-2xl border border-white/10 overflow-hidden shadow-2xl welcome-pop"
        style={{ backgroundColor: '#0F172A' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* ambient glow */}
        <div
          className="pointer-events-none absolute -top-24 left-1/2 -translate-x-1/2 w-72 h-72 rounded-full blur-[90px]"
          style={{ backgroundColor: `${s.accent}22` }}
        />

        {/* progress */}
        <div className="h-[3px] w-full bg-white/10">
          <div
            className="h-full transition-all duration-500 ease-out"
            style={{ width: `${progress}%`, background: `linear-gradient(90deg, #0891B2, ${s.accent})` }}
          />
        </div>

        {/* header */}
        <div className="relative flex items-center justify-between px-6 pt-5">
          <span
            className="font-mono text-[11px] font-bold tracking-wider px-2.5 py-1 rounded-full border"
            style={{ color: s.accent, borderColor: `${s.accent}40`, backgroundColor: `${s.accent}12` }}
          >
            {step + 1} / {STEPS.length}
          </span>
          <button
            onClick={close}
            aria-label="Close"
            className="text-[#7c839b] hover:text-white transition-colors p-1.5 rounded-md hover:bg-white/5"
          >
            <X size={16} />
          </button>
        </div>

        {/* body */}
        <div className="relative px-6 pt-5 pb-2">
          <div
            className="w-13 h-13 rounded-2xl flex items-center justify-center border mb-4"
            style={{ width: 52, height: 52, backgroundColor: `${s.accent}1a`, borderColor: `${s.accent}33`, color: s.accent }}
          >
            <Icon size={24} />
          </div>
          <p className="font-sans text-[11px] font-bold uppercase tracking-[0.08em] mb-1.5" style={{ color: s.accent }}>
            {s.eyebrow}
          </p>
          <h3 className="font-sans text-xl font-bold text-white leading-snug mb-2.5">{s.title}</h3>
          <p className="font-sans text-sm text-[#9aa3b8] leading-relaxed">{s.body}</p>
        </div>

        {/* footer */}
        <div className="relative flex items-center justify-between px-6 pb-5 pt-4 gap-3">
          <div className="flex gap-1.5">
            {STEPS.map((_, i) => (
              <button
                key={i}
                onClick={() => setStep(i)}
                aria-label={`Go to step ${i + 1}`}
                className="h-2 rounded-full transition-all duration-300"
                style={{
                  width: i === step ? 22 : 8,
                  backgroundColor: i === step ? s.accent : 'rgba(255,255,255,0.18)',
                }}
              />
            ))}
          </div>

          <div className="flex items-center gap-2">
            {step > 0 && (
              <button
                onClick={() => setStep(step - 1)}
                className="inline-flex items-center gap-1 text-[13px] font-semibold text-[#9aa3b8] hover:text-white px-3 py-2 rounded-lg hover:bg-white/5 transition-colors"
              >
                <ChevronLeft size={15} /> Back
              </button>
            )}
            {isLast ? (
              <button
                onClick={close}
                className="inline-flex items-center gap-1.5 text-[13px] font-semibold text-white px-4 py-2 rounded-lg transition-all hover:-translate-y-0.5"
                style={{ background: 'linear-gradient(135deg, #0891B2, #06B6D4)', boxShadow: '0 2px 10px rgba(8,145,178,0.35)' }}
              >
                {ctaLabel}
              </button>
            ) : (
              <button
                onClick={() => setStep(step + 1)}
                className="inline-flex items-center gap-1.5 text-[13px] font-semibold text-white px-4 py-2 rounded-lg transition-all hover:-translate-y-0.5"
                style={{ background: 'linear-gradient(135deg, #0891B2, #06B6D4)', boxShadow: '0 2px 10px rgba(8,145,178,0.35)' }}
              >
                Next <ChevronRight size={15} />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
