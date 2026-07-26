# SPEC — LeetCode Retention (concept-first review for solved problems)

Status: **draft, unscheduled**. Written 2026-07-21.
Parents: `ARCHITECTURE-learning-system.md` (layer laws, D-038 — this spec's §5.0/§5.4/§5.5
were promoted there), `SPEC-companion-phase1.md` (event capture), `SPEC-career-coach-phase3.md`
(scheduling), `services/evidence_weights.py` (weight table), `docs/DECISIONS.md`.

---

## 0. The finding that shapes this spec

The proposed architecture — event producers → concept graph → derived mastery → hybrid
shared/personal cards → self-graded FSRS — is **already ~70% built**. This spec is mostly
*wiring*, not new architecture. What already exists at HEAD:

| Proposed layer | Already in repo |
|---|---|
| Event producers, uniform shape | `LearningEvent` — docstring names LeetCode explicitly; `SOURCES` already contains `"leetcode"`; `PROBLEM_SOLVED` already in `EVENT_TYPES` |
| Idempotent capture | `uq_learning_event_dedupe` on `(user_id, source, entity_id)` — built for polling producers |
| Reflection inputs | `Activity.difficulty` (1–5), `.needed_hint`, `.mistake`, `.key_memory` |
| Reflection → mastery | `_PROBLEM_SOLVED_PASS_WEIGHTS` keyed on exactly `(difficulty, assistance)` |
| Concept vocabulary | `dsa` roadmap: 109 nodes, `NodeMeta.stable_key` (`dsa.graphs.bfs`), `NodeMeta.embedding` |
| Prerequisite / transfer graph | `RoadmapNodePrerequisite` — docstring already describes root-cause diagnosis |
| Concept mastery as derived aggregate | `NodeMastery` — recomputable from `learning_events` alone |
| LLM names the gap, never the grade | `Review.ai_verdict` / `.ai_recalled` / `.ai_feedback` — "proposal only — user's rating/recalled stay authoritative" |
| Evidence honesty across producers | `TRUST_TIERS`, `T3_EXPOSURE_CAP = 0.35`, `CAPPED_EVENT_TYPES` |

**Genuinely new work is four things:** a problem catalog, problem→node mapping, a shared
card bank, and backfill import. Everything else is a call into an existing seam.

Design law inherited from the parent docs, restated because it governs every choice below:
*mastery may understate, it must never overstate.*

---

## 1. Not in scope

Copying problem descriptions, editorials, or example test cases (copyright, and it makes us a
problem browser) · AI-generated "interview readiness %" · LLM-assigned review grades ·
non-DSA problem sources (Codeforces, HackerRank) · mobile capture · a second concept graph
parallel to the roadmap nodes (see §2, this is the main failure mode) · problem *recommendation*
("solve these next") — that's the phase-3 scheduler's job, not this spec's.

---

## 2. Concept vocabulary — closed set, and it is the existing `dsa` roadmap

**Decision: the concept vocabulary IS `roadmap_nodes` for the `dsa` roadmap, extended as
needed. No new concept table.**

Rationale: `SPEC-companion-phase1.md` already classifies observed content against the user's
tree nodes via the `NodeMeta.embedding` seam. A parallel LeetCode concept graph would drift
from it within weeks, and the companion classifier would be mapping into the wrong graph.
One graph or the numbers stop meaning anything.

Consequences:

1. The vocabulary is **closed and hand-authored**. LLMs are used to *classify problems onto
   the set*, never to *emit new concepts*. Free-form concept generation produces
   `Hash Map` / `Hashmap` / `Hash Table` / `Dictionary Lookup` as four nodes and the graph is
   landfill by problem 300.
2. Gaps get filled by **authoring a node + lesson** through the normal content pipeline
   (`content/roadmaps/dsa/*.json`, `content/validate.py`), not by a side channel.
3. Current coverage is 109 dsa lessons. Pre-work: audit against a canonical pattern list and
   author the missing *pattern* nodes (monotonic stack, prefix accumulation, difference array,
   binary search on answer already exists, …). Estimate ~20–40 new nodes. **This is the asset.
   Do it by hand, once, before any mapping runs.**
