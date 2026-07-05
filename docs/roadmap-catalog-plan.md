# Roadmap Catalog Plan — domains, flagships, and what NOT to build

Status: **draft for discussion** (2026-07-03). Implements/refines the tiered taxonomy proposal.
Companion to `docs/jd-research-run3.md` (career mobility) and CLAUDE.md's content-build priority.

## The thesis, sharpened

The proposal's framing — "organize by career leverage, not technology" — is right, but its
tier list is still a technology list. RetainHQ's actual differentiators are:

1. **Domain grouping by student goal** (the "signature feature" suggestion — correct, adopt it).
2. **Career Paths** (already shipped) — the true career-leverage layer; roadmaps are what paths
   point at.
3. **Content + retention, not catalog size.** Roadmap skeletons are cheap; every competitor has
   them (roadmap.sh has 60+). A catalog full of node-only shells dilutes the "we out-teach
   YouTube" claim. **The catalog should surface what has lessons first, and never grow faster
   than the content pipeline can follow.**

Rule of thumb: **a new roadmap gets seeded only when (a) a Career Path references it, (b) it's a
placement gate for the target student, or (c) content for it is scheduled.** Everything else is
backlog.

---

## Current inventory (23 seeds — CLAUDE.md's "10" is stale)

UUID registry — **check this table before assigning a UUID to a new seed.**
(A real collision existed: `seed_lld.py` reused the DSA UUID; running it would have deleted the
DSA roadmap. Fixed 2026-07-03 → LLD now `80808080-…`.)

| UUID prefix | Seed | Title | Content status |
|---|---|---|---|
| 11111111 | seed_python_swe | Python for SWE | **lessons: full** |
| 22222222 | seed_striver_a2z | DSA — Striver's A2Z Sheet | nodes only |
| 33333333 | seed_neetcode_150 | DSA — NeetCode 150 | nodes only |
| 44444444 | seed_core_cs | Core CS — OS, DBMS & Networks | lessons: OS batch in progress |
| 55555555 | seed_aptitude | Aptitude — Quant, Reasoning & Verbal | lessons: quant + LR |
| 66666666 | seed_web_dev | Web Development — Full-Stack | nodes only |
| 77777777 | seed_system_design | System Design | nodes only |
| 88888888 | seed_python_backend | Python Backend (Production) | nodes only |
| 99999999 | seed_sql | SQL — Querying & Modeling | **lessons: full** |
| aaaaaaaa | seed_ai_engineering | AI Engineering — LLMs, RAG & Agents | content next in queue |
| bbbbbbbb | seed_git_github | Git & GitHub | nodes only |
| cccccccc | seed_blind75 | DSA — Blind 75 / Top Patterns | nodes only |
| dddddddd | seed_dsa | DSA — Algorithms Visualized | **lessons: phases 1–7 + viz** |
| eeeeeeee | seed_behavioral | Behavioral + HR Interview | nodes only |
| ffffffff | seed_java_swe | Java for SWE | nodes only |
| 10101010 | seed_cpp_swe | C++ for SWE / CP | nodes only |
| 20202020 | seed_machine_learning | Machine Learning (Andrew Ng) | nodes only |
| 30303030 | seed_deep_learning | Deep Learning | nodes only |
| 40404040 | seed_devops_cloud | DevOps & Cloud | nodes only |
| 50505050 | seed_linux_shell | Linux & Shell | nodes only |
| 60606060 | seed_data_engineering | Data Engineering | **NEW — written, not yet run** |
| 70707070 | seed_mlops | MLOps — Models in Production | **NEW — written, not yet run** |
| 80808080 | seed_lld | Low-Level Design (LLD / OOD) | nodes only; **never run in prod** (had colliding UUID) |

Key takeaway: **the Tier 1–4 proposal is ~85% already seeded.** The work is presentation
(domains + flagships) and a handful of gap seeds — not 40 new roadmaps.

---

## Target catalog — 4 domains (the signature feature)

Frontend-only: a static `slug → domain` map (e.g. `frontend/src/lib/roadmapDomains.js`),
consumed by `Roadmaps.jsx` to render grouped sections instead of a flat grid. Order within a
domain: content-live first, then by `progress_pct`, then alphabetical. Unmapped slugs fall into
the domain marked `default` so a new seed never vanishes.

### 🎯 Placement Prep
DSA — Algorithms Visualized *(flagship DSA)* · Striver A2Z · NeetCode 150 · Blind 75 ·
Aptitude · System Design (HLD) · LLD/OOD · Behavioral + HR · Core CS (revision role)

### 💼 Software Engineering
Python for SWE · Web Development (Full-Stack) · Python Backend · SQL · Git & GitHub ·
Linux & Shell · DevOps & Cloud · Java for SWE · C++ for SWE/CP

