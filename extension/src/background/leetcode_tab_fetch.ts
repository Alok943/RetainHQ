// Runs the LeetCode import's HTTP calls inside a real leetcode.com PAGE
// instead of from the background service worker.
//
// WHY (confirmed empirically 2026-08-02, not theorised):
//   from the page console  -> GET /api/submissions/?offset=0&limit=5  ->  200 + JSON
//   from the service worker-> the identical URL, same cookies, same
//                             `credentials: 'include'`, host permission granted
//                                                        ->  403
//
// `/api/submissions/` dumps the full SOURCE CODE of every submission, so
// LeetCode guards it far more tightly than `/api/problems/all/` (which the
// original backfill used and which answered a background fetch happily). A
// background fetch cannot present what that endpoint wants: `Referer` is a
// forbidden header name, so no extension can set it, and an extension-initiated
// request is cross-site for SameSite cookie purposes. There is no header we can
// add to make the worker's request acceptable — the context itself is what's
// being rejected.
//
// So don't fight it: borrow the page. The injected function below is the page's
// OWN `fetch`, running on the page's own origin, which is byte-for-byte the
// context that returned 200 in the console test. That makes this fix correct by
// construction rather than by guessing which header was missing.
//
// The injected code is deliberately three lines that fetch a URL and hand back
// the raw text. ALL the product logic — the date cutoff, the language filter,
// when to stop paginating, which solve date wins — stays in leetcode_backfill.ts
// where it is pure and unit-tested. Nothing that decides what gets imported runs
// inside a page we don't control.

import { tabsQuery, tabsCreate, tabsGet, tabsRemove, scriptingExecuteScript } from '../browser_api'
import type { PageFetch } from './leetcode_backfill'

const LEETCODE_TAB_MATCH = '*://*.leetcode.com/*'
// Opened only when the user has no LeetCode tab already. `/submissions/` is the
// page whose data we're about to read, so it is also the honest one to show if
// the user happens to look — this never opens something unrelated to the action
// they just asked for.
const SCAN_TAB_URL = 'https://leetcode.com/submissions/'
const TAB_READY_TIMEOUT_MS = 20_000
const TAB_POLL_MS = 250

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

export interface ScanTab {
  tabId: number
  /** True when this module opened the tab and must therefore close it again. */
  opened: boolean
}

/**
 * Runs in the PAGE's MAIN world. Must be entirely self-contained: it is
 * serialized and injected, so it closes over nothing and can import nothing.
 *
 * Returns text rather than parsed JSON on purpose — a signed-out response is
 * an HTML login page, and letting the caller hit that as a JSON parse error
 * preserves the "LeetCode sent a login page, not data" message the popup shows.
 */
function fetchInPage(url: string): Promise<{ status: number; ok: boolean; body: string }> {
  return fetch(url, { credentials: 'include' }).then(async (res) => ({
    status: res.status,
    ok: res.ok,
    body: res.ok ? await res.text() : '',
  }))
}

/**
 * A `PageFetch` that satisfies each request from inside `tabId`.
 *
 * Shaped as a minimal Response look-alike (`status` / `ok` / `json()`) so
 * `scanRecentSolves` cannot tell the difference and needed no rewrite — the
 * pagination, 429 handling and login-page detection it already had all still
 * apply, unchanged and still covered by their existing tests.
 */
export function pageFetchVia(tabId: number): PageFetch {
  return async (url: string) => {
    const results = await scriptingExecuteScript<[string], ReturnType<typeof fetchInPage>>({
      target: { tabId },
      world: 'MAIN',
      func: fetchInPage,
      args: [url],
    })
    const result = results?.[0]?.result
    // Injection itself failed — tab navigated away mid-scan, was closed, or the
    // host permission was revoked between pages. Distinct from a bad HTTP
    // status, which arrives as a normal result below.
    if (!result) throw new Error('Lost the LeetCode tab during the import — try again')
    return {
      status: result.status,
      ok: result.ok,
      json: async () => JSON.parse(result.body),
    }
  }
}

/**
 * Finds a usable leetcode.com tab, opening a background one if there is none.
 *
 * Auto-opening rather than erroring out is what keeps "click Import" working
 * from anywhere, which is how the button behaved before this change — telling
 * the user to go open a tab first would be a visible regression caused purely
 * by an internal fix. Anything opened here is closed again in `releaseTab`.
 */
export async function acquireLeetCodeTab(): Promise<ScanTab> {
  // status must be 'complete': injecting into a tab that is still loading can
  // land before the document exists, and the result is an empty injection
  // rather than a clean error.
  const existing = await tabsQuery({ url: LEETCODE_TAB_MATCH })
  const ready = existing.find((tab) => tab.id !== undefined && tab.status === 'complete')
  if (ready?.id !== undefined) return { tabId: ready.id, opened: false }

  const created = await tabsCreate({ url: SCAN_TAB_URL, active: false })
  if (created.id === undefined) throw new Error('Could not open a LeetCode tab for the import')
  try {
    await waitForTabComplete(created.id)
  } catch (error) {
    // Don't strand a tab the user never asked for just because it was slow.
    await releaseTab({ tabId: created.id, opened: true })
    throw error
  }
  return { tabId: created.id, opened: true }
}

/** Closes the tab only if we opened it — never touches the user's own tab. */
export async function releaseTab(tab: ScanTab): Promise<void> {
  if (!tab.opened) return
  try {
    await tabsRemove(tab.tabId)
  } catch {
    // Already closed by the user, or the window went away. Nothing to clean up,
    // and it must not turn a successful import into a reported failure.
  }
}

async function waitForTabComplete(tabId: number): Promise<void> {
  // Polled rather than driven by tabs.onUpdated: the service worker can be
  // evicted and revived around an await, and a listener registered before that
  // does not survive it. A poll re-reads the truth every tick instead.
  const deadline = Date.now() + TAB_READY_TIMEOUT_MS
  while (Date.now() < deadline) {
    const tab = await tabsGet(tabId)
    if (tab.status === 'complete') return
    await sleep(TAB_POLL_MS)
  }
  throw new Error('LeetCode did not finish loading — check you are signed in, then retry')
}
