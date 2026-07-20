# Career Templates v2 — Quality Pass Implementation Spec

**Status:** Ready to implement · **Owner:** Alok · **Date:** 20 Jul 2026
**Parent docs:** `SPEC-career-coach-phase2.md` (template format, §3) · `retainhq-career-coach-design-doc.md` (versioning law, §6)
**Source:** the 2026-07-20 template quality review (this session) — every change below traces to a specific finding, market-checked against 2026 AI/SDE fresher JDs. No speculative additions.

---

## 0. Findings this spec implements

| # | Finding | Severity | Fix lives in |
|---|---|---|---|
| F1 | **Diagnostic probe selection is subject-blind.** `GET /api/career/diagnostic` takes top-8 probe nodes by `priority` desc; Python's stable sort breaks ties by file order, so the AI Engineer diagnostic asks 8 math/classical-ML questions and **zero LLM/GenAI questions** (16 p5 probes exist; the first 8 in file order are all foundational). Backend is milder (6 DSA + 2 SQL, no networking/API probe ever fires). Someone who already builds RAG apps gets their entire GenAI subtree scored `unexposed` → the tree over-assigns work they've done. | **Bug** | `routes/career.py` (§2) |
| F2 | **ai_engineer has no "working with LLM APIs" material.** No chat-completions, streaming, rate-limits/retries, or cost/token-budgeting nodes — the layer every 2026 JD calls baseline, and the layer the repo's own research-gated `ai-engineering` roadmap dedicates an entire phase to. Also hurts Tier-2 topic mapping: lessons studied from that roadmap have nothing to map onto. | High | `ai_engineer.v2.json` (§3.1) |
| F3 | **ai_engineer misses Hugging Face / open-weights, reranking + hybrid retrieval, and a fine-tune-vs-RAG-vs-prompt decision node** — all named in the JD scan. Balance skews theory-heavy (math+classical+DL = 26/68 nodes vs applied GenAI = 10). | Medium | `ai_engineer.v2.json` (§3.1) |
| F4 | **sde_generalist DSA core misses the four highest-frequency interview patterns**: two pointers, sliding window, binary search, heaps/priority queues (backend has 3 of the 4 — generation variance, not curation). No greedy node in any template. | Medium | `sde_generalist.v2.json` (§3.2) |
| F5 | **backend misses heaps/priority queues, greedy, intervals.** | Medium | `backend.v2.json` (§3.3) |
| F6 | **est_effort_min is systematically ~3-5× optimistic** (backend tree totals ~67h; realistic fresher prep is several hundred). Harmless today; phase 3's scheduler will consume it and inherit the error. | Deferred | §6 (constraint note only) |

Market evidence: the 2026 entry hiring triad is RAG + agents + evals; Python + LLM API integration is the stated baseline; Hugging Face/LangChain named explicitly in Indian fresher JDs. (Sources logged in the session review; re-verify via the §8 research prompt if desired.)

---

## 1. Scope

