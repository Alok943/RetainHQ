import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { X, ChevronRight, ChevronLeft, Sparkles, PenLine, Brain, CalendarClock, Vault } from 'lucide-react';

const DISMISSED_KEY = 'retainhq_onboarding_dismissed';

const STEPS = [
  {
    icon: Sparkles,
    accentColor: '#0891B2',
    title: 'Welcome to RetainHQ',
    subtitle: 'Your personal retention engine',
    description:
      'Most tools track what you studied. RetainHQ tracks what you actually remember — and reviews it right before you\'d forget.',
    tip: null,
    action: null,
  },
  {
    icon: PenLine,
    accentColor: '#8B5CF6',
    title: '1. Capture what you learn',
    subtitle: 'Log Activity',
    description:
      'After reading, watching, or practicing — log a quick entry. The key field is the Key Memory: the single thing you want to keep.',
    tip: 'Keep it to one sentence. "Dictionaries store key-value pairs, are mutable" is perfect.',
    action: { label: 'Try logging →', path: '/log' },
  },
  {
    icon: Brain,
    accentColor: '#F59E0B',
    title: '2. Test yourself immediately',
    subtitle: 'Baseline Review',
    description:
      'RetainHQ doesn\'t wait — you get a baseline recall right away. Type what you remember before the reveal. Real recall, not recognition.',
    tip: 'Rating honestly (Easy / Good / Hard) teaches the algorithm how quickly you forget.',
    action: null,
  },
  {
    icon: CalendarClock,
    accentColor: '#10B981',
    title: '3. It schedules itself',
    subtitle: 'Spaced Repetition',
    description:
      'Based on your recall, the next review is scheduled automatically. The spacing widens as it sticks — so you stop relearning things you already know.',
    tip: 'Come back when you see reviews due on your Home screen. That\'s the magic moment.',
    action: null,
  },
  {
    icon: Vault,
    accentColor: '#0891B2',
    title: '4. Watch your vault grow',
    subtitle: 'Knowledge Vault',
    description:
      'Every topic lives in your Vault with its source, key memory, and next review date. Over time, this becomes your personal knowledge base.',
    tip: null,
    action: { label: 'Open Vault →', path: '/vault' },
  },
];

export default function OnboardingGuide() {
  const [dismissed, setDismissed] = useState(true); // default hidden to avoid flash
  const [currentStep, setCurrentStep] = useState(0);
  const [direction, setDirection] = useState(0); // -1 = left, 1 = right, 0 = initial
  const [animating, setAnimating] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const wasDismissed = localStorage.getItem(DISMISSED_KEY);
    if (!wasDismissed) setDismissed(false);
  }, []);

  const dismiss = () => {
    setDismissed(true);
    localStorage.setItem(DISMISSED_KEY, 'true');
  };

  const goTo = (nextStep) => {
    if (animating || nextStep === currentStep) return;
    setDirection(nextStep > currentStep ? 1 : -1);
    setAnimating(true);
    setTimeout(() => {
      setCurrentStep(nextStep);
      setAnimating(false);
    }, 250);
  };

  if (dismissed) return null;

  const step = STEPS[currentStep];
  const Icon = step.icon;
  const isFirst = currentStep === 0;
  const isLast = currentStep === STEPS.length - 1;
  const progress = ((currentStep + 1) / STEPS.length) * 100;

  return (
    <section className="onboarding-guide" id="onboarding-guide">
      {/* Progress bar */}
      <div className="onboarding-progress-track">
        <div
          className="onboarding-progress-fill"
          style={{
            width: `${progress}%`,
            background: `linear-gradient(90deg, #0891B2, ${step.accentColor})`,
          }}
        />
      </div>

      {/* Header row */}
      <div className="onboarding-header">
        <div className="onboarding-step-badge" style={{ color: step.accentColor, borderColor: `${step.accentColor}30` , backgroundColor: `${step.accentColor}10` }}>
          {currentStep + 1} / {STEPS.length}
        </div>
        <button onClick={dismiss} className="onboarding-dismiss" title="Dismiss guide" aria-label="Dismiss guide">
          <X size={16} />
        </button>
      </div>

      {/* Content area */}
      <div className={`onboarding-body ${animating ? (direction > 0 ? 'slide-out-left' : 'slide-out-right') : 'slide-in'}`}>
        <div
          className="onboarding-icon-ring"
          style={{ background: `${step.accentColor}15`, borderColor: `${step.accentColor}30` }}
        >
          <Icon size={24} style={{ color: step.accentColor }} />
        </div>

        <div className="onboarding-text">
          <p className="onboarding-subtitle" style={{ color: step.accentColor }}>
            {step.subtitle}
          </p>
          <h3 className="onboarding-title">{step.title}</h3>
          <p className="onboarding-desc">{step.description}</p>

          {step.tip && (
            <div className="onboarding-tip">
              <span className="onboarding-tip-label">💡 Tip</span>
              <span>{step.tip}</span>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="onboarding-footer">
        <div className="onboarding-dots">
          {STEPS.map((_, i) => (
            <button
              key={i}
              onClick={() => goTo(i)}
              className={`onboarding-dot ${i === currentStep ? 'active' : ''}`}
              style={i === currentStep ? { backgroundColor: step.accentColor } : {}}
              aria-label={`Go to step ${i + 1}`}
            />
          ))}
        </div>

        <div className="onboarding-actions">
          {step.action && (
            <button
              className="onboarding-action-link"
              style={{ color: step.accentColor }}
              onClick={() => {
                dismiss();
                navigate(step.action.path);
              }}
            >
              {step.action.label}
            </button>
          )}

          {!isFirst && (
            <button className="onboarding-nav-btn onboarding-prev" onClick={() => goTo(currentStep - 1)}>
              <ChevronLeft size={16} /> Back
            </button>
          )}

          {isLast ? (
            <button
              className="onboarding-nav-btn onboarding-finish"
              style={{ background: `linear-gradient(135deg, #0891B2, ${step.accentColor})` }}
              onClick={dismiss}
            >
              Get started!
            </button>
          ) : (
            <button
              className="onboarding-nav-btn onboarding-next"
              style={{ background: `linear-gradient(135deg, #0891B2, ${step.accentColor})` }}
              onClick={() => goTo(currentStep + 1)}
            >
              Next <ChevronRight size={16} />
            </button>
          )}
        </div>
      </div>
    </section>
  );
}
