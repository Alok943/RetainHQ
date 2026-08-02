// Cross-browser Promise wrappers for the handful of WebExtension calls this
// codebase `await`s (IMPLEMENTATION-companion-firefox.md §2).
//
// Chrome's `chrome.*` API resolves these as native promises when no callback
// is passed — already relied on throughout this codebase. Firefox's `chrome.*`
// is a callback-only compat alias: the SAME call, awaited with no callback,
// silently resolves to `undefined` instead of the real value or a thrown
// error — a silent-wrong-value bug, not a crash (confirmed against MDN
// `background`/`optional_permissions`, checked 2026-07-26). Firefox's native
// `browser.*` global IS promise-based and exists only on Firefox, so `typeof
// browser` picks the right one on either engine without a build-time branch.
declare const browser: typeof chrome | undefined

// Resolved per-call, not once at module load: vitest's `chrome` mock is
// (re)stubbed per-test via `vi.stubGlobal` in `beforeEach`, which runs after
// this module is first imported — a module-scope constant would capture
// whatever (or nothing) was global at import time and never see it.
function getApi(): typeof chrome {
  return typeof browser !== 'undefined' ? browser : chrome
}

export const storageLocalGet = (keys: string | string[]): Promise<Record<string, unknown>> =>
  getApi().storage.local.get(keys)

export const storageLocalSet = (items: Record<string, unknown>): Promise<void> =>
  getApi().storage.local.set(items)

export const permissionsRequest = (permissions: chrome.permissions.Permissions): Promise<boolean> =>
  getApi().permissions.request(permissions)

export const permissionsRemove = (permissions: chrome.permissions.Permissions): Promise<boolean> =>
  getApi().permissions.remove(permissions)

export const permissionsContains = (permissions: chrome.permissions.Permissions): Promise<boolean> =>
  getApi().permissions.contains(permissions)

export const runtimeSendMessage = <T = unknown>(message: unknown): Promise<T> =>
  getApi().runtime.sendMessage(message)

// Tabs + scripting go through getApi() for the exact reason documented at the
// top of this file, and it bites HARDER here than anywhere else: every call
// below is awaited FOR ITS RETURN VALUE. Elsewhere in this codebase
// `chrome.tabs.*` is called fire-and-forget, where Firefox's callback-only
// alias resolving to `undefined` is harmless. `await chrome.tabs.query(...)`
// on Firefox would resolve to `undefined` and the import would report "open a
// LeetCode tab" with one sitting right there.
export const tabsQuery = (query: chrome.tabs.QueryInfo): Promise<chrome.tabs.Tab[]> =>
  getApi().tabs.query(query)

export const tabsCreate = (props: chrome.tabs.CreateProperties): Promise<chrome.tabs.Tab> =>
  getApi().tabs.create(props)

export const tabsGet = (tabId: number): Promise<chrome.tabs.Tab> =>
  getApi().tabs.get(tabId)

export const tabsRemove = (tabId: number): Promise<void> =>
  getApi().tabs.remove(tabId)

export const scriptingExecuteScript = <Args extends unknown[], Result>(
  injection: chrome.scripting.ScriptInjection<Args, Result>,
): Promise<chrome.scripting.InjectionResult<chrome.scripting.Awaited<Result>>[]> =>
  getApi().scripting.executeScript(injection)

/**
 * Firefox implements `identity.launchWebAuthFlow` as PROMISE-ONLY. Passing a
 * callback there does not throw — the callback is simply never invoked, so the
 * OAuth window opens, the user picks an account, and then nothing happens at
 * all. That was the symptom on Firefox 2026-07-26.
 *
 * The `await chrome.` guard test cannot catch this: the broken form was a
 * callback, not an await. Route every identity call through here.
 */
export const launchWebAuthFlow = (details: { url: string; interactive: boolean }): Promise<string> =>
  getApi().identity.launchWebAuthFlow(details) as unknown as Promise<string>

export const getRedirectURL = (): string => getApi().identity.getRedirectURL()
