# RetainHQ — Content Curation Rig ("caveman" edition)

A dead-simple, decoupled workspace for producing **topic content** with
**Gemini 3.1 Pro** (free via Google AI Pro). This folder has **no dependency on
the RetainHQ app code** — it only produces clean, schema-valid JSON files. A
separate seed step ingests them into the app later.

## Division of labor

| Step | Who | Cost |
|---|---|---|
| Generate topic content (prose, questions, tasks) | **Gemini 3.1 Pro** | free (your quota) |
| Validate + file + catch slop | **Claude Code** | cheap |
| Ingest into RetainHQ roadmaps | a seed script (later) | n/a |

You never spend paid API on bulk content.

## The loop (per topic)

1. Open `_TODO.md`, pick the next unchecked topic.
2. Open `PROMPT.md`, copy it, replace `{{TOPIC}}` / `{{ROADMAP}}` / `{{PREREQS}}`, paste into **Gemini 3.1 Pro**.
3. Gemini returns **one JSON object**. Save it as `roadmaps/<roadmap>/<slug>.json`.
4. Run the validator (catches missing fields, broken prereq refs, missing sources):
   ```bash
   python content/validate.py
   ```
5. Fix anything it flags (re-prompt Gemini if needed), then tick the box in `_TODO.md`.

## Folder layout

```
content/
  README.md          ← this file
  PROMPT.md          ← the golden Gemini prompt (the one artifact that matters)
  schema.json        ← the content contract (human reference)
  validate.py        ← caveman validator (pure stdlib, no installs)
  _TODO.md           ← curation queue, check off as you go
  roadmaps/
    python-swe/
      closures.json  ← golden hand-made example (the quality bar)
```

## Rules that keep the content good (enforced by the prompt)

- **Docs-as-truth:** every topic cites an official-docs URL in `sources`. No invented APIs.
- **No toy examples** (`class Dog: bark()`). Anchor to real code — FastAPI, Pydantic, micrograd, stdlib.
- **Recall questions must be answerable from `overview`** — no un-captured gotcha trivia.
- **`prerequisites` / `unlocks` are slugs** (e.g. `"first-class-functions"`), so they become graph edges on ingest.

## Start here

Curate the **Functions → Closures → Decorators** chain first (~6 topics). Validate
the whole loop on a small chain before mass-producing. `closures.json` is the
golden reference — match its shape and depth.
