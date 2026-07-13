import { supabase } from './supabase';
import { emitToast } from './toastBus';
import { track, EVENTS } from './analytics';
import { captureError } from './errors';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Fallback copy when the backend gives no `detail` (or the request never
// reached it). Only used for the "something's actually broken" statuses —
// 404/400 are left to callers, since those are already used as feature-gate
// signals (e.g. grader off) or form-level validation the component surfaces inline.
const FRIENDLY_STATUS_MESSAGES = {
  401: 'Your session has expired — sign in again.',
  403: "You don't have permission to do that.",
  429: 'Too many requests — slow down and try again.',
  500: 'Something went wrong on our end — try again shortly.',
  502: 'Something went wrong on our end — try again shortly.',
  503: 'Something went wrong on our end — try again shortly.',
  504: 'Something went wrong on our end — try again shortly.',
};

const shouldAutoToast = (status) => status === 401 || status === 403 || status === 429 || status >= 500;

// DEV ONLY: bypass Supabase auth locally so the authenticated app can be reviewed
// without Google OAuth. `import.meta.env.DEV` is false in production builds, so this
// whole branch is dead-code-eliminated from any deployed bundle — it cannot ship.
const DEV_AUTH_BYPASS =
  import.meta.env.DEV && import.meta.env.VITE_DEV_AUTH_BYPASS === 'true';

/**
 * A wrapper around native fetch that automatically attaches the Supabase JWT
 * as a Bearer token to every request.
 */
export const apiFetch = async (endpoint, options = {}) => {
  // optionalAuth: allow the call to proceed without a session (public reads,
  // e.g. roadmaps). The Bearer token is still attached when a session exists.
  const { optionalAuth = false, ...fetchOptions } = options;

  // FormData bodies (file uploads) must NOT get a manual Content-Type — the
  // browser sets multipart/form-data with the boundary itself.
  const isFormData = fetchOptions.body instanceof FormData;
  const headers = {
    ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
    ...fetchOptions.headers,
  };

  if (DEV_AUTH_BYPASS) {
    // Dev: skip Supabase entirely; the backend (DEV_AUTH_BYPASS) ignores the token.
    headers['Authorization'] = 'Bearer dev-bypass';
  } else {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session && !optionalAuth) {
      console.error('No active session found, failing request.');
      const err = new Error('Please sign in to continue.');
      err.status = 401;
      emitToast({ type: 'error', message: err.message });
      throw err;
    }
    if (session) {
      headers['Authorization'] = `Bearer ${session.access_token}`;
    }
  }

  const url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : '/' + endpoint}`;

  let response;
  try {
    response = await fetch(url, {
      ...fetchOptions,
      headers
    });
  } catch (networkErr) {
    const err = new Error("Can't reach the server — check your connection and try again.");
    err.status = 0;
    err.isNetworkError = true;
    emitToast({ type: 'offline', message: err.message });
    track(EVENTS.API_ERROR, { endpoint, status: 0, kind: 'network' });
    captureError(networkErr, { endpoint, network: true });
    throw err;
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    const message = errorData?.detail || FRIENDLY_STATUS_MESSAGES[response.status] || `Request failed (${response.status}).`;
    const err = new Error(message);
    err.status = response.status; // let callers branch on it (e.g. 404 = feature gated off)

    if (shouldAutoToast(response.status)) {
      emitToast({ type: 'error', message });
    }
    // Only server-side breakage is a real friction signal. 4xx are used as
    // feature gates (404 = grader off) and validation, so they'd be noise —
    // never captured (never 401/403/404/429).
    if (response.status >= 500) {
      track(EVENTS.API_ERROR, { endpoint, status: response.status, kind: 'server' });
      captureError(err, { endpoint, status: response.status });
    }
    if (response.status === 401) {
      // Session expired mid-use (as opposed to never having one) — let
      // AuthContext sign the user out and drop them back at the login screen.
      window.dispatchEvent(new CustomEvent('retainhq:unauthorized'));
    }

    throw err;
  }

  if (response.status === 204) return null; // DELETE endpoints — no body to parse
  return response.json();
};

export default apiFetch;
