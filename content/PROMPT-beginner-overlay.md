# Beginner overlay — P0 lesson generation for the tier-3 college student

> **What this is:** an OVERLAY contract, not a new lesson kind. Paste it into Antigravity
> **after** the base contract for the roadmap you're generating (`PROMPT.md` for python-swe,
> `PROMPT-engineering.md` for ai-engineering, `PROMPT-dsa.md` for dsa). Where this overlay
> conflicts with a base rule, **the overlay wins** — each override names the base rule it
> replaces. Everything not overridden still applies (schema shape, validator, JSON rules,
> docs-as-truth, formatting grammar).
>
> **Scope:** the three P0 batches in `docs/PLAN-lesson-generation.md` — ai-engineering
> finish-out, DSA new families, python-swe gap-fill — and any later batch the founder tags
> "beginner-first".

---

## ⚠️ Terminology guard — read this before anything else

The lesson schema has a field `tier: tier1|tier2|tier3` meaning **difficulty of that item
within a topic** (tier1 = state it, tier3 = advanced). This document is about a
**tier-3 COLLEGE student** — an Indian college ranking band, nothing to do with that field.
The two meanings collide head-on: **do NOT generate "tier3" (advanced) items because the
audience is "tier-3"**. In this doc, the audience is always called **the learner**; the
schema field is always written `tier:`.

## The learner (design for this person, not for us)

- First- or second-year BTech student at a tier-3 college. Often the first coder in the family.
- **English is a second or third language.** Reads technical English slowly; idioms and
  cultural references silently fail.
- **Exam-trained**: excellent at memorizing definitions, weak at predicting what code does.
  Rote is their superpower and their trap — use it, then break it (rule B11).
- **AI-assisted from day one**: has ChatGPT/Gemini write code they cannot read back. They've
  "completed" tutorials; they can't trace five lines of it unaided.
- Has NOT used: a debugger, a REPL habitually, git beyond `clone`, any web framework.
  Has used: WhatsApp, UPI, train booking, Excel-ish marksheets, cricket score apps.
- Goal (same ceiling as every RetainHQ learner): **placed**. The floor drops; the ceiling
  — interview-grade recall at 30 days — does not move. Every lesson must still climb there.

**The one-line test for every field you write:** *could this learner read it aloud, then
explain it to a friend in their own words, without translating anything twice?*

---

## Overlay rules (B1–B11)

**B1 — Language register.** Plain English, roughly B1 level. Sentences average under 20
words. No idioms, no slang, no culture-bound metaphors ("footgun", "under the hood",
"bites you", "rabbit hole"). Say "trap" not "gotcha", "error" not "blow up". Prefer
concrete numbers to adjectives ("runs 1000× slower", not "much slower"). This applies to
EVERY prose field: overview, explanations, sections, answers, `why` strings.

**B2 — One-unknown rule (overrides base PROMPT.md rules 2 and 22 for FIRST examples).**
An example may contain **at most ONE thing the learner has not yet been taught.** The base
contract bans toy examples and demands FastAPI/Pydantic anchors — for this learner that
stacks unknowns: the concept is new AND the framework is new, so nothing lands.
Corrected rule:
- FIRST examples use **familiar-domain real data**: a marks list, a cricket scorecard, a
  UPI transaction dict, train seats, a contacts list, OTP validation, a playlist. Real
  data from the learner's life — this is NOT a toy (the ban on `foo/bar`/`class Dog`
  stands: those are meaningless, which is a different sin from unfamiliar).
- The LAST example or `where_used` may show the framework-real version (a FastAPI route,
  a Pydantic model) explicitly labeled: *"you will build this in the backend roadmap —
  notice it is the same pattern."* Plant the bridge; don't teach through it.

