// Reads AI chat turns for topic segmentation (IMPLEMENTATION-companion-chat-content
// §2). Cloud-tier only — gated at the call site by a LIVE consent-tier check,
// not just once at script load, because `optional_host_permissions` can be
// revoked mid-session while an already-injected content script keeps running
// until the tab reloads (consent.ts's own documented caveat). Downgrading the
// tier must stop new extraction immediately even without a reload.
//
// Selectors below are best-effort against each site's DOM as of 2026-07 —
// none of these sites publish a stable API for this, and all three ship
// obfuscated utility classes that churn on every deploy. If a selector
// matches nothing, extraction returns [] and the caller falls back to
// metadata-only (title_sample) rather than sending nothing useful or, worse,
// something wrong.

export interface ChatTurn {
  role: 'user' | 'assistant'
  text: string
}

const MAX_TURNS = 60
const MAX_TOTAL_CHARS = 12_000
const MAX_ASSISTANT_CHARS = 300

// Screen-reader-only labels ("You said", "Gemini said") are real DOM text —
// invisible on screen, but `.textContent` reads them like anything else.
// Confirmed live on gemini.google.com 2026-07-27 (Angular Material's
// `.cdk-visually-hidden`): every turn came back prefixed "You said"/"Gemini
// said". `.sr-only`/`[class*="visually-hidden"]` cover the same pattern on
// non-Angular sites, defensively — not confirmed present on ChatGPT/Claude,
// but the failure mode (silent prefix pollution) is exactly the kind of
// thing textOf's job is to prevent, so strip it everywhere rather than only
// where it's been caught once.
const HIDDEN_LABEL_SELECTOR = '.cdk-visually-hidden, .sr-only, [class*="visually-hidden"]'

function textOf(el: Element): string {
  const clone = el.cloneNode(true) as Element
  // Strip code blocks — high volume, low topic signal (§2.2), and the
  // biggest single contributor to blowing the char budget.
  clone.querySelectorAll('pre').forEach((pre) => pre.remove())
  clone.querySelectorAll(HIDDEN_LABEL_SELECTOR).forEach((hidden) => hidden.remove())
  return (clone.textContent || '').trim()
}

/**
 * Drops any matched node nested inside another matched node. A container and
 * a block inside it can both match the same selector, which would emit the
 * same text twice — once from the outer node (whose textContent already
 * includes the inner) and once from the inner. Keep the outermost.
 *
 * Observed live on claude.ai 2026-07-27: 4 user messages but 6
 * `.font-claude-response` matches in the same conversation.
 */
function outermostOnly(nodes: Element[]): Element[] {
  return nodes.filter((node) => !nodes.some((other) => other !== node && other.contains(node)))
}

/**
 * ONE querySelectorAll with a combined selector, never one query per role.
 * `querySelectorAll` returns matches in DOCUMENT order, which is the only
 * thing that keeps a conversation interleaved (U, A, U, A…).
 *
 * Querying each role separately and concatenating — which this originally did
 * on Claude and Gemini — produces every user turn followed by every assistant
 * turn. That silently wrecks both caps downstream: MAX_TOTAL_CHARS truncates
 * from the oldest end, so it would strip the entire user side of the
 * conversation first, which is precisely the signal worth keeping.
 */
function collectTurns(selector: string, roleOf: (el: Element) => 'user' | 'assistant' | null): ChatTurn[] {
  const nodes = outermostOnly(Array.from(document.querySelectorAll(selector)))
  const turns: ChatTurn[] = []
  for (const node of nodes) {
    const role = roleOf(node)
    if (!role) continue
    const text = textOf(node)
    if (text) turns.push({ role, text })
  }
  return turns
}

function extractChatGPT(): ChatTurn[] {
  return collectTurns('[data-message-author-role]', (el) => {
    const role = el.getAttribute('data-message-author-role')
    return role === 'user' || role === 'assistant' ? role : null
  })
}

// Selector derived from the live claude.ai DOM 2026-07-27, not guessed.
//
// The original `.font-claude-response` was wrong in a way worth recording:
// the reply body's class is `font-claude-response-BODY`, a DIFFERENT class
// token, and CSS matches tokens exactly — so `.font-claude-response` never
// matched a reply at all. What it did match was Claude's THINKING-BLOCK
// summaries ("Pinpointed off-by-one loop initialization error…") plus the
// bare token "DSA_COACHING". A near-miss selector that silently selects
// something else entirely, rather than nothing.
//
// `.standard-markdown` (the reply body's parent) is used instead of
// `.font-claude-response-body` because the latter is a single <p> — a
// multi-paragraph reply would fragment into one "turn" per paragraph and
// burn the MAX_TURNS budget. `.standard-markdown` wraps the whole reply.
//
// User turns keep `[data-testid="user-message"]`, which was confirmed
// accurate in the same check (4 matches for 4 user messages). Role is
// decided by `closest()`, and outermostOnly drops any `.standard-markdown`
// nested inside a user message — so a user turn is never double-counted as
// an assistant one.
function extractClaude(): ChatTurn[] {
  return collectTurns(
    '[data-testid="user-message"], .standard-markdown',
    (el) => (el.closest('[data-testid="user-message"]') ? 'user' : 'assistant'),
  )
}

// Verified against a live gemini.google.com conversation 2026-07-27:
// `user-query`/`model-response` are real custom elements, one per turn,
// interleaved correctly. The only issue was the `.cdk-visually-hidden`
// "You said"/"Gemini said" labels textOf() now strips.
function extractGemini(): ChatTurn[] {
  return collectTurns(
    'user-query, model-response',
    (el) => (el.tagName.toLowerCase() === 'user-query' ? 'user' : 'assistant'),
  )
}

function rawTurnsFor(hostname: string): ChatTurn[] {
  if (hostname.includes('chatgpt')) return extractChatGPT()
  if (hostname.includes('claude')) return extractClaude()
  if (hostname.includes('gemini')) return extractGemini()
  return []
}

/** Turns a raw DOM read into the capped, flattened string sent to the
 * backend — user turns in full (their own words say what they were trying
 * to learn), assistant turns truncated (the reply is mostly the answer being
 * handed over, which is exactly what must not be mistaken for learning). */
export function extractChatContent(hostname: string = window.location.hostname): string {
  const raw = rawTurnsFor(hostname)
  if (raw.length === 0) return ''

  // Keep the most recent turns — the tail is what the session was actually
  // about, not the opening turns a virtualized list may be the only ones
  // still mounted for anyway (see the virtualization note below).
  const kept = raw.slice(-MAX_TURNS)

  const lines = kept.map((turn) => {
    const text = turn.role === 'assistant' ? turn.text.slice(0, MAX_ASSISTANT_CHARS) : turn.text
    return `${turn.role === 'user' ? 'U' : 'A'}: ${text}`
  })

  let content = lines.join('\n')
  if (content.length > MAX_TOTAL_CHARS) {
    // Truncate from the oldest end — the tail (most recent) matters more.
    content = content.slice(content.length - MAX_TOTAL_CHARS)
  }
  return content
}

// ChatGPT and Gemini both virtualize long conversations: turns scrolled far
// out of view are removed from the DOM entirely, so extraction only ever
// sees what's currently mounted. This is accepted, not worked around — do
// NOT programmatically scroll the page to force-mount history. That's
// user-visible interference with a page the user is reading, and exactly the
// kind of behavior an AMO reviewer treats as hostile.
