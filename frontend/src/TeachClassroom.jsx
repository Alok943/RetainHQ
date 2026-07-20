import React, { useEffect, useMemo, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  Presentation, ArrowLeft, Users, Copy, Grid3x3, TrendingUp, ListChecks,
  BookOpen, AlertTriangle, ShieldAlert, Target, X, ChevronUp, ChevronDown,
  ArrowUpDown, RefreshCw, Pencil, Trash2, Check,
} from 'lucide-react';
import { apiFetch } from './lib/api';
import { useClassrooms } from './lib/ClassroomsContext';
import { useToast } from './lib/ToastContext';

/**
 * TeachClassroom — /teach/:id. Three tabs (Overview / Gap Map / Students) per
 * SPEC-teacher-dashboard.md §7. No single-classroom GET exists on the backend
 * (only /mine, which lists all of a teacher's classrooms) — classroom meta
 * (name/school_name/join_code/member_count) is read by finding this id in
 * that list, same as Teach.jsx already fetched it.
 */

const STATUS_COLOR = {
  weak: { bg: 'rgba(185,28,28,0.14)', border: 'rgba(185,28,28,0.45)', text: '#B91C1C', label: 'Weak' },
  developing: { bg: 'rgba(180,83,9,0.14)', border: 'rgba(180,83,9,0.45)', text: '#B45309', label: 'Developing' },
  strong: { bg: 'rgba(15,118,110,0.14)', border: 'rgba(15,118,110,0.45)', text: '#0F766E', label: 'Strong' },
  untouched: { bg: 'rgba(15,23,42,0.05)', border: 'rgba(15,23,42,0.14)', text: '#94A3B8', label: 'Untouched' },
  insufficient_data: { bg: 'rgba(15,23,42,0.03)', border: 'rgba(15,23,42,0.1)', text: '#94A3B8', label: 'Not enough data' },
};

