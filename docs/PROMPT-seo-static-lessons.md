# TASK: Static lesson HTML + crawlable internal links (SEO)

You are working in the RetainHQ monorepo (`frontend/` = React 19 + Vite SPA on Vercel,
lesson content = one JSON per lesson under `content/roadmaps/<roadmapKey>/<slug>.json`,
synced to `frontend/public/content/` by `frontend/scripts/sync-content.mjs`, which runs
as `predev`/`prebuild` and already emits `manifest.json` + `sitemap.xml`).

## Why (context — read once, then build)

The app is a client-rendered SPA: every URL returns an empty `<div id="root">` + JS.
Google renders JS (slowly, low priority); Bing/DuckDuckGo/AI crawlers (ChatGPT,
Perplexity) mostly do NOT — so the 435 static lessons are invisible to them. Also, all
in-app navigation is `onClick={() => navigate()}` (buttons, not links), so crawlers see
**zero internal links** — no link graph, no authority flow.

Two deliverables fix this:

1. **Generate a real static HTML file per lesson at build time** (pure templating from
   the lesson JSON — no SSR, no headless Chrome, no framework change). On Vercel the
   filesystem is served **before** the SPA rewrite in `frontend/vercel.json`, so bots
   get real HTML at each lesson URL while the React app still boots on top for humans.
