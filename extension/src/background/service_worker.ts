import { planSync, stitchSegments } from './stitcher'
import type { Segment, Session, CompanionSessionIn } from '../types'
import { createClient } from '@supabase/supabase-js'
import { getConsentTier } from '../consent'
import { storageLocalGet, storageLocalSet, getRedirectURL, launchWebAuthFlow } from '../browser_api'
import { API_BASE_URL } from '../config'
import { scanRecentPythonSolves, DEFAULT_WINDOW_DAYS } from './leetcode_backfill'

// Constants
// Two different questions, two different numbers (2026-07-27 follow-up):
// "has this genuinely stopped" (kill) vs. "how long can real progress go
// unsynced" (checkpoint). Previously one 15-min constant did both jobs, which
// meant a multi-hour continuous session (a long video, a long LeetCode
// session) never synced anything until it finally ended — nothing showed up
// in the popup or the server for hours despite continuous activity.
const INACTIVITY_KILL_MS = 20 * 60 * 1000 // session is dead — stop counting, safe to close for good
const CHECKPOINT_MS = 15 * 60 * 1000 // still live, but sync progress-so-far on this cadence
// A checkpoint must only fire on a session that is genuinely STILL running.
// activity_tracker.ts emits every 5 min while active, so a last segment older
// than one interval plus a margin means activity has already stopped — that
// session must be left alone to close via INACTIVITY_KILL_MS rather than
// being checkpointed away (see planSync).
const CHECKPOINT_ACTIVITY_RECENCY_MS = 6 * 60 * 1000
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
const STORAGE_KEY_LAST_SYNC = 'lastSyncedAt'

// We'll read these from process.env when bundled by Vite, or you can hardcode for the skeleton
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

/**
 * Fire-and-forget message to the popup, safe when no popup is listening.
 *
 * Firefox REJECTS `runtime.sendMessage` with "Could not establish connection.
 * Receiving end does not exist." when nothing is open to receive it, and every
 * backfill notification below was an unhandled rejection waiting to happen.
 * Not hypothetical: a cold Render instance answered the backfill POST in 90s
 * (observed 2026-08-02), by which point the popup was long gone — the import
 * had fully succeeded and the console still showed an uncaught error.
 *
 * Swallowing is correct here rather than lazy: these messages only drive
 * transient button text. The durable result is already on the server, and the
 * popup re-reads real state on every open.
 */
function notifyPopup(message: unknown): void {
  Promise.resolve(chrome.runtime.sendMessage(message)).catch(() => {})
}

async function maybeShowConsentNudgeBadge(): Promise<void> {
  const tier = await getConsentTier()
  if (tier !== null) return
  chrome.action.setBadgeText({ text: '!' })
  chrome.action.setBadgeBackgroundColor({ color: '#F59E0B' })
  chrome.action.setTitle({ title: 'RetainHQ Companion: choose how to understand your AI chats' })
}

async function getBuffer(): Promise<Segment[]> {
  const data = await storageLocalGet([STORAGE_KEY_BUFFER])
  return (data[STORAGE_KEY_BUFFER] as Segment[] | undefined) || []
}

async function setBuffer(segments: Segment[]): Promise<void> {
  await storageLocalSet({ [STORAGE_KEY_BUFFER]: segments })
}

/**
 * `includeContent: false` for a CHECKPOINT flush of a still-live session.
 *
 * chat_extract.ts returns the whole visible conversation every time, not a
 * delta — so a 50-minute chat checkpointed every 15 minutes would send three
 * cumulative snapshots ("turns 1-6", "turns 1-12", "turns 1-18"), and the
 * backend would segment and record turns 1-6 three separate times: the same
 * topics duplicated in the evidence log, at 3x the Gemini cost. Content
 * therefore rides only the session that genuinely CLOSED, which describes a
 * finished conversation exactly once.
 *
 * Tradeoff, accepted: the closing session covers only the time since the last
 * checkpoint, so the whole conversation's topics attach to that shorter
 * duration. These are weight-0 TIME_BLOCK rows (they can't move mastery
 * either way), so an understated duration is strictly better than the same
 * topic credited three times.
 */
