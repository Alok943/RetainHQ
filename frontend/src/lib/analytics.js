// PostHog product analytics — a thin, centralized wrapper.
//
// Design goals:
//  - **No-op without a key.** If VITE_POSTHOG_KEY is unset (local dev, or before
//    the key is added in prod), every call is a silent no-op. Nothing tracks,
//    nothing breaks.
//  - **Explicit, high-signal events only.** Autocapture is OFF — we send a small
//    curated set (see EVENTS) so the funnel stays readable, not a firehose.
//  - **Privacy-first defaults.** Cookieless (localStorage persistence), no session
//    recording, identify by pseudonymous user id only (NO email/PII by default).
//
// Supply VITE_POSTHOG_KEY (+ optional VITE_POSTHOG_HOST) to turn it on.
import posthog from 'posthog-js';

const KEY = import.meta.env.VITE_POSTHOG_KEY;
const HOST = import.meta.env.VITE_POSTHOG_HOST || 'https://us.i.posthog.com';

let enabled = false;

// The curated event vocabulary — the core-loop funnel. Keep this small: every
// event here must earn a spot in an AARRR funnel, a retention curve, or a
// friction signal (see docs/analytics-plan.md). Don't add a firehose.
export const EVENTS = {
  // --- Acquisition ---
  LANDING_CTA: 'landing_cta', // landing-page CTA click — top of the funnel
  SIGNUP_STARTED: 'signup_started', // Google OAuth initiated (before the redirect)

  // --- Activation (the "aha" path — our biggest funnel leak) ---
  SIGNED_IN: 'signed_in',
  SIGNED_UP: 'signed_up', // first-ever sign-in (new person, not a returning login)
  ONBOARDING_STARTED: 'onboarding_started',
  ONBOARDING_COMPLETED: 'onboarding_completed',
  FIRST_CAPTURE_SHOWN: 'first_capture_shown', // the zero-activity gate rendered
  ACTIVITY_LOGGED: 'activity_logged',
  ACTIVATED: 'activated', // first-ever activity captured — the activation milestone

  // --- Retention (the spaced-repetition return loop) ---
  REVIEWS_DUE_SHOWN: 'reviews_due_shown', // Home surfaced ≥1 due review (return trigger)
  REVIEW_STARTED: 'review_started',
  REVIEW_COMPLETED: 'review_completed', // carries { outcome, rating, recalled, mode } props
  REVIEW_QUEUE_EMPTY: 'review_queue_empty', // opened /reviews with nothing due (friction)
  REMINDER_CLICKED: 'reminder_clicked', // arrived from a reminder email (?src=reminder)

  // --- Engagement (lessons → the retention loop) ---
  LESSON_OPENED: 'lesson_opened',
  LESSON_COMPLETED: 'lesson_completed',
  CARD_CREATED_FROM_LESSON: 'card_created_from_lesson', // lesson → FSRS card bridge
  ROADMAP_OPENED: 'roadmap_opened',
  TEST_STARTED: 'test_started',
  TEST_COMPLETED: 'test_completed', // carries { score, max_score, roadmap, phase }

  // --- Cross-cutting ---
  AUTH_WALL_HIT: 'auth_wall_hit',
  API_ERROR: 'api_error', // a server/network failure the user actually hit
  PUSH_SUBSCRIBED: 'push_subscribed',
  PUSH_UNSUBSCRIBED: 'push_unsubscribed',
};

export function initAnalytics() {
  if (enabled || !KEY) return; // no key → stay a no-op
  posthog.init(KEY, {
    api_host: HOST,
    autocapture: false,           // we send explicit events, not a firehose
    capture_pageview: false,      // SPA: pageviews fired manually on route change
    capture_pageleave: true,      // needed for Web Analytics bounce rate / session duration
    persistence: 'localStorage',  // cookieless
    disable_session_recording: true,
  });
  enabled = true;
}

export function track(event, props) {
  if (!enabled) return;
  posthog.capture(event, props);
}

// Fire an event at most once per page-load session. For events triggered by a
// render/effect (e.g. "the due card was shown", "lesson reached the end") that
// would otherwise double-count on re-renders. `key` dedupes — reuse the same key
// with distinct props only when the props don't matter for the first fire.
const _firedOnce = new Set();
export function trackOnce(key, event, props) {
  if (!enabled || _firedOnce.has(key)) return;
  _firedOnce.add(key);
  posthog.capture(event, props);
}

export function pageview(path) {
  if (!enabled) return;
  posthog.capture('$pageview', { path: path || window.location.pathname });
}

// Pseudonymous: id only (a UUID). Do NOT pass email/PII here by default.
export function identifyUser(id) {
  if (!enabled || !id) return;
  posthog.identify(id);
}

export function resetAnalytics() {
  if (!enabled) return;
  posthog.reset();
}
