# Roadmap node-derivation research prompt (reusable, any roadmap)

> Purpose: decide **which nodes a roadmap should have** (and their phase/section/tier/one-claim
> description) from real hiring + interview evidence — the step BEFORE lesson authoring. Output
> drops straight into a `seed_*.py` NODES list. This is NOT the lesson-enrichment prompt
> (`PROMPT-dsa-research.md` does that, per-node, AFTER this decides the list).
>
> Runs on Gemini Deep Research (recommended) or any deep-research LLM. **Run ONE roadmap per run.**
> Fill the four `<<...>>` slots at the top, paste from ROLE down, then run.

---

## FILL THESE (the only per-roadmap inputs)

- `<<ROADMAP>>` = e.g. **Data Engineering**
- `<<TARGET_ROLES>>` = the exact roles this roadmap serves, e.g. **Data Engineer, Analytics
  Engineer (India + remote-India, 0–4 yrs / new-grad & early-career)**
- `<<CANON>>` = 1–2 authoritative curricula/books/docs to use as a COMPLETENESS CROSS-CHECK ONLY,
  e.g. **"Fundamentals of Data Engineering" (Reis & Housley); dbt + Airflow official docs**
- `<<SIZE>>` = target node count, default **35–45** (hard ceiling 50)

---

## ROLE
You are a senior hiring manager + interview panelist for `<<TARGET_ROLES>>`, doing rigorous,
citation-backed research to design a focused learning roadmap. You know exactly what these
interviews ask and what the job punishes on day one. You are ruthlessly scope-disciplined: your
job is to define what a candidate MUST know to clear the interview and survive week one — NOT to
teach the academic field. Completeness is a failure mode here, not a virtue.

## THE GOVERNING PRINCIPLE — "enough, not a PhD"
Scope to the **external gate**, not the subject. A node earns its place ONLY if you can name
either (a) a realistic interview question for `<<TARGET_ROLES>>` where it decides the answer, OR
(b) a concrete day-1 production decision / incident where not knowing it hurts. If neither, CUT
IT — that direction is the PhD. Canonical textbook depth that interviews never probe is exactly
what to leave out.

## THE OTHER FAILURE MODE — "enough" is not "beginner-only"
"Enough, not a PhD" cuts the ceiling; it does NOT lower the floor to definitions. `<<TARGET_ROLES>>`
covers the WHOLE 0–N band, so the roadmap must include the **intermediate / production nodes that
the interview and the job actually gate on** — not just the foundational recognition nodes a
first-week beginner needs. Concretely, DO include (when the evidence supports them for these
roles): the recurring **trade-off / "when would you use X vs Y" decisions**, the **resilience /
distributed / production-contract** concerns that show up in real incidents (retries, idempotency,
throttling contracts, delivery guarantees, observability *of the contract*), and the **hard-tier
design/debug** question-families — NOT only easy definitions. A roadmap that is all `easy`-tier
recognition nodes has failed the brief as badly as one full of PhD trivia. Check the tier mix
before returning: if almost nothing is `hard`, you under-scoped. (Still bounded by the external
gate + the domain boundary — this raises the floor, it does not remove the cuts.)

## EVIDENCE — gather in THIS priority order (inclusion comes from 1 & 2; 3 is a cross-check only)
1. **JD sweep.** Pull 15–25 real `<<TARGET_ROLES>>` job postings (LinkedIn, Naukri, Wellfound,
   company career pages, Instahyre). Extract the skills/tools/concepts that RECUR across many
   postings. Note rough frequency (how many of N postings mention each).
2. **Real interview questions.** What is ACTUALLY asked in `<<TARGET_ROLES>>` interviews — from
   interview-experience posts (Glassdoor, LeetCode discuss, GeeksforGeeks interview experiences,
   Reddit r/dataengineering-style threads, YouTube mock interviews, question banks). Capture the
   recurring question families, not one-off exotic questions.
3. **Canon cross-check ONLY.** Skim `<<CANON>>` to catch anything genuinely core that evidence
   1–2 missed. Canon reveals GAPS; it never justifies inclusion on its own. If canon covers
   something interviews/JDs don't ask → it stays OUT (flag it in `excluded` with reason
   "canon-only").

