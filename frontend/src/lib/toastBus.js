// Tiny pub-sub so non-React modules (api.js) can trigger toasts without
// prop-drilling a hook through every call site. ToastProvider subscribes on
// mount; emitToast is safe to call before any provider exists (no-op).
let listeners = [];

export function subscribeToast(fn) {
  listeners.push(fn);
  return () => {
    listeners = listeners.filter((l) => l !== fn);
  };
}

export function emitToast(toast) {
  listeners.forEach((fn) => fn(toast));
}
