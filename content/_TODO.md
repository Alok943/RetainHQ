# Curation queue

Tick a box once the topic's JSON is saved **and** `python content/validate.py` passes.
Curate top-to-bottom so prerequisites exist before the topics that reference them.

## python-swe — first chain (validate the loop on these ~6 before scaling)

- [ ] functions
- [ ] scope
- [ ] args-kwargs
- [ ] first-class-functions
- [x] closures   ← golden hand-made reference (already done)
- [ ] decorators

## python-swe — backlog

_(Pull the full ~130-topic list from the seed scripts when the chain above feels good.
 Add them here as slugs, in dependency order.)_

## Notes

- One JSON file per topic: `roadmaps/<roadmap>/<slug>.json`.
- Feed Gemini the slugs you've already done (the `{{PREREQS}}` placeholder) so it
  reuses them instead of inventing new prerequisite slugs.
