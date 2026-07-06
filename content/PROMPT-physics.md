# NCERT Physics lesson generation — PROMPT (kind: physics — Class 9 & 10, school platform)

> **North star:** *"Can a Class 9–10 student, with a weak teacher and boards in March, explain this AND
> solve a board numerical on it — 4 months after first learning it?"*
> Physics is **conceptual AND numerical**. So this kind = `theory`-depth teaching (the lesson IS the
> learning resource — teach from scratch, the student may have no other good source) **PLUS** worked
> numericals, because boards test problem-solving, not just definitions. Retention is the engine's job;
> the lesson is the hook + the method. Do NOT write an NCERT chapter reprint — write the version that
> makes it *click* and leaves the student able to solve a variant they've never seen.

You generate **one JSON per node** for the `physics-9-10` roadmap, `kind: "physics"`. Nodes (title = the
stable key) are in `backend/seed_physics_school.py`. Validate with `python content/validate.py` (physics
branch). Write to `content/roadmaps/physics-9-10/<slug>.json` (filename = slug; slug = kebab-case of title).

**Audience:** Tier 2/3 CBSE private-school students, mixed ability, phones + desktop. Board-exam scope only.

---

## LANGUAGE POLICY — Hinglish code-switch (READ FIRST, applies to every field)

Teach the way a good Indian physics teacher actually talks: **explain in Hinglish, keep the exam layer in
English.** This is not optional flavour — it is the retention design.

- **Hinglish (Roman script):** `hook`, `mental_model` (intuition + description), `explanation`/`sections`
  prose, the *narration* inside `worked_example` steps and `common_mistakes`. Warm, spoken, direct —
  *"Socho ek ball ko upar phenka — neeche aate waqt uski speed badhti hai, kyunki gravity use kheench rahi hai."*
- **English (ALWAYS, never Hinglish):**
  - Every **technical term**: displacement, refractive index, perpendicular, acceleration, resistance.
  - Every **formula, symbol, unit, and number**: `v = u + at`, `F = ma`, `9.8 m/s^2`, `1/v + 1/u = 1/f`.
  - Every **`recall_hint`, `recall_questions` q+answer, and `oa_questions` answer** — these are what the
    FSRS card quizzes and what the board paper demands. The testable claim MUST be in the language of the
    exam, or you build retention for the wrong target.
- **Why:** CBSE boards are written in English. A student who drills *"prakash denser medium mein slow hota hai"*
  but must write "the light slows in the denser medium; refractive index n = c/v" has a transfer gap. Hinglish
  lowers the load on *understanding the concept*; English preserves *scoring the mark*. Terms stay English even
  in NCERT's own Hindi editions — follow that.
- Keep Hinglish spelling **phonetic and simple** (kheenchna, raftaar, seedha). No Devanagari script. No slang
  that dates. If a sentence is all technical terms, it's just English — that's fine.

---

