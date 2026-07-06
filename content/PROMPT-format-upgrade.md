# Handover — lesson format + depth upgrade pass (ALL roadmaps)

> One pass per roadmap. Paste the fenced block below into the agent (Antigravity), replacing
> `{{ROADMAP_DIR}}` and `{{CONTRACT}}` from the rollout table. The renderer already supports
> the new format globally (bullets, inline code chips, code blocks) — this pass upgrades the
> CONTENT to use it. Section 1 (python-swe) already ran; its block is kept below for reference.
>
> **Rollout order** (pitch + build priority): 1 python-swe ✅ → 2 sql → 3 physics-9-10 (school
> pitch) → 4 ai-engineering → 5 dsa → 6 python-backend → 7 core-cs → 8 aptitude (quant +
> reasoning kinds) → 9 cpp-swe (in-authoring; new lessons already follow the updated contract).

---

## Rollout table — parameters per roadmap

| # | `{{ROADMAP_DIR}}` | `{{CONTRACT}}` | prose fields to upgrade | edge-flag flavour |
|---|---|---|---|---|
| 2 | `sql` | `content/PROMPT-sql.md` (rules 11–12) | `overview.what/why`, mistakes, answers, `why` | `NULL = NULL` unknown; `COUNT(col)` vs `COUNT(*)`; join row multiplication; WHERE vs HAVING. Every query MUST still run against `content/roadmaps/sql/_dataset.sql`. |
| 3 | `physics-9-10` | `content/PROMPT-physics.md` (FORMATTING section) | `explanation`/`sections[].body`, worked-example narration | Board traps (mass vs weight, sign convention, current direction). PRESERVE the Hinglish/English split; backticks go on formulas/units/values. NEVER alter numbers, math, or English recall/oa answers. |
| 4 | `ai-engineering` | `content/PROMPT-engineering.md` (Formatting block) | `sections[].body`/`explanation`, snippet `explanation`, `key_points[].detail` | Production traps inline: "more chunks ≠ better", temperature-0 ≠ deterministic, "the model doesn't run your tool". |
| 5 | `dsa` | `content/PROMPT-dsa.md` (Prose formatting section) | `sections[].body`/`explanation`, `mental_model.description` | Off-by-one bounds, overflow in `mid` (fixed-width langs), degradation cases. NEVER touch `viz` blocks. |
| 6 | `python-backend` | `content/PROMPT-backend.md` (Formatting section) | same as ai-engineering | The ground-truth war-story list in the contract (MissingGreenlet, N+1, blocking-in-async…). |
| 7 | `core-cs` | `content/PROMPT-coreCS.md` (Formatting section) | `explanation`, `mental_model.description` | Misconception flags with forward pointers (thrashing, reliable ≠ fast, mutex ≠ semaphore). Promote parallel-item runs to `key_points` where they ARE the concept's parts. |
| 8 | `aptitude` | `content/PROMPT-aptitude.md` + `content/PROMPT-reasoning.md` (FORMATTING bullets) | mental_model description, discovery/rule text, shortcut/trick text, approaches | Light pass: backtick math, split dense sentences, one in-teach trap flag. Lessons are THIN by design — do not add depth. |

Validation: `python content/validate.py` after every batch (it has a branch per kind).
For `python-swe`/`sql` concept lessons, `content/schema.json` also applies.

---

## THE GENERIC PASS (paste this block, after substituting the two placeholders)

```
You are upgrading EXISTING lesson JSON files in content/roadmaps/{{ROADMAP_DIR}}/ to the
formatting + depth standard already live in the renderer. This is a REFORMAT-AND-ENRICH
pass, NOT a regeneration: preserve every correct fact, example, question, and each lesson's
single analogy. You are restructuring prose and adding missing edge-case coverage — nothing else.

CONTRACT: {{CONTRACT}} — its FORMATTING and EDGE-CASE FLAG rules are the spec for this pass.
Follow that contract's field names, language policy, and hard rules exactly; where this
block and the contract disagree, the contract wins.

GOLD STANDARD for the format (read first): content/roadmaps/python-swe/lists.json —
match its rhythm: short prose -> code -> bullets -> flagged trap -> analogy.

THE RENDERER supports exactly three block types inside any long prose field, separated by
BLANK lines (\n\n in the JSON string):
  a) Prose paragraphs — 1-3 sentences MAX. Split anything denser.
  b) Code blocks — every line indented 2 spaces, blank line before and after.
  c) Bullet lists — every line starts with "- " at COLUMN 0 (indented lines render as
     code, so never indent a bullet). One item per line.
Inline: wrap identifiers, calls, formulas, and expressions in `backticks` — they render as
code chips in ALL prose fields (bodies, mistakes, answers, why), so use them everywhere.

PER-FILE TASKS (apply all that are relevant):
1. KILL RUN-ON ENUMERATIONS: any list of 3+ parallel items written as a paragraph or as
   newline-separated pseudo-list becomes a real "- " bullet block (or the contract's
   key_points field when the items ARE the concept's parts). Method/operation bullets
   state: what it does, what it RETURNS, and how the failure path behaves.
2. SPLIT DENSE PARAGRAPHS: no paragraph over 3 sentences. Prose -> example -> prose rhythm.
3. EDGE-CASE FLAGS: add every sharp edge of the topic that bites in real work, even when a
   LATER roadmap topic owns the full treatment. A flag = a short example showing the trap
   firing + 1-2 prose sentences naming the rule + a forward pointer "covered fully in
   <slug>" when a topic in metadata.unlocks (or a sibling node) owns it. The rollout table
   entry for this roadmap names the canonical flags. Do NOT expand a flag into the later
   lesson — plant the hook only.
4. BACKTICK ALL INLINE CODE/FORMULAS in every prose field of the file.
5. CONSISTENCY REPAIR: if task 3 added a new fact to the teach, you MAY add (never remove)
   a matching recall_question / check / common_mistake for it. Everything tested must
   appear in the teach; never test what the lesson doesn't teach. If depth grew
   meaningfully, bump metadata.estimated_minutes by 5.

HARD CONSTRAINTS:
- Never change: slug, title, roadmap, kind, tier, prerequisites, unlocks, sources
  (you may APPEND a source a new flag needs).
- Never delete existing questions, checks, tasks, challenges, viz blocks, diagrams,
  animations, or images. Never touch code_walkthrough/aha_moment/viz code semantics.
- Keep exactly ONE analogy per lesson (the existing one).
- All examples must be correct — mentally dry-run every snippet/query/derivation you add.
  For sql: every query runs unmodified against _dataset.sql. For physics: never alter
  numbers or English exam-layer text. No invented APIs, no toy examples.
- Valid JSON after every edit. \n for newlines inside strings, quotes escaped.

VALIDATE after every batch (from repo root): python content/validate.py

WORK ORDER: alphabetical, batches of ~10 files. After each batch, report: files done,
flags added per file (one line each), files where you were unsure. Do not commit — leave
the working tree for review.

DEFINITION OF DONE per file: no run-on enumerations; no paragraph >3 sentences; every
inline identifier/formula backticked; every real-world trap of the topic flagged with an
example; validate.py green.
```

