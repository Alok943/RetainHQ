# HANDOFF: Sentry + Web Push (PWA) + Learning Analytics

Status: **implemented** (2026-07-13, 13 commits, code-complete and gated-off — see SYSTEM-OVERVIEW.md Changelog for the summary). Remaining work is the founder-action checklist below (Sentry projects, VAPID keygen, env vars) — everything else in this doc is done.
Read `CLAUDE.md` + `docs/SYSTEM-OVERVIEW.md` first. All conventions there apply (RLS on new tables, no-op-when-unset env keys, ownership-scoped queries, SYSTEM-OVERVIEW + Changelog in the same commit, no Co-Authored-By, never push without explicit user "push").

## Context

- Production (retainhq.app) has **zero error visibility**: backend has no logging and no exception handlers (`backend/app/main.py` is bare); frontend has no top-level ErrorBoundary and no error reporting (only a feature-local boundary in `frontend/src/physics/three/Physics3D.jsx`).
- Notifications are **email-only**: GitHub Actions cron (`.github/workflows/reminders.yml`, 01:30 UTC) → `POST /api/internal/send-reminders` (X-Cron-Secret) → `backend/app/services/reminders.py::send_due_reminders` → Resend via `services/mailer.py`. Idempotency via `ReminderLog` (unique `user_id + sent_on`).
- **PostHog is already fully wired** in `frontend/src/lib/analytics.js` (privacy-first: autocapture off, cookieless, pseudonymous id, curated `EVENTS` vocab, ~10 call sites). It no-ops without `VITE_POSTHOG_KEY` — activation is a founder env-var action, not code.
- Learning-insight data largely exists (`Review.recalled/rating/quality/ai_recalled`, `Activity` FSRS `stability`/`difficulty_fsrs` + `source_type`, `TestAttempt.results` JSONB) but there are **no duration/timing columns** and no `metric_events` table (BACKLOG item).

Founder decisions (locked): full push + PWA (no MVP cut); analytics = schema additions + aggregations; push content = mirror the daily email digest only.

Sequencing: **A (Sentry) → B (Push/PWA) → C (Analytics)**. Each phase = one commit.

⚠️ **Dirty-tree warning:** as of 2026-07-12 the working tree holds an uncommitted syllabus-quota feature touching `backend/app/core/config.py`, `backend/app/models/models.py`, `backend/app/api/routes/syllabus.py`, `docs/*`. That work must be committed (by the founder) **before** starting, or phase commits will mix unrelated changes.

## Key decisions (each needs a DECISIONS.md entry when implemented)

1. **No custom global exception handler.** sentry-sdk's FastAPI integration captures unhandled exceptions itself; a custom `@app.exception_handler(Exception)` risks suppressing capture. DO add `logging.basicConfig(level=INFO)` in `main.py` so Render logs carry tracebacks even with Sentry off.
2. **Pseudonymous only.** `send_default_pii=False` both sides; `set_user({"id": <supabase uuid>})` only — never email (matches `analytics.js`). Errors sampleRate 1.0, traces 0.1, **no Session Replay**.
3. **Hand-rolled push-only `sw.js`, NOT vite-plugin-pwa.** SPA is online-only; precaching invites stale-chunk 404s across Vercel deploys. Push-only SW has **no fetch handler** → network path untouched.
4. **Single `ReminderLog` claim gates both channels** (email + push): identical content/cadence; "miss a day rather than spam" stance preserved. Add a `channel` column only if channels ever diverge.
5. **`duration_ms` int on `reviews` (not `started_at`).** Frontend measures with `performance.now()` (no clock skew); backend clamps to (0, 1_800_000 ms] else NULL.
6. **Generic `metric_events` JSONB table.** Backlog signals are heterogeneous/exploratory. Server-side writes via helper by default + ONE allowlisted client POST with ~2KB payload cap. Note: grader calibration and depth-mode retention need NO new capture (derivable from `reviews.recalled` vs `ai_recalled` and `question_sets.depth`).

## New env vars (all follow the empty-default no-op convention in `backend/app/core/config.py`)

| Var | Where | Purpose |
|---|---|---|
| `SENTRY_DSN`, `SENTRY_ENVIRONMENT` (default "development"), `SENTRY_TRACES_SAMPLE_RATE` (0.1) | Render | backend Sentry |
| `VITE_SENTRY_DSN`, `VITE_SENTRY_RELEASE` (=`VERCEL_GIT_COMMIT_SHA`), `SENTRY_AUTH_TOKEN` (build) | Vercel | frontend Sentry + sourcemap upload |
| `VAPID_PRIVATE_KEY`, `VAPID_PUBLIC_KEY`, `VAPID_SUBJECT` (default `mailto:reviews@retainhq.app`) | Render | web-push signing; public key served via API |
| `VITE_POSTHOG_KEY` | Vercel | activates already-shipped analytics wrapper |

