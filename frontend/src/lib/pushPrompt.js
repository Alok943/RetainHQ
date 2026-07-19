// Frequency policy for the soft "turn on notifications" card on Home.
//
// This is a SOFT prompt — an in-app card. It only triggers the browser's native
// permission prompt when the user actually clicks "Turn on". That distinction is
// what keeps the never-prompt-on-load rule (HANDOFF B2) intact.
//
// Why the caps exist: Chrome embargoes a site's notification permission after
// ~3 dismissals of the NATIVE prompt, and its "quieter permissions" heuristic
// suppresses prompts site-wide for domains with low grant rates. So re-asking
// forever is worse than not asking — it can permanently burn the ability to ask
// anyone. Hence: at most once per (local) day, and we stop entirely after a
// couple of ignored native prompts.

const DISMISSED_KEY = 'retainhq_push_prompt_dismissed';    // '1' = never ask again
const LAST_SHOWN_KEY = 'retainhq_push_prompt_last_shown';  // 'YYYY-MM-DD' (local)
const ATTEMPTS_KEY = 'retainhq_push_prompt_attempts';      // native prompts we triggered

// How many times the user may see the native prompt and walk away before we stop.
// Kept under Chrome's ~3-dismissal embargo threshold on purpose.
const MAX_NATIVE_ATTEMPTS = 2;

// Local calendar day, not UTC — a UTC day boundary lands at 05:30 IST, which
// would roll "today" over mid-morning for the user.
function todayLocal() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

// localStorage throws in Safari private mode / when storage is blocked. A prompt
// is never important enough to break a render, so every access degrades to "don't
// show" rather than propagating.
function read(key) {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function write(key, value) {
  try {
    localStorage.setItem(key, value);
  } catch {
    /* storage blocked — the prompt just won't be rate-limited this session */
  }
}

export function shouldShowPushPrompt() {
  if (typeof window === 'undefined' || !('Notification' in window)) return false;
  // 'granted' → already on (ensureSubscribed keeps it live).
  // 'denied'  → the browser will not show a prompt at all, so asking is pointless.
  if (Notification.permission !== 'default') return false;
  if (read(DISMISSED_KEY) === '1') return false;
  if (Number(read(ATTEMPTS_KEY) || 0) >= MAX_NATIVE_ATTEMPTS) return false;
  return read(LAST_SHOWN_KEY) !== todayLocal();
}

// Called when the card actually renders — starts the once-per-day clock.
export function markPushPromptShown() {
  write(LAST_SHOWN_KEY, todayLocal());
}

// Called after the native prompt closed without a grant (permission still
// 'default' = the user dismissed it). Two of these and we stop asking for good.
export function markPushPromptAttempted() {
  write(ATTEMPTS_KEY, String(Number(read(ATTEMPTS_KEY) || 0) + 1));
}

// Permanent opt-out: an explicit "don't ask again", or a successful subscribe.
export function stopAskingPushPrompt() {
  write(DISMISSED_KEY, '1');
}
