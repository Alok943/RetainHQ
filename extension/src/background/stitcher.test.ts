import { describe, it, expect } from 'vitest'
import { unionIntervals, stitchSegments, groupSegmentsBySessionGap, partitionClosedSessions } from './stitcher'
import type { Segment } from '../types'

const GAP_MS = 15 * 60 * 1000

function seg(surface: string, start: number, end: number): Segment {
  return { surface, url_domain: `${surface}.com`, title_metadata: surface, start, end, active: true }
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
