# Maths research — PORTABLE (paste into gemini.google.com, Deep Research mode preferred)

Self-contained research prompt for the Class 11 **Limits & Derivatives** pilot
(`docs/PLAN-school-maths-runtime.md` §5). No repo access needed — everything the model
must know is inline. For later chapters, reuse this file and swap the node list in §THE NODES.

## How to use
1. Open Gemini (gemini.google.com), pick **Deep Research** if available (better
   misconception sourcing); plain chat with search also works.
2. Paste everything inside the `=== RESEARCH PROMPT ===` block.
3. The model returns nodes in batches of 3 as JSON; reply **next** after each batch.
4. Concatenate all batch arrays into ONE array and save as
   `content/research/maths-limits-derivatives.json`. Check it parses:
   `python -c "import json; json.load(open('content/research/maths-limits-derivatives.json', encoding='utf-8'))"`
5. Hand the file to Claude — the lesson/runtime schema gets hardened against it before
   any bulk generation.

---

=== RESEARCH PROMPT ===

You are doing a deep-research pass for a learning app's Class 11 maths chapter:
**Limits & Derivatives (NCERT Class 11, Chapter 13, CBSE)**. You are NOT writing
lessons. You are producing the structured research a lesson author and an interactive
"step player" will be built from. Accuracy beats volume: everything you output will be
shown to students, so a wrong derivation or an invented misconception mis-teaches at
scale.

CONTEXT — what your output feeds (so you know what matters):
- The app teaches with spaced repetition. Students see a derivation one STEP at a time
  and must PREDICT the next step before it is revealed. The wrong options shown to them
  ("distractors") come from YOUR misconception bank — so each misconception must be a
  concrete wrong MOVE, not a vague misunderstanding.
- If a student picks a wrong move, the app can play 1-2 steps down that wrong path
  until it visibly breaks, then rewind. So each misconception needs the actual wrong
  steps it produces.
- Some concepts get an interactive graph: a "limit" view (animate x approaching a from
  left/right with a value table, open-circle holes, asymptotes) and a "secant-tangent"
  view (drag h toward 0, watch the secant become the tangent, live slope readout).
  Suggest a graph entry ONLY where the picture genuinely teaches the idea.

AUDIENCE — write every explanation string for this reader:
A Class 11 student at a rural/small-town Indian school. English is their second or
third language. Rules for every "why" and "feedback" string you write:
- Plain English, sentences under 20 words, no idioms, no culture-bound metaphors.
- Define any technical term in plain words the first time it appears.
- One consistent name per concept (never rotate synonyms).
- Never condescending, never cheerleading. State the rule plainly.

THE NODES — produce ONE research object per node, exactly this ground:
1. What a limit is (intuition; value approached ≠ value at the point)
2. Left-hand and right-hand limits; when a limit does not exist
3. Algebra of limits (sum/product/quotient rules)
4. Evaluating limits: direct substitution and 0/0 factorisation
5. Evaluating limits: rationalisation
6. Standard limits: (x^n − a^n)/(x − a)
7. Standard limits: sin x / x and (1 − cos x)/x (radians!)
8. Limits at infinity and rational functions
9. Derivative as instantaneous rate of change
10. Derivative as slope of the tangent (secant → tangent)
11. Derivative from first principles
12. Algebra of derivatives (sum, product, quotient rules)
13. Derivatives of polynomials
14. Derivatives of trigonometric functions
15. Where derivatives fail: |x| and non-differentiable points

OUTPUT SHAPE — a JSON object per node, exactly this schema:

