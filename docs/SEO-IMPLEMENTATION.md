# SEO Implementation Plan

**Source data:** Google Search Console 3-month export, 2026-07-16 (property covers both hosts).
**Status (2026-07-17):** P0-A, P0-B, and P1-A are implemented and live in production (reviewed & verified — 640 pages prerendered, title parity confirmed in-browser, all word-count criteria pass). Open items: sitemap `<lastmod>` uses build date instead of git date (needs fix), 3 physics `seo.title`s over 60 chars, cross-roadmap links only done for the GIL pair. Next founder action: request indexing for the §0 priority URLs in GSC and judge on 28-day windows.

---

## 0. Where we stand (from the GSC export, verified against the live site)

- **Inflection is real:** 16 impressions (June 21–30) → 614 impressions (July 1–14). 91 distinct pages have impressions. Google is indexing and testing the content.
- **All 9 clicks are brand/homepage** (position ~1 for "retainhq"-type queries). Content pages: **0 clicks on ~600 impressions** at average position 48 — expected; nothing ranks on page 1 yet.
- **Host consolidation is already correct:** `www.` 308-redirects to apex; canonicals, robots.txt, sitemap (641 URLs), and JSON-LD are all in place. The `www.` rows in GSC are historical and will consolidate on their own. **No action needed.**
- **The bottleneck is on-page:** prerendered lesson HTML serves **~80–110 words** to crawlers while the lesson JSON contains **~1,000 words** (verified live on `configdict-from-attributes`: 112 words served, ~1,000 in JSON). We are ranking position 22–50 on ~10% of our content, against official docs and 1,500-word blog posts.

Priority pages (best position × most impressions, 3-month data):

| Page (slug) | Roadmap | Position | Impressions | Top queries it matched |
|---|---|---|---|---|
| configdict-from-attributes | python-backend | 22.5 | 31 | `from_attributes` (pos 12), `from_attributes=true` (15), `pydantic config` |
| api-tests-httpx-testclient | python-backend | 31.1 | 12 | — |
| sieve-of-eratosthenes-prime-factorization | cpp-swe | 36.1 | 9 | — |
| type-checking-imports | python-swe | 37.7 | 39 | — |
| rule-of-3-5-0-copy-move-destructor | cpp-swe | 37.9 | 39 | `rule of 0/3/5` (30.5), `rule of 3/5/0` |
| uvicorn-gunicorn-workers | python-backend | 42.2 | 61 | `uvicorn vs gunicorn`, `gunicorn workers`, `gunicorn worker class/types`, `what is uvicorn` |
| next-permutation-rotate-reverse | cpp-swe | 45.6 | 16 | `c++ next_permutation` |
| pydantic-settings | python-backend | 47.2 | 61 | `pydantic settings`, `pydantic env`, `settingsconfigdict`, `yamlconfigsettingssource` |
| mutable-vs-immutable | python-backend | 49.8 | 19 | many phrasings of "mutable vs immutable" |
| bit-manipulation-tricks-for-cp | cpp-swe | 49.9 | 11 | `bit manipulation in c++` |
| pytest-basics-and-fixtures | python-backend | 50.9 | 21 | `python fixtures`, `pytest yield` |
| threading-vs-multiprocessing | python-backend | 52.6 | 14 | ~8 phrasings |
| rag-evaluation | ai-engineering | 82 | 77 | `rag evaluation` (41 imp), `rag testing`, `rag triad`, `rag evaluation framework` |
| distinguish-live-neutral-and-earth-wires | physics-9 / physics-10 | 41.7 | 11 | `live wire neutral wire earth wire` |
| tcp-3-way-handshake | core-cs | 71 | 10 | ~9 phrasings of "tcp 3 way handshake" |

Geography: India has all clicks + 58 impressions; US leads impressions (100). Desktop = 606 of 630 impressions. Physics `class 9`/`class 10` query phrasing confirms the India school audience is reaching these pages.

---

## P0-A · Prerender the full lesson content

