// Push-only service worker — deliberately hand-rolled, NOT vite-plugin-pwa.
// RetainHQ's SPA is online-only; precaching would invite stale-chunk 404s
// across Vercel deploys. This worker has NO fetch handler, so the network
// path is completely untouched — it exists solely to receive push events.

self.addEventListener('install', () => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('push', (event) => {
  let data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch (e) {
    // Non-JSON payload — fall through to the defaults below.
  }
  const title = data.title || 'RetainHQ';
  const body = data.body || 'You have reviews due.';
  const url = data.url || '/reviews';
  event.waitUntil(
    self.registration.showNotification(title, {
      body,
      icon: '/icon-192.png',
      badge: '/icon-192.png',
      data: { url },
    })
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const url = event.notification.data?.url || '/reviews';
  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clients) => {
      for (const client of clients) {
        if (client.url.includes(self.location.origin) && 'focus' in client) {
          client.navigate(url);
          return client.focus();
        }
      }
      return self.clients.openWindow(url);
    })
  );
});

// The API (Render) is a different origin from this app (Vercel) with no
// rewrite proxy, and a static /public file can't read import.meta.env — so
// push.js stashes the API base URL here (Cache Storage, shared between the
// page and this worker) the first time it registers/subscribes.
async function _apiBase() {
  try {
    const cache = await caches.open('retainhq-sw-config');
    const res = await cache.match('/__sw_config__');
    if (res) return (await res.json()).apiBase;
  } catch (e) {}
  return self.location.origin; // best-effort fallback, likely wrong cross-origin
}

// The browser rotates the push subscription (key rollover, expiry) without
// warning — best-effort resubscribe so the user doesn't silently stop getting
// pushes. NOTE: this fetch has no auth header — a service worker can't reach
// into the page's Supabase session — so it only re-associates the new
// endpoint if the backend ever accepts an unauthenticated re-subscribe for an
// already-known endpoint; today it will 401 and silently drop. That's
// acceptable ("best effort"): the next authenticated page load's
// subscribePush() call re-establishes it properly.
self.addEventListener('pushsubscriptionchange', (event) => {
  event.waitUntil(
    (async () => {
      const apiBase = await _apiBase();
      const sub = await self.registration.pushManager.subscribe(
        event.oldSubscription
          ? { applicationServerKey: event.oldSubscription.options.applicationServerKey, userVisibleOnly: true }
          : undefined
      );
      return fetch(`${apiBase}/api/push/subscribe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(sub.toJSON()),
      }).catch(() => {});
    })()
  );
});