function sessionToPayload(session: Session, includeContent: boolean): CompanionSessionIn {
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
    },
    // SIBLING of payload, never nested inside it — mirrors
    // schemas/companion.py's CompanionSessionIn.content exactly. payload
    // keeps extra="forbid" specifically so raw chat text can never land
    // there even by accident.
    ...(includeContent && session.content ? { content: session.content } : {}),
    // `chapters` is NOT gated by includeContent — unlike content it's a sum
    // of per-segment deltas, not a repeated cumulative snapshot, so it's
    // exactly as safe on a checkpoint flush as on a closed one (see
    // stitcher.ts's stitchSegments).
    ...(session.chapters && session.chapters.length > 0 ? { chapters: session.chapters } : {}),
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

  // planSync decides both WHAT to send and which groups may carry chat
  // content — see its docstring for why that flag matters.
  const { toSync, remainingLive } = planSync(
    buffer, INACTIVITY_KILL_MS, CHECKPOINT_MS, CHECKPOINT_ACTIVITY_RECENCY_MS, Date.now()
  )

  if (toSync.length === 0) {
    await setBuffer(remainingLive)
    return
  }

  const data = await storageLocalGet([STORAGE_KEY_QUEUE])
  const queue: QueuedSession[] = (data[STORAGE_KEY_QUEUE] as QueuedSession[] | undefined) || []

  for (const { group, isClosed } of toSync) {
    const sessionId = crypto.randomUUID()
    const session = stitchSegments(group, sessionId)
    queue.push({ payload: sessionToPayload(session, isClosed), attempts: 0 })
  }

  const overflow = queue.length - MAX_QUEUE_SIZE
  if (overflow > 0) {
    console.error(`Companion sync queue exceeded ${MAX_QUEUE_SIZE}; dropping ${overflow} oldest unsynced session(s).`)
    queue.splice(0, overflow)
  }

  // Chat content took a queued session from ~200 bytes to as much as 16KB, so
  // a full 300-session offline backlog can approach Chrome's 10MB
  // storage.local quota. An over-quota set() REJECTS — and an unhandled
  // rejection here would abort the flush and silently stop syncing forever,
  // which is a far worse outcome than losing the topic split. Content is an
  // attribution nicety; the session record is the actual data. So on a write
  // failure, drop every content field and retry once.
  try {
    await storageLocalSet({ [STORAGE_KEY_QUEUE]: queue })
  } catch (error) {
    console.error('Failed to persist companion sync queue; retrying without chat content', error)
    for (const item of queue) delete item.payload.content
    await storageLocalSet({ [STORAGE_KEY_QUEUE]: queue })
  }
  await setBuffer(remainingLive)

  processQueue()
}

