import { describe, it, expect } from 'vitest'

// `await chrome.foo()` resolves to `undefined` on Firefox instead of throwing
// or returning the real value — Firefox's `chrome.*` alias is callback-only,
// unlike Chrome's, which is promise-native (IMPLEMENTATION-companion-firefox.md
// §2). browser_api.ts is the one place allowed to reference `chrome` directly;
// everywhere else should go through its wrappers. This fails loudly if that
// pattern regresses instead of shipping a silent wrong-value bug.
//
// Uses import.meta.glob (not Node's `fs`) so this stays typeable under the
// project's browser-extension tsconfig, which deliberately has no "node" lib.
const files = import.meta.glob('./**/*.ts', { eager: true, query: '?raw', import: 'default' }) as Record<string, string>

describe('no bare `await chrome.` call sites outside browser_api.ts', () => {
  it('stays clean', () => {
    const offenders = Object.entries(files)
      .filter(([path]) => !path.endsWith('browser_api.ts') && !path.endsWith('.test.ts'))
      .filter(([, content]) => /await chrome\./.test(content))
      .map(([path]) => path)

    expect(offenders).toEqual([])
  })
})

// The original guard only caught `await chrome.*`. It could not catch the bug
// that actually broke Firefox sign-in on 2026-07-26: a CALLBACK passed to
// chrome.identity.launchWebAuthFlow. Firefox implements that API as
// promise-only — the callback is accepted and never invoked, so the OAuth
// window opens, the user picks an account, and nothing happens at all. No
// error, no session, nothing in the console.
//
// Same import.meta.glob approach as above, and for the same reason: this
// tsconfig has no "node" lib, so Node's fs would break `tsc` (it did).
describe('no direct chrome.identity.* outside browser_api.ts', () => {
  it('stays clean', () => {
    const offenders = Object.entries(files)
      .filter(([path]) => !path.endsWith('browser_api.ts') && !path.endsWith('.test.ts'))
      .filter(([, content]) => /chrome\.identity\./.test(content))
      .map(([path]) => path)

    expect(offenders).toEqual([])
  })
})
