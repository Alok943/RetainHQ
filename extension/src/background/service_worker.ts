import { partitionClosedSessions, stitchSegments } from './stitcher'
import type { Segment, Session, CompanionSessionIn } from '../types'
import { createClient } from '@supabase/supabase-js'
import { getConsentTier } from '../consent'

// Constants
const SESSION_GAP_MS = 15 * 60 * 1000 // 15 mins
const ALARM_NAME = 'companion-tick'
// Chrome clamps repeating alarms below 1 min anyway; this also matches the
// gap-check/queue-flush cadence the old setInterval used.
const ALARM_PERIOD_MIN = 1

// A batch that keeps failing (a bad item, a schema mismatch) must not
// retry forever, and the queue must not grow without bound while offline
// for a long stretch — both were unbounded before.
const MAX_ATTEMPTS = 8
const MAX_QUEUE_SIZE = 300
const SEND_CHUNK_SIZE = 20

interface QueuedSession {
  payload: CompanionSessionIn
  attempts: number
}

// MV3 service workers are evicted after ~30s idle — a module-level array
// and setInterval both vanish with it. Everything that must survive an
// eviction lives in chrome.storage.local instead; the alarm (not a timer)
// is what wakes the worker back up.
const STORAGE_KEY_BUFFER = 'segmentBuffer'
const STORAGE_KEY_QUEUE = 'syncQueue'

// We'll read these from process.env when bundled by Vite, or you can hardcode for the skeleton
const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || 'https://kvmymvimlkvepatrlgsf.supabase.co'
const SUPABASE_KEY = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY || 'sb_publishable_c2R4IoLBwDgSFPwbfkqIog_HIFEF4Ej'
// Defaults to PRODUCTION, unlike frontend/src/lib/api.js's localhost default —
// the frontend's prod build always gets VITE_API_BASE_URL injected by Vercel,
// but nothing yet enforces that at extension-package time. A forgotten env
// var when building for the Chrome Web Store must not silently ship an
// extension that points every real user at localhost:8000; a forgotten
// override for local dev only breaks dev, which is loud and immediate.
// Local dev: set VITE_API_BASE_URL=http://localhost:8000 in extension/.env.
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

async function maybeShowConsentNudgeBadge(): Promise<void> {
  const tier = await getConsentTier()
  if (tier !== null) return
  chrome.action.setBadgeText({ text: '!' })
  chrome.action.setBadgeBackgroundColor({ color: '#F59E0B' })
  chrome.action.setTitle({ title: 'RetainHQ Companion: choose how to understand your AI chats' })
}

async function getBuffer(): Promise<Segment[]> {
  const data = await chrome.storage.local.get([STORAGE_KEY_BUFFER])
  return (data[STORAGE_KEY_BUFFER] as Segment[] | undefined) || []
}

async function setBuffer(segments: Segment[]): Promise<void> {
  await chrome.storage.local.set({ [STORAGE_KEY_BUFFER]: segments })
}

function sessionToPayload(session: Session): CompanionSessionIn {
  return {
    session_id: session.session_id,
    duration_min: session.duration_min,
    // Session end (when studying stopped), not sync time — batches can
    // land long after the fact, and the backend uses this to place the
    // event on the right day in the evidence log.
    occurred_at: new Date(session.end).toISOString(),
    payload: {
      sources: session.sources,
      title_sample: session.title_bag, // title bag becomes title_sample for metadata
    }
  }
}

/**
 * Pulls the persisted buffer, splits it into definitively-closed sessions
 * (safe to stitch and enqueue) vs. the trailing group that might still be
 * live, enqueues the closed ones, and persists only the live remainder back
 * as the buffer. Called both on each SEGMENT_EMIT and on the periodic alarm
 * so a session closes promptly whether the tab is still open or not.
 */
async function flushClosedSessions(): Promise<void> {
  const buffer = await getBuffer()
  if (buffer.length === 0) return

  const { closed, live } = partitionClosedSessions(buffer, SESSION_GAP_MS, Date.now())
  if (closed.length === 0) {
    await setBuffer(live)
    return
  }

  const data = await chrome.storage.local.get([STORAGE_KEY_QUEUE])
  const queue: QueuedSession[] = (data[STORAGE_KEY_QUEUE] as QueuedSession[] | undefined) || []

  for (const group of closed) {
    const sessionId = crypto.randomUUID()
    const session = stitchSegments(group, sessionId)
    queue.push({ payload: sessionToPayload(session), attempts: 0 })
  }

  const overflow = queue.length - MAX_QUEUE_SIZE
  if (overflow > 0) {
    console.error(`Companion sync queue exceeded ${MAX_QUEUE_SIZE}; dropping ${overflow} oldest unsynced session(s).`)
    queue.splice(0, overflow)
  }

  await chrome.storage.local.set({ [STORAGE_KEY_QUEUE]: queue })
  await setBuffer(live)

  processQueue()
}

