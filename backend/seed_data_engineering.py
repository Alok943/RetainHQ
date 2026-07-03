"""
Seed script: Data Engineering roadmap.

Sub-tracks (phase = step spine): Foundations · SQL Depth · Python ETL ·
Data Warehousing · Orchestration · Big Data · Streaming · Cloud Platforms · Data Quality & Ops.

The DA→DE transition path (JD research run 3): 230k+ open roles, SQL is the #1 filter,
Airflow/Docker gate the technical screen.

Idempotent. Run: ./.venv/Scripts/python.exe seed_data_engineering.py
"""
import asyncio
import uuid
from sqlalchemy import text
from app.core.database import engine

ROADMAP_ID = uuid.UUID("60606060-6060-6060-6060-606060606060")
SLUG = "data-engineering"  # content folder key + URL id; matches content/roadmaps/data-engineering/
TITLE = "Data Engineering"
DESCRIPTION = "Pipelines that move and shape data reliably: deep SQL, Python ETL, warehouse modeling, Airflow orchestration, Spark, streaming and one cloud done properly."

NODES = [
    # ---------------- Foundations ----------------
    ("Foundations", "Landscape", "What a data engineer owns", "easy", "Ingest → store → transform → serve; DE vs DA vs DS."),
    ("Foundations", "Landscape", "OLTP vs OLAP", "easy", "Row-store transactional DBs vs column-store analytical warehouses."),
    ("Foundations", "Landscape", "Batch vs streaming", "easy", "Scheduled bulk loads vs continuous event processing."),
    ("Foundations", "Storage", "File formats: CSV, JSON, Parquet, Avro", "medium", "Columnar (Parquet) wins for analytics; schema evolution matters."),
    ("Foundations", "Storage", "Data lake vs warehouse vs lakehouse", "medium", "Raw object storage vs modeled warehouse vs Delta/Iceberg hybrid."),
    ("Foundations", "Contracts", "Schema-on-read vs schema-on-write", "medium", "Where structure is enforced decides where failures surface."),

    # ---------------- SQL Depth ----------------
    ("SQL Depth", "Core", "Window functions in anger", "medium", "ROW_NUMBER, LAG/LEAD, running totals — the DE interview staple."),
    ("SQL Depth", "Core", "CTEs & query decomposition", "easy", "Break 200-line production queries into readable steps."),
    ("SQL Depth", "Performance", "Explain plans & indexes", "hard", "Read the plan; know why a query is slow before touching it."),
    ("SQL Depth", "Performance", "Partitioning & clustering", "hard", "Prune data at scan time; the #1 warehouse cost lever."),
    ("SQL Depth", "Patterns", "Slowly changing dimensions in SQL", "hard", "Type 1 vs Type 2 history tracking."),
    ("SQL Depth", "Patterns", "Deduplication & late-arriving data", "medium", "QUALIFY/ROW_NUMBER dedupe; idempotent re-loads."),

    # ---------------- Python ETL ----------------
    ("Python ETL", "Core", "Extract-transform-load anatomy", "easy", "Pull, reshape, land — each step restartable."),
    ("Python ETL", "Core", "pandas for pipeline work", "medium", "Chunked reads, dtype control, merge pitfalls."),
    ("Python ETL", "Reliability", "Idempotent pipeline design", "hard", "Re-running must not duplicate or corrupt — upserts, staging tables."),
    ("Python ETL", "Reliability", "Error handling & retries", "medium", "Fail loudly, retry transient errors with backoff."),
    ("Python ETL", "Production", "Config, secrets & environments", "medium", "Env vars, no hardcoded creds, dev/staging/prod parity."),
    ("Python ETL", "Production", "Packaging & testing pipelines", "medium", "pytest on transforms; pipelines are code, not scripts."),

    # ---------------- Data Warehousing ----------------
    ("Data Warehousing", "Modeling", "Star schema: facts & dimensions", "medium", "The canonical analytics model — grain first."),
    ("Data Warehousing", "Modeling", "Snowflake schema & normalization trade-offs", "medium", "Normalized dims: less redundancy, more joins."),
    ("Data Warehousing", "Modeling", "Choosing the grain", "hard", "One row means what? Wrong grain breaks every metric downstream."),
    ("Data Warehousing", "dbt", "dbt models & refs", "medium", "SQL transforms as versioned, dependency-aware models."),
    ("Data Warehousing", "dbt", "dbt tests & documentation", "medium", "not_null/unique/relationships tests as CI for data."),
    ("Data Warehousing", "Loads", "Incremental vs full-refresh loads", "medium", "Merge strategies; when incremental lies to you."),

    # ---------------- Orchestration ----------------
    ("Orchestration", "Airflow", "DAGs, tasks & operators", "medium", "Pipelines as dependency graphs on a schedule."),
    ("Orchestration", "Airflow", "Scheduling, catchup & backfills", "hard", "Execution dates, data intervals, replaying history."),
    ("Orchestration", "Airflow", "Sensors & cross-DAG dependencies", "medium", "Wait-for-upstream patterns without deadlocks."),
    ("Orchestration", "Airflow", "Idempotency & retries in DAGs", "hard", "Task-level retries only help if tasks are safe to re-run."),
    ("Orchestration", "Alternatives", "Dagster / Prefect at a glance", "easy", "Asset-oriented orchestration; know the landscape."),

    # ---------------- Big Data ----------------
    ("Big Data", "Spark", "Why Spark: distributed dataframes", "medium", "When data outgrows one machine; lazy evaluation."),
    ("Big Data", "Spark", "Transformations vs actions", "medium", "Nothing runs until an action; the DAG behind the API."),
    ("Big Data", "Spark", "Shuffles, partitions & skew", "hard", "The performance model — wide ops are the expensive ones."),
    ("Big Data", "Spark", "Joins at scale (broadcast vs sort-merge)", "hard", "Pick the join strategy or Spark picks a slow one."),
    ("Big Data", "Tables", "Delta Lake / Iceberg table formats", "medium", "ACID on object storage; time travel, compaction."),

    # ---------------- Streaming ----------------
    ("Streaming", "Kafka", "Topics, partitions & consumer groups", "medium", "The distributed log; ordering per partition only."),
    ("Streaming", "Kafka", "Delivery semantics", "hard", "At-least-once vs exactly-once; where duplicates come from."),
    ("Streaming", "Processing", "Windowing & watermarks", "hard", "Event time vs processing time; handling lateness."),
    ("Streaming", "Design", "When streaming is worth it", "medium", "Most 'real-time' asks are micro-batch in disguise."),

    # ---------------- Cloud Platforms ----------------
    ("Cloud Platforms", "Storage", "Object storage (S3/GCS) as the substrate", "easy", "Cheap, durable, slow-listing; layout & lifecycle rules."),
    ("Cloud Platforms", "Warehouse", "One warehouse deep: BigQuery/Redshift/Snowflake", "medium", "Slots/RPUs/credits — the cost model IS the skill."),
    ("Cloud Platforms", "Compute", "Docker for data workloads", "medium", "Reproducible pipeline images; the screen-gate skill."),
    ("Cloud Platforms", "Movement", "Managed ingestion (Fivetran/Airbyte)", "easy", "Buy vs build for connectors."),
    ("Cloud Platforms", "Cost", "Cost control & query hygiene", "medium", "Partition pruning, clustering, kill SELECT *."),

    # ---------------- Data Quality & Ops ----------------
    ("Data Quality & Ops", "Quality", "Data quality checks & contracts", "medium", "Freshness, volume, schema, nulls — checked in-pipeline."),
    ("Data Quality & Ops", "Quality", "Data lineage & observability", "medium", "Trace a bad number back to its source."),
    ("Data Quality & Ops", "Ops", "Incident response for pipelines", "medium", "Backfill playbooks; communicate blast radius."),
    ("Data Quality & Ops", "Governance", "PII handling & access control", "medium", "Masking, least privilege, retention."),
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
