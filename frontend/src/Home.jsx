import React, { useState, useEffect } from 'react';
import { Play, AlertCircle, Clock, CheckCircle2, Key, PlusSquare } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { apiFetch } from './lib/api';
import FirstCapture from './FirstCapture';
import { useAuth } from './lib/AuthContext';

// Per-session opt-out: if a new user clicks "I'll look around first", don't re-gate
// them on every Home visit this session (cleared on tab close).
const SKIP_FIRST_CAPTURE_KEY = 'retainhq_skip_first_capture';

function formatDate(iso) {
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

// Honest due-state label (SM-2 intervals are adaptive — the old fixed Day 3/7/14/30
// ladder no longer applies). Reviews returned by /api/reviews/due are always due now
// or overdue.
function getDueLabel(scheduledFor) {
  const days = Math.floor((new Date() - new Date(scheduledFor)) / (1000 * 60 * 60 * 24));
  if (days <= 0) return 'Due now';
  return `Overdue ${days} day${days === 1 ? '' : 's'}`;
}

function Home({ onStartReviews }) {
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState(null);
  const [dueReviews, setDueReviews] = useState([]);
  const [activities, setActivities] = useState([]);
  // Independent loading per section so each paints the moment its own call returns,
  // instead of the whole page waiting on the slowest of three requests.
  const [loadingReviews, setLoadingReviews] = useState(true);
  const [loadingActivities, setLoadingActivities] = useState(true);
  const [loadingDashboard, setLoadingDashboard] = useState(true);
  const [fetchError, setFetchError] = useState(null);
  const { session, requireAuth } = useAuth();
  const [showFeedback, setShowFeedback] = useState(false);
  const [skipFirstCapture, setSkipFirstCapture] = useState(
    () => sessionStorage.getItem(SKIP_FIRST_CAPTURE_KEY) === 'true'
  );

  useEffect(() => {
    if (!session) {
      setLoadingReviews(false);
      setLoadingActivities(false);
      setLoadingDashboard(false);
      return;
    }

    apiFetch('/api/reviews/due')
      .then(setDueReviews)
      .catch((err) => setFetchError(err.message))
      .finally(() => setLoadingReviews(false));

    apiFetch('/api/activities/')
      .then(setActivities)
      .catch(() => {})
      .finally(() => setLoadingActivities(false));

    apiFetch('/api/dashboard/')
      .then(setDashboard)
      .catch(() => {})
      .finally(() => setLoadingDashboard(false));
  }, []);

  const topReview = dueReviews[0] ?? null;

  // First-run gate: a signed-in user with zero activities gets the full-screen
  // first-capture flow instead of an empty dashboard — that's where our funnel
  // shows people bouncing. Guests (no session) still get the normal explorable
  // Home. We wait for the dashboard count so we don't flash the empty dashboard.
  const isFirstRun =
    session && !loadingDashboard && dashboard?.total_activities === 0 && !skipFirstCapture;

  if (isFirstRun) {
    return (
      <FirstCapture
        onSkip={() => {
          sessionStorage.setItem(SKIP_FIRST_CAPTURE_KEY, 'true');
          setSkipFirstCapture(true);
        }}
      />
    );
  }

  return (
    <div className="flex flex-col lg:flex-row gap-8 p-4 md:p-8 max-w-7xl mx-auto w-full pb-20 md:pb-8">

      {/* --- CENTER COLUMN (Main Content) --- */}
      <div className="flex-1 flex flex-col gap-8 min-w-0">

        {/* Stats (mobile/tablet only — desktop shows them in the right rail) */}
        <div className="lg:hidden">
          <QuickStats dashboard={dashboard} loading={loadingDashboard} />
        </div>

        {/* Reviews Due Section */}
        <section>
          {loadingReviews ? (
            <div className="kinetic-card flex flex-col gap-3">
              <div className="skeleton h-3 w-32" />
              <div className="skeleton h-6 w-2/3" />
              <div className="skeleton h-3 w-40" />
              <div className="skeleton h-11 w-44 mt-3 rounded-lg" />
            </div>
          ) : fetchError ? (
            <div className="kinetic-card flex items-center gap-4 text-[#ba1a1a]">
              <AlertCircle size={20} />
              <p className="font-sans text-sm">Failed to load reviews: {fetchError}</p>
            </div>
          ) : !topReview && !loadingActivities && activities.length === 0 ? (
            // Brand-new user: no reviews because nothing's been logged yet.
            // "All caught up" is the wrong message here — point them at the first action.
            <div className="kinetic-card flex flex-col sm:flex-row sm:items-center gap-5">
              <div className="flex-1">
                <p className="font-sans font-semibold text-[#0F172A] text-lg">Capture your first thing to remember</p>
                <p className="font-sans text-sm text-[#64748B] mt-1">Log one thing you've learned — we'll quiz you on it right away, then space out the reviews so it sticks.</p>
              </div>
              <button
                onClick={() => requireAuth(() => navigate('/log'))}
                className="kinetic-btn kinetic-accent-gradient w-full sm:w-auto px-6 py-3.5 shrink-0"
              >
                <PlusSquare size={16} /> Log your first activity
              </button>
            </div>
          ) : !topReview ? (
            <div className="kinetic-card flex items-center gap-4">
              <CheckCircle2 size={24} className="text-[#166534] shrink-0" />
              <div>
                <p className="font-sans font-semibold text-[#0F172A]">You're all caught up!</p>
                <p className="font-sans text-sm text-[#64748B]">No reviews due right now. Keep learning to build momentum.</p>
              </div>
            </div>
          ) : (
            <div className="kinetic-card flex flex-col xl:flex-row gap-6 xl:items-stretch">
              {/* Left Action Area */}
              <div className="flex-1 flex flex-col justify-between">
                <div>
                  <div className="font-sans text-[11px] font-bold text-[#ba1a1a] uppercase tracking-widest mb-1">
                    Highest Priority Review
                  </div>
                  <h3 className="font-sans text-xl md:text-2xl font-semibold text-[#0F172A] leading-tight mb-2">
                    {topReview.activity.topic}
                  </h3>
                  <div className="flex flex-wrap items-center gap-3 mb-4">
                    <p className="font-mono text-xs text-[#64748B] flex items-center gap-1.5">
                      {getDueLabel(topReview.scheduled_for)}
                      <span className="w-1 h-1 rounded-full bg-[#cbd5e1]"></span>
                      <Clock size={12} /> Spaced Review
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => requireAuth(onStartReviews)}
                  className="kinetic-btn kinetic-accent-gradient w-full md:w-48 py-3.5 mt-auto"
                >
                  <Play size={16} fill="currentColor" /> Start Reviews
                </button>
              </div>

              {/* Right Key Memory Area (Desktop Only) */}
              <div className="hidden xl:flex w-[280px] border-l border-[rgba(15,23,42,0.08)] pl-6 flex-col justify-center">
                <div className="font-sans text-[11px] font-bold text-[#0891B2] uppercase tracking-widest mb-2 flex items-center gap-1">
                  <Key size={12} /> Key Memory
                </div>
                <p className="font-sans text-sm text-[#0F172A] italic leading-relaxed bg-[rgba(15,23,42,0.02)] p-3 rounded border border-[rgba(15,23,42,0.05)]">
                  "{topReview.activity.key_memory}"
                </p>
              </div>
            </div>
          )}
        </section>

        {/* Recent Captures — a naked list (no card) so the due-review card stays
            the only elevated element on the page. */}
        <section>
          <div className="flex justify-between items-end mb-4">
            <h2 className="font-sans text-sm font-semibold text-[#1a1c1b]">Recent captures</h2>
            {activities.length > 0 && (
              <button
                onClick={() => navigate('/vault')}
                className="font-sans text-xs font-semibold text-[#0891B2] hover:text-[#0F172A] transition-colors"
              >
                View all →
              </button>
            )}
          </div>

          {loadingActivities ? (
            <div className="flex flex-col gap-5">
              {[0, 1, 2].map((i) => (
                <div key={i} className="flex gap-4 items-start">
                  <div className="skeleton w-6 h-6 rounded-full shrink-0" />
                  <div className="flex-1 flex flex-col gap-2">
                    <div className="skeleton h-3.5 w-1/2" />
                    <div className="skeleton h-3 w-3/4" />
                  </div>
                </div>
              ))}
            </div>
          ) : activities.length > 0 ? (
            <div className="flex flex-col gap-0 relative">
              <div className="absolute left-[11px] top-4 bottom-4 w-px bg-slate-200"></div>
              {activities.slice(0, 4).map((activity, i) => (
                <TimelineItem
                  key={activity.id}
                  icon={<Key size={12} className="text-[#0891B2]" />}
                  title={activity.topic}
                  time={formatDate(activity.created_at)}
                  detail={activity.key_memory}
                  isLast={i === Math.min(activities.length, 4) - 1}
                />
              ))}
            </div>
          ) : (
            <p className="font-sans text-sm text-[#64748B]">
              Nothing captured yet — log an activity to start your vault.
            </p>
          )}

          <p className="font-sans text-sm text-[#64748B] mt-6">
            Want something structured to study?{' '}
            <button
              onClick={() => navigate('/roadmaps')}
              className="font-semibold text-[#0891B2] hover:text-[#0F172A] transition-colors"
            >
              Explore the roadmaps →
            </button>
          </p>
        </section>

        {/* Feedback Link */}
        <section className="mt-4 pt-4 flex justify-center">
          <button 
            onClick={() => setShowFeedback(true)}
            className="text-sm font-medium text-[#64748B] hover:text-[#0F172A] underline underline-offset-4 transition-colors"
          >
            Want to suggest a change? Tell us.
          </button>
        </section>
      </div>

      {/* --- RIGHT RAIL (Visible only on Desktop lg+) --- */}
      <aside className="hidden lg:flex flex-col w-[280px] shrink-0">
        <QuickStats dashboard={dashboard} loading={loadingDashboard} />
      </aside>

      {showFeedback && <FeedbackModal onClose={() => setShowFeedback(false)} />}
    </div>
  );
}

