# AI Engineering lesson generation — PROMPT (engineering: LLMs / RAG / Agents)

> **North star (same as the rest):** *"Can the learner explain AND build this in an interview 30 days later?"*
> AI Engineering is **applied** — concepts that only make sense when you see the code that runs them.
> So this `kind` is **theory + REAL CODE**: teach the idea from scratch (like Core CS theory), then
> show the actual code a learner would write. The code is **illustrative, not executed in-browser**
> (it calls an LLM / network), so it doesn't need to run — it needs to be *correct and readable*.
> Retention is the engine's job; the lesson is the hook. Do NOT write framework docs — write the
> version that makes RAG / tool-calling / embeddings *click* and leaves the learner able to draw it.

You generate **one JSON per node** for the `ai-engineering` roadmap, `kind: "engineering"`. Topics +
slugs are in `content/_TODO-engineering.md`. Validate with `python content/validate.py` (engineering
branch). Write to `content/roadmaps/ai-engineering/<slug>.json` (filename = slug).

**Gold reference (copy its shape + depth):** `content/roadmaps/ai-engineering/embed-and-retrieve-top-k.json`.

---

## THE TEMPLATE (field order = teaching order)
| # | Field | Required? | What it is |
|---|---|---|---|
| 1 | `hook` | optional | A concrete scene where this bites — a bot hallucinating, a $4k token bill, a prompt-injection leak. `scenario` + optional `question`. Skip if forced. |
| 2 | `mental_model` | **REQUIRED** | The **analogy** that makes it click. *"RAG is an open-book exam." "An embedding is a GPS coordinate for meaning." "An agent is a worker with a toolbox who keeps asking 'am I done yet?'"* `intuition` = one-liner; `description` = expand it. |
| 3 | `sections` | **PREFERRED** (use instead of `explanation`) | The **born-visual layout: small idea → visual → checkpoint.** An ordered list of blocks `[{body, image?, animation?, recap?}]`. Each `body` is ONE ~50–70-word idea; `recap` is a one-line "so far" checkpoint; `image`/`animation` (optional) sit between ideas. This is how we beat the "wall of text" — chunk the teach, put a visual where it earns its place. Schema below. **Author `sections` for new lessons.** |
| 3b | `explanation` | fallback (use ONLY if you skip `sections`) | A monolithic TEACH-from-scratch string, 4–6 blank-line-separated paragraphs. Older lessons use this; new ones should prefer `sections`. Exactly one of `explanation` / `sections` is required. |
| 4 | `code_snippets` | **REQUIRED, ≥1 (usually 2–3)** | Real, readable code that maps to the teaching. `[{title, language, code, explanation}]`. This is what separates `engineering` from `theory` — see rules below. |
| 5 | `illustration` | optional | A single hero image right after the mental model: `{asset, alt}`. Use for one strong intuition picture; for images *between* ideas use a section's `image` instead. `asset` = the bucket key from `_TODO-images.md`. |
| 6 | `animation` | **optional — PROCESS or GEOMETRY** | A structured animated diagram (NOT a video). `sequence`/`cycle` for *processes* (RAG pipeline, agent loop, tool round-trip); **`vector-space`** for the embeddings/RAG *geometry* (clusters + query landing + top-k). Lives top-level OR inside a section. SKIP for static concepts. Schema below. |
| 6 | `key_points` | optional | The component breakdown as `[{title, detail}]` — e.g. the 3 RAG phases; the tool-calling round-trip steps; cosine vs dot vs euclidean. Use when the concept HAS discrete parts. |
| — | `common_mistakes` | **REQUIRED, ≥1** | The classic misconception/bug — *"more chunks = better"; "JSON mode guarantees valid schema"; "temperature 0 is fully deterministic"; "the model runs your tool for you."* |
| 7 | `recall_questions` | **REQUIRED, ≥3** | What an interviewer asks. tier1 = state it, tier2 = apply/debug. Feeds the review engine. |
| 8 | `oa_questions` | **REQUIRED, ≥2** | Real GenAI interview questions (RAG debugging, "explain temperature vs top-p", "how do you stop prompt injection") with `company` + `answer` + `approach`. |

