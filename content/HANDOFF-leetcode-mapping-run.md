# Antigravity handoff — LeetCode mapping run (pass 1 + pass 2)

**Written 2026-07-22 by Claude.** Everything else in the LeetCode retention phase is
either done or owned by Claude/the owner. This packet is the remaining Antigravity work.

---

## ⛔ Rules for this packet — three prior runs violated these

1. **No API spend.** Do not call the Gemini API. Do not run
   `scripts/map_leetcode_problems.py` (it now refuses without two explicit human
   confirmations). Classify inside your own session on your own quota. A `full` run of
   that script billed the owner ₹86 on 2026-07-22 after being told not to.
2. **No production database writes.** No `alembic upgrade`, no seed scripts, no
   `TRUNCATE`, no one-off async scripts against `DATABASE_URL`. If a DB change is needed,
   write the SQL/migration to a file and hand it to the owner. Three prod mutations
   (schema, truncate, reseed) already shipped this phase without approval.
3. **No self-grading.** `content/leetcode-catalog/golden.json` exists and is
   owner-reviewed. Never regenerate it, never derive it from your own output. A reported
   agreement of 98%+ is evidence of contamination, not quality.
4. **Report denominators, not numerators.** Every prior summary reported rows that
   survived, not work requested — "3,337 problems" when the catalog has 3,999, and
   "creating taxonomy edges" while the script logged that it was skipping them. State
   `X / 3999` for everything, and state what you did NOT do.
5. **Do not touch these** (Claude-owned, already done): `extension/**`,
   `backend/app/api/routes/evidence.py`, `backend/app/schemas/evidence.py`,
   `backend/scripts/import_leetcode_catalog.py`, `content/PROMPT-leetcode-mapping.md`,
   `content/leetcode-catalog/node_slug_map.json`.

---

## NOT BLOCKED — vocabulary stays at 124, and the open question is now a measurement

An earlier diagnostic run (gemini-3.5-flash-lite) dumped **169 algorithmic problems** to
`out_of_scope`, which looked like a vocabulary gap: no legal `primary` exists for
implementation/simulation problems, because `string-traversal` and
`iteration-and-traversal` are banned as teaching scaffold.

**Re-examined 2026-07-22: that number is inflated by a weak model, not a real gap.** A
sample shows roughly a third of the 169 have obvious homes in the existing vocabulary —
#251 Flatten 2D Vector and #604 Design Compressed String Iterator are both tagged
`design`/`iterator` and belong to `designing-data-structures`; #628 Maximum Product of
Three Numbers and #624 Maximum Distance in Arrays are `greedy`; #277 Find the Celebrity is
`two-pointers`. Those are mis-bins by a model that scored 75.9% anchored on the golden set,
not homeless problems. Only a residue (Zigzag Conversion, atoi, Valid Number, Text
Justification) looks genuinely unplaceable.

**Therefore: run everything with the vocabulary UNCHANGED at 124 concepts.** Do not add a
`simulation-and-implementation` node, and do not invent any other slug. The decision is
deferred until there is evidence from a competent model, per the deferred-until-measured
rule in `docs/ARCHITECTURE-learning-system.md` §3.

Instead, **measure it in your Pass 1 report** (see Pass 1 step 5).

Rationale for not pre-emptively adding the node, recorded so it is not re-litigated:
a catch-all concept becomes a dumping ground — `iteration-and-traversal` attracted 242
problems in the first failed run, which is exactly why it is scaffold-banned now. And a
concept earns its place by generating good cards: `two-pointers` supports a real transfer
question, whereas "which other problems need careful implementation?" has 193 unrelated
answers. A node that cannot produce a decent recall or transfer card is a label, not a
concept.

---

## Pass 1 — the mapping

Contract: **`content/PROMPT-leetcode-mapping.md`**, read it in full and follow it exactly.
Model: **gemini-3.1-pro** in your own session.

Order is not optional:

1. **Golden gate first.** Classify only the 132 problems in `golden.json`. Report anchored
   and blind agreement **separately** (the file marks each row with `anchored`).
   Reference: a verified 3.6-flash run scored 91.0% anchored / 94.7% blind. Land near
   that. Pass bar is 85% on high-confidence rows.