New deps — backend `pyproject.toml`: `sentry-sdk[fastapi]`, `pywebpush`; frontend: `@sentry/react`, dev `@sentry/vite-plugin`.

## Workstream A — Sentry (3 commits)

**A1 — backend.**
- `backend/app/core/config.py`: `SENTRY_DSN: str = ""`, `SENTRY_ENVIRONMENT: str = "development"`, `SENTRY_TRACES_SAMPLE_RATE: float = 0.1`.
- `backend/app/main.py` (before `app = FastAPI(...)`): `logging.basicConfig(level=logging.INFO)`; gated on `settings.SENTRY_DSN`: `sentry_sdk.init(dsn, environment, release=os.environ.get("RENDER_GIT_COMMIT"), traces_sample_rate, send_default_pii=False)`.
- `backend/app/api/deps.py::get_current_user`: `sentry_sdk.set_user({"id": str(user.id)})` guarded on `settings.SENTRY_DSN`.
- Verify: uvicorn boots with no DSN (no-op path); with a local DSN a temporary raise in a route lands in Sentry with UUID-only user; `/docs` renders.

**A2 — frontend.**
- New `frontend/src/lib/errors.js` mirroring `analytics.js`: `initErrorTracking()` (Sentry.init gated on `VITE_SENTRY_DSN`; sampleRate 1, tracesSampleRate 0.1, no replay, release/environment), `captureError(err, ctx)`, `setErrorUser(id)`, `clearErrorUser()` — every call silent no-op without DSN.
- New `frontend/src/ErrorBoundary.jsx`: small **custom** class component (not `Sentry.ErrorBoundary` — must work with Sentry off); `componentDidCatch → captureError`; fallback = centered card, "Something went wrong", Reload + back-to-dashboard buttons, styled with the app's **literal hex classes** so the `index.css` dark override layer restyles it.
- `frontend/src/main.jsx`: `initErrorTracking()` next to `initAnalytics()`; wrap `<App/>` in `<ErrorBoundary>` (inside ThemeProvider + BrowserRouter so the fallback is themed).
- `frontend/src/lib/api.js` (`apiFetch`): capture **only** `status >= 500` (with `{endpoint, status}`) and network-catch errors (`{endpoint, network: true}`). Never 401/403/404/429.
- `frontend/src/lib/AuthContext.jsx`: `setErrorUser(id)` alongside `identifyUser(id)`; `clearErrorUser()` alongside sign-out/reset.
- Verify: no DSN → zero console noise; temp component throw → themed fallback in light AND dark; kill backend → network error captured once; forced 404 → NOT captured.

**A3 — sourcemaps.**
- `npm i -D @sentry/vite-plugin`; in `frontend/vite.config.js` after `react()`: `sentryVitePlugin({org, project, authToken: process.env.SENTRY_AUTH_TOKEN, disable: !process.env.SENTRY_AUTH_TOKEN})`.
- Verify: `npm run build` without token → silent no-op, build green.

## Workstream B — Web Push + PWA (5 commits)

**B1 — manifest + icons.**
- Generate `frontend/public/icon-192.png`, `icon-512.png`, `icon-512-maskable.png` from existing favicon (one-off script, not committed).
- New `frontend/public/manifest.webmanifest`: name/short_name RetainHQ, `start_url "/dashboard"`, `display "standalone"`, `theme_color "#0b0f1a"`, `background_color "#f9f9f6"`, icons incl. maskable.
- `frontend/index.html`: `<link rel=manifest>`, `meta apple-mobile-web-app-capable`, `meta apple-mobile-web-app-title` (apple-touch-icon already exists at line 6).
- Verify: DevTools Application → Manifest, no warnings.

**B2 — service worker + client lib.**
- New `frontend/public/sw.js` (~40 lines): `install → skipWaiting`; `activate → clients.claim`; `push` → parse `{title, body, url}` → `showNotification(title, {body, icon: '/icon-192.png', data: {url}})`; `notificationclick` → focus existing client or `openWindow(url)`; `pushsubscriptionchange` → best-effort resubscribe + re-POST. **NO fetch handler** (decision 3).
- New `frontend/src/lib/push.js`: `isPushSupported()`, `getPushState()` (unsupported|denied|prompt|subscribed), `registerSW()`, `subscribePush()` (register → `GET /api/push/vapid-public-key` → `pushManager.subscribe({userVisibleOnly: true, applicationServerKey: urlBase64ToUint8Array(key)})` → `POST /api/push/subscribe` with endpoint/p256dh/auth/userAgent), `unsubscribePush()`.
- On app load (main.jsx or AuthContext): if `Notification.permission === 'granted'` → `registerSW()` only. **Never prompt on load.**
- Verify: localhost is a secure context — SW activates; DevTools "Push" test button fires a notification; confirm no fetch interception after rebuild.

