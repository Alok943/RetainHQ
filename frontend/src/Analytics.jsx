import React, { useState, useEffect } from 'react';
import { BarChart2, CalendarCheck, Zap, ClipboardList, Target, BrainCircuit, CalendarDays } from 'lucide-react';
import { apiFetch } from './lib/api';
import ComingSoonBanner from './ComingSoon';
import { useAuth } from './lib/AuthContext';
import ReviewHeatmap from './ReviewHeatmap';

const pct = (x) => (x == null ? '—' : `${Math.round(x * 100)}%`);
const BAND_COLOR = { Mastered: '#0F766E', Strong: '#0891B2', Developing: '#B45309', Weak: '#ba1a1a' };
const REVIEW_METRICS_MIN_UI = 5; // mirrors backend REVIEW_METRICS_MIN

function Analytics() {
  const [stats, setStats] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { session } = useAuth();

  useEffect(() => {
    if (!session) {
      setLoading(false);
      return;
    }
    Promise.all([
      apiFetch('/api/dashboard/'),
      apiFetch('/api/dashboard/review-metrics').catch(() => null), // tolerate older backend
    ])
      .then(([s, m]) => { setStats(s); setMetrics(m); })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const v = (x) => (loading ? '…' : x);

  return (
    <div className="flex flex-col gap-8 p-4 md:p-8 max-w-6xl mx-auto w-full pb-20 md:pb-8 animate-in fade-in duration-300">

      <header className="mb-2">
        <h2 className="font-sans text-2xl font-semibold text-[#0F172A] flex items-center gap-2">
          <BarChart2 size={24} className="text-[#0891B2]" /> Analytics
        </h2>
        <p className="font-sans text-sm text-[#64748B] mt-1">Your real activity so far. Deeper retention metrics arrive with adaptive scheduling.</p>
      </header>

      {error && (
        <div className="kinetic-card bg-white text-[#ba1a1a] text-sm">Couldn't load stats: {error}</div>
      )}

      {/* REAL STATS (from /api/dashboard/) */}
      <section className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Consistency"
          value={v(stats ? `${stats.consistency_window} / 7` : '0 / 7')}
          sub="Active days, last 7"
          icon={<CalendarCheck size={16} />}
          color="#0891B2"
        />
        <StatCard
          title="Activities Logged"
          value={v(stats?.total_activities ?? 0)}
          sub="All time"
          icon={<ClipboardList size={16} />}
          color="#0F766E"
        />
        <StatCard
          title="Reviews Completed"
          value={v(stats?.total_reviews_completed ?? 0)}
          sub="All time"
          icon={<Zap size={16} />}
          color="#B45309"
        />
        <StatCard
          title="Reviews Due"
          value={v(stats?.due_count ?? 0)}
          sub="Right now"
          icon={<Target size={16} />}
          color="#ba1a1a"
        />
      </section>

      {/* REVIEW ACTIVITY HEATMAP */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <h3 className="font-sans text-sm font-semibold text-[#1a1c1b] uppercase tracking-wider flex items-center gap-1.5">
            <CalendarDays size={15} className="text-[#0891B2]" /> Review activity
          </h3>
        </div>
        <ReviewHeatmap />
      </section>

      {/* RETENTION INSIGHTS — real metrics from review history (gated on enough data) */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <h3 className="font-sans text-sm font-semibold text-[#1a1c1b] uppercase tracking-wider">Retention insights</h3>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[0, 1, 2].map((i) => <div key={i} className="kinetic-card bg-white p-5 h-[140px] skeleton" />)}
          </div>
        ) : !metrics?.enough_data ? (
          <div className="kinetic-card bg-white p-6 flex items-start gap-4">
            <div className="w-10 h-10 rounded-lg bg-[#0891B2]/10 flex items-center justify-center text-[#0891B2] shrink-0">
              <BrainCircuit size={18} />
            </div>
            <div>
              <h4 className="font-sans text-sm font-semibold text-[#0F172A] mb-1">Retention metrics unlock after a few reviews</h4>
              <p className="font-sans text-xs text-[#64748B] leading-relaxed">
                You've completed <span className="font-semibold text-[#0F172A]">{metrics?.reviews_completed ?? 0}</span> of {REVIEW_METRICS_MIN_UI} reviews needed. Keep clearing your due reviews — once there's enough recall history, your accuracy, retention strength and compliance show up here for real (no fabricated numbers).
              </p>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <MetricCard
              icon={<Target size={16} />}
              title="Recall Accuracy"
              value={pct(metrics.recall_rate)}
              ratio={metrics.recall_rate}
              sub={`${Math.round((metrics.recall_rate || 0) * metrics.reviews_completed)} of ${metrics.reviews_completed} recalled`}
              color="#0891B2"
            />
            <MetricCard
              icon={<BrainCircuit size={16} />}
              title="Retention Strength"
              value={metrics.retention_score}
              ratio={(metrics.retention_score || 0) / 100}
              band={metrics.retention_band}
              sub="Recall weighted by difficulty"
              color={BAND_COLOR[metrics.retention_band] || '#0891B2'}
            />
            <MetricCard
              icon={<CalendarCheck size={16} />}
              title="Review Compliance"
              value={pct(metrics.compliance_rate)}
              ratio={metrics.compliance_rate}
              sub="Due reviews you've cleared"
              color="#0F766E"
            />
          </div>
        )}
      </section>

      <ComingSoonBanner
        id="analytics-retention-by-source"
        title="Retention by Source"
        description="See which learning sources (books, videos, projects) lead to the strongest long-term retention."
      />

    </div>
  );
}

function StatCard({ title, value, sub, icon, color }) {
  return (
    <div className="kinetic-card bg-white p-4 border-t-2" style={{ borderTopColor: color }}>
      <div className="flex justify-between items-start mb-2">
        <h3 className="font-sans text-[10px] font-bold text-[#64748B] uppercase tracking-widest">{title}</h3>
        <div style={{ color }}>{icon}</div>
      </div>
      <div className="font-mono text-2xl md:text-3xl font-semibold text-[#0F172A]">{value}</div>
      <div className="font-sans text-xs text-[#64748B] mt-1">{sub}</div>
    </div>
  );
}

function MetricCard({ icon, title, value, sub, ratio, band, color }) {
  const width = Math.max(0, Math.min(100, Math.round((ratio || 0) * 100)));
  return (
    <div className="kinetic-card bg-white p-5 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h3 className="font-sans text-[10px] font-bold text-[#64748B] uppercase tracking-widest">{title}</h3>
        <div style={{ color }}>{icon}</div>
      </div>
      <div className="flex items-end gap-2">
        <span className="font-mono text-3xl font-semibold text-[#0F172A] leading-none">{value}</span>
        {band && (
          <span
            className="font-sans text-[11px] font-bold px-2 py-0.5 rounded-full mb-0.5"
            style={{ color, backgroundColor: `${color}14`, border: `1px solid ${color}33` }}
          >
            {band}
          </span>
        )}
      </div>
      <div className="w-full h-1.5 rounded-full bg-[rgba(15,23,42,0.06)] overflow-hidden">
        <div className="h-full rounded-full transition-all duration-700 ease-out" style={{ width: `${width}%`, backgroundColor: color }} />
      </div>
      <div className="font-sans text-xs text-[#64748B]">{sub}</div>
    </div>
  );
}

export default Analytics;
