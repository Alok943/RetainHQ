"""
Seed script: MLOps roadmap.

Sub-tracks (phase = step spine): Foundations · Serving & Features · Deploy & Optimize ·
Monitoring & Rollout.

Node list = the validated node-derivation research run (Gemini Deep Research, 2026-07-04;
ML Engineer / MLOps Engineer, India metros, 0-4yr incl. DS->production). Audit trail + excluded
list + mock-interview validation in content/research/mlops/nodes.md. Evidence-driven and modern:
covers LLM-serving (prefix caching, dynamic batching, quantization), feature stores, drift
monitoring, and canary/shadow/blue-green deploys — the DS->MLE engineering-depth gate (Career
Paths ds-mle). Replaced the earlier hand-drafted MLOps node list.

Tier mix intentionally spans easy->hard (10 hard nodes: feature time-travel, serverless inference,
quantization, compilation, prefix caching, dynamic batching, covariate/concept drift, cold-start,
PII scrubbing) — NOT beginner-only.

Idempotent. Run: ./.venv/Scripts/python.exe seed_mlops.py
"""
import asyncio
import uuid
from sqlalchemy import text
from app.core.database import engine

ROADMAP_ID = uuid.UUID("70707070-7070-7070-7070-707070707070")
SLUG = "mlops"  # content folder key + URL id; matches content/roadmaps/mlops/
TITLE = "MLOps — Models in Production"
DESCRIPTION = "Everything after the notebook: reproducible artifacts, containerized serving, feature stores, cloud deployment, inference optimization (incl. LLMs), drift monitoring and safe rollouts — interview-scoped for 0-4yr roles."

