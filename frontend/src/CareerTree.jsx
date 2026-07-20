import React, { useEffect, useMemo, useState } from 'react';
import {
  TreePine, ChevronDown, ChevronRight, X, Inbox, CheckCircle2, ArrowRight, Loader2, RefreshCw,
} from 'lucide-react';
import { apiFetch } from './lib/api';

// Career tree view + unmapped triage (SPEC-career-coach-phase2.md §8). Renders
// the committed tree grouped by subject with phase-1 mastery state badges;
// tapping a node opens the SAME evidence-log drill-down phase 1 built as a
// debug instrument (GET /api/evidence/nodes/{id}/events) — here it's the
// trust feature parent story 7 asks for, not a dev tool.

const STATE_STYLE = {
  unexposed: { label: 'Unexposed', color: '#94A3B8' },
  exposed: { label: 'Exposed', color: '#B45309' },
  practicing: { label: 'Practicing', color: '#0891B2' },
  solid: { label: 'Solid', color: '#0F766E' },
  interview_ready: { label: 'Interview ready', color: '#15803D' },
};

function StateBadge({ state }) {
  const st = STATE_STYLE[state] || STATE_STYLE.unexposed;
  return (
    <span
      className="font-sans text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full shrink-0"
      style={{ color: st.color, backgroundColor: `${st.color}14`, border: `1px solid ${st.color}33` }}
    >
      {st.label}
    </span>
  );
}

function fmtDate(d) {
  return d ? new Date(d).toLocaleDateString() : 'never';
}

