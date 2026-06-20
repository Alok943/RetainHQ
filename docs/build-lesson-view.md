# Build Spec: Lesson View + Content Serving (RetainHQ)

> Handoff spec for an agentic build (Antigravity). Self-contained — assume no prior
> conversation context. Read this fully before editing. Follow existing patterns.

## 1. Goal

RetainHQ is a learning-retention web app (React + Vite frontend on Vercel, FastAPI
backend on Railway, Supabase Postgres). Roadmaps are skill trees of topic "nodes."
We have started curating **per-topic lesson content** as JSON files. Your job:
surface that content as a **lesson view, opened from a roadmap node**, with a
**live Python execution visualizer** embedded.

**Key product decision (already made — do not change):** lessons are *node-anchored*.
There is NO separate "Learn" tab. A roadmap node that has content gets a "Learn"
affordance that opens its lesson. The roadmap is the syllabus; lessons hang off nodes.

## 2. What ALREADY EXISTS — use these, do not rebuild

- **Content files:** `content/roadmaps/<roadmapKey>/<slug>.json` (repo root, NOT under
  `frontend/`). Currently: `content/roadmaps/python-swe/primitive-types.json`,
  `dynamic-typing.json`, `closures.json`. Schema: `content/schema.json`.
- **The visualizer is built and verified** — DO NOT rewrite it:
  - `frontend/src/CodeTrace.jsx` — default export. Props: `code` (string, Python),
    `focus` (string, optional caption). Renders a "Visualize execution" button that
    lazily boots Pyodide, traces the snippet, and shows a line-by-line scrubber with
    variables + stdout. Just mount it: `<CodeTrace code={lesson.code_walkthrough.code} focus={lesson.code_walkthrough.focus} />`.
  - `frontend/src/lib/pyodideRunner.js` — `tracePython(code)`; CodeTrace uses it internally.
- **API client:** `frontend/src/lib/api.js` → `apiFetch(endpoint, { optionalAuth })`.
  (You will NOT need it for content — see §3 — but the roadmap detail already uses it.)
- **Roadmap detail page:** `frontend/src/RoadmapDetail.jsx`. It fetches a roadmap via
  `apiFetch('/api/roadmaps/:id', {optionalAuth:true})`, has a **list view** (component
  `ListView` → `TopicRow`) and a **map view** (React Flow). Each node has `{id, title,
  phase, section, tier, status, prerequisites, unlocks}`. This is where the "Learn"
  affordance goes.
- **Routing:** `frontend/src/App.jsx` (SPA shell + React Router routes). Roadmap detail
  is at `/roadmaps/:id`. Add the lesson route here.
- **Auth/PLG:** `frontend/src/lib/AuthContext.jsx` (`useAuth`, `requireAuth`). Lessons
  are READ-ONLY content, so they should be viewable by guests (no auth gate).

## 3. Architecture: serve content STATICALLY (no backend, no DB)

The lesson view only *displays* JSON. Do not add a DB table or FastAPI endpoint.
Instead, publish the content as static assets the frontend fetches.

### 3a. Sync script + manifest
Create `frontend/scripts/sync-content.mjs` (Node ESM):
- Read all `content/roadmaps/*/*.json` (path is `../content` relative to `frontend/`).
- Copy each into `frontend/public/content/roadmaps/<roadmapKey>/<slug>.json`.
- Emit `frontend/public/content/manifest.json` shaped as:
  ```json
  {
    "python-swe": {
      "Primitive types: int, float, bool, str": "primitive-types",
      "Dynamic typing and type()": "dynamic-typing",
      "Closures": "closures"
    }
  }
  ```
  i.e. `{ [roadmapKey]: { [exact node title]: slug } }`. Title is read from each
  JSON's `title` field; roadmapKey from its `roadmap` field; slug from `slug`.
- `frontend/public/content/` should be git-ignored OR committed — committing is fine
  and simplest; add it to the build either way.

Wire it into `frontend/package.json` scripts:
```json
"sync:content": "node scripts/sync-content.mjs",
"predev": "npm run sync:content",
"prebuild": "npm run sync:content"
```
So `npm run dev` / `npm run build` always refresh content first.

### 3b. Roadmap → content-key mapping
The frontend roadmap detail knows the roadmap's display **title** (e.g. "Python for
SWE") and UUID, but content is keyed by `roadmapKey` ("python-swe"). Add a small
interim map in a new file `frontend/src/lib/contentRoadmaps.js`:
```js
// Maps a roadmap's display title -> its content key under public/content/roadmaps/.
// Extend as more roadmaps get curated. (Interim until roadmaps carry a slug column.)
export const CONTENT_KEY_BY_TITLE = {
  'Python for SWE': 'python-swe',
};
```

## 4. Tasks

### Task A — sync script + manifest (§3a). Run it once; confirm files land in `public/content/`.