## FROM EVIDENCE TO NODES — the derivation
1. **Extract claims, not topics.** Convert evidence into atomic, testable question-families —
   the unit an interviewer probes in one exchange ("when does an index NOT help?", "why is a
   shuffle expensive in Spark?"). One question-family = one node. A "topic" that needs a whole
   chapter is several nodes; split it.
2. **Frequency-weight & cut.** Recurs across many JDs/interviews → include. Appears once, or only
   at senior/staff level, or canon-only → exclude (record in `excluded`). Hold the `<<SIZE>>`
   budget; if over, cut the lowest-frequency nodes, don't shrink descriptions.
3. **Structure each node as a seed tuple:**
   - `phase` = the prerequisite spine step. Order phases foundations → mechanism → applied →
     production/ops. 5–9 phases typical.
   - `section` = a question cluster within a phase (2–6 nodes share a section label).
   - `tier` = interview altitude: **easy** = definition/recognition; **medium** =
     mechanism/trade-off; **hard** = design / debug / at-scale (the differentiator round).
   - `title` = the node's short name (≤ ~40 chars).
   - `description` = ONE testable claim / the thing to remember, ≤ ~120 chars, mechanism-first
     (this becomes the seed's node description AND the seed of a recall card — make it a CLAIM,
     not a label; "Partitioning prunes data at scan time — the #1 warehouse cost lever", not
     "Learn about partitioning").

## VALIDATE before returning — the mock-interview test
- **Coverage:** list 10 real interview questions for `<<TARGET_ROLES>>`. EVERY one must land on
  at least one node. A question with no home = a missing node (add it).
- **Waste:** EVERY node must catch at least one of those questions OR a named production
  decision. An orphan node = cut it. **Be honest here** — if a node maps to no question, either
  add the question that justifies it or cut it; do NOT silently leave it unmapped and call the
  list validated. (Observed failure: a run kept "HTTP status codes" and "access vs refresh
  tokens" with no mapped question and didn't flag them — both were legit, but the auto-validation
  had quietly passed over them. A human still spot-checks coverage.)
- **Tier mix:** the returned nodes must NOT be almost all `easy`. If `hard` is nearly absent,
  you under-scoped to beginner-recognition — revisit and add the design/debug/trade-off
  question-families the role actually gates on (see "enough is not beginner-only" above).
- **"So that" check:** each phase must complete "learn this phase *so that* you can ___ in the
  interview / on the job." If the blank is "understand the field better" → the phase is too
  academic; retighten.
- **Budget:** node count within `<<SIZE>>` (≤ 50). If not, cut by frequency.

## OUTPUT — return EXACTLY this, nothing else

### 1. `NODES` — ready to paste into a seed_*.py
A fenced Python block: a list of `(phase, section, title, tier, description)` tuples in learning
order, grouped by phase with a `# ---- <phase> ----` comment before each phase's block. Match
this style exactly (it is the existing seed format):
```python
NODES = [
    # ---- Foundations ----
    ("Foundations", "Landscape", "OLTP vs OLAP", "easy", "Row-store transactional DBs vs column-store analytical warehouses."),
    # ... one tuple per node ...
]
```
Also give me, above the block: `SLUG` (kebab-case, = the intended content folder key),
`TITLE`, and a one-sentence `DESCRIPTION` for the roadmap.

### 2. `evidence` — why the list looks like this
- **JD frequency table:** top ~20 skills/concepts, each with "seen in X/N postings".
- **Interview question families:** the recurring question families found, grouped, with a
  rough frequency tag (high/med/low) and which node(s) each maps to.
- **excluded:** things a naive syllabus WOULD include but you cut — each as
  `{item, reason}` where reason ∈ {low-frequency, senior-only, canon-only, belongs-in-<other
  roadmap>, out-of-scope}. This list proves scope discipline; make it substantial.

### 3. `validation` — the mock-interview test, shown
- The 10 real interview questions you used, each mapped to the node(s) that cover it (proves
  coverage).
- Any node that maps to NO question — should be empty; if not, justify or cut.
- The per-phase "so that" sentences.

### 4. `sources` — 8–15 real URLs actually consulted (JD listings, interview-experience posts,
canon). No fabricated links. Split into `jd`, `interviews`, `canon`.

## HARD RULES
- **Roles first, subject second.** If it's not asked of `<<TARGET_ROLES>>` and not a day-1 job
  need, it's out — no matter how "fundamental" it is academically.
- **Boundary respect.** If a concept belongs to a sibling roadmap (e.g. for a Data Engineering
  run, deep SQL windowing is shared but Kafka exactly-once is DE's; distributed-rate-limiting is
  System Design's), keep only what THIS roadmap owns; push the rest to `excluded` with
  `belongs-in-<roadmap>`.
- **Descriptions are claims, not labels** — each must be independently recall-testable.
- **No LaTeX/images** — all math/complexity as plain text.
- **Cite, never copy.** Original wording; sources in `sources`.
- **One roadmap per run.** Don't batch multiple roadmaps.

## WHERE OUTPUT LIVES
- Save the full response to `content/research/<slug>/nodes.md` (evidence + validation + sources
  are the audit trail for why the roadmap looks the way it does).
- Paste the `NODES`/`SLUG`/`TITLE`/`DESCRIPTION` into `backend/seed_<slug>.py` (copy an existing
  seed as the template; assign the UUID from the registry in `docs/roadmap-catalog-plan.md`).
- AFTER the seed exists and nodes are locked, run the PER-NODE lesson-enrichment research
  (`PROMPT-dsa-research.md` for dsa-kind; the matching `PROMPT-*.md` for the node's `kind`) to
  produce lesson content. This prompt's job ENDS at the node list.

### If using Gemini Deep Research (two-step)
Deep Research returns prose. Run it for depth, then in the SAME chat send:
> Now convert your research into the exact OUTPUT format specified: (1) a Python `NODES` list of
> (phase, section, title, tier, description) tuples grouped by phase with SLUG/TITLE/DESCRIPTION
> above it, (2) the evidence tables incl. the `excluded` list, (3) the 10-question validation
> mapping, (4) sources split jd/interviews/canon. Output only that. Descriptions ≤120 chars,
> each a testable claim. Node count ≤ <<SIZE>>. Plain-text math only.
