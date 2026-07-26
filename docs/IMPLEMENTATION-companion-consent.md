# Implementation Plan — Companion Consent, Tiers & Store Readiness

**For the implementer (Sonnet).** `IMPLEMENTATION-career-coach-phase3.md` §0 (async DB,
`SupabaseUser`, IDOR, Pydantic v2, naive-UTC, no push) applies unchanged — read it first.

**`SPEC-companion-phase1.md` §6 is the authority on what the tiers are, what the defaults are,
and what the consent screen says.** It is already decided, including the exact copy. **Do not
redesign it.** This doc is the *how*: manifest, storage, enforcement, tests.

This is the last blocker between the extension and a Chrome Web Store submission. Everything else
(adapters, stitcher, auth, queue, LeetCode probe + reflection) is built and passing —
12 vitest tests, 10 backend companion tests, and `npm run build` is clean.

Baseline: **340 backend tests passing.** Do not finish with fewer.

---

## 1. What §6 already decided — do not re-derive

| Data class | Default | Consent needed |
|---|---|---|
| **Metadata** — titles, domains, filenames, timestamps, durations | **Cloud (Flash-Lite), ON by default.** No choice screen. | No. Covered by the feature's own opt-in + privacy policy. |
| **Chat content** — LLM conversation text | **OFF.** | Yes — one-time choice screen, three real options. |

Three tiers for chat content: `cloud` (Recommended) · `nano` (on-device) · `titles` (minimal).
Copy is written verbatim in §6 — **use it as written**; every claim in it has to stay literally
true. Two conditions on that:

- The "never used to train models" line **requires the paid Gemini API tier**. Verify Google's
  current data-use terms at implementation time. If the project is on a free tier where that claim
  is not true, **the copy must change, not the tier** — say so in your report rather than shipping
  a false statement.
- Declining must be one equally-sized tap, and the setting symmetric to change afterwards.

**Consent artifact:** `metric_events`, `event_type='companion_consent'`, payload carrying the tier
and a timestamp. No new table.

**Hard legal boundary:** the extension **refuses to activate for `audience='school'` accounts**.
Classes 6–12 are minors and DPDP requires verifiable parental consent. This is not a product
toggle — it must be enforced server-side, not only in the extension, because the extension is
client code a user can modify.

---

## 2. [DECISION] Make the LLM hosts optional permissions — and the consent screen moves

> **Correction, 2026-07-26 (see D-043):** the mechanism below (`chrome.scripting.registerContentScripts`
> after the grant, LLM entry removed from static `content_scripts`) does not work with this repo's
> build tooling — `@crxjs/vite-plugin` only bundles content scripts it finds in the manifest's static
> `content_scripts` array; a script referenced solely from a `registerContentScripts()` call is
> silently dropped from `dist/` entirely (confirmed by building it and finding `llm_metadata.ts`
> absent). **Shipped instead:** `llm_metadata.ts` stays a static `content_scripts` entry, and only its
> three origins moved to `optional_host_permissions`. Chrome gates injection on the runtime grant
> either way — a static entry whose origin isn't currently held simply doesn't run, and starts running
> once `chrome.permissions.request()` succeeds (a documented Chrome behavior, same "reload to pick up
> a fresh grant" caveat as host permissions generally). Same enforcement guarantee, no `scripting`
> permission needed, and the file actually ships. The *goal* of this section (host permissions
> requested from a user gesture on the popup, not held at install) is unchanged and implemented as
> written below — only the injection mechanism differs from the original prose.

**This deviates from §6 and needs the owner's sign-off before you write code** (repo rule: spec
edit before code). Implement it as described; flag it in your report.

§6 puts the choice screen "on first visit to an LLM surface after install — not at install, when
the benefit is still abstract." That timing is right, but it assumes `chatgpt.com`, `claude.ai`
and `gemini.google.com` sit in **required** `host_permissions`, as they do today. Two costs:

1. Every user grants AI-chat-site access at install, before consenting to anything — the exact
   posture §6's whole design is trying to avoid.
2. It is the single largest Web Store review risk. Reviewers read required host permissions on
   AI-chat domains adversarially, and rightly.

