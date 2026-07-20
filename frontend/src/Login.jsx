import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from './lib/supabase';
import Logo from './Logo';
import { track, EVENTS } from './lib/analytics';
import { PenLine, RefreshCw, Brain, TrendingUp, ArrowRight, Sparkles, Code2, Eye } from 'lucide-react';

function Login() {
  const navigate = useNavigate();

  const handleGoogleLogin = async () => {
    track(EVENTS.LANDING_CTA, { action: 'login' });
    track(EVENTS.SIGNUP_STARTED, { source: 'landing_nav' });
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: window.location.origin },
    });
    if (error) console.error('Error logging in:', error.message);
  };

  // Primary CTA navigates to dashboard for PLG exploration.
  const GetStarted = ({ className = '' }) => (
    <button
      onClick={() => { track(EVENTS.LANDING_CTA, { action: 'get_started' }); navigate('/dashboard'); }}
      className={`inline-flex items-center justify-center gap-2 rounded-full font-semibold px-7 py-3.5 text-white bg-gradient-to-r from-[#0891B2] to-[#06B6D4] shadow-lg shadow-[#0891B2]/25 hover:-translate-y-0.5 hover:shadow-[#0891B2]/40 transition-all ${className}`}
    >
      Get Started <ArrowRight size={17} />
    </button>
  );

  // Hero primary CTA — a guest-accessible showcase lesson, subject-neutral entry
  // point into the "show, don't tell" mechanism.
  const TryALesson = ({ className = '' }) => (
    <button
      onClick={() => { track(EVENTS.LANDING_CTA, { action: 'try_a_lesson' }); navigate('/roadmaps/dsa/learn/merge-sort'); }}
      className={`inline-flex items-center justify-center gap-2 rounded-full font-semibold px-7 py-3.5 text-white bg-gradient-to-r from-[#0891B2] to-[#06B6D4] shadow-lg shadow-[#0891B2]/25 hover:-translate-y-0.5 hover:shadow-[#0891B2]/40 transition-all ${className}`}
    >
      Try a lesson <ArrowRight size={17} />
    </button>
  );

  // Hero secondary CTA — ghost/outline, defers to the existing Get Started action.
  const GetStartedGhost = ({ className = '' }) => (
    <button
      onClick={() => { track(EVENTS.LANDING_CTA, { action: 'get_started' }); navigate('/dashboard'); }}
      className={`inline-flex items-center justify-center gap-2 rounded-full font-semibold px-7 py-3.5 text-white border border-white/20 hover:border-[#0891B2]/60 hover:bg-white/5 transition-all ${className}`}
    >
      Get Started
    </button>
  );

  // Subject-neutral breadth chip row — quiet proof the method isn't code-only.
  const subjects = ['DSA', 'Aptitude', 'Core CS', 'SQL', 'System Design', 'Python'];

  // FSRS cadence (illustrative): review milestones plotted on the retention
  // graph. Exact days adapt to how well you recall.
  const milestones = [
    { x: 38,  dotY: 30, day: 'Day 0',   label: 'Learn',        delay: 1.2 },
    { x: 96,  dotY: 34, day: 'Day 1',   label: 'First recall', delay: 1.9 },
    { x: 186, dotY: 36, day: 'Day 7',   label: 'Review',       delay: 2.7 },
    { x: 266, dotY: 38, day: 'Day 15+', label: 'Mastered',     delay: 3.5 },
  ];

  // Sawtooth that flattens: decay → review resets it → shallower decay. The
  // shape IS spaced repetition; the gray curve is what happens without it.
  const retainPath =
    'M 38 30 C 55 58, 75 78, 94 88 L 96 34 C 124 46, 154 56, 184 64 L 186 36 C 212 43, 238 48, 264 52 L 266 38 C 287 40, 308 42, 328 43';
  const forgetPath =
    'M 38 30 C 58 78, 88 128, 122 152 C 152 172, 190 180, 230 182 L 328 184';

  const features = [
    { icon: <PenLine size={22} />, title: 'Capture', body: 'Log a topic in seconds.' },
    { icon: <RefreshCw size={22} />, title: 'Review', body: 'Reviews scheduled before you forget.' },
    { icon: <Brain size={22} />, title: 'Recall', body: 'Answer before the reveal — real recall, not recognition.' },
    { icon: <TrendingUp size={22} />, title: 'Retain', body: 'See what actually sticks over time.' },
  ];

  // Step-through execution showcase (the "learn" pillar shown, not told).
  // A looping pre-computed trace of running_total(2) — every step is the real
  // execution order, no live runtime on the landing page.
  const codeLines = [
    'def running_total(n):',
    '    total = 0',
    '    for i in range(n):',
    '        total += i',
    '    return total',
    '',
    'running_total(2)',
  ];
  const traceSteps = [
    { line: 6, vars: [] },
    { line: 1, vars: [{ name: 'total', value: '0', changed: true }] },
    { line: 2, vars: [{ name: 'total', value: '0' }, { name: 'i', value: '0', changed: true }] },
    { line: 3, vars: [{ name: 'total', value: '0', changed: true }, { name: 'i', value: '0' }] },
    { line: 2, vars: [{ name: 'total', value: '0' }, { name: 'i', value: '1', changed: true }] },
    { line: 3, vars: [{ name: 'total', value: '1', changed: true }, { name: 'i', value: '1' }] },
    { line: 4, vars: [{ name: 'total', value: '1' }, { name: 'i', value: '1' }], reveal: true },
  ];
  const [traceStep, setTraceStep] = useState(0);
  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    // Hold the reveal frame longer so the predict → answer beat lands.
    const t = setTimeout(
      () => setTraceStep((s) => (s + 1) % traceSteps.length),
      traceStep === traceSteps.length - 1 ? 2400 : 1100
    );
    return () => clearTimeout(t);
  }, [traceStep, traceSteps.length]);

  // The graph animates only while the user is actually looking at it: the
  // first viewport entry starts it (on mobile it sits below the fold, so a
  // mount-time start would finish before anyone scrolls to it), and each
  // re-entry replays it — bumping the key remounts the SVG, restarting its
  // CSS animations. Reduced-motion users get the final frame via CSS.
  const graphRef = useRef(null);
  const [graphPlay, setGraphPlay] = useState(false);
  const [graphRun, setGraphRun] = useState(0);
  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const el = graphRef.current;
    if (!el || !('IntersectionObserver' in window)) {
      setGraphPlay(true);
      return;
    }
    let wasOut = false;
    const obs = new IntersectionObserver(([e]) => {
      if (e.isIntersecting) {
        setGraphPlay(true);
        if (wasOut) setGraphRun((n) => n + 1);
        wasOut = false;
      } else {
        wasOut = true;
      }
    }, { threshold: 0.35 });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);
  const activeLine = traceSteps[traceStep].line;
  const traceState = traceSteps[traceStep].vars;
  const revealed = Boolean(traceSteps[traceStep].reveal);

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

        <main>
        {/* ---------- Hero ---------- */}
        <section className="grid lg:grid-cols-2 gap-12 lg:gap-10 items-center pt-8 md:pt-12 pb-10">
          {/* Left — problem-first, revealed left → right */}
          <div className="text-center lg:text-left">
            <h1 className="hero-reveal font-sans text-4xl md:text-5xl font-bold text-white tracking-tight leading-[1.08] mb-5">
              Stop watching tutorials you{' '}
              <span className="text-[#22D3EE]">forget by Friday.</span>
            </h1>
            <p className="hero-reveal font-sans text-[#9aa3b8] text-lg leading-relaxed mb-8 max-w-md mx-auto lg:mx-0" style={{ animationDelay: '140ms' }}>
              RetainHQ is a spaced-repetition system for engineers. Learn from visual lessons, then short reviews return right before you'd forget — so it stays in your memory.
            </p>

            <div className="hero-reveal flex flex-col sm:flex-row gap-3 mb-6 justify-center lg:justify-start" style={{ animationDelay: '280ms' }}>
              <TryALesson className="w-full sm:w-auto" />
              <GetStartedGhost className="w-full sm:w-auto" />
            </div>

            {/* Subject-neutral breadth row — the method, not a single subject */}
            <div className="hero-reveal flex flex-wrap items-center gap-2 justify-center lg:justify-start" style={{ animationDelay: '420ms' }}>
              {subjects.map((s) => (
                <span
                  key={s}
                  className="font-mono text-[11px] text-[#9aa3b8] border border-white/[0.12] rounded-full px-[10px] py-[3px]"
                >
                  {s}
                </span>
              ))}
            </div>
          </div>

          {/* Right — animated retention graph: forgetting curve vs spaced reviews */}
          <div className="flex justify-center lg:justify-end">
            <div ref={graphRef} className="relative w-full max-w-md rounded-2xl bg-white/[0.04] border border-white/10 p-6 shadow-2xl backdrop-blur-sm">
              <div className="flex items-center justify-between mb-4">
                <span className="font-sans text-xs font-bold text-[#9aa3b8] uppercase tracking-widest">How a topic sticks</span>
                <span className="font-mono text-[10px] text-[#0891B2] bg-[#0891B2]/10 border border-[#0891B2]/20 rounded px-2 py-0.5">RETENTION</span>
              </div>

              <svg key={graphRun} viewBox="0 0 340 212" className={`w-full h-auto ${graphPlay ? 'rg-play' : ''}`} role="img" aria-label="Graph: memory decays without reviews, but each spaced review resets it and the curve flattens until the topic is mastered">
                <defs>
                  <linearGradient id="rg-area" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#22D3EE" stopOpacity="0.22" />
                    <stop offset="100%" stopColor="#22D3EE" stopOpacity="0" />
                  </linearGradient>
                </defs>

                {/* axes */}
                <line x1="34" y1="188" x2="330" y2="188" stroke="rgba(255,255,255,0.12)" strokeWidth="1" />
                <text x="30" y="33" textAnchor="end" fill="#7c839b" fontSize="8" fontFamily="monospace">100%</text>
                <text x="30" y="187" textAnchor="end" fill="#7c839b" fontSize="8" fontFamily="monospace">0%</text>

                {/* day labels */}
                {milestones.map((m) => (
                  <text
                    key={m.day}
                    x={m.x} y="202" textAnchor="middle"
                    fill="#9aa3b8" fontSize="9" fontFamily="monospace"
                    className="rg-fade" style={{ '--rg-delay': '0.5s' }}
                  >
                    {m.day}
                  </text>
                ))}

                {/* the problem: unaided forgetting curve */}
                <path
                  d={forgetPath} pathLength="1"
                  fill="none" stroke="#64748B" strokeOpacity="0.55" strokeWidth="1.5" strokeDasharray="1" strokeLinecap="round"
                  className="rg-curve" style={{ '--rg-dur': '1.6s', '--rg-delay': '0.4s' }}
                />
                <text x="326" y="176" textAnchor="end" fill="#7c839b" fontSize="9" fontFamily="sans-serif" className="rg-fade" style={{ '--rg-delay': '2s' }}>
                  without reviews
                </text>

                {/* the product: spaced reviews reset the curve */}
                <path
                  d={`${retainPath} L 328 188 L 38 188 Z`}
                  fill="url(#rg-area)" stroke="none"
                  className="rg-fade" style={{ '--rg-delay': '3.9s', '--rg-opacity': '1' }}
                />
                <path
                  d={retainPath} pathLength="1"
                  fill="none" stroke="#22D3EE" strokeWidth="2" strokeLinecap="round"
                  className="rg-curve" style={{ '--rg-dur': '2.8s', '--rg-delay': '1.1s' }}
                />
                <text x="326" y="78" textAnchor="end" fill="#22D3EE" fontSize="9" fontWeight="600" fontFamily="sans-serif" className="rg-fade" style={{ '--rg-delay': '4s' }}>
                  with RetainHQ
                </text>

                {/* review pings + milestone labels */}
                {milestones.map((m, i) => (
                  <g key={m.label}>
                    {i > 0 && (
                      <circle cx={m.x} cy={m.dotY} r="5" fill="none" stroke="#22D3EE" strokeWidth="1.5" className="rg-halo" style={{ '--rg-delay': `${m.delay + 2.2}s` }} />
                    )}
                    <circle
                      cx={m.x} cy={m.dotY} r="4"
                      fill={i === 0 ? '#0891B2' : '#22D3EE'} stroke="#0B1120" strokeWidth="1.5"
                      className="rg-dot" style={{ '--rg-delay': `${m.delay}s` }}
                    />
                    <text
                      x={m.x} y={m.dotY - 12} textAnchor="middle"
                      fill={i === milestones.length - 1 ? '#22D3EE' : '#c9d1e3'} fontSize="9" fontWeight="600" fontFamily="sans-serif"
                      className="rg-fade" style={{ '--rg-delay': `${m.delay + 0.1}s` }}
                    >
                      {m.label}
                    </text>
                  </g>
                ))}
              </svg>

              <p className="font-sans text-[11px] text-[#7c839b] mt-3 leading-relaxed">
                Each review lands right before you'd forget — and the curve flattens until it barely decays at all.
              </p>
            </div>
          </div>
        </section>

        {/* ---------- Showcase: see it execute (the "learn" pillar, shown not told) ---------- */}
        <section id="learn" className="scroll-mt-8 py-12 md:py-16 border-t border-white/5">
          <div className="text-center mb-10">
            <div className="inline-flex items-center gap-2 rounded-full bg-white/5 border border-white/10 px-3 py-1 mb-5">
              <Code2 size={13} className="text-[#22D3EE]" />
              <span className="font-sans text-xs text-[#9aa3b8]">Step 1 — learn it properly</span>
            </div>
            <h2 className="font-sans text-3xl font-bold text-white tracking-tight mb-3">See every line execute</h2>
            <p className="font-sans text-[#9aa3b8] max-w-xl mx-auto">
              Most tutorials show you finished code. RetainHQ runs it — scrub line by line, watch the variables change, and guess the output <span className="text-white">before</span> you reveal it. That predict-then-see moment is what makes it click.
            </p>
          </div>

          <div className="max-w-3xl mx-auto rounded-2xl bg-white/[0.04] border border-white/10 shadow-2xl backdrop-blur-sm overflow-hidden">
            {/* window chrome */}
            <div className="flex items-center justify-between px-4 py-2.5 border-b border-white/10 bg-white/[0.02]">
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-full bg-[#ff5f56]/70" />
                <span className="w-3 h-3 rounded-full bg-[#ffbd2e]/70" />
                <span className="w-3 h-3 rounded-full bg-[#27c93f]/70" />
              </div>
              <span className="font-mono text-[10px] text-[#7c839b]">running_total.py</span>
              <span className="font-mono text-[10px] text-[#22D3EE] bg-[#22D3EE]/10 border border-[#22D3EE]/20 rounded px-2 py-0.5">STEP {traceStep + 1} / {traceSteps.length}</span>
            </div>

            <div className="grid md:grid-cols-[1.5fr_1fr]">
              {/* code — current line highlighted, like the step scrubber */}
              <div className="p-5 font-mono text-[13px] leading-[1.7] border-b md:border-b-0 md:border-r border-white/10 overflow-x-auto">
                {codeLines.map((line, i) => (
                  <div
                    key={i}
                    className={`flex gap-3 px-2 -mx-2 rounded transition-colors duration-300 ${
                      i === activeLine ? 'bg-[#0891B2]/15 border-l-2 border-[#22D3EE]' : 'border-l-2 border-transparent'
                    }`}
                  >
                    <span className="text-[#475569] select-none w-4 text-right shrink-0">{i + 1}</span>
                    <span className={`whitespace-pre ${i === activeLine ? 'text-white' : 'text-[#c9d1e3]'}`}>{line || ' '}</span>
                  </div>
                ))}
              </div>

              {/* live state + predict-before-reveal */}
              <div className="p-5">
                <div className="font-sans text-[10px] uppercase tracking-widest text-[#7c839b] mb-3">State now</div>
                <div className="space-y-2 mb-5 min-h-[52px]">
                  {traceState.length === 0 && (
                    <div className="font-mono text-xs text-[#475569]">— no variables yet</div>
                  )}
                  {traceState.map((v) => (
                    <div key={v.name} className="flex items-center justify-between font-mono text-xs">
                      <span className="text-[#9aa3b8]">{v.name}</span>
                      <span className={`rounded px-2 py-0.5 transition-colors duration-300 ${v.changed ? 'text-[#22D3EE] bg-[#22D3EE]/10 border border-[#22D3EE]/20' : 'text-[#c9d1e3] bg-white/5 border border-white/10'}`}>{v.value}</span>
                    </div>
                  ))}
                </div>

                <div className="rounded-lg bg-[#22D3EE]/[0.06] border border-[#22D3EE]/20 p-3">
                  <div className="flex items-center gap-1.5 mb-2">
                    <Eye size={12} className="text-[#22D3EE]" />
                    <span className="font-sans text-[11px] font-semibold text-[#22D3EE]">Predict before reveal</span>
                  </div>
                  <div className="flex items-center justify-between font-mono text-xs">
                    <span className="text-[#9aa3b8]">running_total(2)</span>
                    <span className={`rounded px-2 py-0.5 border transition-colors duration-300 ${revealed ? 'text-[#22D3EE] bg-[#22D3EE]/15 border-[#22D3EE]/30 font-semibold' : 'text-[#7c839b] bg-white/5 border-transparent'}`}>
                      {revealed ? '= 1' : '= ?'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ---------- Features / How it works ---------- */}
        <section id="features" className="scroll-mt-8 pb-6">
          <div id="how" className="scroll-mt-8 text-center mb-10">
            <div className="inline-flex items-center gap-2 rounded-full bg-white/5 border border-white/10 px-3 py-1 mb-5">
              <RefreshCw size={13} className="text-[#22D3EE]" />
              <span className="font-sans text-xs text-[#9aa3b8]">Step 2 — never forget it</span>
            </div>
            <h2 className="font-sans text-3xl font-bold text-white tracking-tight mb-3">Then it sticks — automatically</h2>
            <p className="font-sans text-[#9aa3b8] max-w-lg mx-auto">Every lesson you finish and every topic you capture enters a spaced-repetition loop, resurfacing right before you'd forget — so a one-time study session becomes durable, long-term knowledge.</p>
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
                  <span className="font-mono text-xs text-[#7c839b]">0{i + 1}</span>
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
            Remember it when the interview comes.
          </h2>
          <p className="font-sans text-[#9aa3b8] text-sm">Learn it visually. Remember it for good. Free to start.</p>
          <GetStarted />
          <p className="font-sans text-[11px] text-[#7c839b] max-w-xs leading-relaxed">
            By continuing, you agree to our Terms of Service and Privacy Policy.
          </p>
        </section>
        </main>

      </div>
    </div>
  );
}

export default Login;
