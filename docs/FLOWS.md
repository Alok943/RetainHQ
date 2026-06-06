# RetainHQ — Application Flows

How the app behaves end-to-end: what happens when a button is clicked, a form is
submitted, a page loads. Each flow traces **UI → `apiFetch` → FastAPI → Postgres → back → UI**.

Legend: 🔒 = requires login · ⚠️ = currently mock / not wired · ✅ = live

---

## 0. The one data path (every authenticated request)

This wraps **every** backend call in the app — read it once, then assume it everywhere below.

1. A component calls `apiFetch(endpoint, options)` (`frontend/src/lib/api.js`).
2. `apiFetch` calls `supabase.auth.getSession()` to get the current **access token (ES256 JWT)**. No session → throws `Not authenticated`.
3. It attaches `Authorization: Bearer <jwt>` + `Content-Type: application/json` and fetches `${VITE_API_BASE_URL}${endpoint}`.
4. **FastAPI** runs the `get_current_user` dependency (`api/deps.py` → `core/security.py: verify_token`):
   - `PyJWKClient` fetches Supabase's public keys from `…/auth/v1/.well-known/jwks.json` (cached 1h), picks the key by `kid`, verifies the signature, checks `role == "authenticated"`.
   - Returns a `SupabaseUser` (`.id`, `.email`, `.role`). JWKS unreachable → **503**; bad/expired token → **401/403**.
5. The route handler runs, **scoping every query to `current_user.id`** (IDOR-safe), via an async `asyncpg` session (`get_db`).
6. Response JSON → `apiFetch` returns it (or throws `Error(detail)` on non-2xx) → component updates state.

> Frontend never touches Postgres directly (no `supabase.from(...)`). Supabase = auth + managed DB only.

---

## 1. 🔒 Auth & session — `Login.jsx`, `App.jsx`

**Page load (unauthenticated):**
1. `App.jsx` mounts → `supabase.auth.getSession()`. While resolving → "Loading…".
2. No session → render `<Login />` (the always-dark landing page).

**Click "Get Started" / "Login" / "Continue with Google":**
1. `handleGoogleLogin` → `supabase.auth.signInWithOAuth({ provider:'google', redirectTo: origin })`.
2. Browser redirects to Google → back to the app with a `?code=` (PKCE).
3. `App.jsx`'s `getSession()` / `onAuthStateChange` parses the code, sets `session`, and strips `?code=` from the URL.
4. With a session, `App.jsx` renders the **app shell** (sidebar/nav + routed page). Default route `/` → `Home`.

**Sign out:** `supabase.auth.signOut()` → `session` becomes null → shell unmounts → `Login` shown.

---

## 2. 🔒 App shell & navigation — `App.jsx`

- **Desktop:** left sidebar (Home, Reviews, Roadmaps, Analytics) + "Log Activity" button + user/sign-out. **Mobile:** top bar + bottom tab nav.
- Nav items call `navigate('/path')` (React Router). Active tab derived from `location.pathname`.
- Routes: `/` Home · `/reviews` Review · `/log` LogActivity · `/roadmaps` Roadmaps · `/roadmaps/:id` RoadmapDetail · `/analytics` Analytics · `/profile` Profile.
- Logo mark is theme-aware (`logoVariant = theme==='dark' ? 'light' : 'dark'`).

---

## 3. 🔒 ✅ Home dashboard — `Home.jsx`

**On mount:** `Promise.all([ apiFetch('/api/dashboard/'), apiFetch('/api/reviews/due') ])`.
- `GET /api/dashboard/` → `{ due_count, consistency_window, daily_progress, total_activities, total_reviews_completed }` (all computed live, scoped to user).
- `GET /api/reviews/due` → array of due reviews (status `due`, `scheduled_for ≤ now`), each with its `activity` eager-loaded (`selectinload`).

**Render states:** loading skeletons → error card → else:
- **Top due review card:** first due review's `activity.topic` + `key_memory`, with a day-label derived from `scheduled_for − activity.created_at`. **"Start Reviews"** → `navigate('/reviews')`. If none due → "all caught up".
- **QuickStats:** real consistency / due / daily-progress from the dashboard payload.
- **MomentumCard:** intentionally a **"Phase 2"** placeholder (no fabricated score).
- **"View Roadmap"** → `navigate('/roadmaps')`.

---

## 4. 🔒 ⚠️ Log Activity — `LogActivity.jsx`  **(NOT WIRED — top-priority fix)**

**Intended flow:**
1. User fills Topic, (Track/Roadmap/Type), Key Memory, optional Mistake, Difficulty (1–5), "needed a hint".
2. Click **"Log & Schedule Review"** → `POST /api/activities/` with the form body.
3. Backend creates the `activity`, then `services/scheduler.py` auto-creates **4 reviews at +3/+7/+14/+30 days IF `difficulty ≥ 4` OR `needed_hint`**.
4. Redirect to Home; the new reviews eventually surface in `/reviews/due`.

