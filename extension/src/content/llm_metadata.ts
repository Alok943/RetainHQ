import { startActivityTracking } from './activity_tracker'
import { extractChatContent } from './chat_extract'
import { getConsentTier } from '../consent'

function getTitle(): string {
  // We explicitly DO NOT capture chat content by default. We only capture the title of the chat.

  // ChatGPT
  if (window.location.hostname.includes('chatgpt.com')) {
    const titleEl = document.querySelector('title')
    return titleEl ? titleEl.textContent?.replace(' - ChatGPT', '') || '' : ''
  }

  // Claude
  if (window.location.hostname.includes('claude.ai')) {
    const titleEl = document.querySelector('title')
    return titleEl ? titleEl.textContent?.replace(' - Claude', '') || '' : ''
  }

  // Gemini
  if (window.location.hostname.includes('gemini.google.com')) {
    const titleEl = document.querySelector('title')
    return titleEl ? titleEl.textContent?.replace(' - Gemini', '') || '' : ''
  }

  return document.title
}

const hostname = window.location.hostname
let surfaceName = 'llm'
if (hostname.includes('chatgpt')) surfaceName = 'chatgpt'
else if (hostname.includes('claude')) surfaceName = 'claude'
else if (hostname.includes('gemini')) surfaceName = 'gemini'

// Live tier check, not a one-time gate at script load — this script keeps
// running until the tab reloads even if the user downgrades the tier
// mid-session (consent.ts's documented Chrome/Firefox caveat), so a stale
// 'cloud' read here would keep extracting content after the user turned it
// off. Re-read on every capture instead of trusting a snapshot.
let cloudTierActive = false
getConsentTier().then((tier) => { cloudTierActive = tier === 'cloud' })
chrome.storage.onChanged.addListener((changes, area) => {
  if (area === 'local' && 'consentTier' in changes) {
    cloudTierActive = changes.consentTier.newValue === 'cloud'
  }
})

function getContent(): string | undefined {
  if (!cloudTierActive) return undefined
  const content = extractChatContent(hostname)
  return content || undefined
}

startActivityTracking({
  surface: surfaceName,
  url_domain: hostname,
  getTitle,
  getContent,
})