**B3 — backend table + routes + service.**
- `models/models.py`: `PushSubscription` — id pk, `user_id` (idx), `endpoint` (unique), `p256dh`, `auth`, `user_agent` optional, `created_at`.
- Alembic migration: table + unique(endpoint) + index(user_id) + **`ALTER TABLE public.push_subscriptions ENABLE ROW LEVEL SECURITY`** (no policies — repo convention).
- New `backend/app/services/push.py`: `is_configured()`, `send_push(sub_row, payload)` via `pywebpush.webpush(subscription_info=..., data=json.dumps(payload), vapid_private_key=..., vapid_claims={"sub": settings.VAPID_SUBJECT})`; raise typed `PushGone` when WebPushException status ∈ (404, 410), `PushError` otherwise.
- New `backend/app/api/routes/push.py` + `backend/app/schemas/push.py`:
  - `GET /api/push/vapid-public-key` — 404 when unconfigured (single source of truth in Render env; avoids Vercel/Render key-sync hazard).
  - `POST /api/push/subscribe` — raw `INSERT ... ON CONFLICT (endpoint) DO UPDATE` user_id/p256dh/auth (same `text()` style as reminders.py).
  - `DELETE /api/push/subscribe` — by endpoint, `WHERE user_id = current_user.id`, 204.
- Router in `main.py` at `/api/push`.
- Verify: `alembic upgrade head` on dev DB; `rowsecurity=true` for the table; `/docs` shows 3 routes; unconfigured → vapid key 404; POST/DELETE round-trip.

**B4 — subscribe UX.**
- `frontend/src/Profile.jsx`: "Daily reminder notifications" toggle (pattern-match the dark-mode toggle row): reflects `getPushState()`; iOS hint when `PushManager` absent ("On iPhone, add RetainHQ to your Home Screen first"); toast on permission denial.
- `frontend/src/Review.jsx` done-screen: one-time dismissible card gated on `Notification.permission === 'default'` + localStorage flag → `subscribePush()`.
- `analytics.js` EVENTS: add `push_subscribed`, `push_unsubscribed`; fire from callers.
- Verify: toggle on → prompt → row in `push_subscriptions` with your user_id; toggle off → row gone + browser sub removed; card shows once, never after dismissal.

**B5 — reminder fan-out.**
- `backend/app/services/reminders.py`: early-return becomes `if not mailer.is_configured() and not push.is_configured()`. After the per-user ReminderLog claim: email as today (skip if mailer unconfigured); then fetch that user's push subscriptions and for each `await asyncio.to_thread(push.send_push, sub, payload)` with payload `{title: "N reviews due", body: "...", url: APP_BASE_URL + "/reviews"}`. On `PushGone` → delete sub row + commit; on `PushError` → count in errors. Summary gains `push_sent/push_errors/push_pruned`.
- Verify E2E on localhost: subscribe in browser; ensure a due review; `curl -X POST localhost:8000/api/internal/send-reminders -H "X-Cron-Secret: <local>"` → OS notification fires, click lands on `/reviews`; second curl no-ops (claim held); email-only users unaffected.

## Workstream C — Analytics (1 founder step + 5 commits)

**C0 — PostHog activation (founder, no code).** Create PostHog project → set `VITE_POSTHOG_KEY` in Vercel → redeploy.

**C1 — review duration capture.**
- Migration: `ALTER TABLE reviews ADD COLUMN duration_ms integer` (nullable; existing table — no new RLS).
- `models.py` Review: `duration_ms: Optional[int] = None`. `schemas/review.py` `ReviewComplete.duration_ms: Optional[int] = None`.
- `routes/reviews.py::complete_review`: persist, clamped — if not `0 < duration_ms <= 1_800_000` → None.
- `frontend/src/Review.jsx`: stamp `performance.now()` at card show/reset; send `duration_ms` in the complete POST; add to `review_completed` PostHog props.
- Verify: complete a review locally → plausible value in row; fake 31-min value → NULL.

