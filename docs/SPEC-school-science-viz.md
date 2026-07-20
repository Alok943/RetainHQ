# SPEC — School Science Sim Runtime + Class-wise IA

**Written:** 2026-07-17. Companion to `docs/PLAN-school-maths-runtime.md` (maths runtime; shares the
enforcement/verified-memory competitive frame in its §1 — read that first, it is not repeated here)
and `docs/PLAN-lesson-generation.md` (content priority). This is the RUNTIME + IA spec for physics
and chemistry visual simulations, Classes 9–12. Content generation starts only after the engine
contracts here are hardened (same rule as the maths runtime).

**Founder decisions locked (2026-07-17):**
1. IA: separate section per **class** (9/10/11/12), subject-wise roadmaps inside each (Physics, Chemistry, Maths…).
2. Flagship: **Light — Class 10 AND Class 12 (Ray Optics)**, both to full quality bar.
3. Engines parameterized for 11–12 depth from day one; 9–10 ships first + Class-12 Light as the stretch proof.
4. No pitch deadline — sequence by dependency, quality first.

---

## 0. The bar: "product, not project"

A sim is a *project* when every lesson hand-rolls its own SVG with its own controls. It is a
*product* when:

- **One chrome.** Every sim sits in the same `SimFrame` (title, control strip, reset, cases
  quick-select, fullscreen). A student who used one sim knows every sim.
- **One grammar.** Predict → manipulate → measure → recall. Interaction never starts before a
  prediction is made (same predict-gate contract as DerivationPlayer/GraphPlay).
- **Phone-first, portrait-first.** ~99% of school students have ONLY a phone (founder call,
  2026-07-17 — this inverts the DSA desktop-first default). The design canvas is **360×640 CSS px
  portrait on a cheap Android**; desktop and smartboard are the scaled-UP cases, never the other
  way around. Concretely:
  - Sim canvas is sized for portrait width; controls/readouts stack **below** the canvas as chips,
    never beside it.
  - **Aspect contract (founder call, 2026-07-17):** every engine mode declares its natural aspect —
    `portrait` (fits 360w as-is: snell, prism, graphs), or `wide` (bench-like, needs width:
    mirror/lens bench, combos, circuits). `wide` modes in a portrait viewport render a compact
    still-usable bench PLUS a prominent "Rotate for the full bench ↻" chip; on rotation the
    SimFrame goes fullscreen-landscape (Android Chrome: fullscreen + `screen.orientation.lock('landscape')`;
    iOS Safari supports neither — fall back to detecting the physical rotation via resize and
    expanding then). Rotation is invited, never required — the compact portrait bench must still
    pass the browser gate.
  - **Fat-finger grammar:** hit areas ≥ 44px and always larger than the glyph; while dragging, the
    touched element shows a magnified callout offset above the finger (the finger occludes exactly
    what you're manipulating); every draggable also has nudge arrows for precision (doubles as the
    a11y/keyboard path — replaces "sliders as fallback").
  - Readout text ≥ 14px at 360w; no hover-only affordances anywhere (there is no hover on touch).
  - Browser gate runs **mobile viewport first**, desktop second (inverts the DSA gate order).
- **Direct manipulation.** Drag the candle, drag the incident ray — with the fat-finger grammar
  above. Classrooms get a smartboard/projector fullscreen mode with enlarged labels, but it is a
  presentation view of the phone design, not a separate layout.
- **Instant.** Geometry recomputes synchronously on pointer-move. No debounce jank, no spinners.
  SVG node budget < 300 per sim; `requestAnimationFrame` only while something is actually animating;
  `prefers-reduced-motion` disables propagation animations.
- **No dead ends.** Every parameter combination renders something teachable — object at focus shows
  "rays emerge parallel — image at infinity," not NaN coordinates. Edge cases are curriculum, not bugs.
- **Theme-native.** Existing color utility classes only, so the `html.dark` override layer works for
  free. No hardcoded hex inside SVG; use CSS vars/currentColor.

Anti-goal: PhET clone. PhET sims are free, better-funded, and pedagogically inert (isolated toys).
Ours are load-bearing: the sim exists to force a prediction, and the prediction feeds recall cards
into FSRS. The sim inside the loop is the product; the sim alone is a demo.

---

## 1. Information architecture & migration — **M0 EXECUTED 2026-07-17** (D-030)

### 1.1 Target IA — no new hub UI needed (discovery)

**Correction to the original plan:** `frontend/src/SchoolRoadmaps.jsx` already exists and already
implements the Class → Subject → Chapter browser this section originally proposed building. It
parses every roadmap's node `phase` field against the `"Class N · Chapter"` convention (already
authored in `backend/seed_physics_school.py`) and groups roadmaps into class buckets generically —
it was written (2026-07-10, D-006) specifically so future roadmaps would slot in for free as long
as their phases follow that convention. So **the entire IA task was splitting the roadmap identity,
not building a hub** — no `/school` nav/route work was needed.

