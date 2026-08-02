import { createClient } from '@supabase/supabase-js'
import { getConsentTier, switchConsentTier, CONSENT_COPY_VERSION, NEETCODE_ORIGIN, type ConsentTier } from '../consent'
import { storageLocalGet, storageLocalSet, runtimeSendMessage, permissionsRequest } from '../browser_api'
import { isTrackingPaused, setTrackingPaused } from '../pause_state'
import type { Segment } from '../types'
import { API_BASE_URL, API_ORIGIN_PATTERN } from '../config'
import { LANGUAGE_GROUPS, WINDOW_OPTIONS, type LeetCodeImportPrefs } from '../leetcode_langs'

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || 'https://kvmymvimlkvepatrlgsf.supabase.co'
const SUPABASE_KEY = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY || 'sb_publishable_c2R4IoLBwDgSFPwbfkqIog_HIFEF4Ej'

// Must match service_worker.ts. The popup only ever READS these — the worker
// owns every write, so a popup that is open while a session closes simply sees
// stale numbers until the next open, never a conflicting write.
const STORAGE_KEY_BUFFER = 'segmentBuffer'
const STORAGE_KEY_QUEUE = 'syncQueue'
const STORAGE_KEY_LAST_SYNC = 'lastSyncedAt'
// service_worker.ts's INACTIVITY_KILL_MS. A segment newer than this is part of a
// session that has not closed yet — i.e. still recording.
const SESSION_GAP_MS = 20 * 60 * 1000

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY, {
  auth: {
    storage: {
      getItem: (key) => {
        return new Promise((resolve) => {
          chrome.storage.local.get([key], (result) => {
            resolve((result[key] as string | undefined) ?? null)
          })
        })
      },
      setItem: (key, value) => {
        return new Promise((resolve) => {
          chrome.storage.local.set({ [key]: value }, () => resolve())
        })
      },
      removeItem: (key) => {
        return new Promise((resolve) => {
          chrome.storage.local.remove([key], () => resolve())
        })
      }
    }
  }
})

const el = <T extends HTMLElement = HTMLElement>(id: string) => document.getElementById(id) as T

const statusEl = el('status')
const signedInEl = el('signedIn')
const signedOutEl = el('signedOut')
const accountEmailEl = el('accountEmail')
const loginBtn = el('loginBtn')
const logoutBtn = el('logoutBtn')
const statePillEl = el('statePill')
const statePillTextEl = el('statePillText')
const pauseToggleBtn = el<HTMLButtonElement>('pauseToggleBtn')

/** The status line is for transient states and failures only — a permanently
 * visible "Signed in as…" line was pure chrome; the account row carries that
 * now. Passing null hides it entirely. */
function setStatus(message: string | null): void {
  statusEl.textContent = message ?? ''
  statusEl.classList.toggle('hidden', message === null)
}

function setPill(state: 'idle' | 'recording' | 'attention' | 'paused', text: string): void {
  statePillEl.setAttribute('data-state', state)
  statePillTextEl.textContent = text
}

// --- Companion consent & tiers (SPEC-companion-phase1.md §6) ----------------
// consentTier === null renders the choice screen; anything else renders the
// settings row instead. The three copy strings live in index.html verbatim —
// this file only wires the buttons.

const consentScreenEl = el('consentScreen')
const settingsRowEl = el('settingsRow')
const currentTierLabelEl = el('currentTierLabel')
const tierSelectEl = el<HTMLSelectElement>('tierSelect')

const TIER_LABELS: Record<ConsentTier, string> = {
  cloud: 'Smart tracking (cloud)',
  titles: 'Titles only',
}

/** Best-effort — the consent record is an artifact of the tap, not a gate on
 * it; a signed-out user or a flaky network must not block the tier from
 * taking effect locally. */
