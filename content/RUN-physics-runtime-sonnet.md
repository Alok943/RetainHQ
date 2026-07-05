# RUN — Physics-kind runtime (Sonnet task pack)

Hand this whole file to a Sonnet coding session in the RetainHQ repo. It is the **80% of the physics
runtime that is pattern-work** — the physics-correct ray-diagram renderer is already done by Fable
(`frontend/src/physics/RayDiagram.jsx`); do NOT touch it. Three tasks below, in order. After each, run the
stated check. Match existing code style exactly (look at the referenced files first).

## Context you need
- New lesson kind **`physics`** (Class 9–10 NCERT school platform). Contract: `content/PROMPT-physics.md`.
  Gold-reference lesson already authored: `content/roadmaps/physics-9-10/apply-mirror-formula.json` — read it.
- Physics lessons render through the SHARED `AptitudeReasoningBody` in `frontend/src/LessonView.jsx`
  (already wired: `physics` added to the kind dispatch; `PhysicsDiagram` dispatcher added; `worked_example`
  block already handles the physics array shape with `{narration, math}` steps + per-example `diagram`).
- A `diagram` object has a `type`: `ray` (done), **`graph`** (YOUR task 2), `circuit`/`free-body` (later,
  render nothing for now — `PhysicsDiagram` already returns null for them), `image` (done via `LessonImage`).
- Content pipeline: lessons at `content/roadmaps/physics-9-10/<slug>.json` → `node scripts/sync-content.mjs`
  copies to `frontend/public/content/`. Validate with `python content/validate.py`.
- Predict-before-reveal reference pattern: the `aha_moment` block and the `worked_example` reveal button in
  `LessonView.jsx` (search `ahaRevealed` / `setAhaRevealed`) — copy that reveal interaction for task 3.

---

## Adjudicated decisions (Fable, do not re-litigate)
- **Diagram validation:** deep-validate the types that have a live renderer (`ray`, `graph`, `image`);
  membership-only for `circuit`/`free-body` (renderers not built — schema discovered when built).
- **oa_questions field:** physics uses **`source`** (e.g. "CBSE 2023"), NOT `company`. Validator accepts
  either (`source` OR `company`). **Also patch the oa renderer** in `LessonView.jsx` (two pill sites, ~lines
  1084 and 1420): change `q.company` → `q.source || q.company` so the source chip shows for physics.
- **_numericals discovery:** the validator glob `ROOT.glob("*/*.json")` is ONE level and SKIPS
  `_numericals/` files. Add a second glob `ROOT.glob("*/_numericals/*.json")`. Check `sync-content.mjs`
  for the same one-level bug and widen it too, or the numericals page 404s.

## TASK 1 — `validate.py`: add `physics` and `numericals` kinds
File: `content/validate.py`.
1. Add `"physics"` and `"numericals"` to the `KIND` set (near line 30).
2. **`physics` branch** (model it on the existing `theory` branch, search `if d.get("kind") == "theory"`):
   - REQUIRED: `mental_model` (`intuition` + `description`), one of `explanation`/`sections`,
     `worked_example` (a **list of exactly 2** `{problem, steps[], answer, diagram?}`; each `steps` item is
     either a string OR `{narration, math?}`), `common_mistakes` (≥1), `recall_questions` (≥3),
     `oa_questions` (≥2, each `{source, q, answer, approach?}` — note `source` not `company`).
   - OPTIONAL: `hook`, `key_points`, `diagram` (top-level).
   - Validate any `diagram` (top-level or inside a worked_example) with a shared helper: `type` in
     `{ray, circuit, graph, free-body, image}`. For `ray`: require `optic` in
     `{concave-mirror, convex-mirror, convex-lens, concave-lens}`, positive numeric `focal_length` &
     `object_distance`. For `graph`: require `axes:{x,y}` and one of `curve`(list of `{x,y}`) or
     `line:{slope,intercept}`. For `image`: require `asset`. (circuit/free-body: accept, shape-check later.)
