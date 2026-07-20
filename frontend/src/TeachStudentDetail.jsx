import React, { useEffect, useMemo, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, User, ShieldAlert, Target, ListChecks, TrendingUp, AlertTriangle,
} from 'lucide-react';
import { apiFetch } from './lib/api';

/**
 * TeachStudentDetail — /teach/:id/students/:memberId. The parent-meeting /
 * remediation screen (SPEC-teacher-dashboard.md §1, screen 3): one student's
 * retention stats, weakest topics, per-node mastery, and an 8-week recall
 * trend. Reuses GET /{classroom_id}/students/{member_id}, which is already
 * scoped server-side to this classroom's assigned roadmaps only (§4.2/§5) —
 * nothing here needs its own scoping logic.
 */

const STATUS_COLOR = {
  weak: { bg: 'rgba(185,28,28,0.14)', border: 'rgba(185,28,28,0.45)', text: '#B91C1C', label: 'Weak' },
  developing: { bg: 'rgba(180,83,9,0.14)', border: 'rgba(180,83,9,0.45)', text: '#B45309', label: 'Developing' },
  strong: { bg: 'rgba(15,118,110,0.14)', border: 'rgba(15,118,110,0.45)', text: '#0F766E', label: 'Strong' },
  untouched: { bg: 'rgba(15,23,42,0.05)', border: 'rgba(15,23,42,0.14)', text: '#94A3B8', label: 'Untouched' },
};

