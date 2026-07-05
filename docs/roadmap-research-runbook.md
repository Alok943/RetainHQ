# Roadmap deep-research runbook — run it in Gemini, not in-app

Status: 2026-07-04. Companion to `content/PROMPT-roadmap-research.md` (the method) and
`docs/roadmap-catalog-plan.md` (the catalog + UUID registry).

## Why external, not the in-app workflow
The in-app deep-research Workflow was tried on the API Design test slice (run `wf_5fd68b10-d88`)
and **failed with 0 sources fetched** — it hit the session request limit mid-run after burning
~856k subagent tokens for zero usable output. Web-fan-out inside the app competes with your
session budget and rate limits. **Run roadmap research in Gemini Deep Research** (or another
standalone deep-research tool). It has the browsing depth, it doesn't spend your Claude session,
and the prompt already has a Gemini two-step path. Use Claude only to review/critique the JSON
that comes back and to wire the resulting `NODES` into the seed.

---

## Procedure (per roadmap, one run at a time)

1. **Open Gemini Deep Research** (gemini.google.com → Deep Research mode).
2. **Paste the filled prompt** for the roadmap (the API Design test slice is ready below; for
   other roadmaps, copy `content/PROMPT-roadmap-research.md`, fill the four `<<...>>` slots).
3. Let Deep Research produce its prose report, then **in the same chat send the conversion
   message** (bottom of `PROMPT-roadmap-research.md`) to get the structured `NODES` + evidence +
   validation + sources.
4. **Save the full response** to `content/research/<slug>/nodes.md` (create the folder). This is
   the audit trail for why the roadmap looks the way it does — keep the evidence + `excluded` +
   validation, not just the tuples.
5. **Hand the `NODES` block back to Claude** (paste it) to: sanity-check scope (is the `excluded`
   list substantial? does every node map to a real interview question?), fix any tier/boundary
   drift, then generate `backend/seed_<slug>.py` from an existing seed template with the UUID
   from the registry in `docs/roadmap-catalog-plan.md`.
6. **You run the seed** against prod (`./.venv/Scripts/python.exe seed_<slug>.py`) — Claude never
   runs prod seeds.
7. Per-node lesson content comes LATER via the matching `content/PROMPT-<kind>.md` enrichment
   prompt — this runbook stops at the node list.

---

## READY TO PASTE — API Design foundational test slice (finish the run that failed)

> Paste this whole block into Gemini Deep Research. It is `PROMPT-roadmap-research.md` pre-filled
> and scoped to 3 phases (~12–15 nodes) as the cheap validation run.

You are a senior hiring manager + interview panelist for **Backend Engineer / Backend SDE roles
in India, 0–4 years / new-grad & early-career**, doing rigorous, citation-backed research to
design the FOUNDATIONAL PORTION of an "API Design & Distributed APIs" learning roadmap. Cover
ONLY three phases: (1) REST fundamentals & resource semantics, (2) API authentication &
authorization, (3) API versioning & evolution. You are ruthlessly scope-disciplined: define what
a candidate MUST know to clear the interview and survive week one — NOT the academic field.

GOVERNING PRINCIPLE — "enough, not a PhD": a node earns inclusion ONLY if you can name (a) a real
interview question asked of these roles where it decides the answer, OR (b) a concrete day-1
production decision/incident where not knowing it hurts. Otherwise CUT IT.

EVIDENCE, in priority order (inclusion comes from 1 & 2; 3 is a cross-check only):
1. Sweep 15–25 real Indian backend JD postings (LinkedIn, Naukri, Wellfound, Instahyre, company
   pages); extract recurring API skills/concepts + rough frequency.
2. Real interview questions ACTUALLY asked of these roles (Glassdoor, LeetCode discuss, GfG
   interview experiences, Reddit) about REST, API auth, and versioning; capture recurring
   question-families.
3. Canon cross-check ONLY (reveals gaps, never justifies inclusion): MDN HTTP docs, the REST
   dissertation summary (Fielding), OAuth 2.0 spec, OWASP API Security Top 10.

BOUNDARY — this roadmap owns the CONTRACT (protocol/resource semantics, auth protocols,
versioning/evolution). CUT and push to `excluded`: gateway internals & distributed rate limiting
at scale (belongs-in-System-Design); framework-specific implementation like FastAPI/Express
specifics (belongs-in-Backend); anything senior-only or canon-only.

DERIVATION: extract testable question-families (one interviewer-probe = one node),
frequency-weight, hold to ~12–15 nodes across the 3 phases.

DELIVERABLE (return exactly this):
1. A Python `NODES` list of `(phase, section, title, tier, description)` tuples grouped by the 3
   phases in learning order, with `SLUG="api-design"`, a `TITLE`, and a one-sentence roadmap
   `DESCRIPTION` above it. tier = easy (definition/recognition) / medium (mechanism/trade-off) /
   hard (design/debug). description = ONE recall-testable claim ≤120 chars, mechanism-first —
   e.g. "PUT is idempotent, POST is not — retrying a failed PUT is safe, retrying POST may
   double-create", NOT "learn PUT vs POST". Plain-text only, no LaTeX/images.
2. `excluded`: things a naive API syllabus would include but you cut — each `{item, reason}`,
   reason ∈ {low-frequency, senior-only, canon-only, belongs-in-System-Design,
   belongs-in-Backend, out-of-scope}. Make this substantial — it proves scope discipline.
3. `validation`: 8 real interview questions for these roles across the 3 phases, each mapped to
   the node(s) that cover it (proves coverage). Flag any node that maps to NO question (candidate
   for cutting). Plus one "so that…" sentence per phase.
4. `sources`: 8–15 real URLs actually consulted, split into `jd` / `interviews` / `canon`. No
   fabricated links.

Cite, never copy — original wording throughout. Then, if you produced a prose report first,
convert it to exactly the above format and output only that.

---

## After the test slice validates
If the API Design slice comes back clean (substantial `excluded`, every node maps to a real
question, tiers sane), run the full roadmaps in this order (matches catalog-plan priority):

1. **API Design** — full (add phases: rate-limit *design*, API security/OWASP, gRPC/GraphQL
   contrast, webhooks/idempotency, OpenAPI) — extend the same run.
2. **Data Engineering** — a hand-drafted seed already exists (`seed_data_engineering.py`);
   run research to VALIDATE/refine that node list rather than from scratch (paste the existing
   NODES as "here is a draft — critique and correct against evidence").
3. **MLOps** — same as DE (`seed_mlops.py` draft exists → validate).
4. Gap seeds from the catalog plan: Math for ML, Discrete Math, Computer Architecture, Testing,
   Security Essentials.

For each: fill the four slots in `content/PROMPT-roadmap-research.md`, pin **geography +
seniority** tightly in `<<TARGET_ROLES>>` (the single biggest scope lever — vague roles are how
this drifts back toward a PhD), run in Gemini, save to `content/research/<slug>/nodes.md`, hand
`NODES` to Claude for the seed.

## Do NOT
- Re-run the in-app deep-research Workflow for this — it exhausted the session limit for 0
  sources. External tool only.
- Batch multiple roadmaps in one research run — one roadmap per run.
- Let Claude run prod seeds — that stays with you.
