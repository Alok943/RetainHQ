# Decision log

Append-only log of non-obvious product/architecture decisions, **from 2026-07-10 onward**. **Append new entries at the END** with the next D-NNN number (numbers = insertion order, not chronology — extracted entries may carry earlier dates). One entry per decision — what, why, tradeoffs, date of the decision. Future sessions read this instead of asking "didn't we already decide this?"

> Decisions made **before** 2026-07-10 are documented in `CLAUDE-ARCHIVE-2026-07.md` ("Decisions / conventions" section) and `SYSTEM-OVERVIEW.md`. Do not migrate them here.

Template:

```markdown
## D-NNN — <short title> (YYYY-MM-DD)
**Decision:** what we chose.
**Why:** the reasoning that would otherwise be re-litigated.
**Tradeoffs / rejected:** what we gave up or ruled out, and why.
```

---

## D-001 — Repo-as-memory documentation layer (2026-07-10)

**Decision:** Restructured project documentation around "the repository is the memory, not the chat":
- `CLAUDE.md` rewritten as a lean rules + update-routing file (~100 lines); the old ~450-line version (half of it a frozen build log) archived verbatim at `docs/CLAUDE-ARCHIVE-2026-07.md`.
- Added `docs/claude-code-workflow.md` (session discipline + token economy), this file (go-forward decision log), and `docs/BACKLOG.md` (idea inbox).
- `docs/SYSTEM-OVERVIEW.md` remains the single living source of truth for system state — deliberately **no** separate `STATE.md`.

**Why:** Anthropic's guidance is that CLAUDE.md loads before every message of every session, so a bloated file is both a per-message token tax and a cause of ignored instructions; durable knowledge belongs in files Claude reads on demand. The founder's observed bottleneck was project memory trapped in ~22 parallel chats ("didn't we already decide this?").

**Tradeoffs / rejected:**
- *Rejected `STATE.md`* — would fork the truth SYSTEM-OVERVIEW already owns under a stricter (verified, same-commit) convention.
- *Rejected nested `frontend/CLAUDE.md` / `backend/CLAUDE.md`* for now — root CLAUDE.md already carries both sides' conventions compactly; nested files would add context, not save it. Revisit if either side's rules outgrow the root file.
- *Rejected one-doc-per-chat* — chats are disposable; docs map to durable topics, or they rot like the old `API.md`/`FLOWS.md`.

---

## D-002 — Physics KC-graph granularity + Hinglish authoring policy (2026-07-05)

**Decision:** The NCERT Physics 9-10 knowledge-component graph targets a **150–250 KC honesty band**, not a padded-to-match number — final came in at 126 KCs / 140 prereq edges / 8 cross-year (Class-9→10) edges. Lesson prose splits by register: **hook/mental-model/explanation in Hinglish, but technical terms, formulas, `recall_hint`s, and `oa_questions` answers stay in English.**

**Why:** The research inputs (ALEKS/KST) suggested 300–500 concepts per multi-year course, but that figure is for a *full* course; padding NCERT Physics 9-10 to match would recreate the Cognitive Tutor over-practice failure the same research flagged (6,000+ KCs → students over-drill trivial nodes). Hinglish-for-teaching mirrors how Indian physics teachers actually teach (explain in Hinglish, board work in English) and keeps the *testable claim* — what an FSRS card actually quizzes — aligned with what CBSE boards demand in English.
**Tradeoffs / rejected:** Rejected matching the source research's 300–500 figure literally. Rejected full-Hinglish content (drills the wrong target for board exams) and full-English content (loses the pedagogical win of native-language explanation for Tier 2/3 students).

---

## D-003 — Physics interactive 3D scope: R3F concept simulators, not a game engine (2026-07-07)

**Decision:** 3D is scoped to exactly **6 concept families** (`orbit`, `magnetic-field`, `fleming-rule`, `em-induction`, `dispersion-prism`, `longitudinal-wave`) via React Three Fiber, lazy-loaded so non-3D lessons never pull in Three.js. Explicitly **not** applied to graphs, circuits, numericals, or mirror/lens ray diagrams (the existing 2D SVG renderers stay). Each scene follows **Predict → (optional Manipulate) → Observe → Reflect**, reusing the app's existing predict-before-reveal UI rather than a parallel prediction system; manipulation is per-scene opt-in (discrete choices only, no sliders), not mandatory. Every scene's physics lives in a pure `computePhysics(params) → derived` function, separate from the Three.js render — **no formula/binding DSL in the lesson JSON**, formulas stay in code.

**Why:** Unity/Unreal were considered and rejected for a mobile-first (₹8–12k Android) product: Unity WebGL ships a 10–30MB runtime with no data-driven content contract; Unreal has no browser export path at all (Pixel Streaming needs a GPU server per session). R3F hits the quality ceiling that matters for teaching (clean, smooth, correctly-lit) at a fraction of the cost, and a photorealistic Earth actively *hurts* learning by pulling attention off the force vector. The litmus test for scope ("if a scene isn't predictable/changeable, it's not thinkable — keep it 2D") prevents 3D becoming decoration.
**Tradeoffs / rejected:** Rejected a JSON `formula:`/`bindings:` mini-language (would mean shipping an expression evaluator into the runtime). Rejected mandatory manipulation on every scene (extra state/UI/mobile-frame cost for no guaranteed learning gain). Rejected designing the primitive library for Chemistry/Math/DSA now — DSA already has its own 2D execution-trace renderer and is a different paradigm; generalize only when a second subject actually needs it.