Moving them to `optional_host_permissions` and requesting them from the consent screen makes the
no-persistence invariant **enforced by Chrome** rather than merely true because of how
`llm_metadata.ts` is written: with no grant, the content script cannot inject on those origins at
all. That is a stronger guarantee than any test can give.

**The cost, stated honestly:** you can no longer detect "first visit to an LLM surface" — that
detection needs either the host permission or `tabs` (which §3 removes). So the choice screen
moves into the **popup**, surfaced prominently on first open after any tracked activity, with a
badge to draw attention. Less contextual than §6 wanted. The benefit — browser-enforced consent
plus a far cleaner review — is worth it.

`chrome.permissions.request()` **must be called from a user gesture**, so it has to be the click
handler on the tier button. It cannot be called from the service worker.

---

## 3. Manifest changes

```jsonc
{
  "icons": { "16": "icons/16.png", "32": "icons/32.png",
             "48": "icons/48.png", "128": "icons/128.png" },   // MISSING today — hard blocker
  "permissions": ["storage", "identity", "alarms"],            // "tabs" REMOVED
  "host_permissions": [
    "*://*.youtube.com/*", "*://*.leetcode.com/*", "*://*.coursera.org/*",
    "https://retainhq.onrender.com/*", "http://localhost:8000/*"
  ],
  "optional_host_permissions": [
    "*://*.chatgpt.com/*", "*://claude.ai/*", "*://gemini.google.com/*"
  ]
}
```

- **Icons are missing entirely** and `public/` holds only SVG. Chrome requires **PNG**; SVG is not
  valid for the `icons` key and the store needs a 128×128. Raster from `public/icons.svg`.
- **`tabs` is declared and never used.** Verified: every call in `src/` is `chrome.storage`,
  `chrome.alarms` or `chrome.identity`; there is not one `chrome.tabs.*`. It grants URL and title
  access to all tabs and is a routine rejection trigger. Drop it.
- The LLM content script entry must move to dynamic registration
  (`chrome.scripting.registerContentScripts`) after the grant, since a static `content_scripts`
  entry for an origin you may not hold is invalid.
- Reword `description`: "tracking" reads adversarially in review. State the single purpose —
  *tracks your study activity so RetainHQ can schedule reviews.*

---

## 4. Backend

### 4.1 Allowlist the consent event
`app/schemas/metrics.py` currently has `CLIENT_EVENT_TYPES = {"review_depth_chosen"}`. Add
`"companion_consent"`. Without this the extension's POST is rejected by the validator — the
consent record silently never lands, which is the worst possible failure for this feature.

Payload shape (keep it inside `MAX_PAYLOAD_BYTES = 2048`):

```json
{ "tier": "cloud" | "nano" | "titles", "copy_version": "v1", "surface": "popup" }
```

`created_at` on the row is the timestamp — do not accept a client-supplied one.

### 4.2 Enforce the school-audience refusal server-side
In `POST /api/companion/sessions`, look up `user_prefs.audience`; if it is `school`, return
**403** and write nothing. The extension should also refuse client-side, but the extension is code
the user controls — the server is where a legal boundary actually holds.

### 4.3 Tier is server-authoritative for content classification
Store the latest consent tier per user (derive it from the newest `companion_consent`
`metric_event` — no new column). `classify_session` must **refuse to process any content-bearing
field unless the stored tier is `cloud`**. Today no content field exists, which is the point of
§6's invariant (a) — so this is a guard for the phase-6 feature that will add one, and it must be
written now, while the invariant is still true and easy to keep.

---

## 5. Extension

### 5.1 Consent state
`chrome.storage.local` key `consentTier`: `null` (unasked) | `'cloud'` | `'nano'` | `'titles'`.
`null` means **no LLM-surface capture of any kind**. Never default it to a value.

### 5.2 The choice screen
Rendered in the popup when `consentTier === null`. Copy verbatim from §6. Each of the three
buttons:

1. `chrome.permissions.request({origins: [...]})` — only for `cloud` and `nano`; `titles` needs no
   origin grant at all, which is itself a truthful selling point of that option.
