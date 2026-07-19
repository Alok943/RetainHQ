import React, { useEffect, useState } from 'react';
import { Bell, X } from 'lucide-react';
import { isPushSupported, subscribePush } from './lib/push';
import {
  shouldShowPushPrompt,
  markPushPromptShown,
  markPushPromptAttempted,
  stopAskingPushPrompt,
} from './lib/pushPrompt';
import { track, EVENTS } from './lib/analytics';

/**
 * Home-screen nudge to turn on review notifications — the Profile toggle alone
 * is too buried to be discovered. Shows at most once per local day and gives up
 * entirely after a couple of ignored native prompts (see lib/pushPrompt.js for
 * why re-asking forever is counterproductive).
 *
 * Soft prompt only: the native permission dialog opens on the button click, so
 * nothing is ever requested on load.
 */
function PushPromptBanner() {
  // Decided once on mount, not on every render — shouldShowPushPrompt() reads
  // localStorage that this component itself writes, so re-evaluating mid-render
  // would hide the card the instant it recorded itself as shown.
  const [visible, setVisible] = useState(() => isPushSupported() && shouldShowPushPrompt());
  const [subscribing, setSubscribing] = useState(false);

  useEffect(() => {
    if (visible) markPushPromptShown();
  }, [visible]);

  if (!visible) return null;

  const enable = async () => {
    setSubscribing(true);
    try {
      await subscribePush();
      track(EVENTS.PUSH_SUBSCRIBED, { source: 'home_banner' });
      stopAskingPushPrompt(); // it's on — never ask again
    } catch {
      // Denied outright, or the native prompt was dismissed. If permission is
      // still 'default' the user walked away rather than deciding; count it so
      // we back off before Chrome embargoes us. An explicit 'denied' means the
      // browser won't prompt again anyway, so stop for good.
      if (Notification.permission === 'default') markPushPromptAttempted();
      else stopAskingPushPrompt();
    } finally {
      setSubscribing(false);
      setVisible(false);
    }
  };

  const dismiss = () => {
    // Soft dismiss: the once-per-day cap already recorded today, so this just
    // closes it. The attempts cap is what eventually stops it for good.
    setVisible(false);
  };

  return (
    <div className="rounded-lg border border-[#0891B2]/25 bg-[#0891B2]/[0.05] p-4 flex items-start gap-3">
      <div className="w-8 h-8 rounded-full bg-[#0891B2]/10 flex items-center justify-center text-[#0891B2] shrink-0">
        <Bell size={15} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-sans text-sm font-semibold text-[#0F172A]">
          Get notified when reviews are due
        </p>
        <p className="font-sans text-xs text-[#64748B] mt-0.5 mb-2.5">
          Same as the daily email, just faster to act on. You can turn it off anytime in Profile.
        </p>
        <button
          onClick={enable}
          disabled={subscribing}
          className="font-sans text-xs font-semibold text-[#0891B2] hover:text-[#0e7490] disabled:opacity-60"
        >
          {subscribing ? 'Enabling…' : 'Turn on notifications'}
        </button>
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

export default PushPromptBanner;
