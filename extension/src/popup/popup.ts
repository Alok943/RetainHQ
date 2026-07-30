import { createClient } from '@supabase/supabase-js'
import { getConsentTier, switchConsentTier, CONSENT_COPY_VERSION, type ConsentTier } from '../consent'
import { getRedirectURL, launchWebAuthFlow, storageLocalGet } from '../browser_api'
import { isTrackingPaused, setTrackingPaused } from '../pause_state'
import type { Segment } from '../types'

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || 'https://kvmymvimlkvepatrlgsf.supabase.co'
const SUPABASE_KEY = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY || 'sb_publishable_c2R4IoLBwDgSFPwbfkqIog_HIFEF4Ej'
// Mirrors service_worker.ts's default — see its comment for why the prod
// fallback (not localhost) is deliberate.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://retainhq.onrender.com'

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
  try {
    const redirectUrl = getRedirectURL()
    // Derived from the extension/add-on id, so it differs by browser
    // (chromiumapp.org vs Firefox's own redirect domain) — logged rather
    // than guessed so the real Firefox value can be added to Supabase's
    // allowed-redirect list (IMPLEMENTATION-companion-firefox.md §5).
    console.log('[RetainHQ] OAuth redirect URL for this build/browser:', redirectUrl)
    const authUrl = `${SUPABASE_URL}/auth/v1/authorize?provider=google&redirect_to=${encodeURIComponent(redirectUrl)}`

    // Promise form, NOT the callback form. Firefox's launchWebAuthFlow is
    // promise-only: a callback is accepted and then never invoked, so the OAuth
    // window opens, the user picks an account, and nothing happens — no error,
    // no session. See browser_api.ts.
    const redirectUri = await launchWebAuthFlow({ url: authUrl, interactive: true })
    if (!redirectUri) {
      setStatus('Sign in failed')
      return
    }

    // Supabase returns tokens in the hash on implicit flow, but in the query
    // string when it hands back an error — read both so a real failure surfaces
    // its reason instead of the generic "failed to parse tokens".
    const url = new URL(redirectUri)
    const params = new URLSearchParams(url.hash.substring(1))
    const query = url.searchParams
    const authError = params.get('error_description') || query.get('error_description')
      || params.get('error') || query.get('error')
    if (authError) {
      console.error('[RetainHQ] OAuth error:', authError)
      setStatus(`Sign in failed: ${authError}`)
      return
    }

    const accessToken = params.get('access_token')
    const refreshToken = params.get('refresh_token')
    if (accessToken && refreshToken) {
      await supabase.auth.setSession({ access_token: accessToken, refresh_token: refreshToken })
      setStatus(null)
      updateUI()
    } else {
      setStatus('Failed to parse tokens')
    }
  } catch (error) {
    console.error(error)
    setStatus(`Sign in error: ${(error as Error)?.message ?? error}`)
  }
})

logoutBtn.addEventListener('click', async () => {
  await supabase.auth.signOut()
  setStatus(null)
  updateUI()
})

const syncBtn = el('syncLeetCodeBtn')
const SYNC_BTN_IDLE_LABEL = syncBtn.textContent ?? 'Import solved LeetCode problems'
syncBtn.addEventListener('click', () => {
  syncBtn.textContent = 'Importing…'
  syncBtn.setAttribute('disabled', 'true')
  chrome.runtime.sendMessage({ type: 'LEETCODE_BACKFILL' })
})

chrome.runtime.onMessage.addListener((message) => {
  if (message.type === 'LEETCODE_BACKFILL_COMPLETE') {
    syncBtn.textContent = `Imported ${message.count} solves`
    syncBtn.removeAttribute('disabled')
    setTimeout(() => { syncBtn.textContent = SYNC_BTN_IDLE_LABEL }, 3000)
  } else if (message.type === 'LEETCODE_BACKFILL_ERROR') {
    syncBtn.textContent = 'Import failed — try again'
    syncBtn.removeAttribute('disabled')
    setTimeout(() => { syncBtn.textContent = SYNC_BTN_IDLE_LABEL }, 3000)
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
