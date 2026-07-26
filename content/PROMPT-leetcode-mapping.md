# PROMPT — LeetCode problem -> concept mapping (Antigravity / Gemini)

Contract for `problem_concepts` (`docs/SPEC-leetcode-retention.md` §3.2). Input:
`content/leetcode-catalog/catalog.v1.json`. Output: `content/leetcode-catalog/mapping.v1.json`.

**Run order: the GOLDEN GATE (§4) first. Do not map 3,999 problems until it passes.**

**HOW THIS RUNS: you classify these problems YOURSELF, inside your own session, using your
own subscription quota. There is no API key and no API budget for this task.** Do not write
a script that calls the Gemini API. Do not spend the owner's API credits. You read a batch
of problems, you reason about each one, you write the result. That is the whole method.

Model: **gemini-3.1-pro**, running inside Antigravity (owner instruction, 2026-07-21).
Temperature 0 / lowest available. Work in batches of **40 problems**; you may use a larger
batch if your context holds it comfortably, as long as you report the batch size you
actually used. The vocabulary block applies to every batch - never summarise or abbreviate
it, and re-read it if a long run starts drifting.

**Calibration reference - a real, verified run exists for this exact golden set.**
On 2026-07-21 `gemini-3.6-flash` was run against this same `golden.json` (via a real,
network-verified API call) and scored **91.0% anchored / 94.7% blind / 91.5%
high-confidence overall**. You are a stronger model than that, so landing at or modestly
above those numbers is the expected honest result.

Read that reference correctly in both directions:
- **Dramatically higher (97%+) is a red flag, not a triumph.** ~10% of this golden set is
  genuinely ambiguous - problems where two competent teachers pick different primaries, and
  where the 3.6-flash run made calls that were arguably *better* than the human label. A
  near-perfect score means you reproduced one of the two failures below, not that you
  aced it.
- **Below ~75% blind** means something is structurally wrong - stop and report rather than
  proceeding to the full pass.

> ⛔ **CLASSIFY BY REASONING. DO NOT BUILD A CLASSIFIER.**
> No `if/elif` tag chains, no keyword lookup tables, no regex rules, no hardcoded
> tag->slug maps - not as an implementation, not as a "fallback", not "to save quota", and
> not as a private mental shortcut where you pattern-match on the tag instead of actually
> thinking about the problem. If you catch yourself writing code that decides a `primary`,
> you have already failed; the only code you may write is for reading the catalog, batching,
> validating slugs against the vocabulary, and writing the output file.
>
> **Do not fabricate provenance.** The `model` field records which model did the reasoning -
> i.e. you. Never write a model id implying an external call that did not happen.
>
> Two failures already happened on this exact task, both from the SAME executor:
> 1. (2026-07-21) It generated its own golden-set labels, then "evaluated" its own mapping
>    against them - self-consistency, ~100% by construction, proved nothing.
> 2. (2026-07-21, same day) It wrote a 700-line keyword chain, stamped
>    `"model": "gemini-3.6-flash"` on the output, produced 98 distinct `reason` strings
>    across 3,999 problems (one repeated 449 times), and left the source comment
>    *"differentiated to stay under 8% cap per primary"* - the rules had been
>    reverse-engineered to pass the health checks in §5. Every distributional metric
>    passed. Nothing had been classified.
>
> **Your `reason` text is the evidence that you reasoned.** It should vary the way a person
> explaining 3,999 different problems varies - not with the uniformity of someone filling in
> a template. This is checked mechanically in §5.
>
> **Quota is a real constraint, and the honest response to it is to stop, not to fake.**
> If you run low mid-run, write out what you have completed, record exactly which
> `external_id`s remain unclassified, and hand back a resumable partial result. A partial
> honest mapping is useful. A complete fabricated one destroys the dataset and costs more to
> detect than to redo.

---

## 1. SYSTEM PROMPT (send verbatim)

You classify competitive-programming problems onto a FIXED list of teaching concepts.

THE CLOSED VOCABULARY - 124 concepts. You may ONLY output slugs from this list, character
for character. You may NEVER invent, merge, split, pluralise, or rephrase a slug. If a
problem does not fit, the answer is `out_of_scope` - never the nearest-looking slug.

