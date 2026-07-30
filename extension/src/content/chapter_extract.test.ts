// @vitest-environment jsdom
import { describe, it, expect, beforeEach } from 'vitest'
import { extractChapters, chapterAt, shouldAttemptChapterParse } from './chapter_extract'

function setBody(html: string) {
  document.body.innerHTML = html
}

beforeEach(() => {
  document.body.innerHTML = ''
})

// Markup mirrors the live freeCodeCamp DOM captured 2026-07-27: each item
// duplicates its own title (a second <h3> with a different class, no relation
// to the visible one) and time — a hover-preview clone, not a real second
// chapter. Real chapter has class "macro-markers" on its <h3>.
function chapterItem(title: string, time: string, withClone = true) {
  const clone = withClone
    ? `<h3 class="problem-walkthroughs">${title}</h3><div id="time">${time}</div>`
    : ''
  return `<ytd-macro-markers-list-item-renderer>
    <h3 class="macro-markers">${title}</h3>
    <div id="time">${time}</div>
    ${clone}
  </ytd-macro-markers-list-item-renderer>`
}

describe('extractChapters', () => {
  it('reads title and timestamp, ignoring the hover-preview clone', () => {
    setBody(chapterItem('Chapter 1 – Modules, Comments & pip', '9:41'))
    const chapters = extractChapters()
    expect(chapters).toEqual([{ title: 'Chapter 1 – Modules, Comments & pip', startSeconds: 581 }])
  })

  it('parses HH:MM:SS timestamps', () => {
    setBody(chapterItem('Late chapter', '1:02:15'))
    expect(extractChapters()).toEqual([{ title: 'Late chapter', startSeconds: 3735 }])
  })

  it('reads multiple chapters in document order', () => {
    setBody([
      chapterItem('Intro', '0:00'),
      chapterItem('Setup', '2:05'),
      chapterItem('NumPy', '9:41'),
    ].join(''))
    expect(extractChapters()).toEqual([
      { title: 'Intro', startSeconds: 0 },
      { title: 'Setup', startSeconds: 125 },
      { title: 'NumPy', startSeconds: 581 },
    ])
  })

  it('returns [] when no chapter markers exist (the common case — most videos have none)', () => {
    setBody('<div>just a normal video page</div>')
    expect(extractChapters()).toEqual([])
  })

  it('skips an item with an unparseable timestamp rather than throwing', () => {
    setBody(chapterItem('Bad chapter', 'not-a-time', false))
    expect(extractChapters()).toEqual([])
  })
})

describe('chapterAt', () => {
  const chapters = [
    { title: 'Intro', startSeconds: 0 },
    { title: 'Setup', startSeconds: 125 },
    { title: 'NumPy', startSeconds: 581 },
  ]

  it('returns the chapter whose start is at or before the playhead', () => {
    expect(chapterAt(chapters, 0)).toBe('Intro')
    expect(chapterAt(chapters, 124)).toBe('Intro')
    expect(chapterAt(chapters, 125)).toBe('Setup')
    expect(chapterAt(chapters, 600)).toBe('NumPy')
  })

  it('returns null before the first chapter or with no chapters at all', () => {
    expect(chapterAt([], 100)).toBeNull()
  })
})

describe('shouldAttemptChapterParse', () => {
  const WINDOW = 30_000
  const INTERVAL = 2_000

  it('allows the first attempt immediately', () => {
    expect(shouldAttemptChapterParse({ startedAt: 0, lastAttemptAt: 0 }, 0, WINDOW, INTERVAL)).toBe(true)
  })

  it('does NOT burn its budget on a burst of MutationObserver callbacks', () => {
    // The bug this exists for: the observer fires hundreds of times in the
    // first moments of a page load. A try-N-times budget was spent within
    // milliseconds — before the lazily-rendered chapter list existed — so
    // chapters were silently missed on real loads while every DOM-populated
    // test passed.
    const win = { startedAt: 0, lastAttemptAt: 0 }
    expect(shouldAttemptChapterParse(win, 0, WINDOW, INTERVAL)).toBe(true)
    win.lastAttemptAt = 1 // the attempt above just ran (0 is the "never" sentinel)
    for (const t of [1, 5, 20, 100, 500, 1_999]) {
      expect(shouldAttemptChapterParse(win, t, WINDOW, INTERVAL)).toBe(false)
    }
    // ...but retries once the spacing interval has genuinely elapsed
    // (lastAttemptAt=1, so the interval is up at 2_001, not 2_000).
    expect(shouldAttemptChapterParse(win, 2_001, WINDOW, INTERVAL)).toBe(true)
  })

  it('keeps retrying long enough for a late-rendering chapter list', () => {
    const win = { startedAt: 0, lastAttemptAt: 8_000 }
    expect(shouldAttemptChapterParse(win, 10_000, WINDOW, INTERVAL)).toBe(true)
  })

  it('stops once the window closes, so a chapterless video is not queried forever', () => {
    const win = { startedAt: 0, lastAttemptAt: 0 }
    expect(shouldAttemptChapterParse(win, 30_001, WINDOW, INTERVAL)).toBe(false)
  })
})