**Current reality:** ⚠️ The form is **static UI only** — no state for Topic/Key Memory/Mistake, no `apiFetch` import, and the submit button has **no `onClick`**. Track/Roadmap/Activity-Type are hardcoded `<option>`s. **Nothing is sent; no activity is created.** Until this is wired, the entire downstream loop can't run from the UI.

---

## 5. 🔒 ✅ Review flow (the retrieval gate) — `Review.jsx`

The product's core mechanic: **commit before reveal.**
1. **On mount:** `GET /api/reviews/due` → builds the queue. Loading / "all caught up" / error states.
2. **Per card:** shows the cue (`activity.topic`). A textarea + **"I don't know"** — the **Reveal button stays disabled until the user types an answer or taps "I don't know"** (this is the gate; no peeking).
3. **Reveal:** shows `activity.key_memory` (the answer) + the user's own attempt (self-compare) + prior `mistake` if any.
4. **Rate:** Easy / Medium / Hard (+ an objective got-it/missed-it → `recalled`).
5. **Submit:** `POST /api/reviews/{id}/complete` with `{ rating, recalled }`. Backend (IDOR-safe): 404 if not owned, 400 if already done; else sets `status='completed'`, `completed_at`, `rating`, `recalled`. **Rating is stored only — it does NOT reschedule anything yet** (SM-2 is Phase 2).
6. Advance to next card; on finish → back to Home.

---

## 6. 🔒 ✅ Roadmaps list — `Roadmaps.jsx`

- **On mount:** `GET /api/roadmaps/` → each roadmap with **server-computed** `progress_pct`, `done_nodes`, `total_nodes` (joins `user_progress` for this user).
- Renders cards (title, %, progress bar, n/total). Click a card → `navigate('/roadmaps/:id')`.
- (Fake "Explore Templates" + non-functional import rail were removed.)

---

## 7. 🔒 ✅ Roadmap detail — `RoadmapDetail.jsx`

- **On mount:** `GET /api/roadmaps/{id}` → `{ title, description, nodes[], per-node status }`. Nodes laid out as a **React Flow + dagre** flowchart: `phase` = vertical step-spine; topics branch off; `tier` → colored dot.
- **Left-click a topic:** optimistic toggle, then `PUT /api/roadmaps/nodes/{id}/progress` `{status:'done'|'not_started'}` (idempotent upsert in `user_progress`). Reverts on failure. Camera pans to the completed node; header `%` updates.
- **Right-click a topic:** opens the **notes popup** → shows the node's `description`. If it's a URL (NeetCode nodes), renders a **"Solve on NeetCode"** link button instead.
- **Double-click a topic:** expands/collapses child subtopics (nodes with `parent_id`), if any.
- **"PDF" button:** client-side `jsPDF` export — navy header band, progress bar, phase cards, completion checkboxes, tier badges, page footers. Downloads `<Roadmap-Title>.pdf`. No backend call.

---

## 8. 🔒 ✅ Analytics — `Analytics.jsx`

- **On mount:** `GET /api/dashboard/`.
- **Real stat cards:** Consistency (x/7), Activities Logged, Reviews Completed, Reviews Due — all live.
- **Retention insights:** Learning Momentum / Retention Strength / Review Compliance shown as labelled **"Phase 2" placeholders** (no fabricated numbers — they need recall history + the SM-2/metrics work first).

---

## 9. 🔒 Profile — `Profile.jsx`

- **On mount:** `supabase.auth.getUser()` → renders email, initials, member-since, user id (Supabase client, not the backend — identity data only).
- **Appearance toggle:** flips dark mode (see §10).
- **Sign Out:** `supabase.auth.signOut()` → returns to Login.
- ⚠️ **Dev "Copy JWT"** button copies the access token to clipboard — pre-prod cleanup item.

---

## 10. Dark mode — `lib/theme.jsx`, `index.css`, `index.html`

- `ThemeProvider` holds `theme` ('light'|'dark'), persisted to `localStorage('retainhq-theme')`, defaulting to system preference.
- Toggling adds/removes `.dark` on `<html>`. A **pre-paint script in `index.html`** applies it before first render (no flash).
- Theming is a **centralized override layer in `index.css`**: under `html.dark`, the app's hardcoded color utilities (`bg-white`, `text-[#0F172A]`, etc.) are remapped — so components inherit dark mode for free *if they reuse existing color classes*.
- The **Login page is intentionally always-dark** (theme-independent via inline styles).

---

## Cross-cutting failure modes

- **No internet / DNS blip:** JWKS fetch or DB connect can fail with `getaddrinfo failed`. Auth now degrades to a clean **503** (not a 500), and the DB pool uses `pool_pre_ping` to recycle dead connections. Usually a transient network issue, not a code bug.
- **Expired/invalid token:** `verify_token` → **401** → frontend should route back to login.
- **Ownership violation (IDOR):** mutating a row you don't own → **404** (never leaks existence).