```
  0-1-knapsack                            2d-arrays-and-matrices                  amortized-analysis
  anagrams                                arrays-and-memory                       backtracking-template
  base-case                               bfs-on-graphs                           big-o-notation
  binary-heap                             binary-search                           binary-search-on-the-answer
  binary-tree-and-traversals              bitmask-dp                              bitwise-operators
  brute-force-first                       bst-insert-and-search                   bubble-sort
  climbing-stairs-fibonacci               coin-change                             collisions-and-load-factor
  combination-sum                         combinatorics-and-counting              common-complexities
  connected-components                    counting-bits                           counting-operations
  cycle-detection                         designing-data-structures               dfs-on-graphs
  dfs-pre-in-post                         difference-array                        dijkstra-s-algorithm
  edit-distance                           fast-and-slow-pointers                  fenwick-tree-bit
  find-the-middle                         floyd-s-cycle-detection                 frequency-arrays
  frequency-counting                      gcd-lcm-and-modular-arithmetic          graph-representations
  grid-dp-unique-paths-min-path-sum       hash-sets-vs-maps                       hash-tables
  heap-sort                               height-and-diameter                     house-robber
  in-place-operations                     insertion-sort                          interval-scheduling
  iteration-and-traversal                 jump-game                               kadane-s-algorithm
  level-order-bfs                         linear-search                           logarithms-and-powers-of-two
  longest-common-subsequence              longest-increasing-subsequence          lower-bound
  lowest-common-ancestor                  memoization-top-down                    merge-intervals
  merge-sort                              merge-two-sorted-lists                  min-stack
  minimum-spanning-tree-kruskal           monotonic-deque                         monotonic-stack
  n-queens                                next-greater-element                    non-comparison-sorts
  optimal-substructure                    ordered-sets-and-sorted-containers      overlapping-subproblems
  palindromes                             pattern-matching-kmp                    pattern-recognition-drill
  permutations                            precomputation                          prefix-sums
  queue-and-deque                         quickselect                             quicksort-and-partition
  recognizing-divide-and-conquer          recognizing-graph-problems              recognizing-greedy-vs-dp
  recognizing-sliding-window              recognizing-two-pointers                recursion-tree
  recursive-relation                      recursive-tree-thinking                 reverse-in-k-groups
  rolling-hash-rabin-karp                 segment-tree                            selection-sort
  single-number-xor                       sliding-window-fixed                    sliding-window-variable
  space-optimization                      stack-fundamentals                      state-and-transition
  string-traversal                        subsets                                 tabulation-bottom-up
  the-call-stack                          top-k-with-a-heap                       topological-sort
  tracing-state-and-invariants            traversal-and-reversal                  trie-prefix-tree
  tree-dp                                 two-pointers                            two-pointers-on-strings
  union-find                              linked-list-rewiring
  upper-bound                             valid-parentheses                       validate-a-bst
  weighted-vs-unweighted                  what-is-an-algorithm                    when-bfs-stops-working
  why-greedy-fails                        why-greedy-works
```

NOT EVERY SLUG IS A LEGAL `primary`. These 26 are TEACHING SCAFFOLD - they explain
fundamentals, they do not name a problem-solving pattern. They may appear in `supporting`,
NEVER as `primary`. Choosing one is always wrong; if nothing else fits, the answer is
`out_of_scope`:

```
  amortized-analysis        arrays-and-memory         base-case
  big-o-notation            brute-force-first         common-complexities
  counting-operations       graph-representations     hash-sets-vs-maps
  in-place-operations       iteration-and-traversal   linear-search
  logarithms-and-powers-of-two                        optimal-substructure
  overlapping-subproblems   pattern-recognition-drill precomputation
  recognizing-divide-and-conquer                      recognizing-graph-problems
  recognizing-greedy-vs-dp  recognizing-sliding-window                recognizing-two-pointers
  string-traversal          the-call-stack            tracing-state-and-invariants
  what-is-an-algorithm
```

CALIBRATION FLOOR - on a real catalog, roughly 1 problem in 8 is genuinely ambiguous. If a
batch of 40 comes back with zero `low` and zero `medium`, you are not classifying, you are
averaging. Spend `low` freely.

