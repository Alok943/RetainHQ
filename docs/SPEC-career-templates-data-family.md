# Spec — Career templates for the data family (Data Analyst, Data Scientist, Data Engineer)

**Status:** Data Analyst is specced and authorable now · Data Scientist and Data Engineer are
**gated on the research run** (§4) · **Date:** 28 Jul 2026

**Why this exists:** `frontend/src/lib/careerPaths.js` advertises six roles; Career Coach has
templates for three (`backend`, `ai_engineer`, `sde_generalist`). The three missing ones —
Data Analyst, Data Scientist, Data Engineer — are exactly the ones `CareerPaths.jsx` renders
with a "Roadmap coming soon" badge, and the page's own meta description promises
*"Data Analyst→Data Engineer."* This closes a truth gap rather than adding scope.

---

## 0. Is deep research required? Split answer.

**No for Data Analyst.** Evidence already exists locally and is sufficient:
- `careerPaths.js` treats DA as a **source** role in two shipped paths (`da-de`, `da-ds`) and
  states its transferable strengths outright: *"SQL + business intuition transfer directly."*
- The DA→DE entry names the DA-side filter precisely: *"SQL depth is the first-round filter
  (200-line production queries, not textbook)."*
- DA is the most stable and least vendor-churned of the three (SQL, stats, spreadsheets, one
  BI tool). Nothing in it has moved enough since the last JD runs to need re-verification.
- DA is entry-level by definition, so the "do fresher roles exist at volume?" framing question
  that blocks DE (below) doesn't arise.

**Yes for Data Engineer — and this is not my call, it's already recorded.**
`SPEC-career-templates-v2.md` §8 states the research prompt is *"required before the
data_engineer template"* and gives the load-bearing reason:

> *"For Data Engineer: establish whether fresher DE roles in India genuinely exist at
> meaningful volume, or whether the realistic entry path is backend/analyst → DE; the tree's
> framing depends on the answer."*

That answer changes the **shape** of the template, not its details — a "first job" tree and a
"transition from analyst/backend" tree have different roots, different priorities, and
different diagnostic probes. Authoring before knowing is authoring the wrong tree.

**Yes for Data Scientist**, same class of risk: "Data Scientist" is a heavily inflated title in
the Indian fresher market (many DS-titled roles are analyst work), so the same
does-this-role-exist-at-this-level question applies. Add it to the run rather than guessing.

**Do not commission a new research run.** §8 of `SPEC-career-templates-v2.md` already holds a
complete, source-ranked prompt. §4 below is a small addendum to it, not a replacement.

---

## 1. The shared decision: templates stay self-contained; accept catalog duplication

Each data template authors **its own** SQL / Python / stats nodes rather than deferring shared
foundations to attached catalog roadmaps.

This looks wrong (it duplicates concepts across templates — prod already has 102 titles
appearing in more than one roadmap, 229 rows) and is nonetheless correct here:

- **Attached roadmaps cannot receive evidence.** `candidate_nodes_for_user`
  (`topic_mapping.py:114-132`) scopes to `personal_ids + [goal.roadmap_id]`, so an attached
  catalog roadmap is never a topic-mapping or companion-classification target, and its
  `node_meta.embedding` is NULL. Foundations parked there would be plan-only and invisible to
  the mastery engine — the opposite of the point.
- **A user has exactly one active goal** (partial unique index `(user_id) WHERE
  status='active'`). Cross-template duplication is therefore invisible to any single user at
  any single time. It is catalog hygiene, not a UX defect.
- It becomes a real problem only when multi-career composition exists — which is precisely when
  canonical node identity would be introduced anyway. Solving it now pays for a problem that
  doesn't exist yet.

**Constraint worth recording:** `validate_career_templates.py` requires every `depends_on` to
resolve **within the same template**. Templates cannot reference each other's nodes. Any future
"compose multiple careers into one graph" work needs a layer *above* templates, not a change to
the template schema.

---

## 2. Contract every template must satisfy

Format (per `backend.v2.json`), gated by `content/validate_career_templates.py`:

```json
{
  "role_key": "data_analyst",
  "version": "v1",
  "title": "Data Analyst",
  "subjects": [
    { "key": "sql_core", "title": "SQL Foundations", "default_priority": 5,
      "nodes": [
        { "stable_key": "sql_core.select.filtering",
          "title": "SELECT, WHERE, ORDER BY",
          "est_effort_min": 45,
          "priority": 5,
          "depends_on": [],
          "diagnostic_probe": "…answerable verbally in under 2 minutes…",
          "diagnostic_answer": "…2-4 sentences…" }
      ] }
  ]
}
```

Hard gates (errors):
- Filename `<role_key>.v<N>.json`, lowercase/digits/underscores; `version` matches `v<N>`.
- `subjects` non-empty; each `default_priority` an int 1–5.
- `nodes` non-empty; each `priority` int 1–5; `est_effort_min` a positive int.
- Every `depends_on` resolves to a `stable_key` **in this file**; no cycles.

