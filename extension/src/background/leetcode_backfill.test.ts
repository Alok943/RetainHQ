import { describe, it, expect, vi } from 'vitest'
import { collectSolves, scanRecentSolves } from './leetcode_backfill'

const HOUR = 60 * 60 * 1000
const DAY = 24 * HOUR

/** Epoch SECONDS, as LeetCode sends them. */
const secondsAgo = (ms: number) => Math.floor((Date.now() - ms) / 1000)

const row = (over: Record<string, unknown> = {}) => ({
  title_slug: 'two-sum',
  lang: 'python3',
  status_display: 'Accepted',
  timestamp: secondsAgo(1 * DAY),
  ...over,
})

const PYTHON = new Set(['python', 'python3'])

describe('collectSolves', () => {
  const cutoff = () => Date.now() - 60 * DAY

  it('keeps an accepted solve inside the window when it matches the language filter', () => {
    const acc = new Map<string, number>()
    collectSolves([row()], cutoff(), acc, PYTHON)
    expect([...acc.keys()]).toEqual(['two-sum'])
  })

  it('null langs means no filter at all — every language is kept', () => {
    const acc = new Map<string, number>()
    collectSolves(
      [row({ lang: 'cpp', title_slug: 'old-cpp' }), row({ lang: 'java', title_slug: 'old-java' })],
      cutoff(),
      acc,
      null,
    )
    expect(acc.size).toBe(2)
  })

  it('a non-null filter drops languages outside it — the whole point of the option', () => {
    const acc = new Map<string, number>()
    collectSolves(
      [row({ lang: 'cpp', title_slug: 'old-cpp' }), row({ lang: 'java', title_slug: 'old-java' })],
      cutoff(),
      acc,
      PYTHON,
    )
    expect(acc.size).toBe(0)
  })

  it('accepts either spelling of python and is case-insensitive', () => {
    const acc = new Map<string, number>()
    collectSolves(
      [row({ lang: 'Python3', title_slug: 'a' }), row({ lang: 'python', title_slug: 'b' })],
      cutoff(),
      acc,
      PYTHON,
    )
    expect([...acc.keys()].sort()).toEqual(['a', 'b'])
  })

  it('drops submissions that were not accepted, filter or no filter', () => {
    const acc = new Map<string, number>()
    collectSolves(
      [row({ status_display: 'Wrong Answer' }), row({ status_display: 'Time Limit Exceeded' })],
      cutoff(),
      acc,
      null,
    )
    expect(acc.size).toBe(0)
  })

  it('drops anything older than the cutoff and reports crossing it', () => {
    const acc = new Map<string, number>()
    const result = collectSolves(
      [row({ title_slug: 'recent' }), row({ title_slug: 'ancient', timestamp: secondsAgo(200 * DAY) })],
      cutoff(),
      acc,
      null,
    )
    expect([...acc.keys()]).toEqual(['recent'])
    expect(result.crossedCutoff).toBe(true)
  })

  it('cutoffMs=0 (all-time scan) never crosses, since every real timestamp is positive', () => {
    const acc = new Map<string, number>()
    const result = collectSolves(
      [row({ timestamp: secondsAgo(2000 * DAY) })],
      0,
      acc,
      null,
    )
    expect(acc.size).toBe(1)
    expect(result.crossedCutoff).toBe(false)
  })

  it('keeps the EARLIEST solve when a problem was re-solved in the window', () => {
    // Re-solving is one act of learning; taking the latest would re-date old
    // work to whenever it was last revisited.
    const acc = new Map<string, number>()
    collectSolves(
      [row({ timestamp: secondsAgo(2 * DAY) }), row({ timestamp: secondsAgo(30 * DAY) })],
      cutoff(),
      acc,
      null,
    )
    const solvedMs = acc.get('two-sum')!
    expect(Math.round((Date.now() - solvedMs) / DAY)).toBe(30)
  })

  it('skips rows with an unusable timestamp rather than guessing', () => {
    const acc = new Map<string, number>()
    const result = collectSolves(
      [row({ timestamp: undefined }), row({ timestamp: 'not-a-number' })],
      cutoff(),
      acc,
      null,
    )
    expect(acc.size).toBe(0)
    // Must NOT be read as "we reached the end of the window" — that would stop
    // pagination early and silently truncate the import.
    expect(result.crossedCutoff).toBe(false)
  })

  it('accepts a string timestamp, which LeetCode sometimes sends', () => {
    const acc = new Map<string, number>()
    collectSolves([row({ timestamp: String(secondsAgo(3 * DAY)) })], cutoff(), acc, null)
    expect(acc.size).toBe(1)
  })
})

