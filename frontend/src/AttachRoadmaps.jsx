import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ListChecks, Loader2, Minus, Plus, X } from 'lucide-react';
import { apiFetch } from './lib/api';

// Shared by CareerTree (post-commit) and CareerOnboarding (mid-flow). Onboarding
// is where the need actually shows up: `ai_engineer.v2` has no DSA subject at
// all, and career_tree.py rejects an invented subject as a hard-rule violation,
// so a user who wants DSA can regenerate forever and never get it. The backend
// guard for these routes is deliberately `_get_active_goal` (not
// `..._with_tree`) so this works before the tree is committed.

// Attach catalog or personal roadmaps to the goal so the planner schedules from
// them too. One click: subject and priority are derived server-side from the
// roadmap, so there's no form to fill — refine them afterwards if you care.
export default function AttachedRoadmaps({ onChanged }) {
  const navigate = useNavigate();
  const [attached, setAttached] = useState(null);
  const [available, setAvailable] = useState(null);
  const [picking, setPicking] = useState(false);
  const [tab, setTab] = useState('inbuilt');
  const [busyId, setBusyId] = useState(null);
  // Distinct from "loaded and genuinely empty" — the Home.jsx lesson (2026-07-24):
  // a failed fetch must never render as "you have nothing".
  const [loadError, setLoadError] = useState(false);
  const [actionError, setActionError] = useState('');

  const load = async () => {
    try {
      const [a, av] = await Promise.all([
        apiFetch('/api/career/roadmaps/'),
        apiFetch('/api/career/roadmaps/available'),
      ]);
      setAttached(a);
      setAvailable(av);
      setLoadError(false);
    } catch {
      setLoadError(true);
    }
  };

  useEffect(() => { load(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, []);

  const attach = async (roadmapId) => {
    setBusyId(roadmapId);
    setActionError('');
    try {
      await apiFetch('/api/career/roadmaps/', {
        method: 'POST',
        body: JSON.stringify({ roadmap_id: roadmapId }),
      });
      await load();
      onChanged?.();
      setPicking(false);
    } catch (err) {
      setActionError(err.message);
    } finally {
      setBusyId(null);
    }
  };

  const detach = async (roadmapId, title) => {
    // Say plainly what is and isn't lost — detaching stops planning, it does not
    // erase evidence, and users will assume the opposite unless told.
    if (!window.confirm(`Stop planning from "${title}"?\n\nYour progress and review history are kept — it just won't appear in your daily plan.`)) return;
    setBusyId(roadmapId);
    setActionError('');
    try {
      await apiFetch(`/api/career/roadmaps/${roadmapId}`, { method: 'DELETE' });
      await load();
      onChanged?.();
    } catch (err) {
      setActionError(err.message);
    } finally {
      setBusyId(null);
    }
  };

  if (loadError) {
    return (
      <div className="bg-white border border-[rgba(15,23,42,0.08)] rounded-2xl p-4">
        <div className="font-sans text-sm text-[#ba1a1a] mb-2">Couldn't load your roadmaps.</div>
        <button onClick={load} className="font-sans text-sm font-semibold underline underline-offset-4 text-[#ba1a1a]">Retry</button>
      </div>
    );
  }
  if (attached === null) return <div className="skeleton h-16 w-full rounded-2xl" />;

  const list = (available?.[tab === 'inbuilt' ? 'inbuilt' : 'mine']) || [];

  return (
    <div className="bg-white border border-[rgba(15,23,42,0.08)] rounded-2xl p-4">
      <div className="flex items-center justify-between gap-3 mb-3">
        <h3 className="font-sans text-sm font-semibold text-[#0F172A] flex items-center gap-2">
          <ListChecks size={16} className="text-[#0891B2]" /> Roadmaps in your plan
        </h3>
        <button
          onClick={() => setPicking((p) => !p)}
          className="font-sans text-xs font-semibold text-[#0891B2] hover:text-[#0F172A] flex items-center gap-1"
        >
          {picking ? <X size={14} /> : <Plus size={14} />} {picking ? 'Close' : 'Add roadmap'}
        </button>
      </div>

      {actionError && (
        <div className="mb-3 px-3 py-2 rounded-lg bg-red-50 border border-red-200 font-sans text-xs text-red-700">{actionError}</div>
      )}

      {attached.length === 0 ? (
        <p className="font-sans text-xs text-[#64748B]">
          Only your career tree feeds today's plan. Add a roadmap to schedule from it too.
        </p>
      ) : (
        <ul className="flex flex-col gap-1.5">
          {attached.map((r) => (
            <li key={r.roadmap_id} className="flex items-center justify-between gap-3 py-1.5 border-b border-[rgba(15,23,42,0.06)] last:border-0">
              <div className="min-w-0">
                <div className="font-sans text-sm text-[#0F172A] truncate">{r.title}</div>
                <div className="font-sans text-[11px] text-[#64748B]">{r.node_count} nodes · counted as “{r.subject}”</div>
              </div>
              <button
                onClick={() => detach(r.roadmap_id, r.title)}
                disabled={busyId === r.roadmap_id}
                title="Stop planning from this roadmap"
                className="shrink-0 text-[#64748B] hover:text-[#ba1a1a] p-1.5 rounded-full hover:bg-[rgba(15,23,42,0.04)] transition-colors disabled:opacity-40"
              >
                {busyId === r.roadmap_id ? <Loader2 size={14} className="animate-spin" /> : <Minus size={14} />}
              </button>
            </li>
          ))}
        </ul>
      )}

      {picking && (
        <div className="mt-4 pt-3 border-t border-[rgba(15,23,42,0.08)]">
          <div className="flex gap-1 mb-3">
            {[['inbuilt', 'Built-in'], ['mine', 'Your own']].map(([key, label]) => (
              <button
                key={key}
                onClick={() => setTab(key)}
                className={`font-sans text-xs font-semibold px-3 py-1.5 rounded-full transition-colors ${
                  tab === key ? 'bg-[#0891B2] text-white' : 'text-[#64748B] hover:bg-[rgba(15,23,42,0.04)]'
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          {list.length === 0 ? (
            <div className="font-sans text-xs text-[#64748B]">
              {tab === 'mine' ? (
                <>
                  You haven't built your own roadmap yet.{' '}
                  <button onClick={() => navigate('/paths')} className="font-semibold text-[#0891B2] underline underline-offset-2">
                    Build one from a syllabus
                  </button>
                </>
              ) : (
                'Nothing left to add — everything available is already in your plan.'
              )}
            </div>
          ) : (
            <ul className="flex flex-col gap-1">
              {list.map((r) => (
                <li key={r.id} className="flex items-center justify-between gap-3 py-1.5">
                  <div className="min-w-0">
                    <div className="font-sans text-sm text-[#0F172A] truncate">{r.title}</div>
                    <div className="font-sans text-[11px] text-[#64748B]">{r.node_count} nodes</div>
                  </div>
                  <button
                    onClick={() => attach(r.id)}
                    disabled={busyId === r.id}
                    className="shrink-0 font-sans text-xs font-semibold text-white bg-[#0891B2] hover:bg-[#0F172A] px-3 py-1.5 rounded-full transition-colors disabled:opacity-40 flex items-center gap-1"
                  >
                    {busyId === r.id ? <Loader2 size={12} className="animate-spin" /> : <Plus size={12} />} Add
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