**B3 — Worked example FIRST (reorders the base learning arc).** The base arc starts at
Predict. A beginner cannot predict behaviour they have never once seen — that's a
guessing game, and losing it on line one teaches "I'm bad at this". Beginner arc:
1. **Show** — a worked example, narrated line by line (what each line does, in order).
2. **Show again, faded** — the same shape with ONE step left blank for the learner to fill.
3. **Predict** — now `understanding_checks` and `aha_moment` fire, and they're fair.
4. **Explain → Vary → Apply** — unchanged from base.
`aha_moment` stays (it's still the highest-value field) but may never be the learner's
first contact with the concept.
**No new JSON fields for this arc** — it lives entirely inside existing fields (the worked
and faded examples are code blocks in `overview.what` / `sections` bodies; predictions are
the existing `understanding_checks` / `aha_moment` / `hook.question`). The validator ignores
invented fields and the renderer never shows them, so anything like `"faded_example": {...}`
is silently lost work.

**B4 — Code budget.** First-exposure snippets ≤ 8 lines. Every line must be readable using
only already-taught syntax — no comprehensions, decorators, ternaries, chained calls, or
f-string tricks before the roadmap teaches them. One idea per snippet. If the base
contract's 12–15-line ceiling tempts you, split into two snippets with one sentence between.

**B5 — Analogy locality (tightens base rule 21).** Still exactly one analogy, still mapped
back explicitly. Choose situations from the learner's daily life where natural — a railway
waiting list for a queue, a tiffin box for a container, UPI collect-request for
request/response. Test: *would this learner's non-coder friend recognize the situation?*
Never force local color where a universal analogy is cleaner — familiarity is the rule,
nationality is not.

**B6 — Sharp-edge budget (overrides base rule 28's "flag EVERY sharp edge").** Maximum
**two** edge-case flags per lesson — the two that will actually bite in the learner's
first month. Front-loading every trap is cognitive overload for a novice and reads as
"this language hates me". The other edges belong to the lesson that owns them; the
forward-pointer convention ("covered fully in <slug>") still applies to the two you keep.

**B7 — Recall ladder starts at reproduction.** The FIRST recall question of every lesson is
always: *"Explain <concept> in your own words, as if to a classmate."* (model answer =
2–3 plain sentences). Then the ladder climbs unchanged — `tier:` tier1 state-it →
tier2 apply/debug — to the SAME interview-grade top rung as the base contracts. Lower
floor, same ceiling.

**B8 — Jargon ledger.** A lesson may introduce at most **7 new technical terms**. Each is
defined in plain words at first use, in the same sentence or the one after — never
"defined later". If the topic genuinely needs more than 7, the topic is two lessons;
flag it in the TODO instead of cramming. (Terms already in the glossary pipeline —
`GlossaryTerm` chips — count as free once previously taught.)

**B9 — Respect, not dilution.** No motivational filler, no "don't worry, this is easy!",
no exclamation-mark cheerleading. This learner is an adult who reads condescension
instantly. Honesty about difficulty is allowed and useful: *"most people need two passes
at this — that is normal."* Simplify the LANGUAGE, never the TRUTH: if the real rule has
three cases, teach three cases in plain words; don't teach two and call it done.

**B10 — Term stability.** One concept = one word for the whole lesson. Never rotate
synonyms for style ("function/routine/method", "parameter/argument" used loosely,
"list/array" interchangeably). Synonym rotation reads as *new concept* to a second-language
reader. If two terms genuinely differ (parameter vs argument), teaching the difference is
content — do it explicitly once, then stay consistent.

**B11 — Use the exam brain, then break it.** This learner memorizes brilliantly. Give
every core rule a **crisp, memorizable statement** (one bolded line — they WILL memorize
it), and then pair it with one predict-style check that pure rote CANNOT answer. The pair
is the pedagogy: the memorized line gets them talking in an interview; the prediction
check makes sure the line is attached to a working model, not just recited.

---

## Per-P0 application

### python-swe gap-fill (40 nodes: Testing + Engineering Practices) — base: `PROMPT.md`
- Kind `concept`, full base schema. Overlay B1–B11 on top; B2/B3/B6 explicitly override
  base rules 2/22, the Tier-A-first arc's opening rung, and rule 28.
- Domain note: these are tooling topics (pytest, mock, git, project structure). The
  familiar-domain rule adapts — the code under test is code this learner has already
  written in this roadmap (an average-marks function, a dedupe function), NOT a FastAPI
  service. Testing a function you wrote yesterday is the honest beginner framing.
- `code_walkthrough` still runs in Pyodide: git/CLI topics that can't run set the
  walkthrough to a pure-Python analogue or drop to prose + `sections` (validator allows it).

### ai-engineering finish-out — base: `PROMPT-engineering.md`
- Kind `engineering`. Overlay applies to `hook`, `mental_model`, `sections` bodies,
  `code_snippets` explanations, `common_mistakes`, both question sets.
- **Known gap (see Proposed contract changes #2):** this kind has NO `understanding_checks`
  field — the highest-value probe type is missing from the P0 #1 roadmap. Until the
  validator + renderer gain it, emulate: (a) `hook.question` is mandatory in beginner
  lessons, phrased as a prediction; (b) at least one `recall_questions` item per lesson is
  a *"what happens if..."* predict-style question (tier2), not a state-it question.
- `code_snippets` are not executed (they call LLM APIs) — B4's 8-line budget applies to
  snippet 1 of each lesson; snippets 2–3 may grow to the base ~20-line ceiling as the
  lesson climbs.
- `oa_questions` keep their company tags (aspiration is a feature), but every `answer`
  must OPEN with a 1–2 sentence plain-words version before the detailed one.

### DSA new families (backtracking / linked-list / tree / graph) — base: `PROMPT-dsa.md`
- The FIVE questions and the ⛔ no-viz boundary are unchanged — Claude still adds the trace.
- Mental simulation uses **tiny concrete inputs**: arrays of ≤5 elements, real values
  (names, marks — not `a, b, c`), and a hand trace written as a step list in `sections`
  ("Step 1: window is [10, 20]; sum = 30…"). The learner must be able to run the algorithm
  on paper before any visualization exists.
- `oa_questions`: same plain-words-first rule as ai-engineering.
- B11 lands naturally here: the memorizable line is the **invariant** ("the window never
  contains a repeated character"), the rote-breaking check is a trace on an input that
  tempts the wrong model.

---

## Critic additions (beginner batches only)

The critic pass (`PROMPT-lesson-critic*.md`, run per D-016 on a non-author model) gains
five beginner checks. Each is a hard finding, not a style note:
1. **Stacked unknowns** — any example containing 2+ untaught things (B2).
2. **Register breach** — idioms, culture-bound metaphors, or >30-word sentences in prose (B1).
3. **Term-before-definition** — a technical term used before its plain-words definition (B8).
4. **Cold-open prediction** — a predict-style probe before any worked example (B3).
5. **Synonym rotation** — the same concept named two ways in one lesson (B10).

---

## Contract changes — status

Applied to the contracts themselves (2026-07-12; no app code touched):
- **Overlay composition + precedence** is now declared at the top of `PROMPT.md`,
  `PROMPT-engineering.md`, and `PROMPT-dsa.md` ("overlay wins on conflict"), so pasting
  base + overlay into any writer model resolves contradictions deterministically.
- **Prediction rung for `engineering` kind** is now a base-contract rule for ALL audiences
  (PROMPT-engineering.md "PREDICTION RUNG"): predict-phrased `hook.question` preferred +
  ≥1 predict-style `recall_questions` item — the contract-only substitute for the missing
  `understanding_checks` field.
- **The five beginner critic checks** now live in both critic contracts
  (`PROMPT-lesson-critic.md` Phase 2 #6, `PROMPT-lesson-critic-external.md` Phase 2 #5),
  gated on the batch being overlay-authored.

Still open (need app-code changes — founder to schedule, NOT for the writer model):

1. **`tier` naming collision.** Schema `tier: tier1-3` (difficulty) vs "tier-3 student"
   (college band). The Terminology guard above is the stopgap; the right fix is renaming
   the field to `depth` in schema + validator + renderer (mechanical, ~3 files).
2. **`engineering` kind still lacks a real `understanding_checks` field** — the prediction-
   rung rule above is a workaround, not the fix. Adding the field to validate.py's
   engineering branch + rendering it in LessonView remains the proper change.
3. **Formatting grammar is duplicated across contracts** (PROMPT.md rule 16, the
   engineering renderer-contract paragraph, the DSA prose rules) with slight drift.
   Extract once into `content/FORMAT.md` and reference it everywhere.
4. **The base arc is expertise-tuned.** If beginner batches perform (retention metrics
   will tell), make the learning arc a per-audience parameter of the base contract
   instead of an overlay override.
5. **Audience is baked into each contract's identity line.** Long-term: contracts take an
   audience block as an input (like `{{TOPIC}}`), this overlay becomes the "beginner"
   value — one contract, N audiences, no forks.
