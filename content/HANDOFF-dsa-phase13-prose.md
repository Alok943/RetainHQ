# Antigravity handoff -- DSA phase 13 (Sorting: Divide & Conquer) -- PROSE PASS

Author 2 NEW `dsa`-kind lessons at `content/roadmaps/dsa/<slug>.json`. **PROSE pass: author everything
EXCEPT the `viz` block.** These are trace algorithms (they'll pair with `ArrayViz` later), but the
quick-sort partition + counting-sort count/prefix-sum generators aren't built yet -- Claude adds the
`viz` in a later pass. A `dsa` lesson validates cleanly with no `viz`. Do NOT add one.

**Only 2 nodes.** `merge-sort` is SKIPPED -- it's Claude's authored gold exemplar. Do not touch it.

**Gate: `python content/validate.py` -- zero errors.** Do NOT run the frontend. Do NOT commit.

## Reference + sources
- **Shape:** copy `content/roadmaps/dsa/merge-sort.json` (the gold `dsa` exemplar), OMIT its `viz` block,
  keep every other key. `roadmap` = "dsa", `kind` = "dsa".
- **Contract:** `content/PROMPT-dsa.md` (esp. QUALITY BAR items 6-7: every recall/oa answer derivable
  from the BODY; no unexplained jargon; `mental_model` analogy must be mechanism-based).
- **Enrichment source:** the phase-13 research JSON at `content/research/dsa/phase-13.json` (produced by
  the phase-13 research run). The concrete per-node material is ALSO inlined below so you can author now
  even if the research JSON isn't in yet.
- `mental_model.repeated_decision` IS required on both (powers the later gated viz).

## The 2 nodes (slugs from `_TODO-dsa.md`) + what each must nail
| slug | title | tier | difficulty |
|---|---|---|---|
| `quick-sort` | Quick sort | tier2 | medium |
| `counting-sort` | Counting sort | tier2 | medium |

### quick-sort -- research-grounded must-hits
- `why_it_exists`: sort in average O(n log n) but **IN-PLACE** (no O(n) aux array like merge sort) with
  great cache locality -- that's why it's the default in-memory library sort in practice.
- `mental_model`: pick a pivot; **partition** so everything <= pivot is left, everything > pivot is
  right; the pivot is now in its FINAL position; recurse on each side. repeated_decision: "is the
  current element <= the pivot (goes left) or > it (goes right)?"
- INVARIANT (teach it): after one partition, the pivot sits in its final sorted index; left partition
  <= pivot <= right partition. **Partition does NOT fully sort** -- it only places the pivot (key
  misconception to kill).
- Complexity: average O(n log n); **worst O(n^2)** on already-sorted / all-equal input with a bad
  (first/last) pivot; space O(log n) avg recursion depth (O(n) worst); NOT stable.
- Pivot choice: last/first is simplest but adversarially O(n^2); **randomized pivot or median-of-three**
  avoids the worst case. Mention Lomuto (single scan pointer) vs Hoare (two ends) partition exist.
- Pattern transfer: **quickselect** (Kth largest in O(n) average) reuses partition -- name it.
- `engineering_examples`: introsort (C++ `std::sort` = quicksort + heapsort fallback + insertion for
  small ranges); most in-memory library sorts. Label interview (hand-rolled) vs real (introsort).
- `common_mistakes`: "quicksort is always O(n log n)"; "partition sorts the array"; "it needs an extra
  array"; picking a fixed pivot on sorted data.
- `practice`: LeetCode 912 (Sort an Array), 215 (Kth Largest -- quickselect), 75 (Sort Colors -- Dutch
  national flag partition).

### counting-sort -- research-grounded must-hits
- `why_it_exists`: sort integers in **O(n + k)** by NOT comparing -- this legally BEATS the O(n log n)
  comparison lower bound (explain WHY: the bound only applies to comparison sorts). k = range of keys.
- `mental_model`: tally how many of each value (a histogram), then walk the value range placing that
  many of each in order. repeated_decision: "how many elements equal this value, and where do they go?"
- MECHANISM (teach precisely -- the recall answers depend on it): count occurrences per value ->
  **prefix-sum the counts** into ending positions -> place elements (the STABLE version scans the input
  right-to-left, decrementing each value's count as it places). INVARIANT: after the prefix sum,
  count[v] = number of elements <= v = the placement boundary for v.
- Complexity: O(n + k) time and space; only practical when **k is not >> n** (bounded integer keys).
- STABILITY matters because counting sort is the building block of **radix sort** (stable-sort by each
  digit, least-significant first) -- cover this link; it's the "where it scales" answer.
- `common_mistakes`: "you can always sort in O(n)" (only for small bounded k); "works on any data" (no
  -- needs bounded integer / mappable keys); "it's just bucketing" (the prefix-sum + stable placement is
  the real trick, not naive buckets).
- `engineering_examples`: radix-sort component; sorting by bounded keys (ages 0-120, ASCII bytes, exam
  scores); histogram-based ordering.
- `practice`: LeetCode 75 (Sort Colors), 1122 (Relative Sort Array), 164 (Maximum Gap -- bucket/radix).

## Quality bar (the FIVE questions -- answerable from the lesson alone)
1. Why it exists (problem -> naive -> better). 2. How to simulate (mental_model + repeated_decision +
a hand-trace in `explanation`). 3. The invariant. 4. A real engineering use. 5. How to recognize it.
- `recall_questions` >=3, `oa_questions` >=2, `sources` 2-5 real URLs, `practice` 2-4 LeetCode (link
  only, never paste). Cross-link `related`: quick-sort <-> merge-sort (divide & conquer pair) <->
  counting-sort (the non-comparison contrast); both prereq `merge-sort`/`recursion-tree`.

## ASCII-only in JSON
`->` not an arrow glyph, `--` not an em-dash, straight quotes.

## Process
1. Read merge-sort.json (shape) + PROMPT-dsa.md + phase-13 research (or the inline must-hits above).
2. Write the 2 files -- NO `viz` block. `python content/validate.py` -> zero errors. Tick `_TODO-dsa.md`.
3. Standing pipeline: **Gemini-in-Antigravity / Sonnet lesson critic** (separate session,
   `content/RUN-lesson-critic-antigravity.md`) -> apply fixes -> re-critic. DONE only when a cold
   beginner can answer every recall/oa question from the body AND the expert finds zero errors.

> Pass 2 (later, Claude): quick-sort gets a partition/pivot `ArrayViz` animation; counting-sort gets a
> count-array + prefix-sum panel. Generators + viz blocks are added then -- not now.
