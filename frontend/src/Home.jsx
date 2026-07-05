import React, { useState, useEffect } from 'react';
import { ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { apiFetch } from './lib/api';
import FirstCapture from './FirstCapture';
import { useAuth } from './lib/AuthContext';
import { useToast } from './lib/ToastContext';
import ReviewHeatmap from './ReviewHeatmap';
import { CONTENT_KEY_BY_TITLE } from './lib/contentRoadmaps';

// Mirrors RoadmapDetail.jsx's node->lesson slug matching: lesson files are named
// slugify(node title), with exact-title lookup in the manifest as the primary path.
const slugifyTitle = (t) => (t || '').toLowerCase().replace(/&/g, 'and').replace(/\//g, ' ').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
function lessonSlugForNode(slugByTitle, title) {
  if (slugByTitle[title]) return slugByTitle[title];
  const s = slugifyTitle(title);
  return Object.values(slugByTitle).includes(s) ? s : null;
}

// Per-session opt-out: if a new user clicks "I'll look around first", don't re-gate
// them on every Home visit this session (cleared on tab close).
const SKIP_FIRST_CAPTURE_KEY = 'retainhq_skip_first_capture';

function formatDate(iso) {
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

function formatUpcoming(iso) {
  const d = new Date(iso);
  const days = Math.ceil((d - new Date()) / (1000 * 60 * 60 * 24));
  if (days <= 0) return 'today';
  if (days === 1) return 'tomorrow';
  if (days < 7) return `in ${days}d`;
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

// SVG progress ring — used at 48px (due card) and 28px (roadmap tiles).
function ProgressRing({ size, stroke, pct, color = '#0891B2', trackColor = 'var(--color-slate-light)', children }) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const offset = c - (Math.max(0, Math.min(100, pct)) / 100) * c;
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={trackColor} strokeWidth={stroke} />
        <circle
          cx={size / 2} cy={size / 2} r={r} fill="none" stroke={color} strokeWidth={stroke}
          strokeDasharray={c} strokeDashoffset={offset} strokeLinecap="round"
        />
      </svg>
      {children && (
        <div className="absolute inset-0 flex items-center justify-center">
          {children}
        </div>
      )}
    </div>
  );
}

function Home({ onStartReviews }) {
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState(null);
  const [dueReviews, setDueReviews] = useState([]);
  const [activities, setActivities] = useState([]);
  const [roadmaps, setRoadmaps] = useState([]);
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
  const [resumeLesson, setResumeLesson] = useState(null);

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

    apiFetch('/api/roadmaps/', { optionalAuth: true })
      .then((data) => setRoadmaps(Array.isArray(data) ? data : []))
      .catch(() => {});
  }, []);

  const [contentManifest, setContentManifest] = useState(null);
  const [entryCard, setEntryCard] = useState(null);
  const [loadingEntry, setLoadingEntry] = useState(true);

  useEffect(() => {
    fetch('/content/manifest.json')
      .then((r) => r.ok ? r.json() : {})
      .then(setContentManifest)
      .catch(() => setContentManifest({}));
  }, []);

  // Compute entry card ("Continue learning" or "Start learning")
  useEffect(() => {
    if (roadmaps.length === 0 || !contentManifest) {
      if (roadmaps.length === 0 && !loadingDashboard) setLoadingEntry(false);
      return;
    }

    const inProgress = roadmaps.filter((r) => (r.progress_pct ?? 0) > 0 && (r.progress_pct ?? 0) < 100)
      .sort((a, b) => (b.progress_pct ?? 0) - (a.progress_pct ?? 0));

    if (inProgress.length > 0) {
      const topRM = inProgress[0];
      const contentKey = topRM.slug || CONTENT_KEY_BY_TITLE[topRM.title];
      
      apiFetch(`/api/roadmaps/${topRM.slug || topRM.id}`, { optionalAuth: true })
        .then(detail => {
          const slugByTitle = contentManifest[contentKey] || {};
          const nodes = (detail.nodes || []).filter((n) => !n.parent_id);
          const phaseOrder = [];
          nodes.forEach((n) => { if (!phaseOrder.includes(n.phase)) phaseOrder.push(n.phase); });
          const ordered = [...nodes].sort((a, b) => {
            const pd = phaseOrder.indexOf(a.phase) - phaseOrder.indexOf(b.phase);
            return pd !== 0 ? pd : a.order_index - b.order_index;
          });
          const withContent = ordered
            .map((n) => ({ node: n, lessonSlug: lessonSlugForNode(slugByTitle, n.title) }))
            .filter((x) => x.lessonSlug);
            
          const nextIdx = withContent.findIndex((x) => x.node.status !== 'done');
          if (nextIdx !== -1) {
            const next = withContent[nextIdx];
            setEntryCard({
              type: 'continue_lesson',
              roadmapSlug: topRM.slug || topRM.id,
              roadmapTitle: topRM.title,
              lessonSlug: next.lessonSlug,
              lessonTitle: next.node.title,
              phase: next.node.phase,
              contentKey,
              index: nextIdx + 1,
              total: withContent.length,
            });
          } else {
            setEntryCard({ type: 'continue_roadmap', roadmap: topRM });
          }
        })
        .catch(() => {
           setEntryCard({ type: 'continue_roadmap', roadmap: topRM });
        })
        .finally(() => setLoadingEntry(false));
    } else {
      // No roadmap in progress (either 0% or all 100%)
      const contentRoadmaps = roadmaps.filter(rm => {
        const key = rm.slug || CONTENT_KEY_BY_TITLE[rm.title];
        return contentManifest[key] && Object.keys(contentManifest[key]).length > 0;
      });
      if (contentRoadmaps.length > 0) {
        setEntryCard({ type: 'start_learning', roadmaps: contentRoadmaps });
      }
      setLoadingEntry(false);
    }
  }, [roadmaps, contentManifest]);

  // In-progress roadmaps first; fall back to a few starters (0% rings, "EXPLORE")
  // so the section is never empty for a new user.
  const inProgress = roadmaps.filter((r) => (r.progress_pct ?? 0) > 0)
    .sort((a, b) => (b.progress_pct ?? 0) - (a.progress_pct ?? 0));
  const roadmapTiles = (inProgress.length > 0 ? inProgress : roadmaps).slice(0, 4);
  const roadmapsHeading = inProgress.length > 0 ? 'ROADMAPS' : 'EXPLORE';

  const topReview = dueReviews[0] ?? null;
  const dueCount = dashboard?.due_count ?? 0;
  const doneToday = dashboard?.daily_progress ?? 0;
  const consistency = dashboard?.consistency_window ?? 0;
  const totalActivities = dashboard?.total_activities ?? 0;
  const nextReviewAt = dashboard?.next_review_at ?? null;

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

  // Guests (no session at all) and any signed-in user with zero activities: brand-new state.
  const isBrandNew = !session || (!loadingActivities && activities.length === 0);

  return (
    <div className="p-4 md:p-8 max-w-7xl mx-auto w-full pb-20 md:pb-8">
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-5 lg:gap-6 items-start">

        {/* --- MAIN COLUMN --- */}
        <div className="flex flex-col gap-5 min-w-0">

          {/* Due-session card */}
          <section>
            {loadingReviews || loadingDashboard ? (
              <div className="bg-white border border-[rgba(15,23,42,0.08)] rounded-lg p-4 flex items-center gap-4">
                <div className="skeleton w-12 h-12 rounded-full shrink-0" />
                <div className="flex-1 flex flex-col gap-2">
                  <div className="skeleton h-2.5 w-20" />
                  <div className="skeleton h-4 w-2/3" />
                  <div className="skeleton h-2.5 w-16" />
                </div>
                <div className="skeleton h-10 w-24 rounded shrink-0" />
              </div>
            ) : fetchError ? (
              <div className="bg-white border border-[rgba(15,23,42,0.08)] rounded-lg p-4 flex items-center gap-4 text-[#ba1a1a]">
                <span className="font-sans text-sm">Failed to load reviews: {fetchError}</span>
              </div>
            ) : (
              <DueSessionCard
                isBrandNew={isBrandNew}
                topReview={topReview}
                doneToday={doneToday}
                dueCount={dueCount}
                nextReviewAt={nextReviewAt}
                onStart={() => requireAuth(onStartReviews)}
                onLog={() => requireAuth(() => navigate('/log'))}
              />
            )}
          </section>

          {/* Entry card — Resume lesson or Start learning */}
          {entryCard && (
            <section>
              {entryCard.type === 'continue_lesson' && (
                <ResumeLessonCard
                  lesson={entryCard}
                  onClick={() => navigate(
                    `/roadmaps/${entryCard.roadmapSlug}/learn/${entryCard.lessonSlug}`,
                    { state: { contentKey: entryCard.contentKey } }
                  )}
                />
              )}
              {entryCard.type === 'continue_roadmap' && (
                <ContinueRoadmapCard 
                  roadmap={entryCard.roadmap} 
                  onClick={() => navigate(`/roadmaps/${entryCard.roadmap.slug || entryCard.roadmap.id}`)} 
                />
              )}
              {entryCard.type === 'start_learning' && (
                <StartLearningCard 
                  roadmaps={entryCard.roadmaps} 
                  onClickRoadmap={(slug) => navigate(`/roadmaps/${slug}`)} 
                />
              )}
            </section>
          )}

          {/* Review heatmap — primary, full-width */}
          <section>
            <ReviewHeatmap />
          </section>

          {/* Roadmaps grid */}
          <section>
            <div className="micro-label text-[#64748B] text-[11px] font-bold uppercase tracking-widest mb-3">
              {roadmapsHeading}
            </div>
            {roadmaps.length === 0 ? (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {[0, 1, 2, 3].map((i) => (
                  <div key={i} className="bg-white border border-[rgba(15,23,42,0.08)] rounded-lg p-3 flex items-center gap-2.5">
                    <div className="skeleton w-7 h-7 rounded-full shrink-0" />
                    <div className="flex-1 flex flex-col gap-1.5">
                      <div className="skeleton h-3 w-full" />
                      <div className="skeleton h-2.5 w-8" />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {roadmapTiles.map((rm) => (
                  <RoadmapTile key={rm.id} rm={rm} onClick={() => navigate(`/roadmaps/${rm.slug || rm.id}`)} />
                ))}
              </div>
            )}
          </section>

        </div>

        {/* --- RIGHT RAIL --- */}
        <aside className="flex flex-col gap-4 min-w-0">
          <StatStrip
            loading={loadingDashboard}
            dueCount={dueCount}
            doneToday={doneToday}
            consistency={consistency}
            totalActivities={totalActivities}
          />
          <RecentRail
            loading={loadingActivities}
            activities={activities}
            onNavigate={() => navigate('/vault')}
          />
        </aside>
      </div>

      {/* Feedback link — small and muted, bottom of page */}
      <div className="mt-6 flex justify-center">
        <button
          onClick={() => setShowFeedback(true)}
          className="text-xs font-medium text-[#64748B] hover:text-[#0F172A] underline underline-offset-4 transition-colors"
        >
          Suggest a change
        </button>
      </div>

      {showFeedback && <FeedbackModal onClose={() => setShowFeedback(false)} />}
    </div>
  );
}

// Due-session card — the single visual element that tells the user what to do next.
// Three states: brand-new (no activities), all-clear (no due reviews), and due (N due).
function DueSessionCard({ isBrandNew, topReview, doneToday, dueCount, nextReviewAt, onStart, onLog }) {
  if (isBrandNew) {
    return (
      <div className="bg-white border border-[rgba(15,23,42,0.08)] rounded-lg p-4 flex items-center gap-4">
        <ProgressRing size={48} stroke={5} pct={0} color="#0891B2">
          <span className="font-mono text-[10px] font-semibold text-[#0F172A]">0</span>
        </ProgressRing>
        <div className="flex-1 min-w-0">
          <div className="font-sans text-[11px] font-bold text-[#0891B2] uppercase tracking-widest mb-1">
            Get started
          </div>
          <h3 className="font-sans text-lg font-semibold text-[#0F172A] truncate">
            Log your first activity
          </h3>
        </div>
        <button
          onClick={onLog}
          className="kinetic-btn kinetic-accent-gradient px-5 py-2.5 shrink-0"
        >
          Log it
        </button>
      </div>
    );
  }

  if (!topReview) {
    // All clear — full teal ring, no button.
    return (
      <div className="bg-white border border-[rgba(15,23,42,0.08)] rounded-lg p-4 flex items-center gap-4">
        <ProgressRing size={48} stroke={5} pct={100} color="#0F766E">
          <span className="font-mono text-[13px] font-semibold text-[#0F766E]">✓</span>
        </ProgressRing>
        <div className="flex-1 min-w-0">
          <div className="font-sans text-[11px] font-bold text-[#0F766E] uppercase tracking-widest mb-1">
            All clear
          </div>
          <div className="font-mono text-sm text-[#64748B] truncate">
            {nextReviewAt ? `Next review ${formatUpcoming(nextReviewAt)}` : 'Nothing scheduled'}
          </div>
        </div>
      </div>
    );
  }

  const total = doneToday + dueCount;
  const pct = total > 0 ? (doneToday / total) * 100 : 0;
  const minutes = Math.max(1, Math.round(dueCount * 0.7));

  return (
    <div className="bg-white border border-[rgba(15,23,42,0.08)] rounded-lg p-4 flex items-center gap-4">
      <ProgressRing size={48} stroke={5} pct={pct} color="#0891B2">
        <span className="font-mono text-[10px] font-semibold text-[#0F172A]">{doneToday}/{total}</span>
      </ProgressRing>
      <div className="flex-1 min-w-0">
        <div className="font-sans text-[11px] font-bold text-[#ba1a1a] uppercase tracking-widest mb-1">
          Due today
        </div>
        <h3 className="font-sans text-lg font-semibold text-[#0F172A] truncate">
          {topReview.activity.topic}
        </h3>
        <div className="font-mono text-[11px] text-[#64748B] mt-0.5">~{minutes} min</div>
      </div>
      <button
        onClick={onStart}
        className="kinetic-btn kinetic-accent-gradient px-5 py-2.5 shrink-0"
      >
        {doneToday > 0 ? 'Continue' : 'Start'}
      </button>
    </div>
  );
}

// "Continue learning" resume card — see design-system/components/resume-lesson.html.
// One click from Home straight into the next unread lesson in the user's furthest-
// along roadmap; progress bar reflects position among that roadmap's lesson-bearing nodes.
function ResumeLessonCard({ lesson, onClick }) {
  const pct = lesson.total > 0 ? Math.round(((lesson.index - 1) / lesson.total) * 100) : 0;
  return (
    <button onClick={onClick} className="w-full text-left group">
      <div className="bg-white border border-[rgba(15,23,42,0.08)] rounded-lg p-4 flex items-center justify-between gap-4 hover:-translate-y-0.5 transition-transform">
        <div className="min-w-0">
          <div className="font-sans text-[11px] font-bold text-[#0891B2] uppercase tracking-widest mb-1.5">
            Continue learning
          </div>
          <h3 className="font-sans text-base font-semibold text-[#0F172A] truncate mb-1.5">
            {lesson.lessonTitle}
          </h3>
          <p className="font-mono text-[11px] font-medium text-[#64748B]">
            {lesson.roadmapTitle} · {lesson.phase} · lesson {lesson.index} of {lesson.total}
          </p>
        </div>
        <span className="kinetic-btn kinetic-accent-gradient shrink-0 px-4 py-2.5 text-sm">
          Resume <ArrowRight size={14} />
        </span>
      </div>
      <div className="h-[3px] rounded-full bg-[rgba(15,23,42,0.08)] mt-2.5 overflow-hidden">
        <div className="h-full rounded-full bg-[#0891B2] transition-all duration-700" style={{ width: `${pct}%` }} />
      </div>
    </button>
  );
}

function ContinueRoadmapCard({ roadmap, onClick }) {
  const pct = roadmap.progress_pct ?? 0;
  return (
    <button onClick={onClick} className="w-full text-left group">
      <div className="bg-white border border-[rgba(15,23,42,0.08)] rounded-lg p-4 flex items-center justify-between gap-4 hover:-translate-y-0.5 transition-transform">
        <div className="min-w-0">
          <div className="font-sans text-[11px] font-bold text-[#0891B2] uppercase tracking-widest mb-1.5">
            Continue learning
          </div>
          <h3 className="font-sans text-base font-semibold text-[#0F172A] truncate mb-1.5">
            {roadmap.title}
          </h3>
          <p className="font-mono text-[11px] font-medium text-[#64748B]">
            {pct}% complete
          </p>
        </div>
        <span className="kinetic-btn kinetic-accent-gradient shrink-0 px-4 py-2.5 text-sm">
          Resume <ArrowRight size={14} />
        </span>
      </div>
      <div className="h-[3px] rounded-full bg-[rgba(15,23,42,0.08)] mt-2.5 overflow-hidden">
        <div className="h-full rounded-full bg-[#0891B2] transition-all duration-700" style={{ width: `${pct}%` }} />
      </div>
    </button>
  );
}

function StartLearningCard({ roadmaps, onClickRoadmap }) {
  return (
    <div className="bg-white border border-[rgba(15,23,42,0.08)] rounded-lg p-4">
      <div className="font-sans text-[11px] font-bold text-[#0891B2] uppercase tracking-widest mb-3">
        Start learning
      </div>
      <div className="flex flex-col gap-3">
        {roadmaps.map(rm => (
          <button 
            key={rm.id} 
            onClick={() => onClickRoadmap(rm.slug || rm.id)}
            className="flex items-center justify-between text-left p-3 rounded-lg border border-[rgba(15,23,42,0.06)] hover:border-[#0891B2] hover:shadow-[0_2px_8px_-2px_rgba(8,145,178,0.2)] bg-white transition-all group"
          >
            <div className="min-w-0 pr-4">
              <div className="font-sans text-sm font-semibold text-[#0F172A] mb-1">{rm.title}</div>
              <div className="font-sans text-xs text-[#64748B] line-clamp-2">{rm.description}</div>
            </div>
            <div className="w-8 h-8 rounded-full bg-[rgba(8,145,178,0.1)] flex items-center justify-center shrink-0 group-hover:bg-[#0891B2] transition-colors">
              <ArrowRight size={14} className="text-[#0891B2] group-hover:text-white transition-colors" />
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

// Compact roadmap tile: small progress ring + title + pct. No description text.
function RoadmapTile({ rm, onClick }) {
  const pct = rm.progress_pct ?? 0;
  return (
    <button
      onClick={onClick}
      className="bg-white border border-[rgba(15,23,42,0.08)] rounded-lg p-3 flex items-center gap-2.5 text-left hover:-translate-y-0.5 transition-transform"
    >
      <ProgressRing size={28} stroke={3.5} pct={pct} color="#0891B2">
        <span className="font-mono text-[8px] font-semibold text-[#0F172A]">{pct}</span>
      </ProgressRing>
      <div className="flex-1 min-w-0">
        <div className="font-sans text-[13px] font-medium text-[#0F172A] truncate">{rm.title}</div>
        <div className="font-mono text-[11px] text-[#64748B]">{pct}%</div>
      </div>
    </button>
  );
}

// Right-rail vertical stat strip — three stats separated by hairline dividers.
function StatStrip({ loading, dueCount, doneToday, consistency, totalActivities }) {
  const total = doneToday + dueCount;
  const reviewsValue = loading ? '…' : dueCount > 0 ? `${doneToday}/${total} done` : 'All clear';
  return (
    <div className="bg-white border border-[rgba(15,23,42,0.08)] rounded-lg p-4">
      <div className="flex flex-col">
        <StatRow
          value={reviewsValue}
          label="Reviews today"
          emphasis={!loading && dueCount > 0}
          mono={!loading}
        />
        <StatRow value={loading ? '…' : `${consistency}/7d`} label="Consistency" mono />
        <StatRow value={loading ? '…' : `${totalActivities}`} label="Total captured" mono />
      </div>
    </div>
  );
}

function StatRow({ value, label, emphasis, mono, isLast }) {
  return (
    <div className={`py-3 first:pt-0 last:pb-0 last:border-b-0 border-b border-[rgba(15,23,42,0.08)]`}>
      <div className={`text-[20px] font-semibold leading-none mb-0.5 ${mono ? 'font-mono' : 'font-sans'} ${emphasis ? 'text-[#ba1a1a]' : 'text-[#0F172A]'}`}>
        {value}
      </div>
      <div className="font-sans text-xs text-[#64748B]">{label}</div>
    </div>
  );
}

// Right-rail recent captures — up to 3 single-line entries linking to the Vault.
function RecentRail({ loading, activities, onNavigate }) {
  const recent = activities.slice(0, 3);
  return (
    <div className="bg-white border border-[rgba(15,23,42,0.08)] rounded-lg p-4">
      <div className="text-[11px] font-bold uppercase tracking-widest text-[#64748B] mb-2.5">
        Recent
      </div>
      {loading ? (
        <div className="flex flex-col gap-2.5">
          {[0, 1, 2].map((i) => (
            <div key={i} className="flex justify-between gap-2">
              <div className="skeleton h-3 w-3/5" />
              <div className="skeleton h-3 w-10" />
            </div>
          ))}
        </div>
      ) : recent.length === 0 ? (
        <div className="font-sans text-xs text-[#64748B]">No captures yet</div>
      ) : (
        <div className="flex flex-col">
          {recent.map((a, i) => (
            <button
              key={a.id}
              onClick={onNavigate}
              className={`flex items-baseline gap-2 py-2 first:pt-0 last:pb-0 last:border-b-0 border-b border-[rgba(15,23,42,0.08)] text-left w-full ${i === recent.length - 1 ? 'border-b-0' : ''}`}
            >
              <span className="font-sans text-[13px] text-[#0F172A] truncate flex-1 min-w-0">{a.topic}</span>
              <span className="font-mono text-[10px] text-[#64748B] shrink-0">{formatDate(a.created_at)}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function FeedbackModal({ onClose }) {
  const [msg, setMsg] = useState('');
  const [sending, setSending] = useState(false);
  const [done, setDone] = useState(false);
  const toast = useToast();

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
      toast.error(`Couldn't send feedback: ${e.message}`);
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
