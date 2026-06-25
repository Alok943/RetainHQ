"""
Seed script: SQL roadmap.

Sub-tracks (phase = step spine): Querying Basics · Joins · Aggregation ·
Subqueries & CTEs · Window Functions · Modeling & Constraints ·
Modifying Data · Performance.

Every backend/data role needs SQL — and it's prime spaced-repetition material.

Idempotent. Run: ./.venv/Scripts/python.exe seed_sql.py
"""
import asyncio
import uuid
from sqlalchemy import text
from app.core.database import engine

ROADMAP_ID = uuid.UUID("99999999-9999-9999-9999-999999999999")
TITLE = "SQL — Querying & Modeling"
SLUG = "sql"  # URL identifier; matches the content/ folder key
DESCRIPTION = "From SELECT to window functions and query plans. The one skill every backend, data and analytics role assumes you have."

NODES = [
    # ---------------- Querying Basics ----------------
    ("Querying Basics", "Reading", "SELECT, FROM & columns", "easy", "Pick columns from a table."),
    ("Querying Basics", "Reading", "WHERE & operators", "easy", "AND/OR/IN/BETWEEN/LIKE/IS NULL."),
    ("Querying Basics", "Reading", "ORDER BY, LIMIT, OFFSET", "easy", "Sort and paginate results."),
    ("Querying Basics", "Reading", "DISTINCT", "easy", "Drop duplicate rows."),
    ("Querying Basics", "Types", "Data types & NULL handling", "medium", "NULL = unknown; COALESCE, IS NULL."),
    ("Querying Basics", "Logic", "CASE expressions", "medium", "Inline conditional values."),

    # ---------------- Joins ----------------
    ("Joins", "Core", "INNER JOIN", "easy", "Rows matching in both tables."),
    ("Joins", "Core", "LEFT / RIGHT JOIN", "medium", "Keep all rows from one side; NULLs for misses."),
    ("Joins", "Core", "FULL OUTER & CROSS JOIN", "medium", "All rows / cartesian product."),
    ("Joins", "Advanced", "Self join", "hard", "Join a table to itself (e.g. employee→manager)."),
    ("Joins", "Keys", "ON vs USING & join keys", "medium", "Match condition; USING for same-named columns."),

    # ---------------- Aggregation ----------------
    ("Aggregation", "Grouping", "GROUP BY", "medium", "Collapse rows into groups."),
    ("Aggregation", "Functions", "Aggregate functions", "easy", "COUNT, SUM, AVG, MIN, MAX."),
    ("Aggregation", "Filtering", "HAVING vs WHERE", "medium", "WHERE filters rows; HAVING filters groups."),
    ("Aggregation", "Grouping", "Multi-column grouping", "medium", "Group by several dimensions."),

    # ---------------- Subqueries & CTEs ----------------
    ("Subqueries & CTEs", "Subqueries", "Scalar & IN subqueries", "medium", "A query inside a query."),
    ("Subqueries & CTEs", "Subqueries", "Correlated subqueries", "hard", "Inner query references the outer row."),
    ("Subqueries & CTEs", "CTEs", "CTEs (WITH)", "medium", "Named, readable sub-results."),
    ("Subqueries & CTEs", "CTEs", "Recursive CTEs", "hard", "Walk hierarchies / graphs."),

    # ---------------- Window Functions ----------------
    ("Window Functions", "Basics", "OVER & PARTITION BY", "hard", "Aggregate without collapsing rows."),
    ("Window Functions", "Ranking", "ROW_NUMBER / RANK / DENSE_RANK", "hard", "Rank within partitions."),
    ("Window Functions", "Offset", "LEAD / LAG", "hard", "Look at next/previous row."),
    ("Window Functions", "Frames", "Running totals & moving averages", "hard", "Frame clause over ordered rows."),

    # ---------------- Modeling & Constraints ----------------
    ("Modeling & Constraints", "Keys", "Primary, foreign & unique keys", "easy", "Identity + referential integrity."),
    ("Modeling & Constraints", "Design", "Normalization (1NF–3NF)", "medium", "Remove redundancy & anomalies."),
    ("Modeling & Constraints", "Rules", "Constraints & defaults", "easy", "NOT NULL, CHECK, DEFAULT."),
    ("Modeling & Constraints", "Speed", "Indexes — what & when", "medium", "Speed reads; cost writes & storage."),

    # ---------------- Modifying Data ----------------
    ("Modifying Data", "Writes", "INSERT", "easy", "Add rows."),
    ("Modifying Data", "Writes", "UPDATE & DELETE (mind the WHERE!)", "easy", "No WHERE = whole table."),
    ("Modifying Data", "Writes", "UPSERT (ON CONFLICT)", "medium", "Insert-or-update in one statement."),
    ("Modifying Data", "Safety", "Transactions (COMMIT / ROLLBACK)", "medium", "All-or-nothing; ACID."),

    # ---------------- Performance ----------------
    ("Performance", "Indexes", "When indexes help (and don't)", "medium", "Selective filters & joins; not tiny tables."),
    ("Performance", "Plans", "EXPLAIN / query plans", "hard", "Read how the DB executes a query."),
    ("Performance", "Pitfalls", "Full scans & N+1", "medium", "Watch for missing indexes & per-row queries."),
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
