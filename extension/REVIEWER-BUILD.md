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

1. `npm ci` — installs exact dependency versions from `package-lock.json`, then runs
   the `postinstall` script (`patch-package`), which applies
   `patches/@supabase+supabase-js+2.110.7.patch`. That patch changes exactly one line
   in the installed copy of `@supabase/supabase-js` — see "Third-party patch" below.
2. `npm run build:firefox` runs three steps back to back:
   - `tsc` — typecheck only, emits nothing.
   - `vite build --mode firefox` (via `@crxjs/vite-plugin`), producing `dist/` — a
     standard Chrome-shape MV3 build. The `--mode firefox` flag makes Vite load
     `.env.firefox` (checked in, alongside this file) on top of any `.env`, pinning
     `VITE_API_BASE_URL` to `https://retainhq.onrender.com`. That file exists so the
     distributed build cannot inherit a developer's local `.env` — without it, a
     machine with `VITE_API_BASE_URL=http://localhost:8000` would silently produce a
     "distribution" build pointing every request at the builder's own machine. There
     is no `.env` in this source archive, so the pin is the only value in play and the
     output is deterministic.
   - `node scripts/build-firefox.mjs` → copies `dist/` to `dist-firefox/` and rewrites
     `dist-firefox/manifest.json`: the `background` key changes from
     `{ service_worker: "..." }` to `{ scripts: ["..."], type: "module" }` (the
     background JS itself is untouched — Firefox loads the same bundled file as an
     event page instead of a service worker), `http://localhost:8000/*` is
     removed from `host_permissions` (a dev-only permission with no purpose in a
     distributed build), and `use_dynamic_url` is stripped from
     `web_accessible_resources` (a Chrome-only key Firefox logs a warning for). See
     the comments at the top of `scripts/build-firefox.mjs` for each.

`npm run build:chrome` exists alongside it for the Chrome Web Store / Edge Add-ons
build (`dist-chrome/`, via `.env.chrome` and `scripts/build-chrome.mjs`). It is not
part of the Firefox submission and can be ignored for this review; it is mentioned
only so its presence in the archive is not surprising. Note that it also writes
`dist/` as a byproduct, so run `npm run build:firefox` last (or on a clean tree) when
reproducing the submitted artifact.

No obfuscation is used anywhere in the build. `vite build`'s default minification
(esbuild) only shortens identifiers and strips whitespace/comments — it does not
alter control flow or encode logic, which is the allowed "minified" case, not the
banned "obfuscated" one.

## Third-party patch: `@supabase/supabase-js`

`@supabase/supabase-js@2.110.7` ships (in its own `dist/index.mjs`, not our code) an
optional OpenTelemetry instrumentation hook:

```js
import(/* @vite-ignore */ OTEL_PKG)   // OTEL_PKG = "@opentelemetry/api", a variable
```

`@opentelemetry/api` is never installed (not a dependency of this extension), so the
call always fails and is caught (`.catch(() => null)`) — dead code at runtime, and the
specifier is a hardcoded package name, never user- or attacker-influenced. Static
analysis still flags a dynamic `import()` whose argument isn't a literal at the call
site, since it can't see that `OTEL_PKG`'s only possible value is that same literal.

The patch changes nothing about behavior — it inlines the literal directly:
`import(/* @vite-ignore */ "@opentelemetry/api")`. Applied automatically via
`patch-package`'s `postinstall` hook, so `npm ci` reproduces the patched build exactly.
Full diff: `patches/@supabase+supabase-js+2.110.7.patch`.
