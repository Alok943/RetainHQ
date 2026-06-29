# HANDOFF — integrate Antigravity-converted DSA lessons (read this first)

Context for a fresh chat. The previous chat got long; this captures exactly where things are so you
can continue. Read `docs/dsa-architecture.md` and `content/PROMPT-dsa-research.md` for the full design.

## IMMEDIATE TASK
Antigravity (Sonnet) converted the Phase-1 deep research into JSON. It currently sits at
**`content/phase1.md`** — a JSON array of 3 Foundations lessons (`what-is-an-algorithm`,
`tracing-state-and-invariants`, `iteration-and-traversal`). The CONTENT is good; it just needs 3
plumbing fixes to pass the validator and render:

1. **`kind`/`runtime` label.** They are `kind:"concept"` + `runtime:"python"`, but they have NO
   `code_walkthrough` — and the concept+python branch in `content/validate.py` (~line 500-512)
   REQUIRES one, so all 3 fail. These are no-code concept lessons. **Fix:** add a `runtime: "none"`
   option to the validator (`RUNTIMES` at line 25 → add `"none"`; in the runtime block ~line 500 skip
   the `code_walkthrough` requirement when runtime is `"none"`), then set `runtime:"none"` on the 3
   lessons. **Also verify `frontend/src/LessonView.jsx` renders a concept lesson when
   `code_walkthrough` is absent** (conditional-render it; don't crash).
2. **`roadmap` field.** They say `"dsa-foundations"`. Our seed (`backend/seed_dsa.py`) has ONE roadmap,
   slug **`dsa`**, with Foundations as a *phase*. **Fix:** set `roadmap:"dsa"` on all 3.
3. **One file per node.** Split `content/phase1.md` into
   `content/roadmaps/dsa/what-is-an-algorithm.json`, `.../tracing-state-and-invariants.json`,
   `.../iteration-and-traversal.json` (filename = slug). Delete `content/phase1.md` after.

Then: `python content/validate.py` (must end "All content valid. [OK]") →
`cd frontend && node scripts/sync-content.mjs` → start the preview and confirm one renders at
`/roadmaps/dsa/learn/what-is-an-algorithm` (note: the roadmap detail page needs `seed_dsa.py` run on
the DB to resolve by slug, but the static lesson page renders without the backend).

**Tell the user:** their conversion pipeline (SKILL.md + schema.json in Antigravity) should emit
`roadmap:"dsa"` and `runtime:"none"` for conceptual nodes so future phases come out clean.

## KEY DECISIONS (don't re-litigate)
- **DSA roadmap** = new, distinct from Striver/NeetCode problem lists. Slug `dsa`, title
  "DSA — Algorithms Visualized". Seed: `backend/seed_dsa.py` (110 nodes, 20 phases, beginner→interview;
  Foundations first, recursion deferred to phase 11). **Seed NOT yet run on the DB — user hand-off**
  (`cd backend && ./.venv/Scripts/python.exe seed_dsa.py`). contentRoadmaps mapping already added
  (`'DSA — Algorithms Visualized': 'dsa'`).
- **Mixed lesson kinds** (deliberate): **conceptual** nodes (what-is-an-algorithm, Big-O, design
  patterns, DP-thinking, why-greedy-fails…) = existing **`concept`** kind (with `runtime:"none"`);
  **trace/visualization** nodes (merge sort, BFS, Dijkstra…) = new **`dsa`** kind (execution-trace
  Player). Don't force a viz onto concept nodes or vice-versa.
- **The `dsa` kind**: validator branch already added in `content/validate.py` (the `if d.get("kind")
  == "dsa":` block). Frontend spine built + golden-tested in `frontend/src/dsa/` (events.js, compile.js,
  generators/merge-sort.js + merge-sort.golden.mjs, registry.js, renderers/ArrayViz.jsx,
  StateMachine.jsx, Player.jsx, DsaDev.jsx + a temp `/dsa-dev` route in App.jsx). **STILL TODO:** wire
  `kind:'dsa'` into `LessonView.jsx` (render path + the five-questions blocks + the lazy Player for
  `viz`), and author the merge-sort `dsa` lesson JSON as the trace gold reference.
- **Five questions** every DSA lesson answers (the quality bar): why it exists · how to mentally
  simulate · invariant/repeated-decision · real-world engineering use · how to recognize. See
  `docs/dsa-architecture.md`.
- **Research → lessons workflow:** Gemini runs `content/PROMPT-dsa-research.md` per phase → JSON →
  Antigravity converts to lessons → Claude reviews quality + builds the trace generators for viz nodes.

## UNCOMMITTED WORK (previous chat) — review/commit as a batch
Committed already: `5cbfe1d` (AI-Engineering content), `9caa0e7` (DSA architecture + spine).
Uncommitted (all on `main`): `backend/seed_dsa.py`, `content/validate.py` (dsa branch + sections/
vector-space earlier), `content/PROMPT-dsa-research.md`, `content/PROMPT-images.md` + `_TODO-images.md`
updates, `frontend/src/lib/contentRoadmaps.js`, `frontend/src/dsa/Player.jsx` (caption-on-top +
read-pause rework), renderers, `DsaDev.jsx`, `frontend/src/App.jsx` (temp /dsa-dev route),
`frontend/package.json` (framer-motion), `docs/dsa-architecture.md` updates. Plus this handoff.
Commits: authored SOLELY by the user, NO `Co-Authored-By: Claude` trailer. Work on `main`.

## OTHER PENDING USER HAND-OFFS (DB/prod — never fire at the live DB yourself)
- Run prod migrations `alembic upgrade head` (slug + node_id) — still pending.
- Run `seed_dsa.py` (creates the DSA roadmap).
- AI-Engineering: 6 thin nodes flagged for an Antigravity deepen-pass (guardrails-and-validation,
  memory-short-and-long-term, multi-step-planning, react-reason-act, streaming-responses,
  tool-use-and-the-call-loop). Images: anchor + embeddings done in `_image-staging/`; tokens needs a
  regen (anchor-contamination); upload to Supabase `lesson-images` bucket.
