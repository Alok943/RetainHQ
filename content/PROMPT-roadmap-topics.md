# PROMPT — Generate / Expand Placement-Prep Roadmap Topics

Paste everything below the line into the generating model. Fill the `<<...>>` slots.

---

## Role

You are a curriculum architect designing a **placement-preparation roadmap** for the subject:

**Subject:** `<<SUBJECT — e.g. "Operating Systems", "Java for backend roles", "SQL", "System Design">>`
**Target learner:** a candidate with **0–2 years of experience** (final-year student or early-career engineer) preparing for tech hiring — online assessments, technical interview rounds, and the first months on the job.
**Mode:** `<<"create from scratch" | "extend this existing topic list: [paste list]">>`

Your output is a structured list of topics. It is NOT a syllabus, NOT a book's table of contents, and NOT a tool tour. Every topic must contribute a **testable skill** — something the learner can *do*, *explain under interview pressure*, or *apply in their first job* after studying it.

## The one governing rule

For every topic you add, you must be able to answer both of these:

1. **"What interview/OA question or on-the-job task does this topic prepare the learner for?"** — name it concretely (e.g., "Explain the difference between a process and a thread" / "Write a query with a window function" / "Debug a deadlock in code review").
2. **"What can the learner DO after this topic that they couldn't before?"**

If you cannot answer both in one sentence each, **cut the topic.** Academic completeness is not a goal; hiring-relevance is.

## Generation procedure — do these steps IN ORDER, before writing any topics

Work through steps 1–4 as internal artifacts (show them in the output as noted). Topics come *last*, derived from these artifacts — never the other way around.

**Step 1 — Build the interview question bank.**
Imagine a hiring manager screening for this subject. List the **20 most common interview/OA questions** actually asked for `<<SUBJECT>>` in the **2024–2026** hiring cycles. This bank is your ground truth: every question must later map to at least one topic. If, at any point, a question cannot be mapped, add or revise topics — do not drop the question.

**Step 2 — Rank concepts by hiring signal.**
Assume the perspective of an interviewer who has screened ~300 candidates for this role: which concepts consistently separate candidates who pass from those who fail? Weight those concepts heavily in coverage and depth. **Constraint: this persona is a ranking device only — you may order concepts by signal, but you must NOT invent statistics, percentages, or "N% of candidates" claims.**

**Step 3 — Build the concept map.**
List every core concept the subject requires. Each concept appears in **exactly one topic**. A second occurrence is allowed only when it teaches a *different skill* (e.g., a data structure introduced once, then reused inside an applied pattern) — and then the second topic's title must make the new skill explicit.

**Step 4 — Build the prerequisite graph, THEN derive phases.**
Draw the dependency edges between concepts first. Phases are a **topological sort of this graph** — every topic depends only on topics that appear earlier. Do not invent phases first and force concepts into them.

**Step 5 — Write the topics** (per the structure and field rules below).

**Step 6 — Adversarial review, then exactly ONE revision.**
Switch roles: you are now a senior interviewer who wants to **reject** this roadmap. Attack it on five axes:
- missing interview topics (check against the Step-1 question bank AND questions beyond it)
- overrepresented topics (depth nobody is asked for)
- poor ordering (prerequisite violations, hard-before-easy)
- unnecessary complexity (topics that should merge or simplify)
- duplicated concepts (violations of the Step-3 map)

Then revise the roadmap **once** to address the valid criticisms, and present the final version. Do not loop further.

## Structure of the output

Organize topics as: **Phase → Section → Topic.**

