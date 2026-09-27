import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { supabase } from './lib/supabase';
import Logo from './Logo';
import { track, EVENTS } from './lib/analytics';
import { useTheme } from './lib/theme';
import { Sun, Moon } from 'lucide-react';

// Defined outside Login: Login re-renders every trace step (~1.1s), and an
// inline component would remount each time, dropping keyboard focus.
function TryALesson() {
  const navigate = useNavigate();
  return (
    <button
      onClick={() => { track(EVENTS.LANDING_CTA, { action: 'try_a_lesson' }); navigate('/roadmaps/dsa/learn/merge-sort'); }}
      className="inline-flex items-center justify-center rounded-lg font-sans font-semibold px-6 py-3 text-sm
        bg-[#1E293B] text-white hover:bg-[#0F172A]
        dark:bg-[#EDEDEB] dark:text-[#0F1113] dark:hover:bg-white
        transition-colors"
    >
      Try a lesson
    </button>
  );
}

function Login() {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';

  const handleGoogleLogin = async () => {
    track(EVENTS.LANDING_CTA, { action: 'login' });
    track(EVENTS.SIGNUP_STARTED, { source: 'landing_nav' });
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: window.location.origin },
    });
    if (error) console.error('Error logging in:', error.message);
  };

  // Subject-neutral breadth row — quiet proof the method isn't code-only.
  const subjects = ['DSA', 'Python', 'SQL', 'System Design', 'Aptitude', 'Core CS'];

  // FSRS cadence (illustrative): review milestones plotted on the retention graph.
  const milestones = [
    { x: 38,  dotY: 30, day: 'Day 0',   label: 'Learn',        delay: 1.2 },
    { x: 96,  dotY: 34, day: 'Day 1',   label: 'First recall', delay: 1.9 },
    { x: 186, dotY: 36, day: 'Day 7',   label: 'Review',       delay: 2.7 },
    { x: 266, dotY: 38, day: 'Day 15+', label: 'Mastered',     delay: 3.5 },
  ];

  // Sawtooth that flattens: decay -> review resets it -> shallower decay. The
  // shape IS spaced repetition; the muted grey curve is what happens without it.
  const retainPath =
    'M 38 30 C 55 58, 75 78, 94 88 L 96 34 C 124 46, 154 56, 184 64 L 186 36 C 212 43, 238 48, 264 52 L 266 38 C 287 40, 308 42, 328 43';
  const forgetPath =
    'M 38 30 C 58 78, 88 128, 122 152 C 152 172, 190 180, 230 182 L 328 184';

  const features = [
    { n: '01', title: 'Capture', body: 'Log a topic in seconds — or let the Companion extension capture what you study.' },
    { n: '02', title: 'Review', body: 'Short sessions, ordered by how soon you’d forget.' },
    { n: '03', title: 'Recall', body: 'Answer before the reveal — real recall, not recognition.' },
    { n: '04', title: 'Retain', body: 'Intervals stretch out automatically as it sticks.' },
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
    // Hold the reveal frame longer so the predict -> answer beat lands.
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

  // Cobalt accent is brightened for dark backgrounds (not a literal inversion
  // of the light value) — see docs/DECISIONS.md.
  const accent = isDark ? '#5B9DF9' : '#2563EB';

  return (
    <div className="min-h-screen w-full bg-[#FBFBFA] dark:bg-[#0F1113] transition-colors">
      <div className="max-w-[1280px] mx-auto px-5 md:px-10 lg:border-x lg:border-[#E5E5E2] dark:lg:border-white/10">

        {/* ---------- Top nav ---------- */}
        <nav className="flex items-center justify-between py-6">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center border border-[#E5E5E2] dark:border-white/10">
              <Logo variant={isDark ? 'light' : 'dark'} className="h-5 w-auto" />
            </div>
            <span className="font-sans text-[1.05rem] font-semibold text-[#18181B] dark:text-[#EDEDEB] tracking-tight">RetainHQ</span>
          </div>
          <div className="flex items-center gap-6">
            <a href="#learn" className="hidden sm:block font-sans text-sm text-[#71717A] dark:text-[#9A9CA3] hover:text-[#18181B] dark:hover:text-[#EDEDEB] transition-colors">Features</a>
            <a href="#how" className="hidden sm:block font-sans text-sm text-[#71717A] dark:text-[#9A9CA3] hover:text-[#18181B] dark:hover:text-[#EDEDEB] transition-colors">How it works</a>
            <button
              type="button"
              aria-label="Toggle dark mode"
              onClick={toggleTheme}
              className="w-8 h-8 rounded-lg border border-[#E5E5E2] dark:border-white/15 flex items-center justify-center text-[#71717A] dark:text-[#9A9CA3] hover:text-[#18181B] dark:hover:text-[#EDEDEB] hover:bg-[#F4F4F1] dark:hover:bg-white/5 transition-colors"
            >
              {isDark ? <Moon size={14} /> : <Sun size={14} />}
            </button>
            <button
              onClick={handleGoogleLogin}
              className="font-sans text-sm font-medium text-[#18181B] dark:text-[#EDEDEB] border border-[#E5E5E2] dark:border-white/15 hover:bg-[#F4F4F1] dark:hover:bg-white/5 rounded-lg px-4 py-2 transition-colors"
            >
              Log in
            </button>
          </div>
        </nav>

        <main>
          {/* ---------- Hero ---------- */}
          <section className="grid lg:grid-cols-2 gap-12 lg:gap-10 items-center pt-10 md:pt-16 pb-12">
            <div>
              <p className="font-mono text-[11px] uppercase tracking-widest text-[#71717A] dark:text-[#9A9CA3] mb-4">
                A note on memory &mdash; for engineers
              </p>
              <h1 className="hero-reveal font-sans text-4xl md:text-5xl font-semibold text-[#18181B] dark:text-[#EDEDEB] tracking-tight leading-[1.08] mb-5">
                Stop watching tutorials you{' '}
                <span style={{ color: accent }}>forget by Friday.</span>
              </h1>
              <p className="hero-reveal font-sans text-[#45474C] dark:text-[#9A9CA3] text-base leading-relaxed mb-7 max-w-md" style={{ animationDelay: '140ms' }}>
                RetainHQ is a spaced-repetition system for engineers. Learn from step-through lessons, then short reviews return right before you&rsquo;d forget &mdash; so it stays.
              </p>

              <div className="hero-reveal mb-7" style={{ animationDelay: '280ms' }}>
                <TryALesson />
              </div>

              {/* Subject-neutral breadth row — the method, not a single subject */}
              <div className="hero-reveal flex flex-wrap items-center gap-2" style={{ animationDelay: '420ms' }}>
                {subjects.map((s) => (
                  <span
                    key={s}
                    className="font-mono text-[11px] text-[#71717A] dark:text-[#9A9CA3] border border-[#E5E5E2] dark:border-white/10 rounded px-2 py-1"
                  >
                    {s}
                  </span>
                ))}
              </div>
            </div>

            {/* Right — the one elevated card on the page: the retention figure */}
            <div ref={graphRef} className="rounded-lg bg-white dark:bg-[#17191C] border border-[#E5E5E2] dark:border-white/10 shadow-sm p-6">
              <div className="flex items-center justify-between mb-1">
                <span className="font-mono text-[10px] uppercase tracking-widest text-[#71717A] dark:text-[#9A9CA3]">Fig 01</span>
              </div>
              <h2 className="font-sans text-sm font-semibold text-[#18181B] dark:text-[#EDEDEB] mb-4">
                How a topic sticks
              </h2>

              <svg key={graphRun} viewBox="0 0 340 212" className={`w-full h-auto ${graphPlay ? 'rg-play' : ''}`} role="img" aria-label="Graph: memory decays without reviews, but each spaced review resets it and the curve flattens until the topic is mastered">
                {/* axes */}
                <line x1="34" y1="188" x2="330" y2="188" stroke="currentColor" className="text-[#E5E5E2] dark:text-white/10" strokeWidth="1" />
                <text x="30" y="33" textAnchor="end" fill="currentColor" className="text-[#71717A] dark:text-[#9A9CA3]" fontSize="8" fontFamily="monospace">100%</text>
                <text x="30" y="187" textAnchor="end" fill="currentColor" className="text-[#71717A] dark:text-[#9A9CA3]" fontSize="8" fontFamily="monospace">0%</text>

                {/* day labels */}
                {milestones.map((m) => (
                  <text
                    key={m.day}
                    x={m.x} y="202" textAnchor="middle"
                    fill="currentColor" className="rg-fade text-[#71717A] dark:text-[#9A9CA3]" fontSize="9" fontFamily="monospace"
                    style={{ '--rg-delay': '0.5s' }}
                  >
                    {m.day}
                  </text>
                ))}

                {/* the problem: unaided forgetting curve */}
                <path
                  d={forgetPath} pathLength="1"
                  fill="none" stroke="currentColor" className="rg-curve text-[#A1A1AA] dark:text-[#5A5D63]" strokeWidth="1.5" strokeLinecap="round"
                  style={{ '--rg-dur': '1.6s', '--rg-delay': '0.4s' }}
                />
                <text x="326" y="176" textAnchor="end" fill="currentColor" className="rg-fade text-[#71717A] dark:text-[#9A9CA3]" fontSize="9" fontFamily="sans-serif" style={{ '--rg-delay': '2s' }}>
                  without reviews
                </text>

                {/* the product: spaced reviews reset the curve */}
                <path
                  d={retainPath} pathLength="1"
                  fill="none" stroke={accent} strokeWidth="2" strokeLinecap="round"
                  className="rg-curve" style={{ '--rg-dur': '2.8s', '--rg-delay': '1.1s' }}
                />
                <text x="326" y="78" textAnchor="end" fill={accent} fontSize="9" fontWeight="600" fontFamily="sans-serif" className="rg-fade" style={{ '--rg-delay': '4s' }}>
                  with RetainHQ
                </text>

                {/* review pings + milestone labels */}
                {milestones.map((m, i) => (
                  <g key={m.label}>
                    {i > 0 && (
                      <circle cx={m.x} cy={m.dotY} r="5" fill="none" stroke={accent} strokeWidth="1.5" className="rg-halo" style={{ '--rg-delay': `${m.delay + 2.2}s` }} />
                    )}
                    <circle
                      cx={m.x} cy={m.dotY} r="4"
                      fill={accent} stroke={isDark ? '#17191C' : '#FFFFFF'} strokeWidth="1.5"
                      className="rg-dot" style={{ '--rg-delay': `${m.delay}s` }}
                    />
                    <text
                      x={m.x} y={m.dotY - 12} textAnchor="middle"
                      fill="currentColor" className={`rg-fade ${i === milestones.length - 1 ? '' : 'text-[#45474C] dark:text-[#C9CBCF]'}`} fontSize="9" fontWeight="600" fontFamily="sans-serif"
                      style={i === milestones.length - 1 ? { color: accent, '--rg-delay': `${m.delay + 0.1}s` } : { '--rg-delay': `${m.delay + 0.1}s` }}
                    >
                      {m.label}
                    </text>
                  </g>
                ))}
              </svg>

              <p className="border-t border-[#E5E5E2] dark:border-white/10 mt-1 pt-3 font-sans text-[11px] text-[#71717A] dark:text-[#9A9CA3]">
                Illustrative &mdash; your intervals adapt to how well you actually recall.
              </p>
            </div>
          </section>

          {/* ---------- Showcase: see it execute ---------- */}
          <section id="learn" className="scroll-mt-8 py-14 md:py-20 border-t border-[#E5E5E2] dark:border-white/10">
            <div className="mb-8 max-w-xl">
              <p className="font-mono text-[11px] uppercase tracking-widest text-[#71717A] dark:text-[#9A9CA3] mb-3">
                Interactive execution
              </p>
              <h2 className="font-sans text-2xl md:text-3xl font-semibold text-[#18181B] dark:text-[#EDEDEB] tracking-tight mb-3">Learn the trace, not just the syntax.</h2>
              <p className="font-sans text-[#45474C] dark:text-[#9A9CA3] leading-relaxed">
                Most tutorials show you finished code. RetainHQ runs it &mdash; scrub line by line, watch the variables change, and guess the output <span className="text-[#18181B] dark:text-[#EDEDEB] font-medium">before</span> you reveal it.
              </p>
            </div>

            <div className="rounded-lg bg-white dark:bg-[#17191C] border border-[#E5E5E2] dark:border-white/10 overflow-hidden">
              {/* honest label bar — no fake OS window chrome */}
              <div className="flex items-center justify-between px-4 py-2.5 border-b border-[#E5E5E2] dark:border-white/10">
                <span className="font-mono text-[11px] text-[#71717A] dark:text-[#9A9CA3]">running_total.py &mdash; step {traceStep + 1} of {traceSteps.length}</span>
              </div>

              <div className="grid md:grid-cols-[1.5fr_1fr]">
                {/* code — current line highlighted, like the step scrubber */}
                <div className="p-5 font-mono text-[13px] leading-[1.7] border-b md:border-b-0 md:border-r border-[#E5E5E2] dark:border-white/10 overflow-x-auto">
                  {codeLines.map((line, i) => (
                    <div
                      key={i}
                      className={`flex gap-3 px-2 -mx-2 rounded transition-colors duration-300 border-l-2 ${
                        i === activeLine ? 'bg-[#2563EB]/[0.08] dark:bg-[#5B9DF9]/[0.12]' : 'border-transparent'
                      }`}
                      style={i === activeLine ? { borderLeftColor: accent } : undefined}
                    >
                      <span className="text-[#A1A1AA] dark:text-[#5A5D63] select-none w-4 text-right shrink-0">{i + 1}</span>
                      <span className={`whitespace-pre ${i === activeLine ? 'text-[#18181B] dark:text-[#EDEDEB]' : 'text-[#45474C] dark:text-[#9A9CA3]'}`}>{line || ' '}</span>
                    </div>
                  ))}
                </div>

                {/* live state + predict-before-reveal */}
                <div className="p-5">
                  <div className="font-mono text-[10px] uppercase tracking-widest text-[#71717A] dark:text-[#9A9CA3] mb-3">Variables now</div>
                  <div className="space-y-2 mb-5 min-h-[52px]">
                    {traceState.length === 0 && (
                      <div className="font-mono text-xs text-[#A1A1AA] dark:text-[#5A5D63]">&mdash; no variables yet</div>
                    )}
                    {traceState.map((v) => (
                      <div key={v.name} className="flex items-center justify-between font-mono text-xs">
                        <span className="text-[#71717A] dark:text-[#9A9CA3]">{v.name}</span>
                        <span
                          className="rounded px-2 py-0.5 border transition-colors duration-300 text-[#18181B] dark:text-[#EDEDEB] border-[#E5E5E2] dark:border-white/10"
                          style={v.changed ? { color: accent, borderColor: accent, backgroundColor: isDark ? 'rgba(91,157,249,0.1)' : 'rgba(37,99,235,0.08)' } : undefined}
                        >
                          {v.value}
                        </span>
                      </div>
                    ))}
                  </div>

                  <div className="rounded-lg border p-3" style={{ borderColor: isDark ? 'rgba(91,157,249,0.3)' : 'rgba(37,99,235,0.2)', backgroundColor: isDark ? 'rgba(91,157,249,0.06)' : 'rgba(37,99,235,0.05)' }}>
                    <p className="font-sans text-[11px] font-semibold mb-2" style={{ color: accent }}>Predict before reveal</p>
                    <div className="flex items-center justify-between font-mono text-xs">
                      <span className="text-[#71717A] dark:text-[#9A9CA3]">running_total(2)</span>
                      <span
                        className="rounded px-2 py-0.5 border transition-colors duration-300"
                        style={revealed
                          ? { color: accent, borderColor: accent, backgroundColor: isDark ? 'rgba(91,157,249,0.15)' : 'rgba(37,99,235,0.12)', fontWeight: 600 }
                          : { color: '#71717A', borderColor: 'transparent' }}
                      >
                        {revealed ? '= 1' : '= ?'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* ---------- Editorial pull-quote ---------- */}
          <blockquote className="border-l-2 pl-8 py-2 my-4 max-w-2xl" style={{ borderColor: accent }}>
            <p className="font-sans text-2xl md:text-3xl font-normal leading-snug text-[#18181B] dark:text-[#EDEDEB]">
              &ldquo;Most tutorials show you finished code. We show you the thirty seconds where it actually clicks.&rdquo;
            </p>
          </blockquote>

          {/* ---------- Features / How it works ---------- */}
          <section id="how" className="scroll-mt-8 py-14 md:py-20 border-t border-[#E5E5E2] dark:border-white/10">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8 lg:gap-6">
              {features.map((f) => (
                <div key={f.title} className="border-t border-[#E5E5E2] dark:border-white/10 pt-4">
                  <span className="font-mono text-xs text-[#A1A1AA] dark:text-[#5A5D63]">{f.n}</span>
                  <h3 className="font-sans text-base font-semibold text-[#18181B] dark:text-[#EDEDEB] mt-2 mb-1.5">{f.title}</h3>
                  <p className="font-sans text-sm text-[#45474C] dark:text-[#9A9CA3] leading-relaxed">{f.body}</p>
                </div>
              ))}
            </div>
          </section>

          {/* ---------- Closing CTA ---------- */}
          <section className="flex flex-col items-center text-center gap-4 py-16 border-t border-[#E5E5E2] dark:border-white/10">
            <h2 className="font-sans text-2xl md:text-3xl font-semibold text-[#18181B] dark:text-[#EDEDEB] tracking-tight max-w-md">
              Build knowledge that outlasts the sprint.
            </h2>
            <p className="font-sans text-[#45474C] dark:text-[#9A9CA3] text-sm">Free to start. Learn it once, still know it when the interview comes.</p>
            <div className="mt-2">
              <TryALesson />
            </div>
          </section>
        </main>

        {/* ---------- Colophon footer ---------- */}
        <footer className="border-t border-[#E5E5E2] dark:border-white/10 py-10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <span className="font-sans text-sm font-semibold text-[#18181B] dark:text-[#EDEDEB]">RetainHQ</span>
            <p className="font-sans text-xs text-[#71717A] dark:text-[#9A9CA3] mt-1">
              Built by a solo engineer, for engineers who want it to actually stick.
            </p>
          </div>
          <div className="flex items-center gap-5">
            <a href="#learn" className="font-mono text-[11px] text-[#71717A] dark:text-[#9A9CA3] hover:text-[#18181B] dark:hover:text-[#EDEDEB] transition-colors">Features</a>
            <a href="#how" className="font-mono text-[11px] text-[#71717A] dark:text-[#9A9CA3] hover:text-[#18181B] dark:hover:text-[#EDEDEB] transition-colors">How it works</a>
            <Link to="/privacy/companion" className="font-mono text-[11px] text-[#71717A] dark:text-[#9A9CA3] hover:text-[#18181B] dark:hover:text-[#EDEDEB] transition-colors">Privacy</Link>
            <span className="font-mono text-[11px] text-[#A1A1AA] dark:text-[#5A5D63]">&copy; {new Date().getFullYear()} RetainHQ</span>
          </div>
        </footer>
      </div>
    </div>
  );
}

export default Login;
