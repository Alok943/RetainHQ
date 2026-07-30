// YouTube only (chapter_extract.ts). `seconds` is a DELTA — how much of this
// chapter was actively watched since the last emit — not a cumulative total,
// unlike `content` below. That's what lets it ride every segment safely,
// checkpointed or closed, with no double-counting risk.
export interface ChapterWatch {
  title: string
  seconds: number
}

export interface Segment {
  surface: string
  url_domain: string
  title_metadata: string
  start: number
  end: number
  active: boolean
  // Cloud-tier only (chat_extract.ts). A snapshot of the currently-mounted
  // conversation at the moment this segment was emitted — NOT incremental —
  // already capped client-side (chat_extract.ts's MAX_TURNS/MAX_TOTAL_CHARS).
  content?: string
  chapters?: ChapterWatch[]
}

export interface Session {
  session_id: string
  sources: string[]
  title_bag: string
  start: number
  end: number
  duration_min: number
  // Picked from whichever segment's snapshot is most complete (stitcher.ts),
  // not concatenated across segments — each snapshot already contains the
  // full conversation as of its own capture time, so joining them would just
  // repeat the same turns many times over.
  content?: string
  // Summed across every segment in the group (stitcher.ts) — the delta
  // semantics above make summing correct, unlike content's pick-the-latest.
  chapters?: ChapterWatch[]
}

export interface CompanionSessionPayload {
  sources: string[]
  study_type?: string
  assistance_level?: string
  confidence_band?: string
  candidates?: any[]
  reason?: string
  title_sample?: string
  classifier?: string
  prompt_version?: string
  embedding_model?: string
}

export interface CompanionSessionIn {
  session_id: string
  node_id?: string
  duration_min: number
  // When the session ended (the stitcher's `end`), NOT when it's synced —
  // sessions batch-sync after offline gaps, and the backend now requires
  // this to place the event on the right day in the evidence log.
  occurred_at: string
  payload: CompanionSessionPayload
  // Transport only — a SIBLING of payload, never nested inside it. Backend
  // schemas/companion.py mirrors this split exactly (payload keeps
  // extra="forbid" and no content field on purpose).
  content?: string
  chapters?: ChapterWatch[]
}
