import { startActivityTracking } from './activity_tracker'

function getTitle(): string {
  // Notion's <title> is "Page Name" alone once a page has a title, or
  // "Workspace Name" on the sidebar/home view — no reliable " | Notion"
  // suffix to strip, unlike Coursera/ChatGPT/Claude.
  return document.title
}

startActivityTracking({
  surface: 'notion',
  url_domain: 'notion.so',
  getTitle
})
