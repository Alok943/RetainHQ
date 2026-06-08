import React from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from './lib/supabase';
import Logo from './Logo';
import { PenLine, RefreshCw, Brain, TrendingUp, Check, ArrowRight, Sparkles } from 'lucide-react';

function Login() {
  const navigate = useNavigate();
  
  const handleGoogleLogin = async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: window.location.origin },
    });
    if (error) console.error('Error logging in:', error.message);
  };

  // Primary CTA navigates to dashboard for PLG exploration.
  const GetStarted = ({ className = '' }) => (
    <button
      onClick={() => navigate('/dashboard')}
      className={`inline-flex items-center justify-center gap-2 rounded-full font-semibold px-7 py-3.5 text-white bg-gradient-to-r from-[#0891B2] to-[#06B6D4] shadow-lg shadow-[#0891B2]/25 hover:-translate-y-0.5 hover:shadow-[#0891B2]/40 transition-all ${className}`}
    >
      Get Started <ArrowRight size={17} />
    </button>
  );

  // SM-2 cadence (illustrative): baseline now, then +1d, +6d, then intervals
  // expand by your ease factor. Exact days adapt to how well you recall.
  const timeline = [
    { day: 'Day 0', label: 'Learn', sub: 'Log a new topic', state: 'done' },
    { day: 'Day 0', label: 'Baseline', sub: 'First recall', state: 'done' },
    { day: 'Day 1', label: 'Review', sub: 'Reinforce', state: 'active' },
    { day: 'Day 6', label: 'Review', sub: 'Strengthen', state: 'todo' },
    { day: 'Day 15+', label: 'Mastered', sub: 'Spacing widens as it sticks', state: 'goal' },
  ];

  const features = [
    { icon: <PenLine size={22} />, title: 'Capture', body: 'Log a topic in seconds.' },
    { icon: <RefreshCw size={22} />, title: 'Review', body: 'Reviews scheduled before you forget.' },
    { icon: <Brain size={22} />, title: 'Recall', body: 'Answer before the reveal — real recall, not recognition.' },
    { icon: <TrendingUp size={22} />, title: 'Retain', body: 'See what actually sticks over time.' },
  ];

  return (
    <div style={{ backgroundColor: '#0B1120' }} className="min-h-screen w-full overflow-y-auto">
      {/* ambient glow */}
      <div className="pointer-events-none fixed -top-40 left-1/2 -translate-x-1/2 w-[700px] h-[700px] rounded-full bg-[#0891B2]/10 blur-[140px]" />

      <div className="relative max-w-6xl mx-auto px-5 md:px-8">

        {/* ---------- Top nav ---------- */}
        <nav className="flex items-center justify-between py-5">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-[#0891B2]/10 rounded-xl flex items-center justify-center border border-[#0891B2]/20 shadow-[0_0_40px_rgba(8,145,178,0.2)]">
              <Logo variant="light" className="h-7 w-auto" />
            </div>
            <span className="font-sans text-[1.6rem] font-bold text-white tracking-tight">RetainHQ</span>
          </div>
          <div className="flex items-center gap-7">
            <a href="#features" className="hidden sm:block font-sans text-sm text-[#9aa3b8] hover:text-white transition-colors">Features</a>
            <a href="#how" className="hidden sm:block font-sans text-sm text-[#9aa3b8] hover:text-white transition-colors">How it works</a>
            <button
              onClick={handleGoogleLogin}
              className="font-sans text-sm font-semibold text-white border border-white/15 hover:border-[#0891B2]/60 hover:bg-white/5 rounded-full px-5 py-2 transition-colors"
            >
              Login
            </button>
          </div>
        </nav>

        {/* ---------- Hero ---------- */}
        <section className="grid lg:grid-cols-2 gap-12 lg:gap-10 items-center pt-8 md:pt-12 pb-10">
          {/* Left */}
          <div className="text-center lg:text-left">
            <div className="inline-flex items-center gap-2 rounded-full bg-white/5 border border-white/10 px-3 py-1 mb-6">
              <Sparkles size={13} className="text-[#22D3EE]" />
              <span className="font-sans text-xs text-[#9aa3b8]">Built on spaced repetition &amp; active recall</span>
            </div>

            <h1 className="font-sans text-4xl md:text-5xl font-bold text-white tracking-tight leading-[1.08] mb-5">
              Track what you remember,{' '}
              <span className="text-[#22D3EE]">not what you complete.</span>
            </h1>
            <p className="font-sans text-[#9aa3b8] text-lg leading-relaxed mb-8 max-w-md mx-auto lg:mx-0">
              Most study tools measure what you did. RetainHQ measures what you still remember — and schedules each review right before you'd forget, so it sticks.
            </p>

            <div className="flex mb-6 justify-center lg:justify-start">
              <GetStarted className="w-full sm:w-auto" />
            </div>

            {/* Honest mechanism strip (no invented stats, no claim of an "optimal" curve) */}
            <div className="flex flex-wrap items-center gap-x-5 gap-y-2 justify-center lg:justify-start font-mono text-[11px] text-[#7c839b]">
              <span className="flex items-center gap-1.5"><Check size={12} className="text-[#0891B2]" /> Active recall, not re-reading</span>
              <span className="flex items-center gap-1.5"><Check size={12} className="text-[#0891B2]" /> Reviewed right before you forget</span>
              <span className="flex items-center gap-1.5"><Check size={12} className="text-[#0891B2]" /> Free to start</span>
            </div>
          </div>

          {/* Right — spaced-repetition timeline */}
          <div className="flex justify-center lg:justify-end">
            <div className="relative w-full max-w-sm rounded-2xl bg-white/[0.04] border border-white/10 p-6 shadow-2xl backdrop-blur-sm">
              <div className="flex items-center justify-between mb-5">
                <span className="font-sans text-xs font-bold text-[#9aa3b8] uppercase tracking-widest">How a topic sticks</span>
                <span className="font-mono text-[10px] text-[#0891B2] bg-[#0891B2]/10 border border-[#0891B2]/20 rounded px-2 py-0.5">RETENTION</span>
              </div>

              <div className="relative">
                {/* connecting line */}
                <div className="absolute left-[15px] top-3 bottom-3 w-px bg-gradient-to-b from-[#0891B2]/60 via-[#0891B2]/30 to-[#22D3EE]/50" />

                <div className="flex flex-col gap-4">
                  {timeline.map((t, i) => {
                    const done = t.state === 'done';
                    const active = t.state === 'active';
                    const goal = t.state === 'goal';
                    return (
                      <div
                        key={t.day}
                        className="sr-row flex items-center gap-4 relative"
                        style={{ animationDelay: `${i * 140 + 150}ms` }}
                      >
                        {/* node */}
                        <div className="relative z-10 shrink-0">
                          {active && (
                            <span className="absolute inset-0 rounded-full bg-[#22D3EE]/40 animate-ping" />
                          )}
                          <div
                            className={`relative w-8 h-8 rounded-full flex items-center justify-center border ${
                              done
                                ? 'bg-[#0891B2] border-[#0891B2] text-white'
                                : active
                                ? 'bg-[#22D3EE] border-[#22D3EE] text-[#0B1120]'
                                : goal
                                ? 'bg-[#22D3EE]/15 border-[#22D3EE] text-[#22D3EE]'
                                : 'bg-white/5 border-white/20 text-[#7c839b]'
                            }`}
                          >
                            {done ? <Check size={15} /> : goal ? <Sparkles size={14} /> : <span className="w-1.5 h-1.5 rounded-full bg-current" />}
                          </div>
                        </div>

                        {/* label */}
                        <div className="flex-1 flex items-center justify-between">
                          <div>
                            <div className={`font-sans text-sm font-semibold ${goal ? 'text-[#22D3EE]' : 'text-white'}`}>
                              {t.label}
                            </div>
                            <div className="font-sans text-xs text-[#7c839b]">{t.sub}</div>
                          </div>
                          <span className="font-mono text-xs text-[#9aa3b8] shrink-0">{t.day}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ---------- Features / How it works ---------- */}
        <section id="features" className="scroll-mt-8 pb-6">
          <div id="how" className="scroll-mt-8 text-center mb-10">
            <h2 className="font-sans text-3xl font-bold text-white tracking-tight mb-3">The learning loop, automated</h2>
            <p className="font-sans text-[#9aa3b8] max-w-lg mx-auto">Four steps that turn a one-time study session into durable, long-term knowledge.</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {features.map((f, i) => (
              <div
                key={f.title}
                className="group rounded-xl bg-white/[0.04] border border-white/10 p-6 transition-all duration-200 hover:-translate-y-1 hover:border-[#0891B2]/50 hover:bg-white/[0.06] hover:shadow-[0_0_30px_rgba(8,145,178,0.15)]"
              >
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 rounded-xl bg-[#0891B2]/10 border border-[#0891B2]/20 flex items-center justify-center text-[#22D3EE] group-hover:scale-105 transition-transform">
                    {f.icon}
                  </div>
                  <span className="font-mono text-xs text-[#475569]">0{i + 1}</span>
                </div>
                <h3 className="font-sans text-lg font-semibold text-white mb-1">{f.title}</h3>
                <p className="font-sans text-sm text-[#9aa3b8] leading-relaxed">{f.body}</p>
              </div>
            ))}
          </div>
        </section>

        {/* ---------- Closing CTA ---------- */}
        <section className="flex flex-col items-center text-center gap-5 py-16 border-t border-white/5">
          <Sparkles size={22} className="text-[#22D3EE]" />
          <h2 className="font-sans text-2xl md:text-3xl font-bold text-white tracking-tight max-w-md">
            Stop relearning what you already studied.
          </h2>
          <p className="font-sans text-[#9aa3b8] text-sm">Inspired by cognitive science. Free to start.</p>
          <GetStarted />
          <p className="font-sans text-[11px] text-[#7c839b] max-w-xs leading-relaxed">
            By continuing, you agree to our Terms of Service and Privacy Policy.
          </p>
        </section>

      </div>
    </div>
  );
}

export default Login;
