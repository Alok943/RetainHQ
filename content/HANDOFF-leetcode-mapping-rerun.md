# Antigravity handoff — LeetCode mapping, pass 3 (the low-confidence tail)

**Written 2026-07-30 by Claude.** Model choice is the owner's, set in the Antigravity UI —
this packet does not name one and no instruction here should be read as recommending one.

Scope: re-classify the **797 mapped rows that v1 self-labelled `medium` or `low`**. The `high`
band is out of scope and must not be touched.

---

## ⛔ Rules — inherited verbatim from `HANDOFF-leetcode-mapping-run.md`, all still binding

1. **No API spend.** Do not call any paid API. Do not run `scripts/map_leetcode_problems.py`
   (it refuses without two human confirmations). Classify inside your own session on your own
   quota. A prior `full` run billed the owner ₹86 after being told not to.
2. **No production database writes.** No `alembic upgrade`, no seed scripts, no `TRUNCATE`, no
   one-off scripts against `DATABASE_URL`. Output is a **file**. If a DB change is needed, write
   the SQL to a file and hand it to the owner.
3. **No self-grading.** `content/leetcode-catalog/golden.json` is owner-reviewed. Never
   regenerate it, never derive it from your own output. A reported agreement of 98%+ is evidence
   of contamination, not quality.
4. **Report denominators, not numerators.** State `X / 797` for everything, and state what you
   did NOT do.
5. **Do not touch** (owner/Claude-owned): `extension/**`, `backend/app/**`,
   `backend/scripts/import_leetcode_catalog.py`,
   `backend/scripts/fix_scaffold_primaries_in_mapping.py`,
   `content/PROMPT-leetcode-mapping.md`, `content/leetcode-catalog/node_slug_map.json`,
   `content/leetcode-catalog/golden.json`, `content/leetcode-catalog/catalog.v1.json`.

---

## 0. Read this before deciding the task is easy

**v1 was not produced by a weak model.** `mapping.v1.json` records
`"model": "gemini-3.1-pro"`. An independent audit of 32 stratified rows on 2026-07-30 found:

| v1 self-labelled | audited quality |
|---|---|
| `high` | 12/14 clearly correct, 0 wrong |
| `medium` | ~6/10 correct |
| `low` | ~2/8 correct |

The conclusion that matters: **v1's confidence labels were well calibrated.** The model knew
which ones it had got right. So this is *not* a "run it again on something smarter" task — a
straight re-run of the same prompt is likely to reproduce the same answers, and if it does, that
is the finding, not a failure.

The tail is low-quality for reasons capability does not fix:

- **Genuinely homeless problems.** Some LeetCode problems are implementation/simulation
  exercises with no pattern to name (Fizz Buzz, Goat Latin, Truncate Sentence). The vocabulary
  has no home for them **by design**. The correct answer is `out_of_scope`, and a model pushed to
  always produce a concept will invent one instead.
- **The one-primary rule.** Some problems genuinely have two equally canonical approaches. The
  schema permits exactly one `primary`; that constraint, not the classifier, is what makes those
  rows uncertain.
- **Thin input.** v1 classified from title + LeetCode tags only.

So the job is a **stricter protocol on the same task**, and an honest measurement of how much of
the tail is fixable at all.

---

## 1. Input

`content/leetcode-catalog/mapping.v1.json` — already patched to `mapping_version: v1.1`
(66 teaching-scaffold `primary` violations were repaired on 2026-07-30; do not re-litigate them).

Select your work set with exactly this rule:

```
rows where primary NOT IN (null, "out_of_scope") AND confidence IN ("medium", "low")
```

That is **797 rows** as of v1.1 (687 medium + 110 low). Report the count you actually loaded; if
it is not 797, stop and say so rather than proceeding.

Vocabulary: `content/leetcode-catalog/node_slug_map.json`, **124 concepts, unchanged**.
**98 are legal as `primary`.** The other 26 are teaching scaffold — legal in `supporting`,
never as `primary`. The list is in `content/PROMPT-leetcode-mapping.md` §"NOT EVERY SLUG IS A
LEGAL primary". **Do not invent a slug. Do not add one. Do not add a
`simulation-and-implementation` catch-all** — that decision is deferred and is not yours; §4 is
how you contribute evidence to it instead.

