import React, { useState } from 'react';
import { Puzzle, X } from 'lucide-react';
import { Link } from 'react-router-dom';

// Dismiss persists across sessions (unlike PushPromptBanner's once-per-day cap) —
// installing a browser extension is a one-time decision, not something worth
// re-asking. Two placements (Home, Career Coach) share one dismiss key so
// closing it in either spot closes it everywhere.
const DISMISS_KEY = 'retainhq_companion_banner_dismissed';

function CompanionInstallBanner() {
  const [dismissed, setDismissed] = useState(
    () => localStorage.getItem(DISMISS_KEY) === 'true'
  );

  if (dismissed) return null;

  const dismiss = () => {
    localStorage.setItem(DISMISS_KEY, 'true');
    setDismissed(true);
  };

  return (
    <div className="rounded-lg border border-[#0891B2]/25 bg-[#0891B2]/[0.05] p-4 flex items-start gap-3">
      <div className="w-8 h-8 rounded-full bg-[#0891B2]/10 flex items-center justify-center text-[#0891B2] shrink-0">
        <Puzzle size={15} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-sans text-sm font-semibold text-[#0F172A]">
          Install RetainHQ Companion
        </p>
        <p className="font-sans text-xs text-[#64748B] mt-0.5 mb-2.5">
          Automatically tracks LeetCode solves, YouTube, and course time — Firefox only, for now.
        </p>
        <Link
          to="/privacy/companion"
          className="font-sans text-xs font-semibold text-[#0891B2] hover:text-[#0e7490]"
        >
          Get the extension
        </Link>
      </div>
      <button
        onClick={dismiss}
        aria-label="Dismiss"
        className="shrink-0 text-[#64748B] hover:text-[#0F172A]"
      >
        <X size={14} />
      </button>
    </div>
  );
}

export default CompanionInstallBanner;