2. On grant: persist the tier, `POST /api/metrics/events` with the consent record, and
   `chrome.scripting.registerContentScripts` for the LLM origins.
3. On denial: fall back to `titles` and record *that* as the consent tier. A denied permission
   prompt is still a choice and must be logged as one.

A settings row in the popup lets the user change tier later, symmetric in both directions —
switching down must call `chrome.permissions.remove()` and unregister the scripts, not merely flip
a flag.

### 5.3 The no-persistence invariant
§6 names four enforcement points. Keep all four true, and make the testable ones tested:

- **(a)** The segment type carries no content field — so nothing content-shaped can reach the sync
  queue by construction. Verify `src/types.ts` still has no such field, and add a test that fails
  if one appears.
- **(b)** `POST /api/companion/sessions`' Pydantic schema rejects unknown fields. Confirm
  `model_config = ConfigDict(extra='forbid')`; **add it if missing** and test that a request with
  a `content` field 422s.
- **(c)** Scrub classifier breadcrumbs from error reporting in the extension.
- **(d)** `payload.title_sample` stays capped and titles-only.

---

## 6. Tests

Extension (vitest):
- `consentTier === null` ⇒ no LLM-origin script registration, no capture
- choosing `titles` requests **no** origins
- a denied permission prompt persists `titles`, not the requested tier
- downgrading calls `permissions.remove()` and unregisters scripts

Backend (pytest, `tests/api/routes/test_companion.py` + `test_metrics.py`):
- `companion_consent` is accepted by the allowlist; an unknown type still 422s
- a session POST carrying a `content` field is **rejected**, not silently stripped
- `audience='school'` ⇒ 403 from `/api/companion/sessions`, and nothing written
- consent record lands with the tier in its payload and a server-set timestamp
- IDOR: user B cannot read or overwrite user A's consent record

---

## 7. Build order

1. Manifest: PNG icons, drop `tabs`, move LLM origins to `optional_host_permissions`, reword
   `description`. `npm run build` must stay clean.
2. Backend: allowlist entry, school refusal, `extra='forbid'` check, tier guard + tests.
3. Extension: consent state, choice screen, dynamic script registration, settings row + tests.
4. Verify the invariant end-to-end: install fresh, confirm **no** LLM-origin access before
   choosing, then confirm capture starts only after.
5. Docs same commit: SYSTEM-OVERVIEW (§1 routes/§2 changelog), DECISIONS (`D-043` — consent tiers,
   optional-permission deviation from §6, school refusal enforced server-side), BACKLOG grooming.

**Do not push.**

---

## 8. Definition of done

- [ ] Backend suite ≥ 340 passing; extension vitest green
- [ ] A fresh install holds **no** permission on any LLM origin until a tier is chosen
- [ ] Consent record lands in `metric_events` with its tier — verified against a real account
- [ ] A session POST with a content-shaped field is rejected by schema, not stripped
- [ ] `audience='school'` is refused **server-side**
- [ ] `npm run build` clean; manifest loads unpacked with no warnings
- [ ] §6 copy reproduced verbatim, and the "never trained" claim verified against Google's current
      terms for the tier actually in use — or the copy changed

## 9. Report back

1. The §2 deviation: agree or disagree, and whether the popup-hosted screen loses enough of §6's
   contextual timing to be worth reverting.
2. Google's current data-use terms for the API tier in use — does the "never used to train models"
   line survive verbatim?
3. Whether `extra='forbid'` was already set on the companion schema or had to be added. If it had
   to be added, invariant (b) was never actually holding.
4. Confirm you did not push.

---

## 10. Not in this doc — the rest of the store submission

Roughly a second day, none of it engineering: hosted privacy policy URL; the dashboard data
disclosure form (declare the web-history-adjacent data honestly — a mismatch with observed
behaviour is the most common cause of rejection and of later takedown); test credentials for
reviewers, since `launchWebAuthFlow` blocks them otherwise; screenshots at 1280×800; short
description ≤132 chars; 440×280 promo tile. Review latency is days to weeks and outside your
control — submit before it feels ready and iterate.
