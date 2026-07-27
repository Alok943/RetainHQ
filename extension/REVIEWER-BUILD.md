# Build reproduction instructions (AMO source-code review)

This extension is bundled (Vite/Rollup), so AMO requires the source archive submitted
alongside it to reproduce `dist-firefox/` byte-for-byte. This directory (`extension/`,
excluding `node_modules/`, `dist/`, `dist-firefox/`) is that source.

## Environment

- Node: **v22.18.0** (any current Node 22.x LTS reproduces the same output)
- npm: 11.12.1
- OS: build is platform-independent (no native addons in the dependency tree)

## Steps

```
npm ci
npm run build:firefox
```

Output: `dist-firefox/` — this is what was submitted to AMO.

## What each step does

1. `npm ci` — installs exact dependency versions from `package-lock.json`.
2. `npm run build:firefox` runs two steps back to back:
   - `npm run build` → `tsc` (typecheck) then `vite build` (via `@crxjs/vite-plugin`),
     producing `dist/` — a standard Chrome-shape MV3 build.
   - `node scripts/build-firefox.mjs` → copies `dist/` to `dist-firefox/` and rewrites
     only the `background` key in `dist-firefox/manifest.json` from
     `{ service_worker: "..." }` to `{ scripts: ["..."], type: "module" }`. The
     background JS itself is untouched — Firefox loads the same bundled file as an
     event page instead of a service worker. See the comment at the top of
     `scripts/build-firefox.mjs` for why this key is patched post-build rather than
     built twice.

No obfuscation is used anywhere in the build. `vite build`'s default minification
(esbuild) only shortens identifiers and strips whitespace/comments — it does not
alter control flow or encode logic, which is the allowed "minified" case, not the
banned "obfuscated" one.