function EventLog({ nodeId }) {
  const [events, setEvents] = useState(null);
  useEffect(() => {
    apiFetch(`/api/evidence/nodes/${nodeId}/events`).then(setEvents).catch(() => setEvents([]));
  }, [nodeId]);

  if (!events) return <div className="p-3 font-sans text-xs text-[#94A3B8] flex items-center gap-2"><Loader2 size={12} className="animate-spin" /> Loading evidence…</div>;
  if (events.length === 0) return <div className="p-3 font-sans text-xs text-[#94A3B8]">No evidence yet — nothing logged against this node.</div>;

  return (
    <div className="p-3 bg-[rgba(15,23,42,0.02)] overflow-x-auto">
      <table className="w-full text-xs font-mono">
        <thead>
          <tr className="text-left text-[#94A3B8]">
            <th className="pr-3 py-1 font-normal">when</th>
            <th className="pr-3 py-1 font-normal">type</th>
            <th className="pr-3 py-1 font-normal">tier</th>
            <th className="pr-3 py-1 font-normal">outcome</th>
            <th className="pr-3 py-1 font-normal">w</th>
            <th className="pr-3 py-1 font-normal">m_learned</th>
          </tr>
        </thead>
        <tbody>
          {events.map((e) => (
            <tr key={e.id} className={e.deleted_at ? 'opacity-40 line-through' : 'text-[#334155]'}>
              <td className="pr-3 py-1 whitespace-nowrap">{fmtDate(e.occurred_at)}</td>
              <td className="pr-3 py-1">{e.event_type}</td>
              <td className="pr-3 py-1">{e.trust_tier.replace('_', ' ')}</td>
              <td className="pr-3 py-1">{e.outcome ?? '—'}</td>
              <td className="pr-3 py-1">{e.weight.toFixed(2)}</td>
              <td className="pr-3 py-1 font-semibold">{e.m_learned_after.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function NodeRow({ node, expanded, onToggle }) {
  return (
    <div className="border-t border-[rgba(15,23,42,0.04)] first:border-t-0">
      <button onClick={onToggle} className="w-full flex items-center justify-between gap-2 py-2.5 text-left hover:bg-[rgba(15,23,42,0.01)] transition-colors">
        <span className="font-sans text-sm text-[#0F172A] truncate">{node.title}</span>
        <div className="flex items-center gap-2 shrink-0">
          <span className="font-mono text-[11px] text-[#94A3B8]">{node.confidence}</span>
          <StateBadge state={node.state} />
        </div>
      </button>
      {expanded && <EventLog nodeId={node.node_id} />}
    </div>
  );
}

function SubjectSection({ subject, nodes, expandedNode, setExpandedNode }) {
  const [open, setOpen] = useState(false);
  const counts = useMemo(() => {
    const c = {};
    for (const n of nodes) c[n.state] = (c[n.state] || 0) + 1;
    return c;
  }, [nodes]);

  return (
    <div className="bg-white border border-[rgba(15,23,42,0.08)] rounded-2xl shadow-sm overflow-hidden">
      <button onClick={() => setOpen((o) => !o)} className="w-full flex items-center justify-between gap-2 px-4 py-3 hover:bg-[rgba(15,23,42,0.01)] transition-colors">
        <div className="flex items-center gap-2 min-w-0">
          {open ? <ChevronDown size={15} className="text-[#94A3B8] shrink-0" /> : <ChevronRight size={15} className="text-[#94A3B8] shrink-0" />}
          <span className="font-sans text-sm font-semibold text-[#0F172A] truncate">{subject}</span>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          {Object.entries(counts).map(([state, n]) => (
            <span key={state} className="font-mono text-[10px] text-[#94A3B8]">{n} {STATE_STYLE[state]?.label.toLowerCase() || state}</span>
          ))}
        </div>
      </button>
      {open && (
        <div className="px-4 pb-2">
          {nodes.map((n) => (
            <NodeRow
              key={n.node_id}
              node={n}
              expanded={expandedNode === n.node_id}
              onToggle={() => setExpandedNode(expandedNode === n.node_id ? null : n.node_id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function UnmappedTriage({ roadmapId, allNodes }) {
  const [items, setItems] = useState(null);
  const [dismissed, setDismissed] = useState(() => new Set());
  const [assigning, setAssigning] = useState(null);

  const load = () => apiFetch('/api/career/unmapped').then(setItems).catch(() => setItems([]));
  useEffect(() => { load(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const assign = async (activityId, nodeId) => {
    setAssigning(activityId);
    try {
      await apiFetch(`/api/career/unmapped/${activityId}/assign`, {
        method: 'POST',
        body: JSON.stringify({ node_id: nodeId }),
      });
      await load();
    } catch (err) {
      // surfaced via apiFetch's own toast for 5xx; 4xx just no-ops here
    }
    setAssigning(null);
  };

  if (items === null) return null;
  const visible = items.filter((i) => !dismissed.has(i.activity_id));
  if (visible.length === 0) return null;

  return (
    <div className="bg-white border border-[rgba(15,23,42,0.08)] rounded-2xl shadow-sm p-4 md:p-5 flex flex-col gap-3">
      <div className="flex items-center gap-2">
        <Inbox size={16} className="text-[#B45309]" />
        <h3 className="font-sans text-sm font-semibold text-[#0F172A]">Unmapped activity ({visible.length})</h3>
      </div>
      <p className="font-sans text-xs text-[#64748B] -mt-1">
        Logged before a node existed for it, or dropped when a node was removed. Assign it somewhere or dismiss it.
      </p>
      <div className="flex flex-col divide-y divide-[rgba(15,23,42,0.05)]">
        {visible.map((item) => (
          <div key={item.activity_id} className="py-2.5 flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3">
            <div className="flex-1 min-w-0">
              <div className="font-sans text-sm text-[#0F172A] truncate">{item.topic}</div>
              <div className="font-mono text-[10px] text-[#94A3B8]">{item.skipped_count} review{item.skipped_count !== 1 ? 's' : ''} affected</div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              {item.suggested_node && (
                <button
                  onClick={() => assign(item.activity_id, item.suggested_node.node_id)}
                  disabled={assigning === item.activity_id}
                  className="flex items-center gap-1 font-sans text-xs font-semibold text-[#0891B2] hover:text-[#0E7490] border border-[#0891B2]/30 rounded-lg px-2.5 py-1.5 disabled:opacity-40"
                  title={`Confidence ${(item.suggested_node.confidence * 100).toFixed(0)}%`}
                >
                  <ArrowRight size={12} /> {item.suggested_node.title}
                </button>
              )}
              <select
                defaultValue=""
                onChange={(e) => { if (e.target.value) assign(item.activity_id, e.target.value); }}
                disabled={assigning === item.activity_id}
                className="font-sans text-xs text-[#64748B] border border-[rgba(15,23,42,0.1)] rounded-lg px-2 py-1.5 bg-white"
              >
                <option value="">Assign to node…</option>
                {allNodes.map((n) => <option key={n.node_id} value={n.node_id}>{n.title}</option>)}
              </select>
              <button
                onClick={() => setDismissed((d) => new Set(d).add(item.activity_id))}
                title="Dismiss (hides for this session only)"
                className="text-[#94A3B8] hover:text-[#0F172A] p-1"
              >
                <X size={14} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function CareerTree({ goal, onGoalChanged }) {
  const [nodes, setNodes] = useState(null);
  const [error, setError] = useState('');
  const [expandedNode, setExpandedNode] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = async () => {
    try {
      const [roadmap, mastery] = await Promise.all([
        apiFetch(`/api/roadmaps/${goal.roadmap_id}`),
        apiFetch(`/api/evidence/nodes?roadmap_id=${goal.roadmap_id}`),
      ]);
      const masteryById = Object.fromEntries(mastery.map((m) => [m.node_id, m]));
      const merged = roadmap.nodes.map((n) => ({
        node_id: n.id,
        title: n.title,
        subject: n.phase,
        ...(masteryById[n.id] || { state: 'unexposed', confidence: 'low', m_learned: 0, m: 0, evidence_count: 0 }),
      }));
      setNodes(merged);
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => { load(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, [goal.roadmap_id]);

  const refresh = async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  };

  const bySubject = useMemo(() => {
    if (!nodes) return [];
    const map = new Map();
    for (const n of nodes) {
      if (!map.has(n.subject)) map.set(n.subject, []);
      map.get(n.subject).push(n);
    }
    return [...map.entries()];
  }, [nodes]);

  const summary = useMemo(() => {
    if (!nodes) return null;
    const counts = {};
    for (const n of nodes) counts[n.state] = (counts[n.state] || 0) + 1;
    return counts;
  }, [nodes]);

  return (
    <div className="max-w-4xl mx-auto w-full p-4 md:p-8 pb-20 md:pb-8 animate-in fade-in duration-300">
      <header className="mb-6 flex items-start justify-between gap-3">
        <div>
          <h2 className="font-sans text-2xl font-semibold text-[#0F172A] flex items-center gap-2">
            <TreePine size={22} className="text-[#0891B2]" /> {goal.title}
          </h2>
          <p className="font-sans text-sm text-[#64748B] mt-1">
            Tracked with the same evidence engine as everything else — tap any node to see exactly why its number is what it is.
          </p>
          {summary && (
            <div className="flex flex-wrap gap-1.5 mt-3">
              {Object.entries(summary).map(([state, n]) => (
                <span
                  key={state}
                  className="font-sans text-[11px] font-medium px-2 py-0.5 rounded-full"
                  style={{ color: STATE_STYLE[state]?.color, backgroundColor: `${STATE_STYLE[state]?.color}14` }}
                >
                  {n} {STATE_STYLE[state]?.label.toLowerCase()}
                </span>
              ))}
            </div>
          )}
        </div>
        <button
          onClick={refresh}
          disabled={refreshing}
          title="Refresh mastery"
          className="shrink-0 text-[#64748B] hover:text-[#0F172A] p-2 rounded-full hover:bg-[rgba(15,23,42,0.04)] transition-colors disabled:opacity-40"
        >
          <RefreshCw size={16} className={refreshing ? 'animate-spin' : ''} />
        </button>
      </header>

      {error && (
        <div className="mb-4 px-4 py-3 rounded-xl bg-red-50 border border-red-200 font-sans text-sm text-red-700">{error}</div>
      )}

      {!nodes ? (
        <div className="flex flex-col gap-3">
          <div className="skeleton h-16 w-full rounded-2xl" />
          <div className="skeleton h-16 w-full rounded-2xl" />
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          <UnmappedTriage roadmapId={goal.roadmap_id} allNodes={nodes} />
          <div className="flex flex-col gap-2">
            {bySubject.map(([subject, subjectNodes]) => (
              <SubjectSection
                key={subject}
                subject={subject}
                nodes={subjectNodes}
                expandedNode={expandedNode}
                setExpandedNode={setExpandedNode}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default CareerTree;