# (phase, section, title, tier, description)
NODES = [
    # ---- Foundations ----
    ("Foundations", "Data Processing", "Row- vs column-major storage", "easy", "Columnar stores prune data at scan time to minimize I/O overhead for offline feature aggregations."),
    ("Foundations", "Data Processing", "Stratified sampling", "easy", "Stratified splitting preserves minority class ratios across datasets to prevent distribution mismatch."),
    ("Foundations", "Data Processing", "Class imbalance mitigation", "medium", "Synthetic minority oversampling generates data points in feature space to balance class distributions."),
    ("Foundations", "Data Processing", "Data leakage prevention", "medium", "Splitting datasets before applying feature scaling prevents future variance from leaking into training."),
    ("Foundations", "Model Basics", "Model signatures", "medium", "Schema definitions enforce validation at model load time to reject mismatched inference input structures."),
    ("Foundations", "Model Basics", "Artifacts vs parameters", "easy", "Parameters represent scalar configurations logged to databases while artifacts are serialized binaries."),
    ("Foundations", "Model Basics", "Immutable registry stages", "easy", "Model registries transition models through immutable stages to separate testing and production runs."),
    ("Foundations", "Containerization", "Docker multi-stage builds", "medium", "Multi-stage builds copy binaries from build environments into slim runtimes to reduce final image size."),
    ("Foundations", "Containerization", "Layer caching strategies", "easy", "Ordering copy instructions after dependency installation leverages caching to speed up image builds."),
    ("Foundations", "Containerization", "Non-root container security", "medium", "User directives specify non-root execution inside containers to mitigate host file system breaches."),

    # ---- Mechanism ----
    ("Serving & Features", "Offline System Design", "Train-serving skew", "medium", "Mismatch between offline feature computation and online parsing degrades downstream production accuracy."),
    ("Serving & Features", "Offline System Design", "Offline vs online evaluation", "medium", "Offline metrics validate statistical performance while A/B tests measure actual business KPI impact."),
    ("Serving & Features", "Offline System Design", "Dataset version hashing", "easy", "Version control tracks data via hashes stored in Git to guarantee exact dataset replication states."),
    ("Serving & Features", "Serving Architecture", "Batch vs real-time serving", "medium", "Batch serving trades off fresh predictions for throughput while online serving optimizes latency."),
    ("Serving & Features", "Serving Architecture", "CPU vs GPU footprint", "easy", "Processors handle high-concurrency small requests efficiently while GPUs maximize large tensor outputs."),
    ("Serving & Features", "Serving Architecture", "Binary protocol serialization", "medium", "Binary serialization via gRPC bypasses JSON parsing bottlenecks to accelerate network throughput."),
    ("Serving & Features", "Feature Stores", "Online vs offline stores", "medium", "Dual databases serve low-latency online reads and high-throughput offline batch queries seamlessly."),
    ("Serving & Features", "Feature Stores", "Feature time travel", "hard", "Point-in-time joins use historical timestamps to merge feature sets and eliminate temporal data leakage."),
    ("Serving & Features", "Feature Stores", "Entity key modeling", "easy", "Entity keys join distinct feature tables to guarantee consistent feature values across serving pools."),
    ("Serving & Features", "Feature Stores", "Low-latency caching", "medium", "In-memory stores act as the online feature layer to provide sub-millisecond retrieval speeds for APIs."),

    # ---- Applied ----
    ("Deploy & Optimize", "Cloud Platforms", "Multi-model endpoints", "medium", "Shared containers load multiple models in memory to cut infrastructure costs for long-tail predictions."),
    ("Deploy & Optimize", "Cloud Platforms", "Serverless inference", "hard", "Serverless endpoints auto-scale to zero during idle periods to eliminate standby compute charges."),
    ("Deploy & Optimize", "Cloud Platforms", "Local mock deployments", "easy", "Local API mocks run within Docker to debug model serving behavior prior to cloud infrastructure setup."),
    ("Deploy & Optimize", "Pipeline Orchestration", "Task retries & backoffs", "easy", "Exponential backoffs handle transient network errors in pipeline runs to prevent cascading failures."),
    ("Deploy & Optimize", "Pipeline Orchestration", "Dynamic configurations", "medium", "Environment variables injected at runtime decouple pipeline parameters from static source code bases."),
    ("Deploy & Optimize", "Pipeline Orchestration", "Data validation checks", "medium", "Schema assertions validate data constraints at runtime to block corrupted inputs from retraining jobs."),
    ("Deploy & Optimize", "Inference Optimization", "Quantization trade-offs", "hard", "Post-training quantization reduces FP32 weights to integer formats to decrease memory footprints."),
    ("Deploy & Optimize", "Inference Optimization", "Model compilation", "hard", "Hardware compilers optimize tensor operations for target devices to accelerate raw execution speeds."),
    ("Deploy & Optimize", "Inference Optimization", "Prompt prefix caching", "hard", "Inference engines cache key-value pairs of matching prompt prefixes to reduce time-to-first-token."),
    ("Deploy & Optimize", "Inference Optimization", "Dynamic request batching", "hard", "Server-level request batching groups multiple inference queries concurrently to maximize GPU usage."),

    # ---- Production/Ops ----
    ("Monitoring & Rollout", "Model Monitoring", "Covariate drift", "hard", "Statistical shifts in input feature distributions degrade predictions without alerting system health."),
    ("Monitoring & Rollout", "Model Monitoring", "Concept drift", "hard", "Underlying shifts in target relationships render historical training patterns obsolete over time."),
    ("Monitoring & Rollout", "Model Monitoring", "Asynchronous logging", "medium", "Message queues decouple prediction logging from the main execution thread to avoid latency overhead."),
    ("Monitoring & Rollout", "Model Monitoring", "Automated alerting", "easy", "Threshold monitors trigger immediate alerts or model fallback pipelines when metric baselines drop."),
    ("Monitoring & Rollout", "Deployment Strategies", "Canary routing", "medium", "Traffic splitters direct a small percentage of requests to new models to limit sudden blast radiuses."),
    ("Monitoring & Rollout", "Deployment Strategies", "Shadow deployment", "medium", "Traffic mirrors clone live requests to candidate models without returning outputs to the end user."),
    ("Monitoring & Rollout", "Deployment Strategies", "Instant rollback mechanics", "medium", "Blue-green load balancers switch targets to instantly rollback traffic if the green deployment fails."),
    ("Monitoring & Rollout", "Deployment Strategies", "Cold start mitigation", "hard", "Provisioned concurrency pre-warms containers to eliminate cold starts during sudden traffic spikes."),
    ("Monitoring & Rollout", "Security & Guardrails", "Readiness probes", "easy", "Readiness endpoints prevent Kubernetes from routing traffic to containers before model weights load."),
    ("Monitoring & Rollout", "Security & Guardrails", "Input guardrails", "medium", "Validation layers sanitize text against safety rules prior to model invocation to block injections."),
    ("Monitoring & Rollout", "Security & Guardrails", "PII payload scrubbing", "hard", "Regular expressions scrub sensitive fields from prediction requests before writing to public logs."),
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
