// Chrome / Edge build step. Both are Chromium MV3 and accept the identical
// package (Edge's own docs say so explicitly) — one artifact, two stores.
//
// Unlike Firefox, nothing about manifest SHAPE needs to change: crxjs's own
// output already targets Chromium (`background.service_worker`, no `scripts`
// key — see build-firefox.mjs's comment on the same quirk from the other
// side). What this script does is what build-firefox.mjs does for the SAME
// reason: strip the localhost dev permission so a `dist/` meant as a personal
// unpacked daily-driver (REVIEWER-BUILD.md) doesn't get zipped up and handed
// to the Chrome Web Store or Edge Add-ons review teams as-is.
import { cpSync, readFileSync, writeFileSync, existsSync, rmSync } from 'node:fs'
import { fileURLToPath, pathToFileURL } from 'node:url'
import { dirname, join } from 'node:path'
import { LOCALHOST_HOST_PERMISSION, VITE_METADATA_DIR } from './build-firefox.mjs'

const extensionRoot = dirname(dirname(fileURLToPath(import.meta.url)))
const distDir = join(extensionRoot, 'dist')
const chromeDir = join(extensionRoot, 'dist-chrome')

/** Pure transform, unit-tested directly (build-chrome.test.mjs) without
 * touching the filesystem. */
export function patchManifestForChrome(manifest) {
  if (!manifest.background?.service_worker) {
    throw new Error('Expected background.service_worker in the built manifest — build shape changed, check this script.')
  }

  const patched = structuredClone(manifest)

  patched.host_permissions = (manifest.host_permissions ?? []).filter(
    (p) => p !== LOCALHOST_HOST_PERMISSION
  )

  // `browser_specific_settings.gecko` is Mozilla's own key — Chrome/Edge
  // ignore unrecognized top-level manifest keys rather than erroring on them,
  // but a store listing has no reason to carry Firefox add-on ID/version-floor
  // metadata that means nothing to either reviewer.
  delete patched.browser_specific_settings

  return patched
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  if (!existsSync(distDir)) {
    console.error('dist/ not found — run `npm run build` first.')
    process.exit(1)
  }

  if (existsSync(chromeDir)) rmSync(chromeDir, { recursive: true })
  cpSync(distDir, chromeDir, { recursive: true })

  // Vite's own build metadata — unread at runtime, and a stray dot-directory
  // in a store package is noise at best. See VITE_METADATA_DIR in
  // build-firefox.mjs for the AMO rejection that surfaced it.
  const viteMetaDir = join(chromeDir, VITE_METADATA_DIR)
  if (existsSync(viteMetaDir)) rmSync(viteMetaDir, { recursive: true })

  const manifestPath = join(chromeDir, 'manifest.json')
  const manifest = JSON.parse(readFileSync(manifestPath, 'utf-8'))

  let patched
  try {
    patched = patchManifestForChrome(manifest)
  } catch (err) {
    console.error(err.message)
    process.exit(1)
  }

  writeFileSync(manifestPath, JSON.stringify(patched, null, 2) + '\n')

  console.log(
    `Chrome/Edge build written to ${chromeDir} (host_permissions: ${patched.host_permissions.length} of ${manifest.host_permissions?.length ?? 0})`
  )
}
