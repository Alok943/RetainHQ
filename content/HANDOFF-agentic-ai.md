# HANDOFF — Agentic AI + MCP batch (26 lessons, ai-engineering roadmap)

> Paste the block below into Antigravity (repo access required). Saved here so the
> mission survives session resets — point a fresh session at this file to resume.
> Status: Batch 1 authored + critiqued (fix list below); batches 2-5 pending.
>
> Provenance (2026-07-17): Trends-validated cluster ("ai agents" ~9x/12mo; "mcp server"
> now out-sizes "langchain"; SERPs young). Curriculum was deep-researched (Gemini),
> critiqued, gap-filled with source-verified round-2 patches (all 31 docs URLs fetch-
> verified), and merged. The research file is the ground truth — lessons are authored
> FROM it, not from model memory.

---

You are authoring the 26-lesson agentic expansion of RetainHQ's `ai-engineering`
roadmap, `kind: "engineering"`. Work inside this repo.

## Read these files FIRST, fully, in this order — they are the contract
1. `content/PROMPT-engineering.md` — base contract, INCLUDING its **AGENTIC BATCH**
   section at the bottom (the 7 rules there govern this batch; they reference the
   research file and outrank your general knowledge).
2. `content/research/agentic-ai-curriculum.json` — 26 research objects keyed by
   `slug`. Before authoring each lesson, read its object end-to-end:
   `core_questions` (must all be answered), `misconceptions` (become common_mistakes
   + the prediction rung via `predict_moment`), `docs_truth` (your only allowed
   sources, weighted by `authority`), `code_moment` (the snippet to implement),
   `churn_risk` (how defensively to write code), `seo` (title/description block),
   `overlaps_existing` (extend, don't re-teach), `prereqs`.
3. Gold reference for shape/depth: `content/roadmaps/ai-engineering/embed-and-retrieve-top-k.json`.
4. The slug/title table: `content/_TODO-engineering.md` § "Agentic expansion (26)".
   Filenames = slugs exactly; lesson `title` may be the nicer display title from the
   research object.

## Batch order & sizing
- **Batch 1 (author first): the 8 MCP lessons** — highest SEO priority; the window is
  open while no education site owns "mcp server" SERPs.
- Batch 2: Agent Architectures (6). Batch 3: Reliability (5). Batch 4: Security (5).
  Batch 5: Memory (2).
- After EVERY batch: `python content/validate.py` must end `All content valid. [OK]`.

## Non-negotiables (critic will check these)
- Every lesson answers ALL of its `core_questions` across its `sections`.
- Every misconception in the research object appears as a `common_mistakes` entry;
  at least one `predict_moment` becomes the hook question or a predict-style recall
  item, keeping its concrete situation (don't generalize it into mush).
- `sources` = the object's `docs_truth` URLs. No other citations.
- Framework names only inside code snippets / clearly-marked application layers;
  prose teaches the concept. `mcp-sampling-and-elicitation` must flag its wire
  format as in-flux (2026-07 spec RC — see its research object).
- Lessons with `overlaps_existing` start at the delta and link back to the existing
  lesson; re-teaching it is a fail.
- Every lesson carries a top-level `"seo": {"title": "...", "description": "..."}`
  (≤60 / ≤158 chars) built from the object's `seo.primary_phrase` + one alternate.
- The one `-unsourced` misconception (multi-agent handoff) may only be phrased as a
  tempting assumption, not as a documented failure.

## After authoring
1. `python content/validate.py` → all green.
2. Report per-lesson: which core_questions map to which sections, and any place you
   had to deviate from the research object (with why). The critic pass (separate
   session, Sonnet) reviews against the research file — deviations you don't declare
   will read as errors.
3. Do NOT run seeds or touch the DB. `backend/seed_ai_engineering.py` already
   contains the 26 nodes (titles slugify to your filenames); the founder runs it.

---

# BATCH 1 CRITIC FIXES — do these BEFORE starting Batch 2 (added 2026-07-18)

Batch 1 was reviewed (independent critic + fact verification against real SDKs/tools).
Overall: teaching quality strong — 4 of 8 lessons pass as-is (`mcp-tools-resources-prompts`,
`mcp-transports-stdio-http`, `mcp-fastmcp-server-building`, `mcp-vs-function-calling` minus one
link fix). The failures cluster in ONE defect class: **invented API surfaces and outputs stated
as fact**. A new RUNNABLE-CLAIMS RULE was added to `content/PROMPT-engineering.md` — read it;
it applies to every remaining batch.

Fixes, ranked (all verified — none are speculative):

1. **`mcp-integration-problem` / code_snippets[0]:** `anthropic.beta.tools.Tool(name=...)` does
   not exist in the Anthropic Python SDK. Real surface: tool definitions are plain dicts passed
   as `tools=[{'name': ..., 'description': ..., 'input_schema': {...}}]` to
   `client.messages.create`. Rewrite the snippet with the real shape.
2. **`mcp-architecture-hosts-clients-servers` / both code_snippets:** `mcp.Client().connect(url)`
   does not exist in the MCP python-sdk. Real surface: `ClientSession` opened over a
   transport-specific context manager (`stdio_client(...)`, `streamablehttp_client(...)`).
   Rewrite with the real shape (see modelcontextprotocol.io/docs/develop — the docs_truth URL
   in your research object).
3. **`mcp-architecture-hosts-clients-servers` / sections[1]:** the spec's lifecycle phases are
   **initialization → operation → shutdown** (ping is a utility, not a lifecycle phase). Correct
   the phase list AND add one sentence on what each phase does (capability negotiation happens
   during initialization) — core_question 2 is currently named, not taught.
4. **`mcp-observability-and-logging`:** two required fixes. (a) The research object's
   second misconception — two connected servers exposing the SAME tool name (e.g. both GitHub
   and Linear expose `create_issue`) resolving ambiguously — is entirely missing; add it as a
   `common_mistakes` entry + one recall question. (b) The lesson never links its
   `overlaps_existing` prerequisite `observability-traces-logging`; add the handoff sentence
   ("general tracing/logging was covered there — this is the MCP transport wrinkle").
5. **`mcp-observability-and-logging` / code_snippets[0]:** the MCP Inspector UI does NOT run on
   `localhost:5173` — verified against the official README: client UI defaults to **6274**,
   proxy to **6277**. Fix the port and keep the `npx @modelcontextprotocol/inspector` invocation.
6. **`mcp-sampling-and-elicitation` / seo.description:** 164 chars — trim to ≤158.
7. **`mcp-vs-function-calling` / mental_model.description:** the
   `[Function/tool calling](file:///roadmaps/...)` link is a broken URI scheme and markdown links
   don't render in that field anyway — replace with a plain-text reference ("you built this loop
   in the Function/tool calling lesson").
8. **`mcp-transports-stdio-http` / code_snippets[1]:** the `"transport": "stdio"` config key is
   not the literal schema of any named real host (Claude Desktop uses `mcpServers` with
   `command`/`args`, or `url` for remote). Either show a real host's actual config or caption
   yours as "illustrative shape, not a specific host's schema".

After fixing: run `python content/validate.py`, then proceed to **Batch 2 (Agent
Architectures, 6 lessons)** per the plan above. Same report format as batch 1, plus: for every
code snippet, state HOW you know the API surface is real (docs URL or "ran it").

---

# SAMPLE-TASK VERDICT — `agent-autonomy-spectrum` (2026-07-18)

**APPROVED — proceed with the remaining 5 Batch-2 lessons.** Research fidelity is clean:
all 3 core_questions are genuinely taught (not just named), both misconceptions became
common_mistakes, BOTH predict_moments are used (one drives the hook, one drives section 4 +
the OA), sources match docs_truth exactly, and the seo block is built on the researched
primary_phrase and well inside limits. The mental model (train-on-a-track vs self-driving
car) maps cleanly, and the three-snippet build-up (workflow → router → agent) is the right
shape for a taxonomy lesson. This is the quality bar — keep it.

Apply these 4 fixes to it, and treat 1-2 as rules for the remaining Batch-2 lessons:

1. **Caption the pseudo-code (RULE — applies to every remaining lesson).** `call_llm()`,
   `fetch_db_record()`, `execute_tool()`, `call_llm_for_next_step()` are invented helpers.
   For a control-flow/architecture lesson this is the RIGHT call — real SDK boilerplate
   would bury the very contrast you are teaching — but the RUNNABLE-CLAIMS RULE in
   PROMPT-engineering.md requires it be *labelled*. Add to each snippet's `explanation` (or
   as a comment on line 1): "Helper names are placeholders — the control flow is the point."
   The rule: real SDK code must be real; illustrative shapes must say they are illustrative.
   Never a third category that looks real but isn't.
2. **Add `key_points` (RULE).** The contract says use it when a concept HAS discrete parts —
   a three-way taxonomy is the canonical case, and it is what a learner will memorize. Add
   three entries (Workflow / Router / Agent) with a one-line "who decides the path" each.
3. **Fix the animation — it currently contradicts the body.** Section 3 teaches
   "ReAct (Reason + Act)", but the animation's two steps are labelled `Act` and `Observe`,
   with no reasoning step. ReAct's defining feature is the interleaved reasoning trace.
   Relabel so the loop reads Reason → Act → Observe (the model actor should carry "Reason").
4. **Last recap must place the node (RULE).** Contract asks the closing recap to locate the
   lesson in the bigger flow; yours closes on a rule ("Never use an AI agent to replace a
   standard code statement"). Point forward to `state-machines-for-agents` (its own `unlocks`)
   — e.g. "...next you'll see how a state machine makes an agent's loop controllable."
   Minor while you're in there: `oa_questions[1].company` "System Design" → "System Design
   interview"; soften "adds a two-second delay" to "adds latency" (unmeasured number).

---

# BLOCKING BUG FOUND IN BATCH 1 — `mcp-transports-stdio-http` teaches a deprecated transport

Your batch-1 fix pass applied 7 of the 8 items correctly (verified: the fabricated
`anthropic.beta.tools.Tool` and `mcp.Client().connect()` are gone, Inspector port is 6274,
the tool-name-collision misconception and the observability-traces-logging link both landed,
the `file:///` link is gone, the lifecycle now reads initialization → operation → shutdown).

**But the transports lesson regressed into a factual error.** It now teaches
Server-Sent Events (SSE) with its dual-endpoint architecture as the CURRENT remote transport
(`sections[3]`, `sections[4]`, and `seo.title` = "MCP Transports: stdio vs SSE"). Verified
against the live spec at modelcontextprotocol.io/specification/2025-11-25/basic/transports:
the current transports are **stdio** and **Streamable HTTP**; HTTP+SSE was replaced in the
2025-03-26 revision and appears on that page only as deprecated/legacy. The page mentions
Streamable HTTP 26 times; your lesson mentions it twice, in passing.

Fix required before Batch 2 ships:
- Rewrite `sections[3]`/`sections[4]` to teach **Streamable HTTP** as the remote transport
  (single MCP endpoint; the server MAY upgrade a response to an SSE stream for
  server→client messages — SSE survives as a streaming mechanism *inside* Streamable HTTP,
  not as a separate transport). Keep SSE only as a one-line "you will see HTTP+SSE in older
  servers and blog posts — that is the pre-2025-03-26 transport, now deprecated." That
  history note is genuinely useful: it is exactly what a learner hits in stale tutorials.
- `seo.title` → lead with the real terms (slug and roadmap node both say "stdio & HTTP"):
  e.g. "MCP transports: stdio vs Streamable HTTP" (40 chars).
- `seo.description` is also **161 chars — over the 158 limit**; rewrite it around the
  research object's `primary_phrase` ("mcp transport stdio") plus the alternate
  "mcp streamable http", and drop the SSE framing.

**Process note:** the critic marked this lesson PASS because it does not web-search — it
flagged the claim for verification instead, and verification caught it. So: any lesson
claim naming a spec revision, a version, a port, or a "X replaced Y" fact must cite the
docs_truth page you actually read, in the section that makes the claim.

---

# BATCH 2 IN-PROGRESS ERROR — `when-multi-agent-underperforms` is the wrong `kind`

`python content/validate.py` currently FAILS on it:
`code_walkthrough is required: an object with a non-empty 'code' string`.

Root cause: the file was authored with **`"kind": "concept"`** and carries the concept-kind
field set (`overview`, `why_learning_this`, `understanding_checks`, `practice_tasks`) instead
of the engineering set. `concept` is the runnable-in-browser kind — it requires
`code_walkthrough`, which is why the validator rejects it. **Every lesson in the
`ai-engineering` roadmap is `kind: "engineering"`** (see the contract's template table:
"No `code_walkthrough` (that's the runnable `concept` kind), no `formula`, no `method`,
no `understanding_checks`").

This is not a one-field fix — re-author the lesson against the engineering template:
`hook` → `mental_model` → `sections` (with recaps) → `code_snippets` → `key_points` →
`common_mistakes` → `recall_questions` → `oa_questions` → `sources`, plus the `seo` block.
Its research object already has everything you need, including the two verified sources
(Anthropic's multi-agent research system post and Cognition's "Don't Build Multi-Agents") —
the compound-error argument is the spine of this lesson, so use them.

Guard for the rest of the batch: `"kind": "engineering"` on every file, and run
`python content/validate.py` after EACH lesson, not just at batch end — this error would
have been caught in seconds instead of surfacing mid-review.
