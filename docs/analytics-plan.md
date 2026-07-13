# RetainHQ — Analytics Plan

> **Living doc.** The disciplined event vocabulary for RetainHQ. Every event here earns a place in an AARRR funnel, the North Star, a retention curve, or a friction signal. **Do not add a firehose** — if a proposed event doesn't answer one of the questions below, it doesn't ship. The frontend vocabulary lives in [`frontend/src/lib/analytics.js`](../frontend/src/lib/analytics.js) (`EVENTS`); server-side events in [`backend/app/services/analytics.py`](../backend/app/services/analytics.py).

Instrumentation is PostHog, one project, keyed by the Supabase user id on both client (`posthog-js`) and server (`posthog` python), so a person's client + server events unify on one timeline.

---

## North Star

**Weekly successful active-recall reviews** — `review_completed` where `recalled = true`, unique users per week.

It's the one number that captures the thesis ("track what you remember, not what you complete") and only rises if acquisition, activation, and retention all work. Vanity-proof: a user can't inflate it without actually recalling material on schedule.

**Counter-metric:** review **lapse rate** — `review_completed` where `recalled = false` / all completions. Guards against gaming volume by burning through cards.

---

## AARRR — the five questions, mapped

| Stage | Question | Events | Where |
|---|---|---|---|
| **Acquisition** | Who lands, from where? | `$pageview` (+ referrer, auto), `landing_cta`, `signup_started` | Login, AuthModal |
| **Activation** | Did they reach the "aha"? | `signed_up`, `onboarding_started/completed`, `first_capture_shown`, `activity_logged`, **`activated`** | AuthContext, WelcomeModal, OnboardingGuide, FirstCapture, LogActivity |
| **Retention** | Do they return for due reviews? | `reviews_due_shown`, `review_started`, `review_completed`, `review_queue_empty`, `reminder_sent` (server), `reminder_clicked` | Home, Review, reminders.py, App |
| **Revenue** | (pre-revenue) | — none yet — | add `pricing_viewed`/`upgrade_clicked` when monetization exists |
| **Referral** | Do they share? | — none yet — | add `shared_*` when a share surface exists |

**Activation is defined** as firing `activated` — the first-ever `activity_logged` (backend signals it via `review_due_now`). It is the precondition for the North Star: a user who never captures a memory can never complete a review.

---

## Event catalog

Legend: **C** = client (`posthog-js`), **S** = server (`posthog` python). ✅ wired · ⬜ planned.

### Acquisition
| Event | C/S | Status | Key props | Notes |
|---|---|---|---|---|
| `$pageview` | C | ✅ | `path` | manual (autocapture off); `capture_pageleave:true` enables Web Analytics bounce/duration |
| `landing_cta` | C | ✅ | `action` | login / get_started / try_a_lesson |
| `signup_started` | C | ✅ | `source` | `landing_nav` \| `auth_wall` — OAuth click, before redirect |

### Activation
| Event | C/S | Status | Key props | Notes |
|---|---|---|---|---|
| `signed_in` | C | ✅ | — | every sign-in (incl. token refresh) |
| `signed_up` | C | ✅ | — | first-ever sign-in only (`created_at` within 2 min); deduped per user id |
| `onboarding_started` | C | ✅ | `surface` | `welcome_modal` \| `home_guide` |
| `onboarding_completed` | C | ✅ | `surface`, `finished`, `last_step` | `finished` = reached last step vs early dismiss |
| `first_capture_shown` | C | ✅ | — | the zero-activity gate rendered (the known funnel leak) |
| `activity_logged` | C | ✅ | `source_type`, `difficulty`, `first_activity` | |
| `activated` | C | ✅ | `via` | `first_capture` \| `log_activity` — first-ever capture |

### Retention
| Event | C/S | Status | Key props | Notes |
|---|---|---|---|---|
| `reviews_due_shown` | C | ✅ | `due_count` | Home surfaced ≥1 due review (return trigger); once per load |
| `review_started` | C | ✅ | `due_count` | |
| `review_completed` | C | ✅ | `outcome`, `rating`, `recalled`, `mode`, `ai_assisted` | **North Star source** |
| `review_queue_empty` | C | ✅ | — | opened /reviews with nothing due (friction/dead-end) |
| `review_scheduled` | S | ✅ | `first_review`, `immediate`, `rating`, `recalled`, `interval_days` | server-truth; rising `interval_days` across a cohort = memory sticking |
| `reminder_sent` | S | ✅ | `due_count`, `channel` | server-truth email metric |
| `reminder_clicked` | C | ✅ | — | arrived via `?src=reminder`; pair with `reminder_sent` for email CTR |

### Engagement (lessons → the loop)
| Event | C/S | Status | Key props | Notes |
|---|---|---|---|---|
| `lesson_opened` | C | ✅ | `roadmap`, `slug` | |
| `lesson_completed` | C | ✅ | `roadmap`, `slug` | end-of-lesson sentinel scrolled into view; `opened→completed` = lesson funnel |
| `card_created_from_lesson` | C | ✅ | `title` | the lesson → FSRS card bridge (content monetizes into retention) |
| `roadmap_opened` | C | ✅ | `roadmap` | |
| `test_started` / `test_completed` | C | ✅ | `roadmap`, `phase`, `score` | |

### Cross-cutting
| Event | C/S | Status | Key props | Notes |
|---|---|---|---|---|
| `auth_wall_hit` | C | ✅ | — | guest hit a write needing an account |
| `api_error` | C | ✅ | `endpoint`, `status`, `kind` | `network` (status 0) or `server` (5xx) only — 4xx are feature-gates, excluded |

---

## PostHog surfaces to turn on (config, not code)

1. **Web Analytics** — live (needs the `capture_pageleave` change to be deployed for bounce/duration).
2. **Funnels** — build: `signup_started → signed_up → first_capture_shown → activated → review_completed`. This is the activation funnel; the biggest leak is post-signup.
3. **Retention** — cohort by `signed_up`, returning event `review_completed`. This is the product's core promise made measurable.
4. **Cohorts** — "Activated" (fired `activated`), "Habitual" (≥3 `review_completed` in 7d).
5. **Session replay** — currently `disable_session_recording: true`. For an early startup, enabling replay on the activation flow (with input masking) is the single highest-leverage debugging tool. Not yet enabled — privacy story first (see SYSTEM-OVERVIEW §privacy).
6. **Experiments** — the "reading-first lesson layout" is an obvious first A/B test; wire a feature flag around it.

---

## Deliberately NOT tracked (and why)

- **Per-keystroke / per-scroll / per-hover** — noise, not signal. Web Analytics + the curated set answer the funnel questions.
- **4xx API errors** — used as feature gates (404 = grader off) and form validation; tracking them would drown the real `api_error` signal.
- **Every button click** — autocapture is deliberately **off**. Add an explicit event only when a funnel needs it.
- **PII in event props** — distinct_id is the pseudonymous Supabase user id only. No email/name in properties.

---

## Open follow-ups

- **`signed_up` is client-side only.** Auth is Supabase-native (`auth.users`); the backend has no "user created" hook (`verify_token` just decodes the JWT), so there's no clean server-truth signup event. If signup accuracy becomes critical, add a lazy profile-upsert on first authenticated request and emit `signed_up` there.
- **Revenue + referral stages are empty** until those surfaces exist.
- **Session replay + experiments** are config decisions gated on the privacy story.
- **Backend `posthog` batches** — flushed on app shutdown (`analytics.shutdown()` in `main.py`). On a hard crash, in-flight events can be lost; `flush_at=1` keeps that window tiny.
