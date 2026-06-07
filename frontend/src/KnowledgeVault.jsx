import React, { useState, useEffect, useMemo } from 'react';
import { Database, Search, AlertCircle, Plus, Key, Clock, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { apiFetch } from './lib/api';
import ComingSoon from './ComingSoon';

const SOURCE_LABELS = {
  problem: 'Problem', lecture: 'Lecture', video: 'Video', book: 'Book',
  article: 'Article', course: 'Course', project: 'Project', other: 'Other',
};

function nextReviewLabel(nextReviewAt) {
  if (!nextReviewAt) return '—';
  const diffMs = new Date(nextReviewAt) - new Date();
  if (diffMs <= 0) return 'Due now';
  const days = Math.round(diffMs / (1000 * 60 * 60 * 24));
  if (days === 0) return 'Due today';
  return `Next review in ${days} day${days === 1 ? '' : 's'}`;
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
}

function KnowledgeVault() {
  const navigate = useNavigate();
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [query, setQuery] = useState('');
  const [showFeedback, setShowFeedback] = useState(false);

  useEffect(() => {
    apiFetch('/api/activities/')
      .then((data) => setActivities(data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return activities;
    return activities.filter(
      (a) =>
        a.topic.toLowerCase().includes(q) ||
        (a.key_memory && a.key_memory.toLowerCase().includes(q))
    );
  }, [activities, query]);

  return (
    <div className="flex flex-col gap-6 p-4 md:p-8 max-w-4xl mx-auto w-full pb-20 md:pb-8 animate-in fade-in duration-300">

      <header className="mb-1">
        <h2 className="font-sans text-2xl font-semibold text-[#0F172A] flex items-center gap-2">
          <Database size={24} className="text-[#0891B2]" /> Knowledge Vault
        </h2>
        <p className="font-sans text-sm text-[#64748B] mt-1">
          Everything you've captured — the key memories you're working to retain.
        </p>
      </header>

      {/* Search */}
      <div className="relative">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#64748B]" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search topics and key memories…"
          className="w-full pl-9 pr-4 py-3 bg-white border border-[rgba(15,23,42,0.12)] rounded font-sans text-sm text-[#0F172A] focus:outline-none focus:border-[#0891B2] transition-colors placeholder-[#94a3b8]"
        />
      </div>

      {/* States */}
      {loading ? (
        <div className="flex flex-col gap-4">
          {[0, 1, 2].map((i) => (
            <div key={i} className="kinetic-card animate-pulse h-28 bg-white/50" />
          ))}
        </div>
      ) : error ? (
        <div className="kinetic-card flex items-center gap-4 text-[#ba1a1a]">
          <AlertCircle size={20} />
          <p className="font-sans text-sm">Failed to load your vault: {error}</p>
        </div>
      ) : activities.length === 0 ? (
        <div className="kinetic-card flex flex-col items-center text-center gap-3 py-12">
          <Database size={28} className="text-[#94a3b8]" />
          <p className="font-sans font-semibold text-[#0F172A]">Nothing captured yet</p>
          <p className="font-sans text-sm text-[#64748B] max-w-sm">
            Log a learning session and the key memory you want to retain will live here.
          </p>
          <button
            onClick={() => navigate('/log')}
            className="kinetic-btn kinetic-accent-gradient px-6 py-2.5 text-sm mt-1 flex items-center gap-2"
          >
            <Plus size={16} /> Log your first activity
          </button>
        </div>
      ) : filtered.length === 0 ? (
        <p className="font-sans text-sm text-[#64748B] text-center py-8">
          No captures match "{query}".
        </p>
      ) : (
        <div className="flex flex-col gap-4">
          <div className="font-mono text-[11px] text-[#64748B] uppercase tracking-widest">
            {filtered.length} {filtered.length === 1 ? 'capture' : 'captures'}
          </div>
          {filtered.map((a) => (
            <article key={a.id} className="kinetic-card flex flex-col gap-3 bg-white border-[rgba(15,23,42,0.12)]">
              <div className="flex items-start justify-between gap-4">
                <h3 className="font-sans text-lg font-semibold text-[#0F172A] leading-snug">{a.topic}</h3>
                <div className="flex items-center gap-2 shrink-0">
                  {a.source_type && (
                    <span className="font-mono text-[10px] font-bold text-[#0891B2] bg-[rgba(8,145,178,0.1)] px-2 py-1 rounded uppercase tracking-wider">
                      {SOURCE_LABELS[a.source_type] || a.source_type}
                    </span>
                  )}
                  <span className="font-mono text-[10px] font-bold text-[#64748B] bg-[rgba(15,23,42,0.05)] px-2 py-1 rounded uppercase tracking-wider">
                    Difficulty {a.difficulty}/5
                  </span>
                </div>
              </div>

              <div className="bg-[rgba(8,145,178,0.06)] border border-[rgba(8,145,178,0.15)] rounded p-3">
                <div className="font-sans text-[10px] font-bold text-[#0891B2] uppercase tracking-widest mb-1 flex items-center gap-1">
                  <Key size={11} /> Key Memory
                </div>
                <p className="font-sans text-sm text-[#0F172A] leading-relaxed whitespace-pre-wrap">{a.key_memory}</p>
              </div>

              {a.mistake && (
                <div className="flex items-start gap-2">
                  <AlertTriangle size={13} className="text-[#B45309] mt-0.5 shrink-0" />
                  <p className="font-sans text-xs text-[#64748B] italic">"{a.mistake}"</p>
                </div>
              )}

              <div className="flex flex-wrap items-center gap-x-4 gap-y-1 pt-1 font-mono text-[11px] text-[#64748B]">
                <span>Logged {formatDate(a.created_at)}</span>
                <span className="flex items-center gap-1">
                  <Clock size={11} /> {nextReviewLabel(a.next_review_at)}
                </span>
                {a.last_reviewed_at && <span>Last reviewed {formatDate(a.last_reviewed_at)}</span>}
              </div>
            </article>
          ))}
        </div>
      )}

      <ComingSoon
        id="vault-edit-delete"
        title="Edit & Delete"
        description="Edit your key memories and remove entries directly from the Vault."
        onFeedback={() => setShowFeedback(true)}
      />

      {showFeedback && <FeedbackModal onClose={() => setShowFeedback(false)} />}
    </div>
  );
}

function FeedbackModal({ onClose }) {
  const [msg, setMsg] = useState('');
  const [sending, setSending] = useState(false);
  const [done, setDone] = useState(false);

  const send = async () => {
    if (!msg.trim()) return;
    setSending(true);
    try {
      await apiFetch('/api/feedback/', {
        method: 'POST',
        body: JSON.stringify({ message: msg })
      });
      setDone(true);
      setTimeout(onClose, 2000);
    } catch (e) {
      alert("Failed to send feedback: " + e.message);
      setSending(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#131b2e]/40 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-[#f9f9f6] rounded-xl shadow-2xl w-full max-w-md overflow-hidden flex flex-col">
        <div className="p-4 border-b border-[rgba(15,23,42,0.08)] flex justify-between items-center bg-white">
          <h2 className="font-sans font-semibold text-[#0F172A]">Want this feature sooner?</h2>
          <button onClick={onClose} className="text-[#64748B] hover:text-[#0F172A] text-lg font-bold">✕</button>
        </div>
        <div className="p-4 bg-white flex flex-col gap-4">
          {done ? (
            <div className="text-center py-8 text-[#166534] font-medium flex flex-col items-center gap-2">
              <CheckCircle2 size={32} />
              Thanks for your feedback!
            </div>
          ) : (
            <>
              <textarea
                className="w-full border border-[rgba(15,23,42,0.12)] rounded p-3 text-sm focus:outline-none focus:border-[#0891B2] focus:ring-1 focus:ring-[#0891B2] min-h-[120px] resize-y font-sans text-[#0F172A]"
                placeholder="Tell us why this feature matters to you…"
                value={msg}
                onChange={e => setMsg(e.target.value)}
                autoFocus
              />
              <button
                onClick={send}
                disabled={sending || !msg.trim()}
                className="kinetic-btn kinetic-accent-gradient w-full py-2.5 disabled:opacity-50 flex items-center justify-center font-semibold"
              >
                {sending ? 'Sending...' : 'Send Feedback'}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default KnowledgeVault;

