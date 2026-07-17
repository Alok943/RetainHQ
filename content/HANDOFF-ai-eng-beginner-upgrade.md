# HANDOFF — AI-Engineering beginner upgrade (P0 #1)

> Paste the block below into Antigravity (repo access required). Saved here so the
> mission survives session resets — point a fresh session at this file to resume.
> Status: NOT started.

---

You are upgrading the AI-Engineering lessons of RetainHQ to a beginner-first standard.
This is a REWRITE PASS of existing lessons, not net-new authoring: all 36 nodes already
have a lesson file. Work inside this repo.

## Read these files FIRST, fully, in this order — they are the contract
1. `content/PROMPT-engineering.md` — the base contract for `kind: "engineering"`. Note
   two recently added sections: **AUDIENCE & OVERLAYS** and **PREDICTION RUNG**.
2. `content/PROMPT-beginner-overlay.md` — the beginner overlay. **Where it conflicts
   with the base contract, the OVERLAY WINS.** Read the Terminology guard twice: the
   schema field `tier: tier1|tier2|tier3` means item difficulty; the audience being a
   "tier-3 college student" must NOT make you generate `tier3` (advanced) items.
3. `content/roadmaps/ai-engineering/embed-and-retrieve-top-k.json` — the gold reference
   for shape and depth. Your output keeps this structure; only the register changes.

## The mission
For EVERY lesson in `content/roadmaps/ai-engineering/` (36 files), rewrite it to satisfy
the overlay rules B1–B11 while preserving everything that is already correct:

**Rewrite (the register):**
- All prose fields — `hook`, `mental_model`, `sections` bodies, `code_snippets`
  explanations, `key_points`, `common_mistakes`, `recall_questions` answers,
  `oa_questions` answers — to overlay register: plain B1-level English, sentences
  under ~20 words, no idioms, every technical term defined in plain words at first use,
  one consistent name per concept, max 7 new terms per lesson.
- First `code_snippets` entry per lesson: ≤8 lines, one idea, no untaught syntax.
  Later snippets may stay at base-contract length.
- Examples: apply the one-unknown rule (overlay B2). First examples use familiar-domain
  data; the framework-real version comes last, labeled as a bridge.
- Every `oa_questions` answer OPENS with a 1–2 sentence plain-words version, then the
  detailed one. Keep company tags exactly as they are.

**Add (the prediction rung — see PREDICTION RUNG in the base contract):**
- A `hook` whose `question` asks the reader to PREDICT something concrete, where the
  lesson lacks one.
- At least ONE predict-style `recall_questions` item ("what happens if <concrete
  change>?", `tier: "tier2"`) per lesson, where the lesson lacks one.

**Preserve (do NOT touch):**
- Slugs, filenames, `kind`, field structure, `sources`, `animation`/`image`/
  `illustration` blocks, company tags, and every factual claim that is correct.
- Do NOT invent new JSON fields — the validator ignores them and the renderer never
  shows them; anything like `"faded_example": {...}` is silently lost work.
- Do NOT delete depth. Simplify the LANGUAGE, never the TRUTH (overlay B9): if a rule
  has three cases, all three stay, in plain words.

## Workflow (per batch of 5–6 lessons)
1. Rewrite the batch.
2. Run `python content/validate.py` — every file must stay green. Fix before moving on.
3. Append one line per lesson to `content/REPORT-ai-eng-beginner-upgrade.md`:
   `<slug> — rewritten: <fields touched> | prediction rung: <added|already present>`.
4. Continue to the next batch until all 36 are done.

## Boundaries
- You are the AUTHOR. Do NOT critique your own output — the critic pass runs later on a
  different model (`content/PROMPT-lesson-critic.md`, with its beginner-batch checks).
- Do NOT commit, push, or touch anything outside `content/roadmaps/ai-engineering/` and
  the report file.
- If a lesson resists the register without losing correctness (dense math, unavoidable
  jargon), do your best pass and flag it in the report line with `FLAG: <one-line why>`
  instead of silently shipping a bad compromise.