## THE TEMPLATE (field order = teaching order)
| # | Field | Required? | What it is |
|---|---|---|---|
| 1 | `hook` | optional | A concrete everyday scene where this bites — *bike brake maarne pe aage jhukna* (inertia), *garmi mein taar ka current* (heating). `scenario` + optional `question`. Skip if forced. |
| 2 | `mental_model` | **REQUIRED** | The **analogy** in Hinglish that makes it click. *"Refraction ek chalti hui gaadi jaise hai jo mud se pakki sadak pe aa rahi ho — ek pehiya pehle grip karta hai, gaadi mud jaati hai."* `intuition` = one-liner; `description` = expand it. |
| 3 | `explanation` | **REQUIRED** (or `sections`) | The **primary teach-from-scratch resource.** Assume zero prior knowledge. Walk through HOW/WHY with a concrete example, tie back to the analogy, name every moving part, end with the practical takeaway. **4–6 substantial paragraphs**, Hinglish prose with English terms/formulas. Beginner must be able to learn it from this alone. (Same depth bar as `theory` — NOT the thin aptitude shape.) |
| 3b | `sections` | alt. to `explanation` | The chunked small-idea→visual→checkpoint layout (`[{body, image?, diagram?, animation?, recap?}]`). Prefer for visual chapters (Light, Motion graphs). Exactly one of `explanation`/`sections`. |
| 4 | `diagram` / `animation` | **strongly preferred** | The **visual**. `diagram` = a structured physics figure (ray/circuit/graph/free-body — schema below). `animation` = a process (`sequence`/`cycle`, e.g. wave propagation, current flow). Physics is a visual subject — a lesson with no figure is suspect. Static one-offs may use a section `image` asset instead. |
| 5 | `key_points` | optional | Discrete parts as `[{title, detail}]` — the 3 equations of motion; the 4 factors affecting resistance; VIBGYOR order. Use when the concept HAS parts. |
| 6 | `worked_example` | **REQUIRED — EXACTLY 2, UNRELATED** | Two solved numericals/applications, each in a **different context** (see rules below). This is what separates `physics` from `theory`. |
| — | `common_mistakes` | **REQUIRED, ≥1** | The classic board error — *"mass aur weight ko same samajhna"; sign convention bhoolna; "current electron ke direction mein behta hai" (galat)*. |
| 7 | `recall_questions` | **REQUIRED, ≥3** | tier1 = state it (English), tier2 = apply/derive. Feeds the review engine. Answers in English. |
| 8 | `oa_questions` | **REQUIRED, ≥2** | Real **board / school-exam** questions (1-mark, 3-mark, numerical) with `source` (e.g. "CBSE 2023", "NCERT Exercise") + `answer` + `approach`. Not company OAs — this is school. |

**No `code_walkthrough`, no `code_snippets`, no `formula` block, no `method`, no `pattern_discovery`.**

---

## `worked_example` — the rules (2 UNRELATED, each visual)
Schema: `[{problem, steps[], answer, diagram?}]` — same base shape as aptitude's, plus an optional `diagram`.

- **EXACTLY 2 examples, and they must be UNRELATED** — different physical context / framing, not the same
  problem with new numbers. *Mirror formula: example 1 = object beyond C (real image); example 2 = object
  between F and P (virtual image, magnification).* The point is **transfer, not pattern-matching** — a student
  who only sees one framing memorises a template and fails the variant. (This is exactly how expert teachers
  probe for rote learning: change the framing.)
- **`problem`** — the question, English terms/numbers, one-line Hinglish framing allowed. Include the given
  values clearly.
