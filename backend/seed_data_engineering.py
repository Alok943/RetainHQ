"""
Seed script: Data Engineering roadmap.

Sub-tracks (phase = step spine): SQL Fundamentals · Python for Data · Data Modeling ·
Big Data & Storage · Distributed Compute · Transformation & Analytics · Orchestration ·
Streaming & Messaging · Production DataOps.

Node list = the validated node-derivation research run (Gemini Deep Research, 2026-07-04;
Data Engineer / Analytics Engineer, India metros, 0-4yr). Audit trail + excluded list +
mock-interview validation in content/research/data-engineering/nodes.md. Evidence-driven: nodes
map to real Deloitte/EY interview questions + real production incidents, not a textbook TOC.

The DA->DE transition path (JD research run 3): SQL is the #1 filter; Airflow/Spark gate the
technical screen. Tier mix intentionally spans easy->hard (Spark optimization + idempotency +
offsets are the differentiator round), NOT beginner-only.

Idempotent. Run: ./.venv/Scripts/python.exe seed_data_engineering.py
"""
import asyncio
import uuid
from sqlalchemy import text
from app.core.database import engine

ROADMAP_ID = uuid.UUID("60606060-6060-6060-6060-606060606060")
SLUG = "data-engineering"  # content folder key + URL id; matches content/roadmaps/data-engineering/
TITLE = "Data Engineering"
DESCRIPTION = "Reliable pipelines end to end: analytical SQL, Python ingestion, warehouse modeling, Spark at scale, dbt, Airflow orchestration, Kafka, and production DataOps — interview-scoped for 0-4yr roles."