async function processQueue(): Promise<void> {
  const data = await storageLocalGet([STORAGE_KEY_QUEUE])
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
      // Read by the popup to show "last upload N min ago" — the only proof a
      // user has that anything reached the server, short of opening the app.
      await storageLocalSet({ [STORAGE_KEY_QUEUE]: rest, [STORAGE_KEY_LAST_SYNC]: Date.now() })
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
    await storageLocalSet({ [STORAGE_KEY_QUEUE]: [...survivors, ...rest] })
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
  } else if (message.type === 'SIGN_IN') {
    // Runs the WHOLE interactive OAuth flow here, never in the popup. Firefox
    // (confirmed 2026-07-30) closes a toolbar popup the instant a competing
    // window takes focus — which is exactly what launchWebAuthFlow's own auth
    // window does the moment it opens. That kills the popup's JS mid-flow
    // before it can ever parse the returned tokens, even though the OAuth
    // round-trip itself completes successfully server-side (confirmed via
    // Supabase auth logs: repeated successful `Login` events with no visible
    // change in the popup — the user's own retries chasing a UI that never
    // updated). The background page has no such lifecycle; it isn't torn down
    // by the popup closing, so the flow's continuation always gets to run.
    // popup.ts now only sends this message and re-renders on the response —
    // see its `loginBtn` handler for why nothing here should move back there.
    ;(async () => {
      try {
        const redirectUrl = getRedirectURL()
        const authUrl = `${SUPABASE_URL}/auth/v1/authorize?provider=google&redirect_to=${encodeURIComponent(redirectUrl)}`

        const redirectUri = await launchWebAuthFlow({ url: authUrl, interactive: true })
        if (!redirectUri) {
          sendResponse({ ok: false, reason: 'no-redirect' })
          return
        }

        // Supabase returns tokens in the hash on implicit flow, but in the query
        // string when it hands back an error — read both so a real failure surfaces
        // its reason instead of a generic parse failure.
        const url = new URL(redirectUri)
        const params = new URLSearchParams(url.hash.substring(1))
        const query = url.searchParams
        const authError = params.get('error_description') || query.get('error_description')
          || params.get('error') || query.get('error')
        if (authError) {
          console.error('[RetainHQ] OAuth error:', authError)
          sendResponse({ ok: false, reason: authError })
          return
        }

        const accessToken = params.get('access_token')
        const refreshToken = params.get('refresh_token')
        if (accessToken && refreshToken) {
          await supabase.auth.setSession({ access_token: accessToken, refresh_token: refreshToken })
          sendResponse({ ok: true })
        } else {
          sendResponse({ ok: false, reason: 'no-tokens' })
        }
      } catch (error) {
        console.error('[RetainHQ] Sign-in error:', error)
        sendResponse({ ok: false, reason: String((error as Error)?.message ?? error) })
      }
    })()
    return true // keep the message channel open for the async sendResponse
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
  } else if (message.type === 'TRACKING_PAUSED_CHANGED') {
    // The popup owns the toggle and has already written pause_state.ts's
    // storage flag by the time this arrives — this only updates the icon so
    // the paused state is visible without opening the popup.
    if (message.paused) {
      chrome.action.setBadgeText({ text: '❚❚' })
      chrome.action.setBadgeBackgroundColor({ color: '#64748B' })
      chrome.action.setTitle({ title: 'RetainHQ Companion: tracking paused' })
    } else {
      chrome.action.setBadgeText({ text: '' })
      chrome.action.setTitle({ title: 'RetainHQ Companion' })
      maybeShowConsentNudgeBadge()
    }
  } else if (message.type === 'LEETCODE_BACKFILL') {
    // The popup sets its button to "Importing…" + disabled the instant this
    // message is sent (see popup.ts), and only ever undoes that on receiving
    // LEETCODE_BACKFILL_COMPLETE or _ERROR. Every exit path below MUST send
    // one or the other — three of them silently didn't (no session, LeetCode
    // fetch failing, and genuinely finding 0 solved problems all fell through
    // with no message at all), which left the button stuck disabled forever,
    // no way to retry short of reopening the popup. Confirmed 2026-07-30.
    ;(async () => {
      try {
        const { data: { session: sbSession } } = await supabase.auth.getSession()
        if (!sbSession) {
          notifyPopup({ type: 'LEETCODE_BACKFILL_ERROR', error: 'Sign in first' })
          return
        }

        // Window and language are the caller's to choose so the popup can offer
        // them later without touching this file; both fall back to the module
        // defaults. `credentials: 'include'` is what makes the scan see the
        // user's own submissions at all — without cookies LeetCode answers as
        // signed-out, which cost this codebase a full debugging session.
        const windowDays = typeof message.windowDays === 'number' ? message.windowDays : DEFAULT_WINDOW_DAYS
        const cutoffMs = Date.now() - windowDays * 24 * 60 * 60 * 1000

        // Throws a message-bearing Error on a bad status or a login page; the
        // outer catch turns it into the popup's error text verbatim.
        const { solves, partial } = await scanRecentPythonSolves(cutoffMs)

        const solvedSlugs = [...solves.keys()]
        if (solvedSlugs.length > 0) {
          // Response deliberately checked — this was fire-and-forget, so a 401
          // (expired Supabase token) or 422 (schema drift) sent the popup a
          // cheerful "Imported N solves" while the backend stored nothing.
          const res = await fetch(`${API_BASE_URL}/api/evidence/leetcode/backfill`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${sbSession.access_token}`
            },
            // solved_at carries the REAL solve date per slug. Without it the
            // backend stamps every historic solve with import time, which
            // stacks two months of work onto today in the evidence log and
            // makes the whole point of a windowed import invisible.
            body: JSON.stringify({
              solved_slugs: solvedSlugs,
              solved_at: Object.fromEntries(
                [...solves].map(([slug, ms]) => [slug, new Date(ms).toISOString()])
              ),
            })
          })
          if (!res.ok) {
            console.error('Backfill rejected by RetainHQ', res.status, await res.text())
            notifyPopup({ type: 'LEETCODE_BACKFILL_ERROR', error: `RetainHQ returned ${res.status}` })
            return
          }
          console.log(`[RetainHQ] Backfilled ${solvedSlugs.length} Python solves from the last ${windowDays} days`)
        }

        // Always report completion, even at 0 solved — 0 is a real, valid
        // result (nothing solved in Python in the window), not an error, and
        // the button must resolve either way. `partial` rides along so a
        // rate-limited scan can't be reported as a clean full import.
        notifyPopup({ type: 'LEETCODE_BACKFILL_COMPLETE', count: solvedSlugs.length, partial })
      } catch (error) {
        console.error('Failed to backfill LeetCode solves', error)
        notifyPopup({ type: 'LEETCODE_BACKFILL_ERROR', error: String(error) })
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
