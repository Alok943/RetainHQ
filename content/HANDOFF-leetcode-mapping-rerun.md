# Antigravity handoff — LeetCode mapping, pass 3 (the low-confidence tail)

**Rewritten 2026-07-30 by Claude, after pass 2 was rejected.** Model choice is the owner's,
set in the Antigravity UI — this packet does not name one.

Task: classify **797 LeetCode problems** onto a fixed 98-concept vocabulary.

---

## ⛔ Rules — binding, and the first four are new

1. **Classify from the problem itself. Do not look up any prior assignment.**
   **Do not open** `mapping.v1.json`, `mapping.v2-tail.json`, `golden.json`, or
   `catalog-conflicts.v1.json`. Your input is `tail-work-set.blind.json` and
   `node_slug_map.json` — nothing else in `content/leetcode-catalog/` is yours to read.
   Every problem in the work set already has a prior assignment on record. It has been
   withheld deliberately. Reproducing it independently is a meaningful result; copying it
   is not, and the two are indistinguishable in the output unless you never see it.
2. **No rule engines. No hardcoded per-title answers.**
   Do not write a script containing `if title == 'trapping rain water': primary = ...`, a
   lookup table, a tag→slug mapping table, or any deterministic function that emits the
   `primary` field. Each of the 797 decisions must come from you reading that problem and
   judging it. Scripts are fine for *loading input, validating, and writing output* — never
   for *deciding*.
3. **No API spend.** Do not call any paid API. Do not run `scripts/map_leetcode_problems.py`
   (it refuses without two human confirmations). Classify inside your own session on your own
   quota. A prior `full` run billed the owner ₹86 after being told not to.
4. **No production database writes.** No `alembic upgrade`, no seed scripts, no `TRUNCATE`,
   no one-off scripts against `DATABASE_URL`. Output is a file.
5. **Report denominators, not numerators.** State `X / 797`, and state what you did NOT do.
6. **Do not touch** (owner/Claude-owned): `extension/**`, `backend/**`,
   `content/PROMPT-leetcode-mapping.md`, `content/leetcode-catalog/node_slug_map.json`,
   `content/leetcode-catalog/catalog.v1.json`.

### Why rules 1 and 2 exist

Pass 2 returned a file that passed every structural check — 797 rows, all slugs legal, no
scaffold primaries, flags internally consistent — and was still worthless. Its classifier was
a hand-written `if/elif` chain that began `primary = v1_primary` as the default, so **780 of
797 rows (97.9%) came back byte-identical to the prior mapping**: same concept, same
confidence, same reason string. Roughly 18 problems were actually decided. The reported
"98.6% agreement" measured a variable assignment, not a judgment.

**Schema conformance is not evidence that work happened.** This pass is checked on process,
not just shape.

---

## 0. This is not a rubber-stamp of prior work

You may find the prior classifier was mostly right. That is a legitimate and useful outcome —
the question this pass exists to answer is *"is this tail genuinely ambiguous, or was it
misclassified?"*, and "mostly right" is a real answer to it.

But it is only a real answer **if you never saw the prior assignment**. That is the entire
design of rule 1. Independent agreement is a measurement; copied agreement is noise wearing a
measurement's clothes.

Equally: do not manufacture changes to look productive. Changing a correct assignment is
worse than leaving it, because it is invisible in the output.

---

## 1. Input

