import React, { useState, useEffect } from 'react';
import { BarChart2, CalendarCheck, Zap, ClipboardList, Target, Lock, TrendingUp, BrainCircuit } from 'lucide-react';
import { apiFetch } from './lib/api';
import ComingSoonBanner from './ComingSoon';
import { useAuth } from './lib/AuthContext';

function Analytics() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { session } = useAuth();

  useEffect(() => {
    if (!session) {
      setLoading(false);
      return;
    }
    apiFetch('/api/dashboard/')
      .then(setStats)
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

      {/* PHASE 2 — honest placeholders, no fabricated numbers */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <h3 className="font-sans text-sm font-semibold text-[#1a1c1b] uppercase tracking-wider">Retention insights</h3>
          <span className="font-mono text-[10px] font-bold text-[#0891B2] bg-[#0891B2]/10 border border-[#0891B2]/20 rounded px-2 py-0.5">PHASE 2</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <ComingSoon
            icon={<TrendingUp size={18} />}
            title="Learning Momentum"
            body="A single score from your consistency, completion and review compliance — unlocks with adaptive scheduling."
          />
          <ComingSoon
            icon={<BrainCircuit size={18} />}
            title="Retention Strength"
            body="How well topics are sticking (Weak → Mastered), computed from your recall outcomes over time."
          />
          <ComingSoon
            icon={<BarChart2 size={18} />}
            title="Review Compliance"
            body="How reliably you clear reviews when they're due — needs a few weeks of review history first."
          />
        </div>
        <p className="font-sans text-xs text-[#64748B] mt-4">
          These need recall history to be meaningful. We're capturing the signals now (every review stores how you rated it and whether you recalled it) — the charts come once there's enough data.
        </p>
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

function ComingSoon({ icon, title, body }) {
  return (
    <div className="kinetic-card bg-white p-5 flex flex-col gap-3 opacity-90">
      <div className="flex items-center justify-between">
        <div className="w-10 h-10 rounded-lg bg-[rgba(15,23,42,0.04)] flex items-center justify-center text-[#64748B]">
          {icon}
        </div>
        <span className="font-mono text-[10px] text-[#94a3b8] flex items-center gap-1">
          <Lock size={11} /> Soon
        </span>
      </div>
      <h4 className="font-sans text-sm font-semibold text-[#0F172A]">{title}</h4>
      <p className="font-sans text-xs text-[#64748B] leading-relaxed">{body}</p>
    </div>
  );
}

export default Analytics;
