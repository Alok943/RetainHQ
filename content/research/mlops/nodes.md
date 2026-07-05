# MLOps — node-derivation research (audit trail)

Source: Gemini Deep Research, 2026-07-04. Target roles: ML Engineer / MLOps Engineer, India
metros, 0–4 yrs (incl. Data Scientists moving to production). Prompt: `content/research/_ready-prompt.md`
(MLOps top block). Seeded by `backend/seed_mlops.py` (UUID 70707070, slug mlops). Replaced the
earlier hand-drafted MLOps node list.

Raw report: compressed via headroom → hash below.

## Node list (41 nodes, 4 phases) — see seed for tuples
Foundations (10) · Mechanism (10) · Applied (10) · Production/Ops (11).
Tuples came in correct (phase, section, title, tier, desc) order — no swap needed this run.

Tier mix: 10 hard (Feature time travel, Serverless inference, Quantization, Model compilation,
Prompt prefix caching, Dynamic request batching, Covariate drift, Concept drift, Cold-start
mitigation, PII payload scrubbing) — a real intermediate roadmap, and notably modern (LLM-serving
aware). Anti-beginner-only rule held.

## Excluded list (boundary discipline)
- Distributed training algorithms (Ring All-Reduce, ZeRO) → senior-only
- Advanced Kubernetes networking (Calico, BGP, custom operators) → belongs-in-DevOps
- Raw Transformer architecture implementation in PyTorch → canon-only
- Algorithm design (CNN/RNN/Random Forest architectures) → out-of-scope
- Multi-armed bandits for exploration/exploitation → senior-only
- Pure graph traversal / DP (A* search) → belongs-in-System-Design
- CUDA kernel low-level programming → senior-only
- Hardware provisioning / bare-metal networking → belongs-in-DevOps

## Validation (10 questions → nodes)
1. Precision dropped 90→70%, diagnose input vs behavior shift → Covariate drift, Concept drift, Asynchronous logging
2. 150ms latency budget, optimize endpoint → Binary protocol serialization, Batch vs real-time serving, Online vs offline stores
3. Feature engineering under rapid data change, avoid historical leakage → Feature time travel, Data leakage prevention
4. 7GB Docker images, autoscaling too slow → Docker multi-stage builds, Layer caching strategies, Cold start mitigation
5. Safely evaluate a new model in prod without affecting users → Shadow deployment, Offline vs online evaluation
6. API endpoint doesn't crash on unexpected/missing JSON → Model signatures, Input guardrails
7. Optimize LLM cost/latency for repetitive prompts → Prompt prefix caching, Quantization trade-offs
8. Prevent scheduled retraining from ingesting corrupted data → Data validation checks, Task retries & backoffs
9. Stop Kubernetes routing to a pod while 4GB model still loading → Readiness probes, Local mock deployments
10. Deployment failing in prod, instantly revert without downtime → Instant rollback mechanics, Canary routing

### Phase objectives
- Foundations — *so that* you build secure, reproducible model artifacts + containerized envs that pass basic compliance.
- Mechanism — *so that* you architect the connective tissue between offline training data and online serving without skew.
- Applied — *so that* you deploy, orchestrate and optimize ML + LLM pipelines on cloud infra.
- Production/Ops — *so that* you route live traffic safely, detect silent failures, and recover autonomously.

### Claude review notes
- **Phase labels RELABELED** (2026-07-04) from the prompt's abstract ordering hints
  (Foundations/Mechanism/Applied/Production-Ops) to descriptive step-spine names matching DE:
  **Foundations · Serving & Features · Deploy & Optimize · Monitoring & Rollout**. Node membership
  unchanged; only the phase field was renamed. The validation "so that" objectives above still map
  (Mechanism→Serving & Features, Applied→Deploy & Optimize, Production/Ops→Monitoring & Rollout).
- **Lighter on CI/CD-for-ML + experiment tracking** than the old hand-draft (no explicit CI-for-ML
  repos / continuous-delivery / MLflow-tracking-depth phase; only Artifacts-vs-Parameters,
  Immutable-registry-stages, Dataset-version-hashing touch it). Evidence-justified (0-4yr MLOps
  screens test serving/drift/deploy more than CI ceremony), but if targeting platform-MLOps roles,
  add a CI/CD + experiment-tracking phase in a later run.
- No orphan nodes: all 40 map to an interview question or a clear day-1 production need.

## Sources
**JD/market:** Wisemonk MLOps hiring · Cognizant MLOps Engineer · RevenueFast Bangalore AI/ML ·
CloudSoftSol Vertex-AI MLOps Qs · GfG MLOps interview Qs
**Interviews:** Kaam.work MLOps India · Kore1 ML Engineer Qs · Reddit r/learnmachinelearning ·
LeetCode MLE interview experience · TowardsAI 101 ML/LLM/AIOps Qs · Hashnode MLOps Qs
**Canon:** "Designing ML Systems" (Chip Huyen) summary · MLflow + RAGAS docs · Docker multi-stage docs

## Headroom hash for full raw report
`356a44bf9485cde9fe01ebb8` — retrieve via mcp__headroom__headroom_retrieve for the full node
list + excluded + validation + sources.
