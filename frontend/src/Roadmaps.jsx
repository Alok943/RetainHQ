import React, { useEffect, useState, useMemo } from 'react';
import {
  GraduationCap, ListChecks, ArrowRight, Plus, Sparkles,
  ChevronDown, ChevronRight, LayoutGrid, List, ArrowUpDown,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { apiFetch } from './lib/api';
import { useAuth } from './lib/AuthContext';
import { getRoadmapStyle, RoadmapLogo } from './lib/roadmapVisuals';
import { useSeo } from './lib/useSeo';
import { DOMAINS, getRoadmapMeta } from './lib/roadmapDomains';
import { CAREER_PATHS } from './lib/careerPaths';
import { CONTENT_KEY_BY_TITLE } from './lib/contentRoadmaps';

// Trade-wise grouping (JD Research Run 3): roadmaps organized by the career track
// they build toward, ordered by the SDE → Backend → GenAI pathway + foundations.
// Each group carries the run-3 insight for that trade. Order matters: first match wins,
// so trade-specific patterns (backend/sql/ai) sit ABOVE the catch-all "python" foundation.


const SORT_OPTIONS = [
  { value: 'title-asc',     label: 'A → Z' },
  { value: 'title-desc',    label: 'Z → A' },
  { value: 'progress-desc', label: 'Progress ↑' },
  { value: 'progress-asc',  label: 'Progress ↓' },
];



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

function RoadmapCard({ rm, index, onClick, meta }) {
  const { Icon, accent } = getRoadmapStyle(rm.title);
  const pct = useCountUp(rm.progress_pct ?? 0);

  return (
    <article
      onClick={onClick}
      style={{ animationDelay: `${index * 60}ms`, animationFillMode: 'backwards' }}
      className="bg-white border border-[rgba(15,23,42,0.08)] rounded-3xl shadow-sm p-5 cursor-pointer group flex flex-col min-h-[210px] transition-all duration-200 hover:-translate-y-1 hover:shadow-xl animate-in fade-in slide-in-from-bottom-3"
    >
      <div className="flex items-start justify-between mb-4">
        <div
          className="w-12 h-12 rounded-2xl flex items-center justify-center shrink-0"
          style={{ backgroundColor: `${accent}14`, border: `1px solid ${accent}26` }}
        >
          <RoadmapLogo title={rm.title} Icon={Icon} accent={accent} size={24} />
        </div>
        <span className="font-mono text-sm font-semibold" style={{ color: accent }}>{pct}%</span>
      </div>

      <div className="flex-1 min-w-0 flex flex-col">
        <h3 className="font-sans text-base md:text-lg font-semibold text-[#0F172A] leading-snug line-clamp-2 mb-1.5">
          {rm.title}
        </h3>
        <p className="font-sans text-xs text-[#64748B] leading-relaxed line-clamp-3 mb-3">
          {rm.description}
        </p>
        
        {meta && (
          <div className="flex flex-wrap gap-2 mt-auto">
            <span className="bg-[rgba(15,23,42,0.04)] text-[#64748B] px-2 py-1 rounded text-[10px] font-mono font-medium">
              {meta.lessonCount} lessons
            </span>
            <span className="bg-[rgba(15,23,42,0.04)] text-[#64748B] px-2 py-1 rounded text-[10px] font-mono font-medium">
              ~{meta.hours} hrs
            </span>
            {meta.pathsCount > 0 && (
              <span className="bg-[#0891B2]/10 text-[#0891B2] px-2 py-1 rounded text-[10px] font-mono font-medium">
                builds {meta.pathsCount} path{meta.pathsCount !== 1 ? 's' : ''}
              </span>
            )}
          </div>
        )}
      </div>

      <div className="mt-4">
        <div className="w-full h-1.5 rounded-full bg-[rgba(15,23,42,0.06)] overflow-hidden mb-2.5">
          <div
            className="h-full rounded-full transition-all duration-700 ease-out"
            style={{ width: `${rm.progress_pct ?? 0}%`, backgroundColor: accent }}
          />
        </div>
        <div className="flex items-center justify-between">
          <span className="font-mono text-[10px] text-[#64748B]">{rm.done_nodes}/{rm.total_nodes} topics</span>
          <ArrowRight
            size={15}
            style={{ color: accent }}
            className="opacity-0 -translate-x-1 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-200"
          />
        </div>
      </div>
    </article>
  );
}

function CollapsibleGroup({ label, blurb, items, navigate }) {
  const [open, setOpen] = useState(true);

  return (
    <div className="mb-6">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2 w-full text-left mb-1 group/hdr"
      >
        {open
          ? <ChevronDown size={14} className="text-[#64748B] shrink-0" />
          : <ChevronRight size={14} className="text-[#64748B] shrink-0" />}
        <span className="font-sans text-xs font-semibold text-[#0F172A] uppercase tracking-wider">
          {label}
        </span>
        <span className="font-mono text-[10px] text-[#94A3B8]">({items.length})</span>
        <div className="flex-1 h-px bg-[rgba(15,23,42,0.07)] ml-1" />
      </button>

      {blurb && (
        <p className="font-sans text-xs text-[#64748B] mb-3 ml-6 leading-snug">{blurb}</p>
      )}

      {open && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {items.map((rm, i) => (
            <RoadmapCard key={rm.id} rm={rm} index={i} meta={rm.meta} onClick={() => navigate(`/roadmaps/${rm.slug || rm.id}`)} />
          ))}
        </div>
      )}
    </div>
  );
}

