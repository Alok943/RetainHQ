import { startActivityTracking } from './activity_tracker'
import { storageLocalGet, storageLocalSet, runtimeSendMessage } from '../browser_api'

/**
 * LeetCode solve capture + reflection (SPEC-leetcode-retention.md §4, §4.1).
 *
 * Verdict detection lives in leetcode_probe.ts (MAIN world); this file runs in the
 * isolated world and owns the queue, the reflection panel, and messaging.
 *
 * Ordering note. The spec says the solve is logged "immediately, regardless of
 * reflection". `learning_events` is append-only, so a row written now cannot be
 * enriched later - writing immediately would permanently score every solve with the
 * conservative no-reflection defaults. Instead the solve is queued to
 * chrome.storage.local the instant it is detected, and flushed once reflection is
 * submitted, skipped, or times out (60s). The queue is durable: a pending solve
 * survives navigation, tab close, and browser restart, and is flushed on next load.
 * Nothing is lost, and the user is never blocked - the panel is dismissible and
 * ignoring it still logs the solve.
 */

function getTitle(): string {
  // Try to find LeetCode problem title
  const titleEl = document.querySelector('div.font-medium.text-label-1') ||
                  document.querySelector('[data-cy="question-title"]')

  if (titleEl && titleEl.textContent) {
    return titleEl.textContent.trim()
  }

  // Fallback to URL path
  const match = window.location.pathname.match(/\/problems\/([^/]+)/)
  if (match) {
    return match[1].replace(/-/g, ' ')
  }

  return document.title.replace(' - LeetCode', '')
}

startActivityTracking({
  surface: 'leetcode',
  url_domain: 'leetcode.com',
  getTitle
})

const REFLECT_TIMEOUT_MS = 60_000
const QUEUE_KEY = 'rhq_pending_leetcode_solves'

interface PendingSolve {
  problem_slug: string
  submission_id: string
  occurred_at: string
  confidence?: number
  needed_hint?: boolean
  mistake?: string
}

function currentSlug(): string | null {
  const m = window.location.pathname.match(/\/problems\/([^/]+)/)
  return m ? m[1] : null
}

async function readQueue(): Promise<PendingSolve[]> {
  const got = await storageLocalGet(QUEUE_KEY)
  return (got[QUEUE_KEY] as PendingSolve[]) ?? []
}

async function writeQueue(q: PendingSolve[]): Promise<void> {
  await storageLocalSet({ [QUEUE_KEY]: q })
}

/** Send everything queued, dropping each item only after it is handed off. */
async function flushQueue(): Promise<void> {
  const queue = await readQueue()
  if (!queue.length) return
  const remaining: PendingSolve[] = []
  for (const item of queue) {
    let delivered = false
    try {
      // Drop ONLY on a confirmed 2xx. Signed out, offline, or a 5xx all keep the
      // solve queued for the next flush rather than losing it.
      const res = await runtimeSendMessage<{ ok?: boolean }>({ type: 'LEETCODE_SOLVED', payload: item })
      delivered = res?.ok === true
    } catch {
      delivered = false // service worker asleep
    }
    if (!delivered) remaining.push(item)
  }
  await writeQueue(remaining)
}

async function enqueue(solve: PendingSolve): Promise<void> {
  const queue = await readQueue()
  // Idempotent per submission: the probe patches both fetch and XHR, and LeetCode
  // polls the check endpoint repeatedly until the judge finishes.
  if (queue.some((s) => s.submission_id === solve.submission_id)) return
  queue.push(solve)
  await writeQueue(queue)
}

async function attachReflection(
  submissionId: string,
  patch: Partial<PendingSolve>,
): Promise<void> {
  const queue = await readQueue()
  const item = queue.find((s) => s.submission_id === submissionId)
  if (item) Object.assign(item, patch)
  await writeQueue(queue)
  await flushQueue()
}