Soft gates (warnings — treat as requirements anyway):
- **60–70 total nodes.** Outside that range warns.
- **≥5 nodes carrying `diagnostic_probe` + `diagnostic_answer`** (the diagnostic draws 5–8).
- **Every subject with `default_priority >= 4` must contain at least one probe-bearing node** —
  probe selection is subject-aware round-robin, so a high-priority subject with no probes
  silently gets zero diagnostic coverage.

Node titles: ≤6 words, atomic, and **testable** — a node that can't be probed can't be
diagnosed. Career-tree nodes need **no lessons**; they are planning targets, and evidence
arrives from reviews / LeetCode / the companion.

---

## 3. `data_analyst.v1.json` — authorable now

Target **64 nodes across 8 subjects**. Priorities below are marked by provenance: **[E]** =
evidence in `careerPaths.js`, **[I]** = inferred structure, verify against frequency data in a
future v2 rather than treating as settled.

| # | subject `key` | title | `default_priority` | nodes | basis |
|---|---|---|---|---|---|
| 1 | `sql_core` | SQL Foundations | **5** | 12 | **[E]** *"SQL — your natural strength — is the #1 DE filter"* |
| 2 | `sql_advanced` | Advanced SQL | **5** | 10 | **[E]** *"200-line production queries, not textbook"* is the stated first-round filter |
| 3 | `statistics` | Statistics for Analysis | **4** | 9 | **[I]** hypothesis testing/sampling is the standard DA screen |
| 4 | `bi_dashboards` | BI & Dashboards | **4** | 8 | **[I]** one BI tool deep (Power BI **or** Tableau — pick one, don't split) |
| 5 | `spreadsheets` | Spreadsheet Analysis | **4** | 7 | **[I]** still a real DA filter in services/GCC segments — verify segment split |
| 6 | `python_analysis` | Python for Analysis | **3** | 8 | **[E]** DA→DS delta is *"Python beyond notebooks"*, so DA baseline is notebook-level pandas, **not** SWE Python |
| 7 | `data_modeling` | Data Modeling & Joins | **3** | 6 | **[E]** star/snowflake appears in the DA→DE delta, so introduce it here, don't own it |
| 8 | `analyst_craft` | Metrics & Communication | **3** | 4 | **[I]** the differentiator per *"business intuition transfer directly"* |

Authoring notes that matter:

- **`sql_advanced` carries the most priority-5 nodes.** Window functions, CTEs, query plans,
  index-aware rewriting. This is the single most load-bearing subject in the template — the
  stated filter is SQL *depth*, and a template that treats SQL as one shallow subject
  reproduces exactly the "textbook, not production" gap `careerPaths.js` warns about.
- **Do not author both Power BI and Tableau.** One tool, deep. Splitting halves the depth in
  the subject a DA is actually screened on and doubles the node count for no gain.
- **`python_analysis` stops at analysis.** No OOP, packaging, or tests — those are explicitly
  the DA→DS *delta* in `careerPaths.js`, so putting them in the DA baseline erases the
  progression the Career Paths page sells.
- **`analyst_craft` is the hardest to probe.** Keep it 4 nodes and make each one genuinely
  testable ("define a metric and its denominator", "what makes a dashboard answer a question")
  rather than unfalsifiable soft-skill nodes. If a node can't carry a probe, cut it.
- **Prerequisites within the template only**, shallow. Mirror `backend.v2`'s sparse style:
  `sql_advanced.*` depends on `sql_core.*`, `data_modeling` on `sql_core`, everything else
  roots free. Do **not** invent a dense edge graph here — prod averages 0.04 edges/node in the
  career catalog and edge authoring is its own task (BACKLOG), not this one's.
- **≥8 probe-bearing nodes**, distributed so all four `default_priority >= 4` subjects
  (`sql_core`, `sql_advanced`, `statistics`, `bi_dashboards`, `spreadsheets`) each have one.

---

## 4. Research addendum (append to `SPEC-career-templates-v2.md` §8, don't rewrite it)

That prompt already covers Backend, AI Engineer, SDE Generalist and Data Engineer. Add:

1. **Extend "ROLES TO COVER" with (5) Data Scientist and (6) Data Analyst.**
2. **Add to CONSTRAINTS:**
   - *For Data Scientist:* establish whether fresher DS roles in India exist at meaningful
     volume or whether most DS-titled fresher postings are analyst work under an inflated
     title — same framing question as Data Engineer, same consequence for the tree's shape.
   - *For Data Analyst:* the app already assumes SQL depth is the primary filter and Python is
     notebook-level only. **Verify or refute both.** Also settle the spreadsheet question with
     a segment breakdown — whether Excel is a genuine screen in IT-services/GCC and
     de-emphasized in product/startup, which decides whether `spreadsheets` deserves
     `default_priority` 4 or 2.
   - *For Data Analyst:* confirm which single BI tool dominates fresher postings in India
     (Power BI vs Tableau), since §3 authors exactly one.
3. **Attach `data_analyst.v1.json`'s subject + node-title list** to the existing section D
   delta request once authored, so the first research pass also grades it.

---

## 5. Sync, registration, deploy

1. Author into `content/career-templates/<role_key>.v1.json`.
2. `python content/validate_career_templates.py` — must exit 0 with no warnings (§2's soft
   gates are requirements here).
3. **Copy to `backend/app/data/career_templates/`** — this sync is manual and is the step most
   likely to be forgotten; the backend reads only its own copy, so a template that validates
   in `content/` but isn't copied simply doesn't appear in `GET /api/career/templates`.
4. No migration, no schema change, no route change. `GET /templates` enumerates the directory.
5. Confirm the new role appears in onboarding step 1 and that `POST /tree/generate` returns a
   schema-valid tree for it (the generator adapts the template; §3.3 hard-rule validation and
   the unmodified-template fallback both apply unchanged).
6. `CareerPaths.jsx` — drop the "coming soon" badge for the newly-backed role in the same
   commit, or the page keeps advertising a gap that no longer exists.

## 6. Definition of done (Data Analyst)

- [x] `data_analyst.v1.json`: 64 nodes, 8 subjects, validator exit 0, zero warnings
- [x] 11 probe-bearing nodes; every `default_priority >= 4` subject has one
- [x] All `depends_on` resolve in-file, no cycles
- [x] Exactly one BI tool authored (Power BI) — verified no Tableau/Looker/Qlik mention
- [x] `python_analysis` contains no OOP/packaging/testing nodes — verified by keyword scan
- [x] Copied to `backend/app/data/career_templates/` — verified byte-identical (sha256 match)
- [x] Appears in `GET /api/career/templates`; `career_tree.list_templates()` lists it (v1, 64 nodes)
- [ ] ~~"Coming soon" badge removed for Data Analyst in `CareerPaths.jsx`~~ **N/A, spec error.**
  That badge is keyed on whether a matching **catalog roadmap** exists (e.g. `sql`, `data
  engineering`), not on Career Coach role templates — this item never applied and is dropped.
- [x] `SYSTEM-OVERVIEW.md` §1 template count + changelog updated same commit

## 7. Verification findings (2026-07-30) — one real defect, found by simulating the plan, not by reading the JSON

Running `build_plan`'s own frontier/scoring logic at zero mastery (rather than eyeballing
`depends_on`) surfaced what the validator structurally cannot catch: **`spreadsheets` held 5 of
the template's 11 root nodes** (every other subject held exactly 1), so a brand-new user's
actual first plan was **40% Excel** — `SELECT/WHERE/ORDER BY`, `Mean/Median/Mode`, then three
spreadsheet nodes back to back. That subject is exactly the one marked `[I]` (inferred, not
evidence-backed) in §3, so an unverified guess was silently dominating the first impression.

