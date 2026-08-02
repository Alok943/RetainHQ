/**
 * MAIN-world probe for neetcode.io. Mirrors leetcode_probe.ts's job — observe the
 * page's own submission traffic and forward a verdict to the isolated content
 * script — but NeetCode's backend shape had to be reverse-engineered rather than
 * read off a known API, and could only be verified up to the auth boundary
 * (2026-08-02 research session, this codebase cannot create accounts to sign in
 * and see past it — CLAUDE.md's operating rules prohibit account creation).
 *
 * Confirmed by direct probing against the live, unauthenticated site:
 *   - POST /api/runCodeFunctionHttp, envelope `{ data: { rawCode, lang, problemId,
 *     testCases } }` — a real endpoint (distinct 400s for each missing field, in
 *     the order rawCode -> lang -> testCases), that finally answers
 *     `{"error":{"message":"Please sign in first.","status":"permission-denied"}}`
 *     once the request is well-formed. That 403 is the actual edge of what could
 *     be verified without an account.
 *   - The catalog list (getProblemListFunctionHttp) and per-problem metadata
 *     (getProblemMetadataFunctionHttp) are both public and unauthenticated —
 *     used by import_neetcode_catalog.py, not this file.
 *   - Nine plausible submit-specific endpoint names (submitCodeFunctionHttp,
 *     submitSolutionFunctionHttp, judgeCodeFunctionHttp, ...) all 200'd with the
 *     Angular app shell — i.e. they don't exist server-side and fall through to
 *     the SPA catch-all route. Whether "Submit" is the SAME endpoint as "Run"
 *     (likely, given a `testCases`-shaped param — omitting it may run the full
 *     hidden suite) or a still-undiscovered sibling is UNKNOWN.
 *
 * Because the verdict-bearing endpoint and response shape are unverified past
 * that point, this probe does NOT try to silently parse a verdict and report it
 * as fact. It correlates a real click on the page's own "Submit" button (whose
 * accessible name IS confirmed — read straight off the live DOM) with whatever
 * *FunctionHttp response follows, forwards a best-effort guess at accept/reject
 * to the isolated world, and — critically — logs the full raw exchange to the
 * console so a real signed-in run can be pasted back to fix any wrong guess.
 * Expect this file to need a follow-up pass once that happens; it is deliberately
 * not claiming more certainty than the research supports.
 *
 * Same non-negotiable as leetcode_probe.ts: this reads only network traffic the
 * page already sends, never page variables/cookies/user code beyond what a
 * request body already contains, and forwards only the fields the isolated
 * world's evidence payload actually needs.
 */

const CODE_EXEC_URL_RE = /FunctionHttp\/?$/
const SUBMIT_ARM_MS = 20_000 // generous — covers a slow judge run, not indefinite

let armedUntil = 0
let reportedForThisClick = false

// Click-delegated on `document` (capture phase) rather than bound to a specific
// button element: the editor UI re-renders on every keystroke/tab-switch, so a
// direct reference taken once would frequently go stale. Matching on the
// accessible name is what read_page confirmed live on a real problem page.
document.addEventListener(
  'click',
  (e) => {
    const target = e.target as HTMLElement | null
    const btn = target?.closest('button')
    if (!btn) return
    const label = (btn.textContent || btn.getAttribute('aria-label') || '').trim()
    if (label !== 'Submit') return
    armedUntil = Date.now() + SUBMIT_ARM_MS
    reportedForThisClick = false
  },
  true,
)

interface ParsedVerdict {
  accepted: boolean | null // null = could not tell from this response
  raw: string // truncated, for the console-paste-back workflow — never sent onward
}

/**
 * Best-effort only — see the module doc for why this can't be more than that
 * yet. Tries several shapes a judge response plausibly takes; if NONE of them
 * match, returns `accepted: null` rather than guessing false, since a false
 * negative silently drops a real solve while a false positive is at least
 * visible (and reviewable) in the reflection panel it triggers.
 */
