# AI Engineering content — TODO (kind: "engineering")

Roadmap: `ai-engineering` · 35 nodes · seed: `backend/seed_ai_engineering.py`
Contract: `content/PROMPT-engineering.md` · Gold reference: `embed-and-retrieve-top-k.json` (DONE ✅)

**Slugs below = `slugify(node title)`** — they MUST match exactly, or the roadmap's "Learn" button
won't appear on that node (the frontend matches node→lesson by slugified title). Filename = slug.

**Author lessons born-visual:** use the `sections` layout (small idea → visual → checkpoint), not a
monolithic `explanation`. Drop a `vector-space` animation into embeddings/retrieval/similarity nodes, and
reference generated stills by the exact filenames in `content/_TODO-images.md` (the slot renders nothing
until the image is uploaded, so referencing ahead is safe). See the updated `content/PROMPT-engineering.md`.

Validate after each batch: `python content/validate.py` (must end `All content valid. [OK]`).

---

## LLM Foundations (6)
- [ ] `tokens-and-tokenization` — Tokens & tokenization · easy · *prereq: —* · the unit of billing + limits
- [ ] `context-window` — Context window · easy · *prereq: tokens-and-tokenization*
- [ ] `temperature-and-top-p` — Temperature & top-p · easy · *prereq: tokens-and-tokenization* · the "temp 0 ≠ fully deterministic" gotcha
- [ ] `embeddings` — Embeddings · medium · *prereq: tokens-and-tokenization* · unlocks the whole RAG/vector track
- [ ] `system-user-assistant-roles` — System / user / assistant roles · easy · *prereq: —*
- [ ] `completion-vs-chat-models` — Completion vs chat models · easy · *prereq: system-user-assistant-roles*

## LLM APIs (6)
- [ ] `chat-completions-api` — Chat completions API · easy · *prereq: completion-vs-chat-models* · the canonical `messages[]` call
- [ ] `streaming-responses` — Streaming responses · medium · *prereq: chat-completions-api* · animation candidate (token-by-token)
- [ ] `function-tool-calling` — Function / tool calling · hard · *prereq: structured-output-json-mode* · animation: model→tool→result→model. The "model does NOT run your tool" mistake.
- [ ] `structured-output-json-mode` — Structured output (JSON mode) · medium · *prereq: chat-completions-api* · validate with Pydantic; "JSON mode ≠ schema-valid" gotcha
- [ ] `cost-and-latency-budgeting` — Cost & latency budgeting · medium · *prereq: tokens-and-tokenization* · tokens × price; smallest model that works
- [ ] `rate-limits-and-retries` — Rate limits & retries · medium · *prereq: chat-completions-api* · 429 backoff; show the retry code

## Prompt Engineering (4)
- [ ] `zero-shot-vs-few-shot` — Zero-shot vs few-shot · easy · *prereq: chat-completions-api*
- [ ] `chain-of-thought` — Chain-of-thought · medium · *prereq: zero-shot-vs-few-shot*
- [ ] `system-prompts-and-guardrails` — System prompts & guardrails · medium · *prereq: system-user-assistant-roles*
- [ ] `output-formatting-and-delimiters` — Output formatting & delimiters · easy · *prereq: zero-shot-vs-few-shot* · delimiting untrusted input (ties to prompt-injection)

## RAG (6)
- [ ] `grounding-with-retrieval` — Grounding with retrieval · easy · *prereq: embeddings* · the "open-book exam" why-RAG lesson; animation candidate (full pipeline)
- [ ] `chunking-strategies` — Chunking strategies · medium · *prereq: grounding-with-retrieval* · size/overlap, semantic vs fixed
- [x] `embed-and-retrieve-top-k` — Embed & retrieve top-k · medium · **DONE ✅ (gold reference)**
- [ ] `reranking` — Reranking · hard · *prereq: embed-and-retrieve-top-k* · "nearest ≠ relevant" → reorder
- [ ] `context-injection-and-prompt-assembly` — Context injection & prompt assembly · medium · *prereq: embed-and-retrieve-top-k*
- [ ] `rag-evaluation` — RAG evaluation · hard · *prereq: context-injection-and-prompt-assembly* · faithfulness, relevance, retrieval recall

## Vector Databases (4)
- [ ] `similarity-metrics` — Similarity metrics · medium · *prereq: embeddings* · cosine vs dot vs euclidean
- [ ] `ann-indexes-hnsw-ivf` — ANN indexes (HNSW / IVF) · hard · *prereq: similarity-metrics* · approximate NN for speed; animation optional
- [ ] `pgvector-pinecone-chroma` — pgvector / Pinecone / Chroma · easy · *prereq: similarity-metrics* · pgvector lives inside Postgres
- [ ] `metadata-filtering` — Metadata filtering · medium · *prereq: embed-and-retrieve-top-k* · combine filters with vector search

## Agents (5)
- [ ] `tool-use-and-the-call-loop` — Tool use & the call loop · hard · *prereq: function-tool-calling* · animation: cycle (model→tool→observe→model)
- [ ] `react-reason-act` — ReAct (reason + act) · hard · *prereq: tool-use-and-the-call-loop*
- [ ] `memory-short-and-long-term` — Memory (short & long term) · medium · *prereq: tool-use-and-the-call-loop*
- [ ] `multi-step-planning` — Multi-step planning · hard · *prereq: react-reason-act*
- [ ] `guardrails-and-validation` — Guardrails & validation · medium · *prereq: tool-use-and-the-call-loop*

## Production AI (5)
- [ ] `evaluation-and-test-sets` — Evaluation & test sets · hard · *prereq: rag-evaluation* · eval harness skeleton
- [ ] `hallucination-mitigation` — Hallucination mitigation · medium · *prereq: grounding-with-retrieval* · grounding, citations, allow-refusal
- [ ] `prompt-injection` — Prompt injection · hard · *prereq: output-formatting-and-delimiters* · untrusted input hijacks the prompt; high interview value
- [ ] `caching-and-cost-control` — Caching & cost control · medium · *prereq: cost-and-latency-budgeting* · cache responses/embeddings
- [ ] `observability-traces-logging` — Observability (traces, logging) · medium · *prereq: cost-and-latency-budgeting*

---

## Notes for the generator
- **Order matters for prereqs:** do LLM Foundations first (esp. `embeddings`), then APIs, then the rest.
  Prereq slugs that don't exist yet only produce a *warning*, not a failure — fine while generating.
- **`embeddings` is load-bearing** — the whole RAG + Vector DB track lists it as an ancestor. Make it strong.
- **Animation candidates** (use `sequence`, or `cycle` for the agent loop): grounding-with-retrieval,
  function-tool-calling, tool-use-and-the-call-loop, streaming-responses. Skip animation elsewhere.
- After generating, run validate, then the frontend `predev`/`prebuild` sync copies to `public/` and
  refreshes the sitemap automatically.