**File:** `frontend/scripts/generate-lesson-html.mjs` (runs post-build; writes `dist/roadmaps/<key>/learn/<slug>/index.html`).

**Problem:** `renderContentBlocks()` only extracts `hook.scenario, overview, why, why_it_matters, mental_model, explanation, analogy, method, formula, key_points, shortcuts, common_mistakes, recall_questions`. It misses the fields carrying most of the words — notably `sections`, `code_snippets`, `glossary`, `oa_questions`, and everything specific to `concept` lessons (227 of ~640 lessons: `why_learning_this`, `code_walkthrough`, `understanding_checks`, `practice_tasks`, `challenge`, `aha_moment`).

**Target:** every lesson page serves 500–1,000+ words of the same content the React app shows.

### Field inventory (verified against all content JSON, by `kind`)

| kind (count) | Content fields present |
|---|---|
| engineering (127) | hook, mental_model, **sections**, **code_snippets**, key_points, common_mistakes, recall_questions, **oa_questions**, **glossary**, explanation, why_it_exists |
| concept (227) | overview, **why_learning_this**, **code_walkthrough**, **understanding_checks**, **practice_tasks**, **challenge**, **aha_moment**, common_mistakes, recall_questions, glossary, query_walkthrough (SQL) |
| theory (61) | hook, mental_model, explanation, key_points, common_mistakes, recall_questions, oa_questions, glossary |
| physics (128) | hook, mental_model, explanation, key_points, **worked_example**, common_mistakes, recall_questions, oa_questions |
| dsa (43) | hook, **why_it_exists**, mental_model, explanation, key_points, **pattern**, **failure_signals**, **engineering_examples**, **when_not_to_use**, common_mistakes, recall_questions, oa_questions, **practice**, **interesting_facts**, glossary |
| aptitude (24) | hook, mental_model, **pattern_discovery**, **formula**, **worked_example**, **shortcuts**, common_mistakes, recall_questions, oa_questions, glossary |
| reasoning (16) | mental_model, **method**, **worked_example**, shortcuts, common_mistakes, recall_questions, oa_questions, glossary |
| maths (3) | mental_model, explanation, **derivation**, common_mistakes, recall_questions |
| numericals (9) | `problems` only — **skip**, or render problem statements as a list; low SEO value |

**Bold** = currently NOT rendered.

### Exact shapes of the missing fields (verified across all files)

```
sections            → [{body, recap?, title?, image?, animation?}]   (title present in only 3 files)
code_snippets       → [{title, language, code, explanation}]
worked_example      → {problem, steps: [str], answer}
oa_questions        → [{question, company?, answer, approach?}]
understanding_checks→ [{type, question, answer, why}]
code_walkthrough    → {code, focus}
practice_tasks      → [{title, prompt, starter_code?, solution?}]
challenge           → {title, prompt, solution?}
glossary            → [{term, definition}]
pattern             → {name, recognition_cues: [str]}
aha_moment          → {code, prediction?, common_guess?, why}
why_it_exists       → str
why_learning_this   → [str]
method              → [str]
pattern_discovery   → {setup, cases: [str], prompt, rule}
formula             → {statement, explain}
derivation          → [{goal, steps: [{expr, rule, why}], rules}]
engineering_examples→ [{title, problem, why_this_algorithm}]
failure_signals     → [str]
when_not_to_use     → [{scenario, reason}]
interesting_facts   → [str]
shortcuts           → [{title, trick, example}]  (also plain [str] in some files)
hook                → {scenario, question?}  or missing
mental_model        → {intuition, description?, repeated_decision?}  or plain str
overview            → {what, why, where_used: [str]}  or plain str
```

Shapes vary — every extractor must tolerate `str | [..] | {..}` and skip silently on anything unrecognized (never crash the build; `console.warn` at most).

### Rendering rules

