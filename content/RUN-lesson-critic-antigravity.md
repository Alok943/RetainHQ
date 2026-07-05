# Run the lesson-critic sweep in Antigravity (Gemini 3.1 Pro, file access)

A runbook for driving the adversarial lesson critic over a whole roadmap using Gemini 3.1 Pro inside
Antigravity (which can read the repo files directly). The RUBRIC is `content/PROMPT-lesson-critic.md`;
this doc is the RUN instructions. Paste the block below into a fresh Antigravity chat.

## Two hard rules before you start
1. **Critic must NOT be the author.** Run this in a session SEPARATE from the one that wrote the
   lessons. A model grading its own output rubber-stamps. If Gemini authored a roadmap, have it critic
   a DIFFERENT roadmap, or start a clean session and instruct it to be adversarial (below).
2. **Report-only by default.** The critic WRITES A FINDINGS FILE; it does NOT edit lessons. Fixes are a
   separate, deliberate pass so you can eyeball each change. (An optional "apply" mode is at the bottom.)

## Sweep order (biggest / most load-bearing first)
python-swe (102) -> core-cs (61) -> aptitude (40) -> dsa (37) -> ai-engineering (36) -> sql (34).
Do ONE roadmap per run. Each writes `content/CRITIC-REPORT-<roadmap>.md`.

---

=== PASTE INTO ANTIGRAVITY ===

You are an ADVERSARIAL LESSON CRITIC. First read the rubric at
`content/PROMPT-lesson-critic.md` and follow it exactly. You did NOT write these lessons — be a genuine
skeptic whose job is to FIND defects, not to praise. Do NOT rubber-stamp. But only flag REAL defects (a
wrong claim, or a question genuinely unanswerable from the lesson body) — never style nits.

TASK: critic every lesson in the roadmap folder **content/roadmaps/<ROADMAP>/** (set <ROADMAP> to e.g.
`python-swe`). For each `*.json` file:
1. Read the FULL lesson JSON.
2. Run the two-persona critic from the rubric:
   - PHASE 1 (cold beginner): using ONLY the lesson body, attempt the lesson's OWN `recall_questions`,
     `understanding_checks`, and `oa_questions`. Flag any not answerable from the body.
   - PHASE 2 (expert): fact-check EVERY claim (language semantics, complexity, invariants,
     common_mistakes, interview framing; for code/`engineering` lessons, verify each `code_snippet` is
     correct and compilable-by-inspection). Classify each missed question as TEACHING HOLE (body lacks
     the info) vs BEGINNER ERROR (info was there).
   - Five-questions coverage: can a learner answer all five from THIS lesson alone? (1) why it exists,
     (2) how to simulate it, (3) the invariant/repeated decision, (4) a real engineering use, (5) how to
     recognize when to apply it.

Lessons come in kinds (`concept`, `dsa`, `engineering`, `aptitude`, `theory`, `reasoning`); the five
questions and the comprehension test are kind-agnostic. The body lives in fields like `overview`,
`why_it_exists`, `mental_model`, `explanation`, `sections`, `key_points`, `code_snippets`.

OUTPUT: WRITE your findings to **content/CRITIC-REPORT-<ROADMAP>.md** (create it). Do NOT modify any
lesson file. Emit exactly one block per lesson:

    LESSON: <slug>
    VERDICT: PASS | NEEDS-WORK
    CORRECTNESS_ERRORS: [{field, wrong_claim, correction}]     # [] if none
    TEACHING_HOLES: [{question, missing_from_field}]           # Qs unanswerable from body; [] if none
    FIVE_QUESTIONS_GAPS: [which of the 5 are unanswerable]     # [] if none
    EXAMPLE_SOURCE_FLAGS: [...]                                # [] if none
    FIX_LIST: [{field, problem, concrete_fix}]                # ranked correctness-first; [] for PASS

VERDICT is PASS only if a cold beginner can answer every recall/oa question from the body AND the expert
found zero correctness errors AND all five questions are answerable. Otherwise NEEDS-WORK.

Work through the folder in filename order. Do NOT stop until every lesson in the folder has a block.
If the folder is large, process ~10 lessons, append them to the report file, then continue — but finish
the whole folder in this run. End the report with:

    SUMMARY: <X> PASS, <Y> NEEDS-WORK out of <N>. NEEDS-WORK slugs: [...].
    SYSTEMIC PATTERNS: <1-3 lines on defects that recurred across lessons>.

=== END PASTE ===

---

## After the report
- The `FIX_LIST` blocks are structured to hand straight back to the AUTHOR (Antigravity, separate
  session) to apply — then RE-CRITIC the revised lessons. A lesson is DONE only when it comes back
  clean (beginner answers everything from the body, expert finds zero errors).
- Keep `CRITIC-REPORT-<roadmap>.md` in the repo as the audit trail; delete once its fixes land.

## Optional: apply mode (only if you want the critic to also fix)
Change OUTPUT to: "For each NEEDS-WORK lesson, ALSO apply the FIX_LIST directly to the lesson JSON,
then run `python content/validate.py` and confirm it ends 'All content valid. [OK]'. Keep edits minimal
and ASCII-only (use `--` not an em-dash, `->` not an arrow glyph — a re-save recently corrupted em-dashes
into mojibake). Still write the report so there's a record of what changed." Riskier (author == fixer),
so review the diff.

## Note on the DSA roadmap
For `dsa`, the visualizer (`viz`) is Claude-owned and some lessons legitimately have no `viz` block yet
(prose-first, viz added later) — that is EXPECTED, not a defect. Critic the prose/teaching only; do not
flag a missing `viz`.
