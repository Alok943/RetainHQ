"""
Seed script: AI Engineering roadmap.

Sub-tracks (phase = step spine): LLM Foundations · LLM APIs · Prompt Engineering ·
RAG · Vector Databases · Agents · Production AI.

The differentiator skillset — building real LLM applications.

Idempotent. Run: ./.venv/Scripts/python.exe seed_ai_engineering.py
"""
import asyncio
import uuid
from sqlalchemy import text
from app.core.database import engine

ROADMAP_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
SLUG = "ai-engineering"  # content folder key + URL id; matches content/roadmaps/ai-engineering/
TITLE = "AI Engineering — LLMs, RAG & Agents"
DESCRIPTION = "Building real LLM applications: APIs, prompting, retrieval-augmented generation, vector search and agents — plus what it takes to run them in production."

NODES = [
    # ---------------- LLM Foundations ----------------
    ("LLM Foundations", "Mechanics", "Tokens & tokenization", "easy", "Text → tokens; limits & billing are per token."),
    ("LLM Foundations", "Mechanics", "Context window", "easy", "Max tokens (in + out); overflow gets truncated."),
    ("LLM Foundations", "Sampling", "Temperature & top-p", "easy", "Randomness vs determinism in outputs."),
    ("LLM Foundations", "Representation", "Embeddings", "medium", "Text → vector capturing meaning; basis of search."),
    ("LLM Foundations", "Chat", "System / user / assistant roles", "easy", "Message roles shape behaviour."),
    ("LLM Foundations", "Models", "Completion vs chat models", "easy", "Chat models take a message list."),

    # ---------------- LLM APIs ----------------
    ("LLM APIs", "Calls", "Chat completions API", "easy", "messages[], model, params → response."),
    ("LLM APIs", "Calls", "Streaming responses", "medium", "Token-by-token; cuts perceived latency."),
    ("LLM APIs", "Tools", "Function / tool calling", "hard", "Model returns a structured call to run."),
    ("LLM APIs", "Output", "Structured output (JSON mode)", "medium", "Force valid JSON; validate with Pydantic."),
    ("LLM APIs", "Ops", "Cost & latency budgeting", "medium", "tokens × price; pick the smallest model that works."),
    ("LLM APIs", "Ops", "Rate limits & retries", "medium", "Backoff and handle 429s."),

    # ---------------- Prompt Engineering ----------------
    ("Prompt Engineering", "Patterns", "Zero-shot vs few-shot", "easy", "Examples in the prompt steer output."),
    ("Prompt Engineering", "Patterns", "Chain-of-thought", "medium", "Ask for step-by-step reasoning."),
    ("Prompt Engineering", "Control", "System prompts & guardrails", "medium", "Set role, rules and boundaries."),
    ("Prompt Engineering", "Control", "Output formatting & delimiters", "easy", "Delimit inputs; specify exact format."),

    # ---------------- RAG ----------------
    ("RAG", "Why", "Grounding with retrieval", "easy", "Feed real facts; cut hallucination."),
    ("RAG", "Ingest", "Chunking strategies", "medium", "Size & overlap; semantic vs fixed splits."),
    ("RAG", "Retrieve", "Embed & retrieve top-k", "medium", "Embed query, fetch nearest chunks."),
    ("RAG", "Retrieve", "Reranking", "hard", "Reorder retrieved chunks by true relevance."),
    ("RAG", "Assemble", "Context injection & prompt assembly", "medium", "Stuff retrieved context into the prompt."),
    ("RAG", "Quality", "RAG evaluation", "hard", "Faithfulness, relevance, retrieval recall."),

    # ---------------- Vector Databases ----------------
    ("Vector Databases", "Search", "Similarity metrics", "medium", "Cosine, dot product, euclidean."),
    ("Vector Databases", "Index", "ANN indexes (HNSW / IVF)", "hard", "Approximate nearest-neighbour for speed."),
    ("Vector Databases", "Options", "pgvector / Pinecone / Chroma", "easy", "pgvector lives inside Postgres."),
    ("Vector Databases", "Search", "Metadata filtering", "medium", "Combine filters with vector search."),

    # ---------------- Agents ----------------
    ("Agents", "Core", "Tool use & the call loop", "hard", "Model → tool → result → model, repeat."),
    ("Agents", "Patterns", "ReAct (reason + act)", "hard", "Interleave reasoning and actions."),
    ("Agents", "State", "Memory (short & long term)", "medium", "Carry context across steps/sessions."),
    ("Agents", "Planning", "Multi-step planning", "hard", "Decompose a goal into steps."),
    ("Agents", "Safety", "Guardrails & validation", "medium", "Constrain and check agent actions."),

    # ---------------- Production AI ----------------
    ("Production AI", "Quality", "Evaluation & test sets", "hard", "Measure quality; catch regressions."),
    ("Production AI", "Quality", "Hallucination mitigation", "medium", "Grounding, citations, allow refusal."),
    ("Production AI", "Security", "Prompt injection", "hard", "Untrusted input can hijack the prompt."),
    ("Production AI", "Ops", "Caching & cost control", "medium", "Cache responses/embeddings."),
    ("Production AI", "Ops", "Observability (traces, logging)", "medium", "Trace prompts, tokens, latency, cost."),

    # ---------------- Agentic expansion (2026-07-17) ----------------
    # 26 nodes from the research-gated curriculum content/research/agentic-ai-curriculum.json
    # (Trends-validated: "ai agents" ~9x/12mo; "mcp server" out-sizes "langchain").
    # Node titles slugify EXACTLY to the lesson slugs in that file — do not reword titles
    # without renaming the lesson file (the frontend matches node->lesson by slugified title).

    # ---------------- Model Context Protocol ----------------
    ("Model Context Protocol", "Why a protocol", "MCP integration problem", "easy", "Custom glue per app x tool scales MxN; one shared protocol makes it M+N."),
    ("Model Context Protocol", "Architecture", "MCP architecture: hosts, clients, servers", "medium", "Host app owns clients; each client holds a 1:1 connection to one server."),
    ("Model Context Protocol", "Architecture", "MCP tools, resources & prompts", "medium", "Tools = model-controlled, resources = application-controlled, prompts = user-controlled."),
    ("Model Context Protocol", "Transports", "MCP transports: stdio & HTTP", "medium", "Local servers are subprocesses speaking JSON-RPC over stdio; remote ones use Streamable HTTP."),
    ("Model Context Protocol", "Build", "MCP: FastMCP server building", "medium", "Type hints + docstrings auto-generate each tool's JSON Schema."),
    ("Model Context Protocol", "Advanced", "MCP sampling and elicitation", "hard", "Servers can request completions (sampling) and user input (elicitation) back through the client."),
    ("Model Context Protocol", "Judgment", "MCP vs function calling", "medium", "The protocol earns its overhead at many-tools x many-apps scale, not for one script."),
    ("Model Context Protocol", "Ops", "MCP observability and logging", "medium", "stdio servers must log to stderr - stdout belongs to the protocol."),

    # ---------------- Agent Architectures & Orchestration ----------------
    ("Agent Architectures", "Foundations", "Agent autonomy spectrum", "easy", "Fixed pipeline = workflow; conditional branch = router; model-directed loop = agent."),
    ("Agent Architectures", "State", "State machines for agents", "medium", "Graph nodes update shared typed state via reducers - append, don't overwrite."),
    ("Agent Architectures", "Multi-agent", "Multi-agent orchestration patterns", "medium", "Supervisor routes; workers execute; a handoff must transfer control AND context."),
    ("Agent Architectures", "Multi-agent", "When multi-agent underperforms", "medium", "Errors compound across handoffs - a single well-structured agent often wins."),
    ("Agent Architectures", "Durability", "Agent checkpointing and resumability", "hard", "Persist state at each step so long tasks pause and resume instead of restarting."),
    ("Agent Architectures", "Durability", "Human-in-the-loop interrupts", "medium", "A durable interrupt checkpoints and exits - it is not input() blocking a thread."),

    # ---------------- Agent Reliability & Evaluation ----------------
    ("Agent Reliability", "Metrics", "Agent trajectory vs outcome evals", "medium", "Score the path as well as the result; pass^k (every time), not pass@k (at least once)."),
    ("Agent Reliability", "Harnesses", "Agent eval harnesses and scoring", "hard", "Deterministic graders verify the end state; LLM-as-judge scores the trajectory."),
    ("Agent Reliability", "Harnesses", "Agent trace normalization for evals", "hard", "Canonicalize noisy multi-step traces before a judge scores them."),
    ("Agent Reliability", "Failure modes", "Agent failure taxonomy", "medium", "Name the failure class first: wrong tool, hallucinated args, context loss, loop, bad handoff."),
    ("Agent Reliability", "Safeguards", "Runaway agent protection", "medium", "Step budgets and cost caps at the orchestrator; max_tokens does not bound a loop."),

    # ---------------- Agent Security ----------------
    ("Agent Security", "Injection", "Indirect prompt injection: tool results", "medium", "Untrusted content returned by tools reads as instructions - the lethal trifecta."),
    ("Agent Security", "MCP threats", "MCP tool poisoning", "medium", "A server can change tool descriptions after approval (rug-pull); pin and re-review."),
    ("Agent Security", "MCP threats", "MCP confused deputy attacks", "hard", "A privileged server tricked into misusing its credentials for an attacker."),
    ("Agent Security", "Containment", "Agent least privilege and consent", "medium", "Grant each tool minimum scope; enforce at the execution layer, not in the prompt."),
    ("Agent Security", "Containment", "Agent tool execution sandboxing", "hard", "Isolate filesystem AND network - one without the other still exfiltrates."),

    # ---------------- Agent Memory & State ----------------
    ("Agent Memory", "Context", "Agent state pruning and compaction", "medium", "Don't replay the full scratchpad every turn - prune ephemeral state, compact the rest."),
    ("Agent Memory", "Memory", "Agent memory as tools", "medium", "Episodic vs semantic memory; the agent retrieves memory via tool calls, not passive injection."),
]


async def main():
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM roadmap_nodes WHERE roadmap_id = :rid"), {"rid": str(ROADMAP_ID)})
        await conn.execute(text("DELETE FROM roadmaps WHERE id = :rid"), {"rid": str(ROADMAP_ID)})
        await conn.execute(
            text("INSERT INTO roadmaps (id, slug, title, description, created_at) VALUES (:id, :slug, :title, :desc, now())"),
            {"id": str(ROADMAP_ID), "slug": SLUG, "title": TITLE, "desc": DESCRIPTION},
        )
        for i, (phase, section, title, tier, desc) in enumerate(NODES):
            await conn.execute(
                text("INSERT INTO roadmap_nodes "
                     "(id, roadmap_id, phase, section, title, tier, order_index, description) "
                     "VALUES (:id, :rid, :phase, :section, :title, :tier, :idx, :desc)"),
                {"id": str(uuid.uuid4()), "rid": str(ROADMAP_ID), "phase": phase,
                 "section": section, "title": title, "tier": tier, "idx": i, "desc": desc},
            )
    print(f"Seeded '{TITLE}' with {len(NODES)} nodes.")


if __name__ == "__main__":
    asyncio.run(main())
