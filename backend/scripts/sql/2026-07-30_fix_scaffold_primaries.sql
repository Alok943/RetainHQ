-- Fix the 66 `role='primary'` rows that point at TEACHING-SCAFFOLD nodes.
--
-- content/PROMPT-leetcode-mapping.md:120 lists 26 scaffold slugs and states:
--   "They may appear in `supporting`, NEVER as `primary`. Choosing one is always
--    wrong; if nothing else fits, the answer is `out_of_scope`."
-- The v1 mapping run violated it 66 times, 28 of them at confidence 0.9 — i.e.
-- inside the band the Log-Activity concept chip auto-fills without asking
-- (docs/IMPLEMENTATION-leetcode-log-capture.md §6, §6.1).
--
-- Reclassified 2026-07-30 by Claude (Opus 5) against the 98 legal slugs, using
-- problem title + LeetCode tags + the existing supporting/alternative rows.
-- NOT owner-reviewed: rows are stamped `reviewed_by='claude-opus-5:scaffold-fix'`,
-- deliberately NOT 'human' — promoting them to 'human' is the owner's call after
-- a spot-check, and content/HANDOFF-leetcode-mapping-run.md rule 3 forbids an
-- agent grading its own output.
--
-- 40 rows reassigned to a legal concept · 26 rows deleted (no legal primary
-- exists — see the note at the bottom, it is evidence for a deferred decision).
--
-- Deleting leaves the problem UNMAPPED, which is exactly how the other ~1,055
-- unmapped problems are already represented. `role='out_of_scope'` is NOT used:
-- problem_concepts.node_id is NOT NULL, so an out_of_scope row cannot exist
-- without a schema change, and there are 0 such rows today.
--
-- APPLY: psql "$DATABASE_URL" -f this_file.sql
-- Idempotent: re-running is a no-op (the scaffold rows are gone after pass 1).

BEGIN;

-- ---------------------------------------------------------------------------
-- 0. The 26 scaffold node titles, by title — roadmap_nodes has no slug column
--    (node_slug_map.json note: "title is the only join key").
-- ---------------------------------------------------------------------------
CREATE TEMP TABLE _scaffold(title text PRIMARY KEY) ON COMMIT DROP;
INSERT INTO _scaffold(title) VALUES
  ('Amortized analysis'),('Arrays & memory'),('Base case'),('Big-O notation'),
  ('Brute force first'),('Common complexities'),('Counting operations'),
  ('Graph representations'),('Hash sets vs maps'),('In-place operations'),
  ('Iteration & traversal'),('Linear search'),('Logarithms & powers of two'),
  ('Optimal substructure'),('Overlapping subproblems'),('Pattern recognition drill'),
  ('Precomputation'),('Recognizing divide & conquer'),('Recognizing graph problems'),
  ('Recognizing greedy vs DP'),('Recognizing sliding window'),('Recognizing two pointers'),
  ('String traversal'),('The call stack'),('Tracing state & invariants'),
  ('What is an algorithm?');

