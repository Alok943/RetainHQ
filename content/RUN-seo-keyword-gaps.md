# Run the P1-A keyword-gap content pass in Antigravity

A runbook for adding the keyword-gap sections from `docs/SEO-IMPLEMENTATION.md` §P1-A to 6 existing
lessons. This is an EDIT task on live, already-published lessons — not new-lesson generation. Paste the
block below into a fresh Antigravity chat.

## Why this exists

GSC shows searchers landing on these 6 pages for sub-topics the lesson text never actually names. The fix
is real teaching content (a new `sections` entry, or a sentence woven into an existing one) that happens
to use the exact phrase searchers type — not keyword stuffing bolted onto the side.

## Two hard rules

1. **Augment, don't rewrite.** Read the full lesson JSON first. Every other field (existing `sections`,
   `code_snippets`, `common_mistakes`, `recall_questions`, `oa_questions`, `metadata`, `seo`, etc.) stays
   byte-identical. You are adding ONE new `sections[]` entry (or, where noted, one sentence inside an
   existing one) per row below — nothing else in the file changes.
2. **Match the lesson's own voice.** Read 2-3 of the lesson's existing `sections[].body` paragraphs before
   writing the new one. Same register, same level of assumed knowledge, same use (or non-use) of Hinglish/
   code-switching if the lesson has it. A new section that reads like a different author wrote it is a
   critic-flaggable defect, not a win.

## Contracts

- `engineering` kind (rag-evaluation, uvicorn-gunicorn-workers, pydantic-settings, the-gil):
  `content/PROMPT-engineering.md`
- `dsa` kind (queue-and-deque, selection-sort): `content/PROMPT-dsa.md`
- `sections[]` shape (both kinds): `{body, recap?, title?, image?, animation?}` — `title` is optional and
  rarely used elsewhere in the corpus; a bare `<h2>`-less body paragraph block is the norm, so don't invent
  a heading unless the lesson already titles its sections.
- Gate: `python content/validate.py` must pass with 0 errors after every edit (also flags oversized
  `seo.title`/`seo.description`, unrelated to this task but don't trip it).

---

=== PASTE INTO ANTIGRAVITY ===

You are adding keyword-gap content to 6 EXISTING lessons in `content/roadmaps/`. This is an augmentation
pass, not authoring from scratch — read each full lesson JSON first, match its existing voice, and change
ONLY what's listed below. Every other field in each file must stay byte-identical.

For each lesson: add the new content as one appended entry to the `sections[]` array (a `{body: "..."}`
object — 2-4 sentences, written to teach, using the exact query phrase naturally) unless the row says to
edit an existing sentence instead. Read `content/PROMPT-engineering.md` (for engineering-kind lessons) or
`content/PROMPT-dsa.md` (for dsa-kind lessons) for voice/depth calibration before writing.

1. **content/roadmaps/ai-engineering/rag-evaluation.json** (engineering) — add a "The RAG triad" section:
   context relevance, groundedness, answer relevance (queries `rag triad` / `rag evaluation framework`
   already land on this page but it never names the triad). Add one sentence naming RAGAS and TruLens as
   frameworks that implement these same three metrics.

2. **content/roadmaps/python-backend/uvicorn-gunicorn-workers.json** (engineering) — add TWO sections:
   (a) "Gunicorn worker classes" — sync, gthread, and `uvicorn.workers.UvicornWorker`, what each is for.
   (b) "How many workers?" — the `2 × cores + 1` heuristic and when it's the wrong answer (e.g. I/O-bound
   async work under Uvicorn workers doesn't need many). Both are distinct GSC queries hitting this page.

3. **content/roadmaps/python-backend/pydantic-settings.json** (engineering) — ensure the exact phrase
   "reading environment variables" (or very close to it) appears explicitly, not just implied by talking
   about `.env` files. If YAML config is covered anywhere in the lesson, name `YamlConfigSettingsSource`
   explicitly (a GSC query) — otherwise skip this clause, do not invent YAML coverage that isn't there.

4. **content/roadmaps/dsa/queue-and-deque.json** (dsa) — add a short "Deque vs dequeue" naming note:
   searchers write "dequeue in data structure" and "deque vs dequeue" (2 distinct GSC queries) — clarify
   that "dequeue" is the operation (remove from front) while "deque" is the double-ended-queue data
   structure, and that this is a common naming confusion.

5. **content/roadmaps/dsa/selection-sort.json** (dsa) — add a short "Is selection sort stable?" note
   answering the exact GSC query `selection sort is stable or not`: the standard array-swap implementation
   is NOT stable (swapping can reorder equal elements), though a variant using insertion instead of
   swapping can be made stable at the cost of more writes.

6. **content/roadmaps/python-backend/the-gil.json** (engineering) — do NOT add a new section. Instead,
   edit the lesson's opening explanation so the exact phrase "Global Interpreter Lock (GIL)" (full name +
   acronym together) appears in the FIRST paragraph, if it doesn't already — read the current opening
   first, this may already be satisfied. Also confirm `threading-vs-multiprocessing` is already linked via
   `metadata.prerequisites`/`unlocks`/`related` (it should be — the generator's hardcoded topical-link map
   already cross-links these two pages regardless); if not linked in metadata, add it to `related`.

After every file edit, run `python content/validate.py` from the repo root and fix any errors before
moving to the next lesson. When all 6 are done, report a short per-lesson summary: what you added, and the
resulting word count delta.

=== END PASTE ===
