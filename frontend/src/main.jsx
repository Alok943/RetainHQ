import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Analytics } from '@vercel/analytics/react'
import { Agentation } from 'agentation'
import '@fontsource/ibm-plex-sans/400.css'
import '@fontsource/ibm-plex-sans/500.css'
import '@fontsource/ibm-plex-sans/600.css'
import '@fontsource/ibm-plex-sans/700.css'
import '@fontsource/jetbrains-mono/400.css'
import '@fontsource/jetbrains-mono/500.css'
import '@fontsource/jetbrains-mono/600.css'
import '@fontsource/jetbrains-mono/700.css'
import './index.css'
import App from './App.jsx'
import ErrorBoundary from './ErrorBoundary.jsx'
import { ThemeProvider } from './lib/theme'
import { initAnalytics } from './lib/analytics'
import { initErrorTracking } from './lib/errors'
import { registerSW, isPushSupported } from './lib/push'

initAnalytics() // no-op unless VITE_POSTHOG_KEY is set
initErrorTracking() // no-op unless VITE_SENTRY_DSN is set

// Re-register the push SW on load if permission was already granted in a
// prior session. Never prompt here — that's an explicit user action
// (Profile.jsx toggle / Review.jsx done-screen card, see B4).
if (isPushSupported() && Notification.permission === 'granted') {
  registerSW();
}

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
