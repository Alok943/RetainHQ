import { describe, it, expect, beforeEach, vi } from 'vitest'
import { getConsentTier, switchConsentTier, hasLlmOriginPermission, LLM_ORIGINS } from './consent'
import { CONSENT_COPY_VERSION } from './consent'

// chrome.* isn't available under vitest's Node environment — a minimal mock
// standing in for chrome.storage.local and chrome.permissions, backed by
// plain in-memory state so assertions can inspect the resulting state
// directly rather than only the mock call history.
let storage: Record<string, unknown>
let grantedOrigins: Set<string>

beforeEach(() => {
  storage = {}
  grantedOrigins = new Set()

  const chromeMock = {
    storage: {
      local: {
        get: vi.fn(async (keys: string[]) => {
          const out: Record<string, unknown> = {}
          for (const k of keys) if (k in storage) out[k] = storage[k]
          return out
        }),
        set: vi.fn(async (items: Record<string, unknown>) => {
          Object.assign(storage, items)
        }),
      },
    },
    permissions: {
      request: vi.fn(async ({ origins }: { origins: string[] }) => {
        origins.forEach((o) => grantedOrigins.add(o))
        return true
      }),
      remove: vi.fn(async ({ origins }: { origins: string[] }) => {
        origins.forEach((o) => grantedOrigins.delete(o))
        return true
      }),
      contains: vi.fn(async ({ origins }: { origins: string[] }) => origins.every((o) => grantedOrigins.has(o))),
    },
  }

  vi.stubGlobal('chrome', chromeMock)
})

describe('consentTier === null (unasked)', () => {
  it('is the default — never defaulted to a real tier', async () => {
    expect(await getConsentTier()).toBeNull()
  })

  it('holds no LLM-origin permission until a tier is chosen', async () => {
    expect(await hasLlmOriginPermission()).toBe(false)
  })
})

describe('switchConsentTier', () => {
  it('choosing titles requests no origins at all', async () => {
    const result = await switchConsentTier('titles', null)
    expect(result).toBe('titles')
    expect(chrome.permissions.request).not.toHaveBeenCalled()
    expect(await getConsentTier()).toBe('titles')
    expect(await hasLlmOriginPermission()).toBe(false)
  })

  it('choosing cloud requests the LLM origins and grants them', async () => {
    const result = await switchConsentTier('cloud', null)
    expect(result).toBe('cloud')
    expect(chrome.permissions.request).toHaveBeenCalledWith({ origins: LLM_ORIGINS })
    expect(await getConsentTier()).toBe('cloud')
    expect(await hasLlmOriginPermission()).toBe(true)
  })

  it('a denied permission prompt persists titles, not the requested tier', async () => {
    (chrome.permissions.request as ReturnType<typeof vi.fn>).mockResolvedValueOnce(false)
    const result = await switchConsentTier('cloud', null)
    expect(result).toBe('titles')
    expect(await getConsentTier()).toBe('titles')
    expect(await hasLlmOriginPermission()).toBe(false)
  })

  it('downgrading from cloud to titles removes the granted permission', async () => {
    await switchConsentTier('cloud', null)
    expect(await hasLlmOriginPermission()).toBe(true)

    const result = await switchConsentTier('titles', 'cloud')
    expect(result).toBe('titles')
    expect(chrome.permissions.remove).toHaveBeenCalledWith({ origins: LLM_ORIGINS })
    expect(await hasLlmOriginPermission()).toBe(false)
  })

  it('calls permissions.request() before any other permissions/storage call — the gesture-preserving order', async () => {
    // Regression for: "permissions.request may only be called from a user
    // input handler" (Firefox, observed 2026-07-30). Awaiting ANYTHING before
    // request() — even a fast, non-gesture-sensitive call like
    // permissions.contains() — already spends the click's gesture context by
    // the time request() runs, so the prompt silently fails. jsdom can't
    // observe real gesture state, but call ORDER is the directly-checkable
    // proxy: request() must be the first mocked call, full stop, whenever the
    // tier needs origins.
    const callOrder: string[] = []
    ;(chrome.permissions.request as ReturnType<typeof vi.fn>).mockImplementationOnce(async ({ origins }) => {
      callOrder.push('request')
      origins.forEach((o: string) => grantedOrigins.add(o))
      return true
    })
    ;(chrome.permissions.contains as ReturnType<typeof vi.fn>).mockImplementation(async ({ origins }) => {
      callOrder.push('contains')
      return origins.every((o: string) => grantedOrigins.has(o))
    })
    ;(chrome.storage.local.set as ReturnType<typeof vi.fn>).mockImplementation(async (items) => {
      callOrder.push('storage.set')
      Object.assign(storage, items)
    })

    await switchConsentTier('cloud', null)

    expect(callOrder[0]).toBe('request')
    expect(callOrder).not.toEqual([]) // sanity: the mocks above actually fired
  })

  it('revokes a dangling origin grant even when the caller passes a stale/wrong currentTier', async () => {
    // Simulates the copy-version re-prompt case: the browser still holds the
    // grant from an earlier choice, but the caller's cached tier value can't
    // be trusted to reflect that — switchConsentTier must check the real
    // permission state itself, not the argument.
    await switchConsentTier('cloud', null)
    expect(await hasLlmOriginPermission()).toBe(true)

    const result = await switchConsentTier('titles', null) // null, not 'cloud'
    expect(result).toBe('titles')
    expect(chrome.permissions.remove).toHaveBeenCalledWith({ origins: LLM_ORIGINS })
    expect(await hasLlmOriginPermission()).toBe(false)
  })
})

describe('consent copy versioning', () => {
  it('a tier chosen under a stale copy version reads back as unset', async () => {
    await switchConsentTier('cloud', null)
    expect(await getConsentTier()).toBe('cloud')

    // Simulate a v1 install: the tier key exists but predates the
    // copy-version key entirely.
    delete storage.consentCopyVersion
    expect(await getConsentTier()).toBeNull()
  })

  it('a tier chosen under the current copy version reads back normally', async () => {
    await switchConsentTier('titles', null)
    expect(storage.consentCopyVersion).toBe(CONSENT_COPY_VERSION)
    expect(await getConsentTier()).toBe('titles')
  })
})
