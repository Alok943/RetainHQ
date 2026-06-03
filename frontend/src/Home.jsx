import React, { useState, useEffect } from 'react';
import { Play, TrendingUp, BookOpen, AlertCircle, Clock, Activity, Target, CheckCircle2, History, Database, Key } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { apiFetch } from './lib/api';

function getReviewDayLabel(scheduledFor, activityCreatedAt) {
  const diffDays = Math.round(
    (new Date(scheduledFor) - new Date(activityCreatedAt)) / (1000 * 60 * 60 * 24)
  );
  if (diffDays <= 5) return 'Day 3 Review';
  if (diffDays <= 10) return 'Day 7 Review';
  if (diffDays <= 20) return 'Day 14 Review';
  return 'Day 30 Review';
}

function Home({ onStartReviews }) {
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState(null);
  const [dueReviews, setDueReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState(null);

  useEffect(() => {
    Promise.all([
      apiFetch('/api/dashboard/'),
      apiFetch('/api/reviews/due'),
    ])
      .then(([dashData, reviewsData]) => {
        setDashboard(dashData);
        setDueReviews(reviewsData);
      })
      .catch((err) => setFetchError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const topReview = dueReviews[0] ?? null;

  return (
    <div className="flex flex-col lg:flex-row gap-8 p-4 md:p-8 max-w-7xl mx-auto w-full pb-20 md:pb-8">

      {/* --- CENTER COLUMN (Main Content) --- */}
      <div className="flex-1 flex flex-col gap-8 min-w-0">

        {/* Momentum & Stats (Visible on Mobile/Tablet, Hidden on Desktop where Right Rail takes over) */}
        <div className="flex flex-col gap-6 lg:hidden">
          <MomentumCard />
          <QuickStats dashboard={dashboard} loading={loading} />
        </div>

        {/* Reviews Due Section (Action Required) */}
        <section>
          <div className="flex justify-between items-end mb-4">
            <h2 className="font-sans text-sm font-semibold text-[#1a1c1b] uppercase tracking-wider flex items-center gap-1.5">
              <AlertCircle size={16} className="text-[#ba1a1a]" /> Action Required
              {!loading && dueReviews.length > 0 && (
                <span className="font-mono text-[10px] font-bold text-[#ba1a1a] bg-[#ba1a1a]/10 px-2 py-0.5 rounded-full ml-1">
                  {dueReviews.length} due
                </span>
              )}
            </h2>
          </div>

          {loading ? (
            <div className="kinetic-card animate-pulse h-32 bg-white/50" />
          ) : fetchError ? (
            <div className="kinetic-card flex items-center gap-4 text-[#ba1a1a]">
              <AlertCircle size={20} />
              <p className="font-sans text-sm">Failed to load reviews: {fetchError}</p>
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
                      {getReviewDayLabel(topReview.scheduled_for, topReview.activity.created_at)}
                      <span className="w-1 h-1 rounded-full bg-[#cbd5e1]"></span>
                      <Clock size={12} /> Spaced Review
                    </p>
                  </div>
                </div>
                <button
                  onClick={onStartReviews}
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

        {/* Suggested Learning — static placeholder until Phase 2 */}
        <section>
          <div className="flex justify-between items-end mb-4">
            <h2 className="font-sans text-sm font-semibold text-[#1a1c1b] uppercase tracking-wider flex items-center gap-1.5">
              <BookOpen size={16} className="text-[#0891B2]" /> Suggested Focus
            </h2>
          </div>

          <div className="kinetic-card flex flex-col md:flex-row md:items-center gap-6">
            <div className="flex-1">
              <h3 className="font-sans text-lg font-semibold text-[#0F172A]">Explore Your Roadmap</h3>
              <p className="font-sans text-sm text-[#64748B] mt-1.5 leading-relaxed max-w-xl">
                Track your learning progress through structured roadmaps. Mark topics as complete and follow the path to mastery.
              </p>
            </div>
            <div className="w-full md:w-auto shrink-0">
              <button
                onClick={() => navigate('/roadmaps')}
                className="kinetic-btn bg-white text-[#0F172A] border border-[rgba(15,23,42,0.12)] w-full md:w-40 hover:bg-gray-50 text-sm"
              >
                View Roadmap
              </button>
            </div>
          </div>
        </section>

        {/* Recent Activity — placeholder until activities list endpoint is available */}
        <section>
          <div className="flex justify-between items-end mb-4">
            <h2 className="font-sans text-sm font-semibold text-[#1a1c1b] uppercase tracking-wider flex items-center gap-1.5">
              <Activity size={16} className="text-[#0F172A]" /> Recent Activity
            </h2>
          </div>

          <div className="kinetic-card">
            {loading ? (
              <div className="animate-pulse space-y-4">
                <div className="h-4 bg-slate-100 rounded w-3/4" />
                <div className="h-4 bg-slate-100 rounded w-1/2" />
              </div>
            ) : dueReviews.length > 0 ? (
              <div className="flex flex-col gap-0 relative">
                <div className="absolute left-[11px] top-4 bottom-4 w-px bg-slate-200"></div>
                {dueReviews.slice(0, 3).map((review, i) => (
                  <TimelineItem
                    key={review.id}
                    icon={<Clock size={12} className="text-[#ba1a1a]" />}
                    title={`Due: ${review.activity.topic}`}
                    time={getReviewDayLabel(review.scheduled_for, review.activity.created_at)}
                    detail={review.activity.key_memory}
                    isLast={i === Math.min(dueReviews.length, 3) - 1}
                  />
                ))}
              </div>
            ) : (
              <p className="font-sans text-sm text-[#64748B]">
                No pending reviews — log an activity to start building your history.
              </p>
            )}
          </div>
        </section>
      </div>

      {/* --- RIGHT RAIL (Visible only on Desktop lg+) --- */}
      <aside className="hidden lg:flex flex-col w-[320px] shrink-0 gap-6">
        <MomentumCard />
        <QuickStats dashboard={dashboard} loading={loading} />
      </aside>

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

function MomentumCard() {
  return (
    <div className="kinetic-card border-l-2 border-l-[#0891B2] flex flex-col gap-4 bg-[#131b2e] border-[#131b2e]">
      <div className="flex justify-between items-start">
        <h3 className="font-sans text-xs font-semibold text-[#7c839b] uppercase tracking-widest">Learning Momentum</h3>
        <span className="font-sans text-[10px] font-bold text-[#0891B2] bg-[#0891B2]/20 px-2 py-0.5 rounded-full flex items-center gap-1 tracking-normal border border-[#0891B2]/30 uppercase">
          <TrendingUp size={10} /> Coming Soon
        </span>
      </div>

      <div className="flex items-center gap-6 mt-2">
        <div className="relative w-20 h-20 flex items-center justify-center shrink-0">
          <svg className="w-full h-full -rotate-90 transform" viewBox="0 0 36 36">
            <path
              className="text-[#1e293b]"
              stroke="currentColor"
              strokeWidth="2.5"
              fill="none"
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
            />
            <path
              className="text-[#0891B2]"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              fill="none"
              strokeDasharray="0, 100"
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center font-mono text-sm font-medium text-[#7c839b] tracking-tighter">
            —
          </div>
        </div>

        <div className="flex flex-col gap-1">
          <div className="font-mono text-sm text-[#7c839b] flex items-center gap-1 font-semibold">
            Phase 2
          </div>
          <div className="font-sans text-xs text-[#7c839b]">
            Adaptive scoring coming soon
          </div>
        </div>
      </div>
    </div>
  );
}

function QuickStats({ dashboard, loading }) {
  const dueCount = dashboard?.due_count ?? 0;
  const consistency = dashboard?.consistency_window ?? 0;
  const dailyProgress = dashboard?.daily_progress ?? 0;

  return (
    <div className="flex flex-col gap-3">
      {/* Consistency Window */}
      <div className="kinetic-card py-3 px-4 flex justify-between items-center bg-white shadow-sm">
        <span className="font-sans text-xs font-semibold text-[#64748B] uppercase tracking-widest">Consistency Window</span>
        <span className="font-mono text-sm font-medium text-[#0F172A]">
          {loading ? '…' : `${consistency} / 7 Days`}
        </span>
      </div>

      {/* Reviews Due Stat */}
      <div className="kinetic-card py-3 px-4 flex justify-between items-center bg-white shadow-sm border-l-2 border-l-[#ba1a1a]">
        <span className="font-sans text-xs font-semibold text-[#64748B] uppercase tracking-widest flex items-center gap-1.5">
          <Target size={14} /> Upcoming Reviews
        </span>
        <span className="font-mono text-sm font-medium text-[#ba1a1a]">
          {loading ? '…' : `${dueCount} Due`}
        </span>
      </div>

      {/* Daily Progress */}
      <div className="kinetic-card py-3 px-4 flex justify-between items-center bg-white shadow-sm">
        <span className="font-sans text-xs font-semibold text-[#64748B] uppercase tracking-widest flex items-center gap-1.5">
          <Activity size={14} /> Daily Progress
        </span>
        <span className="font-mono text-xs font-medium text-[#0F172A]">
          {loading ? '…' : `${dailyProgress} Today`}
        </span>
      </div>
    </div>
  );
}

export default Home;
