// Local-first study history (docs/SPEC-core-loop-v2.md Phase 4, first
// increment — see DECISIONS.md). This is the ONLY place per-session detail
// is kept now: the server still receives full session payloads exactly as
// before (that contract change is a separate, later step), but nothing reads
// it back for display — every session this extension has ever tracked lives
// here, in this browser's IndexedDB, until it ages out.
//
// Deliberately NOT chrome.storage.local: that's a single JSON blob capped at
// ~10MB and awkward to query/range-scan, fine for the small transient
// segmentBuffer/syncQueue but not for months of history. IndexedDB gives a
// real index on `createdAt` for cheap retention eviction and range queries.

export type SyncStatus = 'pending' | 'synced' | 'failed'

export interface StudySessionRecord {
  id: string // = session_id (uuid), primary key
  sources: string[]
  title: string
  startedAt: number // epoch ms
  endedAt: number
  durationMin: number
  syncStatus: SyncStatus
  // Filled in later, if/when the server tells us (it doesn't yet — see the
  // comment above). Null means "no topic resolved for this session."
  topicLabel: string | null
  createdAt: number // = endedAt; the retention/eviction key
}

const DB_NAME = 'retainhq-companion'
const DB_VERSION = 1
const STORE = 'sessions'
const CREATED_AT_INDEX = 'createdAt'

// SPEC default (docs/SPEC-core-loop-v2.md Phase 4 item 1) — oldest-first
// eviction beyond either bound, whichever it hits first.
const RETENTION_DAYS = 90
const MAX_RECORDS = 5000

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION)
    req.onupgradeneeded = () => {
      const db = req.result
      if (!db.objectStoreNames.contains(STORE)) {
        const store = db.createObjectStore(STORE, { keyPath: 'id' })
        store.createIndex(CREATED_AT_INDEX, CREATED_AT_INDEX)
      }
    }
    req.onsuccess = () => resolve(req.result)
    req.onerror = () => reject(req.error)
  })
}

// Every call opens and closes its own connection rather than holding one
// open — this runs inside a service worker that can be evicted between
// calls at any time, so there's no lifecycle to safely cache a connection in.
async function withStore<T>(mode: IDBTransactionMode, fn: (store: IDBObjectStore) => IDBRequest<T> | void): Promise<T | undefined> {
  const db = await openDb()
  try {
    return await new Promise<T | undefined>((resolve, reject) => {
      const tx = db.transaction(STORE, mode)
      const store = tx.objectStore(STORE)
      const req = fn(store)
      tx.onerror = () => reject(tx.error)
      tx.oncomplete = () => resolve(req ? (req.result as T) : undefined)
    })
  } finally {
    db.close()
  }
}

export async function addSession(record: StudySessionRecord): Promise<void> {
  await withStore('readwrite', (store) => store.put(record))
  // Fire-and-forget — a write must never fail because eviction did.
  evictOldSessions().catch((err) => console.error('[RetainHQ] session_store eviction failed', err))
}

export async function markSessionsSyncStatus(ids: string[], status: SyncStatus): Promise<void> {
  if (ids.length === 0) return
  const db = await openDb()
  try {
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction(STORE, 'readwrite')
      const store = tx.objectStore(STORE)
      for (const id of ids) {
        const getReq = store.get(id)
        getReq.onsuccess = () => {
          const existing = getReq.result as StudySessionRecord | undefined
          if (existing) store.put({ ...existing, syncStatus: status })
        }
      }
      tx.onerror = () => reject(tx.error)
      tx.oncomplete = () => resolve()
    })
  } finally {
    db.close()
  }
}

export async function getAllSessions(): Promise<StudySessionRecord[]> {
  const records = (await withStore<StudySessionRecord[]>('readonly', (store) => store.getAll())) || []
  return records.sort((a, b) => b.startedAt - a.startedAt)
}

export async function deleteSession(id: string): Promise<void> {
  await withStore('readwrite', (store) => store.delete(id))
}

export async function deleteAllSessions(): Promise<void> {
  await withStore('readwrite', (store) => store.clear())
}

export async function evictOldSessions(): Promise<void> {
  const cutoff = Date.now() - RETENTION_DAYS * 24 * 60 * 60 * 1000
  const db = await openDb()
  try {
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction(STORE, 'readwrite')
      const store = tx.objectStore(STORE)
      const index = store.index(CREATED_AT_INDEX)
      const cursorReq = index.openCursor(IDBKeyRange.upperBound(cutoff))
      cursorReq.onsuccess = () => {
        const cursor = cursorReq.result
        if (cursor) {
          store.delete(cursor.primaryKey)
          cursor.continue()
        }
      }
      tx.onerror = () => reject(tx.error)
      tx.oncomplete = () => resolve()
    })
  } finally {
    db.close()
  }

  // Size cap as a second pass: IndexedDB has no single-query "keep only the
  // newest N" op, and this only ever needs to trim a LITTLE past the cap
  // (age-based eviction above already does most of the work), so reading
  // everything once here is cheap relative to a real query planner.
  const all = await getAllSessions() // newest-first
  if (all.length > MAX_RECORDS) {
    const overflow = all.slice(MAX_RECORDS)
    const db2 = await openDb()
    try {
      await new Promise<void>((resolve, reject) => {
        const tx = db2.transaction(STORE, 'readwrite')
        const store = tx.objectStore(STORE)
        for (const rec of overflow) store.delete(rec.id)
        tx.onerror = () => reject(tx.error)
        tx.oncomplete = () => resolve()
      })
    } finally {
      db2.close()
    }
  }
}
