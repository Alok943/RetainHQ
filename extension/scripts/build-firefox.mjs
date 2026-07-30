// Firefox build step (IMPLEMENTATION-companion-firefox.md §4).
//
// @crxjs/vite-plugin is Chrome-oriented: confirmed by inspecting dist/manifest.json
// after adding `background.scripts` alongside `background.service_worker` in the
// source manifest — crxjs's own background handling only understands
// `service_worker` and silently drops the `scripts` key from its output entirely
// (the same class of silent-drop bug as D-043's dynamic content-script registration
// finding). So this reuses the Chrome build's bundled JS byte-for-byte — the JS
// itself doesn't differ between targets, only the manifest's `background` shape —
// and patches just that one key rather than running a second, separate bundle.
//
// `service-worker-loader.js` is a one-line ES module re-export
// (`import './assets/service_worker.ts-<hash>.js'`); Firefox's MV3
// `background.scripts` + `"type": "module"` supports that natively as an event
// page, so the same loader file works unmodified as a `scripts` entry.
import { cpSync, readFileSync, writeFileSync, existsSync, rmSync } from 'node:fs'
import { fileURLToPath, pathToFileURL } from 'node:url'
import { dirname, join } from 'node:path'

const extensionRoot = dirname(dirname(fileURLToPath(import.meta.url)))
const distDir = join(extensionRoot, 'dist')
const firefoxDir = join(extensionRoot, 'dist-firefox')

// `manifest.json`'s host_permissions carries 'http://localhost:8000/*'
// unconditionally — it's a static file, not built from VITE_API_BASE_URL, so
// every `npm run build` bakes it in regardless of target. That's correct for
// `dist/` (IMPLEMENTATION-companion-firefox.md documents it as a Chrome
// unpacked daily-driver the owner points at a local backend), but
// `dist-firefox/` is never that — it is only ever the self-host/AMO
// distribution artifact (REVIEWER-BUILD.md), so shipping a permission that
// grants a real-world install access to whatever a user happens to run on
// their own :8000 is a live-but-pointless risk on the one build that's
// actually handed to strangers. AMO review would flag it on the later listed
// submission regardless — cheaper to never ship it.
export const LOCALHOST_HOST_PERMISSION = 'http://localhost:8000/*'

/** Pure transform, unit-tested directly (build-firefox.test.mjs) without
 * touching the filesystem — the two prior crxjs-quirk patches below were
 * each discovered by inspecting build output by hand; this one has a test
 * instead so a manifest-shape change doesn't silently un-fix it. */
export function patchManifestForFirefox(manifest) {
  if (!manifest.background?.service_worker) {
    throw new Error('Expected background.service_worker in the built manifest — build shape changed, check this script.')
  }

  const patched = structuredClone(manifest)

  // @crxjs/vite-plugin is Chrome-oriented: confirmed by inspecting
  // dist/manifest.json after adding `background.scripts` alongside
  // `background.service_worker` in the source manifest — crxjs's own
  // background handling only understands `service_worker` and silently drops
  // the `scripts` key from its output entirely (the same class of
  // silent-drop bug as D-043's dynamic content-script registration finding).
  // So this reuses the Chrome build's bundled JS byte-for-byte — the JS
  // itself doesn't differ between targets, only the manifest's `background`
  // shape — and patches just that one key rather than running a second,
  // separate bundle.
  //
  // `service-worker-loader.js` is a one-line ES module re-export
  // (`import './assets/service_worker.ts-<hash>.js'`); Firefox's MV3
  // `background.scripts` + `"type": "module"` supports that natively as an
  // event page, so the same loader file works unmodified as a `scripts` entry.
  patched.background = {
    scripts: [manifest.background.service_worker],
    type: manifest.background.type,
  }

  // `use_dynamic_url` is another crxjs/Chrome-only key (obscures
  // web-accessible resource URLs behind a per-load random UUID) — Firefox's
  // MV3 web_accessible_resources has no such concept and logs "unexpected
  // property" for it. Harmless (Firefox just ignores the field and serves
  // the resources normally), but it's noise on every load; strip it same as
  // background above.
  patched.web_accessible_resources = (manifest.web_accessible_resources ?? []).map((entry) => {
    const { use_dynamic_url, ...rest } = entry
    return rest
  })

  patched.host_permissions = (manifest.host_permissions ?? []).filter(
    (p) => p !== LOCALHOST_HOST_PERMISSION
  )

  return patched
}

// process.argv[1] is a filesystem path ('C:\...' on Windows); import.meta.url
// is always a file:// URL ('file:///C:/...'). Comparing them as strings
// directly breaks on Windows (backslashes, drive-letter casing, percent
// escaping) and silently turns this whole block into a no-op — pathToFileURL
// normalizes both sides through the same encoding before comparing.
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  if (!existsSync(distDir)) {
    console.error('dist/ not found — run `npm run build` first.')
    process.exit(1)
  }

  if (existsSync(firefoxDir)) rmSync(firefoxDir, { recursive: true })
  cpSync(distDir, firefoxDir, { recursive: true })

  const manifestPath = join(firefoxDir, 'manifest.json')
  const manifest = JSON.parse(readFileSync(manifestPath, 'utf-8'))

  let patched
  try {
    patched = patchManifestForFirefox(manifest)
  } catch (err) {
    console.error(err.message)
    process.exit(1)
  }

  writeFileSync(manifestPath, JSON.stringify(patched, null, 2) + '\n')

  console.log(
    `Firefox build written to ${firefoxDir} (background.scripts: ${patched.background.scripts[0]}, ` +
    `host_permissions: ${patched.host_permissions.length} of ${manifest.host_permissions?.length ?? 0})`
  )
}
