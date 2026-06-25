# Curation queue — Aptitude — Quant, Reasoning & Verbal (`aptitude`)

> **For Antigravity.** Generate **one JSON per node** for the **Quantitative Aptitude** sub-track
> only (Phase 1 below). Contract = **`PROMPT-aptitude.md`** (NOT the Python or SQL prompt) —
> `kind: "aptitude"`, the 8-step intuition→patterns→shortcuts→recall template, **formula LAST**.
> Validate with `python content/validate.py` (aptitude branch). Write files to
> `content/roadmaps/aptitude/<slug>.json` (filename = slug). Tick a box once saved **and** green.

Source of truth for topics: `backend/seed_aptitude.py` (the `NODES` list). Use the **exact node
title** as `{{TOPIC}}`. `roadmap` field = `"aptitude"`.

---

## Why Aptitude is the highest-leverage next roadmap (evidence)
From `docs/jd-research-run1.md` — Aptitude is a **ROUND-1 ELIMINATOR / Core** for **3 of 4 roles**:
- **SDE:** `S&P Global OA: 60 MCQ incl. aptitude, cut 59→14`
- **Backend:** `Increff OA: 50 MCQ, "Aptitude" explicit in tech screen`
- **Data Analyst:** `Deloitte OA "Quants & Logical 20q in 25 min"; Swiggy DA logical reasoning`

It is the **missing second gate of the Data-Analyst track** (SQL ✅ + Python ✅ already shipped;
Aptitude is the only round-1 eliminator left), and it doubles as the on-campus filter for
TCS/Wipro/Cognizant. Short, high-frequency, self-contained topics → ideal for spaced repetition.

## Pedagogy — thin lessons, fat engine (see `PROMPT-aptitude.md`)
**Retention is an ENGINE problem, not a lesson problem.** Lessons are deliberately THIN; the spaced,
mixed review queue is the teacher. Every lesson is `kind: "aptitude"`, template:
`hook` (optional) → `mental_model` (**required** — intuition one-liner) → `pattern_discovery`
(**only if natural**; omit for definitional topics) → `formula` → `shortcuts` → `recall_questions` →
`oa_questions` (+ `common_mistakes`). Real 2026 Indian-context hooks, never workers/red-blue-balls.
**No playgrounds, no visuals, no understanding_checks in V1.** North star: *"can they explain & solve
it 30 days later?"* Full spec + worked example: `PROMPT-aptitude.md`.

### Priority stack (whole-product, not just aptitude)
**P0 Review Engine → P1 Thin Lessons → P2 Analytics/weakness-detection → P3 Playgrounds/animations.**
Playgrounds are DEFERRED — do not build or author them. The retention moat lives in the engine, not
the lesson. The one Claude-side gate for *authoring*: the `validate.py`/`schema.json` aptitude branch.

---

## Phase 1 — Quantitative Aptitude  (24 nodes — BUILD NOW)

> Verified against TCS NQT (PrepInsta) + IndiaBix + GeeksforGeeks (2026). Covers the substantive,
> high-value topics (DI, Statistics, Geometry, Equations), not only the easy arithmetic ones.

### Numbers
- [x] Number system & divisibility  →  `number-system`
- [x] HCF & LCM  →  `hcf-lcm`
- [x] Simplification & approximation  →  `simplification`
- [x] Surds, indices & logarithms  →  `surds-indices-logarithms`
- [x] Number series & progressions  →  `series-progressions`

### Arithmetic
- [ ] Percentages  →  `percentages`
- [x] Profit, loss & discount  →  `profit-loss`
- [x] Ratio & proportion  →  `ratio-proportion`
- [x] Averages  →  `averages`
- [x] Problems on ages  →  `problems-on-ages`
- [x] Mixtures & alligation  →  `mixtures-alligation`
- [x] Simple & compound interest  →  `interest`
- [x] Partnership  →  `partnership`

