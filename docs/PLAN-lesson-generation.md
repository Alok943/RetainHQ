# Content Plan — lesson generation priority

**Written:** 2026-07-12. This is a CONTENT plan (which lessons to generate via the Antigravity bulk pipeline, in what order), not a code plan. It complements `docs/SYSTEM-OVERVIEW.md` §5 ("Content build order") with the reasoning behind the order and a concrete workflow. Re-derive the coverage table before trusting it if this doc is more than a few weeks old — `content/roadmaps/*/*.json` counts drift fast.

## 1. Objective

RetainHQ's moat is the retention engine, not the lesson library — but lessons are the hook that gets someone to open the app and the only place the product can out-teach YouTube+docs (docs-as-truth prose, step-through execution, predict-before-reveal). The founder's job-description research fixed a build order — **AI-Engineering → DSA → Data-Engineering** — because that's the sequence that gets the founder (and the Indian college students RetainHQ targets) placed. The syllabus-upload feature (D-017) now means every roadmap in the 30-strong catalog can be "covered" cheaply via LLM-generated review questions on a personal syllabus upload, even with zero authored lessons — so authored-lesson effort should go exactly where interactive depth (runnable code, step-trace visualization, predict-reveal) is a real teaching advantage over generated Q&A, not where it would just duplicate what an LLM question set already does adequately. Physics 9-10 is the exception that runs on its own clock: it's the pitch artifact for the school B2B motion, not the JD-priority ladder.

## 2. Current coverage

Counted directly from `content/roadmaps/*/*.json` (2026-07-12) against the ~30 roadmaps seeded in `backend/seed_*.py`.

| Roadmap (content folder) | Lesson files | State | Notes |
|---|---|---|---|
| `python-swe` | 120 | **Done** (declared) | 40/148 nodes still lesson-less per BACKLOG (Phase 5 Testing, Phase 6 Engineering Practices) — "done" means swept + critiqued, not 100% node coverage |
| `sql` | 34 | **Done** | PGlite runtime; no open backlog items |
| `physics-9-10` | 128 | **Near-done, pitch-quality push ongoing** | 3D scenes for the pitch-demo lessons only (D-003); ~120 lessons still lack `schematic`/`diagram3d` (BACKLOG) |
| `core-cs` | 61 | **Partial** | OS batch "in progress" per SYSTEM-OVERVIEW §5; not yet critic-swept |
| `dsa` | 51 | **Partial, active** | Viz player ~29 generators, only array/string/stack/search/sort feed it; no backtracking/linked-list/tree/graph generators registered yet; handoffs exist through phase 13 |
| `cpp-swe` | 45 | **Partial (pilot)** | D-014: only Step-1 pilot generated; gold exemplar exists, rest of Steps pending |
| `python-backend` | 71 | **Partial** | Built via cross-reuse from python-swe (D-010); coverage vs its own node list unverified |
| `ai-engineering` | 36 | **Node-complete, P0 = upgrade pass** | Verified 2026-07-12: all 36 seeded nodes have a matching lesson file (answers §7 Q2 — gap is 0). "Finish-out" therefore means: rewrite to the beginner overlay standard + add the prediction rung + critic sweep, not net-new authoring |
| `aptitude` | 40 | **Partial** | Verbal/vocab aptitude explicitly pending (SYSTEM-OVERVIEW §5); not yet critic-swept |
| **All other ~21 seeded roadmaps** | **0** | **Seeded-only** | Data Engineering, Java-SWE, ML, DL, MLOps, Math-for-ML, Git/GitHub, Blind75, NeetCode150, Striver A2Z, Behavioral, DevOps/Cloud, Linux/Shell, LLD, System Design, Cyber Security, Computer Architecture, Discrete Math, Web Dev, Testing, API Design — catalog rows + nodes exist, zero lesson JSON. These roadmaps are exactly what syllabus-upload + generated Q&A now serves as a stopgap. |

Content contracts that exist (`content/PROMPT-*.md`): `aptitude`, `backend` (engineering kind), `coreCS`, `cpp`, `dsa` (+ `dsa-research`), `engineering` (generic, reused by cpp/java), `physics` (+ `physics-3d`, `physics-kc-graph`), `reasoning`, `sql`. **No AI-Engineering-specific or Data-Engineering-specific contract exists yet** — `ai-engineering`'s 36 lessons were presumably authored against a generic/ad-hoc prompt; confirm which contract before scaling it (open question, §7).

## 3. Prioritized next roadmaps

### P0 — next up

