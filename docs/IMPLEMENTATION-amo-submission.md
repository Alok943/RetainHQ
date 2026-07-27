# Implementation Plan — Firefox Distribution (self-hosted first, AMO listing later)

**Target: Firefox only.** Chrome is paused — its $5 fee is deferred, and self-hosting is not an
option there (§0.1). AMO is free.

Requirements below were checked against Mozilla's docs on **2026-07-26** — do not substitute
remembered Chrome Web Store rules, they differ materially.

---

## 0.1 Two distribution paths — pick unlisted first

| | **Unlisted + self-host** (do this now) | **Listed on AMO** (later) |
|---|---|---|
| Public AMO page | no | yes |
| Human review queue | **no** — signing is automated | yes, days to weeks |
| Install | user clicks a link on retainhq.app | AMO "Add to Firefox" |
| Needs §3 reviewer account | **no** | yes |
| Needs §4 listing assets | **no** | yes |
| Needs §1 privacy policy | **yes** | yes |
| Needs §2 data declaration | **yes** | yes |
| Needs §0 source upload | **verify at submission** | yes |

Unlisted skips everything that costs calendar time while keeping everything that protects users —
Firefox still shows the data-collection declaration at install, so §1 and §2 remain mandatory.

**Mozilla must still sign it.** Release Firefox refuses unsigned extensions; there is no way to
distribute entirely outside Mozilla. Unlisted means "not publicly listed", not "unreviewed by
anything".

### The self-host flow

1. Submit `dist-firefox/` to AMO as **unlisted** (web UI, or `web-ext sign` with API credentials
   from the Mozilla Add-on API Keys page — the CLI path is worth wiring since every update repeats it).
2. Download the signed `.xpi`.
3. Host it on retainhq.app. **The server must send `Content-Type: application/x-xpinstall`** — with
   the wrong type Firefox downloads the file instead of offering to install it, which looks broken
   and is the single most common self-hosting mistake.
4. Add an "Add to Firefox" link on the site pointing at the `.xpi`.

Updates: bump `version` in the manifest, re-sign, replace the hosted file. For automatic updates
also publish an update manifest and set `browser_specific_settings.gecko.update_url` — optional for
v1, but without it users stay on whatever they installed forever.

### 0.1.1 Chrome cannot do this

A self-hosted `.crx` fails with `CRX_REQUIRED_PROOF_MISSING`; Google removed one-click off-store
installs. Chrome's only routes are the Web Store, enterprise policy, or developer-mode unpacked.
**Loading unpacked does persist across restarts** (unlike Firefox's temporary add-ons, which drop
on restart) — so `dist/` is a usable personal daily driver on Chrome today. It never auto-updates,
and Chrome nags about developer-mode extensions on each launch.

---

## 0. The requirement most likely to be missed

**AMO requires you to upload your source code separately**, because this extension is bundled.
Mozilla's rule covers "tools that generate a single file from other files" — Vite/rollup qualifies,
so `dist-firefox/` alone will be rejected or stalled.

