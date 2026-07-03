# RetainHQ Design Bible — DRAFT v0.1 (for discussion)

> Status: **derived from the shipped codebase, not yet agreed.** This is the Design Lead audit:
> what the product already believes, stated explicitly, plus every place the pixels contradict
> the philosophy. Argue with it. Nothing here is implemented until we align.
>
> Method: full read of `index.css`, `tailwind.config.js`, `index.html`, `App.jsx`, `Home.jsx`,
> `Review.jsx`, `Login.jsx`, `LogActivity.jsx`; product context from CLAUDE.md and prior
> strategy discussions. Remaining screens (Roadmaps, LessonView, Vault, Analytics, Profile)
> get audited screen-by-screen during implementation against this document.

---

## 01 — What the code already believes

The codebase is not a blank slate. Reading it as a design artifact, a philosophy is already
half-formed — and most of it is good:

- **Warm paper, ink, one accent.** Light mode is `#f9f9f6` (warm paper, not sterile white),
  near-black slate ink (`#0F172A`), and a single cyan accent (`#0891B2`) reserved for action
  and identity. Hairline borders at 5–15% opacity do the separation work — almost no shadows.
- **One elevated element per page.** Home's code comments say it outright: *"Recent Captures —
  a naked list (no card) so the due-review card stays the only elevated element on the page"*,
  *"stats stay quiet."* Focus is engineered by subtraction.
- **Mono is the data voice.** `font-mono` is used semantically: counters (`3 / 10`), dates,
  due labels, keyboard hints, percentages. Prose is sans; *measurements* are mono. This is the
  "instrument" register — the Bloomberg note — and it's already consistent.
- **Editorial micro-labels.** 11px bold uppercase tracked-out section labels (`KEY MEMORY`,
  `RECALL`, `AI FEEDBACK`) structure every screen. Distinctive and consistently applied.
- **Motion is restrained and has a signature.** One curve appears everywhere:
  `cubic-bezier(0.22, 1, 0.36, 1)` (a fast-out ease), durations 150–400ms, entrances are
  small fades/slides (8–12px). Skeletons shimmer instead of pulse and respect
  `prefers-reduced-motion`. Nothing bounces. Nothing loops for attention.
- **The copy is a coach, not a cheerleader.** *"Honest beats optimistic."* *"Pulling it from
  memory is the workout."* *"No invented stats, no claim of an 'optimal' curve"* (a literal
  code comment). The product explains its mechanism instead of hyping outcomes. This voice is
  the strongest design asset RetainHQ has.
- **Respect for the user's hands.** Keyboard shortcuts on the review flow (Ctrl+Enter, 1–4),
  a one-click "I don't know" (the failure path costs *less*, not more), drafts that survive
  OAuth redirects, sections that paint independently instead of waiting on the slowest fetch.
  These are tool-maker decisions, not app-maker decisions.
- **Anti-fatigue by architecture.** Session cap of 10, "Today's review · N cards · ~M min"
  framing, first review deferred to tomorrow with an honest explanation of why. The system
  itself is designed to be calm.

**Derived thesis: RetainHQ's design language is a *calm precision instrument* — a warm-paper
editorial surface with a terminal's honesty.** Not a gamified app, not enterprise chrome, not
Dribbble glass. The product measures memory; the interface should feel like a well-made
measuring instrument: quiet, exact, trustworthy, pleasant to hold.

---

## 02 — The Philosophy, stated explicitly

### Emotional goals (in priority order)
1. **Trust** — the user believes the numbers and the schedule. Earned by honest copy, visible
   mechanism ("here's *why* tomorrow"), and visual precision (aligned, consistent, exact).
2. **Calm competence** — using RetainHQ feels like being organized, never like being behind.
   The backlog is capped, the queue is finishable, due reviews are an *invitation*, not an alarm.
3. **Earned satisfaction** — the good feeling comes from real recall, not from confetti. The
   interface acknowledges wins in proportion: quiet check, one warm sentence, next.
4. **Focus** — one primary action per screen, engineered by keeping everything else quiet.

### Personality
**A precise, honest coach.** Knows the science, explains it in one sentence, never inflates.
If RetainHQ were a person: a senior engineer who mentors well — direct, warm, zero hype.
It is explicitly **not**: a mascot, a game, a dashboard vendor, or a productivity guilt engine.

### Visual principles
1. **Paper + ink + one accent.** Warm paper surfaces, slate ink, cyan for action/identity.
   Every additional hue must earn a *semantic job* (see §05) or it doesn't exist.
2. **Hairlines over shadows.** Separation by 1px borders and background steps, not elevation.
   Elevation is rationed: at most one elevated card per screen (already the Home rule — now law).
