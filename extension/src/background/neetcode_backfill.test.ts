import { describe, it, expect, vi } from 'vitest'
import { extractSlugs, earliestActivityDate, scanCompletedProblems } from './neetcode_backfill'

// Verbatim shape of a real getCompletedProblems response, recorded from a
// signed-in tab 2026-08-02. Kept literal because the ENTIRE reason this module
// works is that NeetCode returns LeetCode URLs — if that ever changes, this
// fixture should stop matching reality and these tests should be the thing that
// notices.
const REAL_RESPONSE = {
  'Two Pointers': [
    'https://leetcode.com/problems/valid-palindrome/',
    'https://leetcode.com/problems/two-sum-ii-input-array-is-sorted/',
    'https://leetcode.com/problems/3sum/',
  ],
  'Arrays & Hashing': [
    'https://leetcode.com/problems/contains-duplicate/',
    'https://leetcode.com/problems/two-sum/',
  ],
}

describe('extractSlugs', () => {
  it('pulls LeetCode slugs out of the category -> URL map', () => {
    expect(extractSlugs(REAL_RESPONSE).sort()).toEqual([
      '3sum', 'contains-duplicate', 'two-sum', 'two-sum-ii-input-array-is-sorted', 'valid-palindrome',
    ])
  })

  it('dedupes a problem listed under two categories', () => {
    expect(extractSlugs({
      A: ['https://leetcode.com/problems/two-sum/'],
      B: ['https://leetcode.com/problems/two-sum/'],
    })).toEqual(['two-sum'])
  })

  it('handles a URL with no trailing slash, a query, or a fragment', () => {
    expect(extractSlugs({
      A: [
        'https://leetcode.com/problems/valid-anagram',
        'https://leetcode.com/problems/lru-cache/?envType=list',
        'https://leetcode.com/problems/min-stack/#solution',
      ],
    }).sort()).toEqual(['lru-cache', 'min-stack', 'valid-anagram'])
  })

  it('DROPS anything that is not a recognisable LeetCode problem URL', () => {
    // NeetCode also lists its own course content. A slug we cannot confidently
    // read is worth losing — attributing it to the wrong problem would be
    // silently-wrong mastery on a real node.
    expect(extractSlugs({
      Courses: [
        'https://neetcode.io/problems/dynamicArray',
        'https://example.com/problems/two-sum/',
        'not a url',
        '',
      ],
    })).toEqual([])
  })

  it('survives junk instead of a response without throwing', () => {
    for (const junk of [null, undefined, 'a string', 42, { A: 'not-an-array' }, { A: [null, 7] }]) {
      expect(extractSlugs(junk)).toEqual([])
    }
  })
})

describe('earliestActivityDate', () => {
  it('returns the OLDEST activity date — backdating understates recency on purpose', () => {
    // NeetCode gives no per-problem date. Choosing the earliest means these
    // solves decay more and surface for review sooner, rather than claiming the
    // user learned everything the day they pressed Import.
    expect(earliestActivityDate({
      activityByDate: {
        '2026-07-21': { hasActivity: true, count: 5 },
        '2026-02-17': { hasActivity: true, count: 2 },
        '2026-08-02': { hasActivity: true, count: 2 },
      },
    })).toBe('2026-02-17T00:00:00.000Z')
  })

  it('returns null rather than inventing a date when there is no activity map', () => {
    for (const junk of [null, undefined, {}, { activityByDate: {} }, { activityByDate: 'nope' }]) {
      expect(earliestActivityDate(junk)).toBeNull()
    }
  })

  it('ignores keys that are not ISO dates', () => {
    expect(earliestActivityDate({ activityByDate: { total: 9, '2026-03-01': 1 } }))
      .toBe('2026-03-01T00:00:00.000Z')
  })
})

const okJson = (data: unknown) => ({ status: 200, ok: true, json: async () => ({ data }) })

describe('scanCompletedProblems', () => {
  it('calls the callable endpoint with the right functionId and returns slugs + date', async () => {
    const pageFetch = vi.fn()
      .mockResolvedValueOnce(okJson(REAL_RESPONSE))
      .mockResolvedValueOnce(okJson({ activityByDate: { '2026-02-17': { count: 2 } } }))

    const result = await scanCompletedProblems(pageFetch)

    expect(result.slugs).toHaveLength(5)
    expect(result.earliestActivity).toBe('2026-02-17T00:00:00.000Z')
    expect(JSON.parse(pageFetch.mock.calls[0][1].body)).toEqual({
      data: { functionId: 'getCompletedProblems' },
    })
    expect(pageFetch.mock.calls[0][1].method).toBe('POST')
  })

  it('does not spend a second round trip when there is nothing to date', async () => {
    const pageFetch = vi.fn().mockResolvedValueOnce(okJson({}))
    const result = await scanCompletedProblems(pageFetch)
    expect(result).toEqual({ slugs: [], earliestActivity: null })
    expect(pageFetch).toHaveBeenCalledTimes(1)
  })

  it('keeps the slugs when the DATE call fails — a worse date beats a lost import', async () => {
    const pageFetch = vi.fn()
      .mockResolvedValueOnce(okJson(REAL_RESPONSE))
      .mockRejectedValueOnce(new Error('boom'))

    const result = await scanCompletedProblems(pageFetch)
    expect(result.slugs).toHaveLength(5)
    // null, not a guess — the backend then falls back to import time.
    expect(result.earliestActivity).toBeNull()
  })

  it('names a bad status so the popup can show it', async () => {
    const pageFetch = vi.fn().mockResolvedValue({ status: 403, ok: false, json: async () => ({}) })
    await expect(scanCompletedProblems(pageFetch)).rejects.toThrow('NeetCode returned 403')
  })

  it('reports a login page as such rather than as a parse error', async () => {
    const pageFetch = vi.fn().mockResolvedValue({
      status: 200, ok: true, json: async () => { throw new SyntaxError('unexpected <') },
    })
    await expect(scanCompletedProblems(pageFetch)).rejects.toThrow(/login page/)
  })
})
