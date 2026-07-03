"""
Seed script: MLOps roadmap.

Sub-tracks (phase = step spine): Foundations · Reproducibility · Model Serving ·
Containers & Orchestration · CI/CD for ML · Cloud ML Platforms · Monitoring & Retraining · LLMOps.

The DS→MLE transition path (JD research run 3): the gap is pure engineering depth —
packaged code, Docker/K8s, CI/CD for models, serving at scale, monitoring.

Idempotent. Run: ./.venv/Scripts/python.exe seed_mlops.py
"""
import asyncio
import uuid
from sqlalchemy import text
from app.core.database import engine

ROADMAP_ID = uuid.UUID("70707070-7070-7070-7070-707070707070")
SLUG = "mlops"  # content folder key + URL id; matches content/roadmaps/mlops/
TITLE = "MLOps — Models in Production"
DESCRIPTION = "Everything after the notebook: reproducible training, model serving, Docker/Kubernetes, CI/CD for models, cloud ML platforms, and monitoring/retraining loops."

NODES = [
    # ---------------- Foundations ----------------
    ("Foundations", "Landscape", "What MLOps actually is", "easy", "DevOps applied to the model lifecycle: train → ship → monitor → retrain."),
    ("Foundations", "Landscape", "Why notebooks don't ship", "easy", "Hidden state, no tests, no versioning — the gap MLOps closes."),
    ("Foundations", "Lifecycle", "The ML lifecycle & its failure points", "medium", "Data drift, training/serving skew, silent degradation."),
    ("Foundations", "Code", "Production Python: packaging & structure", "medium", "src layout, pyproject, entry points — models are libraries."),
    ("Foundations", "Code", "Testing ML code", "medium", "Unit-test transforms, smoke-test training, assert on model contracts."),

    # ---------------- Reproducibility ----------------
    ("Reproducibility", "Versioning", "Versioning data & models (DVC / registries)", "medium", "Code in git isn't enough — pin data + weights too."),
    ("Reproducibility", "Tracking", "Experiment tracking (MLflow / W&B)", "medium", "Params, metrics, artifacts — every run reconstructable."),
    ("Reproducibility", "Environment", "Environment pinning & seeds", "medium", "Lockfiles, random seeds, CUDA versions — determinism limits."),
    ("Reproducibility", "Pipelines", "Training pipelines as code", "hard", "One command retrains end-to-end; no manual steps."),
    ("Reproducibility", "Features", "Feature stores (concept)", "medium", "Same feature computation at train and serve time kills skew."),

    # ---------------- Model Serving ----------------
    ("Model Serving", "Patterns", "Batch vs online vs streaming inference", "medium", "Latency requirement decides the architecture."),
    ("Model Serving", "API", "Model behind a REST API (FastAPI)", "medium", "Load once at startup, validate inputs, version the endpoint."),
    ("Model Serving", "Performance", "Latency, batching & throughput", "hard", "Dynamic batching, model warm-up, p99 not average."),
    ("Model Serving", "Formats", "Model formats: pickle, ONNX, TorchScript", "medium", "Portability + the pickle security problem."),
    ("Model Serving", "Servers", "Dedicated servers (Triton / TorchServe)", "hard", "When a FastAPI wrapper stops being enough."),

    # ---------------- Containers & Orchestration ----------------
    ("Containers & Orchestration", "Docker", "Dockerizing a model service", "medium", "Slim images, layer caching, GPU base images."),
    ("Containers & Orchestration", "Docker", "Image size & build hygiene", "medium", "Multi-stage builds; don't ship the training stack."),
    ("Containers & Orchestration", "Kubernetes", "K8s core: pods, deployments, services", "hard", "Just enough K8s to deploy and scale a model."),
    ("Containers & Orchestration", "Kubernetes", "Autoscaling & resource limits", "hard", "HPA on custom metrics; GPU scheduling basics."),
    ("Containers & Orchestration", "Release", "Rollouts: blue-green & canary for models", "hard", "Ship the new model to 5% first; instant rollback."),

    # ---------------- CI/CD for ML ----------------
    ("CI/CD for ML", "CI", "CI for ML repos", "medium", "Lint, tests, small-data training smoke test on every PR."),
    ("CI/CD for ML", "CD", "Continuous delivery of models", "hard", "Registry promotion: staging → prod with human or metric gates."),
    ("CI/CD for ML", "Validation", "Pre-deployment model validation", "hard", "Eval-set thresholds, bias checks, behavioral tests before promote."),
    ("CI/CD for ML", "Automation", "Retraining triggers", "medium", "Schedule vs drift-triggered vs data-arrival retrains."),

    # ---------------- Cloud ML Platforms ----------------
    ("Cloud ML Platforms", "Platforms", "One platform deep: SageMaker / Vertex", "medium", "Managed train + deploy + registry; the JD keyword."),
    ("Cloud ML Platforms", "Training", "Managed training jobs & spot instances", "medium", "Off-box training; checkpointing survives preemption."),
    ("Cloud ML Platforms", "Endpoints", "Managed endpoints & serverless inference", "medium", "Autoscaling endpoints vs pay-per-request trade-offs."),
    ("Cloud ML Platforms", "Cost", "GPU cost control", "medium", "Right-size instances, quantize, batch — the bill is a metric."),

    # ---------------- Monitoring & Retraining ----------------
    ("Monitoring & Retraining", "Observability", "Service monitoring: latency, errors, saturation", "medium", "The model service is a service first — standard SRE signals."),
    ("Monitoring & Retraining", "Drift", "Data drift & concept drift", "hard", "Input distribution shifts vs the world changing; detection stats."),
    ("Monitoring & Retraining", "Quality", "Online model-quality monitoring", "hard", "Delayed labels, proxy metrics, shadow evaluation."),
    ("Monitoring & Retraining", "Loop", "The retraining loop end-to-end", "hard", "Detect → retrain → validate → promote, without a human bottleneck."),
    ("Monitoring & Retraining", "Safety", "Rollback & incident playbooks", "medium", "Bad model in prod: detect fast, revert faster."),

    # ---------------- LLMOps ----------------
    ("LLMOps", "Delta", "How LLMOps differs from MLOps", "medium", "Prompts + retrieval versioned like models; evals replace test sets."),
    ("LLMOps", "Evals", "Prompt/output evaluation in CI", "hard", "Golden sets, LLM-as-judge, regression gates on prompt changes."),
    ("LLMOps", "Observability", "Tracing LLM apps (tokens, cost, latency)", "medium", "Per-request traces; cost is a first-class metric."),
    ("LLMOps", "Serving", "Self-hosted LLM serving (vLLM)", "hard", "Continuous batching, KV cache; when APIs stop making sense."),
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
