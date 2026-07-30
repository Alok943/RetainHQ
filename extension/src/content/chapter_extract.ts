// Reads YouTube's own chapter markers so a long video (a multi-hour tutorial)
// can be attributed per-topic instead of as one undifferentiated block.
//
// Unlike chat_extract.ts, this is NOT privacy-sensitive: chapter titles are
// public video metadata the uploader added and every viewer already sees —
// not user-authored text, no consent tier, no AI processing of anything
// private. The only bar is DOM accuracy.
//
// Selector verified against a live freeCodeCamp video 2026-07-27 (135-142
// chapter items, no interaction needed to reveal them — unlike YouTube's
// separate "Show transcript" panel, which IS lazy-rendered only after a
// click). `ytd-macro-markers-list-item-renderer` items are present in the
// DOM on load. Each item duplicates its own title/timestamp internally (a
// second, differently-classed <h3> plus a second #time — a hover-preview
// clone of the same chapter, not a real second chapter) — querySelector
// (first match), not querySelectorAll, avoids reading the clone.

export interface Chapter {
  title: string
  startSeconds: number
}

function parseTimeToSeconds(text: string): number | null {
  const parts = text.trim().split(':').map(Number)
  if (parts.some((n) => Number.isNaN(n))) return null
  if (parts.length === 2) return parts[0] * 60 + parts[1]
  if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2]
  return null
}

export function extractChapters(): Chapter[] {
  const items = document.querySelectorAll('ytd-macro-markers-list-item-renderer')
  const chapters: Chapter[] = []
  items.forEach((item) => {
    const title = item.querySelector('h3.macro-markers')?.textContent?.trim()
    // `#time` is duplicated within a single item on the live page (the
    // hover-preview clone reuses the literal id "time" — confirmed 2026-07-27,
    // invalid HTML but real). querySelectorAll(...)[0], not querySelector,
    // because id-selector lookups aren't required to re-verify subtree
    // containment when the id isn't unique document-wide — relying on that
    // is fragile even where it happens to work, and jsdom's querySelector
    // gets it wrong for exactly this shape (nwsapi's #id fast path), which
    // is what caught this.
    const timeText = item.querySelectorAll('#time')[0]?.textContent?.trim()
    if (!title || !timeText) return
    const startSeconds = parseTimeToSeconds(timeText)
    if (startSeconds === null) return
    chapters.push({ title, startSeconds })
  })
  return chapters
}

export interface ChapterParseWindow {
  /** When the current video was first seen (a URL change resets this). */
  startedAt: number
  /** Last time extractChapters() was actually run for this video; 0 = never. */
  lastAttemptAt: number
}

/**
 * Whether to re-run extractChapters() right now.
 *
 * Retries are TIME-spaced, not attempt-counted, because the only caller is
 * YouTube's MutationObserver — which fires hundreds of times in the first
 * moments of a page load. A plain "try at most N times" budget is spent
 * within milliseconds, before the chapter list (rendered below the fold,
 * lazily) exists at all, so chapters were missed on most real loads while
 * looking fine in any test that populates the DOM up front.
 *
 * Bounded by `windowMs` so a video genuinely without chapters — the common
 * case — stops re-querying the DOM instead of doing it forever.
 */
export function shouldAttemptChapterParse(
  win: ChapterParseWindow, now: number, windowMs: number, minIntervalMs: number,
): boolean {
  if (now - win.startedAt > windowMs) return false
  // `lastAttemptAt === 0` means never attempted — checked explicitly rather
  // than left to arithmetic, which would otherwise block the very first
  // attempt whenever `now` is itself near 0.
  if (win.lastAttemptAt !== 0 && now - win.lastAttemptAt < minIntervalMs) return false
  return true
}

/** Which chapter a given playhead position falls in — the last chapter whose
 * start is at or before `currentTime`. `chapters` must already be in
 * video-timeline order, which `extractChapters()` produces (document order
 * matches chapter order on every case checked). */
export function chapterAt(chapters: Chapter[], currentTime: number): string | null {
  let active: Chapter | null = null
  for (const c of chapters) {
    if (c.startSeconds <= currentTime) active = c
    else break
  }
  return active?.title ?? null
}
