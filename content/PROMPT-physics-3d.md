# PROMPT — Interactive Concept Simulators for Physics (`diagram3d`)

Contract for Antigravity. Claude owns this contract + the physics-correctness review; Antigravity
implements the React Three Fiber renderers and authors the per-lesson scene data against it.

> **The current 2D SVG diagrams look cheap on the inherently-spatial concepts** (a magnetic field
> drawn as flat loops, "Fleming's left-hand rule" as a static picture). This adds a layer of **3D
> interactive concept simulators** — NOT animated diagrams. The student doesn't just watch; they
> **predict → observe → reflect** (and, where it teaches, **manipulate**). This exists ONLY for the
> ~6 concept families where 3D changes whether the student *gets it*. Everything else stays 2D. This
> is a scalpel, not a coat of paint.

---

## THE ONE HARD PRINCIPLE (do not violate)

**Data-driven, physics-in-the-renderer.** The lesson JSON supplies *parameters* (masses, distances,
current direction, field direction, wave frequency) — NEVER geometry, coordinates, keyframes, or 3D
model files. A parameterized R3F component computes the scene and the motion from those parameters,
exactly like `RayDiagram.jsx` computes an image from the mirror formula. This guarantees:
- every scene is physically correct by construction (no hand-placed, possibly-wrong vectors),
- the file stays tiny and reviewable,
- no per-lesson `.glb`/`.gltf` asset sprawl (that is the "AI-slop" failure mode — banned).

If a scene needs a hand-authored 3D model or hand-tuned keyframes, it is out of scope. Reject it.

---

## TEACHING OVER RENDERING (the interaction spine)

Every scene must justify its existence by improving *conceptual understanding*, not by looking good.
The default interaction pattern — the same predict-before-reveal loop the rest of RetainHQ runs on:

**Predict → (Manipulate) → Observe → Reflect.** The student predicts the outcome before the animation
completes, optionally changes a physical parameter (distance, current direction, pole orientation),
observes the correct behaviour, and immediately connects it back to the governing principle.

- **Predict and Reflect are required** where the scene supports a prediction (nearly all do).
- **Manipulate is OPTIONAL per scene.** Some concepts teach by manipulation (flip the current → where
  does the force go?); some teach by watching (white light splitting). Do NOT force a control onto a
  scene that doesn't need one — extra controls cost state, UI, and mobile frames for no learning gain.
- **The litmus test (this replaces "is it spatial?"):** if a scene is only *watchable* but not
  *thinkable* — the student can't predict anything, can't change anything meaningful — it should stay
  a **2D diagram**, not become a simulator. Watchable-only 3D is decoration; cut it.

**Reuse, don't reinvent, the prediction mechanic.** The prediction ties into the app's existing
predict-before-reveal (`aha_moment` / `understanding_checks` in `LessonView`) — same reveal-gating,
same UI language — not a second parallel prediction system.

---

## WHEN 3D — the scoped scene-kind catalog

Build EXACTLY these scene-kinds. Each maps to a handful of Class 9–10 lessons. Nothing else gets 3D.

| `scene` | Concept it serves | Why 2D fails | Animates |
|---|---|---|---|
| `orbit` | Universal gravitation, satellites, free-fall-vs-orbit | Orbits + the central force are a spatial relationship | Body revolves; force vector always points to centre |
| `magnetic-field` | Field of a bar magnet / straight wire / solenoid / loop | Field lines are 3D loops; flat drawings mislead | Field-line flow N→S; optional compass needle aligning |
| `fleming-rule` | Force on a conductor (left-hand), induced current (right-hand) | THREE mutually-perpendicular axes — the #1 thing students can't hold in their head | Rotate to show F ⟂ B ⟂ I; highlight the computed third axis |
| `em-induction` | Electromagnetic induction, magnet-through-coil | Flux change through a coil is a 3D motion | Magnet moves in/out; induced current direction flips with motion |
| `dispersion-prism` | Dispersion of white light, spectrum | The prism + fanned spectrum reads better in 3D depth | White ray enters, fans into VIBGYOR on exit |
| `longitudinal-wave` | Sound as a longitudinal wave, compression/rarefaction | Sound is NOT transverse; the 2D "S-curve" actively teaches the wrong thing | Particle grid oscillating along propagation → visible compressions/rarefactions |

