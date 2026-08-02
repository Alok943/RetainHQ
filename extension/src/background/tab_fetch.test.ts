import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

const tabsQuery = vi.fn()
const tabsCreate = vi.fn()
const tabsGet = vi.fn()
const tabsRemove = vi.fn()
const scriptingExecuteScript = vi.fn()

vi.mock('../browser_api', () => ({
  tabsQuery: (...a: unknown[]) => tabsQuery(...a),
  tabsCreate: (...a: unknown[]) => tabsCreate(...a),
  tabsGet: (...a: unknown[]) => tabsGet(...a),
  tabsRemove: (...a: unknown[]) => tabsRemove(...a),
  scriptingExecuteScript: (...a: unknown[]) => scriptingExecuteScript(...a),
}))

const { pageFetchVia, acquireTab, releaseTab, LEETCODE_TAB, NEETCODE_TAB } = await import('./tab_fetch')

beforeEach(() => {
  for (const m of [tabsQuery, tabsCreate, tabsGet, tabsRemove, scriptingExecuteScript]) m.mockReset()
})

describe('pageFetchVia', () => {
  it('runs the request in the PAGE, not the worker — that is the whole fix', async () => {
    // The service worker gets 403 from /api/submissions/ no matter what
    // headers or credentials it sets; the page gets 200. If world is ever
    // anything but MAIN, or the target tab is dropped, the 403 comes back.
    scriptingExecuteScript.mockResolvedValue([{ result: { status: 200, ok: true, body: '{"a":1}' } }])

    await pageFetchVia(7)('https://leetcode.com/api/submissions/?offset=0&limit=20')

    const injection = scriptingExecuteScript.mock.calls[0][0] as Record<string, unknown>
    expect(injection.world).toBe('MAIN')
    expect(injection.target).toEqual({ tabId: 7 })
    // [url, method, body] — method/body undefined for a plain GET.
    expect(injection.args).toEqual([
      'https://leetcode.com/api/submissions/?offset=0&limit=20', undefined, undefined,
    ])
  })

  it('presents the injection result as the Response shape scanRecentSolves expects', async () => {
    scriptingExecuteScript.mockResolvedValue([
      { result: { status: 200, ok: true, body: '{"submissions_dump":[],"has_next":false}' } },
    ])
    const res = await pageFetchVia(1)('https://leetcode.com/api/submissions/')
    expect(res.status).toBe(200)
    expect(res.ok).toBe(true)
    expect(await res.json()).toEqual({ submissions_dump: [], has_next: false })
  })

  it('passes a non-ok status straight through so 429 stays partial, not fatal', async () => {
    scriptingExecuteScript.mockResolvedValue([{ result: { status: 429, ok: false, body: '' } }])
    const res = await pageFetchVia(1)('https://leetcode.com/api/submissions/')
    expect(res.status).toBe(429)
    expect(res.ok).toBe(false)
  })

  it('lets a signed-out HTML body surface as a JSON error, preserving the login-page message', async () => {
    scriptingExecuteScript.mockResolvedValue([{ result: { status: 200, ok: true, body: '<!DOCTYPE html>' } }])
    const res = await pageFetchVia(1)('https://leetcode.com/api/submissions/')
    await expect(res.json()).rejects.toThrow()
  })

  it('names the site in the failure when injection returns nothing (tab navigated away mid-scan)', async () => {
    scriptingExecuteScript.mockResolvedValue([])
    await expect(pageFetchVia(1, 'LeetCode')('https://leetcode.com/api/submissions/'))
      .rejects.toThrow(/Lost the LeetCode tab/)
  })

  it('reads correctly with no label rather than "Lost the the tab"', async () => {
    scriptingExecuteScript.mockResolvedValue([])
    await expect(pageFetchVia(1)('https://leetcode.com/api/submissions/'))
      .rejects.toThrow(/^Lost the tab during the import/)
  })
})