1. **Render order** (extend the existing `fields` array): hook (scenario + question) → overview / why_it_exists / why_learning_this → mental_model (intuition + description) → explanation → **sections** (each `body` as `<p>`s, `recap` as an emphasized line) → method / formula / pattern_discovery / derivation → **code_snippets** (`<h3>{title}</h3><pre><code>{code}</code></pre><p>{explanation}</p>`) → **code_walkthrough** / **aha_moment** (code + why) → worked_example (`<p>{problem}</p><ol>{steps}</ol><p>Answer: {answer}</p>`) → key_points → pattern + failure_signals + engineering_examples + when_not_to_use (dsa) → shortcuts → common_mistakes → **glossary** (`<dl><dt>{term}</dt><dd>{definition}</dd></dl>`) → recall_questions (questions only, as now) → **understanding_checks + oa_questions** as visible Q&A (`<h3>{question}</h3><p>{answer}</p>` — include the answers; they are real content and the app shows them) → practice_tasks + challenge (title + prompt only; **omit `solution` / `starter_code`** — low SEO value, bloats HTML) → interesting_facts.
2. **`sections` headings:** items have no titles (except 3 files). Use one `<h2>` for the block (e.g. "Deep dive") and paragraphs inside; do NOT invent per-section headings.
3. **Code blocks:** `<pre><code class="language-{language}">` with existing `escapeHTML`. Code counts toward relevance for queries like `configdict(populate_by_name=true)` — include it.
4. **Keep** the existing breadcrumb links, prerequisites/unlocks "Continue learning" list, hub back-link, title/canonical/OG replacement, and JSON-LD. None of that changes in P0-A.
5. **Parity guardrail (anti-cloaking):** the static article must remain a plain-HTML rendering of content the React app actually shows users. Never add crawler-only keyword text. Omissions (solutions, viz) are fine; additions are not.
6. Two `extractText` declarations exist in the script (one scoped inside `renderContentBlocks`, one module-level for `getSeoDescription`). Not a bug (the inner one shadows correctly) but consolidate while in there.

### Acceptance criteria

- `node scripts/generate-lesson-html.mjs` (after `vite build`) completes with 0 errors across all ~640 lessons.
- Spot-check word counts of `<article>` text (strip tags): `configdict-from-attributes` ≥ 600 (was 112), `uvicorn-gunicorn-workers` ≥ 500 (was 82), one lesson per kind ≥ 400 (except numericals).
- Rendered HTML for one lesson per kind opens in a browser and reads as a coherent article (no `[object Object]`, no empty headings, no unescaped HTML).
- `<title>`, canonical, JSON-LD unchanged by this item.

### Post-deploy

In GSC → URL Inspection, request indexing for the 15 priority URLs in §0. Then wait; do not re-request repeatedly.

---

## P0-B · Query-matched SEO titles & descriptions (override mechanism + retitle table)

**Decision already made:** search-facing `<title>`/meta-description only. In-app H1s and navigation keep the human titles. Lesson JSON `title` values do not change.

### Mechanism — must cover BOTH render paths

`frontend/src/LessonView.jsx:165` rebuilds `document.title` from `lesson.title` after mount, and Googlebot renders JS — so **a prerender-only retitle would be overwritten and never indexed.** The override must be read by both sides:

1. Add an optional block to lesson JSON (allowed by `content/validate.py` — extend the validator to accept it, optional, both fields optional strings):
   ```json
   "seo": { "title": "…", "description": "…" }
   ```
2. `generate-lesson-html.mjs`: `pageTitle = lesson.seo?.title ?? existing formula`; `pageDesc = lesson.seo?.description ?? getSeoDescription(lesson)`.
3. `LessonView.jsx`: `seoTitle = lesson.seo?.title ?? existing formula`; same for `seoDesc`. H1/breadcrumbs/JSON-LD `name` keep using `lesson.title`.
4. `sync-content.mjs` already copies JSON verbatim — no change.

### Title conventions

- ≤ 60 characters where possible; front-load the query phrase; ` | RetainHQ` suffix only if it fits (dropping the brand is fine — the URL carries it).
- Description ≤ 158 chars, contains the query phrase once, states what the reader gets, no marketing fluff.
- Never two pages targeting the same primary query.