**KEEP 2D (do NOT 3D-ify — the existing SVG is correct and clearer):** distance-time / velocity-time
**graphs**, equations-of-motion numericals, **circuits** (Ohm's law, resistor networks), and
**mirror/lens ray diagrams** (`RayDiagram` is already exact and legible). If tempted to add 3D here,
stop — you will make it worse and slower.

Coverage target: ~15–20 lessons across the 6 kinds. If a lesson isn't in the table above, it does
not get a `diagram3d`.

---

## TECH STACK & INTEGRATION

- **React Three Fiber** (`@react-three/fiber`) + **drei** (`@react-three/drei`) for helpers
  (`<Line>`, `<Text>`, `<OrbitControls>`, `<Html>`). No other 3D deps. No physics engine (motion is
  parametric, not simulated — cheaper and deterministic).
- **Lazy-loaded, always.** Mirror the existing `DsaPlayer`/Pyodide pattern: a `React.lazy` +
  `<Suspense>` boundary so Three.js (~150 KB gz) is NEVER in the main bundle and only loads when a
  lesson with a `diagram3d` is opened. A lesson without one must not pull in Three.js.
- **Integration point:** extend the physics diagram dispatcher. Add a `diagram3d` lesson field
  (top-level and inside `worked_example`), rendered by a new `<Physics3D scene={...} />` that lazy-
  loads and switches on `scene.scene`. Place it in the same slot the 2D `diagram` renders.
- **File layout:** `frontend/src/physics/three/` — `Physics3D.jsx` (lazy loader + dispatcher +
  `<Canvas>` shell + fallback), then one component per scene-kind: `OrbitScene.jsx`,
  `MagneticFieldScene.jsx`, `FlemingRuleScene.jsx`, `EmInductionScene.jsx`, `PrismScene.jsx`,
  `LongitudinalWaveScene.jsx`. Shared helpers (axis, arrow, label) in `three/primitives.jsx`.

---

## THE DATA CONTRACT (what the lesson JSON carries)

`diagram3d` is an object:
`{ "schema_version": 1, "scene": "<kind>", ...params, "prediction"?, "manipulate"?, "reflection"?, "caption", "poster"? }`.

- **`schema_version`** (required, currently `1`) — lets the renderer migrate the contract later without
  guessing. Bump it when the shape changes.
- **Field convention: `snake_case` everywhere** (matches the rest of the lesson JSON: `object_distance`,
  `recall_questions`). NOT camelCase.
- **`caption`** stays `caption` (same field the 2D diagrams use — one name for "the summary line").

`prediction` (strongly preferred), `manipulate` (optional), and `reflection` (preferred) drive the
Predict → Manipulate → Observe → **Reflect** spine:

```jsonc
"prediction": {                       // reuses the app's predict-before-reveal; gates the reveal
  "question": "Where does the force on the wire point?",
  "choices": ["Up (+z)", "Down (-z)", "Into the page"],
  "answer": 0,                        // index; the renderer reveals + explains after the student commits
  "explains": "F = I L x B - perpendicular to both, by the left-hand rule."
},
"manipulate": {                       // OMIT unless changing this teaches something
  "param": "current_direction",       // which scene param the student can change
  "options": ["+y", "-y"],            // discrete only (no free sliders on mobile); renderer recomputes
  "prompt": "Flip the current - predict the new force direction first."
},
"reflection": {                       // closes the loop; a simulation that ends at "Observe" is decoration
  "prompt": "Why did the force reverse when you flipped the current?",
  "answer": "Reversing I reverses I x B, so F flips too."
  // Reflection prompts are prime recall material: a scene's reflection SHOULD be eligible to become
  // an FSRS card via the existing 'Add to reviews' bridge, so the concept re-tests over time.
}
```

Params are physical quantities only. Examples (author against these EXACT shapes):

```jsonc
// orbit  (every example also carries "schema_version": 1 — omitted below for brevity)
{ "scene": "orbit", "central": { "label": "Earth", "mass": 6e24 },
  "satellite": { "label": "Moon", "mass": 7.3e22 }, "radius_km": 384000,
  "show_force_vector": true, "caption": "Gravity keeps the Moon in orbit — force always points to Earth." }

// magnetic-field
{ "scene": "magnetic-field", "source": "bar-magnet", "current_direction": "n/a",
  "show_compass": true, "caption": "Field lines emerge from N, curve around to S." }
// source ∈ bar-magnet | straight-wire | solenoid | circular-loop; current_direction ∈ into|out|n/a

// fleming-rule
{ "scene": "fleming-rule", "rule": "left",         // left = motor force; right = induced current
  "field_direction": "+x", "current_direction": "+y",  // give TWO; renderer computes+highlights the third
  "caption": "Force is perpendicular to both field and current." }

// em-induction
{ "scene": "em-induction", "motion": "insert", // insert | withdraw
  "magnet_pole": "N", "caption": "Pushing N in induces a current that opposes it (Lenz)." }

// dispersion-prism
{ "scene": "dispersion-prism", "caption": "White light splits into VIBGYOR — violet bends most." }

// longitudinal-wave
{ "scene": "longitudinal-wave", "frequency": 2, "caption": "Compressions and rarefactions travel; particles only oscillate in place." }
```

`poster` (optional) = a static 2D fallback (an existing `schematic`/`image` diagram object) shown when
3D is unavailable (see guardrails). If omitted, the fallback is the caption text in a bordered card.

---

## RENDERER SPEC (per scene-kind)

Each scene component takes the parsed params and **computes** the scene. Requirements per kind:

- **`orbit`** — size bodies by mass ratio (log-scaled, clamped so the satellite stays visible), place
  at `radius_km` (scaled to the canvas), animate revolution at a constant angular rate. Force arrow
  from satellite → central, re-pointing every frame. One slow orbit (~8 s), not a blur.
- **`magnetic-field`** — generate field-line curves *analytically* for the chosen `source` (dipole
  loops for bar-magnet; concentric circles around a `straight-wire` per the right-hand rule; solenoid
  = bar-magnet-like external + uniform internal). Animate a subtle directional flow along the lines.
  If `show_compass`, a needle that aligns to the local field direction.
- **`fleming-rule`** — three orthogonal labelled arrows (F, B, I). Author gives two; renderer computes
  the third via **F = I L × B** (left/motor) or the induced-current sense (right). The computed axis
  is highlighted. Correct handedness is the whole point — get the cross product right.
- **`em-induction`** — a coil + a bar magnet translating along the axis (`insert`/`withdraw`). Induced
  current arrows on the coil whose direction obeys **Lenz's law** (opposes the flux change). Reverse
  motion ⇒ reverse current. This must be correct, not decorative.
- **`dispersion-prism`** — a triangular prism; one white incident ray refracts, disperses into 7
  colour rays on exit with violet deviating most (author the deviation order; exact indices not
  required, but the ORDER must be right: red bends least, violet most).
- **`longitudinal-wave`** — a 1D lattice of particles displaced by `A·sin(kx − ωt)` ALONG the
  propagation axis (never transverse). Compressions/rarefactions must be visibly denser/sparser and
  travel while individual particles oscillate in place.

All scenes: neutral studio look (soft ambient + one key light), the app's palette
(cyan `#0891B2` for the "answer"/computed element, slate for structure, amber `#B45309` for
reaction/secondary), a `<Text>` label per actor, and the `caption` rendered in the 2D card chrome
BELOW the canvas (reuse the RayDiagram caption row style).

### Physics ⟂ graphics separation (mandatory, per scene)

Every scene component is split into two explicit stages — the same structure `RayDiagram.solve()`
already uses. This keeps the physics correct, testable, and independent of the visuals:

1. **`computePhysics(params) → derived`** — a PURE function: the governing formula turned into derived
   quantities (e.g. `F = G·m1·m2/r²` → the force magnitude; the cross product → the third axis; Lenz →
   the current sign). No React, no Three.js, no colours. This is the part `three/__checks__.md` pins
   and a human reviews.
2. **`derived → visual props`** — map derived quantities onto primitives (`arrow.length ←
   normalize(F)`, `label.value ← F`, `distanceMarker ← r`). Only here do Three.js and the palette appear.

**Do NOT put formulas or bindings in the lesson JSON.** The formula lives in `computePhysics` (code),
not in content — a JSON formula/binding string would mean shipping an expression-evaluator into the
runtime, which breaks "physics in the renderer, not the content" and is an over-engineered DSL. The
JSON stays declarative parameters; the code owns the math.

### Scene lifecycle (one shared flow — no scene invents its own)

`Load → Initialize → Predict → (Manipulate) → Observe → Reflect → Dispose`. Notes:
- **Initialize** runs `computePhysics` and builds primitives once; re-runs only when a `manipulate`
  choice changes a param.
- **Predict / Reflect** gate on the `prediction` / `reflection` blocks (reuse the app's reveal UI).
- **Dispose is REQUIRED** — on unmount, dispose geometries, materials, and the WebGL context. Leaked
  GL contexts are a real memory killer when a student pages through many lessons on a cheap phone; a
  scene that doesn't clean up will crash the tab after a dozen navigations. Treat this as a guardrail,
  not hygiene.

### Shared primitive library (`three/primitives.jsx`) — grouped

Scenes are COMPOSED from a fixed primitive set — no scene builds geometry ad hoc. Split by role:

- **Geometry:** `Sphere · Cube · Cylinder · Plane`
- **Physics:** `Vector · ForceArrow · Orbit · FieldLine · Compass · DistanceMarker · ParticleGrid · Angle`
- **UI:** `Label · Equation · Tooltip · Highlight · Annotation`

Each takes physical/semantic props (a `Vector` takes a direction + magnitude + colour, not raw points)
and handles its own labelling. **Scope discipline:** build these clean and composable so they *could*
extend to Chemistry/Math later — but do NOT design for those subjects now, and explicitly do NOT target
**DSA**, which already has its own 2D execution-trace renderer (`frontend/src/dsa/`) and is a different
paradigm. Ship physics first; generalize only when a second subject actually needs it.

### Scene-state convention (light)

Every scene manages state through one small shape so no scene reinvents it:
`{ parameters (author-given), derived (computed physics), uiState (camera/paused/offscreen),
prediction (committed? correct?) }`. Keep it a plain object/reducer — not a framework, not ceremony.

---

## NON-NEGOTIABLE GUARDRAILS (a school pitch runs on cheap phones)

1. **Performance budget.** Target 60 fps on desktop, ≥30 fps on a mid Android. Keep triangle counts
   trivial (these are diagrams, not games): field lines ≤ ~24 curves, wave lattice ≤ ~120 particles.
   Cap `dpr={[1, 2]}`. No shadows, no post-processing, no HDRI environments.
2. **Lazy + code-split** (above). Three.js must not touch the main bundle or any non-3D lesson.
3. **Graceful degradation.** If WebGL is unavailable, or `navigator.hardwareConcurrency <= 4` on a
   coarse-pointer device, OR the canvas fails to init → render the `poster` 2D fallback instead. Never
   white-screen. Wrap every scene in an error boundary that falls back to `poster`/caption.
4. **`prefers-reduced-motion`** → freeze animation at a representative frame (still correct, just not
   moving). Also pause when the canvas is offscreen (IntersectionObserver) to save battery.
   **Interactivity must not weaken degradation:** the `prediction` step must still work with motion
   frozen (predict → reveal the correct answer statically) and must still work on the 2D `poster`
   fallback. Manipulation controls may be dropped on the fallback, but predict/reflect may not be.
5. **Controls:** gentle `<OrbitControls>` with damping, zoom disabled or clamped, auto-rotate OFF.
   The default camera angle must already show the concept — the student shouldn't have to fiddle.
6. **Physics correctness is reviewed, not assumed.** Cross products (Fleming), Lenz direction, orbit
   force direction, dispersion order, longitudinal (not transverse) motion — each has a canonical
   right answer. Ship a `three/__checks__.md` listing, per scene, the expected observable (e.g.
   "left-hand rule, B=+x I=+y ⇒ F=+z"). Claude/a teacher reviews these before merge.
7. **No asset files.** No `.glb`, `.gltf`, textures, or external models. Geometry is generated in code.

---

## CONTENT + VALIDATOR INTEGRATION

- `content/validate.py`: add a `validate_diagram3d(...)` used wherever `diagram`/diagram-bearing
  fields are checked. Validate `schema_version == 1`, `scene ∈` the 6 kinds, and the required params
  per kind (membership + presence + enum checks — same philosophy as the 2D diagram branch). If
  present, check `prediction` (`question` + non-empty `choices` + in-range `answer`) and `reflection`
  (`prompt`); `poster`, if present, validates as a normal 2D diagram.
- `diagram3d` is allowed on the physics lesson top-level and inside `worked_example[]`, mutually
  optional with the 2D `diagram` (a lesson may have one, the other, or neither).
- `sync-content.mjs` needs no change (data lives in the lesson JSON).

---

## DELIVERABLES

1. `frontend/src/physics/three/Physics3D.jsx` (lazy loader + dispatcher + `<Canvas>` shell + error
   boundary + fallback) and the 6 scene components + `primitives.jsx`. Each scene splits into
   `computePhysics(params) → derived` (pure) + a visual-mapping render, and disposes its GL resources
   on unmount.
2. Dispatcher wiring: a `diagram3d` branch in the physics diagram render path (LessonView +
   PhysicsNumericals), lazy so non-3D lessons stay light.
3. `content/validate.py` `diagram3d` validation.
4. `three/__checks__.md` — the per-scene expected-observable table for correctness review.
5. `diagram3d` blocks authored into the ~15–20 in-scope lessons (the 6 families above) — and the
   matching `poster` 2D fallback for each.
6. A one-line note in `content/PROMPT-physics.md` pointing to this file for the 3D subset.

## SELF-REVIEW CHECKLIST (before you hand back)

- [ ] Opening a NON-3D lesson does not load Three.js (check the network/bundle).
- [ ] Every scene has a working 2D `poster` fallback; killing WebGL shows it, never a blank.
- [ ] Mid-Android emulation (4× CPU throttle) holds ≥30 fps on each scene.
- [ ] `prefers-reduced-motion` freezes motion; offscreen canvases pause.
- [ ] **Dispose works:** page through ~20 lessons (opening/leaving several 3D scenes); no growing GL
      context count, no tab crash (WebGL context leak is the classic mobile killer).
- [ ] `physics` and `graphics` are separate: `computePhysics` is a pure function with no Three.js import.
- [ ] `prediction` gates the reveal and `reflection` closes the loop (both work motion-frozen).
- [ ] Each scene matches its row in `__checks__.md` (handedness, Lenz, dispersion order, longitudinal).
- [ ] No `.glb`/texture/model files added anywhere.
- [ ] `python content/validate.py` passes.

## NON-GOALS (reject on sight)

- 3D for graphs, circuits, numericals, or mirror/lens ray diagrams.
- **Watchable-only scenes** — if the student can't predict or change anything, keep it a 2D diagram.
- **Manipulation forced onto scenes that don't need it**, or **free/continuous sliders** (discrete
  choices only — sliders are a mobile-frame and correctness sink).
- A second prediction system parallel to the app's existing predict-before-reveal.
- Designing the primitives for DSA/Chemistry/Math now (DSA has its own 2D trace renderer; generalize
  only when a second subject actually lands).
- Imported 3D models, textures, or hand-authored keyframes.
- A physics engine / real simulation (motion is parametric).
- "Game" polish: shadows, bloom, HDRI, free-fly cameras, sound effects.
- 3D on more than the ~20 scoped lessons.
