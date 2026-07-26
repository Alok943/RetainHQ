# RetainHQ Learning System — Architecture

**Status:** adopted 2026-07-21 (D-038). This doc owns the *layer stack and the laws*.
Each layer's implementation detail lives in its owning spec — this doc never duplicates it.

**Relationship to other docs:** `retainhq-career-coach-design-doc.md` (external parent) owns
the career-coach product rationale; `SPEC-career-coach-phase1..3` own the evidence spine,
tree, and scheduler; `SPEC-companion-phase1.md` owns capture; `SPEC-leetcode-retention.md`
owns the problem catalog, card bank, and the inference-layer rules it introduced (§5.0,
§5.4, §5.5 there). Shipped system state stays in `SYSTEM-OVERVIEW.md`. When this doc and an
implementation spec disagree, **this doc's laws win; the spec's details win.**

---

## 0. The law above all layers

> **RetainHQ never makes an irreversible decision from inferred knowledge.**
>
> **Evidence is fact.** An Accepted submission, a completed review, a self-rated
> confidence, a typed mistake — these happened. They are append-only and kept forever.
>
> **Inference is hypothesis.** "Probably knows hash maps", "probably confused DFS/BFS",
> "probably transferred learning" — these are estimates. A hypothesis may **recommend,
> prioritize, explain, and surface**. It may never **overwrite, contradict, delay, or
> delete** anything derived from facts — until the specific inference has been validated
> by shadow-mode measurement (§5).

This is one law seen three times in the existing specs, now stated once:
- Phase 1: "T4 never moves mastery"; mastery may understate, never overstate.
- Phase 3: "the scheduler never overrides FSRS."
- LeetCode spec §5.0: the asymmetry rule — inference may add/advance reviews, never
  remove/delay them.

## 1. The layer stack

```
┌───────────────────────────────────────────────────────────────┐
│ 1. EVIDENCE            learning_events (append-only, forever) │
│    producers: reviews · manual log · extension (companion) ·  │
│    LeetCode Accepted · backfill import · future sources       │
├───────────────────────────────────────────────────────────────┤
│ 2. KNOWLEDGE GRAPH     roadmap_nodes (closed vocabulary) +    │
│    roadmap_node_prerequisites + problems + problem_concepts + │
│    concept_cards                                              │
├───────────────────────────────────────────────────────────────┤
│ 3. LEARNER INFERENCE   node_mastery (strength) · activation · │
│    confusion edges · transfer estimates — ALL derived,        │
│    ALL recomputable from layer 1 alone                        │
├───────────────────────────────────────────────────────────────┤
│ 4. SELECTION           queue builder / scheduler: which due   │
│    cards + study items the user sees, in what order, framed   │
│    under which concept                                        │
├───────────────────────────────────────────────────────────────┤
│ 5. SCHEDULING          FSRS, per card (Activity). Timing is   │
│    memory-physics. Nothing above this line touches it.        │
├───────────────────────────────────────────────────────────────┤
│ 6. REVIEW EXPERIENCE   reveal → self-grade → (LLM diagnoses,  │
│    never grades) → writes layer-1 evidence                    │
└──────────────────────────────────────────────────────────────┘
                    └──── closed loop: 6 feeds 1 ────┘
```

Single responsibility per layer. The differentiator is not any one layer — it is the
closed loop: an increasingly accurate model of how one person learns, across every source.

## 2. Per-layer laws

### Layer 1 — Evidence
- **Append-only, kept forever.** Rows are never updated; correction = compensating event
  or soft-delete + recompute (already the `LearningEvent` contract). Raw evidence is the
  training set for every future model — future models are always better than today's;
  raw data is the only thing that can't be re-derived.
- **Trust tiers survive every abstraction.** A producer pipeline must never flatten
  T1-verified and T3-observed into "a study event." The tier travels with the event.
- **Zero-friction capture.** Ask humans only what machines cannot infer (confidence,
  hint-used, mistake, reflection). Everything inferable is automatic; reflection is
  skippable and never blocks the factual event.