3. **Mono = measurement.** Numbers, dates, intervals, counts, code, keyboard hints. Never prose.
4. **Uppercase micro-labels structure the page.** 11px/bold/tracked. They are the wayfinding
   system; body text never shouts.
5. **Density with breathing room.** This is a desktop tool for developers — comfortable but not
   airy-marketing-page. Information earns space by importance, not by decoration.
6. **Dark mode is a first-class citizen, derived from tokens** — never a per-screen afterthought.

### Interaction philosophy
1. **The keyboard is a first-class input.** Every high-frequency loop (review, log) fully
   drivable without the mouse, with visible hints.
2. **Failure paths cost less than success paths.** "I don't know" is one click. Errors state
   what happened in plain words and keep the user's work.
3. **Motion explains, never performs.** One signature curve, 150–300ms, always tied to a state
   change the user caused. If a screen is idle, nothing moves (skeletons excepted).
4. **Never block on the network.** Paint sections independently, keep drafts, degrade gated
   features silently (the grader-off fallback pattern is the template).
5. **Acknowledge effort in proportion.** Completing a session earns one warm, specific sentence
   — not a celebration screen. The reward is the mechanism working, and the copy says so.

---

## 03 — Audit findings: where the pixels contradict the philosophy

Ordered by severity. Each: what I found → why it matters → recommendation.

### F1 · The fonts don't exist. **(critical, invisible until you look)**
`tailwind.config.js` declares Inter + JetBrains Mono; `index.css` styles reference
`'Inter', system-ui`. **Neither font is loaded anywhere** — no Google Fonts link, no
`@fontsource` package, no `@font-face`. The entire product currently renders in Segoe UI on
Windows and Helvetica/SF on Mac; "mono" falls to Consolas/Menlo. The typography identity is
fiction — every user sees a different product, and none see the intended one.
**Recommendation:** self-host Inter (variable) + JetBrains Mono via `@fontsource-variable`,
preloaded. This is the single highest-leverage perceived-quality fix available; it changes
every pixel of text at once. (Whether Inter is the *right* face is an open question — §06 Q1 —
but loading *a* deliberate face beats shipping the OS default lottery.)

### F2 · Three design languages are competing. **(critical)**
- **Kinetic** (the majority): 4px radius, flat paper, hairlines, mono data — the instrument.
- **Glass/aurora** (roadmap cards, nav): 16px radius, backdrop blur, cyan+**purple** radial
  glows — Apple-consumer softness.
- **Landing** (`Login.jsx`): dark `#0B1120`, glow blurs, `rounded-full` gradient pill CTAs,
  a *fourth* cyan (`#22D3EE`) — modern dev-tool marketing.

The landing being its own world is defensible (marketing ≠ app), and its dark dev-tool
aesthetic actually matches the thesis *better than the app does*. But **inside the app**,
kinetic and glass disagree about what RetainHQ is, and the disagreement reads as inconsistency,
not range. **Recommendation:** pick the instrument. Keep glass *only* on navigation chrome
(sidebar/bottom nav — where "floating over content" is the honest metaphor), retire
`.glass-card` + `.aurora` from content surfaces, and fold the landing's best ideas (the
confident dark, the mono mechanism strip) into the system rather than quarantining them.

### F3 · Border radius has no system. **(high)**
Found in active use: 4px (kinetic-card/btn), `rounded` (4px), 6, 8, 10 (`rounded-lg` variants),
12 (`rounded-xl`, onboarding), 14 (icon rings), 16 (glass), plus `rounded-full` pills — chosen
per-component by feel. Radius is one of the strongest subconscious personality signals
(sharp = precise, round = friendly), and right now RetainHQ's personality wobbles per element.
**Recommendation:** a 3-step scale — **4px** (inputs, buttons, chips: the working surfaces),
**8px** (cards, callouts, modals), **full** (badges/pills only). Nothing else. The 4px working
surface is what keeps the "precision" read.

### F4 · Due reviews are styled as emergencies. **(high — this one is philosophical)**
The due-count badge is **alarm red** (`#ba1a1a`) in both navs; Home's top card is headed
`HIGHEST PRIORITY REVIEW` in red bold uppercase; the due stat turns red under `emphasis`.
The scheduling *architecture* was redesigned to kill review anxiety (cap, roll-forward,
"finishable session" framing) — and then the *color system* re-installs the anxiety: red is
error/danger in this very codebase (`--color-error: #ba1a1a`). A due review is the product
working as designed; it's the core loop's *invitation*.
**Recommendation:** due state = **cyan** (the action color), full stop. Red appears only for
errors and destructive actions. Rename the label (`UP FOR REVIEW` or `DUE TODAY`). Overdue
copy ("Overdue 3 days") stays honest but doesn't need to be dressed as a fire.

