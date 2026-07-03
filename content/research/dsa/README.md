# DSA node research (structured, pre-authoring)

Deep-research output for the **DSA — Algorithms Visualized** roadmap, extracted to structured JSON
**before** lessons are authored. This is the input to lesson authoring — not the lesson itself.

## Layout
- `phase-<N>.json` — a JSON **array**, one object per node in that phase, each keyed by `slug`.
- The schema + field rules live in [`content/PROMPT-dsa-research.md`](../../PROMPT-dsa-research.md).

## Why this exists (not loose .md in Downloads)
Research left as prose reports outside the repo is invisible to the authoring pipeline and to
per-node lesson handoff packets. The **extracted JSON is the artifact; the prose report is a
byproduct.** Authoring transforms one node's JSON into a lesson — it does not re-synthesize from a
56 KB phase essay.

## Status
| Phase | Nodes | Prose report exists | JSON extracted |
|---|---|---|---|
| 1 Foundations | 3 | ✔ (`DSA Foundations Concept Research.md`) | ☐ |
| 2 Complexity | 5 | ☐ | ☐ |
| 3 Arrays | 4 | ✔ (`phase3.md`) | ☐ |
| 4 Hashing | 4 | ✔ (`phase4.md`) | ☐ |
| 5 Strings | 6 | ✔ (`phase5.md`) | ☐ |
| 6 Sorting — Basics | 3 | ✔ (`phase6.md`) | ☐ |
| 7 Searching | 5 | ✔ (`phase7.md`) | ☐ |
| 8 Two Pointers & Windows | 5 | ✔ (`DSA Pointers And Windows Research.md`) | ☐ |
| 9–20 | — | ☐ | ☐ |

> Prose reports currently sit in `~/Downloads`. Retro-extract each into `phase-<N>.json` per the
> "RESCUING OLD PROSE REPORTS" section of the research prompt (repair broken `![][imageN]` math to
> plain text; mark fields the old prompt didn't ask for in `confidence.low_confidence_fields`).