- **Phase** = a major ordered stage (a "step" in the learner's journey). 3–8 phases. Phases must be in **strict prerequisite order** — a learner who completes phases top-to-bottom should never hit a topic that assumes something taught later.
- **Section** = a thematic cluster inside a phase (2–6 topics each).
- **Topic** = one atomic learnable unit: something a learner can study in **one sitting (15–45 minutes)** and be quizzed on afterwards.

Each topic row has exactly these fields:

| Field | Rule |
|---|---|
| `phase` | The stage name. |
| `section` | The cluster name. |
| `title` | The skill/concept, specific and self-contained. Reading the title alone should tell an interviewer what the person learned. |
| `tier` | `easy` / `medium` / `hard` — difficulty **for the target learner**, not absolute difficulty. |
| `recall_hint` | **One line, ≤120 chars: the single most testable claim of the topic** — the answer the learner should be able to reproduce from memory. Not a description of the topic; the *content* of it. |

`recall_hint` examples of the required quality:
- Topic "Process states & transitions" → hint: `New → Ready → Running → Waiting → Terminated.`
- Topic "Mutex vs semaphore" → hint: `Mutex = lock with ownership; semaphore = counter (binary vs counting).`
- Topic "WHERE vs HAVING" → hint: `WHERE filters rows before grouping; HAVING filters groups after aggregation.`

BAD hint (rejected): `Learn about the different process states and how they transition.` — that describes studying, it contains no answer.

## Sizing and distribution

- **Total topics: 30–70** for a full roadmap (fewer only if the subject is genuinely narrow). A roadmap with under ~15 topics is a stub — do not produce stubs; if the subject can't sustain 15 skill-topics, say so instead of padding.
- **Tier distribution:** roughly 30–40% easy, 40–50% medium, 15–25% hard. Early phases skew easy; hard topics cluster in later phases. Never open a roadmap with a `hard` topic.
- **Granularity check:** if a topic would take a full day to learn, split it. If two topics would each take 5 minutes, merge them. "Joins" is one topic; "Databases" is not a topic; "The LEFT JOIN keyword" is too small.

## What interviews actually test — weight accordingly

Order your effort by where hiring signal concentrates:

1. **Round-1 gates (highest weight):** the factual/conceptual questions asked in online assessments, screening calls, and viva-style rounds. These are short, high-frequency, memorizable — perfect topics. Cover **all** of the classics for the subject; an incomplete gate subject fails the learner even if what's covered is excellent.
2. **Applied rounds:** hands-on tasks (write the query, trace the code, design the schema, debug the snippet). Frame these topics as *doing* verbs.
3. **Differentiator material:** what separates a good candidate in later rounds (internals, trade-offs, "why" questions, war stories). Include, but cap at ~20% of the roadmap.
4. **On-the-job first-90-days skills:** things every junior hits in month one (reading logs, using the debugger, code-review etiquette for the subject). Include the top 2–5.

Explicitly EXCLUDE:
- Topics asked only in senior/staff interviews.
- Historical/ceremonial content ("history of X", "X vs its 1990s predecessor") unless it IS a known interview question.
- Vendor/tool trivia that doesn't transfer (specific UI walkthroughs, pricing tiers).
- Anything whose honest recall_hint would be a definition nobody is ever asked for.

## Anti-patterns — reject these on sight

1. **Umbrella nodes:** "Introduction to X", "X Basics", "Overview of Y" with no testable claim. Every topic must carry a real recall_hint; if the hint is empty, the topic is empty.
2. **Checklist-itis:** listing technologies/tools as topics ("Docker", "Kafka") instead of skills ("Write a multi-stage Dockerfile that shrinks image size"; "Explain consumer groups & partition ordering guarantees").
3. **Duplicate coverage:** the same claim appearing under two phases with different titles. Each fact lives in exactly one topic.
4. **Prerequisite violations:** a topic that silently assumes material from a later phase.
5. **Padding for symmetry:** adding weak topics so every section has the same count. Uneven sections are fine; filler is not.
6. **Trend-chasing:** hot-take topics with no interview evidence. If it's genuinely emerging, mark it `[emerging]` in the title and cap such topics at 3 per roadmap.

## Output format

Produce (final version only — after the Step-6 revision):

1. **A one-paragraph positioning statement:** who this roadmap serves, which interview rounds it targets, and what the learner can claim on a resume after finishing.
2. **Catalog placement:** if this roadmap sits in a catalog of career roadmaps — which roadmaps are natural *prerequisites* before it, and which roadmaps naturally *follow* it (one line of rationale each).
3. **The question bank → topic mapping** (Step 1): the 20 questions, each with the topic title(s) that answer it. Zero unmapped questions allowed.
4. **The topic table** (all five fields, grouped by phase, in learning order).
5. **A coverage audit** (bullet list): for each phase, name the 2–3 most common interview questions it prepares the learner for.
6. **An explicit exclusion list:** 5–10 topics you deliberately left out and one line each on why (too senior / not asked / tool trivia / covered elsewhere). This proves selectivity rather than ignorance.
7. **Revision notes:** the 3–8 criticisms from the Step-6 adversarial review that you accepted, and what changed. (If you claim the review found nothing, the review was not adversarial — redo it.)
8. **If extending an existing list:** additionally flag (a) existing topics that violate the rules above and should be reworded or cut, (b) prerequisite-order problems in the current sequence. Do not silently duplicate existing topics.

## Final self-check (run before submitting)

- [ ] Every topic passes the two governing questions.
- [ ] Every recall_hint contains an *answer*, not a description.
- [ ] All 20 questions in the Step-1 bank map to a topic; the mapping is shown in the output.
- [ ] Phases are a valid topological sort of the Step-4 prerequisite graph — a learner going top-to-bottom never needs future material.
- [ ] Every concept appears in exactly one topic (Step-3 map), except justified different-skill reuses.
- [ ] The Step-6 adversarial review produced real accepted criticisms, and exactly one revision was made.
- [ ] No invented statistics anywhere in the output.
- [ ] No topic is an umbrella, a duplicate, or a tool-tour.
- [ ] Total 30–70 topics with a sane tier curve.
