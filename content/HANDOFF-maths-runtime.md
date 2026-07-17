# HANDOFF — Maths runtime (DerivationPlayer + GraphPlay) + 3 golden lessons

> Paste the block below into Antigravity (repo access required). Saved here so the
> mission survives session resets — point a fresh session at this file to resume.
> Status: NOT started.
> Design source: `docs/PLAN-school-maths-runtime.md` §3–5. Research input:
> `class11deepresearch.md` (repo root; nodes 1–3 of the Limits & Derivatives pilot).
> Verification boundary (D-015): you implement + self-check via build/validator;
> **Claude browser-verifies before anything is "done"** — goldens can't catch JSX crashes.

---

You are building RetainHQ's maths lesson runtime: an interactive step-derivation
player, a small graph component, the validator branch for a new lesson kind, and the
first 3 lessons. Work inside this repo. Do NOT commit or push.

## Read FIRST, fully
1. `docs/PLAN-school-maths-runtime.md` — §3 (step-derivation player), §4 (graph-play),
   §5 (pilot). The design intent lives there; this handoff is the build spec.
2. `class11deepresearch.md` (repo root) — the research bank: 3 nodes, each with
   misconceptions (wrong moves + wrong-path steps + feedback), canonical derivations,
   graph_play suggestions, rules glossary. This is your lesson source material.
3. `frontend/src/dsa/` — the existing DSA trace player. Match its interaction feel
   (step cursor, reveal gating) and its code style. The maths player is its sibling.
4. `content/PROMPT-beginner-overlay.md` — register rules B1–B11 for every prose string
   you author in the lessons.
5. `content/validate.py` — study an existing kind branch (e.g. `engineering`) before
   adding the new one.

## Deliverable 1 — lesson schema, new `kind: "maths"`

A maths lesson JSON has:
- `slug`, `title`, `roadmap`, `kind: "maths"`, `tier` (existing conventions).
- `mental_model` — `{intuition, description}` (same shape as engineering kind).
- `sections` OR `explanation` — the prose teach (existing three-block grammar;
  text-only sections, no images).
- `derivation` — REQUIRED, a list of ≥1 derivation objects:
```json
{
  "goal": "Evaluate the limit of (x^2 - 4)/(x - 2) as x approaches 2",
  "steps": [
    { "expr": "\\lim_{x \\to 2} \\frac{x^2 - 4}{x - 2}", "rule": "write-limit",
      "why": "Set up the limit expression." },
    { "expr": "\\lim_{x \\to 2} \\frac{(x-2)(x+2)}{x-2}", "rule": "factor-difference-of-squares",
      "why": "Factor the top. Substituting 2 now gives zero divided by zero.",
      "predict": {
        "question": "What is the correct next move?",
        "options": [
          { "expr": "\\lim_{x \\to 2} \\frac{(x-2)(x+2)}{x-2}", "correct": true },
          { "expr": "\\frac{2^2 - 4}{2 - 2}", "error_id": "limit-is-value-at-point",
            "wrong_path": ["\\frac{2^2 - 4}{2 - 2}", "\\frac{0}{0}"],
            "feedback": "The limit asks what the function approaches near the point, not what it is at the point." }
        ]
      } }
  ],
  "rules": [ { "id": "factor-difference-of-squares", "statement": "Use a^2 - b^2 = (a-b)(a+b)." } ]
}
```
Rules: `expr` is KaTeX-compatible LaTeX (JSON-escaped backslashes). `predict` on 30–60%
of steps, NEVER step 0. Options: 2–4, exactly one `correct: true`; every wrong option
has `feedback` and may have `wrong_path` (1–3 LaTeX steps showing where the wrong move
leads) + `error_id` (traceability to the research bank). `rules` defines every `rule`
id used in this derivation's steps — one plain-words sentence each.
- `graph_play` — OPTIONAL list:
```json
{ "mode": "limit", "fn": "(x^2 - 4)/(x - 2)", "a": 2,
  "predict": { "question": "As x gets close to 2 from both sides, the y-values head toward…",
               "options": ["4", "0", "undefined — there is a hole"], "answer": 0,
               "why": "The hole is only AT x = 2. Near 2, the simplified function x + 2 heads to 4." } }
```
  `mode` ∈ `limit | secant-tangent`. `limit` needs `a` (the approach point);
  `secant-tangent` needs `a` (the fixed point for the tangent).
- `common_mistakes` (≥1), `recall_questions` (≥3, `{q, answer, tier}`), `sources`
  (non-empty; NCERT/official) — existing conventions.

## Deliverable 2 — validator branch (`content/validate.py`)

Add a `kind == "maths"` branch enforcing exactly the shape above:
- `mental_model.intuition` non-empty; `sections` or `explanation` present.
- `derivation`: ≥1; each: `goal` non-empty, `steps` ≥3; each step `expr`/`rule`/`why`
  non-empty; step 0 has NO `predict`; each `predict`: `question`, 2–4 `options`,
  exactly one `correct: true`, every non-correct option has non-empty `feedback`;
  every step `rule` id is defined in that derivation's `rules` list.
- `graph_play` if present: `mode` in whitelist, `fn` non-empty, `a` is a number,
  `predict` has `question`/`options`(≥2)/`answer` (valid index)/`why`.
- `common_mistakes` ≥1, `recall_questions` ≥3, `sources` non-empty.
Follow the existing error-message style (`err(rel, "...")`).

