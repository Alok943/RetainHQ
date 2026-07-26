import { startActivityTracking } from './activity_tracker'

function getTitle(): string {
  // We explicitly DO NOT capture chat content. We only capture the title of the chat.
  
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

startActivityTracking({
  surface: surfaceName,
  url_domain: hostname,
  getTitle
})
