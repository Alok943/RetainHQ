import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Analytics } from '@vercel/analytics/react'
import './index.css'
import App from './App.jsx'
import { ThemeProvider } from './lib/theme'
import { initAnalytics } from './lib/analytics'

initAnalytics() // no-op unless VITE_POSTHOG_KEY is set

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ThemeProvider>
      <BrowserRouter>
        <App />
        <Analytics />
      </BrowserRouter>
    </ThemeProvider>
  </StrictMode>,
)
