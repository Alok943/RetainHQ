// Single source for the backend origin, imported by the popup, the background,
// and consent.ts — it was previously duplicated (default string and all) in the
// first two, and consent.ts needs it now too.
//
// Defaults to PRODUCTION, unlike frontend/src/lib/api.js's localhost default —
// the frontend's prod build always gets VITE_API_BASE_URL injected by Vercel,
// but nothing yet enforces that at extension-package time. A forgotten env var
// when building for the store must not silently ship an extension that points
// every real user at localhost:8000; a forgotten override for local dev only
// breaks dev, which is loud and immediate.
// Local dev: set VITE_API_BASE_URL=http://localhost:8000 in extension/.env.
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://retainhq.onrender.com'

/**
 * The backend origin as a match pattern, for `permissions.request()`.
 *
 * Load-bearing on Firefox, and the reason no companion data ever reached
 * production (verified 2026-08-02: zero `companion_browser` rows, zero
 * `PROBLEM_SOLVED` rows, ever). Firefox MV3 does not grant `host_permissions`
 * at install — the user does — and `main.py`'s CORS allow-list is explicit
 * origins, which a Firefox extension can never appear on: its origin is
 * `moz-extension://<UUID>` where the UUID is regenerated per install. So the
 * ONLY thing that lets the extension talk to our own API is the host-permission
 * grant, which exempts the request from CORS entirely. Without it every call
 * fails as an opaque `TypeError: NetworkError`, indistinguishable from being
 * offline.
 *
 * Supabase calls kept working throughout precisely because supabase.co serves
 * permissive CORS headers and our FastAPI deliberately does not — which is why
 * sign-in always succeeded while nothing else did, and why this went unnoticed.
 *
 * Derived from API_BASE_URL rather than hardcoded so a localhost dev build asks
 * for the origin it will actually call.
 */
export const API_ORIGIN_PATTERN = `${new URL(API_BASE_URL).origin}/*`
