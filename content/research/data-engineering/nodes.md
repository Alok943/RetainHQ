# Data Engineering — node-derivation research (audit trail)

Source: Gemini Deep Research, 2026-07-04. Target roles: Data Engineer / Analytics Engineer,
India metros (Bangalore, Hyderabad, Pune, NCR/Gurugram, Chennai), 0–4 yrs. Prompt:
`content/research/_ready-prompt.md`. Seeded by `backend/seed_data_engineering.py`
(UUID 60606060, slug data-engineering). Replaced the earlier hand-drafted DE node list.

Raw report full text: compressed via headroom → hash recorded below (retrieve for the market
segmentation + prose reasoning). Node list + excluded + validation summarized here.

## Node list (41 nodes, 9 phases) — see seed for tuples
SQL Fundamentals (5) · Python for Data (3) · Data Modeling (5) · Big Data & Storage (3) ·
Distributed Compute (7) · Transformation & Analytics (6) · Orchestration (5) ·
Streaming & Messaging (3) · Production DataOps (3).

Tier mix: 8 hard (Broadcast Hash Joins, Data Skew, OOM Debugging, Schema Change Management,
Sensor Reschedule Mode, Offsets & At-Least-Once, Idempotent Pipelines, Schema Drift Validation),
the rest easy/medium — a real intermediate roadmap, NOT beginner-only. The anti-beginner-only
prompt rule worked.

Format note: the research emitted tuples as (phase, section, TIER, TITLE, desc); the seed schema
is (phase, section, TITLE, TIER, desc) — fields 3 & 4 were swapped during transcription.

## Excluded list (boundary discipline)
- ML modeling & deployment (MLflow, NLP) → Data Science / ML roadmap
- Dashboard / BI UI (Tableau, Looker, PowerBI) → Data Analyst / BI roadmap
- Advanced IaC & Kubernetes (cluster admin, Terraform state) → DevOps / Platform
- Web backend frameworks (Django, FastAPI, Node) → Software Engineering (Backend)
- Advanced algorithms (LeetCode-hard, DP, graphs) → pure SWE; DE screens prioritize applied
  data manipulation + SQL

## Validation (10 questions/incidents → nodes)
1. 3rd-highest salary without subquery → Window functions
2. WHERE vs HAVING execution difference → WHERE vs HAVING
3. RDD vs DataFrame, which for structured → RDD vs DataFrame
4. What is a shuffle; eliminate it joining massive+tiny → Wide transformations & shuffling + Broadcast hash joins
5. INNER vs LEFT JOIN when Table B has 0 rows → NULL join behavior
6. Process 50GB CSV on 8GB RAM in Python → Generator streams
7. cache() vs persist() in PySpark → Cache vs persist
8. Schema evolution when upstream adds columns → Schema change management
9. [incident] Airflow DAG paused a month → unpause → 30 concurrent runs DDOS'd prod DB → Catchup & backfilling
10. [incident] nightly batch failed halfway, blind restart → doubled revenue metrics → Idempotent pipelines

### Claude review notes
- No unmapped/orphan nodes flagged beyond the 10-question sample; nodes not in the 10 (e.g. ACID,
  Star vs Snowflake, Medallion, Topics & Partitions) are all standard DE interview + day-1 items,
  keep.
- vs the earlier hand-drafted DE seed: research version DROPS an explicit cloud-object-storage /
  cost-model phase and a PII/governance node (lower frequency for 0-4yr), and ADDS the Spark
  optimization hard-tier (skew/OOM/broadcast), Python-for-data (generators/pagination), and dbt
  incremental depth — net stronger and evidence-backed. If a later run targets GCC governance
  roles, revisit PII/lineage.

## Sources
**JD:** Egen (GCP DE) · Jobdost Big Data Engineer · Capgemini FBS DE Pune · Loop Analytics Eng ·
NxtWave Analytics Eng Hyd · Bain · Infosys · Two Circles · Indeed dbt Gurugram
**Interviews:** GfG Deloitte DE · GfG EY DE · GfG Accenture 2025-26 · foundit 60+ DE Qs · GfG
top-50 DE Qs · Reddit r/dataengineering AMA · RevenueFast junior-python-DE Blr
**Canon:** dbt Labs docs (incremental strategy/models) · Apache Airflow docs (DAGs, dag-run,
data intervals) · Capgemini/IABAC (Medallion, ELT)

## Headroom hash for full raw report
`cdacb93ae3ecbec836c6b995` — retrieve via mcp__headroom__headroom_retrieve for the full market
segmentation + prose reasoning. (Original Gemini .md also in Downloads: "Data Engineering Roadmap
Research.md".)
