# Companion — Phase 1 Implementation Spec: Browser Extension & Session Intelligence

**Status:** Draft for owner review · **Owner:** Alok · **Date:** 20 Jul 2026
**Parent doc:** `retainhq-career-coach-design-doc.md` (v1.2) — companion is its ambient-evidence layer.
**Design record:** the seven companion entries in `docs/BACKLOG.md` (2026-07-20) + external review archived in headroom `a38879e7a676ab5aed4cb7b3`. This spec lifts those pre-made decisions into build order; it re-litigates none of them except the consent default (§6, owner call 2026-07-20).
**Predecessors shipped:** evidence spine (phase 1) · tree/mapping (phase 2) · templates v2.

---

## 0. What this is

A Chrome (MV3) extension that turns studying the user already does — LLM chats, LeetCode, YouTube, Coursera, browser PDFs — into evidence events, with **zero per-event interaction**. The pitch: *"You study. RetainHQ notices."*

The engine was built for this: ambient evidence enters as T3/w=0 (capped, near-harmless when wrong), `entity_id` dedupes re-syncs, per-event delete+recompute makes everything undoable, and the triage bucket absorbs ambiguity. The companion is a **producer**, nothing more — it writes the same `learning_events` shape as every other producer and touches no engine code.

### Explicitly out of scope (phase C2+)
Desktop companion (local PDFs/IDE) · Android · Notion · LeetCode **API** verification (T1 solves — separate integration; this phase only observes time on leetcode.com) · coaching of any kind (phase-4 coach agent; classification and coaching stay decoupled per the review verdict) · mastery-moving ambient events (§4's promotion criterion gates that) · school audience (§6 — legal, not technical).

---

## 1. Part A first: the embedding seam (prerequisite, ~half day)

Everything above rung 1 runs through `topic_mapping._similarity`, currently Jaccard word-overlap that scored **0/6 on the owner's real data**. Before any extension work:

1. **Extract a dedicated `services/embeddings.py` (`EmbeddingService`)** — `embed()`, `similarity()`, `nearest_nodes(text, candidates, k)`, plus the node-vector cache — and make `topic_mapping` its first consumer. Three consumers are already specced (career mapping, companion rung 2/3, recurring-cluster detection), which is what justifies the extraction *now*; speculative methods (`cluster()` for search/recommendations) wait for a real consumer, same YAGNI rule that kept pgvector out.
2. Backend: Gemini embeddings (`gemini-embedding-001` or current equivalent; same `GEMINI_API_KEY`): embed each of the user's node texts (`title + description`) once at tree commit, cache in `node_meta` (new nullable `embedding` JSON column — no pgvector: in-process cosine over ≤~100 vectors); embed the query string per lookup. `AUTO_MAP_THRESHOLD`/`TRIAGE_THRESHOLD` re-tuned against ground truth.
3. **Validation gate:** re-run `backfill_career_mapping.py` on the owner's history. Success = the 6 known unmapped activities produce sensible suggestions (owner judges). This is the same "does the number feel honest" criterion every phase uses.

Part A ships independently and improves triage today even if the extension slips.

---

## 2. Architecture (extension side)

```
content scripts (per-surface adapters)        background service worker
  claude.ai / chatgpt.com / gemini.google.com   ┌─ segment buffer (local)
  leetcode.com · youtube.com · coursera.org  →  ├─ session stitcher
  browser PDF viewer (filename only)            ├─ classification ladder (§3)
                                                └─ sync queue → POST /api/companion/sessions
```

- **Adapters emit segments**: `{surface, url_domain, title_metadata, start, end, active}`. LLM-chat adapters additionally expose a *content handle* — text reachable for on-device/opted-in classification but **never buffered to storage and never included in a segment**. Metadata-only is a structural property of the segment type, not a policy promise.
- **Stitcher** (runs on session close = `SESSION_GAP_MIN` (15) of inactivity): clusters segments by time-adjacency, computes duration as the **union of active intervals** (tab-switching must never double-count), produces one `Session{sources[], title_bag, start, end, duration_min}`.
- **Sync queue**: batched, offline-tolerant, idempotent (`session_id` UUID minted at session close = the `entity_id` dedupe key server-side).
- **Recording light**: extension badge shows ● + topic while a session is open; click = stop/correct. No notifications, no prompts, ever (BACKLOG rule).
- **Auth**: extension signs in via Supabase OAuth (supabase-js in the service worker) — same account, standard JWT to the API.

---

## 3. Classification ladder (per SESSION, never per event)

Rungs, each short-circuiting the next:

1. **Metadata rules** — domain allowlist (coursera.org, leetcode.com ⇒ studying by definition) + exact title match against the user's nodes. Free.
2. **Embeddings** (Part A) — `title_bag` vs **all the user's nodes** (career tree + personal/syllabus roadmaps + active catalog roadmaps — widen `candidate_nodes_for_active_goal` accordingly; BACKLOG "your nodes are the filter").
3. **Session LLM** — final automatic classifier (review amendment). One call per closed session, prompt = **the embedding shortlist from rung 2 (top-k candidates), not the full node list** + session metadata (+ metadata-only memory: last ~30 session topics, goal, weak node names). Output ONLY JSON:
   ```json
   {"candidates": [{"node": "...", "rank": 1}, {"node": "...", "rank": 2}],
    "selected": "...", "confidence_band": "high|medium|low",
    "study_type": "...", "assistance_level": "...", "reason": "..."}
   ```
   **The LLM re-ranks the shortlist; it never invents a node** — `selected` and every candidate MUST be from the rung-2 shortlist (validated server-side; violation → treat as `medium` band → triage). Ranked candidates make the second choice a pre-computed fallback for the triage UI and a debugging record when a mapping turns out wrong. Confidence is an **ordinal band, never a probability** (LLM self-reported confidence is uncalibrated — banked decision; same reason candidates carry `rank`, not scores). Where it runs is the §6 tier. Deterministic short-circuit: single-surface sessions fully resolved by rung 1 skip it.
4. **Triage** (existing bucket) — `medium` band lands here; `low`/no-match drops silently, EXCEPT the recurring-cluster rule: same unmatched topic ≥`CLUSTER_MIN_SESSIONS` (3) in `CLUSTER_WINDOW_DAYS` (7) → one pull-based suggestion ("~3h on *compiler design* this week — add it?") that creates a `custom.*` node or seeds a personal roadmap and retroactively maps the buffered sessions.

**Assistance detection** (`none | hint | llm_assisted | solution_seen`) is the LLM rung's unique value — it's a 4× spread in the phase-1 weight table and the difference between honest and flattering ambient evidence. Metadata-only tiers record `assistance: null` (conservative default already treats null as `llm_assisted` — understatement built in).

---

## 4. What gets written (backend)

**One event per session×node:** `event_type=TIME_BLOCK`, `trust_tier=T3_observed`, `source=companion_browser`, `entity_id=session_id`, `duration_min`, `node_id` (or NULL → triage), `payload={sources, study_type, assistance_level, confidence_band, candidates, reason, title_sample, classifier, prompt_version, embedding_model}`.

**Every AI decision is versioned** (`classifier` e.g. `gemini-3.1-flash-lite`, `prompt_version` e.g. `v1`, `embedding_model`) — the same principle as `node_mastery.weights_version`, extended to the AI layer. When classification quality shifts six months from now, the payload says whether the prompt, the model, the embeddings, or the thresholds changed. `prompt_version` is a named constant bumped on any prompt edit, enforced by convention in code review.

**Phase C1 is Balance-only by design: TIME_BLOCK ⇒ w=0. Ambient evidence moves NO mastery yet.** Mastery movement stays with verified producers (reviews, future LeetCode API). Promotion criterion for C2: after ≥4 weeks of owner dogfood, if triage-audited precision of `high`-band `watching` classifications is ≥95%, promote that slice to `CONTENT_CONSUMED` (w=0.04, still 0.35-capped). Written down now so the flip is a measured decision, not scope creep.

**Schema changes (one migration):** add `'companion_browser'` to `SOURCES` + expand the `learning_events` source CHECK (follow `d3a1f7c92e10`'s pattern); add `node_meta.embedding` (nullable JSON, Part A).
**New route:** `POST /api/companion/sessions` (batch, auth, per-user rate cap `COMPANION_MAX_SESSIONS_PER_DAY=50`, ownership-checked node_ids, `ON CONFLICT DO NOTHING` via the existing dedupe index).

---

## 5. Cloud model

Gemini Flash-Lite for both server-side jobs (cluster naming, triage suggestions) and the opted-in chat tier — effective cost ≈ input price ($0.125/M as of 2026-07; re-verify at implementation) since outputs are ~100-token JSON; provider already wired (same key/SDK as syllabus + tree-gen); same family as on-device Nano so tiers behave consistently. A second provider (DeepSeek etc.) adds a key + SDK + failure mode to save fractions of a cent/user-day — rejected (banked).

---

## 6. Privacy, consent & defaults (owner call 2026-07-20 — supersedes the earlier "never default cloud" posture, within legal limits)

**The two data classes get different defaults:**

| Data class | Default | Why |
|---|---|---|
| **Metadata** (titles, domains, filenames, timestamps, durations) | **Cloud (Flash-Lite), ON by default** — no choice screen | Non-private by prior classification; covered by the feature's own opt-in + privacy policy notice. This gives every user rungs 1–3 accuracy out of the box. |
| **Chat content** (LLM-conversation text) | **OFF until a one-time choice screen** — Cloud presented first, pre-highlighted, "Recommended" | DPDP (India) and GDPR require specific, informed, affirmative consent to process conversation content. Silent default-on is the "violates a law" case. The tap on the choice screen IS the consent artifact (log it: timestamp + tier chosen). |

**The choice screen** (shown once, on first visit to an LLM surface after install — not at install, when the benefit is still abstract):

> **How should RetainHQ understand your AI chats?**
>
> **⭐ Smart tracking (Recommended)** — Your chats are analyzed by Google's Gemini to tell *learning* from *getting answers* — so your mastery scores stay honest and your daily plan targets what you actually need. Chat text is processed in the moment and **never stored by RetainHQ, and never used to train models**. `[Turn on]`
>
> **On-device AI** — Same understanding, running entirely inside Chrome (when your browser supports it). Nothing leaves your machine. `[Use on-device]`
>
> **Titles only** — We only look at what you can see in the tab bar. Most private; can't tell studying from copy-pasting, so tracking is less accurate. `[Keep it minimal]`
>
> *Change anytime in settings. Every tracked session shows up in your evidence log and can be deleted with one tap.*

Rules for this copy (the honesty line): every claim must be literally true (the never-trained claim requires the paid Gemini API tier — verify Google's current data-use terms at implementation); the alternatives are real and neutrally worded, never shamed; "Recommended" is earned by the accuracy difference, which the evidence log lets users verify themselves. Benefit-forward ≠ dark pattern as long as declining is one equally-sized tap and the setting is symmetric to change.

**Hard legal boundaries:**
- **Career audience only.** The school platform serves classes 6–12 — minors, for whom DPDP requires verifiable parental consent. The extension refuses to activate for `audience='school'` accounts in phase C1. Not a product decision — a legal one.
- Per-surface tracking remains opt-in at onboarding (allowlist), independent of the chat-content tier.
- Privacy policy update ships in the same release; consent record stored per user (`metric_events`, `event_type='companion_consent'`).

**The no-persistence invariant (explicit, for every future contributor):** *Raw chat content is streamed directly to the selected classifier and is never written to RetainHQ logs, databases, analytics events, or crash reports.* Enforced concretely, not by comment: (a) the segment type carries no content field, so nothing content-shaped can reach the sync queue by construction; (b) `POST /api/companion/sessions`'s Pydantic schema rejects unknown fields; (c) Sentry `before_send` scrubs any classifier-call breadcrumbs in the extension; (d) `payload.title_sample` is capped and titles-only — the analytics allowlist (`CLIENT_EVENT_TYPES` pattern) never accepts free text from the companion. Tested where testable (§8: schema rejection, payload shape).

---

## 7. Config constants

`SESSION_GAP_MIN=15` · `CLUSTER_MIN_SESSIONS=3` · `CLUSTER_WINDOW_DAYS=7` · `COMPANION_MAX_SESSIONS_PER_DAY=50` · band→action map (`high`→auto, `medium`→triage, `low`→drop) · re-tuned `AUTO_MAP_THRESHOLD`/`TRIAGE_THRESHOLD` (Part A). All named, all tunable on owner logs first.

---

## 8. Tests

**Part A:** embedding similarity beats Jaccard on the 6-activity ground-truth set (owner-judged); thresholds re-tuned; existing mapping tests stay green.
**Stitcher (pure, golden-tested like the fold):** interval-union duration (overlapping tabs never double-count) · gap-split at 15 min · multi-surface merge → one session · deterministic session_id.
**Ladder:** rung short-circuits · band→action mapping · recurring-cluster trigger fires at exactly 3/7d · one suggestion max per cluster.
**Backend route:** dedupe on re-sync (same session_id twice → one event) · TIME_BLOCK w=0 invariant (ambient NEVER moves mastery — the phase's T4-style law, own test) · IDOR · rate cap · school-audience refusal.
**Consent:** chat-content classification code path unreachable until a consent record exists; tier switch takes effect without re-install.
**No-persistence invariant (§6):** sessions route rejects any content-shaped field (schema `extra='forbid'`); `title_sample` length-capped; LLM `selected`/`candidates` outside the rung-2 shortlist → demoted to `medium` band (never trusted); versioning fields (`classifier`/`prompt_version`/`embedding_model`) present on every classified event.

---

## 9. Build order

0. **Part A** (embedding seam + backfill validation gate). Independent ship.
1. Migration (`companion_browser` source, `node_meta.embedding`) + `POST /api/companion/sessions` + route tests.
2. Extension skeleton: MV3, Supabase auth, one adapter (YouTube — richest metadata, zero privacy questions) → segments → stitcher (golden tests) → sync. **End-to-end with one surface before adding more.**
3. Remaining adapters: leetcode.com, coursera.org, browser-PDF, then LLM surfaces (metadata-only mode).
4. Classification ladder server-side (rungs 1–2 + Flash-Lite rung 3 on metadata) + triage integration + recurring-cluster suggestions.
5. Consent screen + tier plumbing; on-device Nano feasibility spike (½ day, timeboxed — if the Prompt API isn't viable, the tier degrades to Titles-only and the spec doesn't block).
6. Opted-in chat-content classification (cloud tier first; Nano tier if the spike passed).
7. Owner dogfoods **the exact sitting from the design conversation** — Claude + ChatGPT + LeetCode on one DSA topic — and verifies: one session, union duration, right node, sensible assistance label.
8. Docs same commit (SYSTEM-OVERVIEW §1/§2 + changelog, DECISIONS: consent-default entry + Balance-only entry, BACKLOG grooming) . Do not push without explicit "push".

## 10. Definition of done

- [ ] Part A gate passed (owner judges the 6-activity backfill suggestions sensible)
- [ ] The three-surface DSA sitting lands as ONE session with union duration and a reason string
- [ ] Ambient w=0 invariant test green (no mastery movement from any companion event)
- [ ] Chat content provably untouched without a logged consent record
- [ ] School-audience refusal verified
- [ ] Every tracked session visible + deletable in the evidence log
- [ ] Owner has run it for a week and says the sessions feel honest

## 11. Report back

1. Part A before/after on the 6 ground-truth activities.
2. One week of the owner's real sessions: count, band distribution, triage volume, false positives found via the evidence log.
3. Consent-screen tier split once ≥1 real user beyond the owner exists.
4. Whatever this spec got wrong — spec edit before code.