### F5 · Color roles have drifted. **(medium)**
Two reds coexist (`#ba1a1a` tokens/errors vs `#B91C1C` outcome/danger); success is sometimes
`#166534` (green) and sometimes `#0F766E` (teal — which is *also* the "Easy" outcome color);
`#22D3EE` is a landing-only cyan; purple `#8B5CF6` appears as AI-suggestion accent (capture
assist, related subtopics), as "coming soon" badge, *and* as decorative aurora — three
unrelated jobs. **Recommendation:** one hue per job, tokenized: ink, paper, **cyan = action**,
**red = error/missed**, **amber = caution/hard**, **teal = success/easy**, **purple = AI only**
(it's a good, ownable choice for the advisory-AI layer — but then it must stop moonlighting as
decoration and "coming soon" chrome). Exact values fixed in the token table when we implement.

### F6 · The token layer exists but components don't use it. **(medium, debt)**
`:root` defines CSS variables; ~280 call sites hardcode hexes; dark mode works by remapping
each literal class under `html.dark` — clever, documented, and load-bearing, but it means
every new component must reuse the *exact literal strings* or silently break dark mode, and a
palette change means find-and-replace across the app. **Recommendation:** during the restyle,
migrate surfaces/text/borders to semantic Tailwind tokens (`bg-surface`, `text-ink`,
`border-hairline`, …) backed by the CSS variables that already exist. The override layer then
shrinks instead of growing with every feature. This is the mechanical bulk of implementation —
do it screen-by-screen, not big-bang.

### F7 · The landing promises a product the app doesn't visually deliver. **(medium)**
Landing: dark, code-forward, execution traces, "built by people who read code." First
post-login paint: warm paper, GraduationCap icons, roadmap cards with purple auroras — a
pleasant *study planner*. Neither is wrong; the cut between them costs first-impression trust
(the "is this the same product?" flicker at the exact moment a new user judges hardest).
**Recommendation:** don't darken the app to match; *sharpen* it (F2–F5 do most of this) and
carry two landing signatures inside: the mono mechanism strip and the code-trace visual
identity, which the DSA player already provides. Worth checking activation data for
theme-preference signal, but this is primarily fixed by coherence, not theme.

