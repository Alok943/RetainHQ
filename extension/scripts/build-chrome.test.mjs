import { describe, it, expect } from 'vitest'
import { patchManifestForChrome } from './build-chrome.mjs'
import { LOCALHOST_HOST_PERMISSION } from './build-firefox.mjs'

// Regression guard for the Chrome Web Store / Edge Add-ons artifact
// (dist-chrome/) — mirrors build-firefox.test.mjs for the same reason:
// dist/ is documented as a personal unpacked daily-driver that legitimately
// points at a local backend, and must never be the thing actually submitted.
describe('patchManifestForChrome', () => {
  const baseManifest = {
    background: { service_worker: 'assets/service_worker.js', type: 'module' },
    host_permissions: [
      '*://*.youtube.com/*',
      'https://retainhq.onrender.com/*',
      LOCALHOST_HOST_PERMISSION,
    ],
    browser_specific_settings: { gecko: { id: 'companion@retainhq.app' } },
  }

  it('strips the localhost host permission from the distribution artifact', () => {
    const patched = patchManifestForChrome(baseManifest)
    expect(patched.host_permissions).not.toContain(LOCALHOST_HOST_PERMISSION)
  })

  it('leaves every other host permission untouched', () => {
    const patched = patchManifestForChrome(baseManifest)
    expect(patched.host_permissions).toEqual([
      '*://*.youtube.com/*',
      'https://retainhq.onrender.com/*',
    ])
  })

  it('strips browser_specific_settings — Firefox-only, meaningless to either store', () => {
    const patched = patchManifestForChrome(baseManifest)
    expect(patched).not.toHaveProperty('browser_specific_settings')
  })

  it('leaves background.service_worker untouched — Chrome/Edge need it as-is, unlike Firefox', () => {
    const patched = patchManifestForChrome(baseManifest)
    expect(patched.background).toEqual({ service_worker: 'assets/service_worker.js', type: 'module' })
  })

  it('does not mutate the input manifest', () => {
    const before = JSON.stringify(baseManifest)
    patchManifestForChrome(baseManifest)
    expect(JSON.stringify(baseManifest)).toBe(before)
  })

  it('throws if the built manifest has no service_worker (build shape changed)', () => {
    expect(() => patchManifestForChrome({ background: {}, host_permissions: [] })).toThrow(
      /service_worker/
    )
  })

  it('is a no-op on host_permissions when localhost is already absent', () => {
    const clean = { ...baseManifest, host_permissions: ['*://*.youtube.com/*'] }
    const patched = patchManifestForChrome(clean)
    expect(patched.host_permissions).toEqual(['*://*.youtube.com/*'])
  })
})