- **Class → Subject → Chapter browsing:** already shipped, unchanged by this work.
- **Roadmap keys are subject+class:** `physics-9`, `physics-10` (done), `physics-12` (new, M4),
  `chemistry-9`, `chemistry-10` (later), joining the existing `maths-11`. RoadmapDetail/LessonView
  needed only label-map entries, not new components.
- **Hub-page SEO** (static `<title>`/H1 saying "Class 10 Science" per the Trends finding — "class 10
  science" ≈ 5× "class 10 physics" in India, since Science is the CBSE subject name for 9–10) still
  needs its own pass: `SchoolRoadmaps.jsx` is a client-rendered SPA route today, not prerendered
  static HTML like lesson pages, so it currently carries no SEO weight of its own. Prerendering a
  static class-hub page (mirroring `generate-lesson-html.mjs`'s existing hub-page logic) is a
  **follow-up, not blocking M1+** — deferred to M5 (polish) unless it becomes a priority sooner.

### 1.2 Migration of `physics-9-10` (128 lessons) — DONE

Executed as a standalone commit, ahead of and separate from any sim runtime work, per the original
sequencing intent:

- Split by class using `backend/seed_physics_school.py`'s existing `"Class N · Chapter"` phase
  labels (matched **128/128** lesson titles with zero ambiguity — no guesswork needed): 77 lessons
  → `physics-9` (Motion, Force & Laws, Gravitation, Work & Energy, Sound), 51 → `physics-10` (Light,
  Electricity, Magnetic Effects, Eye). **Slugs unchanged.**
- `frontend/vercel.json` gained 129 permanent redirects (128 lesson URLs + the roadmap page itself)
  ahead of the existing SPA rewrite (Vercel always resolves `redirects` before `rewrites`).
- `content/roadmaps/physics-9-10/` → `physics-9/` + `physics-10/`, including `_numericals/` and
  `_test/` (already class-prefixed by filename, e.g. `class-10-light.json` — split was a pure
  filename-prefix sort, no ambiguity).
- `backend/seed_physics_school.py` now seeds two `Roadmap` rows from one shared `NODES` list (split
  at seed time by parsing each node's phase — no content duplication). `physics-10` reuses the
  legacy roadmap UUID so its DELETE-then-insert also retires the old combined row; `physics-9` gets
  a fresh UUID. `seed_physics_school_prereqs.py` splits 140 edges into 132 same-class edges — the
  8 Class 9→10 cross-year edges are **dropped from the DB graph** (documented in that file, listed
  in D-030) because `GET /roadmaps/{id}` resolves prerequisite node IDs strictly within the
  requested roadmap's own node set; a cross-roadmap edge would hand the frontend a prerequisite ID
  with no title/status to show. Reintroducing them needs actual cross-roadmap dependency support in
  the roadmaps API — out of scope here, noted as a real (not accidental) gap.
- **Not yet run against prod:** the reseed is prepared and verified (edge counts, class-consistency,
  no missing titles) but wipes `user_progress` for these roadmaps on every run — same hand-off
  convention as the original seed script ("NOT run yet"), a founder call, not something to trigger
  from an assistant session.
- Verified: `python content/validate.py` clean; `npm run build` → 640 static lesson pages (unchanged
  total), 12 hub pages (was 11 — physics now has two hubs instead of one); the 5 lessons with
  explicit `seo.title` overrides resolve correctly at their new class-scoped URLs; browser-checked
  that `document.title` keeps its value after React mounts at `/roadmaps/physics-10/learn/...` (the
  same title-parity risk as the original P0-B ship).

---

## 2. Sim runtime architecture (`frontend/src/sims/`)

Fourth instance of the proven pattern (DSA trace player, GraphPlay, PGlite/Pyodide): Claude-owned
runtime engines, JSON-configured per lesson, Antigravity scales content against the contract.

```
frontend/src/sims/
  SimFrame.jsx          — shared chrome: title, predict gate, controls strip, reset,
                          cases quick-select, fullscreen, measurement toggle
  registry.js           — { 'ray-optics': { Component, validateParams } , ... }
  engines/
    ray-optics/
      core.js           — PURE geometry/physics functions, zero React, unit-tested
      core.test.mjs     — golden tests (values from NCERT worked examples + our numericals JSON)
      RayOptics.jsx     — SVG renderer + pointer interactions, consumes core.js only.
                          NOT from scratch: frontend/src/physics/RayDiagram.jsx (2026-07-05,
                          240 lines) already computes image position/nature from the mirror/lens
                          formula and renders the static 3-ray SVG, verified on all 8 canonical
                          cases. M1 = extract its math into core.js (+ goldens); M2 = add
                          interactivity (drag/predict/cases) on top. The static `diagram`
                          contract stays for lessons that only need a fixed figure.
    circuits/           — (M4+) same shape
    kinematics/         — thin wrapper: GraphPlay with motion presets (cheapest engine, mostly exists)
    particles/          — (chemistry, M5+) canvas-based; the ONE engine allowed off SVG, for perf
```

### 2.1 Lesson JSON contract

One hero sim per lesson (v1). Top-level optional block on `physics` (and future `chemistry`) kinds:

```json
"sim": {
  "engine": "ray-optics",
  "title": "Concave mirror: image formation",
  "params": { "element": "concave-mirror", "f": 15, "object": { "u": 40, "h": 5 } },
  "predict": {
    "question": "The object sits beyond C. Where does the image form?",
    "options": [
      { "text": "Between F and C — real, inverted, smaller", "correct": true },
      { "text": "Beyond C — real, inverted, larger", "feedback": "That happens when the object is between F and C — try dragging it there after you answer." },
      { "text": "Behind the mirror — virtual, upright", "feedback": "Virtual images need the object inside F. Watch what the reflected rays do here." }
    ]
  },
  "explore_prompts": [
    "Drag the object to exactly F. What happens to the reflected rays?",
    "Find the position where image size equals object size."
  ],
  "cases": ["beyond-C", "at-C", "between-C-F", "at-F", "inside-F"]
}
```

- `predict` shape mirrors the maths-runtime predict block (exactly one `correct: true`, feedback
  required on wrong options) — reuse its validator logic and its UI affordance.
- `explore_prompts` render as text in the prerendered static page too (free SEO prose describing
  the interactive).
- Renderer placement: after `mental_model`, before sections (the hook has set the question; the sim
  is the answer machine).
- `validate.py` gate: `sim.engine` ∈ engine allowlist; per-engine required-param check (kept in a
  small table inside validate.py, mirroring the registry — same discipline as DSA `viz` keys);
  predict/options validation reused from the maths kind.
- Prerender (`generate-lesson-html.mjs`): render `sim.title` + `explore_prompts` + the predict
  question as static text under an "Interactive" H2; never attempt to render the sim itself.

### 2.2 Testing gates

- `core.js` functions are pure → golden unit tests with values cross-checked against NCERT worked
  examples AND our existing numericals JSON (e.g. `apply-mirror-formula.json` answers double as
  test vectors). Extend `npm run golden` to include `sims/engines/*/core.test.mjs`.
- Browser gate: for each engine, one exemplar lesson is manually driven in the preview browser
  (drag, predict, edge cases, dark mode, mobile viewport) before content scales — same
  golden+browser two-gate rule as D-015 gave DSA.

---

## 3. Ray-optics engine (flagship)

One engine, one mental model: a **principal-axis optical bench**. Modes are parameter sets, not
separate components.

### 3.1 Class 10 capabilities (M2–M3)

| Mode | What the student manipulates | Physics core |
|---|---|---|
| `mirror` (concave/convex) | Drag object along axis; drag its tip for height | 3-ray construction (parallel→F, through-C, to-pole), mirror formula, magnification |
| `lens` (convex/concave) | Same | 3-ray construction (parallel→F₂, through-O, through-F₁→parallel), lens formula, power in D |
| `snell` | Drag incident angle at a plane interface | sin i/sin r live readout, n₁/n₂ selectable media, bending toward/away from normal |
| `slab` | Drag incident angle on a glass slab | Lateral displacement, emergent-ray parallelism |

Live readouts: u, v, f, m, image nature badge (real/virtual · inverted/upright · magnified/diminished).
**Sign conventions:** compute internally in a convention-free form; the display layer applies the
New Cartesian Convention (NCERT). A visible "sign convention" toggle overlays the +/− axes — the
single most-tested, most-confused thing in the chapter. This is where the bugs will live; golden
tests hammer it (all 5 canonical object positions × concave/convex × mirror/lens).

Edge cases as curriculum: object at F (parallel rays, "image at infinity" state), object inside F
(virtual image, dashed ray extensions behind mirror/through lens), convex mirror/concave lens
(always-virtual cases). Each canonical case is a named entry in `cases` → one tap jumps the object
there.

### 3.2 Class 12 capabilities (M4) — same engine, more modes

`tir` (draggable angle past critical angle, optical-fiber overlay) · `prism` (i–δ deviation curve
drawn live as the student drags i, minimum-deviation discovery) · `lensmaker` (drag R₁/R₂/n, watch
f respond) · `combo` (two thin lenses in contact → equivalent power; microscope/telescope presets
as named cases) · `spherical-surface` (refraction at a single spherical surface — the n₁/v − n₂/u
relation) · `eye` (myopia/hypermetropia + correcting lens as a two-element combo).

Proof-of-stretch for this round: **the full Class 12 Ray Optics chapter ships** (founder decision
#2), so `physics-12` launches with one complete chapter rather than sample lessons.

### 3.3 `core.js` function surface (all pure, all goldened)

`mirrorImage(u, f)` · `lensImage(u, f)` · `magnification(u, v)` · `snell(n1, n2, thetaI)` ·
`criticalAngle(n1, n2)` · `slabShift(t, n, thetaI)` · `prismDeviation(A, n, i)` ·
`minDeviation(A, n)` · `lensMaker(n, R1, R2)` · `comboPower([f...])` ·
`sphericalSurface(n1, n2, R, u)` · `rayPaths(scene)` (returns polyline segments for the renderer —
geometry only, no styling).

---

## 4. Content plan

### 4.1 `physics-10` — Light: Reflection & Refraction (flagship chapter A)

~18 lessons already exist as prose (ray diagrams ×4, sign conventions ×2, mirror/lens formula,
magnification ×2, power, Snell, refractive index, identification ×2, bending, dispersion…). Work =
author `sim` blocks for each + close gaps (plane-mirror intro if missing). The Human Eye &
Colourful World chapter is the natural follow-on (reuses `prism` + `eye` modes) — backlog, not this
round.

### 4.2 `physics-12` — Ray Optics & Optical Instruments (flagship chapter B, new roadmap)

~14 lessons, authored by Antigravity against the contract: spherical mirrors recap (12th rigor) ·
refraction at plane surfaces · TIR + applications · refraction at spherical surfaces · thin-lens
derivation · lens maker's formula · magnification & power · thin lenses in contact · prism &
minimum deviation · dispersion · simple microscope · compound microscope · telescopes ·
eye defects. JEE/NEET-adjacent numericals set follows the `_numericals` pattern.

### 4.3 Authoring pipeline

`content/PROMPT-physics.md` gains a **sim authoring section** (engine catalog, param schemas, the
predict-gate rules, "sim must be answer-machine for the hook question" rule). Antigravity authors
prose + sim params; `validate.py` checks structure; the critic (Sonnet, per existing convention)
gains a rubric line: *"Does the sim config produce a teachable scene, and does the predict question
have exactly one defensible answer at those params?"* Claude spot-checks params numerically against
`core.js` (a 20-line script can run every lesson's params through the engine and flag degenerate
scenes — add as `content/check-sims.mjs`).

---

## 5. Milestones

| M | Deliverable | Model routing |
|---|---|---|
| M0 | ✅ **DONE 2026-07-17** — IA migration: split physics-9-10 → physics-9/physics-10, redirects, sitemap, label maps (no new hub UI needed — see §1.1). DB reseed prepared, hand-off to run | **Sonnet** — mechanical, spec'd above |
| M1 | `SimFrame` + registry + ray-optics `core.js` + golden tests green | **Strong model** — geometry + sign conventions are where bugs live |
| M2 | `mirror`/`lens` modes rendered + predict gate; 3 exemplar Class-10 lessons wired; browser-verified **at 360×640 portrait first** (drag/fat-finger/edge/dark), then desktop | **Strong model** — locks the interaction grammar |
| M3 | `snell`/`slab` modes; all ~18 Class-10 Light lessons sim-configured (Antigravity) + critic pass + `check-sims.mjs` | Sonnet + Antigravity |
| M4 | Class-12 modes (`tir`/`prism`/`lensmaker`/`combo`/`spherical-surface`/`eye`); `physics-12` roadmap + Ray Optics chapter | Strong model for modes; Antigravity for lessons |
| M5 | Product polish vs design bible; smartboard fullscreen + Android QA; SEO ship (hubs indexed, GSC) | Sonnet |
| M6+ | Circuits engine (Class 10 Electricity ↔ Class 12 Current Electricity) → kinematics presets → particles/chemistry — each repeats M1→M3 shape | — |

Rule carried over from the maths plan: **content scales only after the engine contract hardens**
(M3 starts only when M2's exemplars survive the browser gate).

---

## 6. Risks

- **Sign-convention bugs** — the #1 credibility risk in front of a physics teacher. Mitigation:
  convention-free core + display-layer convention + goldens from NCERT worked examples.
- **Sim-as-decoration** — a sim nobody predicts against is PhET-lite. Mitigation: predict gate is
  mandatory in the schema (validator errors without it), critic rubric line.
- **Scope creep sideways** (more chapters before grammar locks). Mitigation: M2 gate; M6 engines
  each wait for the previous chapter to ship.
- **URL-migration SEO wobble.** Mitigation: 301s + sitemap + GSC in one isolated deploy (M0),
  2-week GSC watch before judging.
- **Low-end Android perf.** Mitigation: SVG node budget, no idle rAF, canvas reserved for particles.
