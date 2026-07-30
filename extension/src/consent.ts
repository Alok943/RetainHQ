// Companion consent & tiers (SPEC-companion-phase1.md §6, IMPLEMENTATION-companion-consent.md §2/§5).
//
// consentTier === null means NO LLM-surface capture of any kind — the extension
// must never default it to a value. `cloud`/`nano` both require the optional
// `optional_host_permissions` grant for the LLM origins (chatgpt.com, claude.ai,
// gemini.google.com); `titles` needs no origin grant at all, which is itself a
// truthful selling point of that option (§6 copy).
//
// Enforced by Chrome, not by convention: `llm_metadata.ts` is a STATIC
// content_scripts entry in manifest.json matching the LLM origins, but those
// origins live under optional_host_permissions, not host_permissions — Chrome
// gates actual injection on the runtime grant (chrome.permissions.request),
// re-evaluating on each navigation. With no grant, there is no code path —
// buggy or otherwise — that can reach an LLM tab's content at all.
//
// [DECISION, deviates from IMPLEMENTATION-companion-consent.md §2/§5]: that doc
// specifies chrome.scripting.registerContentScripts for this. Implemented,
// then reverted: @crxjs/vite-plugin only discovers and bundles content
// scripts that are referenced from a STATIC manifest content_scripts entry —
// a script referenced only from a registerContentScripts() call is silently
// dropped from the build entirely (confirmed: llm_metadata.ts was absent from
// dist/ after building with the dynamic-registration version). The static
// entry + optional_host_permissions combination is confirmed real Chrome
// behavior (a granted optional host permission gates an already-declared
// static content script; Chrome documents that already-open matching tabs
// need a refresh to pick it up, exactly as it does for a host permission
// grant generally) and gives the identical enforcement guarantee — no grant,
// no injection — without a broken build or the extra "scripting" permission.

import { storageLocalGet, storageLocalSet, permissionsRequest, permissionsRemove, permissionsContains } from './browser_api'

// 'nano' (on-device AI) was removed 2026-07-27 — no on-device classification
// path was ever implemented, so it was a relabelled 'titles' that requested
// LLM host permissions it never used.
export type ConsentTier = 'cloud' | 'titles'

export const LLM_ORIGINS = [
  '*://*.chatgpt.com/*',
  '*://claude.ai/*',
  '*://gemini.google.com/*',
]

const STORAGE_KEY_CONSENT = 'consentTier'
const STORAGE_KEY_COPY_VERSION = 'consentCopyVersion'

// Bumped 2026-07-27 (IMPLEMENTATION-companion-chat-content.md §6.4): the
// 'cloud' tier's processing changed materially — it now reads chat TEXT for
// topic segmentation, not just page titles. A v1 consent record described a
// different (lesser) kind of processing than what actually happens today, so
// it isn't meaningful consent for what's happening now. Bump this again any
// time what a tier actually does changes enough that the existing copy would
// misdescribe it.
export const CONSENT_COPY_VERSION = 'v2'

export async function getConsentTier(): Promise<ConsentTier | null> {
  const data = await storageLocalGet([STORAGE_KEY_CONSENT, STORAGE_KEY_COPY_VERSION])
  const tier = (data[STORAGE_KEY_CONSENT] as ConsentTier | undefined) ?? null
  if (tier === null) return null
  const storedVersion = data[STORAGE_KEY_COPY_VERSION] as string | undefined
  // A tier chosen under stale copy is treated as never having been chosen —
  // re-prompts the user rather than silently carrying old consent forward.
  if (storedVersion !== CONSENT_COPY_VERSION) return null
  return tier
}

export async function setConsentTier(tier: ConsentTier): Promise<void> {
  await storageLocalSet({ [STORAGE_KEY_CONSENT]: tier, [STORAGE_KEY_COPY_VERSION]: CONSENT_COPY_VERSION })
}

export async function hasLlmOriginPermission(): Promise<boolean> {
  return permissionsContains({ origins: LLM_ORIGINS })
}

/**
 * The one entry point for every tier transition — the initial choice AND
 * later switching, in both directions, from the popup's settings row.
 * Symmetric by construction: whichever direction, the origin grant is kept
 * in lockstep with the stored tier, never left dangling on its own.
 *
 * Must be called from a user-gesture context (a click handler) — the origin
 * request inside it fails silently otherwise. Cannot be called from the
 * service worker.
 */
export async function switchConsentTier(
  newTier: ConsentTier,
  _currentTier: ConsentTier | null,
): Promise<ConsentTier> {
  const needsOrigins = newTier === 'cloud'
  // Queried live rather than trusted from the caller's cached `currentTier`:
  // getConsentTier() returns null for a tier stored under a stale
  // CONSENT_COPY_VERSION (§ above) even though the browser permission grant
  // from that earlier choice is still live. Deriving hadOrigins from the
  // actual permission state — not the possibly-stale cached tier — is what
  // guarantees a re-prompted v1 'cloud' user who now picks 'titles' actually
  // has the dangling grant revoked instead of silently keeping it.
  const hadOrigins = await hasLlmOriginPermission()

  if (needsOrigins && !hadOrigins) {
    const granted = await permissionsRequest({ origins: LLM_ORIGINS })
    if (!granted) {
      // A denied permission prompt is still a choice, and must be logged as
      // one — the requested tier never took effect, so record what's true.
      await setConsentTier('titles')
      return 'titles'
    }
  } else if (!needsOrigins && hadOrigins) {
    await permissionsRemove({ origins: LLM_ORIGINS })
  }

  await setConsentTier(newTier)
  return newTier
}
