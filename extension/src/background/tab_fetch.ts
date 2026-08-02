// Runs an import's HTTP calls inside a real PAGE on the target site instead of
// from the background service worker. Used by both the LeetCode and NeetCode
// imports; site-specific bits are arguments, not constants.
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
// The injected code is deliberately a few lines that fetch a URL and hand back
// the raw text. ALL the product logic — the date cutoff, the language filter,
// when to stop paginating, which solve date wins, which slugs to keep — stays in
// leetcode_backfill.ts / neetcode_backfill.ts where it is pure and unit-tested.
// Nothing that decides what gets imported runs inside a page we don't control.

import { tabsQuery, tabsCreate, tabsGet, tabsRemove, scriptingExecuteScript } from '../browser_api'
import type { PageFetch } from './leetcode_backfill'

/** The site to borrow a tab from. `fallbackUrl` is opened only when the user has
 * no matching tab already, and is deliberately the page whose data is about to
 * be read — this never opens something unrelated to the action just requested. */
export interface TabTarget {
  match: string
  fallbackUrl: string
  /** Named in the "open a tab" failure messages the popup shows verbatim. */
  label: string
}

export const LEETCODE_TAB: TabTarget = {
  match: '*://*.leetcode.com/*',
  fallbackUrl: 'https://leetcode.com/submissions/',
  label: 'LeetCode',
}

export const NEETCODE_TAB: TabTarget = {
  match: '*://neetcode.io/*',
  fallbackUrl: 'https://neetcode.io/practice',
  label: 'NeetCode',
}

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
 * preserves the "sent a login page, not data" message the popup shows.
 *
 * `body` is passed as a STRING, not an object: everything crossing the
 * injection boundary is structured-cloned, and a pre-serialized string is one
 * less shape to get wrong. NeetCode's import needs POST + a JSON body; LeetCode's
 * needs plain GET, which is what `method: undefined` gives.
 */
function fetchInPage(
  url: string,
  method?: string,
  body?: string,
): Promise<{ status: number; ok: boolean; body: string }> {
  return fetch(url, {
    credentials: 'include',
    method: method || 'GET',
    ...(body ? { headers: { 'Content-Type': 'application/json' }, body } : {}),
  }).then(async (res) => ({
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
export function pageFetchVia(tabId: number, label = ''): PageFetch {
  return async (url: string, init?: RequestInit) => {
    const results = await scriptingExecuteScript<
      [string, string | undefined, string | undefined],
      ReturnType<typeof fetchInPage>
    >({
      target: { tabId },
      world: 'MAIN',
      func: fetchInPage,
      args: [url, init?.method, typeof init?.body === 'string' ? init.body : undefined],
    })
    const result = results?.[0]?.result
    // Injection itself failed — tab navigated away mid-scan, was closed, or the
    // host permission was revoked between pages. Distinct from a bad HTTP
    // status, which arrives as a normal result below.
    if (!result) throw new Error(`Lost the${label ? ` ${label}` : ''} tab during the import — try again`)
    return {
      status: result.status,
      ok: result.ok,
      json: async () => JSON.parse(result.body),
    }
  }
}

/**
 * Finds a usable tab on `target`'s site, opening a background one if there is none.
 *
 * Auto-opening rather than erroring out is what keeps "click Import" working
 * from anywhere, which is how the LeetCode button behaved before any of this —
 * telling the user to go open a tab first would be a visible regression caused
 * purely by an internal fix. Anything opened here is closed again in `releaseTab`.
 */
export async function acquireTab(target: TabTarget): Promise<ScanTab> {
  // status must be 'complete': injecting into a tab that is still loading can
  // land before the document exists, and the result is an empty injection
  // rather than a clean error.
  const existing = await tabsQuery({ url: target.match })
  const ready = existing.find((tab) => tab.id !== undefined && tab.status === 'complete')
  if (ready?.id !== undefined) return { tabId: ready.id, opened: false }

  const created = await tabsCreate({ url: target.fallbackUrl, active: false })
  if (created.id === undefined) throw new Error(`Could not open a ${target.label} tab for the import`)
  try {
    await waitForTabComplete(created.id, target.label)
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

async function waitForTabComplete(tabId: number, label: string): Promise<void> {
  // Polled rather than driven by tabs.onUpdated: the service worker can be
  // evicted and revived around an await, and a listener registered before that
  // does not survive it. A poll re-reads the truth every tick instead.
  const deadline = Date.now() + TAB_READY_TIMEOUT_MS
  while (Date.now() < deadline) {
    const tab = await tabsGet(tabId)
    if (tab.status === 'complete') return
    await sleep(TAB_POLL_MS)
  }
  throw new Error(`${label} did not finish loading — check you are signed in, then retry`)
}