### Retitle table (priority pages; queries from GSC)

| Slug | `seo.title` | `seo.description` (draft — trim to 158) |
|---|---|---|
| python-backend/configdict-from-attributes | `Pydantic from_attributes & ConfigDict, explained` | `What ConfigDict(from_attributes=True) does, when Pydantic needs it, and how FastAPI uses it to serialize SQLAlchemy ORM objects — with runnable examples.` |
| python-backend/uvicorn-gunicorn-workers | `Uvicorn vs Gunicorn: worker types & how many to run` | `Uvicorn vs Gunicorn in production: worker classes, how many workers to run (2×cores+1), and when you need both — explained for FastAPI deployments.` |
| python-backend/pydantic-settings | `pydantic-settings: env vars, .env & SettingsConfigDict` | `Load config from environment variables and .env files with pydantic-settings — SettingsConfigDict, nested models, secrets, and validation at startup.` |
| python-backend/pytest-basics-and-fixtures | `pytest fixtures explained: yield, scope & conftest` | `How pytest fixtures work — yield fixtures, fixture scope, conftest.py, and the patterns you actually use to test a FastAPI backend.` |
| python-backend/mutable-vs-immutable | `Mutable vs immutable in Python: what actually changes` | `Lists vs tuples, why strings can't change, aliasing bugs, and how mutability decides what happens when you pass objects to functions.` |
| python-backend/threading-vs-multiprocessing | `Python threading vs multiprocessing: which to use when` | `Threads vs processes in Python — how the GIL decides which one helps, I/O-bound vs CPU-bound work, and the failure modes of picking wrong.` |
| python-backend/functools-wraps | `functools.wraps: why every decorator needs it` | `What @functools.wraps does, what breaks without it (names, docstrings, introspection), and how to write decorators that don't lie about themselves.` |
| python-backend/api-tests-httpx-testclient | `Testing FastAPI with httpx AsyncClient & TestClient` | `Write API tests for FastAPI with TestClient and httpx AsyncClient — auth headers, async tests, and dependency overrides, step by step.` |
| ai-engineering/rag-evaluation | `RAG evaluation: metrics, the RAG triad & testing pipelines` | `How to evaluate a RAG system — retrieval and generation metrics, the RAG triad (context relevance, groundedness, answer relevance), and building a test set.` |
| cpp-swe/rule-of-3-5-0-copy-move-destructor | `The Rule of 3/5/0 in C++: copy, move & destructors` | `When you need the Rule of 3, when the Rule of 5, and why the Rule of 0 is the goal — copy/move constructors, assignment, and destructors explained.` |
| cpp-swe/next-permutation-rotate-reverse | `std::next_permutation in C++ (+ rotate and reverse)` | `How std::next_permutation works, generating permutations in lexicographic order, and the rotate/reverse tricks interviewers expect.` |
| cpp-swe/bit-manipulation-tricks-for-cp | `Bit manipulation tricks in C++ for competitive programming` | `The bit tricks that matter in contests — set/clear/toggle, lowest set bit, popcount, XOR patterns — with C++ snippets you can paste.` |
| cpp-swe/raii-resource-acquisition-is-initialization | `RAII in C++: Resource Acquisition Is Initialization` | `What RAII means, why destructors make C++ resource-safe without garbage collection, and how unique_ptr/lock_guard apply it.` |
| core-cs/tcp-3-way-handshake | `TCP 3-way handshake, step by step (SYN, SYN-ACK, ACK)` | `Exactly what happens in the TCP three-way handshake — SYN, SYN-ACK, ACK, sequence numbers, and what breaks when a step is lost.` |
| dsa/queue-and-deque | `Queue and deque in data structures (dequeue vs deque)` | `Queues, deques, and the dequeue-vs-deque naming trap — operations, complexity, and where each shows up in real systems.` |
| dsa/selection-sort | `Selection sort: how it works & is it stable?` | `Selection sort step by step — why it's O(n²), why the standard version is not stable, and when it's still the right tool.` |