-- ---------------------------------------------------------------------------
-- 1. Reassignments: (leetcode number, new primary node title, confidence)
-- ---------------------------------------------------------------------------
CREATE TEMP TABLE _fix(external_id int PRIMARY KEY, node_title text, confidence float) ON COMMIT DROP;
INSERT INTO _fix VALUES
  ( 271, 'Designing data structures',      0.9),  -- Encode and Decode Strings — design/serialize
  ( 280, 'Why greedy works',               0.9),  -- Wiggle Sort — one-pass swap greedy
  ( 319, 'Combinatorics & counting',       0.6),  -- Bulb Switcher — count perfect squares
  ( 326, 'GCD, LCM & modular arithmetic',  0.9),  -- Power of Three — 3^19 % n trick
  ( 349, 'Hash tables',                    0.9),  -- Intersection of Two Arrays
  ( 356, 'Hash tables',                    0.9),  -- Line Reflection
  ( 395, 'Sliding window (variable)',      0.9),  -- Longest Substring w/ >=K Repeating
  ( 414, 'Top-K with a heap',              0.6),  -- Third Maximum Number — k=3
  ( 418, 'Memoization (top-down)',         0.6),  -- Sentence Screen Fitting — precomputed fits
  ( 427, 'Recursion tree',                 0.9),  -- Construct Quad Tree — divide & conquer
  ( 442, 'Frequency arrays',               0.9),  -- Find All Duplicates — value-as-index
  ( 448, 'Frequency arrays',               0.9),  -- Find All Numbers Disappeared — same trick
  ( 944, '2D arrays & matrices',           0.9),  -- Delete Columns to Make Sorted — column scan
  ( 985, 'Prefix sums',                    0.6),  -- Sum of Even Numbers After Queries — running agg
  ( 997, 'Frequency arrays',               0.9),  -- Find the Town Judge — indegree/outdegree count
  (1437, 'Two pointers',                   0.6),  -- All 1's at Least K Places Away — last-index gap
  (1446, 'Two pointers on strings',        0.6),  -- Consecutive Characters — longest run
  (1808, 'GCD, LCM & modular arithmetic',  0.9),  -- Maximize Nice Divisors — modpow
  (1827, 'Why greedy works',               0.9),  -- Min Ops to Make Array Increasing
  (1840, 'Why greedy works',               0.6),  -- Maximum Building Height — constraint relax
  (1846, 'Why greedy works',               0.9),  -- Max Element After Decreasing/Rearranging
  (1864, 'Why greedy works',               0.9),  -- Min Swaps Binary String Alternating
  (1874, 'Why greedy works',               0.9),  -- Minimize Product Sum — rearrangement ineq.
  (1881, 'Why greedy works',               0.9),  -- Maximum Value after Insertion
  (1899, 'Why greedy works',               0.9),  -- Merge Triplets to Form Target
  (1903, 'Why greedy works',               0.9),  -- Largest Odd Number in String
  (1909, 'Why greedy works',               0.6),  -- Remove One Element Strictly Increasing
  (1913, 'Why greedy works',               0.6),  -- Max Product Difference Between Two Pairs
  (1921, 'Why greedy works',               0.9),  -- Eliminate Maximum Number of Monsters
  (1922, 'GCD, LCM & modular arithmetic',  0.9),  -- Count Good Numbers — fast modpow
  (1927, 'Why greedy works',               0.9),  -- Sum Game
  (1936, 'Why greedy works',               0.9),  -- Add Minimum Number of Rungs
  (1946, 'Why greedy works',               0.9),  -- Largest Number After Mutating Substring
  (2860, 'Combinatorics & counting',       0.6),  -- Happy Students — count valid k
  (2864, 'Why greedy works',               0.9),  -- Maximum Odd Binary Number
  (2899, 'Stack fundamentals',             0.9),  -- Last Visited Integers — stack semantics
  (2908, 'Prefix sums',                    0.9),  -- Min Sum of Mountain Triplets — prefix/suffix min
  (2914, 'Why greedy works',               0.9),  -- Min Changes Binary String Beautiful — pair scan
  (2934, 'Why greedy works',               0.6),  -- Min Ops Maximize Last Elements — 2-case
  (2937, 'Two pointers on strings',        0.9);  -- Make Three Strings Equal — common prefix

-- ---------------------------------------------------------------------------
-- 2. Deletions: no legal primary exists. Pure implementation / simulation /
--    arithmetic-formula problems. Per the prompt, the answer is out_of_scope,
--    which here means "no mapping row".
-- ---------------------------------------------------------------------------
CREATE TEMP TABLE _drop(external_id int PRIMARY KEY) ON COMMIT DROP;
INSERT INTO _drop VALUES
  ( 412),( 434),( 806),( 824),( 831),( 833),(1427),(1816),(1822),(1828),
  (1844),(1848),(1859),(1860),(1869),(1880),(1904),(1920),(1925),(1929),
  (1933),(1945),(2855),(2942),(2951),(2960);