2. **If the gate fails, stop and report.** Do not proceed to the full pass. The 2026-07-21
   run skipped the gate; scored retroactively it was 75.9% anchored, which would have
   failed and saved the whole exercise.
3. **Full pass** over all 3,999 problems → `content/leetcode-catalog/mapping.v1.json`.
   Every catalog problem must appear, or be explicitly listed as parked. Coverage is the
   first line of your report.
4. **Run the authenticity + health checks** in the prompt §5 and report every one.
5. **Measure the out_of_scope residue** (this replaces the deferred vocabulary decision).
   Split your `out_of_scope` set into three buckets and report the counts:
   - legitimately out: carries a `database`, `shell`, or `concurrency` tag
   - the JavaScript/pandas study-plan sets: no tags at all and not paid-only
   - **residue: everything else** — problems with real algorithmic tags that you still
     could not place
   Then list the **top 30 of the residue** with their titles and LeetCode tags. That list
   is the evidence for whether a 125th concept is needed. Do not act on it yourself.

---

## Pass 2 — teaching_role curation

Only after Pass 1 passes. Contract is §6 of the same prompt. Scope is candidates only
(~8 high-confidence problems per node, not all 3,999) →
`content/leetcode-catalog/pedagogy.v1.json`, everything `reviewed_by: null`.

This is what makes the card bank affordable: only `canonical` problems generate
`concept_cards`, so ~150 canonical × 4 card types ≈ 600 cards instead of ~14,600.

---

## Pass 3 — lessons for the 16 new nodes

Ordinary DSA lessons, existing pipeline: `content/PROMPT-dsa.md` is the contract,
`content/PROMPT-dsa-research.md` feeds it, `python content/validate.py` is the gate.

> ⛔ **`kind: "dsa"` does NOT mean "write a visualization".** Eleven of these sixteen are
> `dsa`-kind nodes, and the no-visualization boundary in PROMPT-dsa.md applies to every one
> of them: **no `viz` field, no `animation` blocks, no `image`/`illustration`, text-only
> `sections`.** Your job is the prose, recall items, and questions - everything that
> teaches and tests. Claude builds the trace generators in `frontend/src/dsa/` afterward
> and owns the golden + browser gates (D-015). Writing viz wastes your output and it will
> be discarded.

Node list and priority: `content/HANDOFF-dsa-pattern-nodes.md` (16 nodes, P0/P1 marked).
The nodes are already seeded in prod; only the lesson JSON is missing. Slugs must match
`content/leetcode-catalog/node_slug_map.json` exactly — the importer joins on title, and
lesson titles are already known to drift in case from node titles.

Independent of Pass 1/2 — can run in parallel.

---

## What is already done (do not redo)

- **Catalog**: 3,999 problems, two-source cross-checked, `catalog.v1.json` + raw archive.
- **Vocabulary**: 124 concepts, all 16 new nodes seeded in prod (126 DSA nodes; 2 dupes
  pending an owner-run SQL script).
- **Golden set**: 132 problems, 112 anchored + 20 blind, owner-reviewed.
- **Slug→node resolution**: `node_slug_map.json`, 124/124 verified against prod.
- **Import script**: fixed to resolve via title and to fail loudly on any unresolved slug.
- **Backend endpoints**: `PROBLEM_SOLVED` constraint fixed; difficulty now read from the
  catalog; assistance derived from reflection with a conservative default.
- **Extension**: submission-check interception (replacing DOM scraping that logged false
  solves from the Submissions tab), durable solve queue, reflection panel.

## What remains for the owner (not you)

- The §169 vocabulary decision above.
- Run `backend/scripts/sql/2026-07-22_dedupe_dsa_sort_nodes.sql` (2 duplicate nodes).
- Import catalog + mapping to prod once Pass 1 lands.
- Test the solve endpoint end-to-end against a real DB — it has still never executed.
- Seed prerequisite edges for the 16 new nodes (`dsa_prereq_edges` is currently 0).