3. **`numericals` branch** (a phase practice set, NOT a lesson): require `phase`, `roadmap`, `kind`,
   `problems` (non-empty list). Each problem: `prompt`, `given` (list), `solution_steps`
   (list of `{narration, math?}`), `answer`; optional `problem_diagram` + `solution_diagram` (validate via
   the shared diagram helper). File lives at `content/roadmaps/physics-9-10/_numericals/<phase-slug>.json`.
   NOTE: `validate.py` currently walks lesson files — make sure `_numericals/*.json` are validated too
   (check how it globs; the leading-underscore folder may need explicit inclusion).
**Check:** `python content/validate.py` passes with the gold reference `apply-mirror-formula.json` present.

## TASK 2 — `GraphDiagram.jsx` (the `graph` diagram type)
New file: `frontend/src/physics/GraphDiagram.jsx`. Mirror the STRUCTURE of `RayDiagram.jsx` (dependency-free
SVG, same card chrome: `rounded-lg border border-[rgba(15,23,42,0.12)] bg-white`, a caption row underneath,
colors `#0891B2` cyan accent, `#94A3B8` axes, `#0F172A` ink). Do NOT compute physics — just plot.
- Props: `{ diagram }` where `diagram = {type:"graph", axes:{x:"time (s)", y:"velocity (m/s)"}, curve:[{x,y}...]
  OR line:{slope, intercept}, annotations?:[{x,y,label}], caption?}`.
- Draw axes with labels, auto-scale to the data range with padding, plot the `curve` polyline OR the `line`,
  small dots at data points, optional annotations. Keep it clean and legible on mobile (viewBox ~ `0 0 520 300`).
- Wire it into `PhysicsDiagram` in `LessonView.jsx`: add `if (diagram.type === 'graph') return <GraphDiagram diagram={diagram} />;` and import it.
**Check:** add a `graph` diagram to a scratch lesson (e.g. a velocity–time line), `sync-content.mjs`, and it
renders (or at minimum `npx vite build` compiles). Then remove the scratch lesson.

## TASK 3 — Phase-end numericals: page + predict-before-reveal + entry point
The `numericals` sets (`content/roadmaps/physics-9-10/_numericals/<phase-slug>.json`) need a place to live in
the UI and a reveal interaction.
1. **Route + view:** add a route like `/roadmaps/:roadmapSlug/numericals/:phaseSlug` rendering a new
   `PhysicsNumericals.jsx`. It fetches `/content/roadmaps/<roadmapSlug>/_numericals/<phaseSlug>.json`
   (static, same as LessonView's fetch) and renders each problem:
   - `prompt` + `given` list + `problem_diagram` (via the existing `PhysicsDiagram` — export it or lift it to
     a shared module) shown IMMEDIATELY.
   - a "Reveal solution" button (copy the `ahaRevealed` interaction from LessonView) that then shows
     `solution_steps` (`{narration, math}`) + `solution_diagram` + `answer`. NEVER show `solution_diagram`
     before reveal.
2. **Entry point:** in `RoadmapDetail.jsx`, when the roadmap is `physics-9-10` (or when a
   `_numericals/<phase>.json` exists for a phase), show a "Practice numericals" affordance at the end of each
   phase that links to the route. Keep it unobtrusive — a button/card, not a node in the graph.
**Check:** with a sample numericals JSON present, the page loads, problem+diagram show, reveal works, solution
diagram appears only after. `npx vite build` compiles.

---

## Guardrails
- Do NOT modify `RayDiagram.jsx` or the physics math anywhere — that's Fable-owned and verified.
- Do NOT author lesson/numericals CONTENT (that's Antigravity) beyond throwaway scratch files for testing,
  which you delete.
- Keep everything dependency-free (no new npm packages); SVG + Tailwind only, matching existing components.
- Run `npx vite build` before finishing; it must compile clean (the RoadmapDetail chunk-size warning is
  pre-existing — ignore it).
