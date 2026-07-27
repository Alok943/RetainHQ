import { createClient } from '@supabase/supabase-js'
import { getConsentTier, switchConsentTier, type ConsentTier } from '../consent'

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || 'https://kvmymvimlkvepatrlgsf.supabase.co'
const SUPABASE_KEY = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY || 'sb_publishable_c2R4IoLBwDgSFPwbfkqIog_HIFEF4Ej'
// Mirrors service_worker.ts's default — see its comment for why the prod
// fallback (not localhost) is deliberate.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://retainhq.onrender.com'

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

const statusEl = document.getElementById('status')!
const loginBtn = document.getElementById('loginBtn')!
const logoutBtn = document.getElementById('logoutBtn')!

// --- Companion consent & tiers (SPEC-companion-phase1.md §6) ----------------
// consentTier === null renders the choice screen; anything else renders the
// settings row instead. The three copy strings live in index.html verbatim —
// this file only wires the buttons.

const consentScreenEl = document.getElementById('consentScreen')!
const settingsRowEl = document.getElementById('settingsRow')!
const currentTierLabelEl = document.getElementById('currentTierLabel')!
const tierSelectEl = document.getElementById('tierSelect') as HTMLSelectElement

const TIER_LABELS: Record<ConsentTier, string> = {
  cloud: 'Smart tracking (cloud)',
  nano: 'On-device AI',
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
        payload: { tier, copy_version: 'v1', surface: 'popup' },
      }),
    })
  } catch (error) {
    console.error('Failed to record companion consent', error)
  }
}

async function renderConsentUI(): Promise<void> {
  const tier = await getConsentTier()
  if (tier === null) {
    consentScreenEl.style.display = 'block'
    settingsRowEl.style.display = 'none'
  } else {
    consentScreenEl.style.display = 'none'
    settingsRowEl.style.display = 'block'
    currentTierLabelEl.textContent = TIER_LABELS[tier]
    tierSelectEl.value = tier
  }
}

async function chooseTier(newTier: ConsentTier): Promise<void> {
  const before = await getConsentTier()
  const effectiveTier = await switchConsentTier(newTier, before)
  await recordConsent(effectiveTier)
  await renderConsentUI()
}

document.getElementById('tierCloudBtn')!.addEventListener('click', () => chooseTier('cloud'))
document.getElementById('tierNanoBtn')!.addEventListener('click', () => chooseTier('nano'))
document.getElementById('tierTitlesBtn')!.addEventListener('click', () => chooseTier('titles'))
tierSelectEl.addEventListener('change', () => chooseTier(tierSelectEl.value as ConsentTier))

renderConsentUI()

async function updateUI() {
  const { data: { session } } = await supabase.auth.getSession()
  
  if (session) {
    statusEl.textContent = `Signed in as ${session.user.email}`
    loginBtn.style.display = 'none'
    logoutBtn.style.display = 'block'
    
    const syncBtn = document.getElementById('syncLeetCodeBtn')
    if (syncBtn) syncBtn.style.display = 'block'
  } else {
    statusEl.textContent = 'Not signed in'
    loginBtn.style.display = 'block'
    logoutBtn.style.display = 'none'
    
    const syncBtn = document.getElementById('syncLeetCodeBtn')
    if (syncBtn) syncBtn.style.display = 'none'
  }
}

loginBtn.addEventListener('click', async () => {
  statusEl.textContent = 'Signing in...'
  try {
    const redirectUrl = chrome.identity.getRedirectURL()
    // Derived from the extension/add-on id, so it differs by browser
    // (chromiumapp.org vs Firefox's own redirect domain) — logged rather
    // than guessed so the real Firefox value can be added to Supabase's
    // allowed-redirect list (IMPLEMENTATION-companion-firefox.md §5).
    console.log('[RetainHQ] OAuth redirect URL for this build/browser:', redirectUrl)
    const authUrl = `${SUPABASE_URL}/auth/v1/authorize?provider=google&redirect_to=${encodeURIComponent(redirectUrl)}`
    
    chrome.identity.launchWebAuthFlow(
      {
        url: authUrl,
        interactive: true
      },
      async (redirectUri) => {
        if (chrome.runtime.lastError || !redirectUri) {
          console.error(chrome.runtime.lastError)
          statusEl.textContent = 'Sign in failed'
          return
        }

        // Parse hash fragment for token
        const hash = new URL(redirectUri).hash.substring(1)
        const params = new URLSearchParams(hash)
        const accessToken = params.get('access_token')
        const refreshToken = params.get('refresh_token')
        
        if (accessToken && refreshToken) {
          await supabase.auth.setSession({
            access_token: accessToken,
            refresh_token: refreshToken
          })
          updateUI()
        } else {
          statusEl.textContent = 'Failed to parse tokens'
        }
      }
    )
  } catch (error) {
    console.error(error)
    statusEl.textContent = 'Error initiating sign in'
  }
})

logoutBtn.addEventListener('click', async () => {
  await supabase.auth.signOut()
  updateUI()
})

const syncBtn = document.getElementById('syncLeetCodeBtn')
if (syncBtn) {
  syncBtn.addEventListener('click', () => {
    syncBtn.textContent = 'Syncing...'
    syncBtn.setAttribute('disabled', 'true')
    chrome.runtime.sendMessage({ type: 'LEETCODE_BACKFILL' })
  })
}

chrome.runtime.onMessage.addListener((message) => {
  if (message.type === 'LEETCODE_BACKFILL_COMPLETE') {
    if (syncBtn) {
      syncBtn.textContent = `Synced ${message.count} solves!`
      syncBtn.removeAttribute('disabled')
      setTimeout(() => { syncBtn.textContent = 'Sync LeetCode' }, 3000)
    }
  } else if (message.type === 'LEETCODE_BACKFILL_ERROR') {
    if (syncBtn) {
      syncBtn.textContent = 'Sync Failed'
      syncBtn.removeAttribute('disabled')
      setTimeout(() => { syncBtn.textContent = 'Sync LeetCode' }, 3000)
    }
  }
})

// Initial check
updateUI()
