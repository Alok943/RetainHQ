import React, { useState, useEffect } from 'react';
import {
  BarChart2, CalendarCheck, Zap, ClipboardList, Target, BrainCircuit, CalendarDays,
  Layers, Scale, Clock, ListX,
} from 'lucide-react';
import { apiFetch } from './lib/api';
import { useAuth } from './lib/AuthContext';
import ReviewHeatmap from './ReviewHeatmap';

const pct = (x) => (x == null ? '—' : `${Math.round(x * 100)}%`);
const BAND_COLOR = { Mastered: '#0F766E', Strong: '#0891B2', Developing: '#B45309', Weak: '#ba1a1a' };
const REVIEW_METRICS_MIN_UI = 5; // mirrors backend REVIEW_METRICS_MIN

const SOURCE_LABEL = {
  problem: 'Problem Solving', self_learn: 'Self Learning', lecture: 'Lecture', video: 'Video',
  book: 'Book', article: 'Article', course: 'Course', project: 'Project', lesson: 'Lesson', other: 'Other',
};

function Analytics() {
  const [stats, setStats] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [sourceRetention, setSourceRetention] = useState(null);
  const [calibration, setCalibration] = useState(null);
  const [strength, setStrength] = useState(null);
  const [nodeAccuracy, setNodeAccuracy] = useState(null);
  const [timeOfDay, setTimeOfDay] = useState(null);
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
      apiFetch('/api/dashboard/source-retention').catch(() => null),
      apiFetch('/api/dashboard/calibration').catch(() => null),
      apiFetch('/api/dashboard/memory-strength').catch(() => null),
      apiFetch('/api/dashboard/node-accuracy').catch(() => null),
      apiFetch('/api/dashboard/time-of-day').catch(() => null),
    ])
      .then(([s, m, src, cal, str, nodes, tod]) => {
        setStats(s); setMetrics(m);
        setSourceRetention(src); setCalibration(cal); setStrength(str);
        setNodeAccuracy(nodes); setTimeOfDay(tod);
      })
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

      {/* RETENTION BY SOURCE */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <h3 className="font-sans text-sm font-semibold text-[#1a1c1b] uppercase tracking-wider flex items-center gap-1.5">
            <Layers size={15} className="text-[#0891B2]" /> Retention by source
          </h3>
        </div>
        {loading ? (
          <div className="kinetic-card bg-white p-5 h-[120px] skeleton" />
        ) : !sourceRetention?.enough_data ? (
          <EmptyStateCard
            icon={<Layers size={18} />}
            text="Log a few more activities from different sources (problems, videos, courses…) — once a source has enough completed reviews, its recall rate shows up here."
          />
        ) : (
          <div className="kinetic-card bg-white p-5 flex flex-col gap-4">
            {sourceRetention.sources
              .slice()
              .sort((a, b) => b.recall_rate - a.recall_rate)
              .map((s) => (
                <BarRow
                  key={s.source_type}
                  label={SOURCE_LABEL[s.source_type] || s.source_type}
                  value={pct(s.recall_rate)}
                  ratio={s.recall_rate}
                  sub={`${s.recalled} of ${s.completed} recalled`}
                  color="#0891B2"
                />
              ))}
          </div>
        )}
      </section>

      {/* GRADER CALIBRATION */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <h3 className="font-sans text-sm font-semibold text-[#1a1c1b] uppercase tracking-wider flex items-center gap-1.5">
            <Scale size={15} className="text-[#0891B2]" /> AI grader calibration
          </h3>
        </div>
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[0, 1, 2].map((i) => <div key={i} className="kinetic-card bg-white p-5 h-[110px] skeleton" />)}
          </div>
        ) : !calibration?.enough_data ? (
          <EmptyStateCard
            icon={<Scale size={18} />}
            text="Once the AI grader has judged a few more recall attempts, you'll see how often its verdict matches your own self-rating."
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <MetricCard
              icon={<Scale size={16} />}
              title="Agreement"
              value={pct(calibration.agreement_rate)}
              ratio={calibration.agreement_rate}
              sub={`${calibration.graded} graded attempts`}
              color="#0F766E"
            />
            <MetricCard
              icon={<Target size={16} />}
              title="Overconfident"
              value={pct(calibration.overconfident_rate)}
              ratio={calibration.overconfident_rate}
              sub="You said recalled, AI disagreed"
              color="#B45309"
            />
            <MetricCard
              icon={<BrainCircuit size={16} />}
              title="Underconfident"
              value={pct(calibration.underconfident_rate)}
              ratio={calibration.underconfident_rate}
              sub="You said missed, AI thought you had it"
              color="#0891B2"
            />
          </div>
        )}
      </section>

      {/* MEMORY STRENGTH DISTRIBUTION */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <h3 className="font-sans text-sm font-semibold text-[#1a1c1b] uppercase tracking-wider flex items-center gap-1.5">
            <BrainCircuit size={15} className="text-[#0891B2]" /> Memory strength
          </h3>
        </div>
        {loading ? (
          <div className="kinetic-card bg-white p-5 h-[160px] skeleton" />
        ) : !strength?.enough_data ? (
          <EmptyStateCard
            icon={<BrainCircuit size={18} />}
            text="FSRS builds a stability estimate (days until you'd likely forget) as you complete reviews — the distribution across your topics shows up here once there's enough history."
          />
        ) : (
          <div className="kinetic-card bg-white p-5">
            <div className="flex items-baseline gap-2 mb-4">
              <span className="font-mono text-2xl font-semibold text-[#0F172A]">{strength.median_stability_days}d</span>
              <span className="font-sans text-xs text-[#64748B]">median stability · {strength.count} topics</span>
            </div>
            <div className="grid grid-cols-5 gap-2 items-end h-[100px]">
              {strength.buckets.map((b) => {
                const max = Math.max(1, ...strength.buckets.map((x) => x.count));
                const h = Math.max(4, Math.round((b.count / max) * 100));
                return (
                  <div key={b.label} className="flex flex-col items-center justify-end h-full gap-1.5">
                    <span className="font-mono text-[11px] text-[#0F172A]">{b.count}</span>
                    <div className="w-full rounded-t bg-[#0891B2]" style={{ height: `${h}px` }} />
                    <span className="font-mono text-[10px] text-[#64748B]">{b.label}</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </section>

      {/* WEAKEST NODES (Tests-section history) */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <h3 className="font-sans text-sm font-semibold text-[#1a1c1b] uppercase tracking-wider flex items-center gap-1.5">
            <ListX size={15} className="text-[#0891B2]" /> Weakest topics
          </h3>
        </div>
        {loading ? (
          <div className="kinetic-card bg-white p-5 h-[140px] skeleton" />
        ) : !nodeAccuracy?.enough_data ? (
          <EmptyStateCard
            icon={<ListX size={18} />}
            text="Take a few tests in the Tests section — the topics you miss most often will show up here so you know what to review next."
          />
        ) : (
          <div className="kinetic-card bg-white p-5 flex flex-col gap-3">
            {nodeAccuracy.weakest.map((n) => (
              <div key={n.node_title} className="flex items-center justify-between gap-3 py-1.5 border-b border-[rgba(15,23,42,0.06)] last:border-b-0">
                <span className="font-sans text-sm text-[#0F172A] truncate flex-1 min-w-0">{n.node_title}</span>
                <div className="flex items-center gap-1.5 shrink-0">
                  <Pill label={`${n.got} got`} color="#0F766E" />
                  <Pill label={`${n.missed} missed`} color="#B45309" />
                  <Pill label={`${n.wrong} wrong`} color="#ba1a1a" />
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* TIME OF DAY */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <h3 className="font-sans text-sm font-semibold text-[#1a1c1b] uppercase tracking-wider flex items-center gap-1.5">
            <Clock size={15} className="text-[#0891B2]" /> Best time to review
          </h3>
        </div>
        {loading ? (
          <div className="kinetic-card bg-white p-5 h-[140px] skeleton" />
        ) : !timeOfDay?.enough_data ? (
          <EmptyStateCard
            icon={<Clock size={18} />}
            text="Complete reviews at different times of day and this fills in with when you recall best — useful for spotting your sharpest hours."
          />
        ) : (
          <TimeOfDayChart buckets={timeOfDay.buckets} />
        )}
      </section>

    </div>
  );
}

function EmptyStateCard({ icon, text }) {
  return (
    <div className="kinetic-card bg-white p-6 flex items-start gap-4">
      <div className="w-10 h-10 rounded-lg bg-[#0891B2]/10 flex items-center justify-center text-[#0891B2] shrink-0">
        {icon}
      </div>
      <p className="font-sans text-xs text-[#64748B] leading-relaxed">{text}</p>
    </div>
  );
}

function BarRow({ label, value, sub, ratio, color }) {
  const width = Math.max(0, Math.min(100, Math.round((ratio || 0) * 100)));
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between gap-3">
        <span className="font-sans text-sm text-[#0F172A]">{label}</span>
        <span className="font-mono text-sm font-semibold text-[#0F172A]">{value}</span>
      </div>
      <div className="w-full h-1.5 rounded-full bg-[rgba(15,23,42,0.06)] overflow-hidden">
        <div className="h-full rounded-full transition-all duration-700 ease-out" style={{ width: `${width}%`, backgroundColor: color }} />
      </div>
      <span className="font-sans text-[11px] text-[#64748B]">{sub}</span>
    </div>
  );
}

function Pill({ label, color }) {
  return (
    <span
      className="font-sans text-[10px] font-bold uppercase tracking-wide px-1.5 py-0.5 rounded-full whitespace-nowrap"
      style={{ color, backgroundColor: `${color}14`, border: `1px solid ${color}33` }}
    >
      {label}
    </span>
  );
}

// UTC→local hour shift so the chart reflects when the user themself reviews,
// not the server's clock. getTimezoneOffset() is UTC-minus-local in minutes.
function TimeOfDayChart({ buckets }) {
  const offsetHours = -new Date().getTimezoneOffset() / 60;
  const byLocalHour = new Map(buckets.map((b) => [b.hour_utc, b]));
  const localBuckets = Array.from({ length: 24 }, (_, localHour) => {
    const utcHour = ((localHour - offsetHours) % 24 + 24) % 24;
    return { hour: localHour, ...byLocalHour.get(Math.round(utcHour)) };
  });
  const maxCount = Math.max(1, ...localBuckets.map((b) => b.count || 0));
  const peak = localBuckets.reduce((best, b) => ((b.count || 0) > (best.count || 0) ? b : best), localBuckets[0]);

  return (
    <div className="kinetic-card bg-white p-5">
      <div className="flex items-baseline gap-2 mb-4">
        <span className="font-mono text-2xl font-semibold text-[#0F172A]">
          {peak.count ? `${peak.hour}:00–${(peak.hour + 1) % 24}:00` : '—'}
        </span>
        <span className="font-sans text-xs text-[#64748B]">your busiest review hour</span>
      </div>
      <div className="grid grid-cols-24 gap-[3px] items-end h-[70px]" style={{ gridTemplateColumns: 'repeat(24, minmax(0, 1fr))' }}>
        {localBuckets.map((b) => {
          const h = Math.max(2, Math.round(((b.count || 0) / maxCount) * 100));
          const opacity = b.recall_rate != null ? 0.35 + b.recall_rate * 0.65 : 0.35;
          return (
            <div
              key={b.hour}
              title={`${b.hour}:00 — ${b.count || 0} review${b.count === 1 ? '' : 's'}${b.recall_rate != null ? `, ${Math.round(b.recall_rate * 100)}% recalled` : ''}`}
              className="w-full rounded-t bg-[#0891B2]"
              style={{ height: `${h}%`, opacity: b.count ? opacity : 0.08 }}
            />
          );
        })}
      </div>
      <div className="flex justify-between mt-1.5">
        <span className="font-mono text-[10px] text-[#64748B]">12am</span>
        <span className="font-mono text-[10px] text-[#64748B]">6am</span>
        <span className="font-mono text-[10px] text-[#64748B]">12pm</span>
        <span className="font-mono text-[10px] text-[#64748B]">6pm</span>
        <span className="font-mono text-[10px] text-[#64748B]">12am</span>
      </div>
      <p className="font-sans text-[11px] text-[#64748B] mt-3">Bar height = review volume · darker = higher recall rate that hour.</p>
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
