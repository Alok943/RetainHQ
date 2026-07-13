// Sentry error tracking — a thin, centralized wrapper mirroring analytics.js.
//
// Design goals (same as analytics.js):
//  - **No-op without a DSN.** If VITE_SENTRY_DSN is unset, every call is a
//    silent no-op. Nothing reports, nothing breaks.
//  - **Privacy-first.** send_default_pii is off; the only user context is a
//    pseudonymous id (matches identifyUser in analytics.js) — never email.
//  - **No Session Replay.** Errors sampleRate 1.0, traces 0.1.
//
// Supply VITE_SENTRY_DSN (+ optional VITE_SENTRY_RELEASE) to turn it on.
import * as Sentry from '@sentry/react';

const DSN = import.meta.env.VITE_SENTRY_DSN;
const RELEASE = import.meta.env.VITE_SENTRY_RELEASE;

let enabled = false;

export function initErrorTracking() {
  if (enabled || !DSN) return; // no DSN → stay a no-op
  Sentry.init({
    dsn: DSN,
    environment: import.meta.env.PROD ? 'production' : 'development',
    release: RELEASE,
    sampleRate: 1.0,
    tracesSampleRate: 0.1,
    sendDefaultPii: false,
    integrations: [], // no Session Replay, no extra auto-instrumentation
  });
  enabled = true;
}

export function captureError(err, ctx) {
  if (!enabled) return;
  Sentry.captureException(err, ctx ? { extra: ctx } : undefined);
}

// Pseudonymous: id only (a UUID) — matches analytics.js's identifyUser.
export function setErrorUser(id) {
  if (!enabled || !id) return;
  Sentry.setUser({ id });
}

export function clearErrorUser() {
  if (!enabled) return;
  Sentry.setUser(null);
}