function TeachClassroom() {
  const { id } = useParams();
  const navigate = useNavigate();
  const toast = useToast();

  // Classroom meta (name/school_name/join_code/member_count) is read by finding
  // this id in the shared /mine list rather than a dedicated single-classroom
  // GET (none exists). Comes from ClassroomsContext, already fetched for the nav.
  const { classrooms, loading: classroomsLoading, refresh: refreshClassrooms } = useClassrooms();
  const meta = useMemo(
    () => (classrooms?.teaching || []).find((c) => c.id === id) || null,
    [classrooms, id],
  );
  const metaLoading = classroomsLoading;
  const notFound = !classroomsLoading && !meta;
  const [tab, setTab] = useState('overview');
  const [regenerating, setRegenerating] = useState(false);

  const [roadmapInfo, setRoadmapInfo] = useState(null); // { roadmap_ids, available }
  const [roadmapLoading, setRoadmapLoading] = useState(true);
  const [showAssignForm, setShowAssignForm] = useState(false);

  const [overview, setOverview] = useState(null);
  const [overviewLoading, setOverviewLoading] = useState(true);
  const [overviewError, setOverviewError] = useState(null);

  const [roster, setRoster] = useState(null);
  const [rosterLoading, setRosterLoading] = useState(false);
  const [rosterError, setRosterError] = useState(null);

  const loadOverview = () => {
    setOverviewLoading(true);
    apiFetch(`/api/classrooms/${id}/overview`)
      .then(setOverview)
      .catch((e) => setOverviewError(e.message))
      .finally(() => setOverviewLoading(false));
  };

  const loadRoster = () => {
    setRosterLoading(true);
    apiFetch(`/api/classrooms/${id}/students`)
      .then((d) => setRoster(d.students || []))
      .catch((e) => setRosterError(e.message))
      .finally(() => setRosterLoading(false));
  };

  useEffect(() => {
    setRoadmapLoading(true);
    apiFetch(`/api/classrooms/${id}/roadmaps`)
      .then(setRoadmapInfo)
      .catch(() => setRoadmapInfo({ roadmap_ids: [], available: [] }))
      .finally(() => setRoadmapLoading(false));

    loadOverview();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const hasRoadmaps = (roadmapInfo?.roadmap_ids?.length || 0) > 0;

  useEffect(() => {
    if (hasRoadmaps) loadRoster();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasRoadmaps, id]);

  const assignedRoadmaps = useMemo(() => {
    if (!roadmapInfo) return [];
    const byId = new Map(roadmapInfo.available.map((r) => [r.id, r.title]));
    return roadmapInfo.roadmap_ids.map((rid) => ({ id: rid, title: byId.get(rid) || 'Untitled subject' }));
  }, [roadmapInfo]);

  const rosterByMember = useMemo(() => new Map((roster || []).map((s) => [s.member_id, s])), [roster]);

  const handleRoadmapsSaved = (newIds) => {
    setShowAssignForm(false);
    setRoadmapInfo((prev) => ({ ...prev, roadmap_ids: newIds }));
    loadOverview();
    if (newIds.length > 0) loadRoster();
  };

  if (metaLoading) return <TeachClassroomSkeleton />;

  if (notFound) {
    return (
      <div className="max-w-4xl mx-auto w-full p-4 md:p-8 pb-20 md:pb-8">
        <div className="kinetic-card bg-white p-8 text-center flex flex-col items-center gap-3">
          <ShieldAlert size={28} className="text-[#B91C1C]" />
          <p className="font-sans text-sm text-[#64748B]">
            Couldn't find that classroom — it may have been archived, or you're not its teacher.
          </p>
          <button onClick={() => navigate('/teach')} className="kinetic-btn kinetic-accent-gradient px-4 py-2 text-sm">
            Back to Teach
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto w-full p-4 md:p-8 pb-20 md:pb-8 flex flex-col gap-6 animate-in fade-in duration-300">
      <div className="flex flex-col gap-1">
        <button
          onClick={() => navigate('/teach')}
          className="flex items-center gap-1.5 font-sans text-xs font-semibold text-[#64748B] hover:text-[#0891B2] transition-colors self-start mb-1"
        >
          <ArrowLeft size={14} /> All classes
        </button>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="font-sans text-2xl font-semibold text-[#0F172A] flex items-center gap-2">
              <Presentation size={22} className="text-[#0891B2]" /> {meta.name}
            </h2>
            <p className="font-sans text-sm text-[#64748B] mt-1">
              {meta.school_name ? `${meta.school_name} · ` : ''}
              {meta.member_count} student{meta.member_count === 1 ? '' : 's'}
              {assignedRoadmaps.length > 0 && <> · {assignedRoadmaps.map((r) => r.title).join(', ')}</>}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              title="Copy join code"
              onClick={() => { navigator.clipboard?.writeText(meta.join_code); toast.success('Join code copied.'); }}
              className="flex items-center gap-2 px-3 py-2 rounded-lg bg-[rgba(15,23,42,0.04)] hover:bg-[rgba(15,23,42,0.07)] transition-colors"
            >
              <span className="font-mono text-xs font-semibold text-[#0F172A] tracking-wider">{meta.join_code}</span>
              <Copy size={12} className="text-[#64748B]" />
            </button>
            <button
              title="Generate a new join code — the old one stops working"
              disabled={regenerating}
              onClick={async () => {
                if (!window.confirm('Generate a new join code? The current code stops working immediately — anyone with the old code (e.g. shared on a WhatsApp group) can no longer join.')) return;
                setRegenerating(true);
                try {
                  const updated = await apiFetch(`/api/classrooms/${id}`, {
                    method: 'PATCH',
                    body: JSON.stringify({ regenerate_join_code: true }),
                  });
                  refreshClassrooms();
                  toast.success('New join code generated.');
                } catch {
                  // apiFetch already toasts server-side failures
                } finally {
                  setRegenerating(false);
                }
              }}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-[#64748B] hover:text-[#0891B2] hover:bg-[rgba(15,23,42,0.04)] transition-colors disabled:opacity-50"
            >
              <RefreshCw size={13} className={regenerating ? 'animate-spin' : ''} />
              <span className="font-sans text-xs font-semibold hidden sm:inline">New code</span>
            </button>
            {hasRoadmaps && (
              <button
                onClick={() => setShowAssignForm((v) => !v)}
                className="font-sans text-xs font-semibold text-[#0891B2] hover:text-[#06B6D4] transition-colors"
              >
                Change subjects
              </button>
            )}
          </div>
        </div>
      </div>

      {showAssignForm && roadmapInfo && (
        <RoadmapAssignForm
          classroomId={id}
          available={roadmapInfo.available}
          initialSelected={roadmapInfo.roadmap_ids}
          onCancel={() => setShowAssignForm(false)}
          onSaved={handleRoadmapsSaved}
        />
      )}

      <div className="flex gap-1 border-b border-[rgba(15,23,42,0.08)]">
        <TabButton icon={<TrendingUp size={15} />} label="Overview" active={tab === 'overview'} onClick={() => setTab('overview')} />
        <TabButton icon={<Grid3x3 size={15} />} label="Gap Map" active={tab === 'gapmap'} onClick={() => setTab('gapmap')} />
        <TabButton icon={<ListChecks size={15} />} label="Students" active={tab === 'students'} onClick={() => setTab('students')} />
      </div>

      {tab === 'overview' && (
        <OverviewTab meta={meta} overview={overview} loading={overviewLoading} error={overviewError} hasRoadmaps={hasRoadmaps} roadmapLoading={roadmapLoading} />
      )}

      {tab === 'gapmap' && (
        roadmapLoading ? (
          <TabSkeleton />
        ) : !hasRoadmaps ? (
          <AssignGate available={roadmapInfo?.available || []} classroomId={id} onSaved={handleRoadmapsSaved} />
        ) : (
          <GapMapTab classroomId={id} assignedRoadmaps={assignedRoadmaps} rosterByMember={rosterByMember} />
        )
      )}

      {tab === 'students' && (
        roadmapLoading ? (
          <TabSkeleton />
        ) : !hasRoadmaps ? (
          <AssignGate available={roadmapInfo?.available || []} classroomId={id} onSaved={handleRoadmapsSaved} />
        ) : (
          <StudentsTab
            classroomId={id}
            roster={roster}
            loading={rosterLoading}
            error={rosterError}
            memberCount={meta.member_count}
            onChanged={loadRoster}
          />
        )
      )}
    </div>
  );
}

/* ---------------------------------------------------------------------------
   Overview tab
--------------------------------------------------------------------------- */

function OverviewTab({ meta, overview, loading, error, hasRoadmaps, roadmapLoading }) {
  if (loading) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[0, 1, 2, 3].map((i) => <div key={i} className="kinetic-card bg-white h-24 skeleton" />)}
      </div>
    );
  }
  if (error) return <div className="kinetic-card bg-white text-[#ba1a1a] text-sm">Couldn't load overview: {error}</div>;
  if (!overview) return null;

  if (overview.member_count === 0) {
    return (
      <EmptyState
        icon={<Users size={18} />}
        title="No students yet"
        text={`Share the join code "${meta.join_code}" with your class — this page fills in with real numbers the moment your first student joins. Never fabricated numbers.`}
      />
    );
  }

  if (!roadmapLoading && !hasRoadmaps) {
    return (
      <EmptyState
        icon={<BookOpen size={18} />}
        title="Assign a subject to unlock the rest"
        text="You have students, but no subject assigned yet — pick one from the Gap Map or Students tab so mastery and recall can be computed."
      />
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Students" value={overview.member_count} icon={<Users size={16} />} color="#0891B2" />
        <StatCard title="Active, last 7d" value={overview.active_last_7d} icon={<TrendingUp size={16} />} color="#0F766E" />
        <StatCard title="Reviews (7d)" value={overview.reviews_completed_7d} icon={<ListChecks size={16} />} color="#B45309" />
        <StatCard
          title="Class recall (7d)"
          value={overview.enough_data_for_recall_rate && overview.class_recall_rate_7d != null ? `${Math.round(overview.class_recall_rate_7d * 100)}%` : '—'}
          icon={<Target size={16} />}
          color="#0891B2"
        />
      </div>

      {overview.at_risk_count > 0 && (
        <div className="kinetic-card bg-white p-4 flex items-center gap-3 border-l-4 border-l-[#B91C1C]">
          <AlertTriangle size={18} className="text-[#B91C1C] shrink-0" />
          <p className="font-sans text-sm text-[#0F172A]">
            <span className="font-semibold">{overview.at_risk_count}</span> student{overview.at_risk_count === 1 ? '' : 's'} at risk right now — see the Students tab for reasons.
          </p>
        </div>
      )}

      {overview.roadmap_coverage.length > 0 && (
        <div className="kinetic-card bg-white p-5 flex flex-col gap-4">
          <h3 className="font-sans text-xs font-bold text-[#64748B] uppercase tracking-widest">Subject coverage</h3>
          {overview.roadmap_coverage.map((r) => (
            <div key={r.roadmap_id} className="flex flex-col gap-1.5">
              <div className="flex items-center justify-between gap-3">
                <span className="font-sans text-sm text-[#0F172A]">{r.title}</span>
                <span className="font-mono text-sm font-semibold text-[#0F172A]">{r.coverage_pct}%</span>
              </div>
              <div className="w-full h-1.5 rounded-full bg-[rgba(15,23,42,0.06)] overflow-hidden">
                <div className="h-full rounded-full bg-[#0891B2] transition-all duration-700 ease-out" style={{ width: `${r.coverage_pct}%` }} />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ---------------------------------------------------------------------------
   Roadmap assignment
--------------------------------------------------------------------------- */

function AssignGate({ available, classroomId, onSaved }) {
  return (
    <div className="kinetic-card bg-white p-6 flex flex-col gap-4">
      <div className="flex items-start gap-4">
        <div className="w-10 h-10 rounded-lg bg-[#0891B2]/10 flex items-center justify-center text-[#0891B2] shrink-0">
          <BookOpen size={18} />
        </div>
        <div>
          <h4 className="font-sans text-sm font-semibold text-[#0F172A] mb-1">Assign a subject first</h4>
          <p className="font-sans text-xs text-[#64748B] leading-relaxed">
            Pick which roadmap this class tracks — the gap map and roster are computed only from a student's activity on assigned subjects, never their other roadmaps.
          </p>
        </div>
      </div>
      <RoadmapAssignForm classroomId={classroomId} available={available} initialSelected={[]} onSaved={onSaved} embedded />
    </div>
  );
}

function RoadmapAssignForm({ classroomId, available, initialSelected, onSaved, onCancel, embedded = false }) {
  const [selected, setSelected] = useState(new Set(initialSelected));
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState(null);

  const toggle = (rid) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(rid)) next.delete(rid); else next.add(rid);
      return next;
    });
  };

  const submit = async () => {
    setSaving(true);
    setErr(null);
    try {
      const ids = [...selected];
      const res = await apiFetch(`/api/classrooms/${classroomId}/roadmaps`, {
        method: 'PUT',
        body: JSON.stringify({ roadmap_ids: ids }),
      });
      onSaved(res.roadmap_ids);
    } catch (e) {
      setErr(e.message);
    } finally {
      setSaving(false);
    }
  };

  const body = (
    <>
      {available.length === 0 ? (
        <p className="font-sans text-sm text-[#64748B]">No school-catalog subjects exist yet — check back once one's published.</p>
      ) : (
        <div className="flex flex-col gap-2">
          {available.map((r) => (
            <label
              key={r.id}
              className="flex items-center gap-2.5 px-3 py-2 rounded-lg border border-[rgba(15,23,42,0.1)] hover:border-[#0891B2]/40 cursor-pointer transition-colors"
            >
              <input type="checkbox" checked={selected.has(r.id)} onChange={() => toggle(r.id)} className="w-4 h-4 accent-[#0891B2]" />
              <span className="font-sans text-sm text-[#0F172A]">{r.title}</span>
            </label>
          ))}
        </div>
      )}
      {err && <p className="font-sans text-xs text-[#ba1a1a]">{err}</p>}
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={submit}
          disabled={saving || selected.size === 0}
          className="kinetic-btn kinetic-accent-gradient px-4 py-2 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {saving ? 'Saving…' : 'Save subjects'}
        </button>
        {onCancel && (
          <button type="button" onClick={onCancel} className="font-sans text-xs font-semibold text-[#64748B] hover:text-[#0F172A]">
            Cancel
          </button>
        )}
      </div>
    </>
  );

  if (embedded) return <div className="flex flex-col gap-3">{body}</div>;
  return <div className="kinetic-card bg-white p-5 flex flex-col gap-3">{body}</div>;
}

/* ---------------------------------------------------------------------------
   Gap Map tab
--------------------------------------------------------------------------- */

function GapMapTab({ classroomId, assignedRoadmaps, rosterByMember }) {
  const [roadmapId, setRoadmapId] = useState(assignedRoadmaps[0]?.id || null);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);

  useEffect(() => {
    if (!roadmapId) return;
    setLoading(true);
    setSelectedNode(null);
    apiFetch(`/api/classrooms/${classroomId}/gap-map?roadmap_id=${roadmapId}`)
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [classroomId, roadmapId]);

  const nodesByPhase = useMemo(() => {
    const map = new Map();
    for (const n of data?.nodes || []) {
      if (!map.has(n.phase)) map.set(n.phase, new Map());
      const sections = map.get(n.phase);
      if (!sections.has(n.section)) sections.set(n.section, []);
      sections.get(n.section).push(n);
    }
    return map;
  }, [data]);

  const nodeById = useMemo(() => new Map((data?.nodes || []).map((n) => [n.node_id, n])), [data]);

  if (loading) return <TabSkeleton />;
  if (error) return <div className="kinetic-card bg-white text-[#ba1a1a] text-sm">Couldn't load the gap map: {error}</div>;
  if (!data || data.nodes.length === 0) {
    return <EmptyState icon={<Grid3x3 size={18} />} title="No topics in this subject yet" text="This roadmap has no nodes to map yet." />;
  }

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        {assignedRoadmaps.length > 1 ? (
          <select
            value={roadmapId}
            onChange={(e) => setRoadmapId(e.target.value)}
            className="px-3 py-2 rounded-lg border border-[rgba(15,23,42,0.12)] font-sans text-sm text-[#0F172A] bg-white focus:outline-none focus:border-[#0891B2]"
          >
            {assignedRoadmaps.map((r) => <option key={r.id} value={r.id}>{r.title}</option>)}
          </select>
        ) : <div />}
        <Legend />
      </div>

      <div className="flex flex-col gap-6">
        {[...nodesByPhase.entries()].map(([phase, sections]) => (
          <div key={phase}>
            <h3 className="font-sans text-sm font-semibold text-[#0F172A] mb-3">{phase}</h3>
            <div className="flex flex-col gap-4">
              {[...sections.entries()].map(([section, nodes]) => (
                <div key={section}>
                  <p className="font-sans text-[11px] font-bold text-[#64748B] uppercase tracking-wide mb-2">{section}</p>
                  <div className="grid gap-2" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))' }}>
                    {nodes.map((n) => (
                      <GapMapCell key={n.node_id} node={n} onClick={() => setSelectedNode(n)} />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {selectedNode && (
        <GapMapSidePanel
          node={selectedNode}
          rootCauseNode={selectedNode.root_cause_node_id ? nodeById.get(selectedNode.root_cause_node_id) : null}
          rosterByMember={rosterByMember}
          onClose={() => setSelectedNode(null)}
        />
      )}
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

function GapMapCell({ node, onClick }) {
  const c = STATUS_COLOR[node.status] || STATUS_COLOR.untouched;
  const total = node.counts.untouched + node.counts.weak + node.counts.developing + node.counts.strong;
  return (
    <button
      onClick={onClick}
      title={node.title}
      className="rounded-lg border px-3 py-2.5 text-left transition-transform hover:-translate-y-0.5"
      style={{ backgroundColor: c.bg, borderColor: c.border }}
    >
      <p className="font-sans text-xs font-semibold leading-snug line-clamp-2" style={{ color: c.text }}>{node.title}</p>
      <p className="font-mono text-[10px] mt-1.5" style={{ color: c.text }}>
        {node.status === 'insufficient_data' ? 'not enough data' : `${node.counts.weak}/${total} weak`}
      </p>
    </button>
  );
}

function GapMapSidePanel({ node, rootCauseNode, rosterByMember, onClose }) {
  const c = STATUS_COLOR[node.status] || STATUS_COLOR.untouched;
  const byStatus = ['weak', 'developing', 'strong', 'untouched'];
  return (
    <div className="fixed inset-0 z-[100] bg-[rgba(15,23,42,0.35)] flex justify-end" onClick={onClose}>
      <div
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-sm h-full bg-white p-6 overflow-y-auto flex flex-col gap-5 animate-in slide-in-from-right duration-200"
      >
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="font-sans text-[11px] font-bold uppercase tracking-wide" style={{ color: c.text }}>{c.label}</p>
            <h3 className="font-sans text-lg font-semibold text-[#0F172A] mt-1">{node.title}</h3>
            <p className="font-sans text-xs text-[#64748B] mt-0.5">{node.phase} · {node.section}</p>
          </div>
          <button onClick={onClose} className="text-[#64748B] hover:text-[#0F172A] shrink-0"><X size={18} /></button>
        </div>

        {rootCauseNode && (
          <div className="rounded-xl p-3.5 border" style={{ backgroundColor: 'rgba(180,83,9,0.08)', borderColor: 'rgba(180,83,9,0.3)' }}>
            <p className="font-sans text-xs text-[#0F172A] leading-relaxed">
              <span className="font-semibold">Likely root cause:</span> students weak here are also weak on the prerequisite{' '}
              <span className="font-semibold">"{rootCauseNode.title}"</span> — reteach that first.
            </p>
          </div>
        )}

        <div className="grid grid-cols-2 gap-3">
          {byStatus.map((s) => (
            <div key={s} className="rounded-lg p-3" style={{ backgroundColor: STATUS_COLOR[s].bg }}>
              <p className="font-mono text-xl font-semibold" style={{ color: STATUS_COLOR[s].text }}>{node.counts[s]}</p>
              <p className="font-sans text-[10px] font-semibold uppercase tracking-wide" style={{ color: STATUS_COLOR[s].text }}>{STATUS_COLOR[s].label}</p>
            </div>
          ))}
        </div>

        {node.weak_students.length > 0 && (
          <div>
            <h4 className="font-sans text-xs font-bold text-[#64748B] uppercase tracking-widest mb-2">Weak on this topic</h4>
            <ul className="flex flex-col gap-1.5">
              {node.weak_students.map((memberId) => (
                <li key={memberId} className="font-sans text-sm text-[#0F172A] px-3 py-2 rounded-lg bg-[rgba(15,23,42,0.03)]">
                  {rosterByMember.get(memberId)?.display_name || 'Student'}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------------------
   Students tab
--------------------------------------------------------------------------- */

const SORTERS = {
  display_name: (s) => s.display_name.toLowerCase(),
  last_active_at: (s) => (s.last_active_at ? new Date(s.last_active_at).getTime() : -1),
  reviews_completed_7d: (s) => s.reviews_completed_7d,
  recall_rate: (s) => s.recall_rate ?? -1,
  current_streak: (s) => s.current_streak,
  weak_node_count: (s) => s.weak_node_count,
  overdue_count: (s) => s.overdue_count,
  at_risk: (s) => (s.at_risk ? 1 : 0),
};

function StudentsTab({ classroomId, roster, loading, error, memberCount, onChanged }) {
  const toast = useToast();
  const [sortKey, setSortKey] = useState('at_risk');
  const [sortDir, setSortDir] = useState('desc');
  const [expanded, setExpanded] = useState(null);
  const [renamingId, setRenamingId] = useState(null);
  const [renameValue, setRenameValue] = useState('');
  const [busyId, setBusyId] = useState(null); // member_id currently saving/removing

  const startRename = (s) => {
    setRenamingId(s.member_id);
    setRenameValue(s.display_name);
  };

  const saveRename = async (memberId) => {
    const name = renameValue.trim();
    if (!name) return;
    setBusyId(memberId);
    try {
      await apiFetch(`/api/classrooms/${classroomId}/members/${memberId}`, {
        method: 'PATCH',
        body: JSON.stringify({ display_name: name }),
      });
      setRenamingId(null);
      onChanged();
    } catch {
      // apiFetch already toasts server-side failures
    } finally {
      setBusyId(null);
    }
  };

  const removeMember = async (s) => {
    if (!window.confirm(`Remove "${s.display_name}" from this class? They lose access to nothing of their own — you just stop seeing their progress here. They can rejoin later with the class code.`)) return;
    setBusyId(s.member_id);
    try {
      await apiFetch(`/api/classrooms/${classroomId}/members/${s.member_id}`, { method: 'DELETE' });
      toast.success(`Removed ${s.display_name}.`);
      onChanged();
    } catch {
      // apiFetch already toasts server-side failures
    } finally {
      setBusyId(null);
    }
  };

  const sorted = useMemo(() => {
    if (!roster) return [];
    const arr = [...roster];
    arr.sort((a, b) => {
      const av = SORTERS[sortKey](a);
      const bv = SORTERS[sortKey](b);
      if (av < bv) return sortDir === 'asc' ? -1 : 1;
      if (av > bv) return sortDir === 'asc' ? 1 : -1;
      return b.weak_node_count - a.weak_node_count;
    });
    return arr;
  }, [roster, sortKey, sortDir]);

  const onSort = (key) => {
    if (key === sortKey) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    else { setSortKey(key); setSortDir('desc'); }
  };

  if (loading) return <TabSkeleton />;
  if (error) return <div className="kinetic-card bg-white text-[#ba1a1a] text-sm">Couldn't load the roster: {error}</div>;
  if (memberCount === 0) {
    return (
      <EmptyState
        icon={<Users size={18} />}
        title="No students yet"
        text="Once students join with your class code, they'll show up here with real activity — never placeholder numbers."
      />
    );
  }

  return (
    <div className="kinetic-card bg-white overflow-x-auto p-0">
      <table className="w-full min-w-[860px] border-collapse">
        <thead>
          <tr className="border-b border-[rgba(15,23,42,0.08)]">
            <Th label="Student" k="display_name" sortKey={sortKey} sortDir={sortDir} onSort={onSort} align="left" />
            <Th label="Last active" k="last_active_at" sortKey={sortKey} sortDir={sortDir} onSort={onSort} />
            <Th label="Reviews (7d)" k="reviews_completed_7d" sortKey={sortKey} sortDir={sortDir} onSort={onSort} />
            <Th label="Recall" k="recall_rate" sortKey={sortKey} sortDir={sortDir} onSort={onSort} />
            <Th label="Streak" k="current_streak" sortKey={sortKey} sortDir={sortDir} onSort={onSort} />
            <Th label="Weak topics" k="weak_node_count" sortKey={sortKey} sortDir={sortDir} onSort={onSort} />
            <Th label="Overdue" k="overdue_count" sortKey={sortKey} sortDir={sortDir} onSort={onSort} />
            <Th label="At risk" k="at_risk" sortKey={sortKey} sortDir={sortDir} onSort={onSort} />
            <th className="px-4 py-3 font-sans text-[10px] font-bold uppercase tracking-widest text-[#64748B] text-center whitespace-nowrap">Actions</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((s) => (
            <React.Fragment key={s.member_id}>
              <tr className="border-b border-[rgba(15,23,42,0.05)] last:border-b-0 hover:bg-[rgba(15,23,42,0.02)] transition-colors">
                <td className="px-4 py-3 font-sans text-sm font-semibold text-[#0F172A] whitespace-nowrap">
                  {renamingId === s.member_id ? (
                    <div className="flex items-center gap-1.5">
                      <input
                        autoFocus
                        value={renameValue}
                        onChange={(e) => setRenameValue(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') saveRename(s.member_id);
                          if (e.key === 'Escape') setRenamingId(null);
                        }}
                        maxLength={120}
                        className="px-2 py-1 rounded border border-[#0891B2] font-sans text-sm text-[#0F172A] focus:outline-none w-32"
                      />
                      <button
                        onClick={() => saveRename(s.member_id)}
                        disabled={busyId === s.member_id || !renameValue.trim()}
                        title="Save"
                        className="text-[#0F766E] hover:text-[#0F766E]/70 disabled:opacity-40 shrink-0"
                      >
                        <Check size={15} />
                      </button>
                      <button onClick={() => setRenamingId(null)} title="Cancel" className="text-[#64748B] hover:text-[#0F172A] shrink-0">
                        <X size={15} />
                      </button>
                    </div>
                  ) : (
                    <Link
                      to={`/teach/${classroomId}/students/${s.member_id}`}
                      className="hover:text-[#0891B2] transition-colors"
                    >
                      {s.display_name}
                    </Link>
                  )}
                </td>
                <td className="px-4 py-3 font-mono text-xs text-[#64748B] text-center whitespace-nowrap">{formatLastActive(s.last_active_at)}</td>
                <td className="px-4 py-3 font-mono text-sm text-[#0F172A] text-center">{s.reviews_completed_7d}</td>
                <td className="px-4 py-3 font-mono text-sm text-[#0F172A] text-center">
                  {s.recall_rate != null ? `${Math.round(s.recall_rate * 100)}%` : '—'}
                </td>
                <td className="px-4 py-3 font-mono text-sm text-[#0F172A] text-center">{s.current_streak}</td>
                <td className="px-4 py-3 font-mono text-sm text-center" style={{ color: s.weak_node_count > 0 ? '#B91C1C' : '#0F172A' }}>
                  {s.weak_node_count}
                </td>
                <td className="px-4 py-3 font-mono text-sm text-[#0F172A] text-center">{s.overdue_count}</td>
                <td className="px-4 py-3 text-center">
                  {s.at_risk ? (
                    <button
                      onClick={() => setExpanded((cur) => (cur === s.member_id ? null : s.member_id))}
                      title={s.at_risk_reasons.join('; ')}
                      className="inline-flex items-center gap-1 font-sans text-[10px] font-bold uppercase tracking-wide px-2 py-1 rounded-full bg-[#B91C1C]/10 text-[#B91C1C] hover:bg-[#B91C1C]/20 transition-colors"
                    >
                      <AlertTriangle size={11} /> At risk
                    </button>
                  ) : (
                    <span className="text-[#94A3B8]">—</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center justify-center gap-1">
                    <button
                      onClick={() => startRename(s)}
                      disabled={busyId === s.member_id}
                      title="Rename"
                      className="p-1.5 rounded text-[#64748B] hover:text-[#0891B2] hover:bg-[rgba(15,23,42,0.04)] transition-colors disabled:opacity-40"
                    >
                      <Pencil size={13} />
                    </button>
                    <button
                      onClick={() => removeMember(s)}
                      disabled={busyId === s.member_id}
                      title="Remove from class"
                      className="p-1.5 rounded text-[#64748B] hover:text-[#B91C1C] hover:bg-[rgba(185,28,28,0.06)] transition-colors disabled:opacity-40"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                </td>
              </tr>
              {expanded === s.member_id && (
                <tr className="bg-[rgba(185,28,28,0.04)]">
                  <td colSpan={9} className="px-4 py-2.5">
                    <ul className="font-sans text-xs text-[#B91C1C] flex flex-col gap-0.5">
                      {s.at_risk_reasons.map((r) => <li key={r}>· {r}</li>)}
                    </ul>
                  </td>
                </tr>
              )}
            </React.Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Th({ label, k, sortKey, sortDir, onSort, align = 'center' }) {
  const active = sortKey === k;
  return (
    <th
      onClick={() => onSort(k)}
      className={`px-4 py-3 font-sans text-[10px] font-bold uppercase tracking-widest cursor-pointer select-none whitespace-nowrap ${active ? 'text-[#0891B2]' : 'text-[#64748B]'}`}
      style={{ textAlign: align }}
    >
      <span className={`inline-flex items-center gap-1 ${align === 'left' ? 'flex-row' : 'flex-row-reverse'}`}>
        {label} {active ? (sortDir === 'asc' ? <ChevronUp size={12} /> : <ChevronDown size={12} />) : <ArrowUpDown size={11} className="opacity-40" />}
      </span>
    </th>
  );
}

function formatLastActive(iso) {
  if (!iso) return 'Never';
  const days = Math.floor((Date.now() - new Date(iso).getTime()) / 86400000);
  if (days <= 0) return 'Today';
  if (days === 1) return 'Yesterday';
  return `${days}d ago`;
}

/* ---------------------------------------------------------------------------
   Shared bits
--------------------------------------------------------------------------- */

function StatCard({ title, value, icon, color }) {
  return (
    <div className="kinetic-card bg-white p-4 border-t-2" style={{ borderTopColor: color }}>
      <div className="flex justify-between items-start mb-2">
        <h3 className="font-sans text-[10px] font-bold text-[#64748B] uppercase tracking-widest">{title}</h3>
        <div style={{ color }}>{icon}</div>
      </div>
      <div className="font-mono text-2xl font-semibold text-[#0F172A]">{value}</div>
    </div>
  );
}

function EmptyState({ icon, title, text }) {
  return (
    <div className="kinetic-card bg-white p-6 flex items-start gap-4">
      <div className="w-10 h-10 rounded-lg bg-[#0891B2]/10 flex items-center justify-center text-[#0891B2] shrink-0">{icon}</div>
      <div>
        <h4 className="font-sans text-sm font-semibold text-[#0F172A] mb-1">{title}</h4>
        <p className="font-sans text-xs text-[#64748B] leading-relaxed">{text}</p>
      </div>
    </div>
  );
}

function TabButton({ icon, label, active, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-1.5 px-4 py-2.5 font-sans text-sm font-semibold border-b-2 -mb-px transition-colors ${
        active ? 'border-[#0891B2] text-[#0891B2]' : 'border-transparent text-[#64748B] hover:text-[#0F172A]'
      }`}
    >
      {icon} {label}
    </button>
  );
}

function TeachClassroomSkeleton() {
  return (
    <div className="max-w-5xl mx-auto w-full p-4 md:p-8 pb-20 md:pb-8 flex flex-col gap-6">
      <div className="skeleton h-4 w-24" />
      <div className="skeleton h-8 w-64" />
      <div className="skeleton h-4 w-48" />
      <div className="skeleton h-10 w-full rounded" />
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[0, 1, 2, 3].map((i) => <div key={i} className="skeleton h-24 rounded-xl" />)}
      </div>
    </div>
  );
}

function TabSkeleton() {
  return (
    <div className="flex flex-col gap-3">
      <div className="skeleton h-24 w-full rounded-xl" />
      <div className="skeleton h-24 w-full rounded-xl" />
    </div>
  );
}

export default TeachClassroom;