| Roadmap | Why |
|---|---|
| **AI-Engineering — finish the remaining nodes** | #1 in the JD build order; already 36 lessons in, SYSTEM-OVERVIEW already calls this the top item; no new runtime needed (reuses `engineering`/`concept` kinds); this is finishing a roadmap already mid-flight, cheapest P0 available |
| **DSA — generators + lessons for backtracking/linked-list/tree/graph families** | #2 in JD build order; viz player is the single biggest interactive-depth advantage this product has over YouTube/LeetCode explainers, and it's sitting half-fed (renderers built, generators missing) — this is a case where NOT generating content means an existing expensive runtime investment (9 renderers) stays half-used. Syllabus-upload does NOT substitute here: DSA needs the step-trace, not a Q&A set, to teach the algorithm |
| **python-swe gap-fill (40 lesson-less nodes) + apply outstanding critic fixes** | Cheap, bounded, closes a known hole in the one roadmap already declared "done" — a support-cost item, not a new roadmap, but it should land before python-swe is cited as a competitive example (SEO/landing use it) |

### P1 — queue behind P0

| Roadmap | Why |
|---|---|
| **Data-Engineering — first content pass** | #3 in JD build order, currently 0 lessons (seeded-only); no existing runtime (SQL-flavored parts could reuse PGlite, but pipeline/orchestration concepts can't) — flag as needing contract work, see §4 |
| **core-cs — finish OS batch + critic sweep** | Already partial and in-progress; low marginal cost to finish vs. starting a fresh roadmap; feeds AI-Eng/DSA interview prep (systems fundamentals) |
| **cpp-swe — remaining Steps beyond the Step-1 pilot** | Already has a validated contract + pilot (D-014); incremental generation, not a cold start; C++ is used for the DSA/CP audience but is lower JD-priority than DSA/Data-Eng itself |
| **Physics 9-10 — retrofit diagrams to pitch-quality** | Runs on the school-pitch clock, not the JD ladder — but it's the closest roadmap to "pitch-ready" and has a hard external deadline (Gorakhpur pitch timeline in BACKLOG); reuses the existing R3F scene library (D-003), no new runtime |

### P2 — lower priority, opportunistic

| Roadmap | Why |
|---|---|
| **aptitude — verbal/vocab gap** | Already partial, low effort to close, but not JD-critical and syllabus-upload covers ad-hoc aptitude topics reasonably (mostly fact/vocab recall, exactly what generated Q&A is good at) |
| **python-backend — verify/complete node coverage** | Reused content from python-swe already covers the overlap; needs an audit pass more than fresh authoring |
| **Java-SWE — Step-1 pilot** | BACKLOG already scopes this (equals/hashCode + autoboxing seed nodes first) but it's a language roadmap analogous to cpp-swe, lower JD priority than Data-Eng |
| **ML / DL / MLOps / Math-for-ML** | JD-relevant but overlaps AI-Engineering conceptually; better sequenced after AI-Eng is actually finished so there's no duplicate authoring, and much of "explain backprop" is exactly the kind of theory-recall content syllabus-upload + generated Q&A already does well |

## 4. P0 scope sketch

