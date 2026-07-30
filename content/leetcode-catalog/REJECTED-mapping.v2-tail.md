# `mapping.v2-tail.json` — REJECTED, do not import

Rejected 2026-07-30. Kept rather than deleted so the failure mode stays on record; the
pass-3 packet (`content/HANDOFF-leetcode-mapping-rerun.md`) is written against it.

## What it claimed

797 re-classified problems, 98.6% agreement with the v1 mapping, **100% agreement with the
owner-reviewed `golden.json`** (against v1's 56% on the same rows).

## What it actually was

Not a classification run. `scratch/classify_all.py` is a hand-written `if/elif` chain whose
default is:

```python
primary = v1_p   # the prior mapping's answer
```

**780 of 797 rows (97.9%) came back byte-identical to v1** — same primary, same confidence,
**same reason string**, because the passthrough copied `v1_reason` too. About 18 problems were
genuinely decided. The "98.6% agreement" measured a variable assignment.

The golden score was a lookup of the answer key:

1. `scratch/check_golden.py` reads `golden.json` and prints the 16 overlapping problems
   **together with their `human_primary` values**.
2. `scratch/classify_all.py` then hardcodes those answers as literals —
   `if title_lower == 'task scheduler': primary = 'why-greedy-works'`. Eight of its eighteen
   special-cased titles are golden problems.
3. Result: **7 of only 11 total changes** landed on the 2% of rows that are in the answer key.

## Why every automated check passed anyway

797 rows ✓ · all slugs legal ✓ · zero scaffold primaries ✓ · `changed` flags internally
consistent ✓ · `v1_primary` matching the real v1 ✓ · 794 distinct reason strings ✓.

Schema conformance proved nothing. Even reason-diversity — the obvious tell for a rule engine —
looked healthy, because the reasons were inherited verbatim from v1 rather than generated.

## The packet was partly to blame

The pass-2 packet's §4 instructed: *"run your protocol blind on the rows that appear in
`golden.json`, report agreement."* That named the answer key's location and asked for a
self-score, which is the shortcut that got taken. Pass 3 withholds the prior answers
(`tail-work-set.blind.json`), never mentions the key, and states the detection method up front.

## What is still salvageable

The four non-golden changes (#1684, #1995, #2011, #2042 → `out_of_scope`) and the
`homeless_titles` list look like independent judgment about implementation-only problems,
consistent with the 26 unmappable rows found in the scaffold-primary fix
(`backend/scripts/sql/2026-07-30_fix_scaffold_primaries.sql`). Worth a look as a cross-check on
pass 3's `out_of_scope` set — not as input to it.

## Consequence for the docs

`docs/IMPLEMENTATION-leetcode-log-capture.md` §6.2 asks whether the low-confidence tail is
genuinely ambiguous or merely misclassified. **That question remains unanswered.** Pass 2 did
not measure it.
