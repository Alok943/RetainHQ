import React, { useState } from 'react';
import { Sparkles, X, MessageSquare } from 'lucide-react';

const DISMISSED_PREFIX = 'retainhq_coming_soon_';

/**
 * A subtle "coming soon" banner for the bottom of pages.
 *
 * Props:
 *   id        — unique key for localStorage dismissal (e.g. "vault-edit")
 *   title     — short feature name (e.g. "Edit & Delete")
 *   description — one-liner explaining the upcoming feature
 *   onFeedback — optional callback to open the feedback modal
 */
export default function ComingSoon({ id, title, description, onFeedback }) {
  const storageKey = `${DISMISSED_PREFIX}${id}`;
  const [visible, setVisible] = useState(() => {
    return !localStorage.getItem(storageKey);
  });

  if (!visible) return null;

  const dismiss = () => {
    setVisible(false);
    localStorage.setItem(storageKey, 'true');
  };

  return (
    <div className="coming-soon-banner">
      <div className="coming-soon-content">
        <div className="coming-soon-icon">
          <Sparkles size={14} />
        </div>
        <div className="coming-soon-text">
          <span className="coming-soon-label">Coming soon</span>
          <span className="coming-soon-title">{title}</span>
          <span className="coming-soon-sep">—</span>
          <span className="coming-soon-desc">{description}</span>
        </div>
      </div>
      <div className="coming-soon-actions">
        {onFeedback && (
          <button className="coming-soon-feedback" onClick={onFeedback}>
            <MessageSquare size={12} />
            Want this sooner?
          </button>
        )}
        <button className="coming-soon-close" onClick={dismiss} aria-label="Dismiss">
          <X size={14} />
        </button>
      </div>
    </div>
  );
}