{
  "node": "Derivative from first principles",
  "ncert_ref": "Ch 13, section and example numbers",
  "assumed_class10": ["algebraic identities", "rationalisation", "basic trig ratios"],
  "misconceptions": [
    {
      "id": "limit-is-value-at-point",
      "wrong_move": "evaluating f(a) directly when the function has a hole at a",
      "why_students_do_it": "ten years of 'plug in the number' — substitution is the only tool they trust",
      "wrong_path": ["the substitution step as the student would write it", "the 0/0 or undefined result it produces"],
      "feedback": "The limit asks what f approaches NEAR a, not what f IS at a — check the left and right values first.",
      "exam_frequency": "high | medium | low"
    }
  ],
  "canonical_derivations": [
    {
      "goal": "d/dx (x^2) from first principles",
      "steps": [
        { "expr": "\\lim_{h \\to 0} \\frac{(x+h)^2 - x^2}{h}", "rule": "first-principles-def", "why": "The definition: slope of the secant as h shrinks to 0." },
        { "expr": "\\lim_{h \\to 0} \\frac{2xh + h^2}{h}", "rule": "expand-and-cancel", "why": "Expand (x+h)^2. The x^2 terms cancel." },
        { "expr": "\\lim_{h \\to 0} (2x + h)", "rule": "factor-h", "why": "Divide top and bottom by h. This is allowed because h is never exactly 0 inside a limit." },
        { "expr": "2x", "rule": "evaluate-limit", "why": "As h goes to 0, the h term vanishes." }
      ],
      "predict_worthy_steps": [2, 3],
      "distractor_ids": ["cancel-h-equals-zero-confusion", "drop-h-too-early"]
    }
  ],
  "graph_play": [
    {
      "mode": "secant-tangent",
      "fn": "x^2",
      "prediction": "As h shrinks, the slope of the secant line approaches…",
      "teaches": "the derivative IS a limit — the two ideas are one picture"
    }
  ],
  "exam_question_types": ["evaluate a 0/0 limit by factorisation (1-2 marks)", "first-principles derivative of a polynomial (4 marks)"],
  "rules_glossary": [
    { "id": "factor-h", "statement": "You may cancel h because inside a limit h approaches 0 but never equals 0." }
  ]
}

FIELD RULES:
1. misconceptions is the heart of this pass — 3 to 6 per node. Each must be a REAL,
   documented student error: source from NCERT Exemplar "common errors", CBSE examiner
   reports / marking-scheme notes, and maths-education research on limits and
   derivatives. NEVER invent one. Every distractor_id referenced in a derivation must
   exist in some node's misconceptions.
2. canonical_derivations: 1-3 per node (the derivations that chapter's marks depend
   on). Every expr in LaTeX (KaTeX-compatible), with backslashes escaped for JSON
   (\\lim, \\frac). DRY-RUN THE ALGEBRA before emitting — verify each step actually
   follows from the previous one. predict_worthy_steps lists step indices (0-based)
   where hiding the step and asking "what comes next?" is a fair question — never
   index 0.
3. rules_glossary: every rule id used in any step, defined ONCE across the whole
   output, in plain words. These lines become the memorizable facts students drill.
4. graph_play: only modes "limit" or "secant-tangent"; only where the picture teaches
   (limit-intuition nodes, derivative-as-slope). Pure-algebra nodes get an empty list.
5. These traps MUST appear somewhere in the bank: degrees-vs-radians in sin x/x;
   |x| non-differentiable at 0 (left and right slopes differ); "the limit exists but
   f(a) does not"; cancelling h and then claiming h = 0 is contradictory; dropping the
   'h → 0' notation mid-derivation.
6. exam_question_types: the CBSE board question shapes for this node with marks, from
   real papers (2015-2025).

PROCESS:
- Research first, then emit. Cite ncert_ref per node so claims are checkable.
- Respond with nodes 1-3 as a JSON array (no commentary, no markdown fences around
  individual objects — one fenced JSON block per batch is fine). I will reply "next"
  for each following batch of 3 until all 15 are done.
- If a misconception cannot be sourced beyond your own intuition, either drop it or
  mark it "exam_frequency": "unsourced" so the reviewer can judge it.

=== END RESEARCH PROMPT ===
