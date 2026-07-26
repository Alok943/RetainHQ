export interface Segment {
  surface: string
  url_domain: string
  title_metadata: string
  start: number
  end: number
  active: boolean
}

export interface Session {
  session_id: string
  sources: string[]
  title_bag: string
  start: number
  end: number
  duration_min: number
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
}