**AI-Engineering finish-out**
- Kind: likely `engineering` (annotated code, no runtime) for framework/API-shaped topics (RAG, evals, agent loops), `concept` where a runnable Pyodide snippet makes sense (embeddings math, tokenization).
- Volume: unknown exact node gap — pull `roadmap_nodes` for `ai-engineering` and diff against the 36 existing slugs before scoping a lesson count (open question, §7).
- Contract: **no dedicated `PROMPT-ai-engineering.md` confirmed to exist** — first task is confirming/writing one (likely adapts `PROMPT-backend.md`'s `engineering`-kind pattern). Flag as a small new-contract cost, not a new-runtime cost.

**DSA backtracking/linked-list/tree/graph generators + lessons**
- Kind: `dsa` (viz-driven).
- Volume: per SYSTEM-OVERVIEW, 4 renderers (`ListViz`, `GraphViz`, `IntervalViz`, `BitsViz`) have zero feeding generators; backtracking already partially feeds `TreeViz`/`GridViz` via existing generators (n-queens, permutations, subsets, combination-sum) but those don't yet have lesson JSON wired to `viz` blocks for all of them — audit lesson-to-generator linkage before counting "new" work.
- Contract: `content/PROMPT-dsa.md` + `PROMPT-dsa-research.md` already exist and are the governing pattern (D-015: generators may be Antigravity-built from a Claude spec, golden + browser-verify stays with Claude — this is a real cost line, not just content authoring).
- **New-runtime flag**: none — this reuses the shipped trace-player; the cost is generator engineering + verification gates, not a new interactive surface.

**python-swe gap-fill**
- Kind: `concept` (existing pattern).
- Volume: 40 nodes (Phase 5 Testing: pytest/mock/black/ruff/mypy/pre-commit/pdb/cProfile; Phase 6 Engineering Practices: git/project-structure/design-patterns) + a handful of Phase 3/4 title-mapping fixes (duck typing, multiple inheritance, property decorator, dataclasses-vs-pydantic, with-statement — likely already-written lessons under different wording, not net-new).
- Contract: `content/PROMPT.md` (python-swe's own, referenced in D-011/D-012) — no new contract needed.

## 5. Generation workflow (Antigravity handoff loop)

1. **Contract** — Claude writes or confirms the `PROMPT-<roadmap>.md` contract (schema shape, misconception map for language/CP topics, format grammar per D-011, sharp-edges rule per D-012). For DSA, this includes a generator spec (D-015) when new viz families are needed. **P0 batches additionally compose `content/PROMPT-beginner-overlay.md`** (tier-3-college beginner register; overlay wins on conflict) — its critic additions apply in step 4.
2. **Generate** — Antigravity (Gemini) bulk-generates lesson JSON against the contract. Claude does not author bulk content directly (working agreement in CLAUDE.md).
3. **Validate** — `content/validate.py` gates structure only (required fields, `kind` branch shape, format grammar). Must pass before anything downstream. `sync-content.mjs` copies validated JSON to `frontend/public/content/` on `predev`/`prebuild`.
4. **Critic pass** — Adversarial pedagogy review, **never on the author model** (D-016): Gemini-in-Antigravity (repo file access, preferred for big sweeps) or a Sonnet agent — never Opus/main-Claude, and never the same session that generated the content. Report-only by default, writes `content/CRITIC-REPORT-<roadmap>.md`. Runbook: `content/RUN-lesson-critic-antigravity.md`.
5. **Founder/Claude spot-check** — Sample-read actual files against the critic report before declaring a roadmap "done" (D-013: verify against real file content, not against a prior self-report — an entire batch of "fixed" findings turned out never to have been applied).
6. **Fix pass** — A deliberate second pass applies the critic's fix list; re-verify against files, not against the fact that a fix pass "ran."
7. **Seed/link** — Ensure `roadmap_nodes.title` matches lesson `title`/slug exactly (case-sensitive gotcha, D-010) so `RoadmapDetail.jsx`'s lesson resolution links correctly; use the progress-safe upsert seed pattern (D-009), never the destructive delete-and-reinsert one (~32 seeds still need conversion per BACKLOG — check before re-running any seed against a live-progress roadmap).
8. **Doc update** — If node/lesson counts materially change "done" state for a roadmap, update this table and SYSTEM-OVERVIEW §5 in the same commit as the content merge (not required per-JSON-file, but required when a roadmap's status line changes).

## 6. Explicitly NOT next

- **The ~21 zero-content seeded roadmaps beyond Data-Engineering** (ML/DL/MLOps, Blind75, NeetCode150, Striver A2Z, Behavioral, DevOps, Linux, LLD, System Design, Cyber Security, Computer Architecture, Discrete Math, Web Dev, Testing, API Design, Git/GitHub) — syllabus-upload + generated Q&A is an adequate stopgap for these until the JD ladder actually reaches them; authoring now would be building ahead of demonstrated need.
- **A new interactive runtime for Data-Engineering** (e.g., a real pipeline/DAG sandbox) — scope Data-Eng's first pass as prose/`engineering`-kind content reusing SQL/PGlite where topics are SQL-shaped; do not greenlight a new client-side compute surface without a separate design decision.
- **Circuit/free-body 2D diagram renderers for Physics** — schema exists, no renderer; explicitly backlogged, not blocking the pitch-quality retrofit which only needs the already-built 3D scenes and static SVGs.
- **DSA `monotonic-stack` bespoke histogram generator** — D-015 already rejected this as polish; reuse `next-greater-element`.
- **tier-field mass realignment** (BACKLOG) — a data-cleanup decision blocking on founder input, not a generation-priority question; don't let it block P0 work.

## 7. Open questions for the founder

1. **Does `ai-engineering` have a dedicated `PROMPT-*.md` contract, or were its 36 lessons authored ad hoc?** Confirms whether P0 #1 starts with a contract-writing step or goes straight to generation.
2. **What's the actual node gap for `core-cs`?** (lesson-file count vs. seeded node count) — `ai-engineering`'s gap was verified at ZERO on 2026-07-12 (36/36 nodes have lesson files; its P0 work is the beginner upgrade pass, not authoring).
3. **Data-Engineering scope**: pure SQL/ETL-pattern content (reuses PGlite) vs. broader pipeline/orchestration/cloud topics (needs a new contract, possibly new runtime surface)? Determines whether P1 Data-Eng is a cheap extension of `sql` or a bigger lift.
4. **Is the mojibake/truncated-question defect in `shallow-vs-deep-copy.json` (BACKLOG) fixed yet?** — small, but it's a known-broken lesson in the "done" python-swe roadmap.
5. **Priority tiebreak: DSA generator engineering vs. AI-Engineering content volume** — if only one can be a background Antigravity task this cycle, which wins? (This plan sequences AI-Eng slightly ahead because it's cheaper/closer to done, but the JD ladder puts DSA second either way — worth an explicit call.)