async function processQueue(): Promise<void> {
  const data = await chrome.storage.local.get([STORAGE_KEY_QUEUE])
  const queue: QueuedSession[] = (data[STORAGE_KEY_QUEUE] as QueuedSession[] | undefined) || []
  if (queue.length === 0) return

  const { data: { session: sbSession } } = await supabase.auth.getSession()
  if (!sbSession) {
    console.warn('Cannot sync session, not authenticated')
    return
  }

  // Send in bounded chunks so one malformed item can only ever poison its
  // own chunk, not every buffered session — the rest still get through.
  const chunk = queue.slice(0, SEND_CHUNK_SIZE)
  const rest = queue.slice(SEND_CHUNK_SIZE)

  try {
    const response = await fetch(`${API_BASE_URL}/api/companion/sessions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${sbSession.access_token}`
      },
      body: JSON.stringify({ sessions: chunk.map(item => item.payload) })
    })

    if (response.ok) {
      console.log(`Successfully synced ${chunk.length} session(s)`)
      await chrome.storage.local.set({ [STORAGE_KEY_QUEUE]: rest })
      // More may be waiting behind this chunk — keep draining.
      if (rest.length > 0) processQueue()
      return
    }

    if (response.status === 429) {
      // Daily cap — transient, resets at the next UTC day. Don't burn
      // attempts on a batch that was never the problem; just wait.
      console.warn('Companion sync rate-limited; will retry next tick')
      return
    }

    // Any other non-2xx (validation error, auth issue, etc.) — this chunk
    // is the problem. Age it and drop anything that's failed too many times
    // rather than retrying an unfixable payload forever.
    console.error('Failed to sync session batch', response.status, await response.text())
    const aged = chunk.map(item => ({ ...item, attempts: item.attempts + 1 }))
    const survivors = aged.filter(item => {
      if (item.attempts >= MAX_ATTEMPTS) {
        console.error(`Dropping session ${item.payload.session_id} after ${item.attempts} failed sync attempts`)
        return false
      }
      return true
    })
    await chrome.storage.local.set({ [STORAGE_KEY_QUEUE]: [...survivors, ...rest] })
  } catch (error) {
    // Network error (offline, DNS, etc.) — transient, don't burn attempts.
    console.error('Error syncing session batch (network offline?)', error)
  }
}

// Listener for messages from content scripts
chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type === 'SEGMENT_EMIT') {
    const segment = message.segment as Segment
    ;(async () => {
      const buffer = await getBuffer()
      buffer.push(segment)
      await setBuffer(buffer)
      await flushClosedSessions()
    })()

    // Set recording badge if active
    if (segment.active) {
      chrome.action.setBadgeText({ text: '●' })
      chrome.action.setBadgeBackgroundColor({ color: '#FF0000' })
      const displayTitle = segment.title_metadata || segment.url_domain
      chrome.action.setTitle({ title: `Recording: ${displayTitle}\nClick to correct/stop.` })
    } else {
      // No LLM host permission until a tier is chosen (§2), so there's no
      // way to detect "first visit to an LLM surface" anymore — the choice
      // screen moves into the popup instead, badged on the first ANY tracked
      // activity so it's noticeable without being a notification/prompt
      // (BACKLOG rule: no notifications, ever). Only shown once the active-
      // recording badge above has cleared, so it never fights that indicator.
      maybeShowConsentNudgeBadge()
    }
  } else if (message.type === 'LEETCODE_SOLVED') {
    // Must report success back: the content script keeps the solve in a durable queue
    // and only drops it once we confirm delivery. Answering optimistically (or not at
    // all) silently loses solves whenever the user is signed out or offline.
    ;(async () => {
      try {
        const { data: { session: sbSession } } = await supabase.auth.getSession()
        if (!sbSession) {
          sendResponse({ ok: false, reason: 'no-session' })
          return
        }
        const res = await fetch(`${API_BASE_URL}/api/evidence/leetcode/solve`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${sbSession.access_token}`
          },
          body: JSON.stringify(message.payload)
        })
        if (!res.ok) {
          console.error('LeetCode solve rejected', res.status)
          sendResponse({ ok: false, reason: `http-${res.status}` })
          return
        }
        sendResponse({ ok: true })
      } catch (error) {
        console.error('Failed to log LeetCode solve', error)
        sendResponse({ ok: false, reason: 'network' })
      }
    })()
    return true // keep the message channel open for the async sendResponse
  } else if (message.type === 'LEETCODE_BACKFILL') {
    ;(async () => {
      const { data: { session: sbSession } } = await supabase.auth.getSession()
      if (!sbSession) return

      try {
        // Fetch from LeetCode
        const lcRes = await fetch('https://leetcode.com/api/problems/all/')
        if (!lcRes.ok) {
          console.error('Failed to fetch from LeetCode API')
          return
        }
        const lcData = await lcRes.json()
        
        // Find solved slugs
        const solvedSlugs = []
        if (lcData.stat_status_pairs) {
          for (const pair of lcData.stat_status_pairs) {
            if (pair.status === 'ac') {
              solvedSlugs.push(pair.stat.question__title_slug)
            }
          }
        }

        if (solvedSlugs.length > 0) {
          // Send to backend
          await fetch(`${API_BASE_URL}/api/evidence/leetcode/backfill`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${sbSession.access_token}`
            },
            body: JSON.stringify({ solved_slugs: solvedSlugs })
          })
          console.log(`[RetainHQ] Backfilled ${solvedSlugs.length} LeetCode solves`)
          
          // Let the popup know we finished
          chrome.runtime.sendMessage({ type: 'LEETCODE_BACKFILL_COMPLETE', count: solvedSlugs.length })
        }
      } catch (error) {
        console.error('Failed to backfill LeetCode solves', error)
        chrome.runtime.sendMessage({ type: 'LEETCODE_BACKFILL_ERROR', error: String(error) })
      }
    })()
  }
})

// chrome.alarms (not setInterval) survives service worker eviction — this
// is what re-wakes the worker to close out sessions and drain the queue
// even if no tab sends a SEGMENT_EMIT message for a while.
chrome.alarms.create(ALARM_NAME, { periodInMinutes: ALARM_PERIOD_MIN })
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === ALARM_NAME) {
    flushClosedSessions()
    processQueue()
  }
})

// Also run once on worker startup (covers the case where the worker was
// evicted and just woke up for an unrelated event) rather than waiting up
// to ALARM_PERIOD_MIN for the next tick.
flushClosedSessions()
processQueue()
