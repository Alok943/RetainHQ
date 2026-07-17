# PROMPT — Physics 9-10 to Pitch Quality (Priority 3)

**Status:** DRAFT session prompt, 2026-07-16. Nothing implemented.
**Goal:** one demo arc of physics content good enough to carry the "visualization" leg of the school pitch, plus the two missing diagram renderers that make physics *look* like nothing else on the market. Scope discipline per D-003: the demo lessons get excellent; the other ~120 physics lessons get nothing until a deal exists.
**Ground truth (checked 2026-07-16):** `content/roadmaps/physics-9-10/` has 131 lesson files; `_numericals/` covers 9 chapters; `_test/` has exactly one bank — `class-9-motion.json`. Live 2D renderers: `RayDiagram`, `GraphDiagram`, `SchematicDiagram` (+ R3F `diagram3d` under `frontend/src/physics/three/`). `circuit` and `free-body` are in `validate.py`'s `DIAGRAM_TYPES` but **membership-only — no deep validation, no renderer** (`_validate_physics_diagram`, validate.py:149-185). ~10+ lessons already carry `schematic`/`diagram3d` blocks from the earlier pitch-demo pass.

---

## 1. The demo arc — decide once, then build only this

**Primary: Class 9 · Motion** — the only chapter with lessons + numericals + a test bank, and the chapter the demo-data story (PROMPT-demo-data.md §3) is scripted against. Its native visuals (distance-time / velocity-time graphs) already render via `GraphDiagram`.

**The "wow" moment: Class 9 · Force & Laws of Motion** — because free-body diagrams ARE this chapter, and a live interactive FBD is the single most differentiated visual we can put on a projector. Numericals exist; no test bank (add one — §4).

**Deferred: circuit renderer / Class 10 Electricity** — build the `circuit` renderer second (same session pattern as FBD), but it does not block the Class-9 pitch. If the school asks about Class 10, the answer is the roadmap slide, not a rushed renderer.

So the pitch demo = **Motion (depth: lessons + graphs + test + analytics story) → Force & Laws (the FBD moment) → teacher gap map over both**.

## 2. Workstream A — Free-body diagram renderer (Claude-owned runtime work)

New `frontend/src/physics/FreeBodyDiagram.jsx`, following `SchematicDiagram.jsx`'s conventions (SVG, existing color classes so dark mode is free, same props contract as the other diagram renderers in `LessonView`).

**Schema contract (define first, in `content/PROMPT-physics.md` + deep-check in `validate.py`):**

```jsonc
{
  "type": "free-body",
  "body": {"label": "block", "shape": "box" | "dot"},         // the object, drawn at center
  "surface": "horizontal" | "incline" | "none",               // optional context line; incline takes "angle_deg"
  "angle_deg": 30,                                             // required iff surface == "incline"
  "forces": [                                                  // 1..6 arrows from the body's center
    {"label": "mg", "direction_deg": 270, "magnitude": 1.0},   // direction in screen degrees (0=right, 90=up)
    {"label": "N",  "direction_deg": 90,  "magnitude": 1.0},
    {"label": "F_applied", "direction_deg": 0, "magnitude": 0.6}
  ],
  "resultant": {"show": true, "label": "F_net"},               // optional computed sum arrow, dashed
  "caption": "Block on a frictionless surface"
}
```

- `magnitude` is relative (arrow length scaling), not physical units — keeps authoring simple and diagrams legible.
- Renderer computes and optionally draws the resultant — this is the interactive beat: a **"show net force" toggle** in the lesson, which is the predict-before-reveal pattern applied to FBDs.
- Upgrade `validate.py`'s `free-body` branch from membership-only to deep checks (required keys, force count 1–6, direction range, incline↔angle coupling). Golden-test the resultant math (pure function) the same way DSA generators are golden-tested.
- Verify in the browser via the dev preview on 2–3 real lessons before calling it done (the `lower-bound` backlog item is the cautionary tale: validated-but-never-rendered).

