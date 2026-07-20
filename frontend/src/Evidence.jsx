import React, { useEffect, useState } from 'react';
import { apiFetch } from './lib/api';

// Dev-only instrument (SPEC-career-coach-phase1 §7) — the "why is this
// mastery number what it is" surface. Not a product page: no design-system
// polish, no nav entry, admin-gated in App.jsx same as /admin.

function fmt(d) {
  return d ? new Date(d).toLocaleString() : '—';
}

function EventRow({ event }) {
  return (
    <tr className={event.deleted_at ? 'opacity-40 line-through' : ''}>
      <td className="pr-4 py-1 whitespace-nowrap">{fmt(event.occurred_at)}</td>
      <td className="pr-4 py-1">{event.event_type}</td>
      <td className="pr-4 py-1">{event.trust_tier}</td>
      <td className="pr-4 py-1">{event.source}</td>
      <td className="pr-4 py-1">{event.outcome ?? '—'}</td>
      <td className="pr-4 py-1">{event.difficulty ?? '—'}</td>
      <td className="pr-4 py-1">{event.assistance ?? '—'}</td>
      <td className="pr-4 py-1">{event.grade ?? '—'}</td>
      <td className="pr-4 py-1">{event.weight.toFixed(3)}</td>
      <td className="pr-4 py-1 font-semibold">{event.m_learned_after.toFixed(3)}</td>
      <td className="pr-4 py-1">
        {!event.deleted_at && (
          <button
            className="text-red-600 underline text-xs"
            onClick={async () => {
              if (!confirm('Soft-delete this event and recompute?')) return;
              await apiFetch(`/api/evidence/events/${event.id}`, { method: 'DELETE' });
              window.location.reload();
            }}
          >
            delete
          </button>
        )}
      </td>
    </tr>
  );
}

function NodeEvents({ nodeId }) {
  const [events, setEvents] = useState(null);
  useEffect(() => {
    apiFetch(`/api/evidence/nodes/${nodeId}/events`).then(setEvents);
  }, [nodeId]);

  if (!events) return <div className="p-4 text-sm text-gray-500">Loading events…</div>;
  if (events.length === 0) return <div className="p-4 text-sm text-gray-500">No events for this node.</div>;

  return (
    <div className="p-4 bg-gray-50 overflow-x-auto">
      <table className="text-xs">
        <thead>
          <tr className="text-left text-gray-500">
            <th className="pr-4">occurred_at</th>
            <th className="pr-4">event_type</th>
            <th className="pr-4">trust_tier</th>
            <th className="pr-4">source</th>
            <th className="pr-4">outcome</th>
            <th className="pr-4">difficulty</th>
            <th className="pr-4">assistance</th>
            <th className="pr-4">grade</th>
            <th className="pr-4">w</th>
            <th className="pr-4">m_learned</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {events.map((e) => <EventRow key={e.id} event={e} />)}
        </tbody>
      </table>
    </div>
  );
}

function Evidence() {
  const [nodes, setNodes] = useState(null);
  const [summary, setSummary] = useState(null);
  const [expanded, setExpanded] = useState(null);
  const [recomputing, setRecomputing] = useState(false);

  const load = () => {
    apiFetch('/api/evidence/nodes').then(setNodes);
    apiFetch('/api/evidence/summary').then(setSummary);
  };

  useEffect(load, []);

  const recompute = async () => {
    setRecomputing(true);
    await apiFetch('/api/evidence/recompute', { method: 'POST' });
    load();
    setRecomputing(false);
  };

  return (
    <div className="p-4 md:p-8 max-w-6xl mx-auto w-full font-mono text-sm">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold">Evidence spine (dev)</h1>
        <button
          onClick={recompute}
          disabled={recomputing}
          className="border px-3 py-1 rounded text-xs disabled:opacity-50"
        >
          {recomputing ? 'Recomputing…' : 'POST /recompute'}
        </button>
      </div>

      {summary && (
        <pre className="bg-gray-100 p-3 rounded text-xs mb-6 overflow-x-auto">
          {JSON.stringify(summary, null, 2)}
        </pre>
      )}

      {!nodes ? (
        <div>Loading…</div>
      ) : nodes.length === 0 ? (
        <div className="text-gray-500">No node mastery yet.</div>
      ) : (
        <table className="w-full text-xs border-collapse">
          <thead>
            <tr className="text-left text-gray-500 border-b">
              <th className="pr-4 py-2">Node</th>
              <th className="pr-4 py-2">m_learned</th>
              <th className="pr-4 py-2">r</th>
              <th className="pr-4 py-2">m</th>
              <th className="pr-4 py-2">state</th>
              <th className="pr-4 py-2">confidence</th>
              <th className="pr-4 py-2">evidence_count</th>
              <th className="pr-4 py-2">last_event_at</th>
            </tr>
          </thead>
          <tbody>
            {nodes.map((n) => (
              <React.Fragment key={n.node_id}>
                <tr
                  className="border-b cursor-pointer hover:bg-gray-50"
                  onClick={() => setExpanded(expanded === n.node_id ? null : n.node_id)}
                >
                  <td className="pr-4 py-2">{n.title}</td>
                  <td className="pr-4 py-2">{n.m_learned.toFixed(3)}</td>
                  <td className="pr-4 py-2">{n.r.toFixed(3)}</td>
                  <td className="pr-4 py-2 font-semibold">{n.m.toFixed(3)}</td>
                  <td className="pr-4 py-2">{n.state}</td>
                  <td className="pr-4 py-2">{n.confidence}</td>
                  <td className="pr-4 py-2">{n.evidence_count}</td>
                  <td className="pr-4 py-2">{fmt(n.last_event_at)}</td>
                </tr>
                {expanded === n.node_id && (
                  <tr>
                    <td colSpan={8}>
                      <NodeEvents nodeId={n.node_id} />
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default Evidence;
