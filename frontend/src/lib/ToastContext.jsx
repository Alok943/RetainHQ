import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react';
import { AlertCircle, CheckCircle2, WifiOff, X } from 'lucide-react';
import { subscribeToast } from './toastBus';

const ToastCtx = createContext(null);
let idSeq = 0;

const ICONS = { error: AlertCircle, offline: WifiOff, success: CheckCircle2, info: AlertCircle };
const ICON_COLOR = {
  error: 'text-[#ba1a1a]',
  offline: 'text-[#B45309]',
  success: 'text-[#166534]',
  info: 'text-[#0891B2]',
};

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const dismiss = useCallback((id) => {
    setToasts((t) => t.filter((x) => x.id !== id));
  }, []);

  const push = useCallback((toast) => {
    const id = ++idSeq;
    const entry = { id, type: 'info', ...toast };
    setToasts((t) => [...t, entry]);
    const duration = toast.duration ?? (entry.type === 'success' ? 3500 : 6000);
    if (duration) setTimeout(() => dismiss(id), duration);
    return id;
  }, [dismiss]);

  // api.js (and anywhere else outside React) triggers toasts through this bus.
  useEffect(() => subscribeToast(push), [push]);

  const api = useRef({
    show: push,
    error: (message, opts) => push({ type: 'error', message, ...opts }),
    success: (message, opts) => push({ type: 'success', message, ...opts }),
    info: (message, opts) => push({ type: 'info', message, ...opts }),
    dismiss,
  }).current;

  return (
    <ToastCtx.Provider value={api}>
      {children}
      <div className="fixed bottom-4 right-4 left-4 sm:left-auto z-[200] flex flex-col gap-2 sm:max-w-sm sm:w-96 pointer-events-none">
        {toasts.map((t) => (
          <Toast key={t.id} toast={t} onDismiss={() => dismiss(t.id)} />
        ))}
      </div>
    </ToastCtx.Provider>
  );
}

function Toast({ toast, onDismiss }) {
  const { type, message, action } = toast;
  const Icon = ICONS[type] || ICONS.info;
  return (
    <div className="pointer-events-auto flex items-start gap-3 bg-white border border-[rgba(15,23,42,0.1)] rounded-xl shadow-lg px-4 py-3 animate-in fade-in slide-in-from-bottom-2 duration-200">
      <Icon size={18} className={`shrink-0 mt-0.5 ${ICON_COLOR[type] || ICON_COLOR.info}`} />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-[#0F172A] leading-snug">{message}</p>
        {action && (
          <button
            onClick={() => { action.onClick(); onDismiss(); }}
            className="mt-1.5 text-xs font-semibold text-[#0891B2] hover:text-[#06B6D4]"
          >
            {action.label}
          </button>
        )}
      </div>
      <button onClick={onDismiss} aria-label="Dismiss" className="shrink-0 text-[#64748B] hover:text-[#0F172A]">
        <X size={16} />
      </button>
    </div>
  );
}

export function useToast() {
  const ctx = useContext(ToastCtx);
  if (!ctx) throw new Error('useToast must be used within a ToastProvider');
  return ctx;
}