function parseVerdict(bodyText: string): ParsedVerdict {
  const raw = bodyText.slice(0, 2000)
  let json: unknown
  try {
    json = JSON.parse(bodyText)
  } catch {
    return { accepted: null, raw }
  }
  const data = (json as { data?: unknown })?.data ?? json

  // Structural guesses, checked in order of how likely each shape is for a
  // Firebase-callable-style judge response. All of these are UNVERIFIED.
  if (data && typeof data === 'object') {
    const d = data as Record<string, unknown>
    if (typeof d.success === 'boolean') return { accepted: d.success, raw }
    if (typeof d.accepted === 'boolean') return { accepted: d.accepted, raw }
    if (typeof d.allPassed === 'boolean') return { accepted: d.allPassed, raw }
    if (typeof d.passed === 'boolean') return { accepted: d.passed, raw }
    if (typeof d.status === 'string') {
      const s = d.status.toLowerCase()
      if (s === 'accepted' || s === 'success' || s === 'pass') return { accepted: true, raw }
      if (s === 'wrong_answer' || s === 'failed' || s === 'fail' || s === 'error') return { accepted: false, raw }
    }
  }
  // Last resort: the literal word LeetCode's own UI uses for a clean pass.
  // Same failure mode risk as leetcode_probe.ts's old text-match bug (matching
  // stale/unrelated "Accepted" text) — mitigated here by only ever reading this
  // out of a response already correlated to a fresh Submit click, not raw DOM.
  if (/"Accepted"/.test(bodyText)) return { accepted: true, raw }
  return { accepted: null, raw }
}

function report(url: string, verdict: ParsedVerdict): void {
  reportedForThisClick = true
  // Always logged, verdict or not — this IS the diagnostic capture the module
  // doc promises, and it's the fastest path to fixing parseVerdict for real.
  console.log('[RetainHQ][neetcode-probe] captured response for', url, verdict)
  if (verdict.accepted === null) return // nothing to forward — inconclusive
  window.postMessage(
    { source: 'retainhq-neetcode-probe', accepted: verdict.accepted },
    window.location.origin,
  )
}

function maybeHandle(url: string, bodyText: string): void {
  if (Date.now() > armedUntil || reportedForThisClick) return
  if (!CODE_EXEC_URL_RE.test(url)) return
  report(url, parseVerdict(bodyText))
}

// --- fetch ---------------------------------------------------------------
const origFetch = window.fetch
window.fetch = async function (...args: Parameters<typeof fetch>) {
  const res = await origFetch.apply(this, args)
  try {
    const url = typeof args[0] === 'string' ? args[0] : (args[0] as Request)?.url ?? ''
    if (CODE_EXEC_URL_RE.test(url)) {
      res.clone().text().then((t) => maybeHandle(url, t)).catch(() => {})
    }
  } catch {
    /* never let instrumentation break the page */
  }
  return res
}

// --- XMLHttpRequest --------------------------------------------------------
const origOpen = XMLHttpRequest.prototype.open
XMLHttpRequest.prototype.open = function (
  this: XMLHttpRequest & { __rhqUrl?: string },
  method: string,
  url: string | URL,
  ...rest: unknown[]
) {
  this.__rhqUrl = String(url)
  // @ts-expect-error - passthrough to the native signature
  return origOpen.call(this, method, url, ...rest)
}

const origSend = XMLHttpRequest.prototype.send
XMLHttpRequest.prototype.send = function (
  this: XMLHttpRequest & { __rhqUrl?: string },
  ...args: unknown[]
) {
  this.addEventListener('load', () => {
    try {
      const url = this.__rhqUrl ?? ''
      if (CODE_EXEC_URL_RE.test(url) && this.responseText) maybeHandle(url, this.responseText)
    } catch {
      /* ignore */
    }
  })
  // @ts-expect-error - passthrough to the native signature
  return origSend.apply(this, args)
}