**Workstream A2 (second session, same template): `CircuitDiagram.jsx`** — series/parallel resistor networks, cell, ammeter/voltmeter symbols per NCERT conventions; deep-check schema mirroring the FBD approach. Not pitch-blocking.

## 3. Workstream B — Demo-lesson content quality (critic → fix → verify)

Scope: the lesson files for the **Motion and Force & Laws node sets only** (derive the list by matching `roadmap_nodes.phase` `"Class 9 · Motion"` / `"Class 9 · Force and Laws of Motion"` titles to lesson slugs — expect ~15–25 files, not 131).

1. **Critic pass** on exactly those files with `content/PROMPT-lesson-critic.md`, run on **Sonnet** (critic ≠ author; rubric work). Physics-specific additions to the rubric for this pass: NCERT terminology/sign-convention fidelity, numericals use SI units consistently, misconception coverage (e.g. "heavier falls faster", velocity vs acceleration direction confusion), every `worked_example` actually steps (no answer-jumps).
2. **Apply the fix lists in the same effort** — D-013's lesson: reported-but-never-applied fixes rot. The critic report artifact lands at `content/CRITIC-REPORT-physics-pitch.md` so the sweep is auditable.
3. **Diagram retrofit, demo lessons only:** every demo-arc lesson where a visual is load-bearing gets a structured diagram — `graph` for the Motion graph lessons, `free-body` (new, §2) for Force & Laws core lessons (`apply-f-ma`, Newton's-laws lessons, friction/normal-force lessons), `diagram3d` only where one already exists or is trivially reusable. Target: **zero walls of text** in any lesson opened live in the pitch.
4. **Numericals pass:** `_numericals/class-9-motion.json` + `class-9-force-and-laws-of-motion.json` get the same critique + attach `problem_diagram`/`solution_diagram` (FBDs on the force problems — solution diagrams that draw the FBD are exactly the "how a good teacher solves it" demo beat).

Everything must pass `content/validate.py`; `sync-content.mjs` handles the copy. Bulk rewriting, if the critic demands it, is Antigravity's job against the contract — Claude critiques and owns the contract, per the standing pipeline split.

## 4. Workstream C — Force & Laws test bank

Author `content/roadmaps/physics-9-10/_test/class-9-force-and-laws-of-motion.json` mirroring `class-9-motion.json`'s structure (same question `type`s, `node_title` join keys matching live roadmap node titles exactly, `trap`/`misconception` tags filled — the teacher drill-down will surface these). ~20–30 questions weighted toward the classic misconceptions. Without this bank, the teacher gap map has test signal for only one of the two demo chapters.

## 5. Sequencing & session plan

| # | Session | Blocks the pitch? | Notes |
|---|---|---|---|
| 1 | FBD schema + `validate.py` deep checks + `FreeBodyDiagram.jsx` + browser verify | YES | Claude session; renderer is the long pole |
| 2 | Critic pass + fixes on the Motion node-set lessons | YES | Sonnet critic, fixes applied same session |
| 3 | Critic + fixes + FBD retrofit on Force & Laws lessons + numericals diagrams | YES | Depends on 1 |
| 4 | Force & Laws test bank | YES (for gap-map story) | Can parallelize with 2–3 |
| 5 | Circuit renderer + Class 10 Electricity spot-polish | no | Post-pitch or spare cycles |

Re-run `PROMPT-demo-data.md`'s seed after 4 so test-attempt data covers both banks.

## 6. Acceptance checklist

- [ ] `free-body` promoted from membership-only to deep-checked in `validate.py`; resultant math golden-tested.
- [ ] FBD renders correctly (light + dark) in ≥3 real lessons and ≥2 numericals solution diagrams, verified in the browser, including the show-net-force toggle.
- [ ] Every lesson in the two demo node-sets: critic-passed, fixes applied, at least one structured visual where load-bearing, validator green.
- [ ] `_test/class-9-force-and-laws-of-motion.json` live and passing validation; Tests page serves it.
- [ ] A full dry-run of the pitch path on retainhq.app clicks through with zero placeholder/empty/ugly screens: lesson → predict-reveal → FBD toggle → add-to-reviews → test → analytics.
