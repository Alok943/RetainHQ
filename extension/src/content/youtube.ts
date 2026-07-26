import { emitSegment, type TrackerOptions } from './activity_tracker'

const options: TrackerOptions = {
  surface: 'youtube',
  url_domain: 'youtube.com',
  getTitle
}

let isTracking = false
let trackingInterval: number | null = null
let currentSegmentStart = 0
// Tracked so visibilitychange can check play state without re-querying the DOM.
let currentVideo: HTMLVideoElement | null = null

function getTitle(): string {
  // YouTube video titles are typically in the document title or a specific h1 element
  const titleEl = document.querySelector('h1.ytd-watch-metadata yt-formatted-string')
  if (titleEl && titleEl.textContent) {
    return titleEl.textContent
  }
  return document.title.replace(' - YouTube', '')
}

function sendSegment(start: number, end: number, active: boolean) {
  emitSegment(options, start, end, active)
}

function startTracking() {
  // A backgrounded/minimized tab must not count as active study time even
  // if the video element is technically still playing (autoplay chaining).
  if (isTracking || document.hidden) return
  isTracking = true
  currentSegmentStart = Date.now()

  // Periodically emit active segments while video is playing
  trackingInterval = window.setInterval(() => {
    const now = Date.now()
    sendSegment(currentSegmentStart, now, true)
    currentSegmentStart = now
  }, 5 * 60 * 1000) // Emit every 5 minutes while active
}

function stopTracking() {
  if (!isTracking) return
  isTracking = false

  if (trackingInterval !== null) {
    clearInterval(trackingInterval)
    trackingInterval = null
  }

  const now = Date.now()
  sendSegment(currentSegmentStart, now, true)
}

function attachVideoListeners() {
  const video = document.querySelector('video')
  if (!video) return

  currentVideo = video

  // Prevent multiple attachments
  if (video.dataset.retainHqAttached === 'true') return
  video.dataset.retainHqAttached = 'true'

  video.addEventListener('play', startTracking)
  video.addEventListener('pause', stopTracking)
  video.addEventListener('ended', stopTracking)

  // Handle initial state
  if (!video.paused) {
    startTracking()
  }
}

// Watch for DOM changes to find the video element (YouTube SPA navigation)
const observer = new MutationObserver(() => {
  if (window.location.pathname === '/watch') {
    attachVideoListeners()
  } else {
    currentVideo = null
    stopTracking()
  }
})

observer.observe(document.body, { childList: true, subtree: true })

// Initial check
if (window.location.pathname === '/watch') {
  attachVideoListeners()
}

// Backgrounded tab (switched away, minimized): stop counting active time.
// Foregrounding resumes tracking if the video is (still) actually playing —
// covers autoplay chaining into a video the user isn't watching.
document.addEventListener('visibilitychange', () => {
  if (document.hidden) {
    stopTracking()
  } else if (currentVideo && !currentVideo.paused) {
    startTracking()
  }
})

// Ensure segment is flushed on navigation/tab-close. `beforeunload` is
// unreliable under MV3 and back-forward-cache; `pagehide` covers both, and
// visibilitychange (above) already covers a plain tab-switch-away.
window.addEventListener('pagehide', () => {
  stopTracking()
})
