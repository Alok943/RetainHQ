# diagram3d — per-scene correctness checks

Companion to `content/PROMPT-physics-3d.md`. Each row is the canonical, checkable
right answer for a scene's `computePhysics()` — a human (or a future test) reads
the pure function and confirms it matches. No Three.js/graphics knowledge needed
to review this table; it's the physics half only.

| Scene | Governing rule | Canonical example | Expected observable |
|---|---|---|---|
| `orbit` | Gravitational force always points from satellite → central body; a lighter/heavier satellite is sized by a log-scaled mass ratio, clamped so it never disappears | `central.mass=6e24, satellite.mass=7.3e22` (Earth–Moon ratio ≈ 1.2e-2) | `computePhysics` returns `satelliteRadius` clamped to `[0.14, 0.55]` and strictly smaller than `centralRadius` (1.0); the force arrow direction each frame = `normalize(-satellitePosition)`, i.e. it always points at the origin, never a fixed world direction |
| `magnetic-field` (`straight-wire`) | Biot–Savart sense: B-hat = Î × r̂ (right-hand rule — thumb along current, fingers curl in B's direction) | `current_direction: "out"` (Î = `[0,1,0]`), probe at `r = [1,0,0]` → `r̂ = [1,0,0]` | `fieldDirectionAt([1,0,0])` = `normalize(cross([0,1,0],[1,0,0]))` = `[0,0,-1]`. Flipping to `current_direction: "into"` (Î = `[0,-1,0]`) must flip the sign to `[0,0,1]` |
| `magnetic-field` (dipole family: `bar-magnet`/`solenoid`/`circular-loop`) | Point-dipole field direction: B-hat ∝ 3(m̂·r̂)r̂ − m̂, with N always at `+y` (`m̂ = [0,1,0]`) | Probe on-axis above N, `r = [0,2,0]` → `r̂=[0,1,0]` | `fieldDirectionAt([0,2,0])` = `normalize(3·1·[0,1,0] − [0,1,0])` = `[0,1,0]` — field points straight away from N, along the axis, matching "field lines emerge from N" |
| `fleming-rule` (`rule: "left"`, motor force) | F̂ = Î × B̂ (FBI left-hand rule: First=Field, seCond=Current, thuMb=force) | `field_direction:"+x"`, `current_direction:"+y"` (the PROMPT's own worked example) | `computePhysics` must return `F = cross([0,1,0],[1,0,0]) = [0,0,-1]` → `computedAxis: "-z"`. **This is the row to hand-check first** — it's the literal example in `PROMPT-physics-3d.md` |
| `fleming-rule` (`rule: "right"`, induced current / dynamo) | Î = v̂ × B̂ (FBI right-hand rule: First=Field, thuMb=motion, seCond=induced current) | `field_direction:"+x"`, `motion_direction:"+y"` | `I = cross([0,1,0],[1,0,0]) = [0,0,-1]` — same cross-product machinery, different physical labels (documented in `FlemingRuleScene.jsx`'s header since the PROMPT's schema doesn't spell out the right-hand-rule inputs) |
| `em-induction` (Lenz's law) | Induced current opposes the CHANGE in flux, not the flux itself | `motion:"insert", magnet_pole:"N"` | `poleFieldSign = +1` (N's field points away from N, i.e. `+y`, toward the coil). Inserting → flux magnitude **increasing** → `inducedFieldSign = -1` (opposes). The coil must therefore repel the approaching N — i.e. the coil's near face acts like a N pole toward the magnet |
| `em-induction` (motion reversal) | Reversing motion (same pole) must reverse the induced current | `motion:"withdraw", magnet_pole:"N"` | `inducedFieldSign` flips to `+1` (reinforces the collapsing flux, trying to hold the magnet in — attraction, opposing the withdrawal) vs. the `insert` case above |
| `dispersion-prism` | Violet deviates most, red least; monotonic in between (ROYGBIV reversed = VIBGYOR order) | n/a — no author params | `computePhysics().rays` deviation angles must be **strictly decreasing** from `violet` (index 0, `0.55` rad) to `red` (index 6, `0.28` rad) — check `rays[i].deviation > rays[i+1].deviation` for all `i` |
| `longitudinal-wave` | Displacement is ALONG the propagation axis (x), never transverse (y/z) | `frequency: 2` | `ParticleGrid` is called with `axis="x"` and each particle's `displacements[i]` is added to its **x** base position (see `LongitudinalWaveScene.jsx`) — a transverse (y-offset) rendering here would be the #1 misconception this scene exists to correct |
| `longitudinal-wave` (`amplitude`, optional extension) | Loudness = amplitude, NOT frequency/pitch — flipping `amplitude` must not change spacing between compressions | `frequency: 2, amplitude: "soft"` vs `"loud"` | `computePhysics` returns `amplitude` from the fixed `{soft: 0.022, loud: 0.05}` map (default `loud`) while `k`/`omega` (spacing/speed) are unchanged by `amplitude` — only the displacement magnitude, never the wavelength, may change. This is what makes `relate-loudness-to-amplitude.json`'s `manipulate` teach the right thing |

## How to re-check after an edit

Each `computePhysics(params)` above is a pure function (no React/Three.js import) —
paste the canonical example's params into it directly (e.g. in a Node REPL with
`--experimental-vm-modules` or a scratch `.mjs` importing the file) and diff the
output against the "Expected observable" column. If a change to `physicsUtils.js`
or a scene's `computePhysics` doesn't reproduce every row above, don't ship it.
