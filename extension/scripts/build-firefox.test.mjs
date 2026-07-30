import { describe, it, expect } from 'vitest'
import { patchManifestForFirefox, LOCALHOST_HOST_PERMISSION } from './build-firefox.mjs'

// Regression guard for the AMO submission artifact (dist-firefox/). Unlike
// dist/ (documented as a personal Chrome daily-driver that legitimately
// points at a local backend), dist-firefox/ is only ever handed to Mozilla
// or self-host visitors — see the comment above LOCALHOST_HOST_PERMISSION.
describe('patchManifestForFirefox', () => {
  const baseManifest = {
    background: { service_worker: 'assets/service_worker.js', type: 'module' },
    host_permissions: [
      '*://*.youtube.com/*',
      'https://retainhq.onrender.com/*',
      LOCALHOST_HOST_PERMISSION,
    ],
    web_accessible_resources: [
      { resources: ['assets/thing.js'], matches: ['<all_urls>'], use_dynamic_url: true },
    ],
  }

  it('strips the localhost host permission from the distribution artifact', () => {
    const patched = patchManifestForFirefox(baseManifest)
    expect(patched.host_permissions).not.toContain(LOCALHOST_HOST_PERMISSION)
  })

  it('leaves every other host permission untouched', () => {
    const patched = patchManifestForFirefox(baseManifest)
    expect(patched.host_permissions).toEqual([
      '*://*.youtube.com/*',
      'https://retainhq.onrender.com/*',
    ])
  })

  it('rewrites background.service_worker to background.scripts', () => {
    const patched = patchManifestForFirefox(baseManifest)
    expect(patched.background).toEqual({ scripts: ['assets/service_worker.js'], type: 'module' })
  })

  it('strips use_dynamic_url from web_accessible_resources entries', () => {
    const patched = patchManifestForFirefox(baseManifest)
    expect(patched.web_accessible_resources[0]).not.toHaveProperty('use_dynamic_url')
    expect(patched.web_accessible_resources[0].resources).toEqual(['assets/thing.js'])
  })

  it('does not mutate the input manifest', () => {
    const before = JSON.stringify(baseManifest)
    patchManifestForFirefox(baseManifest)
    expect(JSON.stringify(baseManifest)).toBe(before)
  })

  it('throws if the built manifest has no service_worker (build shape changed)', () => {
    expect(() => patchManifestForFirefox({ background: {}, host_permissions: [] })).toThrow(
      /service_worker/
    )
  })

  it('is a no-op on host_permissions when localhost is already absent', () => {
    const clean = { ...baseManifest, host_permissions: ['*://*.youtube.com/*'] }
    const patched = patchManifestForFirefox(clean)
    expect(patched.host_permissions).toEqual(['*://*.youtube.com/*'])
  })
})
