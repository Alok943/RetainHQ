# PROMPT — Test-Bank Authoring (global test system, all roadmaps)

Contract for Antigravity. One bank file per roadmap phase. Claude owns this contract; the critic
pass (Sonnet) reviews every bank against it before merge. Runtime spec: `docs/SPEC-test-runtime.md`.

> **What this is:** RetainHQ's Tests section — short, active, roadmap-native test sessions
> (fill-ups, code, SQL, numericals, traps, and *rare, JEE-grade* MCQs). NOT flashcards (reviews
> own that), NOT lessons. A test question must require **producing** the answer, not recognizing it.

---

## THE PHILOSOPHY (governs every authoring decision)

1. **Production over recognition.** Default formats make the user GENERATE the answer: type the
   output, write the fix, compute the number, fill the blank. MCQ is the exception, not the norm
   (rules below) — a plain recall-MCQ where a keyword gives it away is a REJECTED question.
2. **Traps are first-class.** ~1 in 4 questions carries `"trap": true`: the surface-obvious answer
   is wrong, and falling for it reveals a specific misconception. The reveal names the trap
   (`trap_note`) — the student learns more from a sprung trap than from ten easy corrects.
3. **Every question is tagged to a node.** `node` = the lesson slug it tests. Untagged questions are
   invalid — tagging is what makes results diagnostic (mastery per concept, FSRS feedback,
   "why am I stuck" evidence).
4. **Deterministic where possible, LLM only for fill-ups.** Code/query/numeric/MCQ grade
   mechanically. Fill-ups are graded by the LLM against your `answer` (canonical reference) — so
   the canonical answer must be complete and unambiguous, it IS the rubric.

## GOLD REFERENCES (copy their shape, depth, and trap craft — they set the bar)

Three verified sample banks exist. Every answer in them is machine-checked (code outputs executed,
asserts run against starter AND answer, queries run against the seed, numerics recomputed):

- `content/roadmaps/python-swe/_test/functions-and-pitfalls.json` — career/code bank: code-output
  traps (mutable default, late binding), fillup, code-fix with fail-on-starter asserts, code-write,
  and ONE legitimate MCQ (every distractor is a worked-out wrong mental model).
- `content/roadmaps/physics-9-10/_test/class-9-motion.json` — school bank: Hinglish prompts with
  English values/units, numerics with deliberate tolerance, the displacement-vs-distance trap, the
  v=0-so-a=0 trap, and a JEE-grade MCQ whose distractors are the EXACT numbers the three classic
  mistakes produce (8100 / 50 / 1250).
- `content/roadmaps/sql/_test/aggregation-basics.json` — SQL bank: query-write with seed data
  engineered so the wrong query is visibly wrong (one NULL row makes COUNT(*) ≠ COUNT(amount)).

Match their `explain` quality too: it names the principle and, for traps, exactly why the wrong
path felt right.

## File format

`content/roadmaps/<roadmap-key>/_test/<phase-slug>.json`:

```jsonc
{
  "slug": "<phase-slug>",            // filename = slug
  "title": "Test — <phase name>",    // required by the shared validator header (all kinds)
  "roadmap": "<roadmap-key>",
  "kind": "test",
  "tier": "tier1",                   // required; nominal for a bank (not a per-question difficulty)
  "metadata": { "difficulty": "medium", "interview_frequency": "high" },  // required; nominal
  "phase": "<exact phase name from the seed>",
  "questions": [ /* 12–20 per phase; session samples 5–6 */ ]
}
```

Every question object:

```jsonc
{
  "id": "<phase-prefix>-q07",        // unique within the file
  "node": "<lesson-slug>",           // REQUIRED — the concept this tests
  "type": "fillup" | "numeric" | "code-output" | "code-fix" | "code-write" | "query-write" | "mcq",
  "difficulty": "easy" | "medium" | "hard",
  "trap": false,                     // true → the obvious answer is wrong by design
  "trap_note": "...",                // REQUIRED when trap — names the trap, shown on reveal
  "prompt": "...",                   // the question. School roadmaps: Hinglish per the code-switch
                                     // policy (English technical terms/values); career: English.
  "explain": "...",                  // shown after attempt — the WHY, tied to the principle
  ...type-specific fields
}
```

## Type-specific rules

### `fillup` — short-answer, LLM-graded (the workhorse)
```jsonc
{ "type": "fillup",
  "prompt": "A body moves in a circle at constant speed. Its speed is constant but its ______ keeps changing, so it is accelerated.",
  "answer": "velocity (direction changes continuously, so the velocity vector changes even though speed is constant)",
  "accept": ["velocity", "direction of motion"] }   // optional keyword shortlist for offline fallback
```
- `answer` is the FULL canonical answer — it is the LLM's grading rubric AND what the student sees
  on reveal. Never a bare keyword; include the reasoning clause.
- One blank or one asked quantity per question. No double blanks.
- Blanks must target the LOAD-BEARING term (the concept), never trivia ("the unit is named after ____").

### `numeric` — computed answer, deterministic
```jsonc
{ "type": "numeric", "answer": 24, "tolerance": 0.5, "unit": "m/s",
  "prompt": "u = 0, a = 3 m/s^2, t = 8 s. Find v." }
```
- `tolerance` accounts for rounding paths (22/7 vs 3.14); set it deliberately, not 0.
- The prompt must state given values cleanly. Physics: board-exam style; aptitude: OA style.

