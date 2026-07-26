import type { Segment, Session } from '../types'

/**
 * Computes the union of a set of intervals (start, end).
 * Overlapping intervals are merged so they aren't double-counted.
 */
export function unionIntervals(intervals: {start: number, end: number}[]): number {
  if (intervals.length === 0) return 0
  
  // Sort intervals by start time
  const sorted = [...intervals].sort((a, b) => a.start - b.start)
  
  let totalDurationMs = 0
  let currentStart = sorted[0].start
  let currentEnd = sorted[0].end
  
  for (let i = 1; i < sorted.length; i++) {
    const next = sorted[i]
    if (next.start <= currentEnd) {
      // Overlapping or adjacent, extend currentEnd
      currentEnd = Math.max(currentEnd, next.end)
    } else {
      // Gap, commit current interval
      totalDurationMs += (currentEnd - currentStart)
      currentStart = next.start
      currentEnd = next.end
    }
  }
  
  // Add the final interval
  totalDurationMs += (currentEnd - currentStart)
  
  // Return minutes, rounded to nearest integer
  return Math.max(1, Math.round(totalDurationMs / 1000 / 60))
}

/**
 * Stitches segments into a single Session.
 * Only segments that are 'active' contribute to the duration.
 */
export function stitchSegments(segments: Segment[], sessionId: string): Session {
  if (segments.length === 0) {
    throw new Error("Cannot stitch 0 segments")
  }
  
  // Filter active segments for duration calculation
  const activeIntervals = segments
    .filter(s => s.active)
    .map(s => ({ start: s.start, end: s.end }))
    
  const duration_min = unionIntervals(activeIntervals)
  
  const sources = Array.from(new Set(segments.map(s => s.url_domain)))
  
  // title_bag: simple concatenation of unique titles, capped at 255 chars
  const titles = Array.from(new Set(segments.map(s => s.title_metadata).filter(Boolean)))
  let title_bag = titles.join(" | ")
  if (title_bag.length > 255) {
    title_bag = title_bag.substring(0, 252) + "..."
  }
  
  const start = Math.min(...segments.map(s => s.start))
  const end = Math.max(...segments.map(s => s.end))
  
  return {
    session_id: sessionId,
    sources,
    title_bag,
    start,
    end,
    duration_min
  }
}

/**
 * Groups segments into session boundaries by real inactivity gaps between
 * segment timestamps — a pure function of the data, independent of when the
 * caller happens to flush. (Splitting sessions by *flush cadence* instead of
 * by *gap in the data* means a late flush silently merges two real study
 * sessions — e.g. a morning DSA session and an unrelated evening video —
 * into one Session with a wrong union duration and a misleading title_bag.)
 */
export function groupSegmentsBySessionGap(segments: Segment[], gapMs: number): Segment[][] {
  if (segments.length === 0) return []

  const sorted = [...segments].sort((a, b) => a.start - b.start)
  const groups: Segment[][] = []
  let current: Segment[] = [sorted[0]]
  let currentMaxEnd = sorted[0].end

  for (let i = 1; i < sorted.length; i++) {
    const seg = sorted[i]
    if (seg.start - currentMaxEnd >= gapMs) {
      groups.push(current)
      current = [seg]
      currentMaxEnd = seg.end
    } else {
      current.push(seg)
      currentMaxEnd = Math.max(currentMaxEnd, seg.end)
    }
  }
  groups.push(current)
  return groups
}

/**
 * Splits a buffer into sessions that are definitively CLOSED (a gap was
 * observed after them — safe to stitch and sync) versus the trailing group
 * that might still be LIVE (last activity is within one gap window of
 * `now`, so more segments could still arrive for it). The caller should
 * flush `closed` and keep buffering `live`.
 */
export function partitionClosedSessions(
  segments: Segment[], gapMs: number, now: number
): { closed: Segment[][]; live: Segment[] } {
  const groups = groupSegmentsBySessionGap(segments, gapMs)
  if (groups.length === 0) return { closed: [], live: [] }

  const lastGroup = groups[groups.length - 1]
  const lastGroupEnd = Math.max(...lastGroup.map(s => s.end))

  if (now - lastGroupEnd >= gapMs) {
    // Even the trailing group has gone quiet long enough to be closed too.
    return { closed: groups, live: [] }
  }
  return { closed: groups.slice(0, -1), live: lastGroup }
}