2. **Make internal navigation crawlable** (`<a href>` / react-router `<Link>`), and add
   a prev/next + related-lessons link mesh on lesson pages (the graph already exists in
   each lesson's `metadata.prerequisites` / `metadata.unlocks` — both are slug arrays).

---

## Deliverable 1 — `frontend/scripts/generate-lesson-html.mjs` (post-build)

### Wiring
- New script, plain Node ESM (match the style of `sync-content.mjs`).
- Add to `frontend/package.json`: `"postbuild": "node scripts/generate-lesson-html.mjs"`.
  It must run AFTER `vite build` because it uses `dist/index.html` (with the final
  hashed asset tags) as its template. Do NOT write into `public/` (files there bypass
  Vite's HTML transform and would miss the script tags). Write into `dist/` only —
  `dist/` is already gitignored, nothing new to ignore.
- Dev mode needs nothing: this is prod-crawler-only machinery.

### For each lesson JSON under `content/roadmaps/<roadmapKey>/*.json`
Output file: `dist/roadmaps/<roadmapKey>/learn/<slug>/index.html`
(slug = `lesson.slug || filename without .json`). Vercel serves `/a/b` from
`a/b/index.html` on the filesystem pass, so the URL matches the SPA route exactly.

Build each file by transforming a copy of `dist/index.html`:

1. **Replace** (never append — the template already contains one of each; duplicated
   tags are the exact bug this repo previously fixed):
   - `<title>…</title>` → `<Lesson Title> · <RoadmapLabel> | RetainHQ`
   - `<meta name="description" content="…">` → lesson description (see extraction below),
     max 158 chars, whitespace-collapsed, HTML-attribute-escaped.
   - `<link rel="canonical" href="…">` → `https://retainhq.app/roadmaps/<rk>/learn/<slug>`
   - `<meta property="og:url" …>` → same URL; `og:title` + `twitter:title` → page title.
   - Keep everything else in `<head>` untouched (theme script, icons, og:image, @graph).
2. **Append one** `<script type="application/ld+json">` before `</head>` containing an
   array of two objects (mirror the shapes already used in
   `frontend/src/LessonView.jsx` — search for `seoLd`): a `LearningResource` (name,
   description, url, inLanguage:"en", learningResourceType:"lesson", isPartOf Course
   named `<RoadmapLabel> — RetainHQ`, publisher Organization RetainHQ) and a
   `BreadcrumbList` (Roadmaps → `<RoadmapLabel>` → lesson title). `JSON.stringify` the
   array — never hand-build JSON strings.
3. **Inject readable article content into `<div id="root">`** (replacing the current
   `<noscript>` block inside it): a plain `<article>` with the lesson prose (see
   extraction). React replaces `#root`'s children on mount, so users see the static
   article only for a moment before the app takes over — that is expected and fine.
   Do NOT hide the article with CSS (hidden text is an SEO negative). Give it minimal
   inline-styled readability (max-width, padding, system font) so the pre-hydration
   flash looks intentional, and dark text on light background.
4. **Internal links inside the article** (this builds the crawl mesh — do not skip):
   - Breadcrumb links: `<a href="/roadmaps">Roadmaps</a> › <a href="/roadmaps/<rk>"><RoadmapLabel></a>`.
   - A "Continue learning" list: for every slug in `metadata.prerequisites` and
     `metadata.unlocks` that exists as a lesson file in the SAME roadmap folder, emit
     `<a href="/roadmaps/<rk>/learn/<thatSlug>"><that lesson's title></a>`. Build a
     slug→title index for the roadmap first; silently skip slugs with no file.
   - A link to the app: `<a href="/roadmaps/<rk>/learn/<slug>">Open this lesson in RetainHQ</a>`
     is NOT needed (it's this page). Instead link the roadmap page once more at the end.

### Content extraction (lesson JSONs are heterogeneous — be tolerant)
Lessons have `kind` ∈ {concept, aptitude, reasoning, theory, dsa} with different fields.
Write ONE tolerant extractor, not per-kind renderers:

- Description (for meta): first non-empty of `overview` (string), `hook.scenario`,
  `mental_model.text || mental_model` (if string), else fallback
  `Learn <title> and lock it into long-term memory with spaced repetition and active recall on RetainHQ.`
- Article sections: walk these top-level fields in order, rendering each that exists as
  `<h2><Label></h2>` + paragraphs: `hook.scenario`, `overview`, `why` / `why_it_matters`,
  `mental_model`, `explanation`, `analogy`, `method`, `formula`, `key_points` (array →
  `<ul>`), `shortcuts`, `common_mistakes` / `mistakes` (array of strings or
  `{mistake, why}` objects → `<ul>`), `recall_questions` / `recall` (render question
  text only, NOT answers).
- Values may be strings, arrays of strings, or objects with a `text`/`content`/`body`
  string field — handle all three; anything else (code blocks, viz configs, nested
  walkthroughs) SKIP silently. Never render code fields.
- **HTML-escape every piece of content** (`&`, `<`, `>`, `"`) — lesson prose contains
  code-ish characters. Attribute values escape quotes too.
- Malformed JSON: `console.warn` + skip that lesson (same behavior as sync-content).

### Roadmap labels
Copy this map into the script (source of truth is `ROADMAP_LABEL` in
`frontend/src/LessonView.jsx` — add a comment in BOTH places saying to keep them in
sync): python-swe→Python, sql→SQL, aptitude→Aptitude, core-cs→Core CS, dsa→DSA,
ai-engineering→AI Engineering, cpp-swe→C++, python-backend→Python Backend. Unknown
key → "RetainHQ".

### Log line
End with: `[generate-lesson-html] Wrote <N> static lesson page(s).`

---

## Deliverable 2 — crawlable internal links in the React app

Rule: wherever a click's only job is routing to a plain path, render a real link
(react-router `<Link to>` — it already handles ctrl/middle-click) instead of an
`onClick={() => navigate()}` on a div/button. Preserve ALL existing classNames and
visual output exactly; this is a semantics-only change. Where the element must carry
router state, use `<Link to={...} state={{...}}>` — `Link` supports `state`.

Convert these (find by grepping `navigate(`):
1. `frontend/src/Roadmaps.jsx` — roadmap cards → `/roadmaps/<slug or id>`.
2. `frontend/src/RoadmapDetail.jsx` — the "Learn"/lesson affordances that navigate to
   `/roadmaps/<id>/learn/<slug>` (keep the `state` they currently pass: `contentKey`,
   `nodeId`); the "Back to Roadmaps" button → `/roadmaps`.
3. `frontend/src/LessonView.jsx` — "Back to roadmap" buttons → `/roadmaps/<id>`.
4. `frontend/src/App.jsx` — `SidebarItem` and `NavItem`: add an optional `to` prop; when
   present render `<Link>` instead of `<button>` (same classes). Wire Home/Reviews/
   Roadmaps/Vault/Analytics/Admin items with their paths.
5. `frontend/src/Home.jsx` — cards/CTAs that route to `/reviews`, `/log`, `/roadmaps`.

Do NOT convert: sign-out, modal openers, toggle buttons, anything with side effects
beyond navigation, or handlers that branch (e.g. `requireAuth()` gating) — leave those
as buttons.

Also add to `LessonView.jsx` (React side, mirroring the static mesh): a small
"Continue learning" section at the end of the lesson rendering prerequisite/unlock
lessons as `<Link>`s. Resolve titles by fetching nothing new: the lesson JSONs for
sibling slugs are at `/content/roadmaps/<contentKey>/<slug>.json`, but do NOT fetch N
files — instead just render the slug prettified (`tcp-3-way-handshake` → "Tcp 3 Way
Handshake" is ugly; title-case words and uppercase known acronyms tcp/udp/ip/dns/sql/
api/os/http) OR skip the React-side section entirely if it gets complex. The static
HTML mesh (Deliverable 1) is the SEO-critical one; the React section is nice-to-have.

---

## Acceptance checks (run all before finishing)

1. `cd frontend && npm run build` — clean, then verify:
   - `find dist/roadmaps -name index.html | wc -l` equals the lesson count printed by
     sync-content (currently 435).
   - Pick `dist/roadmaps/core-cs/learn/tcp-vs-udp/index.html` and confirm BY READING IT:
     exactly ONE `<title>` (the lesson one), ONE meta description (lesson one), canonical
     = the lesson URL, hashed `/assets/*.js` script tag present, `<article>` contains
     real prose AND ≥3 internal `<a href="/roadmaps/...">` links, the appended JSON-LD
     parses with `JSON.parse`.
2. `npx vite preview` then open `/roadmaps/core-cs/learn/tcp-vs-udp` — the React app
   must still mount and replace the static article (no console errors, no double UI).
3. SPA nav still works: roadmap list → roadmap → lesson → back; sidebar items highlight
   the active tab exactly as before; ctrl+click a roadmap card opens a new tab.
4. `npm run lint` passes on changed files.

## Guardrails
- Do not touch `frontend/src/lib/useSeo.js`, `index.html`'s head block, `vercel.json`,
  the sitemap logic, backend code, or anything under `content/`.
- Do not add dependencies. Do not introduce SSR/frameworks. No headless browsers.
- Static titles/descriptions must byte-match what `useSeo` sets client-side (same
  format strings), so Google never sees the tags change during render.
- Commit style: single commit, message like
  `seo: static lesson HTML at build + crawlable internal links`, NO Co-Authored-By
  trailer, do NOT push.