### `code-output` — read code, type what it prints (deterministic, exact match)
```jsonc
{ "type": "code-output", "runtime": "python",
  "code": "def f(x, items=[]):\n    items.append(x)\n    return items\nprint(f(1))\nprint(f(2))",
  "answer": "[1]\n[1, 2]" }
```
- ≤ 12 lines of code. One concept per snippet. Output must be short and unambiguous (no dict
  ordering games, no float formatting surprises, no randomness/time).
- THE natural home for traps (mutable default, late-binding closure, `is` vs `==`, shallow copy).

### `code-fix` / `code-write` — Pyodide-graded against asserts (deterministic)
```jsonc
{ "type": "code-fix", "runtime": "python",
  "starter": "def add_item(x, items=[]):\n    items.append(x)\n    return items",
  "asserts": "assert add_item(1) == [1]\nassert add_item(2) == [2]",
  "answer": "def add_item(x, items=None):\n    if items is None:\n        items = []\n    items.append(x)\n    return items" }
```
- `asserts` must FAIL on the starter (code-fix) and pass on `answer`. Self-contained: no imports
  beyond stdlib available in Pyodide, no I/O, no network, runs < 1s.
- `code-write`: `starter` is a signature + docstring; keep the task ≤ 10 lines of solution.
- Career roadmaps only (college users are on laptops — these are keyboard questions).

### `query-write` — PGlite-graded by result-set diff (deterministic)
```jsonc
{ "type": "query-write",
  "prompt": "Return each customer's total order value, highest first.",   // the task, in the shared 'prompt' field
  "schema_sql": "CREATE TABLE orders (...); INSERT INTO orders VALUES (...);",
  "canonical_query": "SELECT customer_id, SUM(amount) ... ORDER BY 2 DESC",
  "order_matters": true }
```
- Seed data small (≤ ~12 rows) but engineered so wrong queries produce visibly wrong results
  (e.g. a NULL that breaks naive `COUNT(*)`, a duplicate that punishes a missing GROUP BY).
- `order_matters: false` → results compared as sets.

### `mcq` — the EXCEPTION; JEE-grade only
Allowed ONLY when the question requires multi-step reasoning where recognition doesn't help:
- the distractors are **worked-out wrong answers** (the number you get if you forget r², the output
  if the list aliased — each tagged `"misconception": "<name>"`), or
- assertion–reason format (A true, R true, R explains A?), or
- "which of the following are true" with 2+ correct (guessing odds collapse).
```jsonc
{ "type": "mcq", "options": ["2.01 x 10^20 N", "2.01 x 10^28 N", "5.2 x 10^11 N", "20.09 x 10^35 N"],
  "answer": 0,
  "misconceptions": [null, "forgot to square r", "used g instead of G", "forgot the denominator entirely"] }
```
- REJECT: definition MCQs, "which keyword…", anything answerable by keyword-click. If it can't
  earn JEE-grade, rewrite it as a fillup.
- Cap: ≤ 20% of any bank. (Scoring applies a guess penalty to wrong MCQ — see runtime spec —
  so don't author MCQs the student is meant to guess at.)

## Per-roadmap mix targets (bank composition)

| Roadmap | Primary types | Notes |
|---|---|---|
| python-swe / python-backend / cpp | code-output, code-fix, fillup, code-write | trap-rich (language pitfalls ARE traps) |
| sql | query-write, code-output(query-output), fillup | seed-data traps (NULLs, dupes) |
| dsa | code-output (trace), fillup (complexity, invariants), hard MCQ | keep runnable snippets small |
| core-cs / engineering | fillup-heavy, assertion-reason MCQ | concepts, not code |
| aptitude / reasoning | numeric, fillup | OA-style timing-friendly |
| physics-9-10 (school) | numeric, fillup, hard MCQ | Hinglish prompts, English values/units; numeric from board-exam patterns; NO code types |

Session assembly (runtime handles it, but author so it's possible): each bank needs ≥ 3 types
represented, ≥ 25% traps, ≥ 60% production formats (fillup/numeric/code/query).

## Trap authoring — the craft rules

- A trap must be a DOCUMENTED misconception (from the lesson's `common_mistakes`, the FCI-style
  physics misconceptions, or a language pitfall) — never a gotcha of wording, units-in-fine-print,
  or trick grammar. The student who falls must think "of course — I always do that", not "that's unfair".
- `trap_note` names the trap in one sentence and says what to watch for next time.
- Traps still have exactly one defensible correct answer.

## Self-review (per bank, before handing back)

1. Every `node` slug exists in the roadmap's lesson folder (`content/roadmaps/<key>/`).
2. Run every deterministic answer: code-output answers ARE the real output; asserts fail-on-starter
   and pass-on-answer; canonical queries run against the schema; numeric answers recomputed.
3. MCQ audit: for each MCQ, write one line on why recognition doesn't crack it. Can't? → fillup.
4. Trap ratio ≥ 25%, production ratio ≥ 60%, MCQ ≤ 20%.
5. `python content/validate.py` passes (test branch — see runtime spec).