### Task B — Lesson route
In `App.jsx`, add a route `"/roadmaps/:id/learn/:slug"` → new component `LessonView`
(`frontend/src/LessonView.jsx`). Keep it inside the same app shell/layout as other pages.

### Task C — `LessonView.jsx`
- Read `:id` and `:slug` from the route. Look up the roadmap's content key: fetch the
  roadmap meta via `apiFetch('/api/roadmaps/'+id, {optionalAuth:true})` to get its
  `title`, then `CONTENT_KEY_BY_TITLE[title]`. (Or pass the key via router state from
  RoadmapDetail to avoid the refetch — optional.)
- Fetch the lesson: `fetch('/content/roadmaps/'+key+'/'+slug+'.json')` (plain fetch,
  NOT apiFetch — it's a static asset). Handle loading + 404 ("Lesson not available yet").
- Render these sections in order (match the data shape in §5):
  1. Header: `title`, a back link to the roadmap (`/roadmaps/:id`), tier + difficulty badges.
  2. **Overview**: `overview.what`, then `overview.why`. Chips for `overview.where_used`.
  3. **Why learn this**: bullet list `why_learning_this[]`.
  4. **Watch it run**: `<CodeTrace code={lesson.code_walkthrough.code} focus={lesson.code_walkthrough.focus} />`
     (only if `code_walkthrough` exists).
  5. **Common mistakes**: list of `{title, explanation}`.
  6. **Recall questions**: list of `{q, answer}` — render `q` with the `answer` hidden
     behind a "Reveal" toggle (this is a retention app — don't show answers by default).
  7. **Practice**: `practice_tasks[]` → `{title, prompt}`, with `starter_code`/`solution`
     in collapsed `<details>` blocks.
  8. **Challenge** (if present): `{title, prompt}`, `solution` collapsed.
  9. **Sources**: `sources[]` as external links (open in new tab, `rel="noopener"`).

### Task D — "Learn" affordance in `RoadmapDetail.jsx`
- On load, also `fetch('/content/manifest.json')` once; build a lookup for the current
  roadmap: `const slugByTitle = manifest[CONTENT_KEY_BY_TITLE[meta.title]] || {}`.
- In `TopicRow` (list view), if `slugByTitle[node.title]` exists, render a small
  **"Learn"** button/link → `navigate('/roadmaps/'+id+'/learn/'+slug)`. Nodes without
  content show nothing extra (keep the existing checkbox + notes behavior unchanged).
- Do not touch the completion checkbox, notes popup, or map-view gestures.

## 5. Lesson JSON shape (from content/schema.json)
```
slug, title, roadmap, kind ("concept"|"milestone"), tier ("tier1|2|3"),
metadata: { difficulty, estimated_minutes, importance, interview_frequency,
            prerequisites[], unlocks[], project_usage[] },
overview: { what, why, where_used[] },
why_learning_this: [string],
common_mistakes: [{ title, explanation }],
recall_questions: [{ q, answer, tier? }],
practice_tasks: [{ title, prompt, starter_code?, solution? }],
code_walkthrough?: { code, focus? },     // may be absent on older files
challenge?: { title, prompt, solution? },
sources: [url string]
```

## 6. Styling / conventions (MUST follow)
- Tailwind only. Match the existing palette: ink `#0F172A`, accent `#0891B2`, teal
  `#0F766E`, muted `#64748B`, surfaces `#f9f9f6`. Reuse the `glass-card` class for cards.
- Dark mode is automatic IF you reuse existing color utility classes (there's a
  centralized `html.dark` override layer in `index.css`) — so prefer the same classes
  already used in `RoadmapDetail.jsx`/`Home.jsx`. Do not hand-roll dark variants.
- Fonts: `font-sans` for prose, `font-mono` for code/values. Lucide for icons.
- NO direct `supabase.from(...)` calls in React (project rule). Backend access only via
  `apiFetch`. Static content via plain `fetch` of `/content/...` is fine.
- Keep the lesson view readable on mobile (single column, ~`max-w-3xl mx-auto`).

## 7. Verification (required before done)
1. `cd frontend && npm run dev`.
2. Open a Python for SWE roadmap → the list should show a **"Learn"** link on
   "Primitive types: int, float, bool, str", "Dynamic typing and type()", "Closures".
3. Click it → lesson view renders all sections.
4. In "Watch it run", click **Visualize execution** → Pyodide loads (a few seconds the
   first time), then the scrubber steps through the code with variables + output updating.
5. Reveal a recall answer; open a practice `solution`; click a source link.
6. Take a screenshot of the lesson view with the visualizer mid-trace.
7. Confirm nodes WITHOUT content show no "Learn" link and the checkbox still works.

## 8. Out of scope (do NOT do)
- No DB table / migration / FastAPI endpoint for content.
- Do not modify `CodeTrace.jsx` or `pyodideRunner.js`.
- Do not add a separate "Learn" tab in the nav.
- Do not wire recall questions into the spaced-repetition engine yet (display only).
```
