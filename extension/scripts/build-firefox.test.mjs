import { describe, it, expect } from 'vitest'
import { existsSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { patchManifestForFirefox, LOCALHOST_HOST_PERMISSION, VITE_METADATA_DIR } from './build-firefox.mjs'

// AMO rejected a 1.2.3 upload outright with:
//   Invalid file name in archive: .vite/manifest.json
// Mozilla's validator refuses hidden dot-entries in a submitted package, and
// Vite drops its build manifest there on every build. Both distribution
// scripts now delete it; this asserts they actually did, on whichever build
// output happens to exist locally. Skips (rather than fails) when neither has
// been built, so `npm test` on a clean checkout stays green.
describe('distribution artifacts carry no hidden dot-entries', () => {
  const root = dirname(dirname(fileURLToPath(import.meta.url)))

  for (const target of ['dist-firefox', 'dist-chrome']) {
    it(`${target}/ has no ${VITE_METADATA_DIR}/ (AMO rejects the archive over it)`, () => {
      const outDir = join(root, target)
      if (!existsSync(outDir)) return // not built in this environment
      expect(existsSync(join(outDir, VITE_METADATA_DIR))).toBe(false)
    })
  }
})

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
