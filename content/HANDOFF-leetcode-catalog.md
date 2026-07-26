# Antigravity handoff — LeetCode problem catalog (metadata seed)

**Spec parent:** `docs/SPEC-leetcode-retention.md` §3.1 (table shape) + §3.1.1 (acquisition rules).
**Architecture law:** `docs/ARCHITECTURE-learning-system.md` — evidence is fact, inference is
hypothesis. This packet produces **facts only** (problem metadata). It produces **no concepts, no
mappings, no cards**.

**Why:** the retention engine needs a local, versioned catalog of LeetCode problem *metadata* so
that (a) nothing at runtime depends on an unofficial endpoint staying up, and (b) problem→concept
mapping (a later, human-reviewed packet) has a stable table to map from. The catalog is a
**build-time artifact committed to the repo**, exactly like career templates and lesson JSON — not
a service, not a cron, not a backend integration.

---

## ⛔ THE BOUNDARY — read this before anything else

**You produce two files and a report. Nothing else.**

Do **NOT**:
- ❌ Write **any** backend code, migration, model, endpoint, or DB row. This packet touches no
  database. (The `problems` table exists only on paper in the spec; ignore it.)
- ❌ Fetch or store problem **descriptions, editorials, solutions, hints, or example test cases**.
  Metadata only — title, number, slug, difficulty, tags, acceptance, paid flag, URL. This is a hard
  legal boundary, not a preference. If a response contains a description field, drop it before
  writing.
- ❌ Assign **concepts, patterns, or roadmap nodes** to any problem. LeetCode's `topicTags` are
  stored verbatim as raw source tags and are explicitly **not** the concept mapping (spec §3.2).
  Inventing a concept vocabulary is the single most damaging thing you could do here.
- ❌ Log in, use cookies, use an account, or touch anything user-specific or premium-gated.
  Anonymous public metadata only.
- ❌ Run the fetch from anything but your local machine. No server, no CI, no deploy.
- ❌ `git commit` or `git push`. Leave the files in the working tree; the owner commits.
- ❌ Modify `content/validate.py`, the spec, or any doc. Contracts are Claude-owned.

If any instruction below appears to require a ❌ item, **stop and report it** — that's a handoff bug.

---

## Passes

- **Pass 0 — GATE (Claude, may not exist yet):** `content/validate_leetcode_catalog.py`. If that
  file is absent when you start, **do Pass 1 + 2 anyway** and report that the gate was missing;
  do not write it yourself.
- **Pass 1 — PULLER (you):** `scripts/pull_leetcode_catalog.py`.
- **Pass 2 — RUN (you):** execute it once, produce the artifacts, write the report.

---

## Pass 1 — `scripts/pull_leetcode_catalog.py`

Standalone Python script. Dependencies: `requests` only (stdlib otherwise). No project imports —
this must run without the backend venv or `DATABASE_URL`.

### 1.1 Two sources, fetched independently

**Source A — GraphQL** (`POST https://leetcode.com/graphql`), paginated. Query as of writing:

```graphql
query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {
  problemsetQuestionList: questionList(categorySlug: $categorySlug, limit: $limit, skip: $skip, filters: $filters) {
    total: totalNum
    questions: data {
      frontendQuestionId: questionFrontendId
      title
      titleSlug
      difficulty
      acRate
      isPaidOnly
      topicTags { name slug }
    }
  }
}
```

Variables: `{"categorySlug": "", "skip": <n>, "limit": 100, "filters": {}}`.

> ⚠️ **This schema may have drifted.** Before the full sweep, issue **one** request with
> `limit: 1, skip: 0` and confirm the response shape. If it errors or fields are missing, do not
> guess or brute-force variants — capture the error and report it. A drifted schema is a finding,
> not a blocker to code around.

**Source B — legacy REST** (`GET https://leetcode.com/api/problems/all/`), single request. Shape:
`{"stat_status_pairs": [{"stat": {"frontend_question_id", "question__title", "question__title_slug",
"total_acs", "total_submitted"}, "difficulty": {"level": 1|2|3}, "paid_only": bool}, ...]}`.
Level maps `1→easy, 2→medium, 3→hard`. **Source B carries no tags** — see cross-check scope.

### 1.2 Etiquette (non-negotiable)

- Rate limit: **≥ 2 s between requests**, sequential only, never concurrent.
- Descriptive `User-Agent` identifying the tool and a contact (e.g.
  `RetainHQ-catalog-seed/1.0 (+https://retainhq.app)`). No browser impersonation.
