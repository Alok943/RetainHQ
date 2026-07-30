import type { Segment, Session } from '../types'

// Backend's CompanionSessionIn.content max_length — enforced here too so a
// session assembled from several already-capped segments (e.g. a tab left
// open across two chat_extract.ts snapshots on different pages) can't exceed
// it; each individual snapshot is already within budget, this is a second
// guard on the sum.
const MAX_SESSION_CONTENT_CHARS = 16_000

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

  // Each segment's `content` is a full snapshot of the conversation as of
  // its own capture time (chat_extract.ts), not an incremental delta —
  // concatenating every segment would repeat the same turns over and over as
  // the conversation grows. Take the snapshot from whichever segment ran
  // latest instead; it's the most complete one.
  const contentSegments = segments.filter(s => s.content)
  let content: string | undefined
  if (contentSegments.length > 0) {
    const latest = contentSegments.reduce((a, b) => (b.end > a.end ? b : a))
    content = latest.content!.length > MAX_SESSION_CONTENT_CHARS
      ? latest.content!.slice(latest.content!.length - MAX_SESSION_CONTENT_CHARS)
      : latest.content
  }

  // Unlike content, each segment's `chapters` IS a delta (seconds watched
  // since the last emit — chapter_extract.ts's accumulator resets on every
  // read), so summing same-titled entries across every segment in the group
  // is correct, not double-counting. Order doesn't matter here the way it
  // does for content's snapshot-pick.
  const chapterTotals: Record<string, number> = {}
  for (const seg of segments) {
    if (!seg.chapters) continue
    for (const c of seg.chapters) {
      chapterTotals[c.title] = (chapterTotals[c.title] ?? 0) + c.seconds
    }
  }
  const chapters = Object.entries(chapterTotals).map(([title, seconds]) => ({ title, seconds }))

  return {
    session_id: sessionId,
    sources,
    title_bag,
    start,
    end,
    duration_min,
    ...(content ? { content } : {}),
    ...(chapters.length > 0 ? { chapters } : {}),
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
 * What the service worker should sync right now, and which of those groups is
 * allowed to carry chat content.
 *
 * Pure and here (rather than inline in service_worker.ts) because the
 * `isClosed` flag is load-bearing, not bookkeeping: chat_extract.ts snapshots
 * the WHOLE visible conversation each time, so a long chat checkpointed
 * repeatedly would ship cumulative snapshots and the backend would segment
 * and record the same early turns once per checkpoint. Only a genuinely
 * closed session may carry content. service_worker.ts is untestable in
 * isolation (module-level alarm registration + supabase client), so this
 * decision lives where it can actually be pinned by tests.
 */
export function planSync(
  segments: Segment[], killMs: number, checkpointMs: number, activityRecencyMs: number, now: number
): { toSync: { group: Segment[]; isClosed: boolean }[]; remainingLive: Segment[] } {
  const { closed, live } = partitionClosedSessions(segments, killMs, now)
  const toSync = closed.map((group) => ({ group, isClosed: true }))

  if (live.length > 0) {
    const liveStart = Math.min(...live.map((s) => s.start))
    const lastEnd = Math.max(...live.map((s) => s.end))
    // BOTH conditions, and the second one is not optional. checkpointMs (15m)
    // is SHORTER than killMs (20m), so "has been running a while" alone fires
    // on a session whose activity already stopped — clearing the buffer and
    // destroying the trailing segments before the kill window could ever
    // recognize them as closed. That session then never closes at all: its
    // content is silently dropped and its final minutes sync as a
    // checkpoint. Requiring recent activity means a session that has gone
    // quiet rides out the kill window and closes properly instead.
    const stillActive = now - lastEnd <= activityRecencyMs
    if (stillActive && now - liveStart >= checkpointMs) {
      // Genuinely ongoing and running long enough that withholding it would
      // leave a multi-hour session showing nothing synced. Send
      // progress-so-far — WITHOUT content.
      toSync.push({ group: live, isClosed: false })
      return { toSync, remainingLive: [] }
    }
  }
  return { toSync, remainingLive: live }
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
