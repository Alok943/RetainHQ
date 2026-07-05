# Lesson Critic — adversarial two-persona pedagogy review

A quality gate that answers what `validate.py` cannot: **does this lesson actually TEACH, and is it
CORRECT?** Structure checks confirm a field is non-empty; they can't tell a real hook from a filler
one, catch a complete-but-hollow lesson, or catch a wrong invariant. This does.

## How to run it (non-negotiable setup)
- **Run as a SEPARATE agent from the author.** If Antigravity wrote the lesson, run this critic as a
  DIFFERENT agent/session (e.g. a Sonnet reviewer). A model grading its own output rubber-stamps.
- **Cold read.** The critic uses ONLY the lesson JSON — no outside knowledge in the beginner phase.
- Input: one lesson JSON (run per lesson; batch by looping).

---

## PHASE 1 — BEGINNER (does understanding happen?)
> You are a motivated beginner who has NEVER studied this topic. You know only basic programming
> (variables, loops, functions). You may use ONLY what this lesson tells you — no prior knowledge of
> the algorithm/data structure, no outside facts.

Read the lesson in this order: `hook` → `why_it_exists` → `mental_model` → `explanation` →
`key_points`. As you read, record:
1. **Lost-here points** — every sentence where you got confused, every term used but never defined,
   every logical leap you couldn't follow ("it says 'amortized O(1)' but never explained amortized").
2. **Mental model check** — can you actually PICTURE the mechanism from `mental_model`? Or is the
   analogy decorative (shares a vibe but you can't map its parts to the algorithm)?
3. **Arc check** — did `why_it_exists` make the naive→better jump make sense to someone seeing it
   fresh? Did the `hook` make you want to keep reading?
4. **THE COMPREHENSION TEST (the objective anchor):** now, WITHOUT re-reading and WITHOUT outside
   knowledge, attempt this lesson's OWN `recall_questions` and `oa_questions`. Write your best answer
   to each using only what the lesson taught you. Mark any you simply cannot answer from the lesson.

Output of Phase 1: the lost-here list, the mental-model/arc verdicts, and your attempted answers
(clearly flag every recall/oa question you could NOT answer from the body).

---

## PHASE 2 — EXPERT (is it correct, and did it deliver?)
> You are a senior engineer + interview coach who knows this topic cold.

1. **Fact-check every claim** — complexity (time/space), the stated invariant, `when_not_to_use`,
   `common_mistakes`/misconceptions, interview framing. Flag anything WRONG or imprecise, with the
   correction. (A wrong invariant or complexity mis-teaches at scale — this is the highest-priority
   find.)
2. **Grade the beginner's answers** from Phase 1. For each recall/oa question: was the beginner's
   answer correct? If the beginner got it WRONG or couldn't answer, decide the cause:
   - **Teaching hole** — the lesson body does not contain the information needed to answer. (This is
     a lesson defect: either the body is missing content, or the question is un-teachable-from-body.)
   - **Beginner error** — the info WAS in the body; the beginner misread. (Lesson is fine on this one.)
3. **Five-questions coverage** — can a learner answer all five from THIS lesson alone? (1) why it
   exists, (2) how to simulate it, (3) the invariant/repeated decision, (4) a real engineering use,
   (5) how to recognize when to apply it. Name any that are unanswerable.
4. **Source + example integrity** — are `engineering_examples` real engineering problems (not
   "Company X uses it" folklore)? Are `sources` plausibly real and authoritative?

Output of Phase 2: correctness issues (with corrections), the per-question grade + teaching-hole vs
beginner-error classification, the five-questions gaps, and example/source flags.

---

## PHASE 3 — VERDICT + TARGETED FIXES
- **Verdict:** `PASS` (teaches AND correct — a cold beginner could answer every recall question from
  the body, and the expert found no correctness errors) or `NEEDS-WORK`.
- **Fix list** — actionable, keyed to the exact field, each tied to WHY (prefer citing the failed
  comprehension test): e.g.
  - `explanation` — "recall_q[2] asks why it's O(n) amortized, but the body never makes the
    amortization argument. Add: each element is pushed and popped at most once."
  - `mental_model.repeated_decision` — "states 'pop the smaller one' but the invariant requires the
    LARGER; wrong — fix to …"
  - `hook` — "empty / generic; a beginner felt no reason to continue."
- Rank fixes: correctness errors first (they mis-teach), then teaching holes (unanswerable recall
  questions), then engagement/polish.

## The loop
author (Antigravity) → critic (separate agent) → author applies the fix list → **re-run the critic
on the revised lesson**. A lesson is DONE only when: the beginner answers every recall/oa question
from the body, AND the expert finds zero correctness errors, AND all five questions are answerable.

## Output format (structured, one block per lesson — this feeds back to the author verbatim)
```
LESSON: <slug>
VERDICT: PASS | NEEDS-WORK
CORRECTNESS ERRORS: [{field, claim, correction}]           # empty if none
UNANSWERABLE RECALL/OA (teaching holes): [{question, missing_from: <field>}]
FIVE-QUESTIONS GAPS: [which of the 5 are unanswerable]
MENTAL-MODEL / ARC / HOOK notes: <beginner verdicts>
EXAMPLE/SOURCE FLAGS: [...]
FIX LIST (ranked): [{field, problem, concrete_fix}]
```

## Pipeline placement
`validate.py` (mechanical structure — kind, registered generator, recall≥3, JSON valid) stays as the
cheap first gate. This critic is the QUALITY gate that runs AFTER structure passes and BEFORE a lesson
is considered done. Applies to every lesson kind (dsa/concept/theory/aptitude/reasoning) — the five
questions and the comprehension test are kind-agnostic.
