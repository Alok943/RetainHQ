# Implementation Plan — Firefox Port of the Companion Extension

**For the implementer (Sonnet).** The extension is Chrome-MV3 today and passing (20 vitest tests,
clean `npm run build`). This ports it to Firefox as a **second build target from one source tree** —
not a fork. Owner uses Firefox primarily, so this is the daily-driver target, not an afterthought.

Baseline: 355 backend tests, 20 extension tests. Do not finish with fewer.

---

## 1. What actually differs (verified 2026-07-26, not from memory)

| Concern | Chrome | Firefox |
|---|---|---|
| Background | `background.service_worker` | **`background.scripts`** (event page). Firefox does not support service workers here. |
| Both at once | — | You may declare **both keys**; each browser reads its own. One manifest, no fork. |
| `optional_host_permissions` | supported | supported **from Firefox 128** — set `strict_min_version` accordingly |
| Add-on identity | not needed | **`browser_specific_settings.gecko.id`** required for signing |
| API namespace | `chrome.*` | `browser.*` (promises); `chrome.*` exists as a callback-compatible alias |

The consent design ports intact — `optional_host_permissions` + `permissions.request()` from a user
gesture works on both. That was the main risk and it is clear.

---

## 2. API namespace — do the cheap thing

All 20-odd call sites in `src/` use `chrome.*` and there is no `browser.*` usage. Firefox aliases
`chrome.*`, so most of it runs as-is. **Do not rewrite every call site.**

Two real gaps:
- `chrome.*` on Firefox is **callback-style**; `browser.*` returns promises. Any `await chrome.x()`
  in the code resolves to `undefined` on Firefox instead of throwing — a silent wrong-value bug,
  the worst kind. **Audit every `await chrome.` in `src/` first** and confirm behaviour.
- Add `webextension-polyfill` (or a 15-line local shim) exposing a promise-based `browser` and use
  it in the files that `await`. A shim is preferable to a dependency if the count is small.

Start by listing them:

```bash
grep -rn "await chrome\." extension/src/
```

Report the count in your writeup — it decides shim vs polyfill.

---

## 3. Manifest

Add alongside the existing keys (do not remove the Chrome ones):

```jsonc
{
  "background": {
    "service_worker": "src/background/service_worker.ts",  // Chrome
    "scripts": ["src/background/service_worker.ts"],       // Firefox
    "type": "module"
  },
  "browser_specific_settings": {
    "gecko": { "id": "companion@retainhq.app", "strict_min_version": "128.0" }
  }
}
```

`128.0` is not arbitrary — it is the floor for `optional_host_permissions`, which the consent flow
depends on. A lower floor silently breaks consent on older Firefox.

**Verify the service worker actually runs as an event page.** It uses `chrome.alarms` for the sync
tick, which is the right choice for a non-persistent background context on both browsers — but
confirm no top-level state is assumed to survive, because event pages unload.

---

## 4. Build — the likely sticking point

`vite.config.ts` uses `@crxjs/vite-plugin`, which is Chrome-oriented. Its Firefox support is
limited and version-dependent. **Verify before designing around it**, and expect to need a second
build output rather than one artifact.

Order of preference:
1. `@crxjs` emits a working Firefox build → one config, two outputs.
2. It does not → add a small post-build step producing `dist-firefox/` with the Firefox manifest,
   reusing the same bundled JS. `npm run build:firefox`.

Recall the D-043 lesson before assuming: `@crxjs` only bundles content scripts listed in the static
`content_scripts` array, and silently drops anything else from `dist/`. **After any build change,
verify every content script is actually present in the output** — the failure mode is a missing
file, not an error.

```bash
ls dist-firefox/assets/ | grep -E "llm_metadata|leetcode|youtube|coursera|pdf"
```

Validate the result with `web-ext lint`.

---

## 5. Auth

`chrome.identity.launchWebAuthFlow` and `getRedirectURL` exist on Firefox, but **the redirect URL
differs** — it is derived from the extension id, so the Chrome one will not work. Add the Firefox
redirect URL to the Supabase allowed-redirect list; log the resolved value on first run rather than
guessing it.

This is the most likely thing to break in real use and the least likely to be caught by tests.

---

## 6. Tests

- Existing 20 tests are logic-level and should pass unchanged — confirm.
- Add a manifest test: both `background` keys present, `gecko.id` set, `strict_min_version >= 128`.
- Add the `await chrome.` guard: a test that fails if a bare awaited `chrome.*` call reappears in
  `src/` after the shim lands. Cheap regex test, prevents silent-undefined regressions.

---

## 7. Build order

1. Audit `await chrome.` call sites; shim or polyfill.
2. Manifest keys + `gecko.id`.
3. Firefox build output; verify all content scripts present; `web-ext lint`.
4. Load in Firefox, sign in, confirm: auth completes, a YouTube session syncs, the consent screen
   grants an LLM origin, and capture starts only after.
5. Docs same commit: SYSTEM-OVERVIEW changelog, DECISIONS (`D-045` — two targets, one source tree),
   BACKLOG grooming.

**Do not push.**

## 8. Definition of done

- [ ] Both suites green; `npm run build` and the Firefox build both clean
- [ ] `web-ext lint` passes
- [ ] Loaded in Firefox: auth works, a real session syncs, consent grants an origin
- [ ] Every content script verified present in the Firefox output
- [ ] Chrome build unaffected — same source, no regression

## 9. Report back

1. How many `await chrome.` sites existed, and shim vs polyfill.
2. Whether `@crxjs` produced a usable Firefox build or a second step was needed.
3. The Firefox redirect URL, so it can be added to Supabase.
4. Anything above that turned out wrong — this doc's browser-difference table was checked against
   MDN on 2026-07-26 but the build tooling was not.

Sources checked: MDN `background` and `optional_permissions`; mozilla/web-ext#2532.
