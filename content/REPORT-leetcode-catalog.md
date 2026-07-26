# LeetCode Catalog Seed Run Report

**Pulled At:** `2026-07-21T16:01:35Z`  
**Wall-Clock Duration:** 222.3 seconds  
**Total Requests Made:** 41 requests (1 GraphQL probe + 40 GraphQL paginated requests + 1 legacy REST request)

---

## 1. Counts & Summary

| Metric | Count |
|---|---|
| **Source A (GraphQL) total** | 3,999 |
| **Source B (REST) total** | 3,999 |
| **Accepted (both sources agree)** | 3,999 |
| **Conflicts** | 0 |
| **Acceptance Divergences (> 2 pp)** | 0 |

---

## 2. Schema Verification

- **GraphQL Schema (§1.1):** Matched verbatim. The probe query (`limit: 1, skip: 0`) returned valid `data.problemsetQuestionList` data with all requested fields (`frontendQuestionId`, `title`, `titleSlug`, `difficulty`, `acRate`, `isPaidOnly`, `topicTags`).
- **REST Endpoint (§1.1):** Endpoint `https://leetcode.com/api/problems/all/` returned standard `stat_status_pairs` array matching expected fields.

---

## 3. Conflict Analysis

- **Total Conflicts:** 0
- No missing rows in either source (`missing_in_a`: 0, `missing_in_b`: 0).
- No field mismatches across compared fields (`slug`, `difficulty`, `paid_only`: 0).

---

## 4. Acceptance Rate Divergences

- **Count > 2 percentage points:** 0
- Acceptance rates calculated from Source A (`acRate / 100`) aligned with Source B (`total_acs / total_submitted`) across all rows within the 2 percentage point tolerance threshold.

---

## 5. Surprises & Observations

1. **Flawless Source Alignment:** All 3,999 problems present in Source A matched Source B exactly across `slug`, `difficulty`, and `paid_only` with zero discrepancies.
2. **Paid-Only Problems:** 775 out of 3,999 problems (19.4%) are marked as `paid_only: true`.
3. **Empty Tags:** Exactly 132 problems have no topic tags attached (`tags: []`), triggering a minor warning in the gate validator, which is expected for newer or unclassified problems on LeetCode.
4. **Distinct Tags:** 72 distinct topic tag slugs were extracted and deduplicated.

---

## 6. Gate Validator Output

Result of running `python content/validate_leetcode_catalog.py` verbatim:

```
catalog v1: 3999 problems, 0 conflicts, 775 paid-only
  difficulty: {'easy': 956, 'hard': 955, 'medium': 2088}   distinct tags: 72
WARN  132 problem(s) have zero tags

OK - 0 error(s), 1 warning(s)
```
