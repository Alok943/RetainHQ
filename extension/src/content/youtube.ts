import { emitSegment, type TrackerOptions } from './activity_tracker'
import { extractChapters, chapterAt, shouldAttemptChapterParse, type Chapter } from './chapter_extract'
import type { ChapterWatch } from '../types'

const options: TrackerOptions = {
  surface: 'youtube',
  url_domain: 'youtube.com',
  getTitle,
  getChapterProgress
}

let isTracking = false
let trackingInterval: number | null = null
let currentSegmentStart = 0
// Tracked so visibilitychange can check play state without re-querying the DOM.
let currentVideo: HTMLVideoElement | null = null

// Chapter list for the current video (chapter_extract.ts) — re-read each time
// a video is attached (attachVideoListeners), since a new /watch navigation
// means a new video with its own chapters. Empty for the (majority of)
// videos with no chapters, which is fine: getChapterProgress then returns
// undefined and the session syncs as one whole-video block, unchanged from
// before this existed.
let chapters: Chapter[] = []
// Watched-seconds-per-chapter DELTA since the last getChapterProgress() call
// — sampled on its own short interval (CHAPTER_SAMPLE_MS), independent of
// the 5-min segment-emit cadence, so chapter attribution doesn't get coarser
// just because the emit interval is long.
let chapterAccumulator: Record<string, number> = {}
const CHAPTER_SAMPLE_MS = 15_000
let chapterSampleInterval: number | null = null

function startChapterSampling() {
  if (chapterSampleInterval !== null) return
  chapterSampleInterval = window.setInterval(() => {
    if (!isTracking || !currentVideo || chapters.length === 0) return
    const title = chapterAt(chapters, currentVideo.currentTime)
    if (!title) return
    chapterAccumulator[title] = (chapterAccumulator[title] ?? 0) + CHAPTER_SAMPLE_MS / 1000
  }, CHAPTER_SAMPLE_MS)
}

function getChapterProgress(): ChapterWatch[] | undefined {
  const entries = Object.entries(chapterAccumulator)
  if (entries.length === 0) return undefined
  chapterAccumulator = {} // delta, consumed — next call starts fresh
  return entries.map(([title, seconds]) => ({ title, seconds: Math.round(seconds) }))
}

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

// YouTube reuses the SAME <video> element across an SPA navigation from one
// /watch page straight to another (autoplay-next, clicking a suggestion) —
// so `dataset.retainHqAttached` alone can't detect "this is a new video" and
// gate a chapter re-read on it; that flag stays 'true' across the
// navigation. Tracked separately by URL instead. Bounded retries because the
// chapter panel can render a beat after the URL changes — most videos have
// none at all, so this must stop retrying rather than re-querying the DOM on
// every mutation for a video's entire runtime.
let lastVideoHref: string | null = null
// Keep looking for chapters for this long after a video first appears, at
// most this often. Time-based, NOT a try-N-times budget: this function's only
// caller is the MutationObserver, which fires hundreds of times during
// YouTube's page load, so a count budget is exhausted in milliseconds —
// before the chapter list (below the fold, lazily rendered) exists at all.
// See shouldAttemptChapterParse's docstring.
const CHAPTER_PARSE_WINDOW_MS = 30_000
const CHAPTER_PARSE_MIN_INTERVAL_MS = 2_000
let chapterParseWindow = { startedAt: 0, lastAttemptAt: 0 }

function refreshChaptersIfNewVideo() {
  const now = Date.now()
  if (location.href !== lastVideoHref) {
    lastVideoHref = location.href
    chapters = []
    chapterAccumulator = {}
    chapterParseWindow = { startedAt: now, lastAttemptAt: 0 }
  }
  if (chapters.length > 0) return
  if (!shouldAttemptChapterParse(chapterParseWindow, now, CHAPTER_PARSE_WINDOW_MS, CHAPTER_PARSE_MIN_INTERVAL_MS)) return
  chapterParseWindow.lastAttemptAt = now
  chapters = extractChapters()
}

function attachVideoListeners() {
  const video = document.querySelector('video')
  if (!video) return

  currentVideo = video
  refreshChaptersIfNewVideo()

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

startChapterSampling()

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
