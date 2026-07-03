# RetainHQ Content Engine

A content **operating system** — not a list of post ideas. The goal is that writing happens as a
**by-product of building and learning**, so it's sustainable for 6–12 months without burning out.

> **Positioning:** *An AI Software Engineer building RetainHQ in public.* Not an influencer, not a
> product marketer. People should follow the **engineering journey** and arrive at the product
> naturally.

---

## Operating principles (the filter for every post)
- **Never fake expertise.** If you just learned it today, say "I learned X today," not "Here's how X works" in a guru voice.
- **No clickbait.** No "🚨 This will change everything." Lead with the real thing.
- **Every post teaches, documents, or demonstrates.** If it does none of those, don't post it.
- **The product appears as evidence, not an ad.** "Here's the bug I hit building the review scheduler" → RetainHQ shows up because it's the setting, not the pitch.
- **Show the work, including the messy parts.** Wrong assumptions and dead ends are the most relatable content.

---

## How the engine runs (read this part)

You do **not** sit down to "make content." You build and learn; the system captures the exhaust.

**The loop:** Build/learn something → capture a screenshot or 3 lines of notes *in the moment* → at end of day, spend 15 min turning ONE captured thing into ONE post using a pillar template → drop the rest into the backlog.

Two files do the work:
1. **This doc** — the templates + the standing backlog (below). Reference material.
2. **`CONTENT-LOG.md`** (you maintain it) — your daily checklist + what shipped. Template at the bottom; copy the block each day.

The backlog below is **pre-seeded with ~40 real RetainHQ topics** so you never face a blank page. When you build something new, add a line to the backlog; when you post, check it off.

---

## The 8 pillars (each = a reusable template + real seeds)

### 1. Build Log — *"What changed today"*
**Purpose:** document progress; lowest-effort, highest-frequency pillar (your daily default).

**Template:**
> **Day N building RetainHQ.**
> Today I shipped: **[feature]**.
> Why it matters: **[the user problem in one line]**.
> The interesting part: **[one technical or design detail]**.
> [screenshot / 20s clip]
> Next: **[tomorrow's thing]**.

**Seeds (all already built — pure documentation):**
- Execution-trace DSA visualizer (watch merge sort / binary search run step by step).
- Career Paths tab — role transitions (Backend→GenAI) mapped to roadmaps.
- Hover-to-explain glossary (tough words explained inline, with examples from the topic).
- Trade-wise roadmap grouping driven by real JD research.
- Review metrics: retention strength, recall accuracy, compliance.
- "Self Learning" as a first-class source type (learning via LLMs counts).
- New-user screen now shows roadmaps + a review calendar.

### 2. Engineering Lesson — *"Learn in public from my own code"*
**Purpose:** turn studying your own stack into content. This IS your DSA/interview prep, made public.

**Template:**
> I finally understood **[concept]** while building RetainHQ.
> The thing that confused me: **[the misconception]**.
> What clicked: **[the mental model, plainly]**.
> Where it shows up in my code: **[1–2 lines of context]**.
> (Still fuzzy on: **[honest gap]**.)

**Seeds (real to your stack):**
- ES256 JWT verification via JWKS (why not HS256; what a public-key verify actually does).
- `MissingGreenlet` — why async SQLAlchemy needs `selectinload` and `expire_on_commit=False`.
- FastAPI dependency injection (`Depends`, `get_current_user`).
- Alembic migrations — why you never hand-edit the live DB.
- React re-render model (why the trace Player splits caption vs lagged visual frame).
- Pyodide in the browser — running Python with zero server compute.
- FSRS scheduling — stability vs difficulty, why it beats fixed SM-2 ladders.

### 3. Product Decision — *"Why this exists"*
**Purpose:** show product thinking. These perform well because they're opinionated and non-obvious.

**Template:**
> Most learning apps do **[default thing]**. RetainHQ deliberately does **[your choice]**.
> Here's why: **[the reasoning / the failure mode you're avoiding]**.
> The tradeoff I accepted: **[honest cost]**.

**Seeds (you have strong takes on all of these):**
- Why AI is **not** the headline feature — retention is the moat; lessons are the hook.
- Why the review queue is **capped at 10/day** (killing the "23 due" death-spiral).
- Why the first review is **deferred to tomorrow**, not instant (anti-fatigue).
- Why roadmaps are grouped by **career trade**, not topic.
- Why **Career Paths** exist (job-aligned bundling vs a static roadmap site).
- Why the LLM grader is **advisory only** — the user always picks the final rating.
- "Track what you remember, not what you complete."

### 4. Debugging Diary — *"The bug and the hunt"*
**Purpose:** the most human, most shareable pillar. Structure = Problem → Wrong assumption → Investigation → Root cause → Fix → Lesson.

**Template:**
> **Bug:** [symptom].
> **I assumed:** [wrong guess]. ❌
> **Actually:** [root cause].
> **Fix:** [what changed].
> **Lesson:** [the transferable takeaway].

**Seeds (real war stories from this build):**
- Supabase deploy hell: `ENOTFOUND` (wrong `aws-0` vs `aws-1` shard) + the `ECIRCUITBREAKER` that re-trips on every retry.
- `framer-motion` "more than one copy of React" — a stale Vite dep cache.
- Binary-search viz showed the wrong array — the Player fed the *original* input to `compile`, but the generator had sorted it.
- The grader felt "off" — it rubber-stamped a wrong answer because `reasoning_effort` was pinned to `low`.
- CSS `text-transform: uppercase` broke a string match because `innerText` returns the *rendered* casing.