---

## D-004 — Tests section: production-formats-first, one-way FSRS bridge, redemption lap (2026-07-10)

**Decision:** The Tests section defaults to **production-format questions** (fillup, numeric, code-output, code-fix, code-write, query-write) — MCQ is capped at ≤20% of a bank and allowed only when JEE-grade (multi-step reasoning, distractors that are worked-out wrong answers tagged with a named misconception). ~25%+ of questions carry a `trap: true` flag (an engineered wrong-but-obvious answer) with a `trap_note` explaining it on reveal. Grading is deterministic client-side for every type except `fillup`, which is the **one** LLM call (`grade_fillup`, gated on `GRADER_ENABLED`, canonical-answer-grounded). **FSRS bridge is one-way**: a `wrong`/`missed` test outcome pulls an *existing* due review forward (`apply_fsrs(..., RATING_AGAIN)`) only if the node already has an `Activity`+open `Review`; a `got` outcome never touches FSRS, and a test never creates a new card. One **redemption lap** (retry only the wrong/missed questions) runs at the end of a session as practice — it never changes the submitted score or the FSRS bridge.

**Why:** Recognition-based testing (MCQ) is the weakest form of retrieval and lets students "win" by pattern-matching a keyword — the user's explicit push-back mid-session. The one-way FSRS rule ("one brain, two sensors") stops the quiz from becoming a second competing scheduler: it can only pull a review date *closer*, never push it out from a lucky guess or a different recall format than the review itself uses. The redemption lap gives the honest within-session repeat (practice) without letting same-session re-quizzing measure short-term memory and inflate scores.
**Tradeoffs / rejected:** Rejected the original ask of multiple full passes with shuffling *within* one session (measures short-term memory, not learning — FSRS already owns spaced re-testing). Rejected letting `got` outcomes extend FSRS intervals (would let one lucky/different-format correct answer overwrite a card's real schedule). Scoring is a pure function (`got`=+10, +15 with a trap bonus, `missed`=0, `wrong`-non-MCQ=0, `wrong`-MCQ=−5 guess penalty) — `missed` and non-MCQ `wrong` score identically so honesty never costs more than a guess.

---

## D-005 — query-write test grading needs a fully isolated PGlite instance (2026-07-10)

**Decision:** Added `pgliteRunner.runIsolatedSql(sql, schemaSql)` — a bare PGlite instance seeded with *only* the test question's own `schema_sql`, no canonical dataset. `Tests.jsx`'s `gradeQuery` uses this, not the existing `runSql(sql, setupSql)`.

**Why:** `runSql`'s `setupSql` path is additive-by-design (loads the shared SQL-lessons dataset first, then the caller's extra DDL) — correct for SQL *lessons*, wrong for Tests-section `query-write` questions, which author their own small self-contained schema (e.g. `CREATE TABLE orders`). Found live during verification: a gold-bank question's own `orders` table collided with the lessons dataset's pre-existing `orders` table (`relation "orders" already exists`), silently making every query-write question fail regardless of correctness.
**Tradeoffs / rejected:** Rejected reusing `runSql`'s existing throwaway-DB path as-is — it looked isolated (fresh `PGlite()` instance per call) but wasn't schema-isolated.

---

## D-006 — School roadmap browsing: Class → Subject → Chapter from the phase-naming convention (2026-07-10)

**Decision:** School users get a dedicated `SchoolRoadmaps.jsx` (Class 9/10 → Subject → Chapter), replacing the career-catalog `Roadmaps.jsx` page entirely when `audience==='school'`. It derives Class and Chapter by **parsing the existing `RoadmapNode.phase` string** ("Class 9 · Motion" → class "Class 9", chapter "Motion") — no new backend field or migration. A step auto-advances when it has exactly one option (today: one subject, Physics, so Subject is invisible until Chemistry/Math exist). Picking a chapter navigates into the existing `RoadmapDetail` page with a new `location.state.expandOnlyPhase`, which collapses every *other* phase so the chapter reads as its own page.

