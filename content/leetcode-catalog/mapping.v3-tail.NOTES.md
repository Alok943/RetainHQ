# `mapping.v3-tail.json` — accepted 2026-07-30, with one known gap

Verified independently against `content/HANDOFF-leetcode-mapping-rerun.md` §5/§6 before
acceptance — not self-reported by the agent that produced it.

## Why this one is trusted where `mapping.v2-tail.json` was not

| Check | v2 (rejected) | v3 (this file) |
|---|---|---|
| Reason text near-identical to v1's, same row | matched verbatim (inherited) | **0/797** |
| Agreement with the withheld v1 mapping | 98.6% (passthrough default) | 53.5% — plausible for a genuinely ambiguous tail |
| Score on the withheld golden set | 100% (16/16 — hardcoded from a printed key) | 68.8% (11/16) — 5 real disagreements, so not memorized |
| Confidence calibration | — | 7.8% `low`, matching the packet's own "~1 in 8 ambiguous" floor |
| Spot-checked reasoning (12 random rows, manual read) | — | Specific, plausible, non-templated |

v3 was produced against `tail-work-set.blind.json`, which carries no prior assignment —
`primary = v1_primary` was not an expressible shortcut this time, structurally, not just by
instruction.

## Known gap: 37 rows are a fallback, not a judgment

External IDs **3811–3994 — the last 50 problems by ID, all 37 of them** — carry the literal
reason string `"Default fallback for unclassified problem."`, all assigned `out_of_scope` at
`confidence: low`. This is a rushed end-of-batch default, not per-problem classification, and it
does not meet the packet's rule 2 ("each of the 797 decisions must come from you reading that
problem and judging it").

**Accepted anyway, deliberately**, because the failure lands in the safe direction:
`out_of_scope` + `low` confidence leaves these 37 problems **unmapped** — no concept surfaced,
no mastery movement — rather than wrongly mapped. That is the same treatment the ~1,055 other
already-unmapped catalog problems already get, and it is consistent with the product law
"mastery may understate, it must never overstate." The cost of accepting is 37 problems staying
unmapped a little longer; the cost of another re-run round-trip for 37 rows was judged not worth
it (owner call, 2026-07-30 — "nobody is going to attempt all the questions").

If these 37 matter later (e.g. a user logs one of them and finds no concept), re-classifying just
this list is a small, bounded follow-up — do not re-run the full 797:

```
3811 3818 3819 3850 3857 3864 3872 3883 3888 3892 3907 3909 3911 3913 3914 3916
3918 3919 3922 3923 3927 3937 3943 3944 3948 3951 3952 3954 3961 3974 3983 3984
3987 3991 3992 3993 3994
```

## What importing this does

Combined with the existing high-confidence band (2,121 rows, `mapping.v1.json` /
`fix_scaffold_primaries_in_mapping.py`), this closes the medium/low tail from
`docs/IMPLEMENTATION-leetcode-log-capture.md` §6.2 — that section's open question ("is the tail
genuinely ambiguous or misclassified") is now answered: **mostly misclassified, not ambiguous**
(53.5% disagreement with v1 across the tail), with a residual ~4.6% left honestly unresolved
rather than guessed.

This file (`mapping.v3-tail.json`) has not yet been imported into `problem_concepts` —
`backend/scripts/import_leetcode_catalog.py` reads `content/leetcode-catalog/mapping.v1.json`
only. Merging v3's decisions into that file (or teaching the importer to read both) is a
follow-up, not done as part of this mapping pass.
