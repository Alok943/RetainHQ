import { resolve } from 'node:path'
import { defineConfig } from 'vite'
import { crx } from '@crxjs/vite-plugin'
import manifest from './manifest.json'

export default defineConfig({
  plugins: [crx({ manifest })],
  build: {
    rollupOptions: {
      // index.html (the popup) is picked up automatically via manifest.action.
      // studied.html (the "What I've studied" page, docs/SPEC-core-loop-v2.md
      // Phase 4) is opened at runtime via chrome.tabs.create + getURL, so it
      // isn't referenced anywhere in manifest.json for crx to auto-discover —
      // it needs to be listed as its own build input.
      input: {
        studied: resolve(__dirname, 'studied.html'),
      },
    },
  },
})