-- ---------------------------------------------------------------------------
-- 3. Drop every illegal scaffold primary (both buckets) FIRST, so the upsert
--    below cannot trip uq_problem_concept when a problem already carries a
--    supporting/alternative row on its new primary node (true for 7 of the 40:
--    #271, #395, #418, #427, #944, #997, #1922).
-- ---------------------------------------------------------------------------
DELETE FROM problem_concepts pc
USING roadmap_nodes n, problems p
WHERE pc.node_id = n.id
  AND pc.problem_id = p.id
  AND pc.role = 'primary'
  AND n.title IN (SELECT title FROM _scaffold)
  AND p.external_id IN (SELECT external_id FROM _fix UNION SELECT external_id FROM _drop);

-- ---------------------------------------------------------------------------
-- 4. Insert the corrected primaries; promote an existing supporting/alternative
--    row in place where one already sits on the target node.
-- ---------------------------------------------------------------------------
INSERT INTO problem_concepts (id, problem_id, node_id, role, confidence, reviewed_by, mapping_version)
SELECT gen_random_uuid(), p.id, n.id, 'primary', f.confidence,
       'claude-opus-5:scaffold-fix', 'v1.1'
FROM _fix f
JOIN problems p ON p.external_id = f.external_id AND p.source = 'leetcode'
JOIN roadmap_nodes n ON n.title = f.node_title
JOIN roadmaps r ON r.id = n.roadmap_id AND r.slug = 'dsa'
ON CONFLICT (problem_id, node_id) DO UPDATE
SET role = 'primary',
    confidence = EXCLUDED.confidence,
    reviewed_by = EXCLUDED.reviewed_by,
    mapping_version = EXCLUDED.mapping_version;

-- ---------------------------------------------------------------------------
-- 5. Verify. Both must be 0 / 40 or the transaction is rolled back by hand.
-- ---------------------------------------------------------------------------
DO $$
DECLARE illegal int; fixed int;
BEGIN
  SELECT count(*) INTO illegal
  FROM problem_concepts pc JOIN roadmap_nodes n ON n.id = pc.node_id
  WHERE pc.role = 'primary' AND n.title IN (SELECT title FROM _scaffold);

  SELECT count(*) INTO fixed
  FROM problem_concepts WHERE reviewed_by = 'claude-opus-5:scaffold-fix';

  IF illegal <> 0 THEN
    RAISE EXCEPTION 'still % scaffold primaries after fix', illegal;
  END IF;
  IF fixed <> 40 THEN
    RAISE EXCEPTION 'expected 40 reassigned rows, got %', fixed;
  END IF;
  RAISE NOTICE 'OK: 0 scaffold primaries, % rows reassigned, 26 dropped to unmapped', fixed;
END $$;

COMMIT;

-- ---------------------------------------------------------------------------
-- FINDING worth acting on — the 26 deletions are not noise.
--
-- 40% of the scaffold violations are problems with genuinely no home in the
-- 98-slug vocabulary: Fizz Buzz, Goat Latin, Truncate Sentence, Concatenation of
-- Array, Sign of the Product, Sum of Digits After Convert, Number of Lines To
-- Write String. They are implementation/simulation exercises, not pattern
-- instances. The model reached for 'String traversal' / 'Arrays & memory'
-- precisely because nothing legal fit.
--
-- content/HANDOFF-leetcode-mapping-run.md deferred exactly this decision ("do not
-- add a simulation-and-implementation node ... measure it in your Pass 1 report")
-- on the grounds that the 169 out_of_scope figure came from a weak model. This is
-- the independent measurement it asked for, and it points the same way: there is
-- a real gap, roughly a quarter of the scaffold violations, and these problems
-- are better left unmapped than force-fitted.
--
-- Recommendation: leave them unmapped. A catch-all node attracts hundreds of
-- unrelated problems (the 'iteration-and-traversal' failure, 242 problems) and
-- cannot generate a decent recall or transfer card, which is the bar the handoff
-- sets for a concept earning its place.
-- ---------------------------------------------------------------------------