### 🤖 AI & Data
AI Engineering · Machine Learning · Deep Learning · **Data Engineering** (new) ·
**MLOps** (new) · Math for ML *(gap seed, below)*

### 🎓 B.Tech Core
Core CS (OS · DBMS · Networks) · Discrete Math *(gap seed)* · Computer Architecture *(gap seed)*
· Aptitude (cross-listed if cross-listing is supported; otherwise lives in Placement Prep only)

**Cross-listing: approved wherever applicable** (decision 2026-07-03) — `domain` in the map is
an array; Aptitude and Core CS list in both 🎯 Placement Prep and 🎓 B.Tech Core; the DSA
practice sheets may cross-list if useful. Keep it rare (2 domains max per roadmap) so domains
stay meaningful. Domains render as titled sections with the emoji + a one-line "why this
domain" blurb.

### Homepage flagships
Home (or the top of the Learn tab) features a small "flagship" strip — **content-live roadmaps
only** (currently: DSA Visualized, Python for SWE, SQL, Aptitude, Core CS; AI Engineering joins
when its lessons land). NOT the proposal's fixed 10 — featuring node-only shells above
lesson-backed roadmaps inverts the product thesis. The flagship list is just a `flagship: true`
flag in the same domains file.

---

## Deviations from the proposed taxonomy (the discussion points)

1. **One DSA flagship, not five.** "DSA & Problem Solving" as a category is right, but the
   flagship is **DSA — Algorithms Visualized** (the one with lessons + the viz moat). A2Z /
   NeetCode / Blind 75 remain as practice-sheet alternates listed under it in the Placement
   domain. **"LeetCode Daily" is not a roadmap — it's a habit feature** (daily problem → log →
   FSRS card). Parked in the feature backlog; potentially a great retention hook, wrong shelf.
2. **Math: 4 proposed roadmaps → 2.** Prob/Stats + Linear Algebra + Calculus-for-optimization
   collapse into one **Math for ML** roadmap (phases = the three subjects; that IS the Andrew-Ng
   prerequisite set). **Discrete Math** stays separate (it's a B.Tech subject + placement MCQ
   source, different audience-moment). Four thin math roadmaps = four sad empty pages.
3. **Do NOT split Core CS into OS/CN/DBMS yet.** The theory content pipeline, node IDs, user
   progress and lesson folders all anchor to `core-cs`. Splitting = migration pain + orphaned
   `node_id` FKs on lesson cards, for zero content gain. The phases already read as OS/DBMS/CN
   inside the roadmap. Revisit only if one subject's content grows past ~40 lessons.
   (Computer Architecture is the genuinely missing B.Tech subject → its own gap seed.)
4. **Tier 5 (Android/iOS/Game Dev/UI-UX/Robotics/Blockchain): don't seed.** Off-thesis for the
   AI-assisted-coder + placement audience, and each would sit as an empty shell indefinitely.
   Sequenced last in the backlog (not deleted — full-scope principle), behind demand signal from
   the feedback table. "Data Science" is already covered by ML + SQL + Math-for-ML via Career
   Paths, not a separate roadmap. "Distributed Systems (Advanced)" = a later phase appended to
   System Design, not a new roadmap.
5. **The proposal omits Data Engineering and MLOps** — the two roadmaps your own JD research
   elevated and the only two the Career Paths page still renders as "coming soon" (`__de__`,
   `__mlops__` placeholders, plus `__ml__` which should match the existing ML roadmap). That's
   the strongest evidence the taxonomy was technology-first, not career-first. Both seeds are
   already written (`seed_data_engineering.py`, `seed_mlops.py`) — they just need to be run.
