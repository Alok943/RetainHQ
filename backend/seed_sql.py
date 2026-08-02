"""
Seed script: SQL roadmap.

Structure mirrors the SQL placement roadmap (13 modules) — phases are the module
spine: Querying Basics · Modifying Data · Modeling & Constraints · Joins ·
Aggregation · Subqueries & CTEs · Window Functions · Transactions & ACID ·
Indexes · Query Performance · PostgreSQL Features · RetainHQ SQL Drills ·
Interview Questions.

Node titles MUST match the `title` field of their lesson JSON in
content/roadmaps/sql/ exactly — RoadmapDetail/Home/Review resolve a node to its
lesson via manifest.json (exact title first, slugify(title) as fallback). Nodes
with no lesson yet are intentional: they're the content backlog (docs/BACKLOG.md).

Idempotent AND id-preserving: nodes are matched by title and UPDATEd in place, so
user_progress / node_meta / career mappings survive a re-seed. RENAMES carries
old title -> new title so a retitled node keeps its id too. Nodes no longer in
NODES are deleted (cascading their progress).

Run: ./.venv/Scripts/python.exe seed_sql.py
"""
import asyncio
import uuid
from sqlalchemy import text
from app.core.database import engine

ROADMAP_ID = uuid.UUID("99999999-9999-9999-9999-999999999999")
TITLE = "SQL — Querying & Modeling"
SLUG = "sql"  # URL identifier; matches the content/ folder key
DESCRIPTION = (
    "From SELECT to window functions, transactions, indexes and query plans — plus "
    "PostgreSQL specifics and interview drills. The one skill every backend, data "
    "and analytics role assumes you have."
)

# Titles that changed shape between seed revisions. Applied before the upsert so
# the node keeps its id (and its progress) instead of being dropped + recreated.
RENAMES = {
    "SELECT, FROM & columns": "SELECT, FROM & Columns",
    "WHERE & operators": "WHERE & Operators",
    "ORDER BY, LIMIT, OFFSET": "ORDER BY, LIMIT & OFFSET",
    "Data types & NULL handling": "Data Types & NULL Handling",
    "CASE expressions": "CASE Expressions",
    "Self join": "Self Join",
    "ON vs USING & join keys": "ON vs USING & Join Keys",
    "Aggregate functions": "Aggregate Functions",
    "Multi-column grouping": "Multi-Column Grouping",
    "Scalar & IN subqueries": "Scalar & IN Subqueries",
    "Correlated subqueries": "Correlated Subqueries",
    "LEAD / LAG": "LEAD & LAG",
    "INSERT": "INSERT & Returning",
    "UPDATE & DELETE (mind the WHERE!)": "UPDATE, DELETE & Returning",
    "Transactions (COMMIT / ROLLBACK)": "Transactions (BEGIN, COMMIT, ROLLBACK)",
    "When indexes help (and don't)": "How Databases Use Indexes",
    "EXPLAIN / query plans": "Reading EXPLAIN ANALYZE",
    "Full scans & N+1": "Common Query Pitfalls & Anti-patterns",
}

