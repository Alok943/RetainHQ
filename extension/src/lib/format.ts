// Shared display helpers — previously duplicated only in popup.ts; now also
// used by the "What I studied" page (src/studied/studied.ts).

export const SURFACE_LABELS: Record<string, string> = {
  youtube: 'YouTube',
  coursera: 'Coursera',
  leetcode: 'LeetCode',
  neetcode: 'NeetCode',
  chatgpt: 'ChatGPT',
  claude: 'Claude',
  gemini: 'Gemini',
  pdf: 'PDF',
  llm: 'AI chat',
  notion: 'Notion',
}

export function relativeTime(ms: number): string {
  const mins = Math.round((Date.now() - ms) / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins} min ago`
  const hrs = Math.round(mins / 60)
  if (hrs < 24) return `${hrs} h ago`
  return `${Math.round(hrs / 24)} d ago`
}

// Domain suffixes, for callers holding a Session's `sources` (url_domain
// values, e.g. 'leetcode.com') rather than a live Segment's short `surface`
// (e.g. 'leetcode') — the two are genuinely different fields (stitcher.ts
// builds `sources` from `url_domain` only, never `surface`), so a single
// exact-match table can't serve both.
const DOMAIN_LABELS: [string, string][] = [
  ['youtube.com', 'YouTube'],
  ['coursera.org', 'Coursera'],
  ['leetcode.com', 'LeetCode'],
  ['neetcode.io', 'NeetCode'],
  ['chatgpt.com', 'ChatGPT'],
  ['claude.ai', 'Claude'],
  ['gemini.google.com', 'Gemini'],
  ['notion.so', 'Notion'],
]

export function surfaceLabel(surfaceOrDomain: string): string {
  if (SURFACE_LABELS[surfaceOrDomain]) return SURFACE_LABELS[surfaceOrDomain]
  const hit = DOMAIN_LABELS.find(([domain]) => surfaceOrDomain.endsWith(domain))
  if (hit) return hit[1]
  return surfaceOrDomain.endsWith('.pdf') ? 'PDF' : surfaceOrDomain
}