# (phase, section, title, tier, description)
NODES = [
    # ---- SQL Fundamentals ----
    ("SQL Fundamentals", "Query Logic", "NULL join behavior", "easy", "NULL join keys evaluate to unknown; INNER JOIN drops them while LEFT JOIN preserves the left side with empty targets."),
    ("SQL Fundamentals", "Query Logic", "WHERE vs HAVING", "easy", "WHERE filters source rows before grouping; HAVING filters aggregated results after GROUP BY executes."),
    ("SQL Fundamentals", "Query Logic", "Three-valued logic", "easy", "SQL uses true, false, and unknown; comparisons with NULL require IS NULL rather than standard equality operators."),
    ("SQL Fundamentals", "Advanced SQL", "Common Table Expressions", "easy", "CTEs create modular, readable subqueries that avoid nested logic and allow recursive hierarchical data traversal."),
    ("SQL Fundamentals", "Advanced SQL", "Window functions", "medium", "Window functions compute running totals and rankings over partitions without condensing rows like GROUP BY does."),

    # ---- Python for Data ----
    ("Python for Data", "Data Structures", "Hash map time complexity", "easy", "Dictionary lookups run in O(1) via hashing, scaling far better than O(N) linear list scans for joins/lookups."),
    ("Python for Data", "Memory Management", "Generator streams", "medium", "Generators yield items sequentially via lazy evaluation, preventing memory exhaustion when reading massive datasets."),
    ("Python for Data", "API Integration", "API pagination & backoff", "medium", "Ingesting REST APIs requires offset or cursor looping with exponential backoff retries to prevent rate-limit bans."),

    # ---- Data Modeling ----
    ("Data Modeling", "Database Concepts", "OLTP vs OLAP", "easy", "OLTP systems optimize for fast row-based transactions; OLAP systems use columnar storage for analytical aggregations."),
    ("Data Modeling", "Database Concepts", "ACID properties", "easy", "ACID guarantees transactional integrity; failures trigger rollbacks preventing partial, corrupted data states."),
    ("Data Modeling", "Schema Design", "Normalization vs denormalization", "medium", "Normalization reduces write anomalies by splitting tables; denormalization groups data to speed up analytical reads."),
    ("Data Modeling", "Schema Design", "Star vs snowflake schema", "easy", "Star schemas use single, denormalized dimension tables; snowflake normalizes dimensions into multiple related tables."),
    ("Data Modeling", "Schema Design", "Slowly Changing Dimensions", "medium", "SCD Type 1 overwrites history; Type 2 adds rows with start/end dates to track historical changes over time."),

    # ---- Big Data & Storage ----
    ("Big Data & Storage", "Warehousing", "Columnar storage (Parquet)", "medium", "Columnar formats use dictionary encoding and compression to minimize disk IO and enable aggressive column pruning."),
    ("Big Data & Storage", "Warehousing", "Partitioning & clustering", "medium", "Partitioning prunes data scans by dividing physical storage directories, drastically slashing cloud compute costs."),
    ("Big Data & Storage", "Warehousing", "Decoupled storage & compute", "medium", "Separating compute from storage lets cloud warehouses scale processing power independently without paying for storage."),

    # ---- Distributed Compute ----
    ("Distributed Compute", "Spark Core", "RDD vs DataFrame", "easy", "DataFrames provide structured schemas and Catalyst optimization, outperforming low-level unstructured RDD processing."),
    ("Distributed Compute", "Spark Core", "Lazy evaluation", "medium", "Spark delays execution until an action is called, building a logical plan that optimizes operators before computing."),
    ("Distributed Compute", "Spark Core", "Wide transformations & shuffling", "medium", "Operations like joins or group-bys trigger wide transformations, moving data across the network and bottlenecking IO."),
    ("Distributed Compute", "Spark Core", "Cache vs persist", "medium", "Cache stores dataframes in default memory; persist allows specific storage levels like disk-only to prevent OOM errors."),
    ("Distributed Compute", "Spark Optimization", "Broadcast hash joins", "hard", "Broadcasting small tables to all worker nodes eliminates heavy network shuffles during distributed join operations."),
    ("Distributed Compute", "Spark Optimization", "Data skew management", "hard", "Salting skewed join keys distributes hot partitions across executors, preventing a single worker node from choking."),
    ("Distributed Compute", "Spark Optimization", "OOM debugging", "hard", "Driver OOMs result from collecting huge datasets to the master; executor OOMs require tuning overhead or partitions."),

    # ---- Transformation & Analytics ----
    ("Transformation & Analytics", "Architecture", "ETL vs ELT", "easy", "ETL transforms data before loading to save storage; ELT loads raw data first, using warehouse compute to transform."),
    ("Transformation & Analytics", "dbt Fundamentals", "Modular models & ref", "easy", "The ref() macro generates dynamic schemas and automatically builds a dependency DAG, ensuring models run in sequence."),
    ("Transformation & Analytics", "dbt Fundamentals", "dbt tests", "medium", "Generic tests run automated assertion queries checking for nulls and primary key uniqueness on every pipeline run."),
    ("Transformation & Analytics", "dbt Incremental", "Incremental materialization", "medium", "Incremental models cut compute by selectively processing only new or updated records instead of full-table rebuilds."),
    ("Transformation & Analytics", "dbt Incremental", "Merge vs append strategies", "medium", "Append blindly adds records; merge uses unique keys to update existing rows and insert new ones, avoiding duplicates."),
    ("Transformation & Analytics", "dbt Incremental", "Schema change management", "hard", "Setting on_schema_change to sync_all_columns handles upstream column additions without breaking incremental models."),

    # ---- Orchestration ----
    ("Orchestration", "Airflow Core", "DAG topology", "easy", "Directed Acyclic Graphs define task execution order and dependencies, ensuring cycles never create infinite loops."),
    ("Orchestration", "Airflow Core", "Logical vs execution date", "medium", "Logical date refers to the start of the data interval being processed, not the physical time the pipeline runs."),
    ("Orchestration", "Airflow Core", "Catchup & backfilling", "medium", "Setting catchup=False stops Airflow from blindly scheduling historical runs for periods when the DAG was paused."),
    ("Orchestration", "Airflow Core", "XCom state limitations", "medium", "XComs pass small metadata between tasks via the metastore; large dataframes must use object storage to avoid crashing."),
    ("Orchestration", "Airflow Core", "Sensor reschedule mode", "hard", "Reschedule mode releases worker slots while waiting on external events, preventing idle tasks from exhausting threads."),

    # ---- Streaming & Messaging ----
    ("Streaming & Messaging", "Architecture", "Batch vs streaming", "easy", "Batch processes bounded data at intervals; streaming processes continuous, unbounded event data in real time."),
    ("Streaming & Messaging", "Kafka", "Topics & partitions", "medium", "Kafka topics are split into partitions, allowing horizontal scalability as consumer groups process segments in parallel."),
    ("Streaming & Messaging", "Kafka", "Offsets & at-least-once", "hard", "Consumers track read progress via offsets; committing offsets after processing guarantees at-least-once delivery."),

    # ---- Production DataOps ----
    ("Production DataOps", "Architecture", "Medallion architecture", "easy", "Bronze stores raw data, Silver deduplicates and cleanses, and Gold structures business-level aggregates for reporting."),
    ("Production DataOps", "Reliability", "Idempotent pipelines", "hard", "Idempotent pipelines produce identical outputs regardless of run frequency, preventing duplicate data on re-execution."),
    ("Production DataOps", "Reliability", "Schema drift validation", "hard", "Data contracts block unexpected upstream schema changes, protecting downstream BI tables from silent corruption."),
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