describe('POST support (NeetCode calls a callable function, LeetCode does a plain GET)', () => {
  it('forwards method and body across the injection boundary', async () => {
    scriptingExecuteScript.mockResolvedValue([{ result: { status: 200, ok: true, body: '{}' } }])
    await pageFetchVia(3)('https://neetcode.io/api/callableFunctionHttp', {
      method: 'POST',
      body: JSON.stringify({ data: { functionId: 'getCompletedProblems' } }),
    })
    const injection = scriptingExecuteScript.mock.calls[0][0] as Record<string, any>
    expect(injection.args[1]).toBe('POST')
    expect(JSON.parse(injection.args[2])).toEqual({ data: { functionId: 'getCompletedProblems' } })
  })

  it('sends no method or body for a plain GET, keeping the LeetCode path unchanged', async () => {
    scriptingExecuteScript.mockResolvedValue([{ result: { status: 200, ok: true, body: '{}' } }])
    await pageFetchVia(3)('https://leetcode.com/api/submissions/', { credentials: 'include' })
    const injection = scriptingExecuteScript.mock.calls[0][0] as Record<string, any>
    expect(injection.args[1]).toBeUndefined()
    expect(injection.args[2]).toBeUndefined()
  })
})

describe('tab targets', () => {
  it('each names the site it borrows and a fallback page on that same site', () => {
    // The fallback must be on the matched origin — opening a tab somewhere else
    // would inject into a page with none of the user's session for that site.
    for (const target of [LEETCODE_TAB, NEETCODE_TAB]) {
      const host = new URL(target.fallbackUrl).hostname
      const pattern = target.match.replace('*://', '').replace('/*', '').replace('*.', '')
      expect(host.endsWith(pattern)).toBe(true)
      expect(target.label.length).toBeGreaterThan(0)
    }
  })
})

describe('acquireTab', () => {
  it("reuses a loaded tab and does NOT mark it ours to close", async () => {
    tabsQuery.mockResolvedValue([{ id: 42, status: 'complete' }])
    expect(await acquireTab(LEETCODE_TAB)).toEqual({ tabId: 42, opened: false })
    expect(tabsCreate).not.toHaveBeenCalled()
  })

  it('ignores a still-loading tab — injecting there lands before the document exists', async () => {
    tabsQuery.mockResolvedValue([{ id: 42, status: 'loading' }])
    tabsCreate.mockResolvedValue({ id: 99 })
    tabsGet.mockResolvedValue({ id: 99, status: 'complete' })

    expect(await acquireTab(LEETCODE_TAB)).toEqual({ tabId: 99, opened: true })
  })

  it('opens the tab in the background so the import never steals focus', async () => {
    tabsQuery.mockResolvedValue([])
    tabsCreate.mockResolvedValue({ id: 99 })
    tabsGet.mockResolvedValue({ id: 99, status: 'complete' })

    await acquireTab(LEETCODE_TAB)
    expect(tabsCreate).toHaveBeenCalledWith(expect.objectContaining({ active: false }))
  })

  it('waits for the opened tab to finish loading before reporting it usable', async () => {
    tabsQuery.mockResolvedValue([])
    tabsCreate.mockResolvedValue({ id: 99 })
    tabsGet
      .mockResolvedValueOnce({ id: 99, status: 'loading' })
      .mockResolvedValueOnce({ id: 99, status: 'complete' })

    expect(await acquireTab(LEETCODE_TAB)).toEqual({ tabId: 99, opened: true })
    expect(tabsGet).toHaveBeenCalledTimes(2)
  })
})

describe('acquireTab when the page never loads', () => {
  beforeEach(() => vi.useFakeTimers())
  afterEach(() => vi.useRealTimers())

  it('cleans up the tab it opened instead of stranding one the user never asked for', async () => {
    tabsQuery.mockResolvedValue([])
    tabsCreate.mockResolvedValue({ id: 99 })
    tabsGet.mockResolvedValue({ id: 99, status: 'loading' })
    tabsRemove.mockResolvedValue(undefined)

    const pending = acquireTab(LEETCODE_TAB)
    const assertion = expect(pending).rejects.toThrow(/did not finish loading/)
    await vi.advanceTimersByTimeAsync(25_000)
    await assertion

    expect(tabsRemove).toHaveBeenCalledWith(99)
  })
})

describe('releaseTab', () => {
  it("never closes the user's own tab", async () => {
    await releaseTab({ tabId: 42, opened: false })
    expect(tabsRemove).not.toHaveBeenCalled()
  })

  it('closes a tab this code opened', async () => {
    tabsRemove.mockResolvedValue(undefined)
    await releaseTab({ tabId: 99, opened: true })
    expect(tabsRemove).toHaveBeenCalledWith(99)
  })

  it('does not turn a successful import into a failure when the tab is already gone', async () => {
    tabsRemove.mockRejectedValue(new Error('No tab with id: 99'))
    await expect(releaseTab({ tabId: 99, opened: true })).resolves.toBeUndefined()
  })
})