**Fixed:** `spreadsheets.pivottables`, `.data_validation`, and `.conditional_formatting` now
depend on `.data_cleaning`, matching the single-entry-point shape every other subject already
had. Re-simulated: day-one frontier is now 7 nodes, one per subject (`sql_advanced` correctly
has none — it's gated behind `sql_core` by design), and the top-5 spans 5 different subjects.
Also fixed in the same pass: `python_analysis.data_loading`'s title was 7 words
("Reading CSV, Excel & SQL in Pandas"), over the ≤6-word guideline — shortened to "Reading CSV
& Excel into Pandas". Both files re-verified byte-identical after the edit; validator re-run
clean; 388/388 backend suite unaffected (content-only change).

**Not a defect, kept as authored:** the template's overall edge density (0.83 edges/node) is
higher than `backend.v2`'s 0.44 that §3 instructed authors to mirror. Checked via the same
plan-simulation method: it produces a shallower, healthier DAG (max depth 4, entry points in 7
of 8 subjects) than the sparser reference would have. `backend.v2`'s sparsity is closer to the
near-edgeless catalog problem (prod-wide: 0.04 edges/node in the career catalog) than to a
virtue worth copying — don't "fix" this deviation.

## 8. Report back

1. ~~Final node/subject counts and any validator warning you chose to accept, with the reason~~
   — done above: 64 nodes / 8 subjects, zero warnings on this file.
2. ~~Which BI tool you authored and why~~ — done above: Power BI, one tool only.
3. Any node cut for being unprobeable during a future v2 pass — still open, useful signal for
   `analyst_craft` specifically (the hardest subject to probe per §3).
4. Whether §4's research addendum, once run, changes the `spreadsheets` priority (currently 4,
   marked `[I]`) or confirms it.
