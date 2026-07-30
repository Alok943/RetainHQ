import { describe, it, expect } from 'vitest'
import { unionIntervals, stitchSegments, groupSegmentsBySessionGap, partitionClosedSessions, planSync } from './stitcher'
import type { Segment } from '../types'

const GAP_MS = 15 * 60 * 1000
const KILL_MS = 20 * 60 * 1000
const CHECKPOINT_MS = 15 * 60 * 1000
const RECENCY_MS = 6 * 60 * 1000

function seg(surface: string, start: number, end: number, content?: string): Segment {
  return { surface, url_domain: `${surface}.com`, title_metadata: surface, start, end, active: true, ...(content ? { content } : {}) }
}

describe('unionIntervals', () => {
  it('calculates duration for non-overlapping intervals', () => {
    // 5 mins and 10 mins
    const intervals = [
      { start: 0, end: 5 * 60 * 1000 },
      { start: 10 * 60 * 1000, end: 20 * 60 * 1000 }
    ]
    expect(unionIntervals(intervals)).toBe(15)
  })

  it('merges overlapping intervals (e.g. tabs double counted)', () => {
    // Both tabs active 0-10, one extends to 15
    const intervals = [
      { start: 0, end: 10 * 60 * 1000 },
      { start: 5 * 60 * 1000, end: 15 * 60 * 1000 }
    ]
    expect(unionIntervals(intervals)).toBe(15)
  })

  it('handles nested intervals', () => {
    const intervals = [
      { start: 0, end: 20 * 60 * 1000 },
      { start: 5 * 60 * 1000, end: 10 * 60 * 1000 }
    ]
    expect(unionIntervals(intervals)).toBe(20)
  })

  it('rounds to nearest minute, min 1 min', () => {
    const intervals = [
      { start: 0, end: 30 * 1000 } // 30 seconds
    ]
    expect(unionIntervals(intervals)).toBe(1)
  })
})

describe('stitchSegments', () => {
  it('stitching produces correct Session object', () => {
    const segments: Segment[] = [
      { surface: 'youtube', url_domain: 'youtube.com', title_metadata: 'React Course', start: 1000000, end: 1600000, active: true },
      { surface: 'leetcode', url_domain: 'leetcode.com', title_metadata: 'Two Sum', start: 1300000, end: 2200000, active: true }
    ]
    
    const session = stitchSegments(segments, 'sess-123')
    expect(session.session_id).toBe('sess-123')
    expect(session.sources).toEqual(['youtube.com', 'leetcode.com'])
    expect(session.title_bag).toBe('React Course | Two Sum')
    expect(session.start).toBe(1000000)
    expect(session.end).toBe(2200000)
    expect(session.duration_min).toBe(20) // (2200000 - 1000000)/60000 = 20 mins
  })

  it('ignores inactive segments for duration', () => {
    const segments: Segment[] = [
      { surface: 'youtube', url_domain: 'youtube.com', title_metadata: 'React Course', start: 0, end: 10 * 60 * 1000, active: true },
      { surface: 'leetcode', url_domain: 'leetcode.com', title_metadata: 'Two Sum', start: 10 * 60 * 1000, end: 60 * 60 * 1000, active: false }
    ]

    const session = stitchSegments(segments, 'sess-123')
    expect(session.duration_min).toBe(10) // Only the 10 minute active segment counts
  })

  it('omits content when no segment carries any', () => {
    const session = stitchSegments([seg('youtube', 0, 60000)], 'sess-123')
    expect(session.content).toBeUndefined()
  })

  it('picks the latest content snapshot, not a concatenation of all of them', () => {
    // Each snapshot is already a full read of the conversation as of its own
    // capture time — joining an early, partial snapshot with a later, fuller
    // one would just repeat the earlier turns inside the later ones.
    const segments: Segment[] = [
      { surface: 'chatgpt', url_domain: 'chatgpt.com', title_metadata: 'chat', start: 0, end: 5 * 60 * 1000, active: true, content: 'U: first question' },
      { surface: 'chatgpt', url_domain: 'chatgpt.com', title_metadata: 'chat', start: 5 * 60 * 1000, end: 10 * 60 * 1000, active: true, content: 'U: first question\nA: reply\nU: second question' },
    ]
    const session = stitchSegments(segments, 'sess-123')
    expect(session.content).toBe('U: first question\nA: reply\nU: second question')
  })

  it('caps the stitched content length even though each snapshot is already capped', () => {
    const long = 'x'.repeat(20_000)
    const segments: Segment[] = [
      { surface: 'chatgpt', url_domain: 'chatgpt.com', title_metadata: 'chat', start: 0, end: 60000, active: true, content: long },
    ]
    const session = stitchSegments(segments, 'sess-123')
    expect(session.content?.length).toBe(16_000)
    expect(session.content).toBe(long.slice(-16_000))
  })

  it('omits chapters when no segment carries any', () => {
    const session = stitchSegments([seg('youtube', 0, 60000)], 'sess-123')
    expect(session.chapters).toBeUndefined()
  })

  it('SUMS same-titled chapter seconds across segments, unlike content\'s pick-latest', () => {
    // Each segment's chapters entry is a DELTA (seconds watched since the
    // last emit), not a snapshot — summing is correct here, unlike content.
    const segments: Segment[] = [
      { surface: 'youtube', url_domain: 'youtube.com', title_metadata: 'video', start: 0, end: 5 * 60 * 1000, active: true, chapters: [{ title: 'Intro', seconds: 300 }] },
      { surface: 'youtube', url_domain: 'youtube.com', title_metadata: 'video', start: 5 * 60 * 1000, end: 10 * 60 * 1000, active: true, chapters: [{ title: 'Intro', seconds: 120 }, { title: 'Setup', seconds: 180 }] },
    ]
    const session = stitchSegments(segments, 'sess-123')
    expect(session.chapters).toEqual(expect.arrayContaining([
      { title: 'Intro', seconds: 420 },
      { title: 'Setup', seconds: 180 },
    ]))
    expect(session.chapters?.length).toBe(2)
  })
})