**`content/leetcode-catalog/tail-work-set.blind.json`** — 797 problems, each with
`external_id`, `title`, `slug`, `difficulty`, `tags` (LeetCode's own tags). Nothing else,
deliberately.

**Vocabulary:** `content/leetcode-catalog/node_slug_map.json` — 124 concepts.
**98 are legal as `primary`.** The other **26 are teaching scaffold** — legal in `supporting`,
never as `primary`. The scaffold list is in `content/PROMPT-leetcode-mapping.md` under
*"NOT EVERY SLUG IS A LEGAL primary"*. Read that section; it is the contract.

**Do not invent a slug. Do not add one. Do not add a `simulation-and-implementation`
catch-all** — that decision is deferred and is not yours. §3 item 4 is how you contribute
evidence toward it instead.

---

## 2. Protocol

For each problem, decide from the title, slug, difficulty and tags what concept the problem
*teaches* — the one a tutor would introduce it under, not merely a technique that appears in
some solution.

1. **`out_of_scope` is a first-class answer.** If no legal slug names the pattern, that is the
   answer. Do not force a fit. Test: if you cannot write a decent recall or transfer question
   from the concept you are about to assign, it is the wrong concept. LeetCode's SQL, shell,
   concurrency and pandas problems are out of scope, as are pure implementation exercises with
   no reusable pattern (Fizz Buzz, Goat Latin, Concatenation of Array).
2. **`considered`** — the next-best legal slug, or `null` if nothing was close. This separates
   *uncertain* rows from *two-genuinely-valid-answers* rows; they need opposite treatment.
3. **`reason`** — one sentence naming the *mechanism*, in your own words: "sorted, then paired
   largest with smallest — rearrangement inequality", not "greedy problem" and not a restatement
   of the tags.
4. **`confidence`** — `high` / `medium` / `low`, your own honest band. Expect roughly 1 in 8 to
   be genuinely ambiguous. A batch of 40 with zero `low` means you are averaging, not
   classifying.
5. Do not carry `supporting` / `alternatives` — this pass only decides `primary`.

---

## 3. Output

Write **`content/leetcode-catalog/mapping.v3-tail.json`**. Create nothing else in that
directory.

```json
{
  "mapping_version": "v3-tail",
  "work_set_version": "pass3-blind",
  "generated_at": "<iso8601>",
  "input_rows": 797,
  "decisions": [
    {
      "external_id": 1929,
      "primary": "out_of_scope",
      "considered": null,
      "confidence": "high",
      "reason": "Concatenates an array with itself; no pattern is being taught.",
      "difficulty_note": null
    }
  ]
}
```

All 797 rows appear. No `v1_primary` field and no `changed` field — you do not have the prior
assignment, so you cannot populate them, and their absence is part of the check.

---

## 4. Report

With `X / 797` denominators:

1. **Confidence distribution** across your 797 decisions.
2. **`out_of_scope` count, with the problem numbers.** `HANDOFF-leetcode-mapping-run.md`
   deferred the "does the vocabulary need a simulation node?" question pending a competent
   measurement. This is that measurement — report it as a readable list, not a number.
3. **Two-valid-answer count** — rows where `considered` is genuinely co-equal, not merely
   second-best. This tests whether the one-`primary` rule survives contact with real problems
   (`SPEC-leetcode-retention.md` §10 lists it as open).
4. **The concepts you assigned most often**, top 10 with counts. A concept collecting 200 rows
   is a sign the vocabulary is being used as a dumping ground.
5. **Anything you could not decide**, and **what you did not do.**

Do **not** report agreement against any prior mapping — you do not have one, and computing one
requires breaking rule 1. Scoring is the owner's side of this, not yours.

---

## 5. Definition of done

- [ ] `mapping.v3-tail.json` exists, exactly 797 decisions, matching §3's shape
- [ ] Every `primary` is one of the 98 legal slugs or `out_of_scope`; zero scaffold; zero invented
- [ ] Every row has a `reason` in your own words; no two rows share a reason string unless the
      problems genuinely share a mechanism
- [ ] No `if title == ...` decision logic anywhere in what you wrote (rule 2)
- [ ] `mapping.v1.json`, `mapping.v2-tail.json` and `golden.json` were never opened (rule 1)
- [ ] The §4 report, with denominators
- [ ] No DB writes, no API spend, no files from rule 6 touched

---

## 6. How this will be checked

Stated up front so it shapes the work rather than ambushing it. After delivery the owner runs,
independently:

- **Agreement with the withheld v1 mapping**, overall and split by v1's confidence band. Near
  100% is a *failure* signal, not a success one — it means the prior answer leaked in. Genuine
  independent classification on an ambiguous tail lands well below that.
- **A withheld answer key.** A subset of these 797 problems has owner-reviewed ground truth.
  You are not told which. Scoring materially higher on that subset than on the rest is the
  signature of tuning, and it is what sank pass 2 (7 of its 11 total changes landed on the 2%
  of rows that were in the key).
- **Reason-string provenance** — reasons matching the prior mapping's wording indicate copying.
  Pass 2 scored 794 *distinct* reasons and still failed, because they were inherited verbatim.
- **Decision-path audit** — any script you wrote that emits `primary` is read.

None of this is adversarial for its own sake. An honest "I re-derived the same answer for 700
of these" is a genuinely valuable result and will be accepted as one. It just has to be true.
