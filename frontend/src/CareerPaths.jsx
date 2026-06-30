import React, { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Route, ArrowRight, AlertTriangle, Clock, TrendingUp, Lock, GraduationCap } from 'lucide-react';
import { apiFetch } from './lib/api';
import { useSeo } from './lib/useSeo';
import { CAREER_PATHS, ROLES } from './lib/careerPaths';

const STATUS = {
  common: { label: 'Common path', color: '#0F766E' },
  possible: { label: 'Possible', color: '#B45309' },
};

function CareerPaths() {
  const navigate = useNavigate();
  const [roadmaps, setRoadmaps] = useState([]);

  useSeo(
    'Career Paths — role transitions for B.Tech freshers | RetainHQ',
    'Job-aligned learning paths by role transition (Backend→GenAI, Data Analyst→Data Engineer, and more) — timeline, ROI, blockers and the exact roadmaps that get you there.'
  );

  useEffect(() => {
    apiFetch('/api/roadmaps/', { optionalAuth: true })
      .then((d) => setRoadmaps(Array.isArray(d) ? d : []))
      .catch(() => {});
  }, []);

  // Resolve a roadmap ref's `match` substring against the live roadmap list.
  const resolve = useMemo(() => {
    return (match) => roadmaps.find((r) => (r.title || '').toLowerCase().includes(match));
  }, [roadmaps]);

  const byRole = useMemo(() => {
    const map = {};
    for (const p of CAREER_PATHS) (map[p.from] ||= []).push(p);
    return ROLES.filter((r) => map[r]?.length).map((r) => ({ role: r, paths: map[r] }));
  }, []);

  return (
    <div className="relative max-w-5xl mx-auto w-full p-4 md:p-8 pb-20 md:pb-8 animate-in fade-in duration-300">
      <header className="mb-8">
        <h2 className="font-sans text-2xl font-semibold text-[#0F172A] flex items-center gap-2">
          <Route size={24} className="text-[#0891B2]" /> Career Paths
        </h2>
        <p className="font-sans text-sm text-[#64748B] mt-1 max-w-2xl">
          Where you are → where you want to be. Each path shows the realistic timeline, the ROI, the blocker that
          trips most freshers, and the exact RetainHQ roadmaps that close the gap. Grounded in 2024–2026 Indian
          fresher-market research.
        </p>
      </header>

      <div className="flex flex-col gap-10">
        {byRole.map(({ role, paths }) => (
          <section key={role}>
            <h3 className="font-sans text-sm font-semibold text-[#0F172A] uppercase tracking-wider mb-4 flex items-center gap-2">
              Starting as <span className="text-[#0891B2]">{role}</span>
              <div className="flex-1 h-px bg-[rgba(15,23,42,0.07)]" />
            </h3>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {paths.map((p) => (
                <PathCard key={p.id} path={p} resolve={resolve} navigate={navigate} />
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}

function PathCard({ path, resolve, navigate }) {
  const st = STATUS[path.status] || STATUS.possible;
  return (
    <article className="kinetic-card bg-white p-5 flex flex-col gap-4">
      {/* from → to */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <span className="font-sans text-sm font-semibold text-[#0F172A] truncate">{path.from}</span>
          <ArrowRight size={15} className="text-[#0891B2] shrink-0" />
          <span className="font-sans text-sm font-semibold text-[#0F172A] truncate">{path.to}</span>
        </div>
        <span
          className="font-sans text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full shrink-0"
          style={{ color: st.color, backgroundColor: `${st.color}14`, border: `1px solid ${st.color}33` }}
        >
          {st.label}
        </span>
      </div>

      {/* timeline + roi */}
      <div className="flex flex-col gap-2">
        <span className="font-mono text-xs text-[#64748B] flex items-center gap-1.5">
          <Clock size={12} /> {path.timeline}
        </span>
        <p className="font-sans text-xs text-[#0F172A] leading-relaxed flex items-start gap-1.5">
          <TrendingUp size={13} className="text-[#0F766E] shrink-0 mt-0.5" /> <span>{path.roi}</span>
        </p>
      </div>

      {/* skill delta */}
      <div className="flex flex-wrap gap-1.5">
        {path.skillDelta.map((s) => (
          <span key={s} className="font-sans text-[11px] text-[#475569] bg-[rgba(15,23,42,0.04)] border border-[rgba(15,23,42,0.06)] rounded px-2 py-0.5">
            {s}
          </span>
        ))}
      </div>

      {/* blocker */}
      <p className="font-sans text-xs text-[#92400E] bg-[#B45309]/[0.06] border border-[#B45309]/20 rounded-lg p-2.5 leading-relaxed flex items-start gap-1.5">
        <AlertTriangle size={13} className="shrink-0 mt-0.5" /> <span><span className="font-semibold">Blocker: </span>{path.blocker}</span>
      </p>

      {/* mapped roadmaps */}
      <div>
        <div className="font-sans text-[10px] font-bold text-[#64748B] uppercase tracking-widest mb-2">Roadmaps that build this</div>
        <div className="flex flex-wrap gap-2">
          {path.roadmaps.map((ref, i) => {
            const rm = resolve(ref.match);
            if (rm) {
              const pct = rm.progress_pct ?? 0;
              return (
                <button
                  key={i}
                  onClick={() => navigate(`/roadmaps/${rm.slug || rm.id}`)}
                  className="group flex items-center gap-2 rounded-lg border border-[rgba(15,23,42,0.12)] bg-white px-2.5 py-1.5 hover:border-[#0891B2]/50 hover:bg-[#0891B2]/[0.04] transition-colors"
                  title={ref.note ? `${rm.title} — ${ref.note}` : rm.title}
                >
                  <GraduationCap size={13} className="text-[#0891B2] shrink-0" />
                  <span className="font-sans text-xs font-semibold text-[#0F172A]">{rm.title}</span>
                  <span className="font-mono text-[10px] text-[#0891B2]">{pct}%</span>
                  <ArrowRight size={12} className="text-[#94a3b8] opacity-0 group-hover:opacity-100 transition-opacity" />
                </button>
              );
            }
            return (
              <span
                key={i}
                className="flex items-center gap-1.5 rounded-lg border border-dashed border-[rgba(15,23,42,0.15)] bg-[rgba(15,23,42,0.02)] px-2.5 py-1.5 text-[#94a3b8]"
                title="Roadmap coming soon"
              >
                <Lock size={12} className="shrink-0" />
                <span className="font-sans text-xs font-medium">{ref.label}</span>
                <span className="font-mono text-[9px] uppercase tracking-wide">soon</span>
              </span>
            );
          })}
        </div>
      </div>
    </article>
  );
}

export default CareerPaths;