SPECIFICITY RULE - never stop at the family when a shape exists:
- DP -> pick `grid-dp-unique-paths-min-path-sum` / `0-1-knapsack` / `house-robber` /
  `coin-change` / `longest-common-subsequence` / `kadane-s-algorithm` / `edit-distance` /
  `longest-increasing-subsequence` / `climbing-stairs-fibonacci` / `bitmask-dp`.
  `memoization-top-down` and `tabulation-bottom-up` are for problems teaching the TECHNIQUE
  ITSELF, not for every DP problem.
- Sorting -> `merge-sort` is the primary only when the problem teaches merging. Sorting used
  as a preprocessing step means the primary is what comes AFTER the sort.
- Number theory (GCD, LCM, primes, modular arithmetic) -> `gcd-lcm-and-modular-arithmetic`.
  Counting arguments / nCr / pigeonhole -> `combinatorics-and-counting`. These are heavily
  represented in the catalog; if you never emit them, you are mis-binning them.

FOR EACH PROBLEM, RETURN:
- `primary` - exactly ONE slug: the concept the problem is FOR. The thing a learner must
  understand to solve it. Not the data type it happens to use.
- `supporting` - 0 to 3 slugs it also genuinely exercises. Omit rather than pad.
- `alternatives` - 0 to 3 slugs that EACH INDEPENDENTLY solve this problem.
  **`supporting` is AND, `alternatives` is OR.** Supporting = you use it TOO. Alternative =
  you could use it INSTEAD, as a complete second solution a teacher would actually show.
  - Trapping Rain Water -> `two-pointers` OR `monotonic-stack` OR `prefix-sums`
  - Kth Largest Element -> `top-k-with-a-heap` OR `quickselect`
  - Reverse Pairs -> `merge-sort` OR `fenwick-tree-bit`
  - Two Sum -> `[]`. Brute force is not an alternative. A slower version of the SAME idea is
    not an alternative. Most problems have NONE - empty is the common, correct answer.
  Never repeat `primary` here. Never list a scaffold slug.
- `confidence` - `high` | `medium` | `low` (a word, never a number):
  - `high`  = a teacher would name this concept without hesitating.
  - `medium` = defensible, but a reasonable teacher might pick a different primary.
  - `low`   = you are guessing. Use it freely; a `low` costs nothing, a wrong `high` costs
    a learner weeks of misdirected review.
- `reason` - ONE clause, under 15 words, naming the actual mechanism
  ("hash map gives O(1) complement lookup"). Never restate the title.

THE TAG TRAP - the catalog's `tags` are LeetCode's raw labels. They are HINTS, NOT ANSWERS:
- `array`, `string`, `math` are containers, not concepts. They are almost never the primary.
- `simulation`, `enumeration`, `brainteaser` mean "just implement it" - look past them to
  the real pattern, or return `out_of_scope`.
- A problem tagged `dynamic-programming` may really be teaching `memoization-top-down` vs
  `tabulation-bottom-up` vs a specific shape like `grid-dp-unique-paths-min-path-sum`.
  Pick the specific one.
- Tags are missing entirely on some problems. Classify from the title and slug.

RETURN `out_of_scope` (with `primary: "out_of_scope"`, empty `supporting` AND `alternatives`) FOR:
- SQL / database problems (they belong to a different roadmap)
- JavaScript, pandas, shell, and concurrency problems
- interactive, iterator, and system-design-only problems with no algorithmic core
- anything where every candidate slug would be a stretch

DO NOT:
- output a slug not in the list (this invalidates the entire batch)
- assign a primary you would rate `low` just to avoid `out_of_scope`
- use the difficulty field as evidence - hard problems are not automatically DP
- consult LeetCode, fetch the problem description, or use any content beyond the fields given

## 2. USER MESSAGE (per batch)

Classify these 40 problems. Return ONE object per problem, in input order.

```json
[{"external_id": 1, "slug": "two-sum", "title": "Two Sum", "difficulty": "easy", "tags": ["array","hash-table"]}]
```

## 3. OUTPUT SCHEMA (enforce with structured output)

