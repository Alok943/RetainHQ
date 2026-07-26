import { createClient } from '@supabase/supabase-js'

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || 'https://kvmymvimlkvepatrlgsf.supabase.co'
const SUPABASE_KEY = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY || 'sb_publishable_c2R4IoLBwDgSFPwbfkqIog_HIFEF4Ej'

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