function TimelineItem({ icon, title, time, detail, isLast }) {
  return (
    <div className={`flex gap-4 relative ${isLast ? '' : 'pb-6'}`}>
      <div className="w-6 h-6 rounded-full bg-white border border-slate-200 flex items-center justify-center shrink-0 z-10 mt-0.5">
        {icon}
      </div>
      <div>
        <div className="flex items-baseline gap-2 mb-0.5">
          <span className="font-sans text-sm font-semibold text-[#0F172A]">{title}</span>
          <span className="font-mono text-[10px] text-[#64748B]">{time}</span>
        </div>
        <p className="font-sans text-xs text-[#64748B]">{detail}</p>
      </div>
    </div>
  );
}

function formatUpcoming(iso) {
  const d = new Date(iso);
  const days = Math.ceil((d - new Date()) / (1000 * 60 * 60 * 24));
  if (days <= 0) return 'today';
  if (days === 1) return 'tomorrow';
  if (days < 7) return `in ${days}d`;
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

// Flat stat strip — number + label pairs separated by dividers, no per-stat cards.
// The due-review card is the only elevated element on Home; stats stay quiet.
function QuickStats({ dashboard, loading }) {
  const dueCount = dashboard?.due_count ?? 0;
  const consistency = dashboard?.consistency_window ?? 0;
  const dailyProgress = dashboard?.daily_progress ?? 0;
  const nextReviewAt = dashboard?.next_review_at ?? null;

  const dueValue = loading
    ? '…'
    : dueCount > 0
      ? `${dueCount} due`
      : nextReviewAt
        ? formatUpcoming(nextReviewAt)
        : 'All clear';

  return (
    <div className="flex items-stretch divide-x divide-[rgba(15,23,42,0.08)] border-y border-[rgba(15,23,42,0.08)] py-4">
      <Stat label="Reviews" value={dueValue} emphasis={dueCount > 0} />
      <Stat label="Consistency" value={loading ? '…' : `${consistency}/7d`} />
      <Stat label="Today" value={loading ? '…' : `${dailyProgress}`} />
    </div>
  );
}

function Stat({ label, value, emphasis }) {
  return (
    <div className="flex-1 px-4 first:pl-0 last:pr-0 flex flex-col gap-1">
      <span className={`font-sans text-lg font-semibold leading-none ${emphasis ? 'text-[#ba1a1a]' : 'text-[#0F172A]'}`}>
        {value}
      </span>
      <span className="font-sans text-xs text-[#64748B]">{label}</span>
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
          <h2 className="font-sans font-semibold text-[#0F172A]">Suggest a Change</h2>
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
                placeholder="What needs to be changed or added?"
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

export default Home;
