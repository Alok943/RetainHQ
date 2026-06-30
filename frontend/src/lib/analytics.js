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

// The curated event vocabulary — the core-loop funnel. Keep this small.
export const EVENTS = {
  SIGNED_IN: 'signed_in',
  LANDING_CTA: 'landing_cta', // landing-page CTA click — top of the funnel
  ACTIVITY_LOGGED: 'activity_logged',
  REVIEW_STARTED: 'review_started',
  REVIEW_COMPLETED: 'review_completed', // carries { outcome, rating, recalled, mode } props
  LESSON_OPENED: 'lesson_opened',
  ROADMAP_OPENED: 'roadmap_opened',
  AUTH_WALL_HIT: 'auth_wall_hit',
};

export function initAnalytics() {
  if (enabled || !KEY) return; // no key → stay a no-op
  posthog.init(KEY, {
    api_host: HOST,
    autocapture: false,           // we send explicit events, not a firehose
    capture_pageview: false,      // SPA: pageviews fired manually on route change
    persistence: 'localStorage',  // cookieless
    disable_session_recording: true,
  });
  enabled = true;
}

export function track(event, props) {
  if (!enabled) return;
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
