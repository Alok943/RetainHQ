import type { Segment } from '../types'

const INACTIVITY_TIMEOUT_MS = 3 * 60 * 1000 // 3 minutes
const EMIT_INTERVAL_MS = 5 * 60 * 1000 // Emit segment every 5 minutes if active

export interface TrackerOptions {
  surface: string
  url_domain: string
  getTitle: () => string
}

/** Shared by every adapter (generic activity_tracker AND youtube.ts, which
 * tracks play/pause instead of mouse/keyboard) so segment shape and the
 * message contract to the service worker live in exactly one place. */
export function emitSegment(options: TrackerOptions, start: number, end: number, active: boolean) {
  const segment: Segment = {
    surface: options.surface,
    url_domain: options.url_domain,
    title_metadata: options.getTitle(),
    start,
    end,
    active
  }
  chrome.runtime.sendMessage({ type: 'SEGMENT_EMIT', segment })
}

export function startActivityTracking(options: TrackerOptions) {
  let isTracking = false
  let currentSegmentStart = 0
  let lastActivityTime = Date.now()

  function sendSegment(start: number, end: number, active: boolean) {
    emitSegment(options, start, end, active)
  }

  function checkActivity() {
    const now = Date.now()
    if (document.hidden || now - lastActivityTime > INACTIVITY_TIMEOUT_MS) {
      if (isTracking) {
        // We became inactive (backgrounded tab or genuine idle). Close the segment.
        sendSegment(currentSegmentStart, lastActivityTime, true)
        isTracking = false
      }
    } else {
      if (!isTracking) {
        // Became active again
        isTracking = true
        currentSegmentStart = now
      }
    }
  }

  function handleActivity() {
    if (document.hidden) return // a backgrounded tab firing timers isn't "activity"
    lastActivityTime = Date.now()
    checkActivity()
  }

  // Throttle event listeners to avoid performance issues
  let throttleTimer: number | null = null
  function throttledHandleActivity() {
    if (throttleTimer) return
    throttleTimer = window.setTimeout(() => {
      handleActivity()
      throttleTimer = null
    }, 1000)
  }

  // Bind events
  window.addEventListener('mousemove', throttledHandleActivity, { passive: true })
  window.addEventListener('keydown', throttledHandleActivity, { passive: true })
  window.addEventListener('scroll', throttledHandleActivity, { passive: true })
  window.addEventListener('click', throttledHandleActivity, { passive: true })

  // A backgrounded tab (switched away, minimized) must not keep counting as
  // active study time just because mouse/keyboard events fired recently —
  // and a foregrounded tab should immediately resume tracking rather than
  // waiting for the next mouse move.
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      checkActivity()
    } else {
      handleActivity()
    }
  })

  // Periodically emit while active
  window.setInterval(() => {
    checkActivity() // ensure state is up to date
    if (isTracking) {
      const now = Date.now()
      sendSegment(currentSegmentStart, now, true)
      currentSegmentStart = now
    }
  }, EMIT_INTERVAL_MS)

  // Start tracking initially
  handleActivity()

  // Flush on tab close/navigation. `beforeunload` is unreliable under MV3
  // and back-forward-cache — `pagehide` fires in both the unload and the
  // bfcache-eligible cases, and visibilitychange (above) already covers a
  // plain tab-switch-away.
  window.addEventListener('pagehide', () => {
    if (isTracking) {
      sendSegment(currentSegmentStart, Date.now(), true)
    }
  })
}