# (phase, section, title, tier, description)
NODES = [
    # ---------------- Module 1 — Querying Basics ----------------
    ("Querying Basics", "Reading", "SELECT, FROM & Columns", "easy", "Pick columns from a table; aliases with AS."),
    ("Querying Basics", "Reading", "WHERE & Operators", "easy", "AND/OR/NOT, IN, BETWEEN, LIKE/ILIKE, IS NULL."),
    ("Querying Basics", "Reading", "ORDER BY, LIMIT & OFFSET", "easy", "Sort and paginate results."),
    ("Querying Basics", "Reading", "DISTINCT", "easy", "Drop duplicate rows; COUNT(DISTINCT ...)."),
    ("Querying Basics", "Types", "Data Types & NULL Handling", "medium", "INTEGER/NUMERIC/TEXT/UUID/JSONB; NULL, COALESCE, NULLIF."),
    ("Querying Basics", "Logic", "CASE Expressions", "medium", "Inline conditional values and conditional columns."),
    ("Querying Basics", "Functions", "String Functions", "easy", "CONCAT, LENGTH, LOWER/UPPER, TRIM, SUBSTRING."),
    ("Querying Basics", "Functions", "Date & Time Functions", "medium", "NOW(), CURRENT_DATE, AGE(), DATE_TRUNC()."),

    # ---------------- Module 2 — Modifying Data ----------------
    ("Modifying Data", "Writes", "INSERT & Returning", "easy", "Single and multi-row inserts; INSERT ... RETURNING."),
    ("Modifying Data", "Writes", "UPDATE, DELETE & Returning", "easy", "No WHERE = whole table. UPDATE/DELETE ... RETURNING."),
    ("Modifying Data", "Writes", "DELETE vs TRUNCATE vs DROP", "easy", "Row-by-row vs table-wide vs gone entirely."),
    ("Modifying Data", "Writes", "UPSERT (ON CONFLICT)", "medium", "Insert-or-update in one statement."),

    # ---------------- Module 3 — Modeling & Constraints ----------------
    ("Modeling & Constraints", "Keys", "Primary, foreign & unique keys", "easy", "Identity + referential integrity."),
    ("Modeling & Constraints", "Rules", "Constraints & defaults", "easy", "NOT NULL, CHECK, DEFAULT."),
    ("Modeling & Constraints", "Design", "Normalization (1NF–3NF)", "medium", "Remove redundancy & update anomalies."),
    ("Modeling & Constraints", "Design", "Denormalization & Tradeoffs", "medium", "Trading write cost and consistency for read speed."),

    # ---------------- Module 4 — Joins ----------------
    ("Joins", "Core", "INNER JOIN", "easy", "Rows matching in both tables."),
    ("Joins", "Core", "LEFT / RIGHT JOIN", "medium", "Keep all rows from one side; NULLs for misses."),
    ("Joins", "Core", "FULL OUTER & CROSS JOIN", "medium", "All rows / cartesian product."),
    ("Joins", "Advanced", "Self Join", "hard", "Join a table to itself (e.g. employee→manager)."),
    ("Joins", "Keys", "ON vs USING & Join Keys", "medium", "Match condition; USING for same-named columns; composite keys."),

    # ---------------- Module 5 — Aggregation ----------------
    ("Aggregation", "Functions", "Aggregate Functions", "easy", "COUNT, SUM, AVG, MIN, MAX."),
    ("Aggregation", "Grouping", "GROUP BY", "medium", "Collapse rows into groups."),
    ("Aggregation", "Grouping", "Multi-Column Grouping", "medium", "Group by several dimensions."),
    ("Aggregation", "Filtering", "HAVING vs WHERE", "medium", "WHERE filters rows; HAVING filters groups."),
    ("Aggregation", "Advanced", "Conditional Aggregation (FILTER & CASE)", "hard", "Count/sum only the rows matching a condition, per group."),

    # ---------------- Module 6 — Subqueries & CTEs ----------------
    ("Subqueries & CTEs", "Subqueries", "Scalar & IN Subqueries", "medium", "A query inside a query."),
    ("Subqueries & CTEs", "Subqueries", "EXISTS vs IN", "medium", "Semi-join semantics, and why NOT IN breaks on NULLs."),
    ("Subqueries & CTEs", "Subqueries", "Correlated Subqueries", "hard", "Inner query references the outer row."),
    ("Subqueries & CTEs", "CTEs", "CTEs (WITH)", "medium", "Named, readable sub-results."),
    ("Subqueries & CTEs", "CTEs", "Recursive CTEs", "hard", "Walk hierarchies / graphs."),

    # ---------------- Module 7 — Window Functions ----------------
    ("Window Functions", "Basics", "OVER & PARTITION BY", "hard", "Aggregate without collapsing rows."),
    ("Window Functions", "Ranking", "ROW_NUMBER / RANK / DENSE_RANK", "hard", "Rank within partitions."),
    ("Window Functions", "Offset", "LEAD & LAG", "hard", "Look at next/previous row."),
    ("Window Functions", "Frames", "Running totals & moving averages", "hard", "Frame clause over ordered rows."),

    # ---------------- Module 8 — Transactions & ACID ----------------
    ("Transactions & ACID", "Basics", "Transactions (BEGIN, COMMIT, ROLLBACK)", "medium", "All-or-nothing units of work."),
    ("Transactions & ACID", "Theory", "ACID Properties", "hard", "Atomicity, Consistency, Isolation, Durability — what each buys you."),
    ("Transactions & ACID", "Isolation", "Isolation Levels", "hard", "Read Uncommitted → Read Committed → Repeatable Read → Serializable."),
    ("Transactions & ACID", "Isolation", "Concurrency Problems & Deadlocks", "hard", "Dirty/non-repeatable/phantom reads, lost updates, deadlocks."),
    ("Transactions & ACID", "Control", "Savepoints", "medium", "SAVEPOINT and ROLLBACK TO — partial undo inside a transaction."),

    # ---------------- Module 9 — Indexes ----------------
    ("Indexes", "Why", "Indexes — what & when", "medium", "Speed reads; cost writes & storage."),
    ("Indexes", "Why", "How Databases Use Indexes", "medium", "Full scan vs B-tree lookup — what the planner actually does."),
    ("Indexes", "Creating", "Creating & Dropping Indexes", "medium", "CREATE INDEX / DROP INDEX, and CONCURRENTLY in production."),
    ("Indexes", "Creating", "Composite Indexes", "hard", "Column order decides which queries the index can serve."),
    ("Indexes", "Creating", "Unique & Partial Indexes", "medium", "Enforce uniqueness; index only the rows you query."),
    ("Indexes", "Advanced", "Covering Indexes & Index-Only Scans", "hard", "INCLUDE columns so the heap never gets touched."),
    ("Indexes", "Cost", "When Indexes Hurt", "medium", "Extra storage, slower INSERT/UPDATE/DELETE, unused indexes."),

    # ---------------- Module 10 — Query Performance ----------------
    ("Query Performance", "Plans", "Reading EXPLAIN ANALYZE", "hard", "Estimated vs actual rows and time; where the cost really is."),
    ("Query Performance", "Plans", "Scan Types — Seq, Index & Index-Only", "medium", "When a sequential scan is genuinely the right plan."),
    ("Query Performance", "Pitfalls", "Common Query Pitfalls & Anti-patterns", "medium", "Functions on indexed columns, SELECT *, implicit casts."),
    ("Query Performance", "Pitfalls", "The N+1 Problem (SQL & SQLAlchemy)", "medium", "One query per row; fix with joins or selectinload."),

    # ---------------- Module 11 — PostgreSQL Features ----------------
    ("PostgreSQL Features", "Keys", "SERIAL vs IDENTITY", "medium", "Legacy sequence default vs the SQL-standard GENERATED column."),
    ("PostgreSQL Features", "Keys", "UUID Keys", "medium", "Global uniqueness, opaque ids — and the index cost."),
    ("PostgreSQL Features", "Types", "JSON vs JSONB", "medium", "Text vs binary; which one can be indexed."),
    ("PostgreSQL Features", "Types", "Arrays", "medium", "Array columns, containment operators, unnest()."),
    ("PostgreSQL Features", "Types", "ENUM Types", "medium", "Closed vocabularies at the type level — and migration pain."),
    ("PostgreSQL Features", "Types", "Generated Columns", "medium", "Stored columns computed from other columns."),
    ("PostgreSQL Features", "Views", "Views", "medium", "Named queries — abstraction with no storage."),
    ("PostgreSQL Features", "Views", "Materialized Views", "hard", "Cached query results; REFRESH and staleness tradeoffs."),
    ("PostgreSQL Features", "Programming", "Functions (PL/pgSQL)", "hard", "Logic in the database: when it's right and when it isn't."),
    ("PostgreSQL Features", "Programming", "Triggers", "hard", "Automatic side effects on INSERT/UPDATE/DELETE."),

    # ---------------- Module 12 — RetainHQ SQL Drills ----------------
    ("RetainHQ SQL Drills", "Querying", "Drill — Due & Overdue Reviews", "medium", "Today's due reviews, upcoming, longest overdue, weakest activities."),
    ("RetainHQ SQL Drills", "Aggregation", "Drill — Review Analytics", "medium", "Reviews per day/roadmap, average quality, success & recall rates."),
    ("RetainHQ SQL Drills", "Joins", "Drill — Joining Activities, Reviews & Roadmaps", "hard", "Users ↔ activities ↔ reviews ↔ roadmaps in one result set."),
    ("RetainHQ SQL Drills", "Windows", "Drill — Streaks & Rankings", "hard", "Daily streaks, longest learning streak, running review totals."),
    ("RetainHQ SQL Drills", "Transactions", "Drill — Transactional Review Completion", "hard", "Complete review + update FSRS state + insert next, or roll back."),
    ("RetainHQ SQL Drills", "Performance", "Drill — Indexing the Dashboard Queries", "hard", "Index the due-review path; read the plan before and after."),

    # ---------------- Module 13 — Interview Questions ----------------
    ("Interview Questions", "Fundamentals", "Interview — SQL Fundamentals", "easy", "SQL vs PostgreSQL, keys, DELETE vs TRUNCATE vs DROP."),
    ("Interview Questions", "Joins", "Interview — Joins", "medium", "INNER vs LEFT, LEFT vs RIGHT, CROSS, SELF, ON vs USING."),
    ("Interview Questions", "Aggregation", "Interview — Aggregation", "medium", "GROUP BY vs DISTINCT, HAVING vs WHERE, COUNT(*) vs COUNT(col)."),
    ("Interview Questions", "Subqueries", "Interview — Subqueries & CTEs", "medium", "CTE vs subquery, EXISTS vs IN, correlated subqueries."),
    ("Interview Questions", "Transactions", "Interview — Transactions & ACID", "hard", "Explain ACID, isolation levels, deadlocks."),
    ("Interview Questions", "Performance", "Interview — Indexes & Performance", "hard", "What is an index, why fast, when to avoid, why is this query slow."),
    ("Interview Questions", "PostgreSQL", "Interview — PostgreSQL Specifics", "medium", "Why Postgres, JSON vs JSONB, UUID vs SERIAL, ON CONFLICT, RETURNING."),
]


