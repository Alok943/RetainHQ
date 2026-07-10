import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { School, ChevronRight, Search, ArrowLeft, BookOpen } from 'lucide-react';
import { apiFetch } from './lib/api';
import { useSeo } from './lib/useSeo';
import { getRoadmapStyle, RoadmapLogo } from './lib/roadmapVisuals';

/**
 * SchoolRoadmaps — the Class -> Subject -> Chapter browser for audience='school'.
 *
 * Replaces the career Roadmaps.jsx page for school users (rendered by that same
 * component when the account's audience is 'school' — see the dispatch at the
 * bottom of Roadmaps.jsx). The career page's domain grouping (Placement Prep /
 * Software Engineering / ... / B.Tech Core) is career-specific vocabulary and a
 * school roadmap falling through to its 'btech-core' fallback is exactly the
 * "header still shows BTech core" bug — this component never touches that path.
 *
 * Data model: each school SUBJECT is one roadmap (today: just Physics — Class 9
 * & 10). A CHAPTER is a `phase` on that roadmap's nodes, authored as
 * "Class 9 · Motion" / "Class 10 · Light" (seed_physics_school.py). This page
 * parses that convention to derive the Class step without any new backend field —
 * when Chemistry/Math/Bio land as more school roadmaps, they slot in for free as
 * long as their phases follow the same "Class N · Chapter" naming.
 */

const CLASS_ORDER = ['Class 9', 'Class 10', 'Class 11', 'Class 12'];

function parsePhase(phase) {
  // "Class 9 · Motion" -> { cls: "Class 9", chapter: "Motion" }. Anything that
  // doesn't match the convention still gets a class bucket ("General") instead
  // of silently vanishing.
  const m = /^(Class\s*\d+)\s*·\s*(.+)$/.exec(phase || '');
  return m ? { cls: m[1], chapter: m[2] } : { cls: 'General', chapter: phase || 'Untitled' };
}

const phaseToSlug = (phase) => phase.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