describe('groupSegmentsBySessionGap', () => {
  it('keeps segments within the gap window in one group', () => {
    const segments = [seg('claude', 0, 5 * 60 * 1000), seg('leetcode', 10 * 60 * 1000, 20 * 60 * 1000)]
    const groups = groupSegmentsBySessionGap(segments, GAP_MS)
    expect(groups.length).toBe(1)
    expect(groups[0].length).toBe(2)
  })

  it('splits into separate groups across a gap >= threshold', () => {
    // 0-5min, then a 20 min gap, then 25-30min
    const segments = [seg('claude', 0, 5 * 60 * 1000), seg('leetcode', 25 * 60 * 1000, 30 * 60 * 1000)]
    const groups = groupSegmentsBySessionGap(segments, GAP_MS)
    expect(groups.length).toBe(2)
    expect(groups[0].length).toBe(1)
    expect(groups[1].length).toBe(1)
  })

  it('gap-splitting is a property of the data, not of when the caller flushes', () => {
    // Same two clusters regardless of how many segments accumulate between
    // them before the caller ever looks — this is the point of pulling
    // gap-splitting out of the service worker's flush cadence.
    const morning = [seg('claude', 0, 5 * 60 * 1000), seg('leetcode', 3 * 60 * 1000, 8 * 60 * 1000)]
    const evening = [seg('youtube', 8 * 60 * 60 * 1000, 8 * 60 * 60 * 1000 + 20 * 60 * 1000)]
    const groups = groupSegmentsBySessionGap([...morning, ...evening], GAP_MS)
    expect(groups.length).toBe(2)
    expect(groups[0].length).toBe(2)
    expect(groups[1].length).toBe(1)
  })
})

describe('partitionClosedSessions', () => {
  it('treats the trailing group as live when the gap has not yet elapsed', () => {
    const segments = [seg('claude', 0, 5 * 60 * 1000)]
    const now = 6 * 60 * 1000 // only 1 min since last activity, well under the 15 min gap
    const { closed, live } = partitionClosedSessions(segments, GAP_MS, now)
    expect(closed.length).toBe(0)
    expect(live.length).toBe(1)
  })

  it('closes the trailing group once the gap has elapsed', () => {
    const segments = [seg('claude', 0, 5 * 60 * 1000)]
    const now = 5 * 60 * 1000 + GAP_MS // exactly one gap window after last activity
    const { closed, live } = partitionClosedSessions(segments, GAP_MS, now)
    expect(closed.length).toBe(1)
    expect(live.length).toBe(0)
  })

  it('closes earlier groups while keeping only the trailing one live', () => {
    const earlier = [seg('claude', 0, 5 * 60 * 1000)]
    const recent = [seg('leetcode', 25 * 60 * 1000, 30 * 60 * 1000)]
    const now = 31 * 60 * 1000 // 1 min after recent activity — recent is still live
    const { closed, live } = partitionClosedSessions([...earlier, ...recent], GAP_MS, now)
    expect(closed.length).toBe(1)
    expect(closed[0]).toEqual(earlier)
    expect(live).toEqual(recent)
  })
})

