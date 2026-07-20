# Agentic AI + MCP curriculum research — PORTABLE (paste into gemini.google.com, Deep Research mode preferred)

Self-contained research prompt for the **Agentic AI / MCP expansion of the ai-engineering
roadmap** (Trends evidence 2026-07-16/17: "ai agents" avg 47 and ~9x growth in 12mo;
"mcp server" avg 49 — now bigger than "langchain" at 40 — with young SERPs; "agentic ai"
+1,350% rising under "ai engineer roadmap"). No repo access needed — everything the model
must know is inline, including the 36 existing lessons it must NOT duplicate.

## How to use
1. Open Gemini (gemini.google.com), pick **Deep Research** if available (better
   sourcing of real production failure modes and JD evidence); plain chat with search
   also works.
2. Paste everything inside the `=== RESEARCH PROMPT ===` block.
3. The model first returns the PHASE MAP for approval; reply **approved** (or edit it),
   then it returns lessons in batches of 4 as JSON; reply **next** after each batch.
4. Concatenate all batch arrays into ONE array and save as
   `content/research/agentic-ai-curriculum.json`. Check it parses:
   `python -c "import json; json.load(open('content/research/agentic-ai-curriculum.json', encoding='utf-8'))"`
5. Hand the file to Claude — the lesson list + phase graph gets critiqued and hardened
   against it before Antigravity bulk-generates anything (same gate order as maths:
   research → contract → generation).

---

=== RESEARCH PROMPT ===

You are doing a deep-research pass for a learning app's **Agentic AI curriculum**
(autonomous LLM agents + the Model Context Protocol). You are NOT writing lessons. You
are producing the structured research that a curriculum architect and lesson authors
will build from: which lessons exist, what each must teach, what learners get wrong,
and which official docs are the source of truth. Accuracy beats volume — everything you
output steers content that real job-seekers will study, so an invented "best practice"
or a misattributed spec detail mis-teaches at scale.

CONTEXT — what your output feeds (so you know what matters):
- The app (RetainHQ) teaches developers with docs-as-truth lessons: every lesson is
  grounded in official documentation, uses predict-before-reveal moments (show code,
  ask "what happens?", then explain), and feeds spaced-repetition recall cards. Lessons
  are EVERGREEN CONCEPT lessons — frameworks appear only as application layers on
  stable concepts.
- The app already has a 36-lesson "AI Engineering" roadmap (list below). Your job is
  the AGENTIC expansion: what's missing, not what exists. Where a proposed lesson
  overlaps an existing one, say so explicitly — the author will extend the existing
  lesson instead of duplicating it.
- The audience is Indian CS students and early-career developers targeting AI
  engineering jobs. Interview and job-description relevance is a first-class signal:
  a lesson that never appears in a JD or interview should justify itself some other
  way (production necessity, prerequisite role).

THE EXISTING 36 LESSONS — do NOT propose duplicates of these (slugs):
ann-indexes-hnsw-ivf, caching-and-cost-control, chain-of-thought, chat-completions-api,
chunking-strategies, completion-vs-chat-models, context-injection-and-prompt-assembly,
context-window, cost-and-latency-budgeting, embed-and-retrieve-top-k, embeddings,
evaluation-and-test-sets, function-tool-calling, grounding-with-retrieval,
guardrails-and-validation, hallucination-mitigation, memory-short-and-long-term,
metadata-filtering, multi-step-planning, observability-traces-logging,
output-formatting-and-delimiters, pgvector-pinecone-chroma, prompt-injection,
rag-evaluation, rate-limits-and-retries, react-reason-act, reranking,
similarity-metrics, streaming-responses, structured-output-json-mode,
system-prompts-and-guardrails, system-user-assistant-roles, temperature-and-top-p,
tokens-and-tokenization, tool-use-and-the-call-loop, zero-shot-vs-few-shot

Note what this means: ReAct, basic planning, single-tool call loops, function calling,
and basic memory ALREADY EXIST. The agentic expansion starts where those end: the
protocol layer (MCP), multi-agent orchestration, agent-specific reliability/evals/
security, and production agent operations.

GROUND TO COVER — organize into 4-6 phases, ~22-30 lessons total. This list is the
starting hypothesis; your research should correct it (add what production/JD evidence
demands, cut what nothing demands):

A. MCP — the Model Context Protocol (target 6-9 lessons; this is the priority phase:
   search demand for "mcp server" now exceeds "langchain" and no education site owns
   the topic yet):
   why a protocol (M×N integration problem), architecture (hosts/clients/servers),
   the three primitives (tools, resources, prompts), transports (stdio, streamable
   HTTP), building a server (Python SDK / FastMCP), consuming from a client,
   sampling & elicitation, MCP security (tool poisoning, confused deputy, consent
   model), MCP vs plain function calling (when the protocol earns its complexity).

B. Agent architectures & orchestration (5-8 lessons):
   what makes something an agent (autonomy spectrum: workflow → router → agent),
   single-agent loops in production (beyond the existing ReAct lesson), multi-agent
   patterns (orchestrator-worker, handoffs, when multi-agent is WORSE), graph-based
   orchestration concepts (state machines, checkpointing — LangGraph as the
   application layer), human-in-the-loop gates, durable execution / resumability,
   context engineering for agents (compaction, sub-agent isolation — extends the
   existing context-window lesson).

C. Agent reliability & evaluation (4-6 lessons):
   why agent evals differ from RAG/LLM evals (trajectory vs outcome), eval harnesses
   for multi-step tasks, guarding against loops/runaways (step budgets, cost caps),
   sandboxing & permissioning tool execution, failure taxonomy of production agents
   (real documented incidents preferred), observability for agents (extends the
   existing observability lesson — traces of tool calls, not just LLM calls).

