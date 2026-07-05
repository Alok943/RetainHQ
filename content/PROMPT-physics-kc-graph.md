# PROMPT — NCERT Physics (Class 9–10) Knowledge-Component Graph

Paste everything below the line into the generating model. No slots to fill — this prompt is fully specified.

---

## Role & product context

You are a curriculum architect + cognitive scientist building the **knowledge-component (KC) map** for RetainHQ's school platform.

RetainHQ is a retention engine: every concept a student learns becomes a spaced-repetition card (FSRS scheduler), and concepts live on a **prerequisite graph** so the system can (a) diagnose *why* a student is stuck by walking edges backwards, and (b) recommend the next learnable concept ALEKS-style (the "outer fringe": concepts whose prerequisites are all mastered).

**This deliverable:** the complete concept inventory + prerequisite graph for **NCERT Science — Physics portions, Class 9 and Class 10 (CBSE)**. This is the spine of a school pilot whose pitch is: *"students forget August's chapters by the March board exam; we guarantee they don't."* The Class 9 → Class 10 dependency edges are therefore the single most valuable part of this graph — they are what lets the system say "you're failing refraction numericals in Class 10 because your Class 9 'speed vs velocity' concept has decayed."

You are producing **structured data**, not lessons, not explanations, not a syllabus summary.

## Source of truth

- **NCERT Science textbooks, Class 9 and Class 10 (current rationalized editions)** — Physics chapters only:
  - Class 9: Motion · Force and Laws of Motion · Gravitation (incl. flotation/thrust & pressure as per current edition) · Work and Energy · Sound
  - Class 10: Light — Reflection and Refraction · The Human Eye and the Colourful World · Electricity · Magnetic Effects of Electric Current
- Include the math tools these chapters actually use (graph reading, unit conversion, ratio manipulation, squaring/square roots in formulas) as explicit KCs **only where a physics KC genuinely depends on them** — tag these `section: "Math tools"`.
- Do NOT include: chemistry/biology chapters, deleted/rationalized-out topics, Class 11+ material, or Olympiad extensions. Board-exam scope only.

## Granularity — the one governing rule

A KC is an **ALEKS-style "item": one concept or one problem-type**, at the grain where a teacher would say "the student has/hasn't got *this*." Calibration:

- ✅ Right grain: "Distinguish distance from displacement" · "Read speed off a distance–time graph" · "Apply v = u + at to find final velocity" · "State and apply the law of reversibility in mirror ray diagrams" · "Compute equivalent resistance of resistors in series"
- ❌ Too coarse (umbrella — reject): "Motion" · "Understand electricity" · "Numericals on light"
- ❌ Too fine (micro-skill — reject): "Substitute u=0 into v = u + at" · "Recall the symbol for resistance"

Test for every KC: **(1)** it can be checked with 1–3 short questions in under 3 minutes, **(2)** a student can plausibly have mastered it while NOT having mastered its neighbors, **(3)** it will still be worth reviewing 6 months later (board-exam relevance).

**Target size: 150–250 KCs total across both classes.** This is a hard honesty band, not a quota — the research this design follows (ALEKS/KST: ~300–500 items per full multi-year course; Cognitive Tutor's 6,000-KC failure mode: over-practice of trivia) says padding is worse than missing. If a chapter honestly yields 12 KCs, output 12. Never split to inflate count; never merge to hide complexity.

Each KC needs a `recall_hint`: **one line, ≤120 chars, containing the testable claim itself** — the answer, not a description of studying. `"F = ma; net force, not any force."` ✅ — `"Learn Newton's second law"` ❌.

## Prerequisite edges — rules

An edge `A → B` means: **a student who has NOT mastered A will predictably fail B**, and a teacher remediating B would send the student back to A. That is the only justification for an edge.

1. **Strict necessity, not helpfulness.** "Related to" / "taught before" / "same chapter" are NOT edges. If a student could master B cold without A, there is no edge.
2. **No transitive redundancy.** If A→B and B→C exist, do not also add A→C. Emit the transitive reduction.
3. **DAG required.** No cycles. Verify before output.
4. **Fan-in cap: ≤4 prerequisites per KC.** If you want 5+, your KC is too coarse — split it.
5. **Cross-year edges are mandatory and must be flagged.** Every Class 10 KC that leans on a Class 9 KC gets an explicit edge (e.g., Electricity's "potential difference = work done per unit charge" → Class 9 "Work done by a force = Fs cosθ" chain; refraction speed-change reasoning → Class 9 speed concepts; magnetic force on a conductor → force/motion KCs). List these separately in the audit section — they are the pilot's core demo.
6. **Roots must be genuinely primitive.** KCs with zero prerequisites should be things a Class 9 entrant actually walks in with (basic arithmetic, everyday notions). If a mid-graph KC has no in-edges, you likely forgot an edge.

## Output format

Produce ONE fenced Python code block, drop-in compatible with RetainHQ's existing seed pattern (`seed_*.py` + `seed_*_prereqs.py`), containing exactly two literals:

```python
# (phase, section, title, tier, recall_hint)
NODES = [
    ("Class 9 · Motion", "Describing motion", "Distinguish distance from displacement", "easy",
     "Distance = path length (scalar); displacement = shortest start→end vector; can be zero."),
    ...
]

# title -> [titles that must be mastered BEFORE it]
# Every title on either side MUST appear verbatim in NODES.
PREREQS = {
    "Read speed off a distance-time graph": ["Define average speed as distance/time"],
    ...
}
```

Field rules:
- `phase` = `"Class 9 · <Chapter short name>"` or `"Class 10 · <Chapter short name>"` — the chapter spine, in textbook order.
- `section` = a thematic cluster inside the chapter (2–8 KCs each); math-tool KCs use section `"Math tools"` under the phase where first needed.
- `title` = the KC, specific and self-contained; **unique across the whole file** (titles are the foreign key for edges — a duplicate silently corrupts the graph).
- `tier` = `easy` / `medium` / `hard` for the target student (Class 9–10 CBSE, mixed-ability private-school cohort). Numericals with multi-step algebra skew hard; single-fact recall skews easy.
- `recall_hint` = per the rule above. Plain ASCII (write `v = u + at`, `theta`, `ohm` — no Unicode math), no double quotes inside the string.

## Self-review — do this, then revise ONCE

Before final output, attack your own graph as a skeptical physics teacher with 10 years of board-exam experience:

1. **Coverage sweep:** walk every NCERT chapter's exercise section (including numericals) — is every exercise type mappable to a KC? Name any orphan question type and fix it.
2. **Edge audit:** sample 15 random edges — for each, state the failure a missing prerequisite would cause in ≤1 sentence. Any edge you can't justify that way, delete.
3. **Grain audit:** find your 5 coarsest and 5 finest KCs; re-check them against the calibration examples.
4. **Cycle + dangling-title check:** mechanically verify PREREQS titles all exist in NODES and no cycle exists.

Then output the final version.

## Final deliverable structure

1. The Python code block (NODES + PREREQS).
2. **Counts:** total KCs, per-chapter KCs, total edges, count of Class 9→Class 10 cross-year edges.
3. **Cross-year edge list:** every Class 9 → Class 10 edge as `A -> B`, one per line (the pilot demo material).
4. **Exclusions:** 5–10 things you deliberately left out (too fine / rationalized out of NCERT / not board-tested) — one line each.
5. **Self-review notes:** the 3–8 criticisms from the review you accepted and what changed.
