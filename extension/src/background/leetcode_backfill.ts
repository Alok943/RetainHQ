// Recency- and language-filtered LeetCode import.
//
// The original backfill read `/api/problems/all/`, which answers exactly one
// question per problem — "is it solved, yes or no" — with no language and no
// date attached. That made both filters here impossible by construction, and
// it is why the first-ever import pulled 136 problems spanning every language
// and every year the account has existed.
//
// `/api/submissions/` is the submission LOG instead: newest-first, paginated,
// and each row carries `lang`, `status_display` and a unix `timestamp`. That's
// the only endpoint that can answer "which problems did I solve, in THESE
// languages, in the last N days", so the filtering is real rather than
// approximated.
//
// Language and window are caller-supplied, not hardcoded — this module was
// briefly Python-only, built that way for one user's own migration off C++.
// Shipped as-is it would have silently dropped every non-Python solve for
// every OTHER installed user with no setting to recover it, which is a much
// worse failure than the unfiltered import it replaced. LANGUAGE_GROUPS/
// WINDOW_OPTIONS (../leetcode_langs.ts) are what the popup renders checkboxes
// from; `null` for either means "no filter", which is also what happens if a
// message omits the field entirely — see service_worker.ts.
//
// Deliberately narrow in what it keeps regardless of filter: a row's `code`
// field (the full source of every submission) is read past and never
// retained, so nothing downstream can accidentally forward solution text to
// our backend. Only slug, language and timestamp leave this module.

const PAGE_SIZE = 20
// Bounds the loop if `has_next` never goes false or timestamps look wrong.
// 100 pages x 20 = 2000 submissions, far past any realistic window.
const MAX_PAGES = 100
// LeetCode rate-limits this endpoint aggressively; a short gap between pages
// keeps a normal-sized import under the limit. A 429 is handled as partial
// rather than fatal (see below) — losing the tail of a window beats losing
// everything already collected.
const PAGE_DELAY_MS = 350

export interface SubmissionRow {
  title_slug?: string
  lang?: string
  status_display?: string
  timestamp?: number | string
}

export interface SubmissionsPage {
  submissions_dump?: SubmissionRow[]
  has_next?: boolean
}

/**
 * Folds one newest-first page into `acc` (slug → earliest accepted-in-window
 * epoch ms) and reports whether this page crossed the cutoff.
 *
 * `langs: null` means no language filter at all — every accepted solve in the
 * window counts, matching the pre-filter behavior. A non-null set is matched
 * against `row.lang.toLowerCase()`, since LeetCode has used both "python3"
 * and "Python3" at different points.
 *
 * EARLIEST, not latest: re-solving a problem three times in the window is one
 * act of learning, and the first solve in-window is when it actually
 * happened. Taking the latest would silently re-date old work to whenever it
 * was last revisited, which is the same overstating this codebase refuses
 * elsewhere.
 *
 * Pure and separately tested — this is the product decision ("what counts as
 * a solve in the window"), not the transport around it.
 */
export function collectSolves(
  rows: SubmissionRow[],
  cutoffMs: number,
  acc: Map<string, number>,
  langs: Set<string> | null,
): { crossedCutoff: boolean } {
  let crossedCutoff = false

  for (const row of rows) {
    // Seconds in LeetCode's payload, and sometimes a string. A row without a
    // usable timestamp can't be placed in or out of the window, so it's
    // skipped rather than guessed at.
    const seconds = typeof row.timestamp === 'string' ? Number(row.timestamp) : row.timestamp
    if (!Number.isFinite(seconds as number)) continue
    const ms = (seconds as number) * 1000

    if (ms < cutoffMs) {
      // Newest-first ordering means everything after this is older still.
      crossedCutoff = true
      continue
    }

    if (row.status_display !== 'Accepted') continue
    if (langs !== null && (!row.lang || !langs.has(row.lang.toLowerCase()))) continue
    if (!row.title_slug) continue

    const existing = acc.get(row.title_slug)
    if (existing === undefined || ms < existing) acc.set(row.title_slug, ms)
  }

  return { crossedCutoff }
}

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

export interface BackfillScanResult {
  /** slug → epoch ms of the earliest accepted submission in the window that
   * matched the language filter. */
  solves: Map<string, number>
  /** True when the scan stopped early (rate limit / page cap) and the window
   * is therefore only partly covered — the caller must say so rather than
   * reporting a clean import. */
  partial: boolean
}

/**
 * Walks `/api/submissions/` newest-first until the window is fully covered.
 *
 * `cutoffMs` should be `0` (not e.g. `-Infinity`) for an unbounded "all time"
 * scan — every real submission timestamp is well above zero, so this still
 * short-circuits correctly and stays a valid epoch ms value throughout.
 *
 * `fetchImpl` is injectable purely so the pagination/stop logic is testable
 * without a network or a logged-in browser.
 */
export async function scanRecentSolves(
  cutoffMs: number,
  langs: Set<string> | null,
  fetchImpl: typeof fetch = fetch,
  delayMs: number = PAGE_DELAY_MS,
): Promise<BackfillScanResult> {
  const solves = new Map<string, number>()

  for (let page = 0; page < MAX_PAGES; page++) {
    const url = `https://leetcode.com/api/submissions/?offset=${page * PAGE_SIZE}&limit=${PAGE_SIZE}`
    const res = await fetchImpl(url, { credentials: 'include' })

    if (res.status === 429) {
      // Everything collected so far is still valid and worth keeping.
      console.warn('[RetainHQ] LeetCode rate-limited the submission scan; importing what was collected')
      return { solves, partial: true }
    }
    if (!res.ok) throw new Error(`LeetCode returned ${res.status}`)

    let body: SubmissionsPage
    try {
      body = await res.json()
    } catch {
      throw new Error('LeetCode sent a login page, not data')
    }

    const rows = body.submissions_dump ?? []
    if (rows.length === 0) return { solves, partial: false }

    const { crossedCutoff } = collectSolves(rows, cutoffMs, solves, langs)
    if (crossedCutoff || body.has_next === false) return { solves, partial: false }

    if (delayMs > 0) await sleep(delayMs)
  }

  // Ran out of pages before reaching the cutoff — the window is not fully
  // covered, so this is explicitly partial rather than quietly truncated.
  console.warn(`[RetainHQ] Submission scan hit the ${MAX_PAGES}-page cap before covering the window`)
  return { solves, partial: true }
}
