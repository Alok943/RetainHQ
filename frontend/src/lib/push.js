// Web Push client — registers the (push-only) service worker and manages the
// PushSubscription lifecycle. All server calls go through apiFetch (auth +
// error handling already centralized there).
import { apiFetch } from './api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export function isPushSupported() {
  return typeof window !== 'undefined' && 'serviceWorker' in navigator && 'PushManager' in window;
}

// unsupported | denied | prompt | subscribed — drives the Profile.jsx toggle
// and the Review.jsx done-screen prompt without either guessing at browser state.
export async function getPushState() {
  if (!isPushSupported()) return 'unsupported';
  if (Notification.permission === 'denied') return 'denied';
  if (Notification.permission !== 'granted') return 'prompt';
  const reg = await navigator.serviceWorker.getRegistration();
  const sub = await reg?.pushManager.getSubscription();
  return sub ? 'subscribed' : 'prompt';
}

// atob-based base64url decode — the standard shim for feeding a VAPID public
// key (base64url string) to PushManager.subscribe's applicationServerKey.
function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const raw = atob(base64);
  return Uint8Array.from([...raw].map((c) => c.charCodeAt(0)));
}

// Stash the API origin where sw.js can read it (Cache Storage — a static
// /public file can't see import.meta.env). See sw.js's pushsubscriptionchange
// handler for why this exists.
async function stashApiBaseForSW() {
  if (!('caches' in window)) return;
  const cache = await caches.open('retainhq-sw-config');
  await cache.put('/__sw_config__', new Response(JSON.stringify({ apiBase: API_BASE_URL })));
}

export async function registerSW() {
  if (!isPushSupported()) return null;
  await stashApiBaseForSW();
  return navigator.serviceWorker.register('/sw.js');
}

export async function subscribePush() {
  if (!isPushSupported()) throw new Error('Push not supported on this browser.');
  const reg = await registerSW();
  const { key } = await apiFetch('/api/push/vapid-public-key');
  const subscription = await reg.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array(key),
  });
  const json = subscription.toJSON();
  await apiFetch('/api/push/subscribe', {
    method: 'POST',
    body: JSON.stringify({
      endpoint: json.endpoint,
      p256dh: json.keys.p256dh,
      auth: json.keys.auth,
      userAgent: navigator.userAgent,
    }),
  });
  return subscription;
}

export async function unsubscribePush() {
  if (!isPushSupported()) return;
  const reg = await navigator.serviceWorker.getRegistration();
  const sub = await reg?.pushManager.getSubscription();
  if (!sub) return;
  const endpoint = sub.endpoint;
  await sub.unsubscribe();
  await apiFetch(`/api/push/subscribe?endpoint=${encodeURIComponent(endpoint)}`, { method: 'DELETE' });
}
