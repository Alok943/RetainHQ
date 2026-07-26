/**
 * MAIN-world probe. Observes LeetCode's own submission-result traffic and forwards
 * a verdict to the isolated content script via window.postMessage.
 *
 * Why not read the DOM: the previous implementation matched any element whose text
 * was exactly "Accepted". Opening the Submissions tab of a previously-solved problem
 * renders one such row per past accepted run, so it logged solves that never happened -
 * and logged them as T1_verified_external, the highest-trust tier we have. Evidence
 * corruption, not a cosmetic bug.
 *
 * LeetCode polls /submissions/detail/<id>/check/ after a submit. That response is the
 * authoritative verdict and carries the submission id, so it can only fire for a
 * submission made in this tab, right now.
 *
 * This file runs in the page's MAIN world (see manifest) because it must see the page's
 * own fetch/XHR. It never reads page variables, cookies, or user code - only the status
 * line of a request the page already made.
 */
const CHECK_RE = /\/submissions\/detail\/(\d+)\/check\/?/

interface CheckPayload {
  state?: string
  status_msg?: string
  question_id?: number | string
  submission_id?: number | string
}

function report(submissionId: string, body: CheckPayload): void {
  // state SUCCESS means the judge finished; status_msg is the verdict.
  if (body?.state !== 'SUCCESS') return
  if (body?.status_msg !== 'Accepted') return

  window.postMessage(
    {
      source: 'retainhq-leetcode-probe',
      submission_id: String(body.submission_id ?? submissionId),
      question_id: body.question_id != null ? String(body.question_id) : null,
    },
    window.location.origin,
  )
}

// --- fetch ---------------------------------------------------------------
const origFetch = window.fetch
window.fetch = async function (...args: Parameters<typeof fetch>) {
  const res = await origFetch.apply(this, args)
  try {
    const url = typeof args[0] === 'string' ? args[0] : (args[0] as Request)?.url ?? ''
    const m = CHECK_RE.exec(url)
    if (m) {
      // Clone: the page still needs to read this body.
      res.clone().json().then((b) => report(m[1], b)).catch(() => {})
    }
  } catch {
    /* never let instrumentation break the page */
  }
  return res
}

// --- XMLHttpRequest ------------------------------------------------------
const origOpen = XMLHttpRequest.prototype.open
XMLHttpRequest.prototype.open = function (
  this: XMLHttpRequest & { __rhqUrl?: string },
  method: string,
  url: string | URL,
  ...rest: unknown[]
) {
  this.__rhqUrl = String(url)
  // @ts-expect-error - passthrough to the native signature
  return origOpen.call(this, method, url, ...rest)
}

const origSend = XMLHttpRequest.prototype.send
XMLHttpRequest.prototype.send = function (
  this: XMLHttpRequest & { __rhqUrl?: string },
  ...args: unknown[]
) {
  this.addEventListener('load', () => {
    try {
      const m = CHECK_RE.exec(this.__rhqUrl ?? '')
      if (m && this.responseText) report(m[1], JSON.parse(this.responseText))
    } catch {
      /* ignore */
    }
  })
  // @ts-expect-error - passthrough to the native signature
  return origSend.apply(this, args)
}