**Why:** The career `Roadmaps.jsx` groups roadmaps by a career-specific domain taxonomy (`roadmapDomains.js`); any roadmap not in its registry — physics-9-10 was never added — silently fell back to the `'btech-core'` ("B.Tech Core") domain label, which is how a career-only header ended up showing in the school section. Routing school users to their own page removes that failure mode structurally (it can't recur for any future school roadmap either) rather than patching the fallback. Parsing the phase string instead of adding a `class`/`subject` column keeps the data model unchanged and lets Chemistry/Math slot in for free as long as their content follows the same "Class N · Chapter" phase convention.
**Tradeoffs / rejected:** Rejected fixing only the `roadmapDomains.js` fallback (would leave school users on career-page vocabulary/grouping generally, not just the header). Rejected a dedicated per-chapter route (`/roadmaps/:id/chapter/:phase`) — reusing `RoadmapDetail` with a collapse-all-but-one nav-state was cheaper and kept one source of truth for the phase list UI.

---

## D-007 — JSONB model columns must carry a SQLite variant for the test suite (2026-07-10)

**Decision:** Any `models.py` column using Postgres `JSONB` must be declared via the shared `_JSONB = JSONB().with_variant(JSON(), "sqlite")` variant (see `TestAttempt.results`), not raw `JSONB`. Postgres behavior is unchanged; the variant only swaps to plain `JSON` under SQLite.

**Why:** The tenant-isolation suite (`backend/tests/`) runs `create_all()` against in-memory SQLite (fast, no Supabase needed). A raw Postgres-dialect `JSONB` column makes SQLite's DDL compiler crash at schema creation, killing **all** tests at collection — this is exactly how the audit-generated suite shipped 14-for-14 red. The variant is the one-line convention that keeps the suite runnable as new JSONB columns are added.
**Tradeoffs / rejected:** Rejected pointing the suite at a disposable Postgres (testcontainers/Supabase branch) — heavier setup for a solo repo, and SQLite already exercises the WHERE-clause isolation logic the suite exists for. Known limit (noted in the suite): Postgres-only SQL paths (`array_agg`, `auth.users` in dashboard/admin bodies) can't run on SQLite and stay uncovered until a disposable-Postgres run exists.

---

## D-008 — Baked-`.env` Docker finding downgraded: no emergency secret rotation (2026-07-10)

**Decision:** The audit's critical finding (Dockerfile `COPY . .` with no `.dockerignore` bakes `backend/.env` into image layers → rotate all secrets) was **downgraded**: `backend/.dockerignore` was added and pushed as defense-in-depth, but secret rotation was judged unnecessary — pending one verification (see backlog).

**Why:** `backend/.env` is git-ignored and Railway builds from the **git repo**, not local disk — so Railway's build context never contained the file, regardless of builder. The bake risk only ever applied to *locally* run `docker build` images pushed to a registry, which (to the founder's knowledge) never happened. Rotating four credentials (DB password, JWT secret, Groq key, CRON_SECRET) the day before a pitch carries its own outage risk (Supabase circuit breaker on repeated auth failures) for no established exposure.
**Tradeoffs / rejected:** Rejected blanket rotation as pure-caution — cost/risk without evidence of exposure. Residual condition: if a locally built backend image was ever pushed anywhere, rotation is back on; and if Railway's dashboard shows the **Dockerfile** builder, the backend must be rebuilt once for the `.dockerignore` to take effect (old layers retain whatever they had). Note: if Railway uses Nixpacks, the Dockerfile isn't used in prod at all and the finding was moot for prod from the start.

---

## D-009 — Progress-safe roadmap re-seeding: upsert by title, never delete (2026-07-10)

**Decision:** A roadmap seed that runs against a roadmap with **live user progress** must be a progress-preserving upsert, not the default delete-and-recreate. `seed_python_swe.py` was rewritten to: (1) match existing nodes **case-insensitively by `lower(title)`** and `UPDATE` them in place (phase/section/tier/order_index and title) so the row's `id` never changes; (2) `INSERT` only genuinely new titles; (3) **never delete** — titles in the DB but absent from the seed are reported, not removed; (4) upsert the `roadmaps` row (`ON CONFLICT (id)`) instead of deleting it. The seed file's titles are authoritative and are refreshed onto the matched row.

**Why:** `user_progress.node_id → roadmap_nodes.id` is `ON DELETE CASCADE`, and the original seed did `DELETE FROM roadmap_nodes … + re-INSERT with fresh uuid.uuid4()`. Re-running it to add nodes regenerates every node UUID and **silently cascade-wipes all of that roadmap's user progress** — the exact failure the "add without losing progress" constraint named. Matching must be case-insensitive because live node titles were Title-cased while the seed file was sentence-cased; an exact match would miss every existing row, insert duplicates, and orphan the originals (cascading their progress). The whole run is one `engine.begin()` transaction, so an interrupted attempt (the Supabase pooler dropped connections repeatedly this session) rolls back with zero writes. Verified runs: `18 inserted, 130 updated, 0 removed` then `0 inserted, 148 updated, 0 removed`.

**Tradeoffs / rejected:** Never-deleting means a node genuinely removed from the seed lingers in the DB until cleaned up by hand (reported at run end) — accepted so progress loss is structurally impossible for additive edits. Rejected keeping the fixed-UUID delete+reinsert pattern (fine for a brand-new roadmap, catastrophic for one in use). The other ~32 seeds still use the destructive pattern — see BACKLOG.

---

## D-010 — Cross-roadmap lesson reuse: copy files + align seed titles; `kind` by runnability (2026-07-10)

