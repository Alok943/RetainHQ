import React, { useEffect, useState } from 'react';
import {
  Map, ListChecks, ArrowRight, Plus,
  Binary, Database, Globe, Server, Sparkles, Code2, Cpu, Calculator,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { apiFetch } from './lib/api';
import { useAuth } from './lib/AuthContext';

// Per-roadmap visual identity, matched by title keyword (no backend change).
// First matching rule wins; order matters (specific before generic).
const STYLE_RULES = [
  { match: ['neetcode', 'striver', 'dsa', 'algorithm', 'data structure'], Icon: Binary, accent: '#7C3AED' },
  { match: ['sql'], Icon: Database, accent: '#4F46E5' },
  { match: ['web'], Icon: Globe, accent: '#0891B2' },
  { match: ['system design'], Icon: Server, accent: '#0F766E' },
  { match: ['ai eng', 'machine learning', 'deep learning'], Icon: Sparkles, accent: '#C026D3' },
  { match: ['backend'], Icon: Server, accent: '#059669' },
  { match: ['python'], Icon: Code2, accent: '#2563EB' },
  { match: ['core cs', 'operating system', 'dbms', 'network'], Icon: Cpu, accent: '#475569' },
  { match: ['aptitude', 'quant', 'reasoning'], Icon: Calculator, accent: '#B45309' },
];

function getRoadmapStyle(title = '') {
  const t = title.toLowerCase();
  for (const rule of STYLE_RULES) {
    if (rule.match.some((m) => t.includes(m))) return rule;
  }
  return { Icon: Map, accent: '#0891B2' };
}

// Count a number up from 0 to target once on mount.
function useCountUp(target, duration = 800) {
  const [val, setVal] = useState(0);
  useEffect(() => {
    let raf;
    const start = performance.now();
    const tick = (now) => {
      const p = Math.min(1, (now - start) / duration);
      setVal(Math.round(target * p));
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, duration]);
  return val;
}

function ProgressRing({ pct, accent, Icon }) {
  const [shown, setShown] = useState(0);
  useEffect(() => {
    const raf = requestAnimationFrame(() => setShown(pct)); // trigger the fill transition after mount
    return () => cancelAnimationFrame(raf);
  }, [pct]);
  const ring = 'M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831';
  return (
    <div className="relative w-16 h-16 shrink-0">
      <svg className="w-full h-full -rotate-90 transform" viewBox="0 0 36 36">
        <path stroke="rgba(148,163,184,0.25)" strokeWidth="3" fill="none" d={ring} />
        <path
          stroke={accent}
          strokeWidth="3"
          strokeLinecap="round"
          fill="none"
          strokeDasharray={`${shown}, 100`}
          style={{ transition: 'stroke-dasharray 0.8s ease-out' }}
          d={ring}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center" style={{ color: accent }}>
        <Icon size={20} />
      </div>
    </div>
  );
}

function RoadmapCard({ rm, index, onClick }) {
  const { Icon, accent } = getRoadmapStyle(rm.title);
  const pct = useCountUp(rm.progress_pct ?? 0);

  return (
    <article
      onClick={onClick}
      style={{ borderLeftWidth: '3px', borderLeftColor: accent, animationDelay: `${index * 60}ms`, animationFillMode: 'backwards' }}
      className="kinetic-card bg-white p-5 cursor-pointer group flex gap-4 items-center transition-all duration-200 hover:-translate-y-1 hover:shadow-lg animate-in fade-in slide-in-from-bottom-3"
    >
      <ProgressRing pct={rm.progress_pct ?? 0} accent={accent} Icon={Icon} />

      <div className="flex-1 min-w-0">
        <div className="flex justify-between items-start gap-3 mb-1">
          <h3 className="font-sans text-lg font-semibold text-[#0F172A] line-clamp-1">{rm.title}</h3>
          <span className="font-mono text-sm font-semibold shrink-0" style={{ color: accent }}>{pct}%</span>
        </div>
        <p className="font-sans text-xs text-[#64748B] line-clamp-2 min-h-[32px] mb-2">{rm.description}</p>
        <div className="flex items-center justify-between">
          <span className="font-mono text-[10px] text-[#64748B]">{rm.done_nodes} / {rm.total_nodes} topics complete</span>
          <ArrowRight
            size={16}
            style={{ color: accent }}
            className="opacity-0 -translate-x-1 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-200"
          />
        </div>
      </div>
    </article>
  );
}

function Roadmaps() {
  const navigate = useNavigate();
  const [roadmaps, setRoadmaps] = useState([]);
  const [loading, setLoading] = useState(true);
  const { session } = useAuth();

  useEffect(() => {
    async function fetchRoadmaps() {
      try {
        // Backend returns each roadmap with real progress computed server-side
        const data = await apiFetch('/api/roadmaps/', { optionalAuth: true });
        setRoadmaps(data);
      } catch (err) {
        console.error('Failed to load roadmaps:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchRoadmaps();
  }, []);

  return (
    <div className="flex flex-col gap-8 p-4 md:p-8 max-w-5xl mx-auto w-full pb-20 md:pb-8 animate-in fade-in duration-300">

      <header className="mb-2">
        <h2 className="font-sans text-2xl font-semibold text-[#0F172A] flex items-center gap-2">
          <Map size={24} className="text-[#0891B2]" /> Learning Roadmaps
        </h2>
        <p className="font-sans text-sm text-[#64748B] mt-1">Structured learning paths tracking your completion and retention.</p>
      </header>

      <section>
        <h2 className="font-sans text-sm font-semibold text-[#1a1c1b] uppercase tracking-wider flex items-center gap-1.5 mb-4">
          <ListChecks size={16} className="text-[#0F172A]" /> All Roadmaps
        </h2>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[0, 1, 2, 3].map((i) => (
              <div key={i} className="kinetic-card bg-white p-5 flex gap-4 items-center animate-pulse">
                <div className="w-16 h-16 rounded-full bg-slate-100 shrink-0" />
                <div className="flex-1 space-y-3">
                  <div className="h-4 bg-slate-100 rounded w-2/3" />
                  <div className="h-3 bg-slate-100 rounded w-full" />
                  <div className="h-3 bg-slate-100 rounded w-1/3" />
                </div>
              </div>
            ))}
          </div>
        ) : roadmaps.length === 0 ? (
          <div className="p-8 text-center text-[#64748B] bg-white rounded border border-[rgba(15,23,42,0.1)]">No roadmaps found.</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {roadmaps.map((rm, i) => (
              <RoadmapCard key={rm.id} rm={rm} index={i} onClick={() => navigate(`/roadmaps/${rm.id}`)} />
            ))}
          </div>
        )}
      </section>

      <section className="mt-8">
        <h2 className="font-sans text-sm font-semibold text-[#1a1c1b] uppercase tracking-wider flex items-center gap-1.5 mb-4">
          <Sparkles size={16} className="text-[#0F172A]" /> Custom Roadmaps
        </h2>
        
        <div className="kinetic-card bg-[rgba(15,23,42,0.02)] p-6 md:p-8 flex flex-col md:flex-row items-center gap-6 border-dashed border-2 border-[rgba(15,23,42,0.1)] justify-between">
          <div className="flex-1 text-center md:text-left">
            <h3 className="font-sans text-lg font-semibold text-[#0F172A] mb-2 flex items-center justify-center md:justify-start gap-2">
              Bring Your Own Path
              <span className="bg-[#0891B2]/10 text-[#0891B2] text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full">
                Coming Soon
              </span>
            </h3>
            <p className="font-sans text-sm text-[#64748B] leading-relaxed max-w-xl">
              Soon you'll be able to create custom roadmaps or upload your own curriculum (like a university syllabus or bootcamp schedule) and track your retention node-by-node.
            </p>
          </div>
          <div className="shrink-0 flex gap-3">
            <div className="w-12 h-12 rounded-xl bg-white border border-[rgba(15,23,42,0.08)] flex items-center justify-center shadow-sm">
              <Plus size={20} className="text-[#94a3b8]" />
            </div>
          </div>
        </div>
      </section>

    </div>
  );
}

export default Roadmaps;
