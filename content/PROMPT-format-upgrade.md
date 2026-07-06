# Handover — python-swe lesson format + depth upgrade pass

> Paste everything in the fenced block into the agent (Antigravity). It works file-by-file
> through `content/roadmaps/python-swe/*.json`. The contract lives in `content/PROMPT.md`
> (rules 16 and 28 are the new ones this pass enforces).

---

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
