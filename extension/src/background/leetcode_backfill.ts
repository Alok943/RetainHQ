// Recency- and language-filtered LeetCode import.
//
// The original backfill read `/api/problems/all/`, which answers exactly one
// question per problem — "is it solved, yes or no" — with no language and no
// date attached. That made both filters here impossible by construction, and
// it is why the first import pulled 136 problems spanning every language and
// every year the account has existed.
//
// `/api/submissions/` is the submission LOG instead: newest-first, paginated,
// and each row carries `lang`, `status_display` and a unix `timestamp`. That's
// the only endpoint that can answer "which problems did I solve IN PYTHON in
// the last N days", so the filtering is real rather than approximated.
//
// Deliberately narrow in what it keeps: a row's `code` field (the full source
// of every submission) is read past and never retained, so nothing downstream
// can accidentally forward solution text to our backend. Only slug, language
// and timestamp leave this module.

export const PYTHON_LANGS = new Set(['python', 'python3'])

/** LeetCode returns newest-first, so pagination stops as soon as a page runs
 * past the cutoff — a 2-month window costs a handful of pages, not the whole
 * account history. */
export const DEFAULT_WINDOW_DAYS = 60

const PAGE_SIZE = 20
// Bounds the loop if `has_next` never goes false or timestamps look wrong.
// 100 pages x 20 = 2000 submissions, far past any 2-month window.
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
 * EARLIEST, not latest: re-solving a problem three times in the window is one
 * act of learning, and the first Python solve is when it actually happened.
 * Taking the latest would silently re-date old work to whenever it was last
 * revisited, which is the same overstating this codebase refuses elsewhere.
 *
 * Pure and separately tested — this is the product decision ("what counts as a
 * Python solve in the window"), not the transport around it.
 */
export function collectPythonSolves(
  rows: SubmissionRow[],
  cutoffMs: number,
  acc: Map<string, number>,
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
    // Normalised because LeetCode has used both "python3" and "Python3".
    if (!row.lang || !PYTHON_LANGS.has(row.lang.toLowerCase())) continue
    if (!row.title_slug) continue

    const existing = acc.get(row.title_slug)
    if (existing === undefined || ms < existing) acc.set(row.title_slug, ms)
  }

  return { crossedCutoff }
}

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

export interface BackfillScanResult {
  /** slug → epoch ms of the earliest accepted Python submission in the window. */
  solves: Map<string, number>
  /** True when the scan stopped early (rate limit / page cap) and the window
   * is therefore only partly covered — the caller must say so rather than
   * reporting a clean import. */
  partial: boolean
}

/**
 * Walks `/api/submissions/` newest-first until the window is fully covered.
 *
 * `fetchImpl` is injectable purely so the pagination/stop logic is testable
 * without a network or a logged-in browser.
 */
export async function scanRecentPythonSolves(
  cutoffMs: number,
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

    const { crossedCutoff } = collectPythonSolves(rows, cutoffMs, solves)
    if (crossedCutoff || body.has_next === false) return { solves, partial: false }

    if (delayMs > 0) await sleep(delayMs)
  }

  // Ran out of pages before reaching the cutoff — the window is not fully
  // covered, so this is explicitly partial rather than quietly truncated.
  console.warn(`[RetainHQ] Submission scan hit the ${MAX_PAGES}-page cap before covering the window`)
  return { solves, partial: true }
}