**Decision:** When a new/expanded roadmap overlaps an existing one (python-backend reusing python-swe's Python-language lessons; python-swe's new Phase 2.5 reusing python-backend's concurrency lessons), reuse is done by **copying the lesson JSON into the target roadmap's content folder** (retargeting `roadmap`/`slug`/prereq+unlock edges) and **aligning the seed node titles to the existing lesson titles** — never editing the shared lesson's title. Lesson `kind` is chosen by whether the topic is meaningfully Pyodide-runnable: concurrency / async / threading lessons are **`engineering`** (illustrative, non-executed snippets); stdlib / file-I/O / regex are **`concept`** (runnable `code_walkthrough`), matching python-swe's existing all-`concept` convention.

**Why:** Node→lesson resolution keys on the node title (exact title, then `slugify(title)` against the per-roadmap manifest — `RoadmapDetail.jsx:lessonSlugForNode`), so a node only links to a lesson whose title/slug it matches. Editing a shared lesson's title to fit one roadmap would break resolution in the other; copying keeps each roadmap folder self-contained (the manifest is per-roadmap). `engineering` for concurrency because threading/multiprocessing/asyncio can't execute meaningfully in Pyodide (no OS threads/processes; browser event-loop limits) — forcing them into the runnable `concept` shape would ship broken walkthroughs.

**Tradeoffs / rejected:** Copying duplicates lesson JSON across folders (drift risk if one copy is later edited) — accepted because the pipeline treats each roadmap folder as the unit and there's no shared-lesson abstraction. Rejected editing the existing lessons' titles to match the seed (explicit user directive: reuse existing lessons, align the seed instead). Systemic gotcha surfaced: node titles and lesson titles must agree (case-sensitively on the exact-match path) or the lesson silently shows no "Learn" button — 30 older python-swe nodes were unlinked purely from sentence-vs-Title casing.

---

## D-011 — Lesson renderer stays a bespoke 3-block prose format; content contracts must not use markdown fences (2026-07-10)

**Decision:** Extended (not replaced) the existing lesson-prose renderer (`RichText` in `frontend/src/LessonView.jsx` + `linkifyGlossary` in `frontend/src/lib/glossary.jsx`) to also support `- `-prefixed bullet lists and single-backtick inline code chips, on top of its existing paragraph / indented-code-block split. The renderer still does **not** parse markdown syntax (no ` ``` `-fenced code blocks, no `#` headers) — every roadmap's `PROMPT-*.md` content contract was updated with the exact three-block grammar (blank-line-separated prose / 2-space-indented code / `- ` bullets) so authors don't reach for markdown fences by habit.

**Why:** A live bug was found and fixed mid-session: ~42 already-authored `python-swe` lesson files used ` ```python ` fences in `overview.what` (the natural markdown habit), which the renderer's code-block detector (every line must start with whitespace) doesn't recognize — it silently fell through to a plain `<p>`, collapsing the whole snippet plus its literal ` ``` ` markers into one run-on line. The 42 files were fixed after the fact, but the durable fix is upstream: state the grammar explicitly in every contract so the bug class can't recur as the other 8 roadmaps run their own format-upgrade pass.

**Tradeoffs / rejected:** Rejected teaching the renderer to also parse ` ``` ` fences defensively (papers over the contract violation instead of preventing it, and adds markdown-parsing surface to a renderer kept deliberately minimal). Rejected adopting a full markdown library — the 3-block grammar covers everything lesson content needs (prose, code, bullets, inline code) with no new dependency.

---

## D-012 — Every lesson must inline-flag its own sharp edges, even when a later lesson owns the deep dive (2026-07-10)

**Decision:** Added rule 28 to `content/PROMPT.md` (and the equivalent to all 9 other roadmap `PROMPT-*.md` contracts): every lesson's teaching body must flag the topic's real-world traps with a short example, even when the full treatment belongs to a later lesson in the same roadmap — closing with an explicit "covered fully in `<slug>`" pointer to a topic already listed in that lesson's own `metadata.unlocks`. `PROMPT-lesson-critic.md` now checks for this (and for the D-011 formatting grammar) in its Phase 2 pass.

**Why:** Triggered by a real product gap the user surfaced from a live Python-tutor chat: Sonnet correctly explained that slicing a list is a shallow copy — a fact `lists.json` itself never taught, even though the roadmap graph already listed `shallow-vs-deep-copy` as something `lists` unlocks. The AI tutor was smarter than the lesson content it was supposedly teaching from, undermining the "the lesson is the source of truth" model the retention engine is built on.

**Tradeoffs / rejected:** Rejected leaving traps solely in the later, dedicated lesson (defers the fact past the point a learner actually hits it — the trap fires while using the earlier concept, e.g. `a[:]` looking safe). Rejected fully re-teaching the deep-dive topic inline instead of flagging it (bloats every lesson and duplicates a lesson that already exists) — the rule caps a flag at one short example + 1-2 sentences + the forward pointer.

---

## D-013 — Large content-QA passes: verify findings against file content directly, not against subagent self-reports (2026-07-10)

**Decision:** Running a multi-batch lesson-critic pass over ~117 reformatted `python-swe` files, 3 of 9 background critic-agent batches (33 files) silently failed with zero recoverable output when the orchestrating process exited mid-task — the harness's own notification said only "failed," with 0-byte output files and no partial transcript. Rather than re-launching those batches, Claude read and critiqued the 33 files itself in-session, patching real defects directly (11 of 33 needed fixes). Separately, asked to confirm the earlier 9 batches' ~26-29 flagged NEEDS-WORK files had been fixed, Claude did not trust its own prior summary — it re-read the actual current file content for each flagged defect and found **none** of them had been applied, plus a new regression: an unrelated prior pass had "fixed" a mojibake character in `shallow-vs-deep-copy.json` by truncating two recall-questions mid-sentence instead of repairing them.

**Why:** Background subagent batches can lose work invisibly on process exit, and a critic's own "PASS/NEEDS-WORK" verdict is not the same as the finding being *fixed* — nothing had actually applied any of the first 9 batches' fix lists despite them having been reported as found. For content-quality work at this scale, verifying against the real file before reporting status is the only way to avoid compounding an already-stale claim.

**Tradeoffs / rejected:** Rejected re-dispatching the 3 failed batches as fresh subagents (repeats the same silent-failure risk and still needs the same verification step afterward) — direct, synchronous review is slower but leaves nothing unverified. Rejected treating "critic ran and reported a verdict" as equivalent to "fixed" for status reporting going forward.

---

## D-014 — C++/Java language roadmaps: reuse `kind:"engineering"`, prose+code (no runtime), design-doc replaces deep-research (2026-07-10)

**Decision:** C++ (`cpp-swe`) and Java (`java-swe`) language-roadmap lessons reuse the existing `kind:"engineering"` validator branch (teach-from-scratch prose + a required `code_snippets` list) rather than a new kind. There is no in-browser C++/Java runtime, so lessons are prose + **≥2 hardcoded, annotated, never-executed** code snippets. For a *language* roadmap a well-defined design doc (`content/PROMPT-cpp.md`, carrying a per-node misconception map) **replaces the DSA-style Gemini deep-research step**. Generate **one Step per handoff packet, pilot Step 1 first**; algorithmic CP nodes (segment/Fenwick tree, DSU, LRU) are authored prose-first and tagged `[trace-later]` for a future viz pass. C++ seed gained `const-correctness` + `iterator-invalidation` nodes.

**Why:** `engineering`'s field contract already fits language lessons exactly (annotated code + prose), so no validator/renderer work is needed — roadmap and kind are independent. Deep research earns its keep for DSA because it supplies fabrication-prone facts (engineering examples, interview frequency); language semantics (RAII, move, `equals`/`hashCode`) are canonical and in-distribution, so a pitfall-dense design doc suffices — *provided* it carries the per-node misconception (the anti-hallucination anchor). Batch-by-Step because long-horizon generation degrades and, worst for a language, fabricates APIs.

**Tradeoffs / rejected:** Rejected a new `language` kind (needless validator+renderer work; `engineering` fits — the historical kind name stays semantically odd but the fields are exact). Rejected a deep-research run per language phase (canonical knowledge; the design doc substitutes). Rejected whole-roadmap one-shot generation (thinning + API fabrication).

---

## D-015 — DSA viz generators can be Antigravity-built from a Claude spec; golden + browser render-verify is mandatory and stays with Claude (2026-07-10)

**Decision:** DSA execution-trace **viz generators** (not just renderers) may be built by Antigravity from a Claude-written spec (e.g. `content/HANDOFF-dsa-phase12-viz.md`), reversing the prior "viz is Claude-owned, not Antigravity." A viz item is **not "done"** until each generator has a `*.golden.mjs` passing `npm run golden` **and** Claude browser-verifies the lesson renders — goldens cannot catch JSX render crashes. Content call: `monotonic-stack` reuses the `next-greater-element` generator (distinct default input) instead of a bespoke histogram generator.

**Why:** Antigravity already built the renderers (Tree/Grid/List/etc.), so it understands the frame contract and can build the matching generators; delegating the generator bulk conserves Claude usage. But the render layer is where silent JSX crashes live (a null-guard crash once shipped clean past goldens), so the browser pass must stay a Claude gate. The monotonic reuse is best-UX-per-effort: the NGE generator already *is* the decreasing-stack eviction demo, and a bespoke histogram viz needs area rendering `StackQueueViz` lacks.

**Tradeoffs / rejected:** Rejected Antigravity self-certifying viz as done (background agents lose state on exit and goldens miss JSX crashes — verification stays with Claude). Rejected a bespoke monotonic-stack histogram generator now (renderer can't draw the area; deferred as polish).

---

## D-016 — Lesson-critic runs on Gemini-in-Antigravity (file access) or Sonnet, never Opus; report-only, separate session (2026-07-10)

**Decision:** The adversarial lesson-critic pass runs on **Gemini 3.1 Pro inside Antigravity** (repo file access) — or a **Sonnet** agent — but **never Opus/main-Claude**, to conserve Claude usage. It runs in a session **separate from the author**, is instructed to be adversarial (no rubber-stamp), and is **report-only by default** (writes `content/CRITIC-REPORT-<roadmap>.md`; fixes are a deliberate second pass). Runbook: `content/RUN-lesson-critic-antigravity.md`; paste-only fallback `content/PROMPT-lesson-critic-external.md`.

**Why:** The critic is a structured-rubric task, not hard reasoning, so Opus/Claude budget is wasted on it; Gemini-in-Antigravity reads lesson files directly (no paste). Critic≠author avoids self-rubber-stamping. Found this session: a batch of in-Claude Sonnet critic agents lost all work when the process exited mid-run (cf. D-013) — another reason to prefer the external path for big sweeps.

**Tradeoffs / rejected:** Rejected running the critic on Opus/main-Claude (cost). Rejected letting the author critique its own output (rubber-stamps). Rejected apply-mode by default (author==fixer is riskier; keep report-only so diffs are reviewed).

---

## D-017 — Syllabus-upload roadmaps: frontier model, review-before-commit, per-user rows in the same tables (2026-07-11)

**Decision:** The "Bring Your Own Path" feature (PDF syllabus → personal roadmap) is built as:
- **One model call** (`services/syllabus.py`) taking the raw PDF as a document/inline part (vision path) with a JSON schema — no client-side text extraction, no Groq. The provider is **routed by `SYLLABUS_MODEL`**: a `gemini*` id calls Google (`google-genai`), anything else calls Anthropic (`claude-opus-4-8`). Both send the identical prompt + schema, so switching providers to compare extraction quality/cost is a config change (Gemini Flash-Lite wired in 2026-07-11 to A/B against Opus).
- **Two-step review-before-commit API**: `/api/syllabus/extract` returns a draft and saves nothing; the user edits it in the UI; `/api/syllabus/commit` persists it. The draft is never auto-saved.
- **Personal roadmaps are ordinary `roadmaps`/`roadmap_nodes` rows** with a new nullable `roadmaps.user_id` (NULL = official catalog), inheriting the creator''s `audience`, `slug` NULL (route by UUID). Visibility = catalog-by-audience + own; personal roadmaps resolve only for their owner.
- The extraction prompt forces **decomposition into atomic, testable topics** (capability-phrased titles), because node granularity determines whether logged activities and their FSRS cards stay sharp.

**Why:** Reusing the existing tables means `Activity.node_id`, the log form''s roadmap picker, progress, blockers, and the whole FSRS loop work with zero changes — the feature is purely additive. A frontier model is justified because extraction is one-shot, user-visible, and low-volume (guarded by a 5/user/day limit + 10 MB cap); quality of the parse is the product. Review-before-commit exists because an LLM syllabus parse is ~90% right and silently persisting the wrong 10% erodes trust.

**Tradeoffs / rejected:** Rejected a separate `custom_roadmaps` table (duplicates the graph machinery for nothing). Rejected client-side PDF text extraction (breaks on scanned/table syllabi; the model''s vision path handles both). Rejected auto-generating prerequisite edges in v1 (LLM-guessed edges would pollute the "Why am I stuck?" diagnosis; sequential order carries enough structure). Deletion nulls activity links instead of cascading them — review history is the user''s memory data and outlives the roadmap.

---

## D-018 — Landing page repositioned problem-first around the retention engine (2026-07-11)

**Decision:** The landing hero leads with the problem ("Stop watching tutorials you forget by Friday."), names the category in plain words ("a spaced-repetition system for engineers"), and gives the retention engine the hero visual — an animated SVG forgetting-curve graph (gray unaided-decay curve vs cyan sawtooth that flattens with each review ping). The code-stepper demo stays but is demoted to "Step 1 — learn it properly"; the loop is "Step 2 — never forget it". The stepper now loops a real 7-step trace of `running_total(2)` (honest full trace, predict `= ?` → reveal `= 1`).

**Why:** External reviewers (friends, fresh visitors) could not articulate what the site was for — the old headline "Learn it visually. Remember it forever." split the value prop, and the first visual (code stepper) made it read as another interactive-tutorial site. The moat (FSRS retention engine) had no visual and appeared only as a side effect ("Then it sticks"). Whatever gets the demo is the product in the visitor's mind, so the engine got the graph.

**Tradeoffs / rejected:** Rejected leading with the lesson demo (impressive but positions us in the most crowded category). Rejected a fake-precise Ebbinghaus stat ("you forget 70% in 7 days") — engineers smell folklore numbers; the unlabeled decay curve makes the same point honestly. Rejected Title Case headline (reads as dated marketing; sentence case scans better for average-English readers). Kept "Review" over the more Indian-college-natural "revision" for product-term consistency.

---

## D-019 — Review questions: persisted reusable sets, topic-grounded for roadmap cards, explicit depth choice (2026-07-12)

**Decision:** Question mode moves from generate-per-request to a persisted `question_sets` table. A set is generated ONCE per card (+depth), stored as `[{question, reference_answer}]`, served SHUFFLED for at least `QUESTION_SET_REUSE` (=2) review sessions, then regenerated. Grounding splits by card type: **node-linked cards** (e.g. syllabus roadmaps) are TOPIC-grounded — the node title+description is the contract, standard textbook knowledge of that topic is fair game, key_memory only biases; **free-form cards** keep key_memory as sole ground truth. The generator writes a `reference_answer` per question at generation time; grading judges against the stored reference (injected server-side, never sent to the client). The user explicitly picks revision depth ('main' = 2-3 core Qs, 'deep' = 4-5 incl. apply/derive/edge-case) via a Review-screen toggle remembered in localStorage. Grader model: `openai/gpt-oss-120b` (probe showed `llama-3.1-8b-instant` produced repetitive, under-specified questions).

**Why:** Persistence amortizes the LLM cost (~1 generation per 2+ sessions instead of per view), keeps the quiz stable while a memory is forming, and the shuffle stops answer-order memorization. Topic grounding fixes the "key memory serves nothing for roadmap cards" problem: an exam grades you on the syllabus topic, not on whatever you happened to write down. Reference answers written at generation time are what make persistence + strict grading possible without a user rubric.

**Tradeoffs / rejected:** Rejected regenerating every session (cost + churn). Rejected sending reference answers to the client (leaks the answer key pre-attempt). Rejected auto-detecting depth from FSRS state in v1 (explicit user choice is the ask; adaptive depth can come once metrics exist). times_used increments on serve (not on grade), so an abandoned session burns a use — acceptable, guarantees "at least two" without double-count bookkeeping.

---

## D-020 — Personal roadmaps capped at 3 per user, lifetime (2026-07-12)

**Decision:** Syllabus→roadmap commits are limited to `SYLLABUS_LIFETIME_LIMIT` (=3) per user, enforced by a counter on `user_prefs` (`custom_roadmaps_created`) that is claimed atomically at commit (`UPDATE … WHERE count < limit`) and **never decremented** — deleting a roadmap does not refund quota. The upload page shows remaining quota and blocks at 0; commit returns 403 when spent.

**Why:** Extraction is frontier-model spend and roadmaps are durable artifacts; a lifetime cap (vs. concurrent cap) stops the create-delete-recreate loop from turning the delete button into an unlimited-extraction exploit. Counting live `roadmaps` rows can''t enforce lifetime semantics, hence the dedicated counter (backfilled by migration `c8e2a7f5d1b9`).

**Tradeoffs / rejected:** Rejected a concurrent cap (delete = refund = unbounded extraction spend). Rejected counting roadmap rows (same flaw). The lifetime rule is deliberately strict for launch — it can be relaxed per-user or made a paid tier later; the config knob exists.

---

## D-021 — Positioning vs teachers & LLMs: complete the teacher, package the discipline (2026-07-12)

**Decision:** RetainHQ does not compete on explanation (commoditized by LLMs, 3Blue1Brown, GeoGebra, teachers). The positioning, for school AND career roadmaps: (a) **vs teachers/smartboards** — the after-class memory layer, plus a class-decay dashboard that makes the teacher the champion, not the competitor; (b) **vs a student's own LLM** — *enforcement, not recall*: modern LLMs hold months-long memory and, for power users with tutor skills, approximate a personal RetainHQ — so the defensible edge is that our loop is **enforced by the product** (predict-before-reveal gates, FSRS-initiated returns, session caps) and **packaged** for students — especially rural/tier-3 — who lack the prompting literacy to assemble memory+skills themselves; (c) **verified memory state** — measured retention curves as the trust artifact schools/parents accept where LLM self-report fails. Maths runtime plan + full frame: `docs/PLAN-school-maths-runtime.md`.

**Why:** Founder pushback corrected a draft that leaned on "LLMs forget you" — false since persistent LLM memory shipped; the founder's own skill-file tutors prove a power user can self-assemble the loop. What survives is enforcement UX + packaged defaults + verified analytics + B2B school distribution.

**Tradeoffs / rejected:** Concedes the explanation layer permanently (visuals are hooks, not moats). The "LLMs don't schedule" line has a shelf life (vendors are productizing study loops) — the frame carries an explicit quarterly-revisit clock rather than pretending the moat is static.

---

## D-022 — No custom global exception handler for Sentry (2026-07-13)

**Decision:** Backend Sentry integration relies entirely on `sentry-sdk`'s FastAPI integration to capture unhandled exceptions — no `@app.exception_handler(Exception)`. `logging.basicConfig(level=logging.INFO)` is added unconditionally (not gated on `SENTRY_DSN`) so Render's log stream carries tracebacks even with Sentry off.

**Why:** A custom global handler risks swallowing the exception before Sentry's middleware sees it, silently disabling capture while looking like it's still wired. `sentry_sdk.init()` is the documented, tested integration point.

**Tradeoffs / rejected:** Rejected a custom handler for uniform error-response shaping — that can be added later as a thin wrapper that re-raises after logging, once there's an actual need for a consistent client-facing error envelope.

---

## D-023 — Hand-rolled push-only service worker, not vite-plugin-pwa (2026-07-13)

**Decision:** `public/sw.js` is a ~65-line hand-written file (install/activate/push/notificationclick/pushsubscriptionchange) with **no fetch handler**, not generated by `vite-plugin-pwa` or any precaching library.

**Why:** RetainHQ's SPA is online-only by design (no offline mode planned) — a precaching service worker invites stale-chunk 404s across Vercel deploys (a cached old `index-XXXX.js` referencing a hash that no longer exists on the CDN). A push-only worker with no fetch handler leaves the network path completely untouched, so this class of bug is structurally impossible.

**Tradeoffs / rejected:** Rejected `vite-plugin-pwa` (brings precaching/offline support RetainHQ doesn't want and a heavier maintenance surface for one small file). Revisit if true offline support ever becomes a product goal.

---

## D-024 — One `reminder_log` claim gates both email and push (2026-07-13)

**Decision:** The daily reminder batch claims a single `reminder_log` row per `(user_id, sent_on)` (unchanged from the email-only design), then fans out to whichever channels are configured — email via Resend, push to each of the user's `push_subscriptions` — independently under that one claim. A failure in one channel never blocks or retries the other.

**Why:** Content and cadence are identical across channels (both mirror "N reviews due"), so there's no reason for separate idempotency ledgers. Preserves the existing "miss a day rather than risk double-sending" stance from the email-only design without adding a second claim table.

**Tradeoffs / rejected:** Add a `channel` column to `reminder_log` only if email and push cadence/content ever diverge — no reason to build that flexibility before it's needed.

---

## D-025 — `duration_ms` on `reviews`, measured client-side via `performance.now()` (2026-07-13)

**Decision:** `reviews.duration_ms` (nullable int) is stamped by the frontend as `performance.now()` at card-show minus `performance.now()` at outcome-submit, sent in the `/complete` POST body, and clamped server-side to `(0, 1_800_000]` — anything outside that range persists as NULL rather than rejecting the completion.

**Why:** `performance.now()` is monotonic and immune to system clock changes/skew, unlike a `started_at` timestamp column that would need `completed_at - started_at` and inherits any clock adjustment during the session. Clamping instead of rejecting means a broken/garbage client timer never blocks the actual review completion — it just costs one data point.

**Tradeoffs / rejected:** Rejected a `started_at` timestamp column (clock-skew exposure, and a second write path to keep in sync). The 30-minute ceiling is a single-card sanity bound, not a real UX limit — nobody spends 30 minutes on one flashcard, so anything past it is treated as an abandoned/backgrounded tab, not real duration.

---

## D-026 — Generic `metric_events` JSONB table instead of per-metric tables (2026-07-13)

**Decision:** New learning-analytics signals land in one generic `metric_events` table (`user_id`, `event_type`, `entity_id`, JSONB `payload`) rather than a dedicated table per metric. `record_metric_event()` never commits — it rides the caller's existing transaction. Server-side producers call it directly; the one client-writable path (`POST /api/metrics/events`) is allowlisted (`CLIENT_EVENT_TYPES`) and payload-capped (2KB) so an arbitrary client can't write arbitrary event types.

**Why:** These signals are heterogeneous and exploratory (extraction edit-deltas today, grader-calibration self-report and depth-mode retention analysis being genuine future candidates) — building a dedicated table + migration for each one before there's a proven consumer is premature. A JSONB payload keyed by `event_type` gets the same information captured without the schema churn. Note: grader calibration and depth-mode retention analysis turned out to need **no new capture at all** — both are derivable from existing `reviews.recalled` vs `reviews.ai_recalled` and `question_sets.depth`, which is why only `extraction_edit_delta` shipped as an actual producer this round.

**Tradeoffs / rejected:** A generic JSONB table trades query ergonomics (no typed columns, no indexes on payload fields) for schema flexibility — acceptable while these are exploratory; promote a specific `event_type` to its own table if it becomes a stable, frequently-queried metric.

---

## D-027 — No `user_prefs.role` column: teacher = classroom owner (2026-07-16)

**Decision:** The teacher dashboard (`docs/SPEC-teacher-dashboard.md`) adds no role system. "Is a teacher" is defined purely as "owns ≥1 row in the new `classrooms` table." The frontend shows the "Teach" nav entry exactly when `GET /api/classrooms/mine.teaching` is non-empty; there's no signup flow, gate, or flag that designates someone a teacher ahead of time.
**Why:** A role column would need migrating away from later if the product ever supports a user being both a student and a teacher (already true in v1 — nothing stops a user from creating a class and joining someone else's), or multi-teacher classrooms (Phase 2). Deriving "teacher" from ownership avoids that migration entirely and keeps the signup surface at zero — any authenticated user can create a classroom and thereby become a teacher, which matches the product's actual gating story (visibility is consent-gated by students joining, not by who's allowed to create a class).
**Tradeoffs / rejected:** Rejected adding `user_prefs.role` (or a new `is_teacher` flag) — would need backfilling and a migration path the day multi-role or multi-teacher support lands. Rejected a dedicated teacher signup/onboarding flow — unnecessary gatekeeping for a feature where the real authorization boundary is per-classroom ownership, not an account-level designation.

---

## D-028 — Teacher-never-sees-private-content boundary is enforced server-side, not by frontend omission (2026-07-16)

**Decision:** The classroom analytics endpoints (`GET /{id}/overview`, `/gap-map`, `/students`, `/students/{member_id}`) scope every query to `student_user_id IN classroom_members` **AND** content restricted to that classroom's assigned `classroom_roadmaps`, and select only a fixed allowlist of fields (activity timing, review counts/outcomes, FSRS-derived mastery, test scores, streaks). `key_memory`/notes/mistake text, free-recall answer text, AI feedback text, email/Google identity, and any non-assigned-roadmap or career-side activity are never fetched by these queries in the first place — the boundary is a WHERE-clause and field-selection guarantee, not a "don't render this field" choice left to the React layer. It is covered by an explicit test (`test_classrooms.py`): seed one activity linked to an assigned roadmap and one linked to an unassigned roadmap for the same student, assert the teacher's responses reflect only the former.
**Why:** This is a DPDP-relevant boundary for a product whose students are minors, and the spec calls it out as load-bearing for the school pitch — a leak here (a teacher seeing a student's private notebook, or career-roadmap activity unrelated to the class) would be both a real privacy harm and a credibility-ending demo failure. Enforcing it in the query layer means a future frontend bug (e.g. a careless component spreading a full API response into props) can't leak the field, because the field was never in the response to begin with.
**Tradeoffs / rejected:** Rejected trusting frontend-only field omission (cheaper to write, but one stray `{...student}` spread away from a real leak). Rejected a more general per-field ACL system — the fixed allowlist per endpoint is simpler and sufficient for the two roles (teacher/student) this feature actually has.
