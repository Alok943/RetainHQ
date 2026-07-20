# Antigravity handoff — physics math-in-prose remediation (64 lessons)

**The defect (user-reported, 2026-07-19):** in `physics-10/cross-multiplication-in-proportions`,
a fully solved example sits inside an `explanation` paragraph as plain text — *"Agar aapko
(-5)/v = 2/(-3) mile … -5 × -3 = v × 2, yani 15 = 2v"* — no visual highlight, easy to skim past,
duplicating `worked_example`'s job badly. Scan of all 138 physics-9/physics-10 lessons found **64
offenders**: **21 with solving chains in prose** (severe) and **43 with formulas/values outside
backticks** (contract violation — `PROMPT-physics.md` has required backticks all along).

**What the renderer already gives you (no frontend changes needed):**
- `` `backtick spans` `` in any prose field → styled inline code chips (`glossary.jsx`).
- **Indented lines** inside `explanation`/`sections[].body` → a highlighted display block
  (`RichText`, LessonView.jsx) — use for short derivations that ARE the teach.
- `worked_example` → a full card: problem shown, "Reveal the solution" button, numbered steps
  with `narration` + highlighted `math` lines, answer box. Use for anything being *solved*.

## The three rules (now also in `PROMPT-physics.md` §FORMATTING)

1. **Backtick every formula, symbol, unit, and value** in ALL prose fields: `` `1/v + 1/u = 1/f` ``,
   `` `9.8 m/s^2` ``, `` `u = -infinity` ``. No naked `=`, `×`, units, or numbers-with-units in
   running text.
2. **Never solve in prose.** A solving chain (two or more `=` steps walking a calculation forward)
   must move to `worked_example` — as a new example if the existing two don't cover it, or merged
   into one of them if it's the same case with different numbers. Remember the physics contract:
   **exactly 2 worked examples, UNRELATED contexts** — don't end up with 3.
3. **Short derivations that are genuinely part of the teach** (e.g. deriving `1/Rp = 1/R1 + 1/R2`
   from `I = I1 + I2 + I3`) stay in the explanation, but each equation line goes on its own
   **indented line** (renders as a highlighted block), with the Hinglish narration between blocks.
   Deciding rule: *derivation of the formula being taught → indented block; applying the formula
   to numbers → worked_example.*

**Do not change:** meaning, Hinglish voice, lesson structure, any other field. This is a formatting
pass, not a rewrite. Where a solving chain moves out of prose, leave a one-sentence prose pointer
("Neeche worked example 2 mein isko solve karke dekho") only if the paragraph reads broken
without it.

**Gate: `python content/validate.py` — zero errors. Do NOT commit.**
Claude lands a validator check for naked-math/solving-chains in the SAME commit as this fix pass
(landing it earlier would turn CI red on all 64 files).

---

## Tier 1 — solving chains in prose (21 files, fix rules 1+2+3)

```
physics-10/apply-electric-power-formulas.json
physics-10/apply-mirror-formula.json
physics-10/calculate-equivalent-resistance-in-parallel.json
physics-10/calculate-equivalent-resistance-in-series.json
physics-10/calculate-linear-magnification-lenses.json
physics-10/calculate-linear-magnification-mirrors.json
physics-10/calculate-power-for-vision-correction.json
physics-10/cross-multiplication-in-proportions.json
physics-9/apply-2as-v-2-u-2.json
physics-9/apply-acceleration-formula.json
physics-9/apply-average-speed-formula.json
physics-9/apply-equations-of-motion-for-free-fall.json
physics-9/apply-f-g-m1-m2-r-2.json
physics-9/apply-f-ma.json
physics-9/calculate-speed-in-circular-motion.json
physics-9/convert-km-h-to-m-s.json
physics-9/define-frequency-time-period-and-wavelength.json
physics-9/interpret-sign-of-acceleration.json
physics-9/interpret-uniform-velocity-on-velocity-time-graph.json
physics-9/read-displacement-off-a-velocity-time-graph.json
physics-9/select-correct-equation-of-motion.json
```

## Tier 2 — naked math, backticks only (43 files, fix rule 1)

```
physics-10/apply-laws-of-refraction-snells-law.json
physics-10/apply-lens-formula.json
physics-10/apply-ohms-law-to-circuits.json
physics-10/apply-relative-refractive-index.json
physics-10/apply-resistivity-formula.json
physics-10/calculate-heat-generated-by-current.json
physics-10/calculate-inverse-sums.json
physics-10/calculate-power-of-a-lens.json
physics-10/define-electric-current.json
physics-10/define-electric-potential-difference.json
physics-10/define-principal-focus-and-focal-length.json
physics-10/distinguish-live-neutral-and-earth-wires.json
physics-10/explain-role-of-a-fuse.json
physics-10/identify-cause-of-refraction.json
physics-10/relate-refractive-index-to-speed-of-light.json
physics-10/solve-complex-resistor-networks.json
physics-10/state-ohms-law.json
physics-9/apply-pressure-force-area.json
physics-9/apply-s-ut-1-2-at-2.json
physics-9/apply-v-u-at.json
physics-9/apply-wave-speed-equation.json
physics-9/calculate-area-of-triangle-and-rectangle.json
physics-9/calculate-average-velocity.json
physics-9/calculate-distance-using-echo.json
physics-9/calculate-mechanical-energy-of-free-falling-object.json
physics-9/calculate-the-slope-of-a-straight-line.json
physics-9/calculate-weight-on-earth-and-moon.json
physics-9/convert-commercial-unit-of-energy.json
physics-9/define-acceleration.json
physics-9/define-average-speed.json
physics-9/define-distance.json
physics-9/define-momentum.json
physics-9/define-pressure.json
physics-9/define-relative-density.json
physics-9/define-velocity.json
physics-9/distinguish-mass-and-weight.json
physics-9/distinguish-uniform-and-non-uniform-acceleration.json
physics-9/read-acceleration-off-a-velocity-time-graph.json
physics-9/rearrange-linear-algebraic-equations.json
physics-9/state-archimedes-principle.json
physics-9/state-newtons-second-law-of-motion.json
physics-9/state-newtons-third-law-of-motion.json
physics-9/state-the-universal-law-of-gravitation.json
```

(Encoding note: several physics-9 files contain mojibake — `�` where `½`/`²` should be, e.g.
`apply-potential-energy-formula.json` "1/2 mv�". Fix any you touch: write `1/2 m v^2` ASCII-style
inside backticks, per the contract's existing ASCII-math convention.)

---

## Worked exemplar — `cross-multiplication-in-proportions.json`

Before (in `explanation`, plain prose):

> Sign mistakes yahan bahut aam hain. Agar aapko (-5)/v = 2/(-3) mile, toh cross multiply karte
> time minus signs ko dhyan se numbers ke sath hi rakhna chahiye. -5 × -3 = v × 2, yani 15 = 2v.

After: the sign-handling *point* stays in prose with backticks; the *solving* is already covered by
worked example 2 (`(-v)/20 = (-3)/(-5)`), so the chain simply comes out:

> Sign mistakes yahan bahut aam hain. Agar equation mein negative values hon (jaise `(-5)/v = 2/(-3)`),
> toh cross multiply karte time minus sign ko uske number ke saath hi rakhna chahiye — neeche
> worked example 2 mein yahi trap solve karke dikhaya hai.