### Time & Distance
- [x] Time & work  →  `time-and-work`
- [x] Pipes & cisterns  →  `pipes-cisterns`
- [x] Time, speed & distance  →  `time-speed-distance`
- [x] Trains, boats & streams  →  `trains-boats-streams`

### Advanced
- [x] Permutations & combinations  →  `permutations-combinations`
- [x] Probability  →  `probability`
- [x] Mensuration  →  `mensuration`

### Algebra & Geometry
- [x] Linear & quadratic equations  →  `equations`
- [x] Geometry & coordinate geometry  →  `geometry`

### Data & Statistics  *(highest DA-relevance — see jd-research-run1)*
- [x] Mean, median, mode & dispersion  →  `statistics-basics`
- [x] Data interpretation (tables & charts)  →  `data-interpretation`

### Prereq backbone (suggested edges — feed done slugs into the next topic's `prerequisites`)
`number-system` → `hcf-lcm`, `simplification`; `simplification` → `surds-indices-logarithms`;
`percentages` → `profit-loss`, `interest`, `mixtures-alligation`, `partnership`;
`ratio-proportion` → `mixtures-alligation`, `partnership`, `averages`; `time-and-work` → `pipes-cisterns`;
`time-speed-distance` → `trains-boats-streams`; `permutations-combinations` → `probability`;
`averages` → `statistics-basics` → `data-interpretation`; `equations` → `geometry`.
`number-series`/`series-progressions`, `problems-on-ages`, `mensuration` are mostly independent (roots).

### Topic-specific notes (per `PROMPT-aptitude.md`)
- **`data-interpretation`** — frame as **"reading business dashboards"** (Zomato/IPL/stock charts);
  embed the small table inline. Most DA-aligned node — invest in the recall prompts here.
- **`statistics-basics`** — real dataset (delivery times, salaries); aha = "the mean lies when the
  median doesn't." Bridges into the DA/DS Statistics requirement.
- **`permutations-combinations` / `logarithms` / `clocks` / `mensuration`** — definitional; **OMIT
  `pattern_discovery`**, lead with `mental_model` → `formula` (forcing discovery here = fake discovery).

---

## Phase 2 — Logical Reasoning + Verbal  (UNBLOCKED → `content/_TODO-reasoning.md`)
The 19 nodes (Logical Reasoning ×11, Verbal Ability ×8) use their own `kind: "reasoning"`
(method + worked-example, no formula/discovery) — contract = **`PROMPT-reasoning.md`**, queue =
**`_TODO-reasoning.md`**, exemplar = `roadmaps/aptitude/blood-relations.json` (validated). Same
`aptitude` folder, different `kind`. Generate Logical first (evidenced), Verbal second, Vocab last.
(Letter-series: quant = `series-progressions`, logical = `series-reasoning` — de-duped.)
Renderer (`kind: "reasoning"`) is a Claude-side task, like the aptitude renderer.

---

## Claude-side build (NOT Antigravity)
1. **`validate.py` + `schema.json` aptitude branch** — `kind:"aptitude"` required:
   `mental_model`, `formula`, `shortcuts≥1`, `recall_questions≥3`, `oa_questions≥2`,
   `common_mistakes≥1`; optional: `hook`, `pattern_discovery`. NO playground/visual fields. **Do
   FIRST** — gates green output. Enforce the law: if `pattern_discovery` present, it precedes `formula`.
2. **`LessonView` aptitude renderer** — renders the thin template in order; formula collapsed until
   `pattern_discovery` revealed (when present).
3. **Wiring:** `mkdir content/roadmaps/aptitude`; add `'Aptitude — Quant, Reasoning & Verbal': 'aptitude'`
   to `frontend/src/lib/contentRoadmaps.js`; `sync-content.mjs` already copies the dir; live on next push.
4. **Playgrounds = P3, DEFERRED.** Not built, not authored. Revisit only after the review engine (P0).
