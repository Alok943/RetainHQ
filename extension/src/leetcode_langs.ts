// Shared between the popup (import options UI) and the background scan
// (background/leetcode_backfill.ts) — a small, deliberately incomplete map
// from a label a human recognizes to the raw `lang` value(s) LeetCode's
// submission API actually reports. Not every language LeetCode supports is
// listed; this is the common set, and a filter this codebase doesn't know
// about simply can't be selected rather than silently mismatching.
//
// Grouped, not 1:1: LeetCode has used both "python" and "python3" for the
// same human choice at different points, so "Python" maps to both.

export interface LanguageGroup {
  label: string
  langs: string[]
}

export const LANGUAGE_GROUPS: LanguageGroup[] = [
  { label: 'Python', langs: ['python', 'python3'] },
  { label: 'C++', langs: ['cpp'] },
  { label: 'Java', langs: ['java'] },
  { label: 'JavaScript', langs: ['javascript'] },
  { label: 'TypeScript', langs: ['typescript'] },
  { label: 'C', langs: ['c'] },
  { label: 'C#', langs: ['csharp'] },
  { label: 'Go', langs: ['golang'] },
  { label: 'Rust', langs: ['rust'] },
  { label: 'Swift', langs: ['swift'] },
  { label: 'Kotlin', langs: ['kotlin'] },
]

export interface WindowOption {
  /** Stable value for a <select>/storage — NOT the same as `days`, since
   * "all time" has to serialize to something other than `null` in an HTML
   * <option value>. */
  value: string
  label: string
  /** null = no cutoff at all. */
  days: number | null
}

export const WINDOW_OPTIONS: WindowOption[] = [
  { value: '30', label: 'Last 30 days', days: 30 },
  { value: '60', label: 'Last 60 days', days: 60 },
  { value: '90', label: 'Last 90 days', days: 90 },
  { value: '365', label: 'Last 12 months', days: 365 },
  { value: 'all', label: 'All time', days: null },
]

/** LeetCode returns submissions newest-first, so pagination stops as soon as
 * a page runs past the cutoff — a 2-month window costs a handful of pages,
 * not the whole account history. Matches WINDOW_OPTIONS's "Last 60 days". */
export const DEFAULT_WINDOW_DAYS = 60

/**
 * Persisted shape of the user's last import choice (`chrome.storage.local`,
 * key `leetcodeImportPrefs`). `langs: null` and `windowDays: null` both mean
 * "no filter" — matches everything, same as the pre-filter behavior — which
 * is also what a never-configured install effectively falls back to if a
 * message omits these fields (see service_worker.ts).
 */
export interface LeetCodeImportPrefs {
  windowDays: number | null
  /** Raw `lang` values already flattened out of whichever LanguageGroups were
   * checked — the background scan only ever compares against this flat form. */
  langs: string[] | null
}
