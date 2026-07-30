// Manual pause (SPEC follow-up 2026-07-27): tracking is otherwise fully
// automatic, but a surface like Notion mixes personal notes with study
// material and the extension has no way to tell those apart. Rather than
// guess, give the user a single global Start/Pause control in the popup and
// have every content script honor it.
import { storageLocalGet, storageLocalSet } from './browser_api'

const STORAGE_KEY_PAUSED = 'trackingPaused'

export async function isTrackingPaused(): Promise<boolean> {
  const data = await storageLocalGet([STORAGE_KEY_PAUSED])
  return Boolean(data[STORAGE_KEY_PAUSED])
}

export async function setTrackingPaused(paused: boolean): Promise<void> {
  await storageLocalSet({ [STORAGE_KEY_PAUSED]: paused })
}

/** Content scripts run in a separate context from the popup and need to react
 * to a pause toggled mid-session — not just read the flag once at page load. */
export function onTrackingPausedChanged(callback: (paused: boolean) => void): void {
  chrome.storage.onChanged.addListener((changes, area) => {
    if (area === 'local' && STORAGE_KEY_PAUSED in changes) {
      callback(Boolean(changes[STORAGE_KEY_PAUSED].newValue))
    }
  })
}
