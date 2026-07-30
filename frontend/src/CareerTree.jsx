import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  TreePine, ChevronDown, ChevronRight, X, Inbox, CheckCircle2, ArrowRight, Loader2, RefreshCw,
  ListChecks, Minus, Plus,
} from 'lucide-react';
import { apiFetch } from './lib/api';
import AttachedRoadmaps from './AttachRoadmaps';

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
    <div id={`node-row-${node.node_id}`} className="border-t border-[rgba(15,23,42,0.04)] first:border-t-0">
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

function SubjectSection({ subject, nodes, expandedNode, setExpandedNode, forceOpenSignal }) {
  const [open, setOpen] = useState(false);
  // A Today-card deep-link bumps forceOpenSignal for this section — force it
  // open without taking over ordinary clicks (which stay purely local state).
  useEffect(() => { if (forceOpenSignal) setOpen(true); }, [forceOpenSignal]);
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

// Today card (SPEC-career-coach-phase3.md §4/§7): an ordered checklist on
// top of the tree — reviews link to /reviews, study/balance items deep-link
// to the node (handled by the parent via onSelectNode, since there's no
// separate node page). Never a new page/route — Today is a section here.

function PlanItemRow({ item, onSelectNode }) {
  const navigate = useNavigate();
  const isReview = item.kind === 'review';
  const isBalance = item.kind === 'balance';
  const dotColor = isReview ? 'bg-[#0891B2]' : isBalance ? 'bg-[#94A3B8]' : 'bg-[#0F766E]';

  return (
    <button
      onClick={() => (isReview ? navigate('/reviews') : item.node_id && onSelectNode(item.node_id))}
      className="w-full text-left flex items-start gap-3 py-2.5 px-1 -mx-1 hover:bg-[rgba(15,23,42,0.01)] rounded-lg transition-colors"
    >
      <div className={`mt-1.5 shrink-0 w-1.5 h-1.5 rounded-full ${dotColor}`} />
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-sans text-sm text-[#0F172A] truncate">{item.label}</span>
          {isBalance && (
            // Quiet, not alarming — a small neutral label, never a colored badge (§7).
            <span className="font-sans text-[9px] font-semibold uppercase tracking-wider text-[#64748B] bg-[rgba(15,23,42,0.05)] px-1.5 py-0.5 rounded-full shrink-0">
              Catch-up
            </span>
          )}
        </div>
        {/* The reason is the trust surface, not decoration — never truncated, even on mobile. */}
        <p className="font-sans text-xs text-[#64748B] mt-0.5">{item.reason}</p>
      </div>
      <ArrowRight size={14} className="text-[#94A3B8] shrink-0 mt-1.5" />
    </button>
  );
}

function BalanceStrip({ balance }) {
  const entries = Object.entries(balance || {});
  if (entries.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-x-4 gap-y-1.5 pt-3 mt-1 border-t border-[rgba(15,23,42,0.06)]">
      {entries.map(([subject, value]) => {
        const pct = Math.round(value * 100);
        const isNeg = value < 0;
        return (
          <div key={subject} className="flex items-center gap-1.5">
            <span className="font-sans text-[11px] text-[#64748B]">{subject.replace(/_/g, ' ')}</span>
            <span className={`font-mono text-[11px] font-medium ${isNeg ? 'text-[#B45309]' : 'text-[#0F766E]'}`}>
              {isNeg ? '' : '+'}{pct}%
            </span>
          </div>
        );
      })}
    </div>
  );
}

function TodayCard({ onSelectNode }) {
  const [plan, setPlan] = useState(null);
  // Fetch failure tracked separately from genuine emptiness (Home.jsx
  // 2026-07-24 pattern) — a failed /today must never render as "nothing to do".
  const [fetchError, setFetchError] = useState(null);
  const [minutesDraft, setMinutesDraft] = useState(null);
  const [saving, setSaving] = useState(false);

  const load = () => {
    setFetchError(null);
    return apiFetch('/api/career/today')
      .then((data) => { setPlan(data); setMinutesDraft(data.daily_minutes); })
      .catch((err) => setFetchError(err.message));
  };

  useEffect(() => { load(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, []);

  const commitMinutes = async (value) => {
    const clamped = Math.max(30, Math.min(240, value));
    setMinutesDraft(clamped);
    setSaving(true);
    try {
      await apiFetch('/api/career/goals/active', {
        method: 'PATCH',
        body: JSON.stringify({ daily_minutes: clamped }),
      });
      await load();
    } catch (err) {
      // apiFetch already toasts server errors (5xx); nothing further to do.
    }
    setSaving(false);
  };

  if (plan === null && !fetchError) {
    return (
      <div className="bg-white border border-[rgba(15,23,42,0.08)] rounded-2xl shadow-sm p-4 md:p-5 flex flex-col gap-2">
        <div className="skeleton h-4 w-20" />
        <div className="skeleton h-10 w-full" />
        <div className="skeleton h-10 w-full" />
      </div>
    );
  }

  if (fetchError) {
    return (
      <div className="bg-white border border-[rgba(15,23,42,0.08)] rounded-2xl shadow-sm p-4 md:p-5 flex items-center gap-3">
        <span className="font-sans text-sm text-red-700 flex-1">Couldn't load today's plan: {fetchError}</span>
        <button onClick={load} className="font-sans text-xs font-semibold text-[#0891B2] underline underline-offset-4 shrink-0">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white border border-[rgba(15,23,42,0.08)] rounded-2xl shadow-sm p-4 md:p-5 flex flex-col gap-3">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <ListChecks size={16} className="text-[#0891B2]" />
          <h3 className="font-sans text-sm font-semibold text-[#0F172A]">Today</h3>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          <button
            onClick={() => commitMinutes(minutesDraft - 15)}
            disabled={saving || minutesDraft <= 30}
            title="15 fewer minutes"
            className="text-[#64748B] hover:text-[#0F172A] disabled:opacity-30 p-1 rounded-full hover:bg-[rgba(15,23,42,0.04)]"
          >
            <Minus size={13} />
          </button>
          <span className="font-mono text-xs text-[#64748B] w-14 text-center">{minutesDraft} min</span>
          <button
            onClick={() => commitMinutes(minutesDraft + 15)}
            disabled={saving || minutesDraft >= 240}
            title="15 more minutes"
            className="text-[#64748B] hover:text-[#0F172A] disabled:opacity-30 p-1 rounded-full hover:bg-[rgba(15,23,42,0.04)]"
          >
            <Plus size={13} />
          </button>
        </div>
      </div>

      {plan.overflow && (
        <p className="font-sans text-sm text-[#64748B]">Today's reviews fill your time — no new material.</p>
      )}
      {!plan.overflow && plan.tree_complete && (
        <p className="font-sans text-sm text-[#64748B]">Nothing new to study. Reviews only.</p>
      )}

      {plan.items.length === 0 ? (
        <p className="font-sans text-sm text-[#94A3B8]">Nothing due right now.</p>
      ) : (
        <div className="flex flex-col divide-y divide-[rgba(15,23,42,0.04)]">
          {plan.items.map((item, idx) => (
            <PlanItemRow
              key={`${item.kind}-${item.review_id || item.node_id}-${idx}`}
              item={item}
              onSelectNode={onSelectNode}
            />
          ))}
        </div>
      )}

      <BalanceStrip balance={plan.balance} />
    </div>
  );
}

function CareerTree({ goal, onGoalChanged }) {
  const [nodes, setNodes] = useState(null);
  const [error, setError] = useState('');
  const [expandedNode, setExpandedNode] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  // { subject, nonce } — a Today-card click forces that node's SubjectSection
  // open and scrolls its row into view. nonce just guarantees the effect
  // re-fires on a repeat click into an already-open section.
  const [deepLink, setDeepLink] = useState(null);
  // Attaching/detaching changes what the planner can schedule, so the Today
  // card must refetch — remounting it via key is the smallest way to do that
  // without lifting its whole fetch into this component.
  const [attachNonce, setAttachNonce] = useState(0);

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

  // Today items carry node_meta.subject (a key, e.g. "dsa"); SubjectSection
  // groups by RoadmapNode.phase (a title, e.g. "Data Structures & Algorithms")
  // — two different strings for the same concept. Resolve via the already-
  // loaded `nodes` list rather than trusting the plan's subject string.
  const selectNode = (nodeId) => {
    const node = (nodes || []).find((n) => n.node_id === nodeId);
    if (!node) return;
    setExpandedNode(nodeId);
    setDeepLink({ subject: node.subject, nonce: Date.now() });
  };

  useEffect(() => {
    if (!deepLink) return;
    const t = setTimeout(() => {
      const el = document.getElementById(`node-row-${expandedNode}`);
      el?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 80); // let the SubjectSection's forced-open render land first
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [deepLink]);

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
          <TodayCard key={attachNonce} onSelectNode={selectNode} />
          <AttachedRoadmaps onChanged={() => setAttachNonce((n) => n + 1)} />
          <UnmappedTriage roadmapId={goal.roadmap_id} allNodes={nodes} />
          <div className="flex flex-col gap-2">
            {bySubject.map(([subject, subjectNodes]) => (
              <SubjectSection
                key={subject}
                subject={subject}
                nodes={subjectNodes}
                expandedNode={expandedNode}
                setExpandedNode={setExpandedNode}
                forceOpenSignal={deepLink?.subject === subject ? deepLink.nonce : null}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default CareerTree;
