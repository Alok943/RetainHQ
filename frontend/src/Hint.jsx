import React, { useState } from 'react';
import { X } from 'lucide-react';

// One-time contextual hint — the game-tutorial pattern: teach at the moment of
// action, once, then get out of the way. Dismissal is per-hint and permanent
// (localStorage). One accent, no emoji, no rainbow.
export default function Hint({ id, children }) {
  const storageKey = `retainhq_hint_${id}`;
  const [visible, setVisible] = useState(() => localStorage.getItem(storageKey) !== 'done');

  if (!visible) return null;

  const dismiss = () => {
    localStorage.setItem(storageKey, 'done');
    setVisible(false);
  };

  return (
    <div className="flex items-start gap-3 rounded-lg border border-[#0891B2]/25 bg-[#0891B2]/5 px-4 py-3 animate-in fade-in duration-300">
      <p className="flex-1 font-sans text-sm text-[#0F172A] leading-relaxed">{children}</p>
      <button
        onClick={dismiss}
        aria-label="Dismiss hint"
        className="text-[#64748B] hover:text-[#0F172A] transition-colors shrink-0 mt-0.5"
      >
        <X size={14} />
      </button>
    </div>
  );
}