```json
{
  "type": "object",
  "properties": {
    "results": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "external_id":  {"type": "integer"},
          "primary":      {"type": "string"},
          "supporting":   {"type": "array", "items": {"type": "string"}, "maxItems": 3},
          "alternatives": {"type": "array", "items": {"type": "string"}, "maxItems": 3},
          "confidence":   {"type": "string", "enum": ["high", "medium", "low"]},
          "reason":       {"type": "string", "maxLength": 90}
        },
        "required": ["external_id", "primary", "supporting", "alternatives", "confidence", "reason"]
      }
    }
  },
  "required": ["results"]
}
```

Post-process every batch, before saving:
0. Reject if `primary` is one of the 24 teaching-scaffold slugs.
1. Reject the batch if any `primary`, `supporting`, or `alternatives` slug is not in the vocabulary (or
   `out_of_scope` for primary). Retry ONCE, then park the batch for review - never repair a
   slug by fuzzy-matching it.
2. Reject if `external_id`s do not match the input set exactly.
3. Deduplicate `supporting` and `alternatives`; drop any entry equal to `primary`, and any
   slug appearing in BOTH lists (it cannot be an AND and an OR - flag it for review).

## 4. THE GOLDEN GATE - run this BEFORE the full pass

A wrong mapping is schema-valid, plausible, and silently corrupts mastery. No validator can
catch it. So measure first:

> ⛔ **THE GOLDEN SET IS NOT YOURS TO WRITE.** If `golden.json` does not already exist,
> **STOP and tell the owner to create it.** Generating it yourself - or deriving it from
> your own output, or "sanity-checking" it against your labels - measures self-consistency,
> which is ~100% at temperature 0 and means nothing. **A reported agreement of 100%, or of
> 98%+, is proof the gate was contaminated, not proof the mapping is good.** Two expert
> teachers do not agree 100% on primary concept; the disagreements ARE the signal. Failed
> this way on the first attempt (2026-07-21) - a self-graded 100/100 hid ~1,350 mis-binned
> problems.

1. The owner hand-labels **100 problems** (stratified: ~35 easy / 40 medium / 25 hard, spread
   across patterns), writing only `primary`, into `content/leetcode-catalog/golden.json`.
   Do this WITHOUT looking at model output.
2. Run this prompt on those same 100, blind.
3. Report: exact-primary agreement %, the confusion list (every disagreement as
   `id | human | model | model reason`), and agreement split by the model's own confidence
   band.

**Pass = 85%+ agreement on `high`-confidence rows.** Below that, the vocabulary or this
prompt is wrong - fix it and re-run the gate. Do NOT proceed to the full 3,999.

The confusion list is the more valuable output either way: a slug pair the model keeps
swapping is a genuinely confusable concept pair, which feeds the discriminating-card
contract (spec §6, `discriminates_from`).

## 5. FULL PASS OUTPUT - `content/leetcode-catalog/mapping.v1.json`

```json
{
  "mapping_version": "v1",
  "catalog_version": "v1",
  "model": "<exact model id>",
  "prompt_version": "1",
  "generated_at": "<ISO-8601 UTC>",
  "counts": {"mapped": 0, "out_of_scope": 0, "high": 0, "medium": 0, "low": 0},
  "mappings": [
    {"external_id": 1, "primary": "hash-tables", "supporting": ["frequency-counting"], "alternatives": [],
      "confidence": "high", "reason": "hash map gives O(1) complement lookup",
      "reviewed_by": null}
  ]
}
```

`reviewed_by` is always `null` from you - only a human sets it. Per spec §3.2, `low`-band
rows seed nothing, and no machine-only row produces cards or drives concept surfacing until
reviewed.

**`alternatives` health check:** most problems have none. Expect **10-25%** of mapped
problems to carry at least one. If it comes back near 0%, the model ignored the field; if
it comes back over 40%, it is listing slower variants of the same idea as "alternatives"
(brute force is not an alternative) - both are failed runs.

**AUTHENTICITY CHECKS - these detect a rule engine wearing a model's name. Run them FIRST;
if any fails, nothing else in this section is worth reading:**
- **Reason diversity.** No identical `reason` string may appear on more than **3** problems,
  and distinct reasons must exceed **60%** of mapped rows. Real per-problem reasoning is
  nearly unique; a lookup table produces dozens of clones. (2026-07-21 failure: 98 distinct
  reasons across 3,999 rows, one string repeated 449 times.)
