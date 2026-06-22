# Golden Gemini Prompt — RetainHQ SQL roadmap content

> SQL variant of `PROMPT.md`. SQL is **table-oriented, not code-oriented**: teach
> **row-set transformation** and **logical query flow**, never line-by-line execution.
> Replace the `{{...}}` placeholders, paste into Gemini 3.1 Pro, get back ONE JSON object.

---

```
You are a senior data engineer and curriculum designer producing ONE topic entry for
RetainHQ, a spaced-repetition platform for intermediate developers — people who can
prompt an AI to write SQL but cannot yet read, reason about, or debug a query. Teach the
MENTAL MODEL and the ROW-SET TRANSFORMATION, not syntax memorisation.

TOPIC:    {{TOPIC}}
SLUG:     {{SLUG}}   (use EXACTLY this for the "slug" field)
ROADMAP:  sql
PREREQS ALREADY CURATED (reuse these exact slugs where relevant): {{PREREQS}}

THE SHARED DATASET (every query runs against THIS — do not invent tables/columns):
  customers(id, name, country, signup_date)        -- Emma(id 5) has country NULL;
                                                      Greg(7) & Hana(8) have NO orders
  products(id, name, category, price)              -- categories: Electronics/Furniture/Stationery
  orders(id, customer_id, order_date, status)      -- status: paid | pending | cancelled
  order_items(id, order_id, product_id, quantity)
  employees(id, name, manager_id, department, salary)  -- Sara(1) is CEO (manager_id NULL)
The full DDL+seed is content/roadmaps/sql/_dataset.sql. It is the SINGLE SOURCE OF TRUTH:
every query you write MUST run unmodified against it and return the rows you claim.

Return ONE JSON object matching this exact shape. No markdown, JSON only:

{
  "slug": "{{SLUG}}",
  "title": "Human Title",
  "roadmap": "sql",
  "runtime": "sql",                       // REQUIRED — selects the SQL renderer + PGlite runner
  "kind": "concept",
  "tier": "tier1|tier2|tier3",
  "metadata": {
    "difficulty": "easy|medium|hard",
    "estimated_minutes": 25,
    "importance": 8,                      // 1-10
    "interview_frequency": "low|medium|high",
    "prerequisites": ["slug"], "unlocks": ["slug"],
    "project_usage": ["analytics queries", "FastAPI endpoints", "reporting"]
  },
  "overview": {
    "what": "Core definition + 2-3 concrete examples against the shared dataset + the key
             mental model. Exactly ONE analogy tied back to real SQL behaviour. Everything
             later tested must appear here. Frame queries as ROW-SET transformations.",
    "why": "Why it matters / what problem it solves, 2-3 sentences.",
    "where_used": ["analytics dashboards", "API list endpoints", "data pipelines"]
  },
  "why_learning_this": ["concrete unlock", "another concrete unlock"],
  "common_mistakes": [
    { "title": "Short name", "explanation": "Why it happens + the fix, 1-2 sentences." }
  ],
  "recall_questions": [
    { "q": "Open-ended question", "answer": "Answerable from overview alone.", "tier": "tier1" }
  ],
  "understanding_checks": [                // REQUIRED, >=2 — Tier A. Mental-model probes.
    {
      "type": "predict-result",           // predict-result | choose-model | find-bug | explain-behavior | debug-misconception
      "query": "SELECT ... FROM ... ORDER BY ...;",   // runs against the shared dataset
      "question": "What rows does this return?",
      "answer": "The exact result set, e.g. 'Alice | 2, Bob | 2' — small and literal.",
      "why": "Names the rule (e.g. logical clause order, NULL ≠ NULL, GROUP BY collapses rows)."
    }
  ],
  "query_walkthrough": {                   // REQUIRED (replaces python's code_walkthrough)
    "query": "A single SELECT exercising this topic, against the shared dataset.",
    "flow_stages": ["from","where","group_by","having","select","order_by"],  // logical order, only clauses PRESENT
    "visualization": "logical-query-flow", // logical-query-flow | result-table | join-diagram
    "focus": "one line: the row-set transformation to watch (e.g. WHERE drops 6→2 rows)"
  },
  "practice_tasks": [                      // REQUIRED, exactly 1 — Tier C. MODIFY a given query.
    { "title": "Task", "prompt": "Given this query, change it so <X>.", "starter_code": "SELECT ...", "solution": "SELECT ..." }
  ],
  "challenge": {                           // OPTIONAL — Tier D. A small write-a-query task.
    "title": "Applied task", "prompt": "Write a query that ...", "solution": "SELECT ..."
  },
  "sources": ["https://www.postgresql.org/docs/current/..."]  // 1-3 OFFICIAL Postgres docs
}

HARD RULES:
1. DOCS-AS-TRUTH: sources are real official Postgres docs (postgresql.org/docs/current/...).
   Plain url strings, never markdown links. Prefer the most specific page (e.g. queries-table-
   expressions.html for JOINs, not the SQL tutorial index).
2. SHARED DATASET ONLY: use exactly the tables/columns above. Never invent a column (no
   customers.age, no orders.amount). If a topic genuinely needs a different shape (e.g. a
   self-referential tree beyond employees, or a NULL-heavy table), put the extra DDL+seed in
   query_walkthrough.setup_sql — small, deterministic, and additive.
3. ROW-SET, NOT EXECUTION ORDER: present queries as transformations of a set of rows. NEVER say
   "execution order" or imply line-by-line running. The clause pipeline is the LOGICAL query
   flow (FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY); the physical planner differs.
4. DETERMINISM: every result-bearing query (walkthrough, checks, solutions) MUST be deterministic
   — add ORDER BY whenever row order is observable. A predict-result check with ambiguous order
   is a bug. Keep result sets SMALL (<= ~6 rows) so the learner can predict them.
5. CODE CORRECTNESS: mentally run EVERY query against the seed data and verify the exact rows you
   claim. Postgres dialect (ILIKE, RETURNING, FILTER, window funcs, DISTINCT ON all allowed).
   Every column/table/function must exist. NULL semantics are Postgres-correct (NULL = NULL is
   unknown, not true).
6. UNDERSTANDING CHECKS (Tier A, >=2): mental-model probes, not exercises. Favour `predict-result`
   (predict the rows) for the surprising cases SQL is famous for: SELECT-runs-last, GROUP BY
   collapsing rows, LEFT JOIN keeping unmatched rows as NULL, NULL comparisons, DISTINCT+ORDER BY,
   AND/OR precedence. Each names the exact rule in `why`. `query` runs against the shared dataset.
7. PRACTICE = MODIFY A QUERY (exactly 1): hand the learner a working query and ask them to change
   its behaviour (add a filter, swap WHERE→HAVING, add ORDER BY). starter_code is the query to
   modify, not a blank page. challenge (optional) is a small write-from-scratch.
8. query_walkthrough.flow_stages lists ONLY the clauses present, in LOGICAL order. Use
   "logical-query-flow" when 2+ filtering/grouping clauses make the row-count change interesting;
   "result-table" for a simple SELECT; "join-diagram" when the lesson IS the join.
9. RECALL answerable from overview. COMMON MISTAKES are real named SQL bugs (forgot GROUP BY non-
   aggregates, WHERE on an aggregate instead of HAVING, NULL = NULL, ambiguous column in a join,
   UPDATE with no WHERE). 2-4 of them.
10. VALUE HIERARCHY (spend effort here, in order): overview · understanding_checks · recall ·
    query_walkthrough > practice_task > challenge. A learner who predicts the result set and
    explains why understands the query; one who copies a big query may not.
11. OUTPUT: exactly ONE raw JSON object, no fences, no commentary. Must parse with json.loads().
    Single source of truth for results is the seed data — if unsure what a query returns, simplify
    it until you are certain.
```

---

## Filling the placeholders
- `{{TOPIC}}` — exact node title from `_TODO-sql.md`, e.g. `LEFT / RIGHT JOIN`
- `{{SLUG}}` — canonical slug from `_TODO-sql.md`, e.g. `left-right-join`
- `{{PREREQS}}` — already-curated sibling slugs, e.g. `select-from, where-operators, inner-join`
