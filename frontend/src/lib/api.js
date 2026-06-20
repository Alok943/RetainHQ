import { supabase } from './supabase';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

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

  const headers = {
    'Content-Type': 'application/json',
    ...fetchOptions.headers,
  };

  if (DEV_AUTH_BYPASS) {
    // Dev: skip Supabase entirely; the backend (DEV_AUTH_BYPASS) ignores the token.
    headers['Authorization'] = 'Bearer dev-bypass';
  } else {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session && !optionalAuth) {
      console.error('No active session found, failing request.');
      throw new Error('Not authenticated');
    }
    if (session) {
      headers['Authorization'] = `Bearer ${session.access_token}`;
    }
  }

  const url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : '/' + endpoint}`;

  const response = await fetch(url, {
    ...fetchOptions,
    headers
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    const err = new Error(errorData?.detail || `API request failed with status ${response.status}`);
    err.status = response.status; // let callers branch on it (e.g. 404 = feature gated off)
    throw err;
  }

  return response.json();
};

export default apiFetch;