### 5. Architecture — *"Why it's built this way"*
**Purpose:** demonstrate system thinking. Explain a design choice, not a tutorial.

**Template:**
> One architecture decision in RetainHQ: **[the choice]**.
> The naive version: **[what most would do]**.
> Why I went the other way: **[constraint / tradeoff]**.
> [a simple diagram or the folder shot]

**Seeds:**
- FastAPI as the **single gateway** to the DB — React never touches Supabase directly. Why.
- The DSA viz spine: **the event trace is the source of truth** (events → compile → frames → renderers), code is authored separately. Why not generate frames directly.
- Content-as-source-of-truth lessons (one JSON per node, validated, synced) — no CMS.
- The FSRS scheduler living on the activity row (denormalized next-review).

### 6. Learning Journal — *"One file a day"*
**Purpose:** a daily study habit that doubles as content. Pick one file, understand it, write 3 lines.

**Template:**
> Today I read **[file]** in my own codebase.
> What it does: **[one line]**.
> What I learned: **[the non-obvious bit]**.
> What still confuses me: **[honest gap]**.

**Seeds (files worth a journal entry):** `services/scheduler.py` (FSRS), `services/grader.py`,
`core/security.py` (JWT), `frontend/src/dsa/compile.js`, `lib/pyodideRunner.js`, `api/deps.py`.

### 7. UI Showcase — *"30–60s, one feature, minimal edit"*
**Purpose:** show, don't tell. Screen-record one flow. No fancy editing.

**Format:** one feature, narrate or caption the *why* in one line, end on the result.
**Seeds:** DSA step-through (scrub merge sort), Career Paths, the review retrieval gate,
the dashboard, the hover glossary, the predict-before-reveal aha.

### 8. Weekly Reflection — *"Wins / mistakes / lessons / next"*
**Purpose:** zoom out, show momentum, set up next week. Post every Friday/Sunday.

**Template:**
> **Week N building RetainHQ.**
> Shipped: [2–3 things]. Broke (and fixed): [1 thing]. Learned: [1 concept].
> Next week: [1 focus].

---

## The daily checklist (the actual system)

Copy this block into `CONTENT-LOG.md` each morning. It's 5 tiny commitments — most days you only *write* one of them, the rest are by-products of building.

```
## YYYY-MM-DD — Day N
- [ ] 📖 Learn ONE concept (from a file I touched today) → Pillar 2 or 6 note
- [ ] 💻 Build/polish ONE thing → Pillar 1 material
- [ ] 🎥 Record ONE 20–60s screen capture (if anything visual changed) → Pillar 7
- [ ] ✍️ Write & post ONE LinkedIn post (pick a pillar + a backlog item)
- [ ] 📝 Add ≥1 new idea to the backlog (from whatever I hit today)
Shipped today: …
Posted: [pillar] — [link]
```

**Rules that keep it sustainable:**
- Posting **one** is the only hard requirement. Build days fill the backlog; you don't need a fresh insight daily.
- Capture in the moment (screenshot folder open while you work). Editing later from nothing is what kills these systems.
- A "boring" build-log day is a valid post. Consistency > virality.

---

## Standing backlog (pre-seeded — start here)

Pull from the **Seeds** under each pillar above — that's ~40 ready posts before you write a single new idea. Suggested **first 2 weeks** (one per day, varied pillars so it doesn't feel repetitive):

| Day | Pillar | Topic |
|---|---|---|
| 1 | Build Log | The DSA execution-trace visualizer (clip of merge sort) |
| 2 | Product Decision | Why AI isn't RetainHQ's headline feature |
| 3 | Debugging Diary | The Supabase `aws-1` shard + circuit-breaker deploy saga |
| 4 | Engineering Lesson | What `MissingGreenlet` taught me about async DB |
| 5 | UI Showcase | Predict-before-reveal aha moment (clip) |
| 6 | Build Log | Career Paths — role transitions mapped to roadmaps |
| 7 | Weekly Reflection | Week 1 |
| 8 | Architecture | Why the event trace is the source of truth, not the frames |
| 9 | Product Decision | Why reviews are capped at 10/day |
| 10 | Engineering Lesson | ES256 JWT verification (JWKS, not HS256) |
| 11 | Debugging Diary | The grader that rubber-stamped a wrong answer |
| 12 | Build Log | Hover-to-explain glossary |
| 13 | Learning Journal | Reading my own `scheduler.py` (FSRS) |
| 14 | Weekly Reflection | Week 2 |

---

## Content library (so capture is frictionless)
Keep a simple folder structure (local or Drive) — capture first, caption later:
```
content/
  screenshots/   YYYY-MM-DD-feature.png
  clips/         YYYY-MM-DD-feature.mp4   (raw 20–60s screen captures)
  drafts/        post-ideas.md            (or just the backlog table above)
  posted/        links + what worked
```

## Repurposing (write once, post thrice)
- **LinkedIn** = home base (1/day, the full post).
- **X** = the same insight, compressed to 1–2 lines + the screenshot. Thread the Debugging Diaries.
- **Reddit** = only the genuinely useful Engineering Lessons / Architecture posts, in the relevant sub (r/learnprogramming, r/webdev), framed as "here's what I learned," never as promo.
- **No Instagram pressure** — only if a UI clip is genuinely nice.

## The 6–12 month goal (what the body of work proves)
By the end, a recruiter or founder landing on your profile should immediately see: **product thinking,
full-stack engineering, AI-assisted development, continuous learning, and clear technical
communication** — i.e. someone who can *build and own a complex product*, not just clear LeetCode.
The DSA prep, the system design instincts, the debugging stories — they all become public evidence,
generated as a side effect of doing the work.