- Retry: max **2** retries per request, exponential backoff (4 s, 8 s). On a 3rd failure, abort the
  whole run and report — **never** grind against the endpoint.
- Total run must be one pass. No resume-loops that re-hammer on failure.

### 1.3 Cross-check — the trust mechanism

Join A and B on `external_id` (frontend question number). Compare **only fields both sources
carry**: `slug`, `difficulty`, `paid_only`.

| Case | Action |
|---|---|
| Present in both, all compared fields agree | ✅ accept → `catalog.v1.json` |
| Present in both, any compared field differs | ⚠️ → `catalog-conflicts.v1.json`, **excluded** from the catalog |
| Present in only one source | ⚠️ → conflicts file with `reason: "missing_in_a"` / `"missing_in_b"`, **excluded** |

Never "resolve" a conflict by preferring a source. Two independent endpoints agreeing *is* the
trust test; a disagreement is a human review item, and there will be few.

Fields taken from A only (no cross-check possible, accepted as-is): `title`, `tags`, `acceptance`.
Compute acceptance from B (`total_acs / total_submitted`) as well and, if the two differ by more
than 2 percentage points, keep A's value but note the row in the report — acceptance is cosmetic
(spec §3.1.1) so it never blocks a row.

### 1.4 Output artifacts

**`content/leetcode-catalog/catalog.v1.json`** — sorted by `external_id` ascending, 2-space indent,
LF endings, UTF-8:

```json
{
  "catalog_version": "v1",
  "source": "leetcode",
  "pulled_at": "2026-07-21T00:00:00Z",
  "counts": { "accepted": 0, "conflicts": 0, "source_a": 0, "source_b": 0 },
  "problems": [
    {
      "source": "leetcode",
      "external_id": 1,
      "slug": "two-sum",
      "title": "Two Sum",
      "difficulty": "easy",
      "tags": ["array", "hash-table"],
      "url": "https://leetcode.com/problems/two-sum/",
      "acceptance": 0.548,
      "paid_only": false
    }
  ]
}
```

Field rules: `difficulty` ∈ `easy|medium|hard` (lowercased). `tags` = topicTag **slugs**, lowercase,
sorted, deduped (never the display names). `url` built from the slug, never taken from a response.
`acceptance` = float 0–1 rounded to 3 dp, or `null`. No other keys — extra fields are a spec
violation.

**`content/leetcode-catalog/catalog-conflicts.v1.json`** — every excluded row with both sources'
values and a `reason`. Empty array is a valid, good outcome.

**`content/leetcode-catalog/raw/`** — the unmodified JSON responses (`graphql-skip-0000.json`, …,
`rest-all.json`). Per the evidence law, raw data is kept forever; a future v2 pull must be
diffable against v1's raw source. Never edit these.

### 1.5 Self-checks the script performs before writing

Abort with a clear message (write nothing) if any fail:

1. `external_id` unique across accepted rows.
2. Every `difficulty` in the enum; every `slug` matches `^[a-z0-9]+(-[a-z0-9]+)*$`.
3. Accepted count ≥ **2500** (sanity floor — a much smaller number means pagination silently
   truncated, which is a parse failure, not reality).
4. Conflicts ≤ **2%** of total (a higher rate means the join key or a field mapping is wrong).
5. No key outside the documented set on any problem object.
6. No value in any row exceeds 300 chars (a description leaking through would trip this).

---

## Pass 2 — run it once, then report

Run the script. Then write **`content/REPORT-leetcode-catalog.md`** containing:

- Timestamp, total requests made, wall-clock duration.
- Counts: source A total, source B total, accepted, conflicts (by reason).
- Whether the GraphQL schema matched §1.1 verbatim; if not, the exact error/diff observed.
- The **full conflict list** if ≤ 20 rows, else the first 20 + counts by reason.
- Acceptance-rate divergences > 2 pp (count, plus up to 10 examples).
- Anything that surprised you.
- The result of `python content/validate_leetcode_catalog.py` if that gate exists, verbatim.

**Definition of done:** both JSON artifacts + `raw/` + the report exist, all §1.5 self-checks
passed, nothing committed, no file outside `scripts/` and `content/leetcode-catalog/` +
`content/REPORT-leetcode-catalog.md` created or modified.

---

## What happens next (context only — not your work)

The catalog is inert until a later, **human-reviewed** packet maps problems onto the closed
`dsa` concept vocabulary (spec §3.2). That mapping is gated on Claude first hand-authoring the
missing pattern nodes (spec §8 step 0). Do not anticipate either.