6. **"MCP / AI Evaluation / AI Deployment" etc. are nodes, not roadmaps** — additions inside
   AI Engineering (MCP node under Agents; Deployment overlaps MLOps' LLMOps phase). Same for
   most sub-bullets in the proposal: they map to phases/sections of existing seeds.

---

## Gap seeds to write (career/placement-justified only, in priority order)

| Seed | Domain | Justification | UUID (reserve) |
|---|---|---|---|
| `seed_math_ml.py` — Math for ML (Prob/Stats · LinAlg · Calc-for-optimization) | AI & Data | SDE→MLE blocker per run 3 ("math gap"); Andrew-Ng prereq | 90909090 |
| `seed_discrete_math.py` — Discrete Mathematics | B.Tech Core | B.Tech subject + placement MCQs | a0a0a0a0 |
| `seed_computer_architecture.py` — Computer Architecture (COA) | B.Tech Core | the missing 4th core subject | b0b0b0b0 |
| `seed_testing.py` — Software Testing | Software Engineering | JD-common; cheap to seed | c0c0c0c0 |
| `seed_cyber_security.py` — Security Essentials (OWASP-first) | Software Engineering | placement + real-world; keep applied, not academic | d0d0d0d0 |
| `seed_api_design.py` — API Design & Distributed APIs | Software Engineering | learned piecemeal everywhere; distinct interview surface; content is cheap to make honest (it's RetainHQ's own stack). **Boundary:** owns the *contract* (REST/GraphQL/gRPC semantics, auth protocols, versioning, pagination, idempotency, rate-limit design, OpenAPI, webhooks, API security); System Design keeps infra-at-scale (gateway internals, distributed rate limiting); Python Backend keeps implementation. | e0e0e0e0 |

Deferred (backlog, in CLAUDE.md already): TypeScript, React-deep, GenAI-apps,
Resume + Job Hunt (candidate for a *checklist* feature rather than a roadmap), SDLC/Agile
("Software Engineering" the subject — lowest signal, last), Tier-5 specializations.
**Data Structures in Practice** (HashMap internals · LRU · Bloom filters · tries · heaps in
schedulers · B-Trees · skip lists · consistent hashing — "why Redis works"): strong brand fit
with the AI-assisted-coder thesis AND can **reuse the DSA execution-trace viz** (heap ops, trie
walks, hash-ring rebalancing are all traceable) — sequence it right after the viz renderers it
needs exist (heap/tree/graph, DSA phases 9–16). Later addition, but flagged as a signature
candidate, not filler.

Seed conventions (enforce on every new seed): fixed UUID **from the registry above**, `SLUG`
constant (newer pattern — older seeds got slugs backfilled), idempotent delete-then-insert,
`(phase, section, title, tier, description)` tuples, `phase` = step spine, `tier` ∈
{easy, medium, hard}.

> ⚠️ Re-running any seed deletes + recreates its nodes with NEW node UUIDs → wipes
> `user_progress` rows and nulls `activities.node_id` links for that roadmap. Fine pre-content;
> destructive once users have progress/lesson-cards on it. Don't casually re-run seeds for
> roadmaps with live users (this is why the LLD/DSA UUID collision was serious).

---

## Content scoping — "enough, not a PhD"

The depth rule: **scope to the external gate, not the subject.** "Enough" = what the target
role's interview round asks + what day-1 production work punishes you for not knowing. Both are
finite and observable (JD runs, interview-question sweeps via the `PROMPT-*-research.md`
pattern); academic completeness is not. A roadmap drifts toward a PhD the moment the author asks
"what else is true?" instead of "what else gets asked?"

Enforced at three levels (two already exist in the machinery):

1. **Node-inclusion test (the key_memory cap as depth governor).** A node earns its place only
   if (a) you can name a realistic interview question OR a production decision/incident where it
   matters, and (b) its core claim compresses into ~500 chars — 1–3 recall questions a real
   interviewer would plausibly ask. Needs a chapter to answer honestly → split into two nodes or
   cut. Can't write the interview question → cut.
2. **Lesson `kind` = the depth ceiling, enforced by `validate.py`.** Aptitude THIN by contract,
   theory DEEP by contract, concept = runnable. Depth is a schema property, not re-litigated per
   lesson. The rule is two-sided: deep enough to teach from scratch (thin theory fails), capped
   at what the kind's schema shapes.
3. **Roadmap size budget: ~30–50 nodes** (existing seeds sit here naturally; AI Eng = 38).
   Wants 80 → it's two roadmaps, or it's chasing completeness.

Authoring rules:
- **Teach to the decision, not the derivation.** Include: mental model + consequence + common
  mistake. Exclude: proofs, history, exhaustive variant taxonomies, build-from-scratch — UNLESS
  the role's interviews specifically demand it ("implement an LRU cache" is in; "derive the
  decay curve" is not).
- **Every phase completes: "learn X *so that* you can Y in {interview | job}."** If Y is
  "understand the field better" → cut.
- **Breadth of testable claims beats depth of essays.** 45 nodes × one recallable claim each
  outperforms 20 essays — the retention engine schedules claims, not chapters.

### How a roadmap's node list is derived (the recipe)

Five steps; run them in order when writing any new seed. Ownership: Claude curates the node
list against the research evidence (contract side); Antigravity fills lesson content per node
afterwards.

1. **Evidence pass** (the existing `PROMPT-*-research.md` pattern), sources in priority order:
   (a) JD sweep — skills recurring across target-role postings; (b) REAL interview questions
   for the role (question banks, discussion boards — what's actually asked); (c) one or two
   canonical curricula (Andrew Ng, Striver, official docs) as a **completeness cross-check
   only** — canon reveals what you might have missed; inclusion comes from (a)+(b). This
   ordering is the anti-PhD mechanism: syllabi are where scope creep enters.
2. **Extract claims, not topics.** Turn evidence into atomic testable question-families
   ("why is X O(n log n)?", "when does an index not help?"). **A node = one question-family** —
   what an interviewer probes in one exchange. Topics yield chapter-shaped nodes; question-
   families yield card-shaped nodes, which is what the retention engine schedules.
3. **Frequency-weight.** Recurs across JDs/interviews → in. Appears once, or only at
   staff-level → cut, or merge into a neighbor's description. The objective tiebreaker that
   holds the 30–50 budget without taste debates.
4. **Structure.** `phase` = prerequisite spine (foundations → mechanism → applied →
   production/ops); `section` = question cluster (2–6 nodes); `tier` = interview altitude:
   easy = definition/recognition, medium = mechanism/trade-off, hard = design/debug/at-scale.
   Tier answers "which round asks this", not "how it feels".
5. **Validate: the mock-interview test.** Take ~10 real interview questions for the role.
   Every question must land on a node (coverage — a miss is a gap) AND every node must catch at
   least one plausible question or production decision (waste — orphans get cut). Then the
   per-phase "so that" sentence check.

**Reusable prompt:** `content/PROMPT-roadmap-research.md` runs this whole recipe for any roadmap
(fill roadmap + target-roles + canon + size → get a paste-ready `NODES` list + evidence +
mock-interview validation). It stops at the node list; per-node lesson content is the separate
`PROMPT-*.md` enrichment step that runs after the seed exists.

Worked example (Data Engineering seed): "Slowly changing dimensions" is IN — stock DE interview
question + day-1 warehouse decision. "Airflow catchup/backfills" is IN — the JD research says
skipping Airflow fails the screen. "B-tree page layout internals" is OUT — canonical-textbook
material that DE interviews don't ask; that's the PhD direction.

## Catalog card metadata (from the proposal — adopted with the honest-numbers filter)

Principle (existing house rule): **no fabricated numbers.** Per roadmap card:
- **Lesson count — YES.** Computed from the content manifest (same source as the flagship/
  Start-learning logic). Doubles as honest signaling: content-live roadmaps look richer because
  they ARE richer.
- **Estimated hours — YES, derived only.** `Σ lessons × avg-minutes-per-kind`, rounded
  ("~8 hrs"). Never hand-authored; recomputes as content lands.
- **Industry-value — ONLY grounded, no editorial stars.** Either a demand badge sourced from
  the JD research ("High demand · JD research '26") or "builds N career paths" computed from
  `careerPaths.js` references. Five hand-assigned stars = fake precision; rejected.
- **Projects count — NO for now.** Zero projects exist in the product; add the field when they
  do.

## Implementation phases

### Phase A — presentation + wiring (frontend-heavy, no new content; do first)
1. `frontend/src/lib/roadmapDomains.js`: `{ slug: {domain, flagship?, alternateOf?} }` + domain
   metadata (title, emoji, blurb, order). `Roadmaps.jsx` renders grouped sections; unmapped
   slugs → default domain.
2. Flagship strip (content-live only) at the top of the Learn tab; ties into the
   "Start learning" card from `docs/PROMPT-review-ux-friction.md` Task 2 — same
   content-availability source, don't build it twice.
3. `careerPaths.js`: replace placeholders — `__ml__` → `'machine learning'`,
   `__de__` → `'data engineering'`, `__mlops__` → `'mlops'`. (Substring match on lowercased
   title; verify no accidental double-matches, e.g. 'ai engineering' must not match
   "Data Engineering" — it doesn't, but check after any title edits.)
4. **Run the two written seeds** (user runs against prod): `seed_data_engineering.py`,
   `seed_mlops.py`. Verify `/paths` chips resolve and both roadmaps render.
5. Optionally run `seed_lld.py` (now collision-safe) — Placement Prep wants it.
6. Card metadata v1 (lesson count + derived hours + career-path count) once the content
   manifest from step 2 exists — same data source, one pass.

### Phase B — gap seeds
Write + run the 5 gap seeds from the table. Pure additive; each is an hour of curation.
Add each to the domains map + UUID registry as it lands.

### Phase C — content (unchanged priority, this plan does NOT reshuffle it)
AI Engineering → DSA phases 8+ → Data Engineering → ML. The catalog plan only changes what
users SEE; the content queue stays JD-research-driven.

### Update CLAUDE.md when Phase A ships
Fix the stale "10 seeded roadmaps" claim → point at this file's registry; note domains file as
the catalog source of truth.

---

## Non-goals (explicit)
- No backend/schema changes — domains are a frontend concern until proven otherwise.
- No re-titling of existing roadmaps (Career Paths matches on title substrings).
- No mass-seeding of Tier-5 specializations.
- No per-roadmap "% to role X" tracker yet (Career Paths Phase-2 item, separate).
