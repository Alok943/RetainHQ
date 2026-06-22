# Curation queue — SQL — Querying & Modeling (`sql`)

Source of truth for topics: `backend/seed_sql.py` (the `NODES` list, 32 nodes).
Generate **one JSON per node** with **`PROMPT-sql.md`** (NOT the Python prompt), using the
**exact title** below as `{{TOPIC}}`. Tick a box once the JSON is saved **and**
`python content/validate.py` passes. Feed done slugs into the next topic's `{{PREREQS}}`.

**Runtime:** every file sets `"runtime": "sql"` and uses `query_walkthrough` (not
`code_walkthrough`). All queries run against the **shared dataset** in
`content/roadmaps/sql/_dataset.sql` (customers · products · orders · order_items ·
employees). Topic-specific extras go in `query_walkthrough.setup_sql`.

**Why SQL fits RetainHQ:** queries are row-set transformations → predict-before-reveal on the
result set, and the FROM→WHERE→GROUP BY→HAVING→SELECT→ORDER BY **logical query flow** kills the
#1 beginner misconception (that SELECT runs first).

---

## Sub-track 1 — Querying Basics  (6)
- [x] SELECT, FROM & columns  →  `select-from`
- [x] WHERE & operators  →  `where-operators`
- [x] ORDER BY, LIMIT, OFFSET  →  `order-by-limit`
- [x] DISTINCT  →  `distinct`
- [x] Data types & NULL handling  →  `null-handling`
- [x] CASE expressions  →  `case-expressions`

## Sub-track 2 — Joins  (5)
- [x] INNER JOIN  →  `inner-join`
- [ ] LEFT / RIGHT JOIN  →  `left-right-join`
- [x] FULL OUTER & CROSS JOIN  →  `full-cross-join`
- [x] Self join  →  `self-join`
- [x] ON vs USING & join keys  →  `join-keys`

## Sub-track 3 — Aggregation  (4)
- [x] GROUP BY  →  `group-by`
- [x] Aggregate functions  →  `aggregate-functions`
- [x] HAVING vs WHERE  →  `having-vs-where`
- [x] Multi-column grouping  →  `multi-column-grouping`

## Sub-track 4 — Subqueries & CTEs  (4)
- [x] Scalar & IN subqueries  →  `subqueries`
- [x] Correlated subqueries  →  `correlated-subqueries`
- [x] CTEs (WITH)  →  `ctes`
- [x] Recursive CTEs  →  `recursive-ctes`

## Sub-track 5 — Window Functions  (4)
- [ ] OVER & PARTITION BY  →  `over-partition-by`
- [ ] ROW_NUMBER / RANK / DENSE_RANK  →  `ranking-functions`
- [ ] LEAD / LAG  →  `lead-lag`
- [ ] Running totals & moving averages  →  `window-frames`

## Sub-track 6 — Modeling & Constraints  (4)
- [ ] Primary, foreign & unique keys  →  `keys`
- [ ] Normalization (1NF–3NF)  →  `normalization`
- [ ] Constraints & defaults  →  `constraints`
- [ ] Indexes — what & when  →  `indexes`

## Sub-track 7 — Modifying Data  (4)
- [ ] INSERT  →  `insert`
- [ ] UPDATE & DELETE (mind the WHERE!)  →  `update-delete`
- [ ] UPSERT (ON CONFLICT)  →  `upsert`
- [ ] Transactions (COMMIT / ROLLBACK)  →  `transactions`

## Sub-track 8 — Performance  (3)
- [ ] When indexes help (and don't)  →  `index-usage`  *(applied angle; `indexes` above is the what/when)*
- [ ] EXPLAIN / query plans  →  `query-plans`
- [ ] Full scans & N+1  →  `query-pitfalls`

---

## Prereq backbone (suggested edges)
`select-from` → `where-operators` → `order-by-limit` → `distinct`; `null-handling` after
`where-operators`; `case-expressions` after `where-operators`. Joins build on `select-from`
(+`where-operators`). Aggregation: `group-by` → `aggregate-functions` → `having-vs-where` →
`multi-column-grouping`. Subqueries/CTEs build on aggregation + joins. Window functions build on
`group-by` + `order-by-limit`. Modeling is mostly independent. Modifying Data builds on
`where-operators` (esp. `update-delete`). Performance builds on `indexes` + joins.

## Wiring note (do once, before serving SQL lessons)
Add to `frontend/src/lib/contentRoadmaps.js`:
`'SQL — Querying & Modeling': 'sql'` so the lesson view resolves the content key.

## Build status (runtime/frontend — separate from content)
Content contract is **ready** (`PROMPT-sql.md`, `schema.json` `runtime:"sql"` branch,
`validate.py`, `_dataset.sql`). Still to build (P0→P3, per the runtime review): PGlite runner,
result-table renderer, predict-before-reveal on result sets, logical-query-flow scrubber, JOIN
visualizer.