async def main():
    titles = [n[2] for n in NODES]
    assert len(titles) == len(set(titles)), "duplicate node titles in NODES"

    async with engine.begin() as conn:
        # Roadmap row: upsert, never delete (deleting it cascades every node).
        existing = (await conn.execute(
            text("SELECT 1 FROM roadmaps WHERE id = :rid"), {"rid": str(ROADMAP_ID)}
        )).first()
        if existing:
            await conn.execute(
                text("UPDATE roadmaps SET slug = :slug, title = :title, description = :desc WHERE id = :rid"),
                {"rid": str(ROADMAP_ID), "slug": SLUG, "title": TITLE, "desc": DESCRIPTION},
            )
        else:
            await conn.execute(
                text("INSERT INTO roadmaps (id, slug, title, description, created_at) "
                     "VALUES (:rid, :slug, :title, :desc, now())"),
                {"rid": str(ROADMAP_ID), "slug": SLUG, "title": TITLE, "desc": DESCRIPTION},
            )

        # Retitle first, so renamed nodes are matched (and keep their id) below.
        for old, new in RENAMES.items():
            await conn.execute(
                text("UPDATE roadmap_nodes SET title = :new "
                     "WHERE roadmap_id = :rid AND title = :old "
                     "AND NOT EXISTS (SELECT 1 FROM roadmap_nodes x "
                     "                WHERE x.roadmap_id = :rid AND x.title = :new)"),
                {"rid": str(ROADMAP_ID), "old": old, "new": new},
            )

        rows = (await conn.execute(
            text("SELECT title FROM roadmap_nodes WHERE roadmap_id = :rid"), {"rid": str(ROADMAP_ID)}
        )).all()
        present = {r[0] for r in rows}

        inserted = updated = 0
        for i, (phase, section, title, tier, desc) in enumerate(NODES):
            params = {"rid": str(ROADMAP_ID), "phase": phase, "section": section,
                      "title": title, "tier": tier, "idx": i, "desc": desc}
            if title in present:
                await conn.execute(
                    text("UPDATE roadmap_nodes SET phase = :phase, section = :section, "
                         "tier = :tier, order_index = :idx, description = :desc "
                         "WHERE roadmap_id = :rid AND title = :title"),
                    params,
                )
                updated += 1
            else:
                await conn.execute(
                    text("INSERT INTO roadmap_nodes "
                         "(id, roadmap_id, phase, section, title, tier, order_index, description) "
                         "VALUES (:id, :rid, :phase, :section, :title, :tier, :idx, :desc)"),
                    {**params, "id": str(uuid.uuid4())},
                )
                inserted += 1

        stale = present - set(titles)
        if stale:
            await conn.execute(
                text("DELETE FROM roadmap_nodes WHERE roadmap_id = :rid AND title = ANY(:titles)"),
                {"rid": str(ROADMAP_ID), "titles": list(stale)},
            )

    print(f"Seeded '{TITLE}': {len(NODES)} nodes "
          f"({inserted} inserted, {updated} updated, {len(stale)} removed).")
    if stale:
        for s in sorted(stale):
            print(f"  removed: {s}")


if __name__ == "__main__":
    asyncio.run(main())