D. Agent security (3-4 lessons; extends the existing prompt-injection lesson):
   indirect prompt injection via tool results/browsed content, tool poisoning &
   rug-pulls in MCP servers, excessive agency / least-privilege design, data
   exfiltration paths ("lethal trifecta": private data + untrusted content +
   external communication).

E. Agent memory & state (2-3 lessons; extends memory-short-and-long-term):
   agent-specific memory architectures (scratchpads, episodic vs semantic,
   memory-as-tools), state persistence across sessions.

FRAMEWORK POLICY (critical — bakes in evergreen-vs-churn discipline):
- Concepts are framework-agnostic. A lesson named after a framework is allowed ONLY
  where the framework IS the topic's search demand (LangGraph qualifies: avg 23 vs
  CrewAI 8, OpenAI Agents SDK 6 in Trends; nothing else currently does).
- For each lesson, name which framework(s) illustrate it best TODAY and rate the
  churn risk: would this lesson still be correct if that framework renamed its API
  next quarter? The concept must survive; only code snippets may rot.
- Viral tools of the moment (e.g. OpenClaw/Moltbook-type breakouts) are trend
  EVIDENCE, never lesson topics.

OUTPUT SHAPE — first the phase map (for approval), then one JSON object per lesson:

{
  "slug": "mcp-tools-resources-prompts",
  "title": "MCP primitives: tools, resources, and prompts",
  "phase": "Model Context Protocol",
  "why_now": "one sentence: the demand/JD/production evidence for this lesson existing",
  "core_questions": [
    "3-5 questions the lesson must answer — phrased as a learner would ask them"
  ],
  "docs_truth": [
    { "url": "https://modelcontextprotocol.io/...", "which_sections": "what specifically to ground in", "authority": "spec | official-sdk-docs | vendor-docs | none-exists" }
  ],
  "misconceptions": [
    {
      "id": "mcp-is-just-function-calling",
      "wrong_belief": "the concrete wrong mental model, stated as the learner holds it",
      "why_learners_hold_it": "where this belief comes from",
      "reality": "the correct model, 1-3 plain sentences",
      "predict_moment": "a concrete code/config situation where the wrong belief gives a wrong prediction — this becomes the lesson's predict-before-reveal"
    }
  ],
  "code_moment": "the minimal Python (or config) example that makes the concept land — describe it, don't write it",
  "seo": {
    "primary_phrase": "the exact search phrasing to target (verify real phrasing, not invented)",
    "alternates": ["other real phrasings"],
    "serp_note": "who ranks today and whether the SERP is winnable (official docs only? blog spam? unclaimed?)"
  },
  "prereqs": ["slugs — existing-roadmap slugs allowed and encouraged"],
  "overlaps_existing": "existing slug this extends, or null",
  "churn_risk": { "level": "low | medium | high", "what_could_change": "the specific API/spec surface at risk" },
  "interview_signals": ["real interview questions or JD requirement lines this lesson maps to, with source"]
}

FIELD RULES:
1. misconceptions: 2-5 per lesson, and they are the heart of this pass. Source them
   from real evidence: GitHub issues on the official SDKs, Stack Overflow questions,
   documented production post-mortems, official docs' own "common pitfalls" sections,
   security research (e.g. published MCP tool-poisoning research). NEVER invent one.
   If you cannot source it beyond intuition, mark the id with suffix "-unsourced" so
   the reviewer can judge it.
2. docs_truth: the spec/official docs are the ONLY acceptable primary grounding. If a
   topic has no authoritative doc (some multi-agent patterns don't), say
   "authority": "none-exists" and name the 2-3 most-cited practitioner sources
   instead — the lesson author needs to know they are on softer ground.
3. seo.primary_phrase must be a REAL phrasing people search (check autocomplete-style
   phrasings, docs titles, question sites) — not a phrase you composed. The SERP note
   is load-bearing: "official spec + nothing else" means high-priority lesson;
   "OpenAI's own guide ranks #1-3" means target the long-tail alternate instead.
4. interview_signals: quote or closely paraphrase real JD lines / interview questions
   (2024-2026), name where seen (company careers page, interview-prep sites). If a
   lesson has none, write [] and justify the lesson in why_now on production grounds.
5. prereqs must form a DAG with the existing 36 slugs as available roots. No cycles,
   fan-in ≤ 4 per lesson.
6. These topics MUST appear somewhere (they are documented, high-evidence, and
   currently missing from most curricula): MCP tool poisoning; the M×N integration
   argument for protocols; trajectory-vs-outcome agent evals; step/cost budget
   runaway protection; indirect prompt injection through tool results; when
   multi-agent architectures UNDERPERFORM single agents (documented evidence exists);
   checkpointing/resumability; least-privilege tool permissioning.

PROCESS:
- Research first, then emit. Every docs_truth URL must be real and current — verify it
  resolves; a hallucinated URL poisons the whole pipeline.
- STEP 1: emit the phase map only — phases in order, each with its lesson slugs +
  one-line scope, plus a short list of what you CUT from my ground-to-cover hypothesis
  and why. Wait for "approved".
- STEP 2: emit lessons in batches of 4 as a JSON array (one fenced JSON block per
  batch). I reply "next" for each following batch until done.
- Where the evidence contradicts my hypothesis (a phase is too big, a topic has no
  demand, something major is missing — e.g. computer-use agents, A2A-style
  inter-agent protocols), SAY SO in the phase map. The hypothesis is a starting
  point, not a constraint.

=== END RESEARCH PROMPT ===
