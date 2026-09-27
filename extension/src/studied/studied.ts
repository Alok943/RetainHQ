// "What I've studied" (docs/SPEC-core-loop-v2.md Phase 4) — the extension's
// only view of per-session study history. Reads src/lib/session_store.ts's
// IndexedDB directly; nothing here talks to the network or the backend.
import { getAllSessions, deleteSession, deleteAllSessions, type StudySessionRecord } from '../lib/session_store'
import { surfaceLabel } from '../lib/format'

type GroupMode = 'day' | 'surface' | 'topic'

const listEl = document.getElementById('list') as HTMLDivElement
const subtitleEl = document.getElementById('subtitle') as HTMLParagraphElement
const clearAllBtn = document.getElementById('clearAllBtn') as HTMLButtonElement
const tabs = Array.from(document.querySelectorAll<HTMLButtonElement>('.tab'))

let currentGroup: GroupMode = 'day'
let allSessions: StudySessionRecord[] = []

function formatMinutes(mins: number): string {
  if (mins < 60) return `${mins} min`
  const h = Math.floor(mins / 60)
  const m = mins % 60
  return m > 0 ? `${h}h ${m}m` : `${h}h`
}

function dayLabel(ms: number): string {
  const d = new Date(ms)
  const today = new Date()
  const yesterday = new Date(Date.now() - 86400000)
  const sameDay = (a: Date, b: Date) => a.toDateString() === b.toDateString()
  if (sameDay(d, today)) return 'Today'
  if (sameDay(d, yesterday)) return 'Yesterday'
  return d.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })
}

function timeLabel(ms: number): string {
  return new Date(ms).toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' })
}

function groupKey(session: StudySessionRecord, mode: GroupMode): string {
  if (mode === 'day') return new Date(session.startedAt).toDateString()
  if (mode === 'surface') return surfaceLabel(session.sources[0] ?? 'unknown')
  return session.topicLabel ?? 'Not yet matched to a topic'
}

function render(): void {
  const groups = new Map<string, StudySessionRecord[]>()
  for (const session of allSessions) {
    const key = groupKey(session, currentGroup)
    if (!groups.has(key)) groups.set(key, [])
    groups.get(key)!.push(session)
  }

  let orderedKeys = [...groups.keys()]
  if (currentGroup === 'day') {
    orderedKeys.sort((a, b) => groups.get(b)![0].startedAt - groups.get(a)![0].startedAt)
  } else {
    orderedKeys.sort((a, b) => {
      const totalA = groups.get(a)!.reduce((n, s) => n + s.durationMin, 0)
      const totalB = groups.get(b)!.reduce((n, s) => n + s.durationMin, 0)
      return totalB - totalA
    })
  }

  listEl.innerHTML = ''

  if (orderedKeys.length === 0) {
    listEl.innerHTML = `
      <div class="empty">
        <p><strong>Nothing recorded yet.</strong></p>
        <p>Once the companion tracks a study session, it shows up here.</p>
      </div>
    `
    return
  }

  for (const key of orderedKeys) {
    const sessions = groups.get(key)!.sort((a, b) => b.startedAt - a.startedAt)
    const totalMin = sessions.reduce((n, s) => n + s.durationMin, 0)

    const groupEl = document.createElement('div')
    groupEl.className = 'group'

    const label = document.createElement('div')
    label.className = 'group-label'
    label.innerHTML = `<span>${currentGroup === 'day' ? dayLabel(sessions[0].startedAt) : escapeHtml(key)}</span><span class="group-total">${formatMinutes(totalMin)}</span>`
    groupEl.appendChild(label)

    for (const session of sessions) {
      groupEl.appendChild(renderCard(session))
    }
    listEl.appendChild(groupEl)
  }
}

function renderCard(session: StudySessionRecord): HTMLDivElement {
  const card = document.createElement('div')
  card.className = 'card'

  const info = document.createElement('div')
  info.className = 'info'
  const title = document.createElement('div')
  title.className = 'title'
  title.textContent = session.title || session.sources.map(surfaceLabel).join(', ') || 'Untitled session'
  const meta = document.createElement('div')
  meta.className = 'meta'
  const sourceText = session.sources.map(surfaceLabel).join(', ')
  meta.textContent = `${sourceText} · ${formatMinutes(session.durationMin)} · ${timeLabel(session.startedAt)}`
  info.appendChild(title)
  info.appendChild(meta)
  card.appendChild(info)

  if (session.syncStatus !== 'synced') {
    const badge = document.createElement('span')
    badge.className = `badge ${session.syncStatus}`
    badge.textContent = session.syncStatus === 'pending' ? 'Syncing' : 'Not synced'
    card.appendChild(badge)
  }

  const delBtn = document.createElement('button')
  delBtn.className = 'del-btn'
  delBtn.type = 'button'
  delBtn.setAttribute('aria-label', 'Delete this session from local history')
  delBtn.textContent = '×'
  delBtn.addEventListener('click', async () => {
    await deleteSession(session.id)
    allSessions = allSessions.filter((s) => s.id !== session.id)
    render()
    renderSubtitle()
  })
  card.appendChild(delBtn)

  return card
}

function escapeHtml(s: string): string {
  const div = document.createElement('div')
  div.textContent = s
  return div.innerHTML
}

function renderSubtitle(): void {
  const totalMin = allSessions.reduce((n, s) => n + s.durationMin, 0)
  const days = new Set(allSessions.map((s) => new Date(s.startedAt).toDateString())).size
  subtitleEl.textContent = allSessions.length === 0
    ? 'No study sessions recorded yet on this browser.'
    : `${formatMinutes(totalMin)} across ${allSessions.length} session${allSessions.length === 1 ? '' : 's'}, over ${days} day${days === 1 ? '' : 's'}.`
}

async function load(): Promise<void> {
  allSessions = await getAllSessions()
  renderSubtitle()
  render()
}

tabs.forEach((tab) => {
  tab.addEventListener('click', () => {
    tabs.forEach((t) => t.setAttribute('aria-selected', String(t === tab)))
    currentGroup = tab.dataset.group as GroupMode
    render()
  })
})

clearAllBtn.addEventListener('click', async () => {
  if (allSessions.length === 0) return
  if (!confirm('Delete all locally stored study history on this browser? This cannot be undone. (Already-synced evidence on the server is not affected.)')) return
  await deleteAllSessions()
  allSessions = []
  renderSubtitle()
  render()
})

load()