describe('scanRecentSolves', () => {
  const page = (rows: unknown[], has_next = true) => ({
    ok: true,
    status: 200,
    json: async () => ({ submissions_dump: rows, has_next }),
  }) as unknown as Response

  it('stops paginating as soon as a page crosses the cutoff', async () => {
    const fetchImpl = vi.fn()
      .mockResolvedValueOnce(page([row({ title_slug: 'a' })]))
      .mockResolvedValueOnce(page([row({ title_slug: 'b', timestamp: secondsAgo(400 * DAY) })]))
      .mockResolvedValueOnce(page([row({ title_slug: 'c' })]))

    const { solves, partial } = await scanRecentSolves(
      Date.now() - 60 * DAY, null, fetchImpl as unknown as typeof fetch, 0,
    )

    expect([...solves.keys()]).toEqual(['a'])
    expect(partial).toBe(false)
    expect(fetchImpl).toHaveBeenCalledTimes(2) // never fetched the third page
  })

  it('applies the language filter across the whole scan', async () => {
    const fetchImpl = vi.fn().mockResolvedValueOnce(page(
      [row({ title_slug: 'py', lang: 'python3' }), row({ title_slug: 'cpp', lang: 'cpp' })],
      false,
    ))
    const { solves } = await scanRecentSolves(
      Date.now() - 60 * DAY, PYTHON, fetchImpl as unknown as typeof fetch, 0,
    )
    expect([...solves.keys()]).toEqual(['py'])
  })

  it('stops on has_next=false', async () => {
    const fetchImpl = vi.fn().mockResolvedValueOnce(page([row({ title_slug: 'a' })], false))
    const { solves, partial } = await scanRecentSolves(
      Date.now() - 60 * DAY, null, fetchImpl as unknown as typeof fetch, 0,
    )
    expect(solves.size).toBe(1)
    expect(partial).toBe(false)
    expect(fetchImpl).toHaveBeenCalledTimes(1)
  })

  it('returns what it has and flags partial on a 429 rather than losing everything', async () => {
    const fetchImpl = vi.fn()
      .mockResolvedValueOnce(page([row({ title_slug: 'a' })]))
      .mockResolvedValueOnce({ ok: false, status: 429 } as Response)

    const { solves, partial } = await scanRecentSolves(
      Date.now() - 60 * DAY, null, fetchImpl as unknown as typeof fetch, 0,
    )
    expect([...solves.keys()]).toEqual(['a'])
    expect(partial).toBe(true)
  })

  it('throws a message-bearing error on a login page so the popup can name it', async () => {
    const fetchImpl = vi.fn().mockResolvedValueOnce({
      ok: true, status: 200, json: async () => { throw new SyntaxError('unexpected <') },
    } as unknown as Response)

    await expect(
      scanRecentSolves(Date.now() - 60 * DAY, null, fetchImpl as unknown as typeof fetch, 0),
    ).rejects.toThrow('login page')
  })

  it('sends cookies — without them LeetCode answers as signed-out', async () => {
    const fetchImpl = vi.fn().mockResolvedValueOnce(page([], false))
    await scanRecentSolves(Date.now() - 60 * DAY, null, fetchImpl as unknown as typeof fetch, 0)
    expect(fetchImpl).toHaveBeenCalledWith(expect.any(String), { credentials: 'include' })
  })
})