function SchoolRoadmaps() {
  const navigate = useNavigate();
  const [roadmaps, setRoadmaps] = useState(null); // null = loading
  const [details, setDetails] = useState({});     // roadmapId -> { title, slug, nodes }
  const [selectedClass, setSelectedClass] = useState(null);
  const [selectedSubject, setSelectedSubject] = useState(null); // roadmap id
  const [query, setQuery] = useState('');

  useSeo(
    'School — Class 9 & 10 | RetainHQ',
    'NCERT-aligned Physics, chapter by chapter, tracked by spaced repetition so what you study for boards actually sticks.'
  );

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const list = await apiFetch('/api/roadmaps/', { optionalAuth: true });
        if (cancelled) return;
        setRoadmaps(list);
        const entries = await Promise.all(
          list.map((rm) =>
            apiFetch(`/api/roadmaps/${rm.slug || rm.id}`, { optionalAuth: true })
              .then((d) => [rm.id, { title: d.title, slug: d.slug || rm.slug, nodes: d.nodes || [] }])
              .catch(() => [rm.id, { title: rm.title, slug: rm.slug, nodes: [] }])
          )
        );
        if (!cancelled) setDetails(Object.fromEntries(entries));
      } catch {
        if (!cancelled) setRoadmaps([]);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  // { className: { roadmapId: { title, slug, chapters: [{phase, chapter, done, total}] } } }
  const byClass = useMemo(() => {
    const out = {};
    for (const rm of roadmaps || []) {
      const detail = details[rm.id];
      if (!detail) continue;
      const byPhase = new Map();
      detail.nodes.forEach((n) => {
        if (!byPhase.has(n.phase)) byPhase.set(n.phase, []);
        byPhase.get(n.phase).push(n);
      });
      for (const [phase, nodes] of byPhase) {
        const { cls, chapter } = parsePhase(phase);
        out[cls] = out[cls] || {};
        out[cls][rm.id] = out[cls][rm.id] || { title: detail.title, slug: detail.slug, chapters: [] };
        out[cls][rm.id].chapters.push({
          phase,
          chapter,
          done: nodes.filter((n) => n.status === 'done').length,
          total: nodes.length,
        });
      }
    }
    return out;
  }, [roadmaps, details]);

  const classNames = useMemo(() => {
    const found = Object.keys(byClass);
    return [...CLASS_ORDER.filter((c) => found.includes(c)), ...found.filter((c) => !CLASS_ORDER.includes(c))];
  }, [byClass]);

  // Auto-advance: one class -> select it; one subject in that class -> select it.
  useEffect(() => {
    if (!selectedClass && classNames.length === 1) setSelectedClass(classNames[0]);
  }, [classNames, selectedClass]);
  useEffect(() => {
    if (!selectedClass) return;
    const subjects = Object.keys(byClass[selectedClass] || {});
    if (!selectedSubject && subjects.length === 1) setSelectedSubject(subjects[0]);
  }, [selectedClass, byClass, selectedSubject]);

  const loading = roadmaps === null;
  const subjectsInClass = selectedClass ? byClass[selectedClass] || {} : {};
  const subjectIds = Object.keys(subjectsInClass);
  const chapters = selectedSubject ? subjectsInClass[selectedSubject]?.chapters || [] : [];
  const filteredChapters = query.trim()
    ? chapters.filter((c) => c.chapter.toLowerCase().includes(query.trim().toLowerCase()))
    : chapters;

  const goChapter = (subjectId, phase) => {
    const slug = subjectsInClass[subjectId]?.slug || subjectId;
    navigate(`/roadmaps/${slug}`, { state: { expandOnlyPhase: phase } });
  };

  return (
    <div className="relative max-w-5xl mx-auto w-full p-4 md:p-8 pb-20 md:pb-8 animate-in fade-in duration-300">
      <header className="mb-6">
        <h2 className="font-sans text-2xl font-semibold text-[#0F172A] flex items-center gap-2">
          <School size={24} className="text-[#0891B2]" /> School
        </h2>
        <p className="font-sans text-sm text-[#64748B] mt-1">
          NCERT concept-by-concept, tracked by spaced repetition so nothing you learn is forgotten by boards.
        </p>
      </header>

      {/* Breadcrumb */}
      {(selectedClass || selectedSubject) && (
        <div className="flex items-center gap-1.5 mb-5 font-sans text-sm">
          <button
            onClick={() => { setSelectedClass(null); setSelectedSubject(null); setQuery(''); }}
            className="text-[#64748B] hover:text-[#0891B2] transition-colors"
          >
            Classes
          </button>
          {selectedClass && (
            <>
              <ChevronRight size={14} className="text-[#94A3B8]" />
              <button
                onClick={() => { setSelectedSubject(null); setQuery(''); }}
                className={selectedSubject ? 'text-[#64748B] hover:text-[#0891B2] transition-colors' : 'text-[#0F172A] font-semibold'}
              >
                {selectedClass}
              </button>
            </>
          )}
          {selectedSubject && (
            <>
              <ChevronRight size={14} className="text-[#94A3B8]" />
              <span className="text-[#0F172A] font-semibold">{subjectsInClass[selectedSubject]?.title}</span>
            </>
          )}
        </div>
      )}

      {loading ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="skeleton h-28 rounded-2xl" />
          ))}
        </div>
      ) : classNames.length === 0 ? (
        <div className="p-8 text-center text-[#64748B] bg-white rounded border border-[rgba(15,23,42,0.1)]">
          No school roadmaps yet.
        </div>
      ) : !selectedClass ? (
        /* Step 1: Class */
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {classNames.map((cls) => {
            const subjects = Object.values(byClass[cls]);
            const total = subjects.reduce((s, sub) => s + sub.chapters.reduce((a, c) => a + c.total, 0), 0);
            const done = subjects.reduce((s, sub) => s + sub.chapters.reduce((a, c) => a + c.done, 0), 0);
            return (
              <button
                key={cls}
                onClick={() => setSelectedClass(cls)}
                className="bg-white border border-[rgba(15,23,42,0.08)] rounded-2xl shadow-sm p-5 text-left hover:-translate-y-1 hover:shadow-xl transition-all duration-200"
              >
                <div className="w-11 h-11 rounded-xl bg-[#0891B2]/10 flex items-center justify-center mb-3">
                  <School size={20} className="text-[#0891B2]" />
                </div>
                <h3 className="font-sans text-base font-semibold text-[#0F172A]">{cls}</h3>
                <p className="font-mono text-[11px] text-[#64748B] mt-1">
                  {subjects.length} subject{subjects.length !== 1 ? 's' : ''} · {total > 0 ? Math.round((done / total) * 100) : 0}% done
                </p>
              </button>
            );
          })}
        </div>
      ) : !selectedSubject ? (
        /* Step 2: Subject */
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {subjectIds.map((sid) => {
            const sub = subjectsInClass[sid];
            const { Icon, accent } = getRoadmapStyle(sub.title);
            const total = sub.chapters.reduce((a, c) => a + c.total, 0);
            const done = sub.chapters.reduce((a, c) => a + c.done, 0);
            return (
              <button
                key={sid}
                onClick={() => setSelectedSubject(sid)}
                className="bg-white border border-[rgba(15,23,42,0.08)] rounded-2xl shadow-sm p-5 text-left hover:-translate-y-1 hover:shadow-xl transition-all duration-200"
              >
                <div className="w-11 h-11 rounded-xl flex items-center justify-center mb-3" style={{ backgroundColor: `${accent}14` }}>
                  <RoadmapLogo title={sub.title} Icon={Icon} accent={accent} size={20} />
                </div>
                <h3 className="font-sans text-base font-semibold text-[#0F172A]">{sub.title}</h3>
                <p className="font-mono text-[11px] text-[#64748B] mt-1">
                  {sub.chapters.length} chapters · {total > 0 ? Math.round((done / total) * 100) : 0}% done
                </p>
              </button>
            );
          })}
        </div>
      ) : (
        /* Step 3: Chapter */
        <div>
          {chapters.length > 6 && (
            <div className="relative mb-4">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#94A3B8]" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search chapters…"
                className="w-full pl-9 pr-3 py-2.5 rounded-lg border border-[rgba(15,23,42,0.12)] bg-white font-sans text-sm text-[#0F172A] placeholder:text-[#94A3B8] focus:outline-none focus:border-[#0891B2] focus:ring-2 focus:ring-[#0891B2]/20"
              />
            </div>
          )}
          {filteredChapters.length === 0 ? (
            <p className="font-sans text-sm text-[#64748B] p-6 text-center">No chapters match "{query}".</p>
          ) : (
            <div className="flex flex-col gap-2">
              {filteredChapters.map((c) => {
                const pct = c.total > 0 ? Math.round((c.done / c.total) * 100) : 0;
                return (
                  <button
                    key={c.phase}
                    onClick={() => goChapter(selectedSubject, c.phase)}
                    className="w-full flex items-center gap-3 bg-white border border-[rgba(15,23,42,0.08)] rounded-xl px-4 py-3.5 text-left hover:border-[#0891B2]/40 hover:bg-[#0891B2]/[0.03] transition-colors group"
                  >
                    <div className="w-9 h-9 rounded-lg bg-[rgba(15,23,42,0.04)] flex items-center justify-center shrink-0">
                      <BookOpen size={16} className="text-[#0891B2]" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-sans text-sm font-semibold text-[#0F172A] truncate">{c.chapter}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <div className="w-24 h-1 rounded-full bg-[rgba(15,23,42,0.08)] overflow-hidden">
                          <div className="h-full bg-[#0891B2] rounded-full" style={{ width: `${pct}%` }} />
                        </div>
                        <span className="font-mono text-[10px] text-[#64748B]">{c.done}/{c.total}</span>
                      </div>
                    </div>
                    <ChevronRight size={16} className="text-[#94A3B8] shrink-0 group-hover:text-[#0891B2] group-hover:translate-x-0.5 transition-all" />
                  </button>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default SchoolRoadmaps;
