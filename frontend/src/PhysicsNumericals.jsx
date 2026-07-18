import React, { useEffect, useState, useCallback, Suspense, lazy } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, BookOpen, Eye, EyeOff, ChevronDown, ChevronRight, AlertCircle } from 'lucide-react';
import RayDiagram from './physics/RayDiagram';
import GraphDiagram from './physics/GraphDiagram';
import SchematicDiagram from './physics/SchematicDiagram';
import { useSeo } from './lib/useSeo';

// Lazy — mirrors LessonView.jsx; Three.js only loads if a problem carries a diagram3d.
const Physics3D = lazy(() => import('./physics/three/Physics3D.jsx'));
function Physics3DFallback() {
  return <div className="rounded-lg border border-[rgba(15,23,42,0.12)] bg-[#f9f9f6] animate-pulse" style={{ height: 320 }} />;
}

/**
 * PhysicsNumericals — phase-end problem sets for the physics-9 / physics-10 roadmaps.
 *
 * Fetches  /content/roadmaps/<roadmapSlug>/_numericals/<phaseSlug>.json
 * and renders each problem with:
 *  - prompt + given[] + problem_diagram  ALWAYS visible
 *  - "Reveal solution" button (predict-before-reveal)  →  solution_steps + solution_diagram + answer
 *
 * Matches the visual style of LessonView (white section cards, cyan accents, same
 * typography) without re-importing the 1400-line file.
 */

/* ── Shared diagram dispatcher (mirrors PhysicsDiagram in LessonView) ── */
function PhysicsDiagram({ diagram }) {
  if (!diagram || typeof diagram !== 'object') return null;
  if (diagram.type === 'ray') return <RayDiagram diagram={diagram} />;
  if (diagram.type === 'graph') return <GraphDiagram diagram={diagram} />;
  if (diagram.type === 'schematic') return <SchematicDiagram diagram={diagram} />;
  // image: render nothing for now (bucket URL logic lives in LessonView); circuit/free-body: pending
  return null;
}

