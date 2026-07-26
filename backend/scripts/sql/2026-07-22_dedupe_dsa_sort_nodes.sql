-- Deduplicate two DSA concept nodes created by the 2026-07-21 "Advanced" seed pass.
-- RUN BY THE OWNER against prod. Verified safe 2026-07-22: all four nodes below have
-- 0 user_progress, 0 learning_events, 0 activities, 0 node_mastery, 0 prerequisite edges.
--
-- Why: seed_dsa.py added "Quicksort & partition" while "Quick sort" already existed with
-- an IDENTICAL description, and "Non-comparison sorts" while "Counting sort" already
-- existed (the former subsumes the latter). Two nodes meaning one concept is exactly the
-- vocabulary pollution the closed-set rule exists to prevent - the mapper would split
-- problems across both. The mapping vocabulary uses the surviving names.
--
-- seed_dsa.py has already been updated to match: the two originals are removed and the
-- survivors moved out of the generic "Advanced" phase, so a reseed reproduces this state.

BEGIN;

-- 1. Survivors move into the sorting phase (they were seeded under a generic "Advanced").
UPDATE roadmap_nodes SET phase = 'Sorting — Divide & Conquer', section = 'Efficient'
WHERE id = '3a4500e2-0991-463e-ae9e-3135c14a0431';  -- Quicksort & partition

UPDATE roadmap_nodes SET phase = 'Sorting — Divide & Conquer', section = 'Non-comparison'
WHERE id = '31d3886b-7002-4ac9-af7c-a99d29dea770';  -- Non-comparison sorts

-- 2. Drop the superseded originals.
DELETE FROM roadmap_nodes WHERE id = 'fb06fc57-f023-4396-b717-4e3fd5b170f5';  -- Quick sort
DELETE FROM roadmap_nodes WHERE id = 'b9669f92-d550-4321-a61a-d6fccf3cf7cd';  -- Counting sort

-- 3. Verify BEFORE committing. Expect: dsa_nodes = 124, dupes = 0.
--    124 nodes == 124 vocabulary slugs, 1:1, which is what the importer now requires.
SELECT count(*) AS dsa_nodes FROM roadmap_nodes rn
  JOIN roadmaps r ON r.id = rn.roadmap_id WHERE r.slug = 'dsa';
SELECT count(*) AS dupes FROM roadmap_nodes rn
  JOIN roadmaps r ON r.id = rn.roadmap_id
  WHERE r.slug = 'dsa' AND rn.title IN ('Quick sort', 'Counting sort');

COMMIT;
-- ROLLBACK;  -- use this instead if the counts above are not 124 / 0