**In:** probe-selection fix (code + test) · three `*.v2.json` template files · validator probe-spread check · sync + docs.
**Out (explicitly):** effort recalibration (F6 — do it as part of phase-3 scheduler work, when there's a consumer to calibrate against) · template-upgrade UX for existing committed trees (parent §16, still P2) · new roles (data_engineer — needs the §8 research first) · any change to committed v1 trees.

Per the parent scope rule, ai_engineer additions are paid for with removals (§3.1) to stay ≤70 nodes.

---

## 2. Fix F1 — subject-aware probe selection

In `backend/app/api/routes/career.py`, replace the current sort-and-slice in `get_diagnostic`:

```python
# OLD: probe_nodes.sort(key=lambda n: -n["priority"]); selected = probe_nodes[:8]
# NEW: round-robin across subjects so no subject monopolizes the 8 slots.
```

Algorithm (deterministic, no randomness — repeat calls must return the same set):

1. Group probe-bearing nodes (`diagnostic_probe` **and** `diagnostic_answer` present) by subject, in template subject order.
2. Within each subject, order by `priority` desc (stable → template order within a priority).
3. Round-robin across subjects in template order, taking each subject's next-best probe, until `DIAGNOSTIC_PROBE_COUNT` (8) collected or probes exhausted.

Result for ai_engineer v2: 8 probes spanning ≥8 subjects instead of 2. The fix makes **every future template safe by construction** — template authors can keep assigning honest priorities without gaming file order.

`POST /diagnostic/submit` needs no change (it validates against the full template, not the selected subset).

**Tests** (extend `test_career.py`):
- T1: for each shipped template, the selected probe set spans ≥ `min(8, subjects_with_probes)` distinct subjects.
- T2: ai_engineer's selection includes ≥1 probe from `nlp_llms` **and** ≥1 from `genai_engineering` (the exact regression F1 describes).
- T3: selection is deterministic across two calls.

---

## 3. Template changes — shipped as new `*.v2.json` files

**Versioning decision (per parent §6):** template files are immutable once shipped — content changes mean a new version file, never an edit to `*.v1.json`. Keep the v1 files in place. `list_templates()` already resolves the latest version per role, so new goals pick up v2 automatically. **Committed v1 trees are unaffected**: `template_version` pinned at commit is metadata only — nothing re-reads the template file post-commit. (Pre-commit, `GET /diagnostic` loads the *latest* template, which is correct: the version isn't pinned until commit.) Removed nodes' stable_keys are retired, never reused for a different concept.

All new probe-bearing nodes need an authored `diagnostic_probe` + `diagnostic_answer` (validator enforces the pair). Author at implementation time to the same standard as v1 — conceptual, one-sitting-answerable, grading-rubric-quality answers.

### 3.1 `ai_engineer.v2.json` (68 → 70 nodes)

**Add — new subject `llm_apis` ("Working with LLM APIs"), default_priority 5, placed after `python_ml`:**

| stable_key | title | prio | effort | depends_on | probe |
|---|---|---|---|---|---|
| `llm_apis.chat_completions` | Calling Chat Completion APIs | 5 | 60 | — | ✓ |
| `llm_apis.streaming` | Streaming Responses | 3 | 45 | `llm_apis.chat_completions` | |
| `llm_apis.rate_limits_retries` | Rate Limits & Retries | 3 | 45 | `llm_apis.chat_completions` | |
| `llm_apis.cost_token_budgeting` | Cost & Token Budgeting | 4 | 45 | `llm_apis.chat_completions`, `nlp.tokenization` | ✓ |
| `llm_apis.open_weights_hf` | Open-Weight Models & Hugging Face | 4 | 75 | `llm_apis.chat_completions` | ✓ |

**Add — into `genai_engineering`:**

| stable_key | title | prio | effort | depends_on | probe |
|---|---|---|---|---|---|
| `genai.reranking_hybrid_retrieval` | Reranking & Hybrid Retrieval | 3 | 60 | `genai.rag_basics` | |
| `genai.finetune_vs_rag_vs_prompt` | Fine-tune vs RAG vs Prompt: Choosing | 4 | 45 | `genai.rag_basics`, `nlp.pretraining_finetuning` | ✓ |

**Remove (the payment — all low-priority, weak-JD-signal for this role):** `classical_ml.clustering_kmeans` (p2) · `classical_ml.dimensionality_reduction_pca` (p2) · `math.eigenvalues_eigenvectors` (p3 — its only dependent was PCA) · `data_eng.feature_stores` (p2) · `dl.rnn_and_sequence_models` (p3 — near-legacy for this role; attention node already motivates the sequence-modeling problem itself).

**Rewire:** `genai.prompt_engineering_basics` gains dep `llm_apis.chat_completions` (you prompt an API you can call). Nothing else changes.

Net: 68 − 5 + 7 = **70** — at the soft cap, acceptable.

### 3.2 `sde_generalist.v2.json` (57 → 62 nodes)

**Add — into `dsa_core`:**

| stable_key | title | prio | effort | depends_on | probe |
|---|---|---|---|---|---|
| `core.two_pointers` | Two Pointers | 4 | 90 | `core.arrays_and_strings` | |
| `core.sliding_window` | Sliding Window | 4 | 90 | `core.two_pointers` | |
| `core.binary_search` | Binary Search | 4 | 60 | `core.arrays_and_strings` | ✓ |
| `core.heaps_priority_queues` | Heaps & Priority Queues | 4 | 75 | `core.trees_and_traversals` | ✓ |
| `core.greedy` | Greedy Algorithms | 3 | 75 | `core.sorting_algorithms` | |

No removals needed (62 < 70).

### 3.3 `backend.v2.json` (63 → 66 nodes)

**Add — into `dsa`:**

| stable_key | title | prio | effort | depends_on | probe |
|---|---|---|---|---|---|
| `dsa.heaps_priority_queues` | Heaps & Priority Queues | 4 | 75 | `dsa.trees.binary_trees` | ✓ |
| `dsa.greedy` | Greedy Algorithms | 3 | 75 | `dsa.sorting.comparison_sorts` | |
| `dsa.intervals` | Interval Problems | 3 | 60 | `dsa.sorting.comparison_sorts` | |

---

## 4. Validator addition (`content/validate_career_templates.py`)

New **warning** (not error): any subject with `default_priority >= 4` that contains zero probe-bearing nodes. Rationale: after the §2 round-robin fix, a high-priority subject with no probes silently gets zero diagnostic coverage — the author should know. Warning, not error, because some subjects legitimately don't probe well (e.g. `interview_prep`).

---

## 5. Sync + registration

After template files land: run `backend/sync_career_templates.py` (manual, per D-035) so `backend/app/data/career_templates/` carries all six files (3× v1 + 3× v2). `list_templates()` needs no change — it already picks the highest version per role. Verify `GET /api/career/templates` reports `v2` for all three roles.

---

## 6. Deferred: effort recalibration (F6)

Do **not** touch `est_effort_min` in this pass — there is no consumer yet, so there's nothing to calibrate against, and doubling numbers by gut feel just swaps one fiction for another. **Binding constraint recorded for phase 3:** the scheduler must not treat `est_effort_min` as trustworthy absolute time; treat it as *relative* weight until calibrated against real per-node time-on-task data (which `learning_events.duration_min` is already accumulating). Add one line to `BACKLOG.md`: "Calibrate template est_effort_min against real learning_events durations before the phase-3 scheduler consumes them."

---

## 7. Build order

`pytest` green between steps; `validate_career_templates.py` green after every template edit.

1. §2 probe-selection fix + tests T1–T3 (code first — makes the template work verifiable).
2. §4 validator warning.
3. `ai_engineer.v2.json` (author the 4 new probes) → validate.
4. `sde_generalist.v2.json` (2 new probes) → validate.
5. `backend.v2.json` (1 new probe) → validate.
6. Run `sync_career_templates.py`; verify `GET /templates` serves v2.
7. Live check: create a throwaway goal for `ai_engineer`, hit `GET /diagnostic`, confirm the 8 probes span the subjects (T2's claim, verified against the real file). Archive the goal after.
8. Docs, same commit: `SYSTEM-OVERVIEW.md` (§ content system: six template files, probe round-robin; changelog line) + `DECISIONS.md` (one entry: v2-file versioning + round-robin selection + the additions-paid-with-removals list).

Do not push. Deploy only on an explicit "push".

## Definition of done

- [ ] All three roles report `version: "v2"` from `GET /api/career/templates`
- [ ] ai_engineer diagnostic includes ≥1 LLM/GenAI probe (live-verified, not just unit-tested)
- [ ] Both validators + full backend suite green
- [ ] v1 files untouched; owner's committed v1 tree unaffected (spot-check `/coach` still renders)
- [ ] `SYSTEM-OVERVIEW.md` + `DECISIONS.md` + `BACKLOG.md` updated in the same commit

---

## 8. Deep-research prompt (optional now; required before the data_engineer template)

The v2 changes above are already evidence-backed — running this now would mostly re-confirm them. Its real purpose is (a) the **next** template (`data_engineer`, per build priority AI-Eng → DSA → Data-Eng) and (b) evidence-based priority calibration across all templates in a future v3. Run it through a deep-research tool (or hand to Antigravity) as-is:

```text
ROLE: You are researching skill requirements for entry-level (0-2 yrs) software
roles in India, 2026 hiring cycle, to build curriculum trees for a learning app.
Output must be evidence-ranked, not vibes-ranked.

ROLES TO COVER: (1) Backend Engineer, (2) AI Engineer (LLM/GenAI application
engineer, NOT ML researcher), (3) SDE Generalist, (4) Data Engineer.

SOURCES — in priority order, cite every claim:
1. Real job postings (Naukri, LinkedIn India, Internshala, company career pages —
   sample ≥25 postings per role; classify each as IT-services / GCC / product /
   startup, since requirements differ sharply by segment).
2. Interview experiences (GeeksforGeeks interview experiences, LeetCode Discuss
   compensation+interview threads, Glassdoor India) — what is actually ASKED,
   by round type (OA / DSA round / CS-fundamentals round / LLD / HLD / domain).
3. Salary/role reports for India 2025-26 to weight which segments hire most freshers.
Reject: influencer roadmaps, course-seller blogs, anything without primary data.

FOR EACH ROLE, PRODUCE:
A. Skill-frequency table: skill → % of sampled postings mentioning it →
   segment breakdown (services/GCC/product/startup) → representative citations.
B. Interview-topic-frequency table: topic → % of sampled interview experiences
   where it was asked → which round it appears in.
C. A proposed curriculum tree: 40-70 atomic, testable topic nodes grouped into
   6-9 subjects. Per node: title (≤6 words), priority 1-5 assigned FROM the
   frequency data (5 = appears in >60% of postings or interviews; 1 = <10%),
   estimated effort in minutes, prerequisite topics (within the same tree only,
   no cycles), and — for the top ~15 nodes by priority — one diagnostic question
   answerable verbally in under 2 minutes plus a 2-4 sentence reference answer.
D. Deltas vs the app's current template (summaries attached below): nodes we
   have that the data says to cut or demote; nodes the data says we're missing;
   priorities that disagree with observed frequency by ≥2 levels. Cite each delta.

CONSTRAINTS:
- Distinguish "mentioned in JD" from "actually tested in interviews" — weight
  interview evidence higher for priority assignment.
- For AI Engineer: verify or refute — (a) fine-tuning is oversold in JDs relative
  to what juniors actually do; (b) evals/RAG/agents are the 2026 triad; (c) how
  much classical ML is genuinely asked of GenAI-app hires at each segment.
- For Data Engineer: establish whether fresher DE roles in India genuinely exist
  at meaningful volume, or whether the realistic entry path is backend/analyst →
  DE; the tree's framing depends on the answer.
- Flag every claim you could NOT verify with a primary source as UNVERIFIED
  rather than silently including it.

CURRENT TEMPLATE SUMMARIES (for section D):
[paste the subjects + node-title lists from content/career-templates/*.v2.json]
```

---

## 9. Report back on completion

1. The 8 probes each template's diagnostic now serves, listed — the owner sanity-checks they read like a sensible screen for that role.
2. Node counts + validator output for all three v2 files.
3. Confirmation the owner's committed v1 tree is untouched.
4. Anything in this spec that turned out wrong or underspecified — spec edit before code, per the parent doc's rule.