async function recordConsent(tier: ConsentTier): Promise<void> {
  try {
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) return
    await fetch(`${API_BASE_URL}/api/metrics/events`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`,
      },
      body: JSON.stringify({
        event_type: 'companion_consent',
        payload: { tier, copy_version: CONSENT_COPY_VERSION, surface: 'popup' },
      }),
    })
  } catch (error) {
    console.error('Failed to record companion consent', error)
  }
}

// Mirrors the stored tier so a click handler can read it WITHOUT awaiting.
// Firefox requires permissions.request() to be reached synchronously from the
// user gesture; any prior await drops the gesture context and the prompt never
// appears — the button silently does nothing (observed on Firefox 2026-07-26).
let cachedTier: ConsentTier | null = null

async function renderConsentUI(): Promise<void> {
  const tier = await getConsentTier()
  cachedTier = tier
  // display:flex, not block — both blocks are flex columns in the new layout.
  consentScreenEl.style.display = tier === null ? 'flex' : 'none'
  settingsRowEl.style.display = tier === null ? 'none' : 'flex'
  if (tier !== null) {
    currentTierLabelEl.textContent = TIER_LABELS[tier]
    tierSelectEl.value = tier
  }
}

async function chooseTier(newTier: ConsentTier): Promise<void> {
  // NO await before switchConsentTier — see cachedTier above.
  const effectiveTier = await switchConsentTier(newTier, cachedTier)
  await recordConsent(effectiveTier)
  await renderConsentUI()
  await renderActivity()
}

el('tierCloudBtn').addEventListener('click', () => chooseTier('cloud'))
el('tierTitlesBtn').addEventListener('click', () => chooseTier('titles'))
tierSelectEl.addEventListener('change', () => chooseTier(tierSelectEl.value as ConsentTier))

// --- Live activity ----------------------------------------------------------
// The popup previously showed nothing about capture at all, so the badge was
// the only signal that anything worked and there was no way to see that a
// session was still buffered locally rather than lost.

const SURFACE_LABELS: Record<string, string> = {
  youtube: 'YouTube',
  coursera: 'Coursera',
  leetcode: 'LeetCode',
  neetcode: 'NeetCode',
  chatgpt: 'ChatGPT',
  claude: 'Claude',
  gemini: 'Gemini',
  pdf: 'PDF',
  llm: 'AI chat',
  notion: 'Notion',
}

function relativeTime(ms: number): string {
  const mins = Math.round((Date.now() - ms) / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins} min ago`
  const hrs = Math.round(mins / 60)
  if (hrs < 24) return `${hrs} h ago`
  return `${Math.round(hrs / 24)} d ago`
}

async function renderActivity(): Promise<void> {
  const data = await storageLocalGet([STORAGE_KEY_BUFFER, STORAGE_KEY_QUEUE, STORAGE_KEY_LAST_SYNC])
  const buffer = (data[STORAGE_KEY_BUFFER] as Segment[] | undefined) ?? []
  const queued = ((data[STORAGE_KEY_QUEUE] as unknown[] | undefined) ?? []).length
  const lastSync = data[STORAGE_KEY_LAST_SYNC] as number | undefined
  const paused = await isTrackingPaused()

  pauseToggleBtn.textContent = paused ? 'Resume tracking' : 'Pause tracking'

  if (paused) {
    el('nowTitle').textContent = 'Tracking paused'
    el('nowMeta').textContent = 'Nothing is being recorded until you resume.'
    el('nowCard').classList.add('empty')
    setPill('paused', 'Paused')
    // Nothing else in this function reads consent/sync state differently
    // while paused — fall through so the sync card still reports honestly.
  }

  const latest = buffer.length > 0 ? buffer[buffer.length - 1] : null
  const isLive = latest !== null && Date.now() - latest.end < SESSION_GAP_MS

  if (paused) {
    // already rendered above — skip the Now-card branches below.
  } else if (latest && isLive) {
    const mins = Math.max(1, Math.round(buffer.reduce((n, s) => n + (s.end - s.start), 0) / 60000))
    const surface = SURFACE_LABELS[latest.surface] ?? latest.url_domain
    el('nowTitle').textContent = latest.title_metadata || latest.url_domain
    el('nowMeta').textContent = `${surface} · ${mins} min · updated ${relativeTime(latest.end)}`
    el('nowCard').classList.remove('empty')
    setPill('recording', 'Recording')
  } else if (latest) {
    el('nowTitle').textContent = latest.title_metadata || latest.url_domain
    el('nowMeta').textContent = `Last seen ${relativeTime(latest.end)} · closing out`
    el('nowCard').classList.remove('empty')
    setPill('idle', 'Idle')
  } else {
    el('nowTitle').textContent = 'Nothing tracked yet'
    el('nowMeta').textContent = 'Open a video, course or LeetCode problem.'
    el('nowCard').classList.add('empty')
    setPill('idle', 'Idle')
  }

  if (!paused && cachedTier === null) setPill('attention', 'Choose')

  if (queued > 0) {
    el('syncTitle').textContent = `${queued} session${queued === 1 ? '' : 's'} waiting to upload`
    el('syncMeta').textContent = 'Retries automatically — needs you signed in.'
  } else if (lastSync) {
    el('syncTitle').textContent = 'Up to date'
    el('syncMeta').textContent = `Last upload ${relativeTime(lastSync)}`
  } else {
    el('syncTitle').textContent = 'Nothing uploaded yet'
    // The single most-asked question about this extension: it looks broken at
    // first because nothing has synced yet. Say so — a long, continuous
    // session checkpoints every 15 min; a genuinely idle one closes at 20.
    el('syncMeta').textContent = 'Long sessions sync every 15 min; idle ones close at 20.'
  }
}

async function updateUI() {
  const { data: { session } } = await supabase.auth.getSession()
  const signedIn = Boolean(session)

  signedInEl.classList.toggle('hidden', !signedIn)
  signedOutEl.classList.toggle('hidden', signedIn)
  if (session) accountEmailEl.textContent = session.user.email ?? ''

  await renderActivity()
}

loginBtn.addEventListener('click', async () => {
  setStatus('Opening Google sign-in…')
  // The ENTIRE flow (launchWebAuthFlow, token parsing, setSession) runs in the
  // background script, not here — see service_worker.ts's 'SIGN_IN' handler
  // for why. Firefox closes this popup the instant the OAuth window it opens
  // takes focus, which used to kill everything below this line mid-flight:
  // the auth completed successfully server-side every time (confirmed via
  // Supabase's own logs), but this popup's code never survived to consume the
  // result, so nothing ever appeared to happen. The background has no such
  // lifecycle, so it always gets to finish and persist the session to the
  // SAME chrome.storage.local this popup's own supabase client reads —
  // durable even if this exact popup instance doesn't survive to see the
  // response below. If it doesn't, reopening the popup shows signed-in
  // immediately, since renderConsentUI().then(updateUI) at the bottom of this
  // file re-reads that storage on every fresh open.
  try {
    const response = await runtimeSendMessage<{ ok: boolean; reason?: string }>({ type: 'SIGN_IN' })
    if (response?.ok) {
      setStatus(null)
      updateUI()
    } else {
      console.error('[RetainHQ] Sign-in failed:', response?.reason)
      setStatus(`Sign in failed: ${response?.reason ?? 'unknown error'}`)
    }
  } catch (error) {
    // Only reached if THIS popup instance is still alive to catch it — a
    // closed popup silently drops this, which is fine per the comment above.
    console.error(error)
    setStatus(`Sign in error: ${(error as Error)?.message ?? error}`)
  }
})

logoutBtn.addEventListener('click', async () => {
  await supabase.auth.signOut()
  setStatus(null)
  updateUI()
})

// --- LeetCode import options -------------------------------------------
// Was hardcoded to Python/60-days as a single-user shortcut — wrong the
// moment a second install exists, since it would silently drop every
// non-Python solve for every OTHER user with no setting to recover it. The
// panel below asks instead of assuming, and the checked-by-everything /
// all-time starting state is the SAME behavior as no filter at all, so a
// user who ignores the panel entirely still gets the safe default.

const STORAGE_KEY_IMPORT_PREFS = 'leetcodeImportPrefs'

const importOptionsToggle = el('importOptionsToggle')
const importOptionsEl = el('importOptions')
const importWindowSelect = el<HTMLSelectElement>('importWindowSelect')
const importLangGrid = el('importLangGrid')

// createElement/textContent, not `innerHTML = \`<option>...\``: AMO's linter
// (no-unsanitized/property) flags an innerHTML sink the instant it sees a
// `${}` substitution, even one that's provably a hardcoded literal —
// WINDOW_OPTIONS is a static const in leetcode_langs.ts, never touched by
// user input, but the linter can't see that far. Same fix already applied in
// leetcode.ts/neetcode.ts's reflection panel for the identical warning.
for (const opt of WINDOW_OPTIONS) {
  const option = document.createElement('option')
  option.value = opt.value
  option.textContent = opt.label
  importWindowSelect.appendChild(option)
}
// "All time" — the no-filter starting point — not DEFAULT_WINDOW_DAYS, so an
// untouched panel matches "no filter" exactly rather than one particular window.
importWindowSelect.value = 'all'

const langCheckboxes: HTMLInputElement[] = LANGUAGE_GROUPS.map((group, i) => {
  const label = document.createElement('label')
  const input = document.createElement('input')
  input.type = 'checkbox'
  input.checked = true // starting state = everything, i.e. no filter
  input.dataset.groupIndex = String(i)
  label.appendChild(input)
  label.appendChild(document.createTextNode(group.label))
  importLangGrid.appendChild(label)
  return input
})

el('importLangAllBtn').addEventListener('click', () => {
  langCheckboxes.forEach((cb) => { cb.checked = true })
})
el('importLangNoneBtn').addEventListener('click', () => {
  langCheckboxes.forEach((cb) => { cb.checked = false })
})

// Pure DOM toggle — no permission-sensitive call lives here, so this is safe
// to make async-adjacent to anything without spending a Firefox gesture.
importOptionsToggle.addEventListener('click', () => {
  importOptionsEl.classList.toggle('hidden')
})

/** Reads the panel's current state SYNCHRONOUSLY — called from the very top
 * of the import click handler, before the gesture-sensitive permission
 * request, so this must never await. */
function readImportPrefsFromForm(): LeetCodeImportPrefs {
  const opt = WINDOW_OPTIONS.find((o) => o.value === importWindowSelect.value)
  const checkedGroups = LANGUAGE_GROUPS.filter((_, i) => langCheckboxes[i].checked)
  const langs = checkedGroups.length === LANGUAGE_GROUPS.length
    ? null // everything checked = no filter, not "here's every group we know about"
    : checkedGroups.flatMap((g) => g.langs)
  return { windowDays: opt?.days ?? null, langs }
}

function applyImportPrefsToForm(prefs: LeetCodeImportPrefs): void {
  const opt = WINDOW_OPTIONS.find((o) => o.days === prefs.windowDays)
  importWindowSelect.value = opt?.value ?? 'all'
  LANGUAGE_GROUPS.forEach((group, i) => {
    langCheckboxes[i].checked = prefs.langs === null || group.langs.every((l) => prefs.langs!.includes(l))
  })
}

/** Loads any saved choice on popup open; if there is none, this is a
 * never-imported install, and the panel opens expanded so the choice is
 * visible before the first scan ever runs rather than buried behind
 * "Options". */
async function initImportOptions(): Promise<void> {
  const data = await storageLocalGet([STORAGE_KEY_IMPORT_PREFS])
  const saved = data[STORAGE_KEY_IMPORT_PREFS] as LeetCodeImportPrefs | undefined
  if (saved) {
    applyImportPrefsToForm(saved)
  } else {
    importOptionsEl.classList.remove('hidden')
  }
}

const syncBtn = el('syncLeetCodeBtn')
const SYNC_BTN_IDLE_LABEL = syncBtn.textContent ?? 'Import solved LeetCode problems'

// `*://*.leetcode.com/*` sits in manifest host_permissions, which Chrome grants
// at install — so nothing ever requested it at runtime. Firefox MV3 does NOT:
// host permissions there are user-granted, and MDN is explicit that "if an
// extension update requests new host permissions, these are not shown to the
// user" — so an updating Firefox install can sit permanently ungranted with no
// prompt ever shown. leetcode.com/api/problems/all/ returns NO CORS headers at
// all (verified 2026-08-02), so without the grant the background fetch isn't
// merely cookie-less, it's blocked outright: "NetworkError when attempting to
// fetch resource". Same missing grant also stops leetcode.ts injecting, which
// is why live solve capture and backfill failed together.
// Still required after the import moved into the page (leetcode_tab_fetch.ts):
// both tabs.query({url}) and scripting.executeScript need host access to the
// tab they touch, so an ungranted origin now fails as "no LeetCode tab" rather
// than as a network error — a different symptom, same missing grant.
// The API origin rides along because the backfill makes TWO cross-origin
// calls, and the second one — the POST to our own backend — is the one that
// actually failed (`TypeError: NetworkError`, verified 2026-08-02 from the
// background console: both LeetCode fetches returned 200, credentialed
// included). See API_ORIGIN_PATTERN for why our own API needs a host grant
// when leetcode.com's doesn't strictly.
const LEETCODE_ORIGIN = '*://*.leetcode.com/*'

syncBtn.addEventListener('click', async () => {
  // Synchronous DOM reads, not awaits — safe before the gesture-sensitive
  // call below. An explicit "select at least one language" guard here, not a
  // disabled button kept in sync with checkbox state: simpler, and it still
  // fails before any permission prompt or network call.
  const prefs = readImportPrefsFromForm()
  if (prefs.langs !== null && prefs.langs.length === 0) {
    setStatus('Select at least one language to import')
    return
  }

  // FIRST await in this handler, deliberately — Firefox only honours
  // permissions.request() inside a live user-gesture context, and any earlier
  // await spends it (the same trap documented on cachedTier above and in
  // consent.ts's switchConsentTier). Resolves true with no dialog when the
  // origin is already granted, so calling it unconditionally is safe.
  let granted = true
  try {
    granted = await permissionsRequest({ origins: [LEETCODE_ORIGIN, API_ORIGIN_PATTERN] })
  } catch (error) {
    // Chrome rejects request() for an origin that isn't in
    // optional_host_permissions — but Chrome already granted it at install,
    // so treat the throw as "nothing to ask for" rather than a failure.
    console.debug('[RetainHQ] LeetCode origin request not applicable', error)
  }

  if (!granted) {
    syncBtn.textContent = 'Failed: LeetCode access denied'
    setTimeout(() => { syncBtn.textContent = SYNC_BTN_IDLE_LABEL }, 3000)
    return
  }

  setStatus(null)
  syncBtn.textContent = 'Importing…'
  syncBtn.setAttribute('disabled', 'true')
  // Not awaited — nothing downstream depends on this write landing before the
  // message send, and awaiting it would only delay the scan starting.
  storageLocalSet({ [STORAGE_KEY_IMPORT_PREFS]: prefs })
  chrome.runtime.sendMessage({ type: 'LEETCODE_BACKFILL', windowDays: prefs.windowDays, langs: prefs.langs })
})

chrome.runtime.onMessage.addListener((message) => {
  if (message.type === 'LEETCODE_BACKFILL_COMPLETE') {
    // 0 is a real, valid result (nothing matched the chosen filters) — say so
    // plainly rather than the slightly odd "Imported 0 solves".
    // `partial` means the scan was cut short by LeetCode's rate limiter, so the
    // window is only partly covered; reporting that as a clean import would be
    // a lie the user can't detect, and re-running picks up the rest.
    if (message.count > 0) {
      syncBtn.textContent = message.partial
        ? `Imported ${message.count} — run again for more`
        : `Imported ${message.count} solves`
    } else {
      syncBtn.textContent = message.partial ? 'Rate-limited — try again' : 'No solves matched your filters'
    }
    syncBtn.removeAttribute('disabled')
    setTimeout(() => { syncBtn.textContent = SYNC_BTN_IDLE_LABEL }, 3000)
  } else if (message.type === 'LEETCODE_BACKFILL_ERROR') {
    // Surface the actual reason (e.g. "Sign in first") rather than a generic
    // "try again" — service_worker.ts now sends one on every failure path,
    // never silently drops the button in "Importing…" forever.
    syncBtn.textContent = message.error ? `Failed: ${message.error}` : 'Import failed — try again'
    syncBtn.removeAttribute('disabled')
    setTimeout(() => { syncBtn.textContent = SYNC_BTN_IDLE_LABEL }, 3000)
  }
})

// NeetCode import. Separate button rather than a mode on the LeetCode one:
// they read different sources, produce different trust tiers, and this one has
// no window/language options because getCompletedProblems is an undated,
// unfiltered list — there is nothing to filter on.
const neetSyncBtn = el('syncNeetCodeBtn')
const NEET_BTN_IDLE_LABEL = neetSyncBtn.textContent ?? 'Import completed NeetCode problems'

neetSyncBtn.addEventListener('click', async () => {
  // FIRST await, for the gesture reason documented on the LeetCode handler.
  // neetcode.io is in host_permissions but Firefox does not grant those at
  // install (D-053/054), and the consent flow only asks on a FIRST install —
  // so an existing install reaching this button may still not have it.
  let granted = true
  try {
    granted = await permissionsRequest({ origins: [NEETCODE_ORIGIN, API_ORIGIN_PATTERN] })
  } catch (error) {
    console.debug('[RetainHQ] NeetCode origin request not applicable', error)
  }
  if (!granted) {
    neetSyncBtn.textContent = 'Failed: NeetCode access denied'
    setTimeout(() => { neetSyncBtn.textContent = NEET_BTN_IDLE_LABEL }, 3000)
    return
  }

  setStatus(null)
  neetSyncBtn.textContent = 'Importing…'
  neetSyncBtn.setAttribute('disabled', 'true')
  chrome.runtime.sendMessage({ type: 'NEETCODE_BACKFILL' })
})

chrome.runtime.onMessage.addListener((message) => {
  if (message.type === 'NEETCODE_BACKFILL_COMPLETE') {
    neetSyncBtn.textContent = message.count > 0
      ? `Imported ${message.count} problems`
      : 'No completed problems found'
    neetSyncBtn.removeAttribute('disabled')
    setTimeout(() => { neetSyncBtn.textContent = NEET_BTN_IDLE_LABEL }, 3000)
  } else if (message.type === 'NEETCODE_BACKFILL_ERROR') {
    neetSyncBtn.textContent = message.error ? `Failed: ${message.error}` : 'Import failed — try again'
    neetSyncBtn.removeAttribute('disabled')
    setTimeout(() => { neetSyncBtn.textContent = NEET_BTN_IDLE_LABEL }, 3000)
  }
})

pauseToggleBtn.addEventListener('click', async () => {
  const nextPaused = !(await isTrackingPaused())
  await setTrackingPaused(nextPaused)
  // Content scripts pick this up via storage.onChanged (pause_state.ts) on
  // their own; the service worker doesn't watch storage, so it's told
  // directly so the icon updates without waiting for the next segment.
  chrome.runtime.sendMessage({ type: 'TRACKING_PAUSED_CHANGED', paused: nextPaused })
  await renderActivity()
})

el('version').textContent = `v${chrome.runtime.getManifest().version}`

// Consent first: renderActivity's pill depends on cachedTier being resolved.
renderConsentUI().then(updateUI)
initImportOptions()
