import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Analytics } from '@vercel/analytics/react'
import { Agentation } from 'agentation'
// Subsets pinned deliberately: latin + latin-ext + greek only (not the
// bundled 400.css, which pulls all 6 subsets incl. cyrillic/vietnamese).
// greek is REQUIRED — Ω λ θ ρ π ν σ appear in 14 physics-10/core-cs lessons
// (e.g. content/roadmaps/physics-10/apply-ohms-law-to-circuits.json).
// latin-ext is REQUIRED — ŷ/ẑ vector notation in apply-flemings-left-hand-rule.json.
// cyrillic/cyrillic-ext/vietnamese dropped: zero occurrences in shipped content.
import '@fontsource/ibm-plex-sans/latin-400.css'
import '@fontsource/ibm-plex-sans/latin-ext-400.css'
import '@fontsource/ibm-plex-sans/greek-400.css'
import '@fontsource/ibm-plex-sans/latin-500.css'
import '@fontsource/ibm-plex-sans/latin-ext-500.css'
import '@fontsource/ibm-plex-sans/greek-500.css'
import '@fontsource/ibm-plex-sans/latin-600.css'
import '@fontsource/ibm-plex-sans/latin-ext-600.css'
import '@fontsource/ibm-plex-sans/greek-600.css'
import '@fontsource/ibm-plex-sans/latin-700.css'
import '@fontsource/ibm-plex-sans/latin-ext-700.css'
import '@fontsource/ibm-plex-sans/greek-700.css'
import '@fontsource/jetbrains-mono/latin-400.css'
import '@fontsource/jetbrains-mono/latin-ext-400.css'
import '@fontsource/jetbrains-mono/greek-400.css'
import '@fontsource/jetbrains-mono/latin-500.css'
import '@fontsource/jetbrains-mono/latin-ext-500.css'
import '@fontsource/jetbrains-mono/greek-500.css'
import '@fontsource/jetbrains-mono/latin-600.css'
import '@fontsource/jetbrains-mono/latin-ext-600.css'
import '@fontsource/jetbrains-mono/greek-600.css'
import '@fontsource/jetbrains-mono/latin-700.css'
import '@fontsource/jetbrains-mono/latin-ext-700.css'
import '@fontsource/jetbrains-mono/greek-700.css'
import './index.css'
import App from './App.jsx'
import ErrorBoundary from './ErrorBoundary.jsx'
import { ThemeProvider } from './lib/theme'
import { initAnalytics, track, EVENTS } from './lib/analytics'
import { initErrorTracking } from './lib/errors'
import { ensureSubscribed } from './lib/push'

// initAnalytics/initErrorTracking are cheap here (this module is already in
// the entry chunk) — the actual weight, posthog-js and @sentry/react, is
// dynamic-imported *inside* those functions (see lib/analytics.js, lib/errors.js),
// so deferring the call keeps both SDKs off the critical path without a
// separate no-op call site.
function initDeferred() {
  initAnalytics();
  initErrorTracking();
}
if ('requestIdleCallback' in window) {
  window.requestIdleCallback(initDeferred);
} else {
  setTimeout(initDeferred, 200);
}

// Re-register the push SW on load if permission was already granted in a prior
// session, and silently re-create the subscription if it went stale (cleared
// site data, new profile, rotated endpoint, changed VAPID key) — otherwise the
// user stays "granted" but never receives anything. Never prompts: that's an
// explicit user action (Profile.jsx toggle / Review.jsx + Home.jsx cards, B4).
// Fire-and-forget so a push hiccup can never block app startup.
ensureSubscribed().catch(() => {});

// Fires once, whenever the browser actually installs the PWA (Add to Home
// Screen / desktop install) — a real intent signal, not just a manifest check.
window.addEventListener('appinstalled', () => track(EVENTS.PWA_INSTALLED));

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ThemeProvider>
      <BrowserRouter>
        <ErrorBoundary>
          <App />
        </ErrorBoundary>
        <Analytics />
        {import.meta.env.DEV && <Agentation endpoint="http://localhost:4747" />}
      </BrowserRouter>
    </ThemeProvider>
  </StrictMode>,
)