**No `code_walkthrough` (that's the runnable `concept` kind), no `formula`, no `method`, no `understanding_checks`.**

---

## `code_snippets` — the rules (this is the whole point)
- **Real and runnable-in-principle.** Use the real APIs: `openai` / `anthropic` SDK, `pgvector`, plain
  `numpy`. No pseudo-code, no `...magic()...`. A learner should be able to paste it into a file and,
  with a key, have it work.
- **Small and focused.** ~5–20 lines each. One idea per snippet. Build up: snippet 1 = the simplest
  call, snippet 2 = the realistic version, snippet 3 = the production shortcut (e.g. "let the vector DB
  do the search"). Mirror the gold reference.
- **`language`** is a lowercase hint for the chip: `python` | `bash` | `json` | `sql` | `text`.
- **`code`** is a JSON string — escape newlines as `\n`, use 4-space indents, keep inline `# comments`
  that teach. **Use single quotes inside the code where possible** so they nest cleanly in JSON.
- **`explanation`** (1–3 sentences) sits under the block and says what to NOTICE — the invariant, the
  gotcha, why this line matters. Not a restatement of the code.
- These are **not executed** by the app (no Pyodide) — so correctness is on you, the author. Don't ship
  code you wouldn't run.

## `sections` — the born-visual layout (PREFER THIS over `explanation`)
Break the teach into ordered blocks, each ONE small idea, with visuals and checkpoints between. This is
the fix for "feels like a blog post." 4–7 blocks; each `body` ~50–70 words; add a `recap` (one-line "so
far") on most; drop an `image` or `animation` into the 1–2 blocks where a visual genuinely helps.
```json
"sections": [
  { "body": "<~60-word idea>", "recap": "So far: <one-line checkpoint>" },
  { "body": "<next idea>", "image": { "asset": "ai-engineering/<slug>/<id>.png", "alt": "<what it shows>" }, "recap": "..." },
  { "body": "<idea the animation illustrates>", "animation": { "type": "vector-space", "...": "..." }, "recap": "..." }
]
```
Rules: every block needs a non-empty `body`; `image`/`animation`/`recap` are optional per block; the LAST
recap should be the **pipeline-recap / where-this-fits** line. Total teaching across blocks must still be
complete (a beginner could learn it) — chunking is about *rhythm*, not *cutting depth*.
Reference: `content/roadmaps/ai-engineering/embed-and-retrieve-top-k.json`.

## `image` / `illustration` — generated stills (optional)
Images are generated separately (see `content/PROMPT-images.md` + `content/_TODO-images.md`) and stored in
Supabase. In the lesson you reference ONLY the key + alt: `{ "asset": "ai-engineering/<slug>/<id>.png",
"alt": "..." }` — as a section's `image` (preferred, sits between ideas) or top-level `illustration` (a
hero). Use the EXACT filename from `_TODO-images.md`. If the image isn't uploaded yet the slot renders
nothing (no broken image), so it's safe to reference ahead of generation. Only reference an image that is
(or will be) on the worklist — don't invent assets.

## `animation` — PROCESS (`sequence`/`cycle`) or GEOMETRY (`vector-space`) (optional)
Structured data, not a video. Lives top-level or inside a section.

**`sequence`/`cycle`** — `actors` (boxes) + directed `steps` (`from`→`to`), each a plain `label` + optional
`term`. `sequence` = a pipeline/round-trip; `cycle` = a true loop (the agent reason→act→observe loop).
```json
"animation": {
  "type": "sequence",
  "actors": [ { "id": "model", "label": "Model" }, { "id": "tool", "label": "Tool" } ],
  "steps": [
    { "from": "model", "to": "tool", "label": "calls with arguments", "term": "tool call" },
    { "from": "tool", "to": "model", "label": "returns a result", "term": "observation" }
  ]
}
```
Rules: 2–6 actors; every `from`/`to` is an actor `id`; 3–5 steps; author only for true processes.

**`vector-space`** — the embeddings/RAG geometry (clusters of chunks + the query landing nearest one + the
top-k lighting up). Use it for embeddings/retrieval/similarity nodes; it shows "how retrieval works" in a
way the box-flow can't.
```json
"animation": {
  "type": "vector-space",
  "clusters": [
    { "label": "Password", "color": "teal" },
    { "label": "Billing", "color": "amber" },
    { "label": "API docs", "color": "cyan" }
  ],
  "query": { "label": "reset my password", "near": "Password" },
  "k": 3
}
```
Rules: 2–4 `clusters` each with a `label` (optional `color`: cyan|teal|violet|amber); `query.near` MUST be
one of the cluster labels; `k` is a positive int. The renderer animates the query landing near that cluster
and highlights the `k` nearest dots.

## Topic notes (AI Engineering)
- **Use real, current APIs (2025–2026):** `text-embedding-3-small/large`, `gpt-4o`/`gpt-4o-mini` or
  Claude; the `client.chat.completions.create` / `client.messages.create` shapes; `pgvector`'s `<=>`
  operator; tool/function-calling JSON. Don't invent endpoints.
- **Same-model invariant, token economics, "nearest ≠ correct", prompt injection** are the high-value
  ideas interviewers probe — give them their own crisp lesson treatment where the node calls for it.
- **Production AI nodes** (eval, hallucination, injection, caching, observability) are conceptual but
  still show code where there's a concrete pattern (a cache key, an eval harness skeleton, a delimiter
  guardrail). If there's genuinely no code, this node may fit `theory` better — flag it, don't fake it.
- **`company` tags = honest categories** — `GenAI Engineer interview`, `LLM Engineer OA`, `RAG system
  design`, `ZS Associates` (only where the run-2 research actually cited it). Never fabricate a company.
- **`sources` = docs-as-truth:** link the real provider/library docs (platform.openai.com, docs.
  anthropic.com, github.com/pgvector, python.langchain.com), not blog spam.

## Teaching order & retention (make the invisible visible)
These rules came out of reviewing the gold reference — they apply to EVERY lesson:
- **Lead with the picture, not the mechanism.** Open the first `sections` block with the analogy/geometry
  made concrete (dots clustering in space; an agent's reason→act loop), THEN introduce the machinery.
- **Chunk it (use `sections`).** Each block = one ~60-word idea + a `recap` checkpoint; put a visual where
  it earns its place. This rhythm — small idea → visual → checkpoint — is the whole point; don't ship a
  6-paragraph `explanation` wall when `sections` will carry it.
- **Delay the math/formula.** Describe the intuition first (e.g. "arrows pointing the same way = similar
  meaning"), name the precise metric/formula second. The learner should never need the formula to grasp
  the idea. Cut low-level asides (bit-twiddling, "it's just multiply-and-add") — they don't earn tier-1 space.
- **Show the naive-vs-real contrast.** Where the concept has a "why not just do the obvious thing?" moment,
  show it: keyword search vs semantic search; brute-force scan vs ANN index; string-concat prompt vs
  structured messages. The contrast is where the *why* lives.
- **One surprising insight per lesson.** End on the counterintuitive line that sticks — *"the vector store
  never understands English, it only compares numbers"*; *"the model doesn't run your tool, it just asks
  you to."* This is the retention hook.
- **Close with a one-line pipeline recap** that places this node in the bigger flow (*"Docs → Chunk →
  Embed → Store … this lesson is the Embed → Retrieve hinge"*). It cements where the piece fits.
- **Don't over-teach a neighbour's node.** Motivate and link (ANN gets its own node — here you just say
  *why* a vector DB exists), don't duplicate it.
- **Render order is fixed by the engine:** hook → mental_model → illustration → sections (or
  animation+explanation) → key_points → code → common_mistakes → recall → oa. Code sits right after the
  teach (so the `common_mistakes`, usually *about the code*, land with it fresh). Write to that order.

## Quality bar (self-sufficiency is the gate)
- **Could a learner answer EVERY one of your `oa_questions` using only what THIS lesson teaches plus its
  listed prerequisites?** If an OA needs a concept you never taught, either teach it or cut the question.
- Does `mental_model` make it feel **obvious**? Generic analogies ("it's like a database") fail — sharpen.
- Is the teach (across `sections`, or the `explanation`) a real **teach-from-scratch**, not a summary?
  Chunking into `sections` must not thin the depth — a beginner should still learn it fully. (engineering ≠ thin aptitude.)
- Does every `code_snippet` use **real APIs** and carry a **teaching** explanation, not a restatement?
- Does every `section` have a `recap`-worthy single idea, and does the LAST recap place the node in the bigger pipeline?
- Reference only images that are on `_TODO-images.md` (exact filename); never invent an `asset` key.
- Single quotes inside strings so they nest in JSON.