**C2 — metric_events.**
- Model `MetricEvent`: id, `user_id` (idx), `event_type` (str, idx), `entity_id` (uuid, nullable), `payload` JSONB, `created_at`. Migration **with ENABLE ROW LEVEL SECURITY**.
- New `backend/app/services/metrics.py::record_metric_event(db, user_id, event_type, payload=None, entity_id=None)` — no commit (caller's transaction).
- First server-side producer: syllabus commit flow records `extraction_edit_delta` (added/removed/renamed node counts vs LLM draft) in `routes/syllabus.py`.
- New `backend/app/api/routes/metrics.py`: `POST /api/metrics/events` — allowlisted `CLIENT_EVENT_TYPES` (start: `review_depth_chosen`), payload ≤ 2KB, 204. Router at `/api/metrics`.
- Also: strike the `metric_events` line from `docs/BACKLOG.md` in this commit.
- Verify: rowsecurity check; allowlisted POST → row; disallowed type → 400/422.

**C3 — aggregation endpoints on `routes/dashboard.py`** (one per card, FILTER-aggregate style, each with an `enough_data` floor like `REVIEW_METRICS_MIN`; schemas in `schemas/dashboard.py`):
- `GET /source-retention` — Review join Activity, group by `source_type` (NULL → 'other'): completed, recalled, recall_rate; groups ≥ 3 completed. Fills the "Retention by Source" ComingSoonBanner.
- `GET /calibration` — rows where `ai_recalled IS NOT NULL`: agreement rate, overconfident (recalled ∧ ¬ai_recalled), underconfident (¬recalled ∧ ai_recalled).
- `GET /memory-strength` — `Activity.stability IS NOT NULL`: histogram (<1d, 1–7d, 7–30d, 30–90d, >90d), median, count.
- `GET /node-accuracy` — `text()` SQL, `jsonb_array_elements(test_attempts.results)` grouped by node_title: got/missed/wrong; weakest N (≥ 2 results/node).
- `GET /time-of-day` — completed reviews by `extract(hour from completed_at)` (UTC; frontend shifts local via `getTimezoneOffset`): count, recall_rate, avg duration_ms.
- Verify: hand-check numbers via read-only Supabase MCP against founder account; empty-history user → `enough_data: false` everywhere, no 500s.

**C4 — Analytics UI (`frontend/src/Analytics.jsx`).**
- Extend the Promise.all; each new fetch `.catch(() => null)` so sections degrade independently.
- Replace Retention-by-Source ComingSoonBanner with real per-source rows (MetricCard-style bars).
- New sections, hand-rolled divs (no chart lib), StatCard/MetricCard visual language, hex-literal classes for dark mode: calibration card, 5-bar strength histogram, 24-bar time-of-day, weakest-nodes list (got/missed/wrong pills).
- Verify: both themes; sparse-data states.

**C5 — PostHog event audit.**
- Add to EVENTS + wire: `pwa_installed` (`window 'appinstalled'` listener in main.jsx), `syllabus_committed`, `review_skipped` (only if a skip affordance exists — audit), `feedback_sent` (audit call sites). Keep vocabulary curated.

## Founder-action handoff (dashboard work, not code)

1. Sentry: create org + 2 projects (retainhq-backend python/fastapi, retainhq-frontend react); copy DSNs.
2. Render env: `SENTRY_DSN`, `SENTRY_ENVIRONMENT=production`; later `VAPID_PRIVATE_KEY`/`VAPID_PUBLIC_KEY`/`VAPID_SUBJECT`. Redeploy.
3. Generate VAPID keypair once, locally: `vapid --gen` (py-vapid CLI, installs with pywebpush). Both keys → Render only.
4. Vercel env: `VITE_SENTRY_DSN`, `VITE_SENTRY_RELEASE=$VERCEL_GIT_COMMIT_SHA`, `SENTRY_AUTH_TOKEN` (project:releases scope), `VITE_POSTHOG_KEY`. Redeploy.
5. Prod migrations: Dockerfile already runs `alembic upgrade head` on deploy (3 new migrations: push_subscriptions, reviews.duration_ms, metric_events).
6. Post-deploy smoke: test error each side → Sentry; subscribe on retainhq.app + workflow_dispatch the reminders Action → notification received; Supabase advisors show no new RLS warnings.
7. iPhone: Add to Home Screen → open → Profile → enable notifications.

## Docs obligations (same-commit rule)

- `docs/SYSTEM-OVERVIEW.md`: integrations (Sentry, web push), new endpoints (`/api/push/*`, `/api/metrics/events`, 5 dashboard GETs), new tables (push_subscriptions, metric_events), new env vars — each in the phase commit that introduces it, + Changelog line.
- `docs/DECISIONS.md`: entries for decisions 1, 3, 4, 5, 6 above.
- `docs/BACKLOG.md`: strike `metric_events` line at C2.