- **`steps`** — each step `{narration, math?}`: `narration` = Hinglish "what we're doing and WHY" (*"Pehle
  sign convention lagao — object hamesha left mein, so u negative"*); `math` = the English equation/substitution
  for that step. Show the method, not just the algebra. Do NOT skip the "why this formula" step.
- **`answer`** — final result with **unit**, English.
- **`diagram`** (per example) — the **setup drawn** (ray diagram, circuit, graph). Strongly preferred for any
  example that has a spatial setup. Schema below.
- Numbers and formulas must be **correct** — you are the author of record; the app does not compute physics.
  Verify every substitution. A wrong worked example is worse than none.

## `diagram` — structured physics figure (the visual layer)
A data-driven figure (NOT a raster image, NOT a video) the renderer draws as SVG. Emit `type` + typed fields:

- `type: "ray"` — optics. `elements`: mirror/lens (`kind`, `focal_length`, `center_x`), `object` (`x`,`height`),
  rays `[{from, via, to}]`, `image` (`x`,`height`,`nature`). For mirror/lens ray diagrams.
- `type: "circuit"` — `components` `[{kind: cell|resistor|ammeter|voltmeter|switch|bulb, label, value?}]`,
  `topology: series|parallel|mixed`, `connections`. For Electricity.
- `type: "graph"` — `axes: {x, y}`, `curve: [{x,y}...]` or `line: {slope, intercept}`, `annotations`. For
  distance-time / velocity-time / v-i graphs.
- `type: "free-body"` — `object`, `forces: [{label, dir, magnitude?}]`. For Force/Motion.
- `type: "image"` — fallback: `{asset, alt}` from the image bucket, for one-off setups with no structured type.

Author the structured type where one fits (renderer draws it consistently + can animate the reveal); use
`image` only for genuine one-offs. **If unsure a structured type renders yet, use `image` and flag it** — do
not block a lesson on a diagram type. (Renderer coverage is tracked separately; ray + circuit + graph first.)

**3D subset:** for the ~6 spatial concept families where a flat diagram misleads (gravitation/orbits,
magnetic fields, Fleming's rule, EM induction, prism dispersion, longitudinal sound waves), a lesson may
carry a `diagram3d` field instead of/alongside `diagram` — see `content/PROMPT-physics-3d.md` for that
contract (separate schema, own validator branch, own renderer). Everything else stays 2D.

---

## PHASE-END NUMERICALS (separate deliverable — predict-before-reveal practice set)
Besides the per-node lessons, author **one numericals set per phase** (chapter). File:
`content/roadmaps/physics-9-10/_numericals/<phase-slug>.json` (phase-slug = kebab of the phase, e.g.
`class-9-motion`). These are **practice the student ATTEMPTS**, distinct from in-lesson worked examples
(which demonstrate). They drive the predict-before-reveal mechanic.

Shape:
```json
{
  "phase": "Class 9 · Motion",
  "roadmap": "physics-9-10",
  "kind": "numericals",
  "problems": [
    {
      "prompt": "<question, English terms/numbers, optional Hinglish framing>",
      "given": ["u = 0", "a = 2 m/s^2", "t = 5 s"],
      "problem_diagram": { <diagram spec — the SETUP, shown BEFORE the attempt> },
      "attempt_hint": "<one Hinglish nudge, optional — 'kaunsa equation? jisme s na ho'>",
      "solution_steps": [ { "narration": "<Hinglish why>", "math": "<English eq>" } ],
      "solution_diagram": { <diagram spec — the WORKED/REVEALED figure, shown AFTER attempt> },
      "answer": "v = 10 m/s"
    }
  ]
}
```
- **Problem shown visually first** (`problem_diagram` = the labelled setup) → student predicts/attempts →
  **solution revealed visually** (`solution_diagram` = the completed ray diagram / reduced circuit / plotted
  graph) with step-by-step. Never show the solution figure before the attempt.
- 5–8 problems per phase, ordered easy→hard, mirroring **NCERT exercise + board** style. Cover the phase's
  numerical KCs (the ones whose titles start with "Apply"/"Calculate").
- Same language policy: Hinglish narration, English math/terms/answers.

---

## Sizing, scope, self-check
- Lesson depth: `explanation` 4–6 paras; `estimated_minutes` 8–15. Conceptual nodes (field lines, audible
  range) can be lighter; numerical nodes (equations of motion, mirror formula) MUST carry strong worked
  examples.
- Board scope only — no Class 11 lookahead, nothing rationalised out of the current NCERT edition.
- **Before writing each file:** (1) Could a student learn this cold from the explanation alone? (2) Are the 2
  worked examples genuinely UNRELATED framings? (3) Every formula/number correct and every recall_hint in
  English? (4) Is there a visual, or is this honestly a no-figure concept? (5) `python content/validate.py` passes.

## Order of generation (for Antigravity)
Do the **MVP showcase first** so the pitch has polished lessons before scaling:
1. **Class 9 · Motion** (full: lessons + phase numericals) — most visual+numerical, best demo of the whole kind.
2. **Class 10 · Light — Reflection and Refraction** (ray diagrams = the killer visual).
3. Then the rest, chapter by chapter, lessons then the phase numericals set.