You must supply:
- a source archive (the repo's `extension/` directory, excluding `node_modules`, `dist`, `dist-firefox`)
- **build reproduction instructions** a reviewer can follow exactly

Write those instructions into `extension/REVIEWER-BUILD.md`:

```
Node: <the exact version you build with — run `node -v`>
npm ci
npm run build:firefox
Output: dist-firefox/   (this is what was submitted)
```

Obfuscated code is banned outright. Minified/bundled is fine **provided** the source is attached —
which is exactly what this step buys.

---

## 1. Privacy policy — blocking

Host at a stable public URL on retainhq.app (e.g. `/privacy/companion`). It must be reachable
without logging in.

Say precisely what is true today — the code already makes these claims defensible, so do not
soften or inflate them:

- **Collected:** page titles, domains, PDF filenames, timestamps, durations; LeetCode problem slugs
  and Accepted-submission events; optional reflection answers (confidence, hint used, mistake note).
- **Not collected:** the contents of any page, and specifically **not the text of AI chats** —
  `llm_metadata.ts` reads `document.title` and nothing else.
- **Where it goes:** the user's own RetainHQ account, via the RetainHQ API (Render) into Supabase
  Postgres. Metadata is classified by Google Gemini; chat *content* is never sent, at any tier.
- **Consent:** LLM-site access is an optional permission the user grants explicitly; the choice is
  recorded and changeable at any time.
- **Deletion:** every tracked session appears in the in-app evidence log and can be deleted there.
- **Not sold, not shared with third parties, not used for advertising.**

Do not claim "never used to train models" unless the Gemini API tier in use actually guarantees it —
verify before writing that sentence, and omit it rather than ship a false claim.

---

## 2. Data collection disclosure — blocking

Since **3 November 2025**, new Firefox extensions must declare data collection in
`browser_specific_settings.gecko.data_collection_permissions`. The manifest already has:

```jsonc
"data_collection_permissions": { "required": ["browsingActivity"] }
```

**Verify this is the correct and complete set** against Mozilla's current permitted values before
submitting — an inaccurate declaration is the fastest route to rejection, and later to a block.
Check specifically whether the LeetCode reflection notes (free-text "biggest mistake") require an
additional category beyond `browsingActivity`; free text a user types is a different class from
browsing metadata.

Mozilla's policy: **opt-in** consent for personally identifiable data, **opt-out** for technical
and interaction data. The existing design matches — chat-site access is opt-in, metadata is on by
default and disclosed — but confirm the reflection free-text sits on the right side of that line.

Firefox surfaces these declarations in its own install consent screen, so this is not paperwork:
it is what the user reads before installing.

---

## 3. Reviewer access — blocking

The extension is useless without a RetainHQ login, and `identity.launchWebAuthFlow` will block a
reviewer completely.

Create a **dedicated reviewer account** (not your own), seeded with a little data so the popup is
not empty, and put the credentials plus a short walkthrough in the "Notes for reviewers" field:

```
Sign in via the popup with: reviewer@retainhq.app / <password>
Then visit any youtube.com/watch page for ~1 min; the popup shows the tracked session.
Chat-site access is OFF until the tier button in the popup is used — it requests the
optional host permission at that point, and nothing is captured before it.
```

That last sentence is the single most useful thing you can tell a reviewer, because it pre-answers
the question the optional AI-site permissions will otherwise raise.

---

## 4. Listing assets

- **Name:** RetainHQ Companion
- **Summary (≤250 chars on AMO):** state the single purpose plainly. Avoid "tracking" as the lead
  verb — "RetainHQ Companion notices what you study — videos, courses, LeetCode — so RetainHQ can
  schedule reviews before you forget it."
- **Description:** what it captures, what it does not, and that it requires a RetainHQ account.
- **Screenshots:** at minimum the popup signed-in state and the consent tier screen. The consent
  screen is worth showing — it is the reassuring one.
- **Icon:** already present (`icons/128.png`).
- **Category:** Productivity. **License:** your choice; a repo license file is not required for AMO.
- **Listed vs unlisted:** choose **listed** for a public page. Unlisted still gets signed and is
  self-distributed — useful if you want to install it on your own Firefox today without waiting for
  review.

---

## 5. Order of work — unlisted path only

Sections 3 and 4 are **skipped** for unlisted; do them only when going listed.

1. `extension/REVIEWER-BUILD.md` + confirm `npm ci && npm run build:firefox` reproduces from clean.
2. Privacy policy page live on retainhq.app; note the URL.
3. Verify `data_collection_permissions` values; amend the manifest if the free-text notes need more.
4. Submit `dist-firefox/` to AMO as **unlisted**; attach source if prompted; download the signed `.xpi`.
5. Host the `.xpi` on retainhq.app with `Content-Type: application/x-xpinstall`, and add an
   "Add to Firefox" button. **Verify by installing from a clean Firefox profile** — not from the
   profile that already has the unpacked build loaded, which would mask a broken MIME type.
6. Docs same commit: SYSTEM-OVERVIEW changelog + BACKLOG (Chrome listing deferred; pin the Chrome
   extension id via a manifest key before that submission so the redirect URL stops changing;
   `gecko.update_url` + update manifest for auto-updates).

## 6. Definition of done

- [ ] `npm ci && npm run build:firefox` reproduces `dist-firefox/` from a clean checkout
- [ ] Privacy policy live at a public URL and linked in the listing
- [ ] `data_collection_permissions` verified accurate against current Mozilla docs
- [ ] Reviewer account works end-to-end from a fresh browser profile
- [ ] Source archive + build instructions attached to the submission

## 7. Report back

1. Whether `browsingActivity` alone covered the disclosure, or the reflection free-text forced more.
2. The privacy policy URL, for the listing and the SYSTEM-OVERVIEW entry.
3. Anything AMO asked for that this doc did not anticipate.

Sources checked 2026-07-26: [Source code submission](https://extensionworkshop.com/documentation/publish/source-code-submission/) ·
[Submitting an add-on](https://extensionworkshop.com/documentation/publish/submitting-an-add-on/) ·
[Add-on policies](https://extensionworkshop.com/documentation/publish/add-on-policies/) ·
[Data collection consent changes](https://blog.mozilla.org/addons/2025/10/23/data-collection-consent-changes-for-new-firefox-extensions/)