### F8 · Small honesty leaks in an otherwise honest interface. **(low)**
- `PartyPopper` icon on session completion — the one confetti-adjacent moment in a product
  that promises earned satisfaction. The *copy* next to it is perfect ("that's what builds
  long-term memory"); the icon undercuts it. Swap for the quiet check.
- Landing timeline shows "Day 7 → Day 15+" for an FSRS schedule that adapts (the code comment
  admits it's "illustrative") — borderline; fine if visibly framed as an example.
- `alert()` for feedback-modal errors (Home.jsx) — a browser artifact inside a designed product.

### What is explicitly *not* broken (don't fix)
Spacing (consistent 4/8-based rhythm), the skeleton system, the voice/copy, keyboard
interaction model, the one-elevated-element rule, the hint system, independent section
loading, reduced-motion handling. These are the foundation the philosophy was derived *from*.

---

## 04 — The system (to be finalized post-alignment)

Locked-in direction, exact values at implementation:

| Layer | Rule |
|---|---|
| Type | Inter Variable (UI) + JetBrains Mono (data), actually loaded; scale ~12/14/16/20/24/30 with mono sizes one step down |
| Color | Semantic tokens only (§F5 roles); components never hardcode hexes again |
| Radius | 4 / 8 / full |
| Space | 4px base; section rhythm 24/32; page gutters 16/32 (matches current p-4/p-8) |
| Elevation | Hairlines; ≤1 elevated card per screen; shadows only on overlays (modal, FAB, expanded nav) |
| Motion | One curve `cubic-bezier(0.22,1,0.36,1)`; 150ms hover / 200ms state / 300ms enter; no idle motion |
| Dark | Derived from the same tokens; override layer frozen and shrinking |

## 05 — Color semantics (roles, not values)

| Role | Job | Never |
|---|---|---|
| Ink / Paper | text / surfaces | — |
| Cyan | action, identity, **due reviews**, progress | body text |
| Red | errors, destructive, "Missed it" | due counts, badges-by-default |
| Amber | caution, "Hard" | decoration |
| Teal | success, "Easy" | doubling as generic green |
| Purple | AI advisory layer only | aurora decoration, "coming soon" chrome |

## 06 — Decisions (resolved 2026-07-02, optimizing for user retention)

1. **Typeface: IBM Plex Sans + JetBrains Mono (decided 2026-07-03, design-lead call after
   founder delegated).** Inter was rejected by founder review. Plex chosen for its
   instrument/engineering character vs generic-SaaS Inter, small-size quality, and mono
   pairing. Cheap to reverse (one-line stack change) if the live app feels wrong.
2. **Glass: navigation chrome only** (sidebar + bottom nav, where content genuinely scrolls
   under it). `.glass-card` and `.aurora` retired from content surfaces.
3. **Due reviews stay RED — founder veto of the cyan proposal (2026-07-02).** Red is kept for
   due badges/labels alongside its error/destructive/"Missed it" roles. Revisit ONCE only if
   the deep-research run returns strong evidence that alarm-colored due framing drives
   avoidance; otherwise settled.
4. **Purple = AI advisory layer, exclusively.** One legible rule — "purple means the AI is
   suggesting, you decide" — builds trust in the grader/assist features. Purple's other jobs
   ("coming soon" chrome, aurora decoration) end.
5. **Landing dark / app paper stays a deliberate two-world split.** Retention lives inside the
   app; the trust gap closes via coherence (F2–F5), not a theme change.

6. **Landing (2026-07-03):** decluttered PROPOSED variant approved, with founder flag "reads
   as solely a coding platform" → fix is a quiet mono breadth-chip row (DSA · Aptitude ·
   Core CS · SQL · System Design · Python) under the CTAs, not more prose. Code demo stays
   the hook.
7. **Resume-lesson card: APPROVED** — implement on Home, deep-linking to the next unfinished
   content-bearing node of the top in-progress roadmap. Fail silent when no target exists.
8. **Home direction (founder, 2026-07-03): minimal text, visual-first.** Information conveyed
   by number, ring, grid, and bar — text only as labels. Full-layout mock goes through the
   Claude Design review gate before implementation.

## 06b — Deep-research verdicts (2026-07-03, full report: `docs/research-motivation.md`, headroom hash `b2323fba5e52a13c9fd6a421`)

Shipped decisions validated (Strong evidence): daily cap of 10 ("retain it", explicitly);
one-click "I don't know" (Productive Failure); no XP/leaderboards/loss-framed streaks
(Overjustification + What-the-Hell effects); quiet no-confetti completion; deferred first
review (consistent, not directly studied). **Due-badge red: report is silent on color —
founder's red decision is final** (its evidence targets backlog *size/framing*, already
solved by the cap).

Adopted refinements (evidence-graded, queued for implementation):
- Queue framed as progress ("0/10 complete"), never a bare due-count integer (Zeigarnik, Strong).
- Roll-forward prioritizes most at-risk cards, not oldest-first (report Tension 2 resolution).
- Heatmap codes single missed days neutrally — never a broken chain (habit-lapse evidence, Strong).
- Session-complete payoff = real ipsative retention delta ("projected to hold 45 days"), data
  not praise (Overjustification, Strong). Replaces PartyPopper (confirms F8).
- Long-gap re-entry: same 10-card cap regardless of absence + "recoverable, not lost" coaching
  copy (Bjork storage/retrieval strength); never a debt count.
- Future (backend): confidence-aware AI grading — elaborate hardest on confident misses
  (Hypercorrection, Strong). Optional middle path to consider later: non-punitive "Two-Day
  Rule" consistency signal.

**RESOLVED (design-lead call, founder-delegated, 2026-07-03):** adopt the report's
recommendation — the failed-recall moment loses red entirely. "Missed it" outcome button =
neutral slate (a miss is information, not an error); "Previous Mistake" callout = amber
caution voice. Red remains only for true errors/destructive actions and the due badge
(founder decision). Home mock APPROVED (founder, same date) with additions: all sections
must render meaningful empty states for new users; due ring reads "0/N" + "Start"
(→ "Continue" after first completion); brand-new users get "Log your first activity" in the
due-card slot. Landing positioning: subject-neutral "unique learning system" copy — sell the
method (visual lessons, recall-before-reveal, spaced repetition), never code-only.

## 07 — Implementation order (after alignment + deep-research pass)

1. Fonts (F1) + Tailwind semantic tokens (F6 foundation) — one PR, app-wide effect.
2. Color-role cleanup (F4, F5) — due-state recolor is a ~10-line, high-impact change.
3. Radius + card-language consolidation (F2, F3) screen-by-screen: Review → Home → Log →
   Roadmaps → Vault → Analytics → Profile (thesis-critical screens first).
4. Detail pass (F8) + per-screen audits of the screens not yet read (LessonView, RoadmapDetail).
5. Fold in deep-research findings (motivation/anxiety evidence) → revise §02 emotional goals
   and the Review experience if the evidence disagrees with us.
