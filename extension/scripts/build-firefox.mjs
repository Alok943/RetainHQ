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
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const extensionRoot = dirname(dirname(fileURLToPath(import.meta.url)))
const distDir = join(extensionRoot, 'dist')
const firefoxDir = join(extensionRoot, 'dist-firefox')

if (!existsSync(distDir)) {
  console.error('dist/ not found — run `npm run build` first.')
  process.exit(1)
}

if (existsSync(firefoxDir)) rmSync(firefoxDir, { recursive: true })
cpSync(distDir, firefoxDir, { recursive: true })

const manifestPath = join(firefoxDir, 'manifest.json')
const manifest = JSON.parse(readFileSync(manifestPath, 'utf-8'))

if (!manifest.background?.service_worker) {
  console.error('Expected background.service_worker in the built manifest — build shape changed, check this script.')
  process.exit(1)
}

manifest.background = {
  scripts: [manifest.background.service_worker],
  type: manifest.background.type,
}

writeFileSync(manifestPath, JSON.stringify(manifest, null, 2) + '\n')

console.log(`Firefox build written to ${firefoxDir} (background.scripts: ${manifest.background.scripts[0]})`)