### Layer 2 — Knowledge graph
- **The concept vocabulary is closed and hand-authored.** LLMs classify *into* it; they
  never extend it. There is exactly one graph (`roadmap_nodes`) — no parallel ontologies.
- **One graph, two traversals:** upstream = diagnosis ("why did this fail?" → root-cause
  prerequisite), downstream = surfacing ("what else is now suspect?"). Same edges, two
  named queries — neither absorbs the other.
- **Hundreds of concepts, not thousands of items.** Problems, videos, PDFs, lessons all
  map into the same node set. The catalog (mapping + canonical cards + misconceptions) is
  the compounding asset; item metadata is a convenience.

### Layer 3 — Learner inference
- **Everything is a derived cache.** Deleting layer 3 costs CPU, never data
  (the existing `node_mastery` contract, generalized).
- **One fold, documented weights, versioned.** Every strength adjustment goes through
  `evidence_weights.py` with a `WEIGHTS_VERSION` bump. No second accumulator, no ad-hoc
  "+0.08", no boost/penalty side-scores — or nobody can explain why a number moved.
- **Every inference knows its own certainty.** Any derived estimate carries
  `{confidence, evidence_count, model/weights_version}` (the pattern `NodeMastery`
  already sets with `evidence_count` + `weights_version`; new inference types must match
  it). An inference that can't state its evidence base may not be surfaced to the user.
- **Strength ≠ activation.** Strength: slow fold, long-term. Activation: fast-decay fold
  over recent events, "hot today." Same fold machinery, different decay constant.

### Layer 4 — Selection
- **Selection is a query, not a scheduler.** "Review Prefix Accumulation" = pick the
  lowest-retrievability due card touching that node, framed under the concept's name.
- **The asymmetry rule** (LeetCode spec §5.0): selection may add, advance, prioritize,
  reorder-within-due. It may not remove or delay a due card on inferred strength until
  shadow mode validates the specific inference.
- **Explainability is a feature requirement, not a debug nicety.** Every card shown must
  be able to answer "why this card, now?" from its inputs — FSRS state, concept mastery,
  activation, transfer/propagation trigger — on an internal explain surface (extends the
  phase-1 debug page + phase-3 plan `reasons`). If the system can't explain a selection,
  the selection logic doesn't ship.

### Layer 5 — Scheduling
- **FSRS is per-card and untouched.** Concepts are never an FSRS item (blending unlike
  difficulties silently degrades stability estimates). Review timing is never rewritten
  by layers 3–4. Inventing review history is forbidden — the FSRS log must remain a
  record of reviews that actually happened.

### Layer 6 — Review experience
- **The user (or objective correctness) grades. The LLM diagnoses.** `ai_verdict` /
  `ai_feedback` are proposals and gap-labels; `rating`/`recalled` stay authoritative.
- **No unexplainable numbers.** A mastery or readiness figure may be shown only with its
  derivation one tap away ("4 of 17 subpatterns touched; retrievability 61% on those").
  Anything labeled "readiness" that can't show its arithmetic is banned.
- Confusion claims obey the reporting floor (LeetCode spec §6): ≥5 failures, ≥3 cards,
  ≥2 weeks.

## 3. V1 discipline — log everything, use almost none of it

Explicitly **postponed** (collect the data now, act on it later):
transfer coefficients · automatic delay of due cards · activation-driven scheduling ·
confusion inference (until the floor is met) · adaptive graph propagation.

Live from day one: shadow-mode logging (§5.4 of the LeetCode spec) — every
"would-have-delayed / would-have-propagated" decision is logged with its inputs and the
observed outcome. Each postponed feature graduates by measurement, not by argument.

## 4. What each layer is measured by

| Layer | Honest when… |
|---|---|
| Evidence | replaying it reproduces all derived state, byte-for-byte |
| Graph | a human curated every edge that drives user-facing claims |
| Inference | understates under uncertainty; states its evidence count |
| Selection | every shown card explains itself |
| Scheduling | the FSRS log contains only reviews that happened |
| Experience | the user's grade is final; every number shows its arithmetic |