## Deliverable 3 — frontend runtime (`frontend/src/maths/`)

**Dependency:** add `katex` (npm, pinned latest 0.16.x) + import its CSS once. Render
LaTeX via `katex.renderToString(expr, {throwOnError: false})` into
`dangerouslySetInnerHTML`. No other new dependencies — NO mathjs, NO plotting library.

**`DerivationPlayer.jsx`** — the centerpiece. Behavior contract:
1. Shows `goal`, then steps revealed one at a time (Next button / Enter). Revealed
   steps stack vertically; the current step is visually emphasized; each revealed
   step's `why` appears under it in muted text.
2. At a step with `predict`: before revealing the step, show the question + shuffled
   options (each option's `expr`/text KaTeX-rendered). Next is DISABLED until a choice
   is made — prediction is a hard gate, exactly like the DSA player's predict gate.
3. Correct pick → brief confirm state → step reveals with its `why`.
4. Wrong pick → play that option's `wrong_path` steps one by one in a visually
   distinct error branch (red-tinted background), then show its `feedback`, then a
   "Rewind" button collapses the branch back to the decision point for another try.
   Track attempts internally (no backend calls in v1 — same as the DSA player).
5. A completed derivation shows a compact "rules used" recap (the `rules` list) —
   these lines are the memorizable facts.
6. Rendering budget: works on a 360px-wide phone; long expressions scroll horizontally
   inside the step row, never overflow the page.

**`GraphPlay.jsx`** — deliberately small, hook-not-tool, but complete within scope:
- Plain SVG (no library). Axes + curve for `fn`, sampled at ~200 points over a
  sensible window around `a` (window = a±4 by default).
- Function evaluation: write a tiny safe evaluator supporting EXACTLY this grammar:
  numbers, `x`, `+ - * / ^`, parentheses, `|x|` (or `abs(x)`), `sin( ) cos( )`.
  Recursive-descent parser or shunting-yard, ~80 lines, NO `eval`, NO `new Function`
  on raw input. Handle division-by-zero as a discontinuity (skip the sample; render a
  hole marker if it's a removable hole at `a`).
- `mode: "limit"`: the `predict` question gates first (same hard-gate pattern). Then
  an Animate button walks two dots along the curve, one from each side of `a`, with a
  live 2-column value table (x, f(x)) filling in; open circle at the hole; when
  LHL ≠ RHL (e.g. |x|/x), the two dots visibly stop at different heights.
- `mode: "secant-tangent"`: fixed point at `a`; slider for `h` (range 2 → 0.01,
  log-ish steps); secant line through (a, f(a)) and (a+h, f(a+h)); live slope readout
  `slope = (f(a+h) - f(a))/h`; as h shrinks the secant visibly settles onto the
  tangent. The `predict` question gates before the slider unlocks.
- Both modes: dark mode comes free if you reuse existing color utility classes
  (see index.css override layer) — do NOT hardcode new hex values.

**`LessonView.jsx` wiring:** render `kind: "maths"` as: mental_model → sections/
explanation → DerivationPlayer (one per `derivation` entry) → GraphPlay (per entry) →
common_mistakes → recall_questions. Reuse the existing section components; add only
the two new blocks. Lazy-load the maths components (React.lazy) so KaTeX isn't in the
main bundle.

## Deliverable 4 — 3 golden lessons

Author from `class11deepresearch.md` nodes 1–3, at
`content/roadmaps/maths-11/{what-is-a-limit,left-and-right-hand-limits,algebra-of-limits}.json`
(`roadmap: "maths-11"` — content folder only; no DB seeding in this handoff):
- Convert each research node: canonical_derivations → `derivation` (attach `predict`
  at the researched `predict_worthy_steps`, building wrong options from the node's
  misconceptions: `wrong_move`/`wrong_path`/`feedback` map directly; `error_id` = the
  misconception id). Research `rules_glossary` → per-derivation `rules` — but DROP
  narration-only entries (`write-limit`, `simplify-arithmetic`, `evaluate-lhl`,
  `evaluate-rhl`): a rule must state a mathematical law, not a stage direction. Keep
  the step's `rule` ids consistent with what remains; rename steps to a kept rule or
  define a real law for them.
- `graph_play` from the research node's entries (node 3 has none — omit).
- Prose (`mental_model`, `sections`, mistakes, recalls) authored fresh under the
  beginner overlay register; the research `feedback`/`why` lines are already in
  register — reuse them verbatim where they fit.
- All three must pass `python content/validate.py`.

## Order of work + self-checks
1. Validator branch → 2. golden lessons (validator green) → 3. evaluator + its edge
cases (test `|x|/x` at 0, hole at removable discontinuity, `^` precedence) →
4. GraphPlay → 5. DerivationPlayer → 6. LessonView wiring → 7. `npm run build` green.
Then STOP and report — Claude runs the browser verification pass (render, predict
gates, wrong-path playback, mobile width, dark mode) before this is called done.
Report file: `content/REPORT-maths-runtime.md` — one line per deliverable + any FLAG.

## Boundaries
- No DB/seed/backend changes. No commits/pushes. No new dependencies beyond `katex`.
- Don't touch the DSA player or other roadmaps' content.
- If the spec fights reality somewhere (KaTeX quirk, layout constraint), implement the
  closest faithful version and FLAG it in the report — don't silently redesign.