---

## 2. Protocol — what is different from v1

For each row, produce a decision under these constraints:

1. **`out_of_scope` is a first-class answer, not a failure.** If no legal slug names the pattern,
   that is the answer. Do not force a fit. Rule of thumb: if you cannot write a decent recall or
   transfer question from the concept you are about to assign, it is the wrong concept.
2. **Name the runner-up.** Every decision records `considered`: the next-best legal slug, or
   `null` if nothing else was close. This is the field that tells the owner whether a row is
   *uncertain* or genuinely *two-valid-answers*, and those need opposite treatments.
3. **`reason` is one sentence naming the mechanism**, not the tag. "Sorted then paired
   largest-with-smallest, rearrangement inequality" — not "greedy problem".
4. **Confidence is your own honest band** (`high` / `medium` / `low`). v1's calibration was good;
   match it. If a batch of 40 comes back with zero `low`, you are averaging, not classifying.
5. **Do not read the v1 answer before deciding.** Classify from the problem, then compare. If you
   condition on v1 you will mostly reproduce it and the exercise measures nothing.
6. Leave `supporting` / `alternatives` alone unless your `primary` changes make them wrong.

---

## 3. Output

Write **`content/leetcode-catalog/mapping.v2-tail.json`**. Do not modify `mapping.v1.json`.

```json
{
  "mapping_version": "v2-tail",
  "based_on": "v1.1",
  "generated_at": "<iso8601>",
  "input_rows": 797,
  "decisions": [
    {
      "external_id": 1929,
      "v1_primary": "arrays-and-memory",
      "primary": "out_of_scope",
      "considered": null,
      "confidence": "high",
      "reason": "Concatenate an array with itself; no pattern is being taught.",
      "changed": true
    }
  ]
}
```

`changed` is `primary != v1_primary`. Every one of the 797 rows appears, including unchanged ones.

---

## 4. The measurement — this is the deliverable, not the file

Report all of these with `X / 797` denominators:

1. **Agreement with v1**: how many rows you left unchanged, split by v1's medium vs low band.
2. **Where the changes went**: how many moved to a different legal concept vs. to `out_of_scope`.
3. **Golden-set score**: run your protocol blind on the rows that appear in
   `content/leetcode-catalog/golden.json`, report agreement, and **report it separately** from
   everything else. This is the only externally-valid number in the report. Do not tune against it.
4. **The homeless count and list.** How many of the 797 you sent to `out_of_scope` because no
   legal concept fit, with the problem numbers. `HANDOFF-leetcode-mapping-run.md` deferred the
   "does the vocabulary need a simulation node?" decision pending exactly this measurement from a
   competent run. **This is that measurement.** Report it as a list the owner can read, not a
   number.
5. **Two-valid-answer count**: rows where `considered` is a genuinely co-equal approach. This
   tests whether the one-`primary` rule survives contact with real problems — an open question in
   `SPEC-leetcode-retention.md` §10.
6. **What you did not do**, and any row you could not decide.

**If your agreement with v1 is high (say >80% on the medium band), say so plainly and stop.**
That is a valid, useful result: it means the tail is genuinely ambiguous rather than
misclassified, and the owner should spend review time on it rather than another re-run. Do not
manufacture changes to look productive.

---

## 5. Definition of done

- [ ] `mapping.v2-tail.json` exists, contains exactly 797 decisions, valid against §3's shape
- [ ] Zero `primary` values outside the 98 legal slugs + `out_of_scope`
- [ ] Zero invented slugs; `node_slug_map.json` untouched
- [ ] The §4 report, with denominators, including the homeless list
- [ ] Golden-set score reported separately and not tuned against
- [ ] No DB writes, no API spend, no files from §5 of the rules touched

The owner reviews `mapping.v2-tail.json` before anything is imported. Nothing here reaches
production without that pass.