**Physics pattern** (apply per lesson; queries carry `class 9` / `class 10` — Indian NCERT phrasing):

| Slug | `seo.title` |
|---|---|
| physics-10/distinguish-live-neutral-and-earth-wires | `Live, neutral & earth wires explained — Class 10 Physics` |
| physics-10/relate-refractive-index-to-speed-of-light | `Refractive index & speed of light — Class 10 Physics` |
| physics-10/define-electric-potential-difference | `Electric potential difference: definition & formula — Class 10` |
| physics-9/state-laws-of-reflection-of-sound | `Laws of reflection of sound — Class 9 Physics` |
| physics-9/define-pressure | `Pressure: definition, formula & SI unit — Class 9 Physics` |

### Acceptance criteria

- For each retitled page: static HTML `<title>` == JS-rendered `document.title` (load the page, wait for React mount, compare). This is the whole point of the mechanism.
- `content/validate.py` passes on all lessons (with and without `seo` block).
- App UI shows no change anywhere (H1s, cards, nav).

---

## P1-A · Keyword-gap coverage inside existing lessons

GSC shows searchers arriving on sub-topics the pages never name. Add these as **real content** (a section/heading + 2–4 sentences in the lesson JSON, written to teach — not keyword stuffing). Content edits can go through the normal Antigravity pipeline against `content/PROMPT-*.md` contracts; each must pass `content/validate.py`.

| Lesson | Add |
|---|---|
| ai-engineering/rag-evaluation | A "The RAG triad" section (context relevance, groundedness, answer relevance — queries `rag triad` already hit this page); a sentence naming common frameworks (RAGAS, TruLens) as things this lesson's concepts map to |
| python-backend/uvicorn-gunicorn-workers | "Gunicorn worker classes" (sync, gthread, `uvicorn.workers.UvicornWorker`) and "How many workers?" (the 2×cores+1 heuristic and when it's wrong) — both are distinct GSC queries |
| python-backend/pydantic-settings | Explicit "Reading environment variables" phrasing; name `YamlConfigSettingsSource` (a GSC query) if YAML config is covered at all |
| dsa/queue-and-deque | A "deque vs dequeue" naming note — searchers write `dequeue in data structure` (2 distinct GSC queries) |
| dsa/selection-sort | "Is selection sort stable?" — an exact GSC query (`selection sort is stable or not`) |
| python-backend/the-gil | Make sure the exact phrase "Global Interpreter Lock (GIL)" appears in the first paragraph; cross-link threading-vs-multiprocessing |

---

## P1-B · Internal linking

Current crawl graph: hubs → lessons; lessons → prerequisites/unlocks + own hub. Gaps:

1. **Same-roadmap prev/next:** in the prerendered article, link the adjacent lessons in roadmap order (the hub index already has the ordered list at generation time). Adds 2 contextual links per page across all ~640 pages.
2. **dsa `related` field** (31 lessons have it) — render it as links; it's currently ignored.
3. **Cross-roadmap topical links** (hand-curated, in lesson content or a small map in the generator): the-gil ↔ threading-vs-multiprocessing ↔ concurrency-vs-parallelism; configdict-from-attributes ↔ sqlalchemy-sqlmodel-async; rag-evaluation ↔ evaluation-and-test-sets ↔ grounding-with-retrieval.
4. **Sitemap `<lastmod>`:** add from the content file's git commit date (fall back to file mtime). Helps recrawl prioritization after the P0-A content change ships.

---

## P2 · Deliberately deferred / do NOT do

- **No FAQPage rich-result markup** — Google restricted FAQ rich results to government/health sites (2023); the visible Q&A text from P0-A is what matters. `LearningResource` + `BreadcrumbList` already in place suffice.
- **No new pages purely for keywords.** All P1 additions live inside existing lessons. New lessons keep following the roadmap/content strategy, not SEO.
- **No llms.txt, no programmatic doorway pages, no title churn.** After P0-B, leave titles alone for ≥ 6 weeks; rankings need stable signals to settle.
- **Backlinks/distribution** (dev.to cross-posts with canonical back, Reddit/HN, "learn in public" threads) — the biggest lever for the RAG-evaluation-tier queries, but it's founder work, not repo work. Out of scope here.

---

## Ongoing · GSC-only keyword workflow (no paid tools)

Monthly, ~30 minutes:

1. GSC → Performance → 28-day window → Queries, sorted by impressions.
2. Shortlist queries at **position 11–30 with ≥ 5 impressions** — these are the winnable ones.
3. For each: does the mapped page's `<title>`/H2s contain the exact phrase? If not → add a heading/section (P1-A pattern) or adjust `seo.title` (only if the page hasn't been retitled in the last 6 weeks).
4. Queries with impressions but **no good page** → candidate for the next Antigravity content batch; note in `docs/BACKLOG.md`.
5. Free supplements when researching a specific page: Google autocomplete + "People also ask" for the primary query; Google Trends to compare phrasings (e.g., "rag evaluation" vs "rag testing").

