// Reads the user's completed-problem list off neetcode.io.
//
// Endpoint found 2026-08-02 by recording API traffic in a signed-in tab:
//
//   POST /api/callableFunctionHttp  {"data":{"functionId":"getCompletedProblems"}}
//   -> {"data":{"Two Pointers":["https://leetcode.com/problems/valid-palindrome/", ...],
//               "Arrays & Hashing":[...]}}
//
// Two things about that response drive everything below.
//
// It returns LEETCODE URLs. NeetCode links out to LeetCode to solve, so what
// comes back are LeetCode problem slugs — which resolve against our existing
// LeetCode catalog directly and need no alias lookup at all (the alias table
// from D-071 is for LIVE capture, where the slug is NeetCode's own).
//
// It carries NO DATES. Not per problem, not anywhere. `getUserStreakData` gives
// daily activity COUNTS but never says which problem, so a per-problem date
// cannot be reconstructed without inventing it. Instead we send the EARLIEST
// date the account has any activity on, for the whole batch: that understates
// recency, so those solves decay more and come up for review sooner, rather
// than claiming the user learned 22 problems this afternoon. Backdating like
// this is the same direction the rest of the evidence pipeline errs in.
//
// The backend tiers this import T3_observed, not T1 — see the /neetcode/backfill
// docstring. Nothing here should be read as "these are verified solves".

import type { PageFetch } from './leetcode_backfill'

const CALLABLE_URL = 'https://neetcode.io/api/callableFunctionHttp'

/** Matches the slug in a LeetCode problem URL, with or without a trailing slash. */
const LEETCODE_SLUG_RE = /leetcode\.com\/problems\/([^/?#]+)/i

export interface NeetCodeScanResult {
  /** LeetCode slugs, deduped. Order is not meaningful. */
  slugs: string[]
  /** ISO date of the account's earliest recorded activity, or null when
   * NeetCode reports none — the caller must then let the backend fall back to
   * import time rather than invent a date here. */
  earliestActivity: string | null
}

async function callFunction(pageFetch: PageFetch, functionId: string): Promise<any> {
  const res = await pageFetch(CALLABLE_URL, {
    method: 'POST',
    body: JSON.stringify({ data: { functionId } }),
  })
  if (!res.ok) throw new Error(`NeetCode returned ${res.status}`)
  try {
    return (await res.json())?.data
  } catch {
    // Signed out, or NeetCode served an interstitial. Same failure shape the
    // LeetCode scan reports, and the popup shows it verbatim.
    throw new Error('NeetCode sent a login page, not data — sign in and retry')
  }
}

/**
 * Pulls the LeetCode slugs out of `getCompletedProblems`'s category → URL map.
 *
 * Pure and separately tested: this is the product decision (what counts as an
 * imported completion), not the transport around it. Anything that isn't a
 * recognisable LeetCode problem URL is DROPPED rather than guessed at — NeetCode
 * also lists its own course content, and a slug we can't confidently read is
 * worth losing rather than attributing to the wrong problem.
 */
export function extractSlugs(completed: unknown): string[] {
  if (!completed || typeof completed !== 'object') return []
  const slugs = new Set<string>()
  for (const urls of Object.values(completed as Record<string, unknown>)) {
    if (!Array.isArray(urls)) continue
    for (const url of urls) {
      if (typeof url !== 'string') continue
      const match = LEETCODE_SLUG_RE.exec(url)
      if (match) slugs.add(match[1].toLowerCase())
    }
  }
  return [...slugs]
}

/**
 * Earliest date in `getUserStreakData`'s `activityByDate` map (keys are
 * 'YYYY-MM-DD'). Returns null rather than a default when the map is missing or
 * empty — a fabricated date is worse than none, and the backend already has a
 * documented fallback.
 */
export function earliestActivityDate(streak: unknown): string | null {
  const byDate = (streak as { activityByDate?: unknown } | null)?.activityByDate
  if (!byDate || typeof byDate !== 'object') return null
  // Lexicographic sort is correct for zero-padded ISO dates, and avoids parsing
  // 300+ keys into Date objects just to find a minimum.
  const dates = Object.keys(byDate).filter((d) => /^\d{4}-\d{2}-\d{2}$/.test(d)).sort()
  return dates.length ? `${dates[0]}T00:00:00.000Z` : null
}

export async function scanCompletedProblems(pageFetch: PageFetch): Promise<NeetCodeScanResult> {
  const completed = await callFunction(pageFetch, 'getCompletedProblems')
  const slugs = extractSlugs(completed)
  if (slugs.length === 0) return { slugs, earliestActivity: null }

  // Only worth a second round trip once we know there is something to date.
  // A failure here must not lose the slugs we already have — the backend's
  // import-time fallback is a worse date, not a broken import.
  let earliestActivity: string | null = null
  try {
    earliestActivity = earliestActivityDate(await callFunction(pageFetch, 'getUserStreakData'))
  } catch (error) {
    console.warn('[RetainHQ] Could not read NeetCode activity dates; backend will use import time', error)
  }
  return { slugs, earliestActivity }
}