// --- reflection panel ----------------------------------------------------
// Rendered in a shadow root so LeetCode's stylesheets cannot affect it, and ours
// cannot affect the page.
function showReflectionPanel(submissionId: string, slug: string): void {
  if (document.getElementById('rhq-reflect-host')) return

  const host = document.createElement('div')
  host.id = 'rhq-reflect-host'
  host.style.cssText = 'position:fixed;bottom:20px;right:20px;z-index:2147483647;'
  const root = host.attachShadow({ mode: 'open' })
  // No interpolation anywhere in this template — AMO's linter (no-unsanitized/property)
  // flags an innerHTML sink the moment it sees a `${}` substitution, even one that's
  // provably a hardcoded literal (the old version's `${n}` from a fixed [1,2,3,4,5]
  // array). The confidence buttons are appended below via createElement/textContent
  // instead, so this string is 100% static and the sink is genuinely safe, not just
  // safe-by-inspection.
  root.innerHTML = `
    <style>
      .card{width:300px;font:13px/1.45 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
        background:#1e1e28;color:#e8e8ef;border:1px solid #35354a;border-radius:12px;
        padding:14px 16px;box-shadow:0 8px 28px rgba(0,0,0,.45);}
      .t{font-weight:600;margin:0 0 2px;font-size:13px}
      .s{color:#9a9ab0;font-size:11px;margin:0 0 12px}
      .l{display:block;color:#b9b9cc;font-size:11px;margin:10px 0 5px}
      .row{display:flex;gap:5px}
      .row button{flex:1;background:#2a2a38;border:1px solid #3d3d52;color:#e8e8ef;
        border-radius:6px;padding:6px 0;cursor:pointer;font-size:12px}
      .row button:hover{background:#34344a}
      .row button[aria-pressed="true"]{background:#4c6ef5;border-color:#4c6ef5;color:#fff}
      input{width:100%;box-sizing:border-box;background:#15151d;border:1px solid #3d3d52;
        color:#e8e8ef;border-radius:6px;padding:7px 9px;font-size:12px;margin-top:2px}
      .actions{display:flex;gap:8px;margin-top:14px}
      .save{flex:1;background:#4c6ef5;border:0;color:#fff;border-radius:6px;padding:8px 0;
        cursor:pointer;font-weight:600;font-size:12px}
      .skip{background:none;border:0;color:#8a8aa0;cursor:pointer;font-size:12px;padding:8px 6px}
    </style>
    <div class="card">
      <p class="t">Solved — 10 seconds of recall?</p>
      <p class="s">Logged either way. This is what makes the review worth doing.</p>
      <label class="l">Confidence</label>
      <div class="row" id="conf"></div>
      <label class="l">Needed a hint?</label>
      <div class="row" id="hint">
        <button data-v="no">No</button><button data-v="yes">Yes</button>
      </div>
      <label class="l">Biggest mistake <span style="color:#6a6a80">(optional)</span></label>
      <input id="mistake" placeholder="forgot to check the empty case" maxlength="200"/>
      <div class="actions">
        <button class="save" id="save">Save</button>
        <button class="skip" id="skip">Skip</button>
      </div>
    </div>`

  const confRow = root.getElementById('conf')!
  for (const n of [1, 2, 3, 4, 5]) {
    const btn = document.createElement('button')
    btn.dataset.v = String(n)
    btn.textContent = String(n)
    confRow.appendChild(btn)
  }

  let confidence: number | undefined
  let neededHint: boolean | undefined

  const pick = (groupId: string, cb: (v: string) => void) => {
    root.getElementById(groupId)?.addEventListener('click', (e) => {
      const btn = (e.target as HTMLElement).closest('button')
      if (!btn) return
      root.querySelectorAll(`#${groupId} button`).forEach((b) =>
        b.setAttribute('aria-pressed', String(b === btn)),
      )
      cb(btn.getAttribute('data-v')!)
    })
  }
  pick('conf', (v) => { confidence = Number(v) })
  pick('hint', (v) => { neededHint = v === 'yes' })

  let done = false
  const close = () => {
    if (done) return
    done = true
    clearTimeout(timer)
    host.remove()
  }

  root.getElementById('save')?.addEventListener('click', () => {
    const mistake = (root.getElementById('mistake') as HTMLInputElement)?.value.trim()
    close()
    void attachReflection(submissionId, {
      confidence,
      needed_hint: neededHint,
      mistake: mistake || undefined,
    })
  })
  root.getElementById('skip')?.addEventListener('click', () => {
    close()
    void flushQueue() // solve still logs, with conservative defaults
  })

  // Ignoring the panel is a valid answer: flush unreflected after the timeout.
  const timer = setTimeout(() => {
    close()
    void flushQueue()
  }, REFLECT_TIMEOUT_MS)

  document.documentElement.appendChild(host)
  console.log(`[RetainHQ] Accepted on ${slug} (submission ${submissionId})`)
}

// --- probe bridge --------------------------------------------------------
window.addEventListener('message', (event) => {
  if (event.source !== window) return
  if (event.origin !== window.location.origin) return
  const d = event.data
  if (!d || d.source !== 'retainhq-leetcode-probe' || !d.submission_id) return

  const slug = currentSlug()
  if (!slug) return

  void (async () => {
    await enqueue({
      problem_slug: slug,
      submission_id: String(d.submission_id),
      occurred_at: new Date().toISOString(),
    })
    showReflectionPanel(String(d.submission_id), slug)
  })()
})

// Anything left over from a previous session goes out now.
void flushQueue()