### Trends findings — 2026-07-16 run (worldwide, 12-month, unless noted)

Checked live in Google Trends; fold into P0-B/P1-A wording where noted:

- **"llm evaluation" ≈ 3–4× "rag evaluation"** and climbing steeply; "rag testing"/"llm evals" are noise. → The rag-evaluation `seo.title`/description should carry "LLM evaluation" phrasing alongside RAG (§P0-B table already does via "testing pipelines"; prefer "RAG & LLM evaluation…" if it fits 60 chars).
- **India (5-yr): "class 10 science" ≈ 5× "class 10 physics"** — CBSE's subject is *Science*, so students search "class 10 science". Physics lesson titles/descriptions should say "Class 10 Science (Physics)" where honest. Sharp annual spikes in board-exam season on a school-year ramp → physics content should be indexed by ~October to catch the ramp.
- **pydantic at all-time high** (Jun 2026 = 100); #1 rising related topic: **pydantic-settings (Breakout)** — validates that lesson as a growth page.
- **fastapi at all-time high**; real rising queries: "fastapi documentation" +900%, "fastapi docs" +700% (docs-as-truth demand).
- **"retrieval augmented generation" grew ~10×** over 12 months (9 → 100) and is still accelerating.
- **"ai engineer roadmap"** doubled+ over the year (avg 37 vs "machine learning roadmap" 52, "dsa roadmap" 20, "backend developer roadmap" 12); rising under it: **"agentic ai" +1,350%**, "forward deployed engineer" (Breakout), "system design engineer" (Breakout). Under "dsa roadmap": "striver a2z dsa sheet" +600% (the India competitor benchmark), "system design roadmap" +200%.
- **Caveat:** Trends "Related queries → Rising" is polluted with unrelated noise ("walmart near me", news queries) on mid/low-volume terms — trust Related *Topics* and percent-labelled query entries; ignore generic Breakout rows.

## Measurement

- **Judge on 28-day windows** (the July 1–14 baseline: 614 impressions, 0 content clicks, avg position 48).
- Success for this plan, ~6 weeks after P0 ships: configdict-from-attributes and 2+ other python-backend pages in the **top 10** for their primary query; first organic (non-brand) clicks; impressions ≥ 3× baseline.
- Watch the 15 priority pages individually (GSC → Pages → filter by URL).
- Expectation-setting: `rag evaluation` (position 82) will not reach page 1 from on-page work alone — it needs the P1 depth *and* external links *and* time. The python-backend long-tail is where page 1 happens first.

## Suggested execution order

1. P0-A (prerender full content) — one script, all pages, biggest lever.
2. P0-B (seo override mechanism + the two tables) — touches validator, generator, LessonView.
3. Deploy together, request indexing for the 15 priority URLs, note the date.
4. P1-A content edits via Antigravity batch; P1-B linking alongside.
5. Monthly GSC loop thereafter.