function Roadmaps() {
  const navigate = useNavigate();
  const [roadmaps, setRoadmaps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('grouped'); // 'grouped' | 'list'
  const [sortBy, setSortBy] = useState('title-asc');
  const { session } = useAuth();
  const [contentManifest, setContentManifest] = useState(null);

  useEffect(() => {
    fetch('/content/manifest.json')
      .then((r) => r.ok ? r.json() : {})
      .then(setContentManifest)
      .catch(() => setContentManifest({}));
  }, []);

  const roadmapsWithMeta = useMemo(() => {
    return roadmaps.map(rm => {
      const contentKey = rm.slug || CONTENT_KEY_BY_TITLE[rm.title];
      const lessonCount = contentManifest && contentManifest[contentKey] ? Object.keys(contentManifest[contentKey]).length : 0;
      const hours = Math.max(1, Math.round((lessonCount * 15) / 60));
      
      const pathsCount = CAREER_PATHS.filter(p => p.roadmaps.some(r => r.match && rm.title.toLowerCase().includes(r.match.toLowerCase()))).length;
      
      return { ...rm, meta: { lessonCount, hours, pathsCount } };
    });
  }, [roadmaps, contentManifest]);

  useSeo(
    'Learning Roadmaps · DSA, System Design, Python & SQL | RetainHQ',
    'Structured learning roadmaps for DSA, system design, Python, SQL, Core CS, and aptitude — each topic tracked by spaced repetition so what you study actually sticks.'
  );

  useEffect(() => {
    async function fetchRoadmaps() {
      try {
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

  const sorted = useMemo(() => {
    const copy = [...roadmapsWithMeta];
    if (sortBy === 'title-asc')     return copy.sort((a, b) => a.title.localeCompare(b.title));
    if (sortBy === 'title-desc')    return copy.sort((a, b) => b.title.localeCompare(a.title));
    if (sortBy === 'progress-desc') return copy.sort((a, b) => (b.progress_pct ?? 0) - (a.progress_pct ?? 0));
    if (sortBy === 'progress-asc')  return copy.sort((a, b) => (a.progress_pct ?? 0) - (b.progress_pct ?? 0));
    return copy;
  }, [roadmapsWithMeta, sortBy]);

  const grouped = useMemo(() => {
    const map = {};
    for (const rm of roadmapsWithMeta) {
      const meta = getRoadmapMeta(rm.slug || rm.id);
      const domain = meta.domain;
      if (!map[domain]) map[domain] = [];
      map[domain].push(rm);
    }
    
    const result = [];
    for (const [slug, dInfo] of Object.entries(DOMAINS)) {
      if (map[slug]?.length) {
        const items = map[slug].sort((a, b) => {
          const aMeta = getRoadmapMeta(a.slug || a.id);
          const bMeta = getRoadmapMeta(b.slug || b.id);
          const aLive = aMeta.flagship && a.meta.lessonCount > 0 ? 1 : 0;
          const bLive = bMeta.flagship && b.meta.lessonCount > 0 ? 1 : 0;
          
          if (aLive !== bLive) return bLive - aLive;
          if ((b.progress_pct || 0) !== (a.progress_pct || 0)) return (b.progress_pct || 0) - (a.progress_pct || 0);
          return a.title.localeCompare(b.title);
        });
        
        result.push({
          label: `${dInfo.emoji} ${dInfo.title}`,
          blurb: dInfo.blurb,
          items
        });
      }
    }
    return result;
  }, [roadmapsWithMeta]);

  const flagships = useMemo(() => {
    return roadmapsWithMeta.filter(rm => {
      const meta = getRoadmapMeta(rm.slug || rm.id);
      return meta.flagship && rm.meta.lessonCount > 0;
    });
  }, [roadmapsWithMeta]);

  return (
    <div className="relative max-w-5xl mx-auto w-full p-4 md:p-8 pb-20 md:pb-8 animate-in fade-in duration-300">
      <div className="relative z-10 flex flex-col gap-8">


      <header className="mb-2">
        <h2 className="font-sans text-2xl font-semibold text-[#0F172A] flex items-center gap-2">
          <GraduationCap size={24} className="text-[#0891B2]" /> Learn
        </h2>
        <p className="font-sans text-sm text-[#64748B] mt-1">Structured roadmaps and step-through lessons, tracked by spaced repetition so what you study sticks.</p>
      </header>
      
      {flagships.length > 0 && viewMode === 'grouped' && (
        <section className="mb-4">
          <h2 className="font-sans text-sm font-semibold text-[#1a1c1b] uppercase tracking-wider flex items-center gap-1.5 mb-3">
            Flagships
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-3">
            {flagships.map((rm) => (
              <button
                key={rm.id}
                onClick={() => navigate(`/roadmaps/${rm.slug || rm.id}`)}
                className="bg-white border border-[rgba(15,23,42,0.08)] rounded-xl p-3 flex items-center gap-3 text-left hover:-translate-y-0.5 hover:shadow-md transition-all group"
              >
                <div className="w-10 h-10 rounded-lg bg-[rgba(15,23,42,0.03)] flex items-center justify-center shrink-0 border border-[rgba(15,23,42,0.05)]">
                   <RoadmapLogo title={rm.title} Icon={getRoadmapStyle(rm.title).Icon} accent={getRoadmapStyle(rm.title).accent} size={20} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-sans text-sm font-semibold text-[#0F172A] truncate">{rm.title}</div>
                  <div className="font-sans text-[10px] text-[#0891B2] font-semibold mt-0.5">{rm.meta.lessonCount} lessons</div>
                </div>
              </button>
            ))}
          </div>
        </section>
      )}


      <section>
        {/* Controls bar */}
        <div className="flex items-center justify-between mb-4 gap-3 flex-wrap">
          <h2 className="font-sans text-sm font-semibold text-[#1a1c1b] uppercase tracking-wider flex items-center gap-1.5">
            <ListChecks size={16} className="text-[#0F172A]" /> All Roadmaps
          </h2>

          <div className="flex items-center gap-2">
            {/* Sort dropdown — only in list mode */}
            {viewMode === 'list' && (
              <div className="flex items-center gap-1.5">
                <ArrowUpDown size={13} className="text-[#64748B]" />
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="text-xs font-sans text-[#0F172A] bg-white border border-[rgba(15,23,42,0.12)] rounded-lg px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-[#0891B2] cursor-pointer"
                >
                  {SORT_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>
            )}

            {/* View toggle */}
            <div className="flex rounded-lg border border-[rgba(15,23,42,0.12)] overflow-hidden">
              <button
                onClick={() => setViewMode('grouped')}
                title="Group by category"
                className={`px-2.5 py-1.5 flex items-center gap-1 text-xs font-sans transition-colors ${
                  viewMode === 'grouped'
                    ? 'bg-[#0F172A] text-white'
                    : 'bg-white text-[#64748B] hover:bg-[rgba(15,23,42,0.04)]'
                }`}
              >
                <LayoutGrid size={13} /> Grouped
              </button>
              <button
                onClick={() => setViewMode('list')}
                title="Sort & list all"
                className={`px-2.5 py-1.5 flex items-center gap-1 text-xs font-sans border-l border-[rgba(15,23,42,0.12)] transition-colors ${
                  viewMode === 'list'
                    ? 'bg-[#0F172A] text-white'
                    : 'bg-white text-[#64748B] hover:bg-[rgba(15,23,42,0.04)]'
                }`}
              >
                <List size={13} /> All
              </button>
            </div>
          </div>
        </div>

        {/* Content */}
        {loading ? (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {[0, 1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="bg-white border border-[rgba(15,23,42,0.08)] rounded-3xl shadow-sm p-5 flex flex-col min-h-[210px]">
                <div className="skeleton w-12 h-12 rounded-2xl mb-4" />
                <div className="flex-1 space-y-2">
                  <div className="skeleton h-4 w-2/3" />
                  <div className="skeleton h-3 w-full" />
                  <div className="skeleton h-3 w-1/2" />
                </div>
                <div className="skeleton h-1.5 w-full rounded-full mt-4" />
              </div>
            ))}
          </div>
        ) : roadmaps.length === 0 ? (
          <div className="p-8 text-center text-[#64748B] bg-white rounded border border-[rgba(15,23,42,0.1)]">No roadmaps found.</div>
        ) : viewMode === 'grouped' ? (
          <div>
            {grouped.map(({ label, blurb, items }) => (
              <CollapsibleGroup key={label} label={label} blurb={blurb} items={items} navigate={navigate} />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {sorted.map((rm, i) => (
              <RoadmapCard key={rm.id} rm={rm} index={i} meta={rm.meta} onClick={() => navigate(`/roadmaps/${rm.slug || rm.id}`)} />
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
    </div>
  );
}

export default Roadmaps;