function TeachStudentDetail() {
  const { id, memberId } = useParams();
  const navigate = useNavigate();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    apiFetch(`/api/classrooms/${id}/students/${memberId}`)
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id, memberId]);

  const nodesByPhase = useMemo(() => {
    const map = new Map();
    for (const n of data?.node_mastery || []) {
      if (!map.has(n.phase)) map.set(n.phase, new Map());
      const sections = map.get(n.phase);
      if (!sections.has(n.section)) sections.set(n.section, []);
      sections.get(n.section).push(n);
    }
    return map;
  }, [data]);

  if (loading) return <DetailSkeleton />;

  if (error || !data) {
    return (
      <div className="max-w-3xl mx-auto w-full p-4 md:p-8 pb-20 md:pb-8">
        <div className="kinetic-card bg-white p-8 text-center flex flex-col items-center gap-3">
          <ShieldAlert size={28} className="text-[#B91C1C]" />
          <p className="font-sans text-sm text-[#64748B]">
            {error || "Couldn't find that student in this class."}
          </p>
          <button onClick={() => navigate(`/teach/${id}`)} className="kinetic-btn kinetic-accent-gradient px-4 py-2 text-sm">
            Back to classroom
          </button>
        </div>
      </div>
    );
  }

  const rm = data.review_metrics || {};
  const na = data.node_accuracy || {};

  return (
    <div className="max-w-3xl mx-auto w-full p-4 md:p-8 pb-20 md:pb-8 flex flex-col gap-6 animate-in fade-in duration-300">
      <div className="flex flex-col gap-1">
        <button
          onClick={() => navigate(`/teach/${id}`)}
          className="flex items-center gap-1.5 font-sans text-xs font-semibold text-[#64748B] hover:text-[#0891B2] transition-colors self-start mb-1"
        >
          <ArrowLeft size={14} /> Back to classroom
        </button>
        <h2 className="font-sans text-2xl font-semibold text-[#0F172A] flex items-center gap-2">
          <User size={22} className="text-[#0891B2]" /> {data.display_name}
        </h2>
        <p className="font-sans text-sm text-[#64748B] mt-1">
          Joined {new Date(data.joined_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
        </p>
      </div>

      {/* Retention stats */}
      {!rm.enough_data ? (
        <div className="kinetic-card bg-white p-5 flex items-center gap-3">
          <TrendingUp size={18} className="text-[#94A3B8] shrink-0" />
          <p className="font-sans text-sm text-[#64748B]">
            Not enough review history yet — retention stats need a few completed reviews first.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard title="Retention" value={rm.retention_score != null ? `${rm.retention_score}` : '—'} sub={rm.retention_band} icon={<Target size={16} />} color="#0891B2" />
          <StatCard title="Recall rate" value={rm.recall_rate != null ? `${Math.round(rm.recall_rate * 100)}%` : '—'} icon={<TrendingUp size={16} />} color="#0F766E" />
          <StatCard title="Reviews done" value={rm.reviews_completed ?? 0} icon={<ListChecks size={16} />} color="#B45309" />
          <StatCard title="On-time rate" value={rm.compliance_rate != null ? `${Math.round(rm.compliance_rate * 100)}%` : '—'} icon={<ShieldAlert size={16} />} color="#0891B2" />
        </div>
      )}

      {/* Weekly recall trend — last 8 weeks */}
      {data.weekly_recall_trend?.length > 0 && (
        <div className="kinetic-card bg-white p-5 flex flex-col gap-4">
          <h3 className="font-sans text-xs font-bold text-[#64748B] uppercase tracking-widest">Recall trend, last 8 weeks</h3>
          <WeeklyTrendChart weeks={data.weekly_recall_trend} />
        </div>
      )}

      {/* Weakest topics */}
      {na.enough_data && na.weakest?.length > 0 && (
        <div className="kinetic-card bg-white p-5 flex flex-col gap-3">
          <h3 className="font-sans text-xs font-bold text-[#64748B] uppercase tracking-widest">Weakest topics</h3>
          <div className="flex flex-col gap-2">
            {na.weakest.map((row) => (
              <div key={row.node_title} className="flex items-center justify-between gap-3 px-3 py-2 rounded-lg bg-[rgba(185,28,28,0.04)]">
                <span className="font-sans text-sm text-[#0F172A]">{row.node_title}</span>
                <span className="font-mono text-xs text-[#B91C1C] shrink-0">
                  {row.got}/{row.total} ({Math.round(row.accuracy * 100)}%)
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Per-node mastery grid */}
      {nodesByPhase.size > 0 && (
        <div className="kinetic-card bg-white p-5 flex flex-col gap-5">
          <div className="flex items-center justify-between">
            <h3 className="font-sans text-xs font-bold text-[#64748B] uppercase tracking-widest">Topic mastery</h3>
            <Legend />
          </div>
          {[...nodesByPhase.entries()].map(([phase, sections]) => (
            <div key={phase}>
              <h4 className="font-sans text-sm font-semibold text-[#0F172A] mb-2">{phase}</h4>
              <div className="flex flex-col gap-3">
                {[...sections.entries()].map(([section, nodes]) => (
                  <div key={section}>
                    <p className="font-sans text-[11px] font-bold text-[#64748B] uppercase tracking-wide mb-1.5">{section}</p>
                    <div className="grid gap-1.5" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))' }}>
                      {nodes.map((n) => {
                        const c = STATUS_COLOR[n.status] || STATUS_COLOR.untouched;
                        return (
                          <div
                            key={n.node_id}
                            title={n.title}
                            className="rounded-lg border px-2.5 py-2 text-left"
                            style={{ backgroundColor: c.bg, borderColor: c.border }}
                          >
                            <p className="font-sans text-[11px] font-semibold leading-snug line-clamp-2" style={{ color: c.text }}>{n.title}</p>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function WeeklyTrendChart({ weeks }) {
  const max = 1; // recall_rate is 0-1, fixed scale so bar heights are comparable across students
  return (
    <div className="flex items-end gap-2 h-28">
      {weeks.map((w) => {
        const hasData = w.count > 0;
        const pct = hasData ? Math.max(0.04, (w.recall_rate ?? 0) / max) : 0;
        const isLow = hasData && (w.recall_rate ?? 0) < 0.5;
        return (
          <div key={w.week_start} className="flex-1 flex flex-col items-center gap-1.5 min-w-0">
            <div className="w-full h-24 flex items-end rounded overflow-hidden bg-[rgba(15,23,42,0.04)]">
              {hasData && (
                <div
                  className="w-full rounded-t transition-all duration-500"
                  style={{ height: `${pct * 100}%`, backgroundColor: isLow ? '#B91C1C' : '#0891B2' }}
                  title={`${w.count} review${w.count === 1 ? '' : 's'} · ${Math.round((w.recall_rate ?? 0) * 100)}% recalled`}
                />
              )}
            </div>
            <span className="font-mono text-[9px] text-[#94A3B8] truncate w-full text-center">
              {new Date(w.week_start).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
            </span>
          </div>
        );
      })}
    </div>
  );
}

function Legend() {
  const items = ['weak', 'developing', 'strong', 'untouched'];
  return (
    <div className="flex flex-wrap items-center gap-3">
      {items.map((s) => (
        <div key={s} className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: STATUS_COLOR[s].border }} />
          <span className="font-sans text-[11px] text-[#64748B]">{STATUS_COLOR[s].label}</span>
        </div>
      ))}
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
      <div className="font-mono text-2xl font-semibold text-[#0F172A]">{value}</div>
      {sub && <div className="font-sans text-[11px] text-[#64748B] mt-0.5">{sub}</div>}
    </div>
  );
}

function DetailSkeleton() {
  return (
    <div className="max-w-3xl mx-auto w-full p-4 md:p-8 pb-20 md:pb-8 flex flex-col gap-6">
      <div className="skeleton h-4 w-32" />
      <div className="skeleton h-8 w-56" />
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[0, 1, 2, 3].map((i) => <div key={i} className="skeleton h-24 rounded-xl" />)}
      </div>
      <div className="skeleton h-40 w-full rounded-xl" />
    </div>
  );
}

export default TeachStudentDetail;
