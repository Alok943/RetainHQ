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
