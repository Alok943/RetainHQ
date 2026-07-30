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
2. `npm run build:firefox` runs two steps back to back:
   - `npm run build` → `tsc` (typecheck) then `vite build` (via `@crxjs/vite-plugin`),
     producing `dist/` — a standard Chrome-shape MV3 build.
   - `node scripts/build-firefox.mjs` → copies `dist/` to `dist-firefox/` and rewrites
     `dist-firefox/manifest.json`: the `background` key changes from
     `{ service_worker: "..." }` to `{ scripts: ["..."], type: "module" }` (the
     background JS itself is untouched — Firefox loads the same bundled file as an
     event page instead of a service worker), and `http://localhost:8000/*` is
     removed from `host_permissions` (a dev-only permission with no purpose in a
     distributed build). See the comments at the top of `scripts/build-firefox.mjs`
     for both.

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