4. Transfer edges reuse `RoadmapNodePrerequisite` where the relation is genuinely prerequisite.
   A distinct *sibling/confusable* edge type is likely needed (§6) — defer until §6 has data.

---

## 3. Data model (new)

Three new tables. All migrations must include `ENABLE ROW LEVEL SECURITY` per CLAUDE.md.

### 3.1 `problems` — shared catalog, no `user_id`

```
id            uuid pk
source        text        # 'leetcode' (only value for now; keeps the table honest later)
external_id   int         # LeetCode question number — unique per source, user-searchable
slug          text        # 'product-of-array-except-self'
title         text
difficulty    text        # 'easy' | 'medium' | 'hard'
tags          jsonb       # raw source tags, stored as-is. NOT the concept mapping.
url           text
acceptance    float|null
catalog_version text      # bump when re-imported
UNIQUE (source, external_id)
```

Metadata only. No description, no editorial, no test cases — see §1.

### 3.1.1 Catalog acquisition — RetainHQ servers never call LeetCode

Governing rule: all LeetCode traffic happens in a browser or an owner-run script — never
from prod infra (no official API; unofficial surfaces are ToS-grey; a server dependency on
them is an outage and an IP-ban waiting to happen). Three channels:

1. **Seed (build-time artifact).** Delegated to Antigravity — contract:
   `content/HANDOFF-leetcode-catalog.md`. One-off owner-run script pulls the problem list from TWO
   independent unofficial surfaces — `graphql` `problemsetQuestionList` and the legacy
   `api/problems/all/` REST endpoint — rate-limited (~1 req/2s). Accept only rows where both
   agree on `(number, slug, difficulty)`; disagreements go to manual review. Output is
   committed as `content/leetcode-catalog/catalog.v1.json` + the archived raw responses
   (evidence law: keep raw data). Re-import = a deliberate versioned re-run, never a cron.
   Import gate validates: unique `(source, external_id)`, difficulty enum, slug format, and
   count sanity vs. the prior version (a big drop = parse failure, not reality). Store the
   paid-only flag.
2. **Live capture (self-healing).** The extension reads problem metadata from the DOM of
   the page the user opened themselves and attaches it to the solve event; backend upserts
   unknown problems. New problems enter the catalog the first time anyone solves them —
   no re-import required, no extra requests made.