---

## Section 1 — python-swe (RAN — kept for reference)

> The original python-swe block. Its output is the ~100 modified files under
> `content/roadmaps/python-swe/` awaiting review.

```
You are upgrading EXISTING lesson JSON files in content/roadmaps/python-swe/ to a new
formatting + depth standard. This is a REFORMAT-AND-ENRICH pass, NOT a regeneration:
preserve every correct fact, example, question, and the lesson's single analogy. You are
restructuring prose and adding missing edge-case coverage — nothing else.

GOLD STANDARD (read these three files FIRST, before touching anything):
  content/roadmaps/python-swe/lists.json          <- full exemplar, match this quality
  content/roadmaps/python-swe/dictionaries.json   <- bullet + edge-flag pattern
  content/roadmaps/python-swe/tuples.json         <- edge-flag pattern
These three are DONE — skip them.

CONTRACT: content/PROMPT.md, especially rule 16 (formatting) and rule 28 (edge-case
flags). Schema: content/schema.json. Every output must still validate.

THE RENDERER supports exactly three block types inside overview.what (and any long prose
field), separated by BLANK lines (\n\n in the JSON string):
  a) Prose paragraphs — 1-3 sentences MAX. Split anything denser.
  b) Code blocks — every line indented 2 spaces, blank line before and after.
  c) Bullet lists — every line starts with "- " at COLUMN 0 (indented lines render as
     code, so never indent a bullet). One item per line.
Inline: wrap every identifier, call, literal, and expression in `backticks` — they render
as code chips. This works in ALL prose fields (overview, common_mistakes.explanation,
answers, why, etc.), so use backticks everywhere, not just in overview.

PER-FILE TASKS (apply all that are relevant):
1. KILL RUN-ON ENUMERATIONS: any list of 3+ parallel items (methods, rules, options,
   cases) written as a paragraph or as newline-separated pseudo-list becomes a real
   "- " bullet block. Method bullets must state: what it does, what it RETURNS (call
   out the ones returning None), and which exception the failure path raises.
2. SPLIT DENSE PARAGRAPHS: no paragraph over 3 sentences. Prose -> code -> prose rhythm.
3. EDGE-CASE FLAGS (rule 28): add every sharp edge of the topic that bites in real code,
   even when a LATER roadmap topic owns the full treatment. A flag = a 3-6 line code
   block showing the trap firing + 1-2 prose sentences naming the rule + a forward
   pointer "covered fully in <slug>" when a topic in metadata.unlocks owns it. Examples
   of the level required: list copies are shallow; tuple immutability protects slots
   not contents; dict.copy() is shallow; except order matters; closures late-bind.
   Do NOT expand a flag into the later lesson — plant the hook only.
4. BACKTICK ALL INLINE CODE in every prose field of the file.
5. CONSISTENCY REPAIR: if task 3 added a new fact to overview.what, you MAY add (never
   remove) a matching recall_question, understanding_check, or common_mistake for it.
   Everything tested must appear in overview; never test what the overview doesn't teach.
   If depth grew meaningfully, bump metadata.estimated_minutes by 5.

HARD CONSTRAINTS:
- Never change: slug, title, roadmap, kind, tier, prerequisites, unlocks, sources
  (you may APPEND a source if a flag needs one, e.g. docs.python.org/3/library/copy.html).
- Never delete existing questions, checks, tasks, or the challenge.
- Keep exactly ONE analogy per lesson (the existing one).
- All code must be runnable and correct — mentally dry-run every snippet you add.
- No invented APIs. No toy examples (no foo/bar, no class Dog).
- Valid JSON after every edit. \n for newlines inside strings, quotes escaped.

VALIDATE after EVERY file (from repo root):
  python -c "import json,jsonschema; from pathlib import Path; s=json.loads(Path('content/schema.json').read_text(encoding='utf-8')); d=json.loads(Path('content/roadmaps/python-swe/<FILE>.json').read_text(encoding='utf-8')); jsonschema.validate(d,s); print('OK')"

WORK ORDER: alphabetical, batches of ~10 files. After each batch, report: files done,
flags added per file (one line each), files where you were unsure. Do not commit — leave
the working tree for review.

DEFINITION OF DONE per file: no run-on enumerations; no paragraph >3 sentences; every
inline identifier backticked; every real-world trap of the topic flagged with a code
example; schema-valid JSON.
```