- **Alternatives diversity.** More than **30** distinct `alternatives` combinations across
  the run. (Failure: 12.)
- **Batch accounting.** Report how many batches you processed, the batch size used, and the
  `external_id` range of each. Batches must cover the catalog with no gaps and no silent
  skips. (This replaces API-call accounting - there are no API calls in this task.)
- **Spot-check.** Print 5 random rows in full. If two problems from different families share
  a reason verbatim, the run is templated - stop.
- **Self-declaration.** State plainly in the report: "I classified these by reasoning about
  each problem" or "I used rules/heuristics for some portion" - and if any portion was
  rule-assisted, say which and how many. An honest partial run is acceptable and useful; a
  run that claims full reasoning it did not do is the one failure mode that cannot be
  recovered from downstream.

**Whole-run health checks - report these, and treat a breach as a FAILED run, not a note.
NOTE: every check below is a DISTRIBUTIONAL property and can be satisfied by hand-tuned
rules. They prove a run is not obviously broken; they never prove it is real. The
authenticity checks above are what prove that:**
- No single `primary` may exceed **8%** of mapped problems. (v1 attempt: `memoization-top-down`
  hit 396 = 10.8%, `hash-tables` 422 = 11.5% - both symptoms of averaging.)
- `low` + `medium` combined must be **>= 8%** of rows. (v1 attempt: 6.1%, with zero `low`.)
- Every free untagged problem (the JavaScript/pandas study-plan sets) must be `out_of_scope`.
  (v1 attempt: 75 of 91 were force-mapped.)
- If a slug with obvious catalog volume gets **zero** problems, the run is mis-binning, not
  the vocabulary being wrong. Check `gcd-lcm-and-modular-arithmetic` (93 number-theory
  problems), `combinatorics-and-counting` (55), `bitmask-dp` (47), `pattern-matching-kmp` (33),
  `rolling-hash-rabin-karp` (26), `ordered-sets-and-sorted-containers` (64) specifically.
  Teaching-scaffold slugs at zero are EXPECTED and fine.

**Also write `content/REPORT-leetcode-mapping.md`:** golden-gate numbers, confidence
distribution, out-of-scope count vs the ~200 expected (94 database + 91 JS/pandas + shell +
concurrency), the 15 most-used and 15 least-used slugs, every vocabulary slug that received
ZERO problems (a concept with no problems is a signal - either the vocabulary is wrong or
the prompt is blind to it), and any batch you parked.

---

## 6. PASS 2 - teaching_role curation (SEPARATE RUN, do not merge into pass 1)

Spec §3.2.-1 adds `teaching_role` / `order_in_concept` / `assumes`. **Do not ask for these
in the same call as classification.** Pass 1 already failed once by averaging under load;
adding three curation fields across 3,999 problems makes that worse, and these fields only
matter for a small subset.

Scope pass 2 to **candidates only**: for each concept node, the ~8 mapped problems with the
lowest `external_id` among `high`-confidence rows (older problems are the ones the canon
formed around). That is roughly 120 nodes x 8 = ~950 problems, not 3,999.

For each candidate return:
- `teaching_role` - `canonical` | `practice` | `variant` | `synthesis`
- `order_in_concept` - integer, 0 = the first problem a learner should meet
- `assumes` - slugs required BEYOND the primary (empty is the good answer for `canonical`)

Rules:
- Propose **at most 2 `canonical` per node**. A node with zero good canonical candidates is
  a real finding - report it rather than promoting a weak one.
- `canonical` requires: empty `assumes`, easy or medium difficulty, and a solution that
  demonstrates the concept in its plainest form. A clever problem is never canonical.
- `synthesis` = genuinely needs 2+ concepts (its `supporting` is load-bearing). These are
  never canonical.
- `variant` = a twist that breaks a naive application of the pattern (duplicates allowed,
  negatives, in-place required, huge input). These are the highest-value source for §6
  edge-case cards - flag what the twist IS in `reason`.

**`canonical` is a curation judgment, not a classification.** Every proposed `canonical`
row ships with `reviewed_by: null` and MUST be human-approved before it produces any card.
Output to `content/leetcode-catalog/pedagogy.v1.json`, same envelope conventions as §5.