/* ── Single problem card ── */
function ProblemCard({ problem, index }) {
  const [revealed, setReveal] = useState(false);

  return (
    <section className="bg-white border border-[rgba(15,23,42,0.08)] rounded-lg shadow-sm p-5 mb-4">
      {/* Problem header */}
      <div className="flex items-start gap-3 mb-3">
        <span className="shrink-0 w-7 h-7 rounded-full bg-[#0891B2]/10 text-[#0891B2] font-mono text-[12px] font-bold flex items-center justify-center">
          {index + 1}
        </span>
        <p className="font-sans text-sm font-semibold text-[#0F172A] leading-relaxed flex-1">
          {problem.prompt}
        </p>
      </div>

      {/* Given list */}
      {Array.isArray(problem.given) && problem.given.length > 0 && (
        <div className="ml-10 mb-3">
          <div className="font-sans text-[10px] font-bold uppercase tracking-wider text-[#64748B] mb-1.5">
            Given
          </div>
          <ul className="flex flex-col gap-1">
            {problem.given.map((g, i) => (
              <li key={i} className="font-mono text-[12.5px] text-[#0891B2] bg-[#0891B2]/[0.05] rounded px-2.5 py-1">
                {g}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Problem diagram (always visible) — diagram3d takes precedence if present */}
      {problem.problem_diagram3d ? (
        <div className="ml-10 mb-3">
          <Suspense fallback={<Physics3DFallback />}>
            <Physics3D diagram3d={problem.problem_diagram3d} />
          </Suspense>
        </div>
      ) : problem.problem_diagram && (
        <div className="ml-10 mb-3">
          <PhysicsDiagram diagram={problem.problem_diagram} />
        </div>
      )}

      {/* Reveal gate */}
      {!revealed ? (
        <button
          onClick={() => setReveal(true)}
          className="ml-10 flex items-center gap-2 text-sm font-semibold text-white bg-[#7C3AED] hover:bg-[#6D28D9] rounded px-3.5 py-2 transition-colors"
        >
          <Eye size={15} /> Reveal solution
        </button>
      ) : (
        <div className="ml-10 flex flex-col gap-3 animate-in fade-in duration-200">
          {/* Solution steps */}
          {Array.isArray(problem.solution_steps) && problem.solution_steps.length > 0 && (
            <div>
              <div className="font-sans text-[10px] font-bold uppercase tracking-wider text-[#7C3AED] mb-2">
                Solution
              </div>
              <ol className="flex flex-col gap-2">
                {problem.solution_steps.map((st, i) => (
                  <li key={i} className="flex items-start gap-2.5">
                    <span className="shrink-0 w-5 h-5 rounded-full bg-[#7C3AED]/10 text-[#7C3AED] font-mono text-[10px] font-bold flex items-center justify-center mt-0.5">
                      {i + 1}
                    </span>
                    <span className="font-sans text-sm text-[#0F172A] leading-relaxed">
                      {typeof st === 'string' ? st : (
                        <>
                          {st.narration}
                          {st.math && (
                            <span className="block font-mono text-[12.5px] text-[#0891B2] mt-0.5">
                              {st.math}
                            </span>
                          )}
                        </>
                      )}
                    </span>
                  </li>
                ))}
              </ol>
            </div>
          )}

          {/* Solution diagram — ONLY after reveal — diagram3d takes precedence if present */}
          {problem.solution_diagram3d ? (
            <div>
              <div className="font-sans text-[10px] font-bold uppercase tracking-wider text-[#7C3AED] mb-2">
                Diagram (after solution)
              </div>
              <Suspense fallback={<Physics3DFallback />}>
                <Physics3D diagram3d={problem.solution_diagram3d} />
              </Suspense>
            </div>
          ) : problem.solution_diagram && (
            <div>
              <div className="font-sans text-[10px] font-bold uppercase tracking-wider text-[#7C3AED] mb-2">
                Diagram (after solution)
              </div>
              <PhysicsDiagram diagram={problem.solution_diagram} />
            </div>
          )}

          {/* Answer box */}
          <div className="rounded-lg border border-[#0F766E]/20 bg-[#0F766E]/[0.05] p-3">
            <div className="font-sans text-[10px] font-bold uppercase tracking-wider text-[#0F766E] mb-1">
              Answer
            </div>
            <p className="font-sans text-sm font-semibold text-[#0F172A] leading-relaxed">
              {problem.answer}
            </p>
          </div>

          {/* Collapse button */}
          <button
            onClick={() => setReveal(false)}
            className="flex items-center gap-1.5 font-sans text-xs font-semibold text-[#64748B] hover:text-[#0F172A] transition-colors self-start"
          >
            <EyeOff size={13} /> Hide solution
          </button>
        </div>
      )}
    </section>
  );
}

/* ── Main page ── */
export default function PhysicsNumericals() {
  const { roadmapSlug, phaseSlug } = useParams();
  const navigate = useNavigate();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useSeo(
    phaseSlug
      ? `Practice Numericals — ${phaseSlug.replace(/-/g, ' ')} | RetainHQ`
      : 'Practice Numericals | RetainHQ',
    'Phase-end numerical practice problems for physics with step-by-step solutions.'
  );

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(
          `/content/roadmaps/${roadmapSlug}/_numericals/${phaseSlug}.json`
        );
        if (!res.ok) throw new Error('not-found');
        const json = await res.json();
        if (!cancelled) setData(json);
      } catch (e) {
        if (!cancelled) setError(e.message === 'not-found' ? 'Practice set not found.' : 'Failed to load. Please try again.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, [roadmapSlug, phaseSlug]);

  return (
    <div className="max-w-4xl mx-auto w-full px-4 md:px-8 py-6 pb-24">
      {/* Back navigation */}
      <button
        onClick={() => navigate(`/roadmaps/${roadmapSlug}`)}
        className="flex items-center gap-1.5 font-sans text-sm text-[#0891B2] hover:text-[#0F172A] mb-6 transition-colors"
      >
        <ArrowLeft size={15} /> Back to roadmap
      </button>

      {loading && (
        <>
          <div className="mb-6">
            <div className="skeleton h-3 w-28 mb-2" />
            <div className="skeleton h-6 w-64 mb-2" />
            <div className="skeleton h-3 w-72" />
          </div>
          {[0, 1, 2].map((i) => (
            <section key={i} className="bg-white border border-[rgba(15,23,42,0.08)] rounded-lg shadow-sm p-5 mb-4">
              <div className="flex items-start gap-3 mb-3">
                <div className="skeleton shrink-0 w-7 h-7 rounded-full" />
                <div className="flex-1 flex flex-col gap-2">
                  <div className="skeleton h-3.5 w-full" />
                  <div className="skeleton h-3.5 w-2/3" />
                </div>
              </div>
              <div className="ml-10 skeleton h-9 w-40 rounded" />
            </section>
          ))}
        </>
      )}

      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-[#B91C1C]/20 bg-[#B91C1C]/[0.04] p-4 text-[#B91C1C] font-sans text-sm">
          <AlertCircle size={16} /> {error}
        </div>
      )}

      {data && !loading && (
        <>
          {/* Header */}
          <div className="mb-6">
            <p className="font-sans text-xs font-semibold uppercase tracking-widest text-[#0891B2] mb-1">
              Phase practice
            </p>
            <h1 className="font-sans text-xl font-bold text-[#0F172A] leading-snug">
              {data.phase || phaseSlug}
            </h1>
            {Array.isArray(data.problems) && (
              <p className="font-sans text-sm text-[#64748B] mt-1">
                {data.problems.length} numerical{data.problems.length !== 1 ? 's' : ''} — solve each before revealing the solution.
              </p>
            )}
          </div>

          {/* Problems */}
          {Array.isArray(data.problems) && data.problems.length > 0 ? (
            data.problems.map((p, i) => (
              <ProblemCard key={i} problem={p} index={i} />
            ))
          ) : (
            <p className="font-sans text-sm text-[#64748B]">No problems found in this set.</p>
          )}
        </>
      )}
    </div>
  );
}