3. **Backfill (user's own session).** The public profile API caps at ~20 recent solves —
   useless for backfill. Instead, on opt-in the extension calls `api/problems/all/` with
   the user's own cookies (rows carry per-user `status:"ac"`), extracts solved problem
   numbers client-side, and POSTs the list. RetainHQ never holds or proxies LeetCode
   credentials.

Degradation: if every surface breaks, channel 2 still works (the page is the source), the
last committed catalog still serves, and §4 manual entry covers the rest. Acceptance rate
is cosmetic — never chase its freshness.

### 3.2 `problem_concepts` — the mapping, hand-reviewed

```
id          uuid pk
problem_id  uuid fk problems
node_id     uuid fk roadmap_nodes
role        text     # 'primary' | 'supporting'
confidence  float    # classifier output, retained for audit
reviewed_by text|null # 'human' once curated; NULL = machine-only, see below
UNIQUE (problem_id, node_id)
```

Add to the table: `mapping_version text` — bumped whenever a problem's concept assignment
changes, same discipline as `WEIGHTS_VERSION`. "Why did mastery move?" must always be
answerable with "mapping v1 → v2 moved Two Sum's primary from X to Y", and re-imports that
bring new LeetCode tags/patterns get a `review_date` sweep (cadence: open question §10).

`role='primary'` is capped at **one per problem** (application-enforced) — the concept the
problem is *for*. Supporting concepts are what it also touches.

**Machine-only rows (`reviewed_by IS NULL`) may not produce shared cards or drive concept
surfacing.** They can seed mastery at reduced weight, **banded by `confidence`** — reuse the
companion's ordinal-band rule (high/med/low → auto / triage / drop), never treat the float
as a calibrated probability. A 0.98 machine row and a 0.54 machine row are both un-reviewed,
but only the high band may seed mastery; the low band maps nothing. This is the gate that
stops a mushy mapping from silently becoming the product.

### 3.2.-1 The pedagogy axis — study vs. practice

`role` answers *which concept*. This answers *why this problem*, and it is what makes the
card bank affordable: **only `canonical` problems produce `concept_cards`.** 3,659 mapped
problems x 4 card types is ~14,600 cards (unbuildable); ~150 canonical x 4 is ~600
(authorable, curatable, improves forever). Practice problems produce no cards — they are
pure mastery evidence.

Added to `problem_concepts`:

```
teaching_role     text   # canonical | practice | variant | synthesis
order_in_concept  int    # sequence within (node_id, teaching_role); 0 = first
assumes           jsonb  # [node_id, ...] concepts required BEYOND the primary
alternatives      jsonb  # [node_id, ...] concepts that EACH independently solve it
```

**`supporting` is AND, `alternatives` is OR.** Supporting = concepts the problem also
exercises (you need them too). Alternatives = approaches that each solve it on their own —
Trapping Rain Water by `two-pointers` OR `monotonic-stack` OR `prefix-sums`; Kth Largest by
`top-k-with-a-heap` OR `quickselect`; Reverse Pairs by `merge-sort` OR `fenwick-tree-bit`.

`primary` stays exactly one, and not as a matter of taste: it is the key
`learning_events.node_id` resolves from (§3.2.1). Two primaries means an event either
double-counts mastery across both nodes or picks one arbitrarily — the exact failure the
evidence law exists to prevent. Multi-approach is a fact about the *problem*, so it lives in
the catalog, not in the mastery routing key.

Why this field earns its keep — it is the best card source in the system:
- **Transfer cards** (§5's strongest type) come straight from it: *"You solved this with a
  heap. What would quickselect buy you, and when would you prefer it?"* Generated from a
  curated fact rather than an LLM guess about what's related.
- **Complexity cards** get real material: O(n log k) heap vs O(n) average quickselect.
- **§6 discriminating cards**: a problem with 3 approaches is where confusable concepts
  genuinely touch, so it is the highest-yield place to author cards that separate them.

A problem may be `canonical` for more than one node — Trapping Rain Water can legitimately
introduce both `two-pointers` and `monotonic-stack`. The cap is **2 canonical problems per
node**, never a cap on nodes per problem.

**Deferred seam (do not build yet):** with opt-in code capture (§4.2), the event's `node_id`
could resolve to the approach the user *actually wrote* rather than the canonical primary —
§3.2.1 already makes node assignment re-resolvable, so the seam exists. It is inference, so
it waits for shadow-mode validation like everything else in §5.0.

| `teaching_role` | Meaning | Produces cards? | Scheduler uses it for |
|---|---|---|---|
| `canonical` | The problem a teacher introduces the concept with. **Max 2 per node**, app-enforced like `role='primary'`. | **Yes** | "Study X" |
| `practice` | A rep. Same pattern, no new idea. | No | "Practice X" (N of them, ordered) |
| `variant` | A twist that breaks a naive application of the pattern (duplicates allowed, negative numbers, in-place required). | No | Late practice; feeds §6 edge-case cards |
| `synthesis` | Genuinely needs 2+ concepts. `supporting` is load-bearing here. | No | Readiness checks, never teaching |

**Selecting `canonical` is a curation judgment, not a classification** — it is the one field
that must be `reviewed_by='human'` before use. Signals to propose it: namesake match
(problem slug ≈ concept slug), low `external_id` (older problems are the ones the canon
formed around), easy/medium difficulty, high acceptance, and no `assumes` entries. **Do not
import another site's curated list** (NeetCode 150, Blind 75) wholesale — that is someone
else's editorial work, and §1's "don't become a problem browser" applies to curation too.

`assumes` is what makes "can this learner attempt this yet?" answerable: a problem whose
`assumes` contains a node the user has no mastery on is not practice, it is a wall.

**Open — deferred, do not build yet:** a `synthesis` problem arguably should move mastery on
its `supporting` nodes too, not just `primary`. That is a weight-table change with a real
double-counting risk (companion spec's stitching concern in a new costume), and it needs
`evidence_weights.py` versioning plus a golden scenario before anyone touches it. Until
then: primary only.

### 3.2.0 Not every catalog problem is mappable — the out-of-scope bucket

Verified against the real v1 pull (2026-07-21, 3999 problems): **~91 free problems carry
zero tags because they are not algorithm problems** — LeetCode's JavaScript
(`counter`, `sleep`, `memoize`, `array-prototype-last`) and pandas study-plan sets. A
further 41 untagged rows are paid-only (tags hidden from anonymous requests; benign).

The mapping packet therefore needs a third outcome besides primary/supporting:
`role='out_of_scope'` — recorded explicitly, with no `node_id`. Forcing `sleep` onto a DSA
node is precisely the vocabulary pollution §2's closed-set rule exists to prevent, and a
classifier told to always produce an answer *will* produce one.

Solves on out-of-scope problems still write a `PROBLEM_SOLVED` event (the solve is a fact)
but with `node_id = NULL` — no mastery movement, no cards. If JS/pandas ever get their own
roadmap, those events remap for free (§3.2.1 makes node assignment re-resolvable).

### 3.2.1 The mapping is a hypothesis — events must not freeze it

Architecture-doc consequence (D-038: evidence is fact, inference is hypothesis): the *fact*
in a solve event is **which problem was solved** (`entity_id` / payload problem reference).
The *node* is the mapping's current opinion. Therefore `LearningEvent.node_id` for
catalog-mapped solves is a **denormalized cache of mapping-at-write**, not part of the fact:
on a `mapping_version` bump, mastery recompute re-resolves node assignment from the current
mapping. Otherwise a corrected mapping leaves historical events pointing at the wrong
concept and "recomputable from evidence alone" silently becomes false. (Events from
non-catalog producers — reviews, manual logs with an explicit node — are unaffected; there
the node *is* the fact.)

### 3.3 `concept_cards` — shared card bank, no `user_id`

```
id          uuid pk
node_id     uuid fk roadmap_nodes      # the concept, always set
problem_id  uuid fk problems | null    # null = pure concept card, not problem-anchored
card_type   text     # 'intuition' | 'complexity' | 'edge_case' | 'transfer'
prompt      text
model_answer text                      # revealed on grade — authored, not generated at review time
discriminates_from jsonb               # [node_id, ...] — see §6
status      text     # 'draft' | 'published'
version     int
```

Generated once (Antigravity, against a Claude-owned `PROMPT-concept-card.md`), critiqued by
the Sonnet critic, published by hand. Never generated per-review — that cost curve ends the
project, and it means a new user's first review is good instead of cold-start mush.

### 3.4 Reuse: `Activity` is still the card

`Activity` carries the FSRS state (`stability`, `difficulty_fsrs`, `next_review_at`) and
`Review` is its log; one activity = one card. Do not build a second scheduler.

Add one nullable column:

```
Activity.concept_card_id  uuid fk concept_cards | null
```

- `concept_card_id IS NULL` → today's behaviour, a user-authored key memory. Unchanged.
- `concept_card_id` set → the card's text comes from the shared bank; the FSRS state, review
  history, and `Activity.mistake` stay per-user. `node_id` is set from the card's node.

Personal cards (from the user's own mistake text / code) are plain Activities with
`node_id` set and `concept_card_id` NULL — i.e. **the existing shape**, no new mechanism.

---

## 4. Event capture (§ reconciles with companion phase 1)

Two producers, two tiers. **The producer abstraction must not flatten the tier** — that is
what keeps mastery honest.

| Producer | event_type | trust_tier | entity_id | Moves mastery? |
|---|---|---|---|---|
| Extension detects **Accepted** on leetcode.com | `PROBLEM_SOLVED` | `T1_verified_external` | submission id | Yes, per `_PROBLEM_SOLVED_PASS_WEIGHTS` |
| Time on leetcode.com without a solve | `TIME_BLOCK` | `T3_observed` | session id | No — `w=0`, companion phase C1 rule |
| Backfill import (§7) | `PROBLEM_SOLVED` | `T1_verified_external` | `import:{external_id}` | Yes, at defaults (§7) |
| Manual entry by question number / fuzzy title | `PROBLEM_SOLVED` | `T4_claimed` | NULL | Yes, lowest weight |

`node_id` on the event = the `role='primary'` concept for that problem.

Manual entry is a **fallback**, not the primary path (non-Chrome, mobile, correcting a miss) —
per `SPEC-companion-phase1.md` §"zero per-event interaction", the extension path must never
require a form. Search accepts LeetCode question number (unique, exact) or fuzzy title match.

### 4.1 Reflection

The only human input, and it is **skippable and deferrable**:

```
Confidence     1–5   → Activity.difficulty
Needed hint?   y/n   → Activity.needed_hint → event.assistance
Biggest mistake      → Activity.mistake  (free text, optional)
```

Note these already exist on `Activity` and already key the weight table. Nothing new.

Rules:
- The solve event is written **immediately on Accepted**, before and regardless of reflection.
  Never block logging on reflection.
- If skipped, the event takes the conservative defaults already in `evidence_weights.py`
  (`_DEFAULT_ASSISTANCE = "llm_assisted"`) — understate, never overstate.
- Deferred reflection is offered once, at the first review of that problem's card, then dropped.

### 4.2 User code (optional)

If the user opts in, the extension captures **their own submitted solution** (theirs, not
LeetCode's) into `Activity.notes`. This is the highest-signal personalization input available
at zero typing cost; one line of takeaway text cannot carry that load. Opt-in per the
companion privacy-tier ladder — treat code as content, not metadata.

---

## 5. Scheduling — cards are the FSRS unit, concepts are an aggregate

**Decision: FSRS schedules cards. Concepts are never an FSRS item.**

FSRS fits stability and difficulty **per item**. Feeding one "Hash Map" state alternating
observations from Two Sum and LRU Cache blends unlike difficulties; the estimate does not
average out, it degrades — and it degrades silently, producing intervals that feel arbitrary
and cost the user's trust in the scheduler, which is the whole product. Concept-level
scheduling is a different model (knowledge tracing), not an FSRS parameter.

The layering that gets the same product experience:

1. **Timing** — `scheduler.py`, per Activity. Untouched.
2. **Mastery** — `NodeMastery.m_learned`, derived from `learning_events`. Untouched.
3. **Selection + framing** — new. "Review *Prefix Accumulation*" resolves to: among due cards
   whose `node_id` (or `problem_concepts`) touches that node, pick the lowest retrievability,
   and present it under the concept's name.

Layer 3 is where the "memory consolidates around concepts, not problems" experience lives.
It is a query, not a scheduler.

### 5.0 The asymmetry rule (governs the whole inference layer)

**The concept/inference layer may ADD or ADVANCE reviews. It may never REMOVE or DELAY
them — until delay is validated by shadow-mode measurement (§5.4).**

Rationale: every honesty mechanism in the evidence system (T3 cap, w=0 time blocks,
conservative defaults) bounds *overstated mastery*. Delaying a due card is a different
category of action — it removes a repetition. If the transfer inference is wrong
("sibling card felt Easy, therefore this one is safe"), the user forgets, the app told
them not to review, and no cap bounds that cost. Concept-level strength ≠ item-level
memory; the transfer coefficient between them is an empirical unknown, not a design input.

Concretely allowed: surface a dependent concept's card sooner after an upstream failure
(promote-on-weakness — costs at most one unneeded review, fails safe). Concretely
forbidden until validated: skip or push back a due card because its concept looks strong
(demote-on-strength — fails expensive).

### 5.4 Shadow-mode validation — the delay decision becomes a measurement

When the concept layer *would have* delayed a card (concept confidence above threshold,
card due), log the would-have-delayed event, **show the card anyway**, and record the
grade. Each shadow event directly measures the transfer coefficient: "when concept
confidence > X, the due sibling card was graded Good-or-better Y% of the time."

After months of accumulation, delay stops being philosophy and becomes a threshold read
off a table. This log is also the dataset any future research claim
(cross-concept memory inference alongside an untouched FSRS) would rest on — the
product ships a selection query in days; the validated student model is only ever
derivable from this data, so start logging from day one.

### 5.5 Activation vs. strength (deferred, banked)

Distinct from mastery: **strength** is slow-moving (`m_learned`); **activation** is
fast-decaying — 3 hours reading DP makes DP *hot* today regardless of long-term strength.
Two design notes for when it lands:

- Activation is a reason to **deprioritize within the due set** (show cold cards first —
  reviewing an already-active trace is low-value massed practice), never to delay past
  due. Reordering passes the asymmetry rule; removal does not.
- No new pipeline: activation = a fold over recent `learning_events`
  (`occurred_at`, `duration_min`) with a fast decay constant, exactly as `m_learned` is
  the same fold with a slow one. A derived value, not a system.

Deferred until companion C1 time-block events flow (its input signal).

### 5.1 Grading

Self-graded, four buttons (Again / Hard / Good / Easy) after reveal — mapped through the
existing `rating` + `recalled` → `quality` path.

The LLM's role is **already correctly scoped at HEAD**: `Review.ai_verdict` / `.ai_feedback`
are explicitly "proposal only — user's rating/recalled stay authoritative." Keep that boundary
exactly. The LLM reads the answer and *names the gap*; it never sets the interval. Banning the
LLM from grading is right; banning it from diagnosing would delete §6.

---

## 6. Confusion detection — earn it or don't ship it

"You repeatedly confuse prefix products / range sums / difference arrays" is the strongest
moment in the pitch and **cannot be derived from self-grades**. A four-button rating says
recall failed; it never says *what it was confused with*.

Two mechanisms, both required:

1. **Discriminating cards.** `concept_cards.discriminates_from` lists the near-miss concepts a
   card is authored to separate. A failure on a discriminating card localises by construction.
   This is a card-contract decision made once at authoring time — encode it in
   `PROMPT-concept-card.md`, same as every other content contract.
2. **Gap labels.** `Review.ai_feedback` already stores the LLM's one-sentence read of a
   free-text answer. Store a structured `confused_with` node reference alongside it when the
   model can name one.

**Reporting floor:** never surface a confusion claim below **n ≥ 5 failures across ≥ 3 distinct
cards spanning ≥ 2 weeks**. Below that it is the readiness-percentage failure mode in better
clothes — a confident-looking claim from noise, which damages trust harder precisely because
it looks credible.

---

## 7. Backfill import — this is the onboarding, not a nice-to-have

Under capture-only, a user who has already solved 200 problems opens an empty app. Their
public LeetCode profile carries the solved list.

- Import solved problems → `PROBLEM_SOLVED` events, `entity_id = "import:{external_id}"`
  (dedupes cleanly against later live captures via the existing partial unique index).
- Imported solves have **no confidence, no hint flag, no mistake**. They take
  `evidence_weights` defaults, which understate. Correct.
- First session is therefore a **diagnostic, not a review**: *"You've solved 187 problems —
  let's find out which ones you still have."* Far better than an empty queue, and it fills the
  concept graph before the user has done any work.

Acquisition mechanics: §3.1.1 channel 3 — the extension fetches the solved list inside the
user's own authenticated session, client-side; RetainHQ servers never call LeetCode. Never
make a user-facing promise that depends on any unofficial surface staying up.

---

## 8. Build order (dependency-sequenced, no scope cuts)

0. **Concept vocabulary audit** — hand-author the missing dsa pattern nodes + prerequisite
   edges. Blocking; nothing downstream is meaningful without it.
1. **`problems` catalog** + import script (metadata only).
2. **`problem_concepts` mapping** — LLM classifies against the closed set, human reviews.
   Ship with `reviewed_by='human'` on the top ~150 problems only; the rest stay machine-only.
3. **Backfill import** (§7) + diagnostic first session.
4. **Extension Accepted detection** → `PROBLEM_SOLVED` event, wired into the existing
   companion pipeline.
5. **Reflection UI** — skippable, deferrable.
6. **`concept_cards` bank** — contract, Antigravity generation, Sonnet critique, 4 card types.
7. **Concept-framed selection** (§5.3) + the concept view.
8. **Confusion detection** (§6), gated on the reporting floor.

## 9. Hypothesis and success metrics

**H1 (research hypothesis, NOT an architecture assumption):** concept-first review produces
higher long-term retention than problem-first review. Everything above is machinery for
testing H1; the architecture must remain useful even if H1 is refuted (the capture,
catalog, and evidence layers stand on their own).

**Honesty constraint:** a four-week n=1 dogfood cannot measure H1 — retention differences
need months and a comparison condition. The dogfood measures the *leading indicators* that
decide whether H1 is worth the longer test. Two tiers, two timelines:

### 9.1 Dogfood gate (4 weeks, owner, after step 6) — "is this worth continuing?"

| Metric | Source | Pass looks like |
|---|---|---|
| Reflection completion rate | events with non-default confidence/hint ÷ solves | ≥ 60% — below that, reflection UX has failed and personal cards starve |
| Recognition rate on transfer cards | per-review 1-tap "did this connect?" flag | transfer cards produce recognition moments problem cards don't |
| Review time per card | `Review.duration_ms` (exists) | concept cards not materially slower than existing cards |
| Queue completion | completed ÷ due, weekly | no drop vs. pre-feature baseline |
| Subjective usefulness | weekly 1-line owner note | at least one "that question caught a real gap" per week |

Fail on the first two → stop before building §6/§7 polish. The others are guardrails.

### 9.2 H1 proper (months, needs >1 user) — "did it work?"

Primary: retention — grade distribution on cards at matched intervals, concept-framed vs.
problem-framed (the shadow log §5.4 accumulates exactly this). Secondary: mastery
trajectory per node, re-solve success on previously-solved problems. Not designed in
detail here; designed only after 9.1 passes.

---

## 10. Open questions

- Does `role='primary'` survive contact with real problems, or do too many genuinely have two?
- `discriminates_from` needs a real confusable-pair list before the card contract can be
  written — derive it from the vocabulary audit (step 0) or from early failure data?
- Sibling/confusable edges: reuse `RoadmapNodePrerequisite` with an edge-type column, or a new
  table? Defer until §6 has data; a premature edge type is worse than none.
- Weight for `T4_claimed` manual entries is not yet in `evidence_weights.py` — needs a value
  and a `WEIGHTS_VERSION` bump.
- Prerequisite-edge queries run in both directions and they are different features:
  backward = root-cause diagnosis (fail Decorators → blocker is Closures, per the
  `RoadmapNodePrerequisite` docstring); forward = weakness propagation (fail Prefix Sum →
  surface Difference Array sooner, allowed under §5.0). Same edges, two queries — keep them
  named separately so neither silently absorbs the other.
- Any concept-strength adjustment goes through the `evidence_weights.py` fold with a
  documented weight and `WEIGHTS_VERSION` bump — never a second ad-hoc additive accumulator
  ("+0.08"), or mastery stops being auditable/recomputable.
- Mapping staleness cadence: LeetCode adds tags and the pattern meta evolves — how often
  does the catalog re-import + `review_date` sweep run? Per catalog_version bump, or
  calendar-scheduled? Decide when the first re-import actually happens, not before.
- Recompute cost of §3.2.1: re-resolving node assignment on mapping bumps means recompute
  reads `problem_concepts` per event. Fine at current scale; if it ever isn't, snapshot the
  mapping per version rather than weakening the re-resolution rule.