describe('planSync — content rides only genuinely-closed sessions', () => {
  it('holds a short live session back entirely', () => {
    const segments = [seg('chatgpt', 0, 5 * 60 * 1000, 'U: turns 1..2')]
    const { toSync, remainingLive } = planSync(segments, KILL_MS, CHECKPOINT_MS, RECENCY_MS, 6 * 60 * 1000)
    expect(toSync).toEqual([])
    expect(remainingLive).toEqual(segments)
  })

  it('marks a checkpointed-but-still-live session isClosed=false', () => {
    // 16 min of continuous activity: past the checkpoint window, not past kill.
    const segments = [seg('chatgpt', 0, 16 * 60 * 1000, 'U: turns 1..6')]
    const { toSync, remainingLive } = planSync(segments, KILL_MS, CHECKPOINT_MS, RECENCY_MS, 16 * 60 * 1000)
    expect(toSync.length).toBe(1)
    expect(toSync[0].isClosed).toBe(false)
    expect(remainingLive).toEqual([]) // buffer cleared; next checkpoint restarts the window
  })

  it('does NOT checkpoint a session whose activity already stopped', () => {
    // The root-cause regression: checkpointMs (15m) < killMs (20m), so a
    // "has been running >= 15 min" test alone fires on a session that went
    // quiet 10 minutes ago — clearing the buffer and destroying the trailing
    // segments before the kill window could ever close them. That session
    // then never closes, and its content is dropped entirely.
    const segments = [seg('chatgpt', 45 * 60 * 1000, 50 * 60 * 1000, 'U: turns 1..20')]
    const now = 60 * 60 * 1000 // 15 min since liveStart, but 10 min since last activity
    const { toSync, remainingLive } = planSync(segments, KILL_MS, CHECKPOINT_MS, RECENCY_MS, now)
    expect(toSync).toEqual([])
    expect(remainingLive).toEqual(segments) // retained, so the kill window can still close it
  })

  it('marks a genuinely-idle session isClosed=true', () => {
    const segments = [seg('chatgpt', 0, 5 * 60 * 1000, 'U: turns 1..6')]
    const { toSync } = planSync(segments, KILL_MS, CHECKPOINT_MS, RECENCY_MS, 5 * 60 * 1000 + KILL_MS)
    expect(toSync.length).toBe(1)
    expect(toSync[0].isClosed).toBe(true)
  })

  it('a long conversation yields exactly ONE content-bearing sync, not one per checkpoint', () => {
    // The regression this whole flag exists for. chat_extract.ts snapshots the
    // WHOLE visible conversation every time, so without the isClosed split a
    // 50-minute chat shipped three cumulative snapshots and the backend
    // segmented + recorded turns 1-6 three separate times.
    let buffer: Segment[] = []
    let turns = 0
    const contentBearingSyncs: string[] = []
    const EMIT = 5 * 60 * 1000

    for (let t = 0; t <= 70 * 60 * 1000; t += 60 * 1000) {
      // Activity stops at 50 min; after that only the alarm keeps ticking.
      if (t > 0 && t % EMIT === 0 && t <= 50 * 60 * 1000) {
        turns += 2
        buffer.push(seg('chatgpt', t - EMIT, t, `U: turns 1..${turns}`))
      }
      const { toSync, remainingLive } = planSync(buffer, KILL_MS, CHECKPOINT_MS, RECENCY_MS, t)
      for (const { group, isClosed } of toSync) {
        const stitched = stitchSegments(group, `sess-${t}`)
        if (isClosed && stitched.content) contentBearingSyncs.push(stitched.content)
      }
      if (toSync.length > 0) buffer = remainingLive
    }

    expect(contentBearingSyncs.length).toBe(1)
    // And it's the final, fullest snapshot — not an early partial one.
    expect(contentBearingSyncs[0]).toBe('U: turns 1..20')
  })
})

describe('planSync — chapters survive checkpointing (unlike content, by design)', () => {
  it('a long continuous watch accumulates chapter seconds exactly once, across checkpoints', () => {
    // Same 70-min simulation shape as the chat regression above, but chapters
    // are deltas — every checkpoint AND the final close should contribute,
    // with no double-count and no loss, unlike content which is deliberately
    // dropped on every checkpoint but the last.
    let buffer: Segment[] = []
    const chapterTotals: Record<string, number> = {}
    const EMIT = 5 * 60 * 1000

    for (let t = 0; t <= 70 * 60 * 1000; t += 60 * 1000) {
      if (t > 0 && t % EMIT === 0 && t <= 50 * 60 * 1000) {
        // Alternates chapters to prove cross-checkpoint summing works per-title.
        const title = t <= 25 * 60 * 1000 ? 'Intro' : 'NumPy'
        buffer.push(seg('youtube', t - EMIT, t))
        buffer[buffer.length - 1].chapters = [{ title, seconds: 300 }] // 5 min, in seconds
      }
      const { toSync, remainingLive } = planSync(buffer, KILL_MS, CHECKPOINT_MS, RECENCY_MS, t)
      for (const { group } of toSync) {
        // NOTE: chapters are NOT gated by isClosed — checkpoints count too.
        const stitched = stitchSegments(group, `sess-${t}`)
        for (const c of stitched.chapters ?? []) {
          chapterTotals[c.title] = (chapterTotals[c.title] ?? 0) + c.seconds
        }
      }
      if (toSync.length > 0) buffer = remainingLive
    }

    // 10 emits x 5 min each = 50 min total watched, split 25/25 between the
    // two chapters (5 emits each) — none lost to a checkpoint, none doubled.
    expect(chapterTotals).toEqual({ Intro: 1500, NumPy: 1500 })
  })
})
