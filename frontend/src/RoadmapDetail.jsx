import React, { useEffect, useState, useCallback, useMemo, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { apiFetch } from './lib/api';
import { ArrowLeft, Check, ChevronDown, ChevronRight, StickyNote, X, MousePointerClick, ExternalLink, Download, List, Map as MapIcon, PlusSquare, Compass, BookOpen } from 'lucide-react';
import { CONTENT_KEY_BY_TITLE } from './lib/contentRoadmaps';
import { useSeo } from './lib/useSeo';
import { jsPDF } from 'jspdf';
import { useAuth } from './lib/AuthContext';
import { track, EVENTS } from './lib/analytics';
import { getRoadmapStyle, RoadmapLogo } from './lib/roadmapVisuals';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Handle,
  Position,
  useNodesState,
  useEdgesState,
} from 'reactflow';
import 'reactflow/dist/style.css';
import dagre from 'dagre';

const TIER_COLORS = { easy: '#0F766E', medium: '#B45309', hard: '#B91C1C' };
const NODE_W = 230;
const NODE_H = 64;
const STEP_W = 260;
const STEP_H = 58;

/* ---------------- Custom node renderers ---------------- */

function StepNode({ data }) {
  return (
    <div
      className="rounded-lg bg-[#131b2e] text-white flex items-center justify-center px-4 shadow-md border border-[#0891B2]/30"
      style={{ width: STEP_W, height: STEP_H }}
    >
      <Handle type="target" position={Position.Top} style={{ opacity: 0 }} />
      <span className="font-sans text-sm font-semibold tracking-tight text-center leading-tight">{data.label}</span>
      <Handle type="source" position={Position.Bottom} style={{ opacity: 0 }} />
    </div>
  );
}

function TopicNode({ data }) {
  const done = data.status === 'done';
  const tierColor = TIER_COLORS[data.tier] || '#0891B2';
  return (
    <div
      className={`rounded-lg flex items-center gap-2.5 px-3 shadow-sm border transition-colors select-none ${
        done ? 'bg-[#0F766E]/10 border-[#0F766E]' : 'bg-white border-[rgba(15,23,42,0.15)] hover:border-[#0891B2]'
      } ${data.isChild ? 'border-dashed' : ''}`}
      style={{ width: NODE_W, height: NODE_H }}
    >
      <Handle type="target" position={Position.Top} style={{ opacity: 0 }} />

      {/* completion check */}
      <div
        className={`w-5 h-5 rounded-full shrink-0 flex items-center justify-center border ${
          done ? 'bg-[#0F766E] border-[#0F766E]' : 'border-[rgba(15,23,42,0.3)]'
        }`}
      >
        {done && <Check size={12} className="text-white" />}
      </div>

      <div className="flex-1 min-w-0">
        <div className={`font-sans text-[13px] font-semibold leading-tight line-clamp-2 ${done ? 'text-[#0F766E]' : 'text-[#0F172A]'}`}>
          {data.label}
        </div>
      </div>

      {/* indicators */}
      <div className="flex flex-col items-end gap-1 shrink-0">
        {data.tier && (
          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: tierColor }} title={data.tier} />
        )}
        {data.hasChildren && (
          <span className="text-[#64748B]">
            {data.expanded ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
          </span>
        )}
        {data.description && <StickyNote size={11} className="text-[#94a3b8]" />}
      </div>

      <Handle type="source" position={Position.Bottom} style={{ opacity: 0 }} />
    </div>
  );
}

const nodeTypes = { step: StepNode, topic: TopicNode };

/* ---------------- dagre layout ---------------- */

function layoutGraph(rfNodes, rfEdges) {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: 'TB', nodesep: 24, ranksep: 70, marginx: 20, marginy: 20 });

  rfNodes.forEach((n) => {
    const w = n.type === 'step' ? STEP_W : NODE_W;
    const h = n.type === 'step' ? STEP_H : NODE_H;
    g.setNode(n.id, { width: w, height: h });
  });
  rfEdges.forEach((e) => g.setEdge(e.source, e.target));
  dagre.layout(g);

  return rfNodes.map((n) => {
    const p = g.node(n.id);
    const w = n.type === 'step' ? STEP_W : NODE_W;
    const h = n.type === 'step' ? STEP_H : NODE_H;
    return { ...n, position: { x: p.x - w / 2, y: p.y - h / 2 } };
  });
}

/* ---------------- main component ---------------- */

function RoadmapDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  // Analytics: opening a roadmap is a key "explore" funnel event.
  useEffect(() => {
    track(EVENTS.ROADMAP_OPENED, { roadmap: id });
  }, [id]);

  const [meta, setMeta] = useState(null);          // {title, description}
  const [rawNodes, setRawNodes] = useState([]);    // flat nodes from API
  const [statusMap, setStatusMap] = useState({});  // node_id -> status
  const [expanded, setExpanded] = useState(() => new Set());
  const [loading, setLoading] = useState(true);
  const [contextNode, setContextNode] = useState(null); // {raw, x, y}

  // "Why am I stuck?" — dependency-graph diagnosis panel.
  const [blockersOpen, setBlockersOpen] = useState(false);
  const [blockers, setBlockers] = useState(null);       // { blockers: [], total_incomplete }
  const [blockersLoading, setBlockersLoading] = useState(false);

  // List view is the default — it scans, works on touch, and matches the data's
  // linear shape. The flowchart stays available as "Map".
  const [view, setView] = useState(() => localStorage.getItem('retainhq_roadmap_view') || 'list');
  const switchView = (v) => { setView(v); localStorage.setItem('retainhq_roadmap_view', v); };
  const [collapsedPhases, setCollapsedPhases] = useState(null); // null until initialised from data
  const [openTopic, setOpenTopic] = useState(null);             // node id with notes expanded inline
  // "Log what you learned" prompt after checking a node off — a toast, not a
  // redirect, so batch-checking several nodes isn't hijacked (design doc §9b).
  const [logPrompt, setLogPrompt] = useState(null);             // node title | null
  const logPromptTimer = useRef(null);

  // Content manifest: { [nodeTitle]: slug } for the current roadmap
  const [slugByTitle, setSlugByTitle] = useState({});
  const [contentKey, setContentKey] = useState(null);

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // Camera control
  const rfRef = useRef(null);
  const nodesRef = useRef([]);
  const [instanceReady, setInstanceReady] = useState(false);
  const didInitialFocus = useRef(false);
  useEffect(() => { nodesRef.current = nodes; }, [nodes]);

  // Per-page SEO — title/description from the loaded roadmap (null until fetched).
  useSeo(
    meta?.title ? `${meta.title} Roadmap · Spaced Repetition | RetainHQ` : null,
    meta?.description ? meta.description.replace(/\s+/g, ' ').trim().slice(0, 158) : null
  );

  const focusNode = useCallback((nodeId, zoom = 1.1) => {
    const inst = rfRef.current;
    if (!inst) return;
    const node = nodesRef.current.find((n) => n.id === nodeId);
    if (!node) return;
    const w = node.type === 'step' ? STEP_W : NODE_W;
    const h = node.type === 'step' ? STEP_H : NODE_H;
    inst.setCenter(node.position.x + w / 2, node.position.y + h / 2, { zoom, duration: 700 });
  }, []);

  // Fetch roadmap detail
  const { session, requireAuth } = useAuth();
  
  useEffect(() => {
    async function load() {
      try {
        const data = await apiFetch(`/api/roadmaps/${id}`, { optionalAuth: true });
        setMeta({ title: data.title, description: data.description });
        // The roadmap slug IS the content folder key; fall back to the title map for
        // any roadmap that predates the slug backfill.
        const ck = data.slug || CONTENT_KEY_BY_TITLE[data.title] || null;
        setContentKey(ck);
        setRawNodes(data.nodes);
        const sm = {};
        data.nodes.forEach((n) => { sm[n.id] = n.status; });
        setStatusMap(sm);
      } catch (err) {
        console.error('Failed to load roadmap:', err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  // Fetch the content manifest once to know which nodes have lessons
  useEffect(() => {
    if (!contentKey) return;
    fetch('/content/manifest.json')
      .then((r) => r.ok ? r.json() : {})
      .then((manifest) => setSlugByTitle(manifest[contentKey] || {}))
      .catch(() => {});
  }, [contentKey]);

  // Collapse phases that are already 100% done, once, when data first arrives —
  // so a long sheet opens scrolled-to-where-you-are instead of a wall of finished work.
  useEffect(() => {
    if (rawNodes.length === 0 || collapsedPhases !== null) return;
    const byPhase = {};
    rawNodes.forEach((n) => { (byPhase[n.phase] = byPhase[n.phase] || []).push(n); });
    const done = new Set(
      Object.keys(byPhase).filter((p) => byPhase[p].every((n) => statusMap[n.id] === 'done'))
    );
    setCollapsedPhases(done);
  }, [rawNodes, statusMap, collapsedPhases]);

  // Group children by parent
  const childrenByParent = useMemo(() => {
    const map = {};
    rawNodes.forEach((n) => {
      if (n.parent_id) {
        (map[n.parent_id] = map[n.parent_id] || []).push(n);
      }
    });
    return map;
  }, [rawNodes]);

  // Build + lay out the graph whenever structure/status/expansion changes
  useEffect(() => {
    if (rawNodes.length === 0) return;

    const topLevel = rawNodes.filter((n) => !n.parent_id);
    const phases = [];
    topLevel.forEach((n) => { if (!phases.includes(n.phase)) phases.push(n.phase); });

    const rfNodes = [];
    const rfEdges = [];

    // Step spine
    phases.forEach((phase, i) => {
      const stepId = `step:${phase}`;
      rfNodes.push({ id: stepId, type: 'step', data: { label: phase }, position: { x: 0, y: 0 } });
      if (i > 0) {
        rfEdges.push({
          id: `e:${phases[i - 1]}->${phase}`,
          source: `step:${phases[i - 1]}`,
          target: stepId,
          type: 'smoothstep',
          style: { stroke: '#0891B2', strokeWidth: 2 },
        });
      }
    });

    // Topic nodes branch from their step
    topLevel.forEach((n) => {
      const kids = childrenByParent[n.id] || [];
      const isExpanded = expanded.has(n.id);
      rfNodes.push({
        id: n.id,
        type: 'topic',
        data: {
          label: n.title,
          tier: n.tier,
          status: statusMap[n.id] || 'not_started',
          description: n.description,
          hasChildren: kids.length > 0,
          expanded: isExpanded,
        },
        position: { x: 0, y: 0 },
      });
      rfEdges.push({
        id: `e:${n.phase}->${n.id}`,
        source: `step:${n.phase}`,
        target: n.id,
        type: 'smoothstep',
        style: { stroke: 'rgba(15,23,42,0.18)', strokeWidth: 1.5 },
      });

      // Subtopics (only when expanded)
      if (isExpanded) {
        kids.forEach((c) => {
          rfNodes.push({
            id: c.id,
            type: 'topic',
            data: {
              label: c.title,
              tier: c.tier,
              status: statusMap[c.id] || 'not_started',
              description: c.description,
              hasChildren: false,
              isChild: true,
            },
            position: { x: 0, y: 0 },
          });
          rfEdges.push({
            id: `e:${n.id}->${c.id}`,
            source: n.id,
            target: c.id,
            type: 'smoothstep',
            style: { stroke: 'rgba(8,145,178,0.4)', strokeWidth: 1.5, strokeDasharray: '4 3' },
          });
        });
      }
    });

    const laid = layoutGraph(rfNodes, rfEdges);
    setNodes(laid);
    setEdges(rfEdges);
  }, [rawNodes, statusMap, expanded, childrenByParent, setNodes, setEdges]);

  /* ---- interactions ---- */

  const toggleComplete = useCallback(async (nodeId) => {
    if (!requireAuth()) return;

    const cur = statusMap[nodeId] || 'not_started';
    const next = cur === 'done' ? 'not_started' : 'done';
    setStatusMap((m) => ({ ...m, [nodeId]: next })); // optimistic
    if (next === 'done') focusNode(nodeId); // pan to the topic just completed (map view; no-op in list)
    if (next === 'done') {
      const raw = rawNodes.find((n) => n.id === nodeId);
      if (raw) {
        setLogPrompt(raw.title);
        clearTimeout(logPromptTimer.current);
        logPromptTimer.current = setTimeout(() => setLogPrompt(null), 8000);
      }
    }
    try {
      await apiFetch(`/api/roadmaps/nodes/${nodeId}/progress`, {
        method: 'PUT',
        body: JSON.stringify({ status: next }),
      });
    } catch (err) {
      console.error('Failed to save progress:', err);
      setStatusMap((m) => ({ ...m, [nodeId]: cur })); // revert
    }
  }, [statusMap, focusNode, rawNodes, requireAuth]);

  useEffect(() => () => clearTimeout(logPromptTimer.current), []);

  // Re-fetch each open so it reflects current progress (cheap, no caching).
  const openBlockers = useCallback(async () => {
    setBlockersOpen(true);
    setBlockersLoading(true);
    try {
      const data = await apiFetch(`/api/roadmaps/${id}/blockers`, { optionalAuth: true });
      setBlockers(data);
    } catch (err) {
      console.error('Failed to load blockers:', err);
      setBlockers({ blockers: [], total_incomplete: 0 });
    } finally {
      setBlockersLoading(false);
    }
  }, [id]);

  // On load: center on the furthest-completed topic, or the first node if none done
  useEffect(() => {
    if (!instanceReady || didInitialFocus.current || nodes.length === 0 || rawNodes.length === 0) return;
    const tops = rawNodes.filter((n) => !n.parent_id);
    const doneTops = tops.filter((n) => statusMap[n.id] === 'done');
    let targetId = null;
    if (doneTops.length) targetId = doneTops.reduce((a, b) => (a.order_index > b.order_index ? a : b)).id;
    else if (tops.length) targetId = tops.reduce((a, b) => (a.order_index < b.order_index ? a : b)).id;
    if (targetId) { focusNode(targetId); didInitialFocus.current = true; }
  }, [instanceReady, nodes, rawNodes, statusMap, focusNode]);

  const onNodeClick = useCallback((e, node) => {
    if (node.type === 'step') return;
    setContextNode(null);
    toggleComplete(node.id);
  }, [toggleComplete]);

  const onNodeContextMenu = useCallback((e, node) => {
    e.preventDefault();
    if (node.type === 'step') return;
    const raw = rawNodes.find((n) => n.id === node.id);
    setContextNode({ raw, x: e.clientX, y: e.clientY });
  }, [rawNodes]);

  const onNodeDoubleClick = useCallback((e, node) => {
    if (node.type === 'step') return;
    const kids = childrenByParent[node.id] || [];
    if (kids.length === 0) return; // "if any"
    setContextNode(null);
    setExpanded((s) => {
      const ns = new Set(s);
      ns.has(node.id) ? ns.delete(node.id) : ns.add(node.id);
      return ns;
    });
  }, [childrenByParent]);

  /* ---- progress ---- */
  const { done, total, pct } = useMemo(() => {
    const ids = rawNodes.map((n) => n.id);
    const d = ids.filter((i) => statusMap[i] === 'done').length;
    const t = ids.length;
    return { done: d, total: t, pct: t ? Math.round((d / t) * 100) : 0 };
  }, [rawNodes, statusMap]);

  // Export the roadmap to a styled PDF (header band, progress bar, phase cards,
  // checkboxes reflecting your progress, and tier badges).
  const downloadPdf = useCallback(() => {
    if (!meta || rawNodes.length === 0) return;
    // jsPDF's built-in fonts are WinAnsi — normalise smart punctuation to ASCII.
    const clean = (s) => (s || '').replace(/[—–]/g, '-').replace(/[‘’]/g, "'").replace(/[“”]/g, '"');

    const C = {
      navy: [19, 27, 46], slate: [15, 23, 42], ink: [30, 41, 59], muted: [100, 116, 139],
      cyan: [8, 145, 178], teal: [15, 118, 110], amber: [180, 83, 9], red: [185, 28, 28],
      track: [226, 232, 240], card: [243, 246, 250], hair: [226, 232, 240],
    };
    const tierColor = (t) => (t === 'easy' ? C.teal : t === 'medium' ? C.amber : t === 'hard' ? C.red : C.cyan);

    const doc = new jsPDF({ unit: 'pt', format: 'a4' });
    const pageW = doc.internal.pageSize.getWidth();
    const pageH = doc.internal.pageSize.getHeight();
    const margin = 44;
    const right = pageW - margin;
    let y = 0;
    const ensure = (h) => { if (y + h > pageH - 46) { doc.addPage(); y = margin; } };

    // ---------- Header band ----------
    doc.setFillColor(...C.navy); doc.rect(0, 0, pageW, 96, 'F');
    doc.setTextColor(255, 255, 255); doc.setFont('helvetica', 'bold'); doc.setFontSize(20);
    doc.text(clean(meta.title), margin, 42, { maxWidth: pageW - margin * 2 });
    doc.setFont('helvetica', 'bold'); doc.setFontSize(8); doc.setTextColor(120, 200, 218);
    doc.text('RETAINHQ  ·  LEARNING ROADMAP', margin, 58, { charSpace: 0.5 });
    doc.setTextColor(210, 220, 235); doc.setFont('helvetica', 'normal'); doc.setFontSize(9);
    doc.text(`${pct}%  ·  ${done}/${total} complete`, right, 58, { align: 'right' });
    // progress bar
    doc.setFillColor(44, 56, 82); doc.roundedRect(margin, 72, pageW - margin * 2, 7, 3.5, 3.5, 'F');
    if (pct > 0) { doc.setFillColor(...C.cyan); doc.roundedRect(margin, 72, Math.max((pageW - margin * 2) * pct / 100, 5), 7, 3.5, 3.5, 'F'); }

    y = 96 + 26;

    // ---------- Description ----------
    if (meta.description) {
      doc.setFont('helvetica', 'normal'); doc.setFontSize(9.5); doc.setTextColor(...C.muted);
      const lines = doc.splitTextToSize(clean(meta.description), pageW - margin * 2);
      ensure(lines.length * 12); doc.text(lines, margin, y); y += lines.length * 12 + 8;
    }

    const phases = [];
    rawNodes.forEach((n) => { if (!phases.includes(n.phase)) phases.push(n.phase); });

    phases.forEach((phase) => {
      const inPhase = rawNodes.filter((n) => n.phase === phase);
      const phDone = inPhase.filter((n) => statusMap[n.id] === 'done').length;

      // phase card header
      ensure(40); y += 6;
      doc.setFillColor(...C.card); doc.roundedRect(margin, y, pageW - margin * 2, 26, 4, 4, 'F');
      doc.setFillColor(...C.cyan); doc.roundedRect(margin, y, 4, 26, 2, 2, 'F');
      doc.setTextColor(...C.navy); doc.setFont('helvetica', 'bold'); doc.setFontSize(12.5);
      doc.text(clean(phase), margin + 14, y + 17, { maxWidth: pageW - margin * 2 - 90 });
      doc.setTextColor(...C.muted); doc.setFont('helvetica', 'normal'); doc.setFontSize(8.5);
      doc.text(`${phDone}/${inPhase.length}`, right - 10, y + 17, { align: 'right' });
      y += 26 + 14;

      const sections = [];
      inPhase.forEach((n) => { if (!sections.includes(n.section)) sections.push(n.section); });
      sections.forEach((section) => {
        ensure(20);
        doc.setFont('helvetica', 'bold'); doc.setFontSize(8.5); doc.setTextColor(...C.cyan);
        doc.text(clean(section).toUpperCase(), margin + 4, y, { charSpace: 0.4 });
        y += 13;

        inPhase.filter((n) => n.section === section).forEach((n) => {
          const isDone = statusMap[n.id] === 'done';
          const tier = n.tier;
          const badgeW = tier ? 52 : 0; // reserved slot for the right-aligned tier pill
          const textX = margin + 6 + 11 + 6;
          doc.setFont('helvetica', 'normal'); doc.setFontSize(9.5);
          const wrapped = doc.splitTextToSize(clean(n.title), right - textX - badgeW - 6);
          const rowH = wrapped.length * 11.5;
          ensure(rowH + 6);
          const baseline = y + 8;

          // checkbox
          const cbX = margin + 6, cbY = y + 1, cb = 10;
          if (isDone) {
            doc.setFillColor(...C.teal); doc.roundedRect(cbX, cbY, cb, cb, 2, 2, 'F');
            doc.setDrawColor(255, 255, 255); doc.setLineWidth(1.3);
            doc.line(cbX + 2.4, cbY + 5.2, cbX + 4.2, cbY + 7.2);
            doc.line(cbX + 4.2, cbY + 7.2, cbX + 8, cbY + 2.8);
          } else {
            doc.setDrawColor(196, 204, 216); doc.setLineWidth(0.9);
            doc.roundedRect(cbX, cbY, cb, cb, 2, 2, 'S');
          }

          // title
          doc.setTextColor(...(isDone ? C.muted : C.slate));
          doc.text(wrapped, textX, baseline);

          // tier badge (right-aligned, on first line)
          if (tier) {
            const tc = tierColor(tier);
            const label = tier.toUpperCase();
            doc.setFont('helvetica', 'bold'); doc.setFontSize(7);
            const tw = doc.getTextWidth(label);
            const bw = tw + 12, bh = 12, bx = right - bw, by = y;
            doc.setDrawColor(...tc); doc.setLineWidth(0.8);
            doc.roundedRect(bx, by, bw, bh, 6, 6, 'S');
            doc.setTextColor(...tc); doc.text(label, bx + 6, by + 8.2);
          }

          y += rowH + 5;
        });
        y += 4;
      });
    });

    // ---------- Footer on every page ----------
    const pages = doc.getNumberOfPages();
    for (let i = 1; i <= pages; i++) {
      doc.setPage(i);
      doc.setDrawColor(...C.hair); doc.setLineWidth(0.5);
      doc.line(margin, pageH - 34, right, pageH - 34);
      doc.setFont('helvetica', 'normal'); doc.setFontSize(7.5); doc.setTextColor(...C.muted);
      doc.text('Generated with RetainHQ', margin, pageH - 22);
      doc.text(`Page ${i} of ${pages}`, right, pageH - 22, { align: 'right' });
    }

    doc.save(`${clean(meta.title).replace(/[^a-z0-9]+/gi, '-').replace(/^-|-$/g, '')}.pdf`);
  }, [meta, rawNodes, statusMap, pct, done, total]);

  if (loading) {
    return (
      <div className="flex flex-col h-full">
        <div className="px-4 md:px-8 pt-4 md:pt-6 pb-3 border-b border-[rgba(15,23,42,0.08)] bg-[#f9f9f6]">
          <div className="skeleton h-4 w-36 mb-3" />
          <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-3">
            <div className="flex items-center gap-3 min-w-0">
              <div className="skeleton shrink-0 w-12 h-12 rounded-xl" />
              <div className="min-w-0 flex flex-col gap-2">
                <div className="skeleton h-5 w-48" />
                <div className="skeleton h-3 w-64" />
              </div>
            </div>
            <div className="flex items-center gap-3 shrink-0">
              <div className="skeleton w-40 h-2 rounded-full" />
              <div className="skeleton h-4 w-10" />
            </div>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto" style={{ minHeight: 0 }}>
          <div className="max-w-3xl mx-auto w-full px-4 md:px-8 py-6 pb-24 flex flex-col gap-3">
            {[0, 1, 2].map((i) => (
              <div key={i} className="glass-card !p-0 overflow-hidden">
                <div className="flex items-center gap-2.5 px-4 py-3">
                  <div className="skeleton h-4 w-40" />
                  <div className="flex-1" />
                  <div className="skeleton h-4 w-10 rounded-full" />
                </div>
                <div className="border-t border-[rgba(15,23,42,0.06)]">
                  {[0, 1, 2].map((j) => (
                    <div key={j} className="border-t border-[rgba(15,23,42,0.05)] flex items-center gap-3 px-4 py-2.5">
                      <div className="skeleton w-5 h-5 rounded-full shrink-0" />
                      <div className="skeleton h-3.5 flex-1 max-w-xs" />
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }
  if (!meta) return <div className="p-8 text-center text-[#ba1a1a]">Roadmap not found.</div>;

  const { Icon: RoadmapIcon, accent } = getRoadmapStyle(meta.title);

  return (
    <div className="flex flex-col h-full" onClick={() => setContextNode(null)}>
      {/* Header */}
      <div className="px-4 md:px-8 pt-4 md:pt-6 pb-3 border-b border-[rgba(15,23,42,0.08)] bg-[#f9f9f6]">
        <button
          onClick={() => navigate('/roadmaps')}
          className="flex items-center gap-2 text-[#64748B] hover:text-[#0F172A] font-sans text-sm font-medium mb-3 transition-colors"
        >
          <ArrowLeft size={16} /> Back to Roadmaps
        </button>
        <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            {/* Official logo / themed glyph — matches the roadmap list card identity */}
            <div
              className="glass-card shrink-0 w-12 h-12 flex items-center justify-center !rounded-xl"
              style={{ borderBottomColor: accent, borderBottomWidth: '2px' }}
            >
              <RoadmapLogo title={meta.title} Icon={RoadmapIcon} accent={accent} size={24} />
            </div>
            <div className="min-w-0">
              <h1 className="font-sans text-xl md:text-2xl font-semibold text-[#0F172A] truncate">{meta.title}</h1>
              <p className="font-sans text-xs text-[#64748B] mt-0.5 max-w-2xl line-clamp-1">{meta.description}</p>
            </div>
          </div>
          <div className="flex items-center gap-3 shrink-0">
            <div className="w-40 h-2 bg-[rgba(15,23,42,0.06)] rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-[#0891B2] to-[#0F766E] transition-all duration-500" style={{ width: `${pct}%` }} />
            </div>
            <span className="font-mono text-sm font-semibold text-[#0F172A]">{pct}%</span>
            <span className="font-mono text-[11px] text-[#64748B]">{done}/{total}</span>
            <button
              onClick={openBlockers}
              title="See which foundational topics to tackle first"
              className="flex items-center gap-1.5 text-xs font-semibold text-[#0891B2] border border-[#0891B2]/30 hover:bg-[#0891B2]/10 rounded px-2.5 py-1.5 transition-colors"
            >
              <Compass size={14} /> Why am I stuck?
            </button>
            <button
              onClick={downloadPdf}
              title="Download this roadmap as a PDF"
              className="flex items-center gap-1.5 text-xs font-semibold text-[#0891B2] border border-[#0891B2]/30 hover:bg-[#0891B2]/10 rounded px-2.5 py-1.5 transition-colors"
            >
              <Download size={14} /> PDF
            </button>
            <div className="flex rounded border border-[rgba(15,23,42,0.12)] overflow-hidden">
              <button
                onClick={() => switchView('list')}
                className={`flex items-center gap-1 text-xs font-semibold px-2.5 py-1.5 transition-colors ${view === 'list' ? 'bg-[rgba(15,23,42,0.06)] text-[#0F172A]' : 'text-[#64748B] hover:text-[#0F172A]'}`}
              >
                <List size={13} /> List
              </button>
              <button
                onClick={() => switchView('map')}
                className={`flex items-center gap-1 text-xs font-semibold px-2.5 py-1.5 transition-colors border-l border-[rgba(15,23,42,0.12)] ${view === 'map' ? 'bg-[rgba(15,23,42,0.06)] text-[#0F172A]' : 'text-[#64748B] hover:text-[#0F172A]'}`}
              >
                <MapIcon size={13} /> Map
              </button>
            </div>
          </div>
        </div>
        {/* interaction hint — only the map view has hidden gestures to explain */}
        {view === 'map' && (
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-3 font-sans text-[11px] text-[#64748B]">
            <span className="flex items-center gap-1"><MousePointerClick size={12} /> Left-click: complete</span>
            <span className="flex items-center gap-1"><StickyNote size={12} /> Right-click: notes</span>
            <span className="flex items-center gap-1"><ChevronDown size={12} /> Double-click: subtopics</span>
          </div>
        )}
      </div>

      {/* List view (default) */}
      {view === 'list' && (
        <div className="flex-1 overflow-y-auto" style={{ minHeight: 0 }}>
          <div className="max-w-3xl mx-auto w-full px-4 md:px-8 py-6 pb-24">
            <ListView
              rawNodes={rawNodes}
              statusMap={statusMap}
              childrenByParent={childrenByParent}
              collapsedPhases={collapsedPhases ?? new Set()}
              onTogglePhase={(phase) =>
                setCollapsedPhases((s) => {
                  const ns = new Set(s ?? []);
                  ns.has(phase) ? ns.delete(phase) : ns.add(phase);
                  return ns;
                })
              }
              openTopic={openTopic}
              onOpenTopic={(id) => setOpenTopic((cur) => (cur === id ? null : id))}
              onToggleComplete={toggleComplete}
              slugByTitle={slugByTitle}
              roadmapId={id}
              contentKey={contentKey}
            />
          </div>
        </div>
      )}

      {/* Flow canvas */}
      <div className={`flex-1 relative ${view === 'map' ? '' : 'hidden'}`} style={{ minHeight: 0 }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          onNodeClick={onNodeClick}
          onNodeContextMenu={onNodeContextMenu}
          onNodeDoubleClick={onNodeDoubleClick}
          onInit={(inst) => { rfRef.current = inst; setInstanceReady(true); }}
          defaultViewport={{ x: 0, y: 0, zoom: 0.9 }}
          minZoom={0.2}
          maxZoom={1.8}
          proOptions={{ hideAttribution: true }}
        >
          <Background color="#cbd5e1" gap={20} />
          <Controls showInteractive={false} />
          <MiniMap
            pannable
            zoomable
            nodeColor={(n) => (n.type === 'step' ? '#131b2e' : n.data?.status === 'done' ? '#0F766E' : '#cbd5e1')}
          />
        </ReactFlow>

        {/* Notes popup (right-click) */}
        {contextNode && (
          <div
            className="fixed z-50 w-72 bg-white rounded-lg shadow-2xl border border-[rgba(15,23,42,0.12)] p-4 animate-in fade-in zoom-in-95 duration-150"
            style={{ left: Math.min(contextNode.x, window.innerWidth - 300), top: Math.min(contextNode.y, window.innerHeight - 200) }}
            onClick={(e) => e.stopPropagation()}
          >
            {(() => {
              const desc = contextNode.raw.description;
              const isLink = desc && /^https?:\/\//.test(desc.trim());
              const isNeetcode = isLink && desc.includes('neetcode.io');
              return (
                <>
                  <div className="flex justify-between items-start mb-2">
                    <div className="font-sans text-[11px] font-bold text-[#0891B2] uppercase tracking-widest flex items-center gap-1">
                      <StickyNote size={12} /> {isLink ? 'Resource' : 'Notes'}
                    </div>
                    <button onClick={() => setContextNode(null)} className="text-[#94a3b8] hover:text-[#0F172A]">
                      <X size={14} />
                    </button>
                  </div>
                  <h4 className="font-sans text-sm font-semibold text-[#0F172A] mb-2">{contextNode.raw.title}</h4>
                  {isLink ? (
                    <a
                      href={desc.trim()}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="kinetic-btn kinetic-accent-gradient w-full py-2 text-xs flex items-center justify-center gap-1.5 font-medium"
                    >
                      <ExternalLink size={13} /> {isNeetcode ? 'Solve on NeetCode' : 'Open link'}
                    </a>
                  ) : (
                    <p className="font-sans text-xs text-[#475569] leading-relaxed">
                      {desc || 'No notes yet for this topic.'}
                    </p>
                  )}
                </>
              );
            })()}
          </div>
        )}
      </div>

      {/* "Why am I stuck?" — dependency-graph diagnosis */}
      {blockersOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/30"
          onClick={() => setBlockersOpen(false)}
        >
          <div
            className="w-full max-w-md bg-white rounded-xl shadow-2xl border border-[rgba(15,23,42,0.12)] max-h-[80vh] overflow-y-auto animate-in fade-in zoom-in-95 duration-150"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between px-5 py-4 border-b border-[rgba(15,23,42,0.08)] sticky top-0 bg-white">
              <div className="flex items-center gap-2">
                <Compass size={16} className="text-[#0891B2]" />
                <h3 className="font-sans text-sm font-semibold text-[#0F172A]">Why am I stuck?</h3>
              </div>
              <button onClick={() => setBlockersOpen(false)} className="text-[#94a3b8] hover:text-[#0F172A]">
                <X size={16} />
              </button>
            </div>
            <div className="p-5">
              {blockersLoading ? (
                <p className="font-sans text-sm text-[#64748B] text-center py-8">Analyzing your progress…</p>
              ) : !blockers || blockers.blockers.length === 0 ? (
                <p className="font-sans text-sm text-[#64748B] text-center py-8 leading-relaxed">
                  Nothing's blocking you on this roadmap — the foundations are covered. Keep going.
                </p>
              ) : (
                <>
                  <p className="font-sans text-xs text-[#64748B] mb-4 leading-relaxed">
                    These are ready to learn now (their prerequisites are done) and they unlock the
                    most of what's ahead. Start here — it's the fastest way forward.
                  </p>
                  <div className="flex flex-col gap-2.5">
                    {blockers.blockers.map((b, i) => (
                      <div key={b.node_id} className="rounded-lg border border-[rgba(15,23,42,0.1)] p-3">
                        <div className="flex items-start gap-2.5">
                          <span className="shrink-0 w-5 h-5 rounded-full bg-[#0891B2]/10 text-[#0891B2] font-mono text-[11px] font-bold flex items-center justify-center mt-0.5">
                            {i + 1}
                          </span>
                          <div className="min-w-0 flex-1">
                            <div className="font-sans text-sm font-semibold text-[#0F172A] leading-snug">{b.title}</div>
                            <div className="font-sans text-[11px] text-[#64748B] mt-0.5">{b.section}</div>
                            <div className="font-sans text-[11px] text-[#0F766E] font-medium mt-1.5">
                              Unlocks {b.unlocks_count} topic{b.unlocks_count === 1 ? '' : 's'}
                              {b.unlocks_sample?.length > 0 && (
                                <span className="text-[#94a3b8] font-normal">
                                  {' · '}{b.unlocks_sample.join(', ')}
                                  {b.unlocks_count > b.unlocks_sample.length ? '…' : ''}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Post-completion nudge: close the roadmap → capture loop without hijacking
          batch-checking. Auto-dismisses; "Log it" pre-fills the topic. */}
      {logPrompt && (
        <div className="fixed bottom-20 md:bottom-8 left-1/2 -translate-x-1/2 z-50 flex items-center gap-3 bg-[#131b2e] text-white rounded-lg shadow-xl px-4 py-3 animate-in fade-in slide-in-from-bottom-3 duration-200 max-w-[calc(100vw-2rem)]">
          <Check size={16} className="text-[#5DCAA5] shrink-0" />
          <span className="font-sans text-sm truncate max-w-[200px]">{logPrompt}</span>
          <button
            onClick={() => navigate(`/log?topic=${encodeURIComponent(logPrompt)}`)}
            className="flex items-center gap-1.5 font-sans text-sm font-semibold text-[#22D3EE] hover:text-white transition-colors shrink-0"
          >
            <PlusSquare size={14} /> Log what you learned
          </button>
          <button onClick={() => setLogPrompt(null)} aria-label="Dismiss" className="text-[#7c839b] hover:text-white shrink-0">
            <X size={14} />
          </button>
        </div>
      )}
    </div>
  );
}

/* ---------------- list view ---------------- */

// Match a roadmap node to its lesson. Lesson files are named slugify(node title),
// but lesson `title` fields drift from seed node titles — so match by SLUG (robust),
// with exact-title as a fallback. slugify mirrors content/_TODO generators (Python).
const slugifyTitle = (t) => (t || '').toLowerCase().replace(/&/g, 'and').replace(/\//g, ' ').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
function lessonSlugForNode(slugByTitle, title) {
  if (slugByTitle[title]) return slugByTitle[title];           // exact title match
  const s = slugifyTitle(title);
  return Object.values(slugByTitle).includes(s) ? s : null;    // slugified-title match
}

function ListView({ rawNodes, statusMap, childrenByParent, collapsedPhases, onTogglePhase, openTopic, onOpenTopic, onToggleComplete, slugByTitle, roadmapId, contentKey }) {
  const topLevel = rawNodes.filter((n) => !n.parent_id);
  const phases = [];
  topLevel.forEach((n) => { if (!phases.includes(n.phase)) phases.push(n.phase); });

  return (
    <div className="flex flex-col gap-3">
      {phases.map((phase) => {
        const inPhase = rawNodes.filter((n) => n.phase === phase);
        const phDone = inPhase.filter((n) => statusMap[n.id] === 'done').length;
        const allDone = phDone === inPhase.length;
        const collapsed = collapsedPhases.has(phase);
        const tops = topLevel.filter((n) => n.phase === phase).sort((a, b) => a.order_index - b.order_index);

        const sections = [];
        tops.forEach((n) => { if (!sections.includes(n.section)) sections.push(n.section); });
        const showSectionHeaders = sections.length > 1 || (sections[0] && sections[0] !== phase);

        return (
          <section key={phase} className="glass-card !p-0 overflow-hidden">
            <button
              onClick={() => onTogglePhase(phase)}
              className="w-full flex items-center gap-2.5 px-4 py-3 text-left hover:bg-[rgba(15,23,42,0.02)] transition-colors"
            >
              {collapsed ? <ChevronRight size={15} className="text-[#94a3b8] shrink-0" /> : <ChevronDown size={15} className="text-[#94a3b8] shrink-0" />}
              <span className="font-sans text-sm font-semibold text-[#0F172A] flex-1">{phase}</span>
              <span className={`font-mono text-[11px] px-2 py-0.5 rounded-full shrink-0 ${allDone ? 'bg-[#0F766E]/10 text-[#0F766E]' : 'text-[#64748B]'}`}>
                {phDone}/{inPhase.length}
              </span>
            </button>

            {!collapsed && (
              <div className="border-t border-[rgba(15,23,42,0.06)]">
                {sections.map((section) => (
                  <div key={section}>
                    {showSectionHeaders && (
                      <div className="px-4 pt-3 pb-1 font-sans text-[11px] font-semibold text-[#0891B2]">{section}</div>
                    )}
                    {tops.filter((n) => n.section === section).map((n) => (
                      <React.Fragment key={n.id}>
                        <TopicRow
                          node={n}
                          done={statusMap[n.id] === 'done'}
                          open={openTopic === n.id}
                          onOpen={() => onOpenTopic(n.id)}
                          onToggle={() => onToggleComplete(n.id)}
                          learnSlug={lessonSlugForNode(slugByTitle, n.title)}
                          roadmapId={roadmapId}
                          contentKey={contentKey}
                        />
                        {(childrenByParent[n.id] || []).map((c) => (
                          <TopicRow
                            key={c.id}
                            node={c}
                            done={statusMap[c.id] === 'done'}
                            open={openTopic === c.id}
                            onOpen={() => onOpenTopic(c.id)}
                            onToggle={() => onToggleComplete(c.id)}
                            isChild
                            learnSlug={lessonSlugForNode(slugByTitle, c.title)}
                            roadmapId={roadmapId}
                            contentKey={contentKey}
                          />
                        ))}
                      </React.Fragment>
                    ))}
                  </div>
                ))}
              </div>
            )}
          </section>
        );
      })}
    </div>
  );
}

function TopicRow({ node, done, open, onOpen, onToggle, isChild, learnSlug, roadmapId, contentKey }) {
  const navigate = useNavigate();
  const desc = node.description;
  const hasInfo = Boolean(desc);
  const isLink = hasInfo && /^https?:\/\//.test(desc.trim());
  const isNeetcode = isLink && desc.includes('neetcode.io');
  const tierColor = TIER_COLORS[node.tier];

  return (
    <div className={`border-t border-[rgba(15,23,42,0.05)] ${isChild ? 'pl-6' : ''}`}>
      <div className="flex items-center gap-3 px-4 py-2.5">
        <button
          onClick={onToggle}
          aria-label={done ? 'Mark as not started' : 'Mark as done'}
          className={`w-5 h-5 rounded shrink-0 flex items-center justify-center border transition-colors ${
            done ? 'bg-[#0F766E] border-[#0F766E]' : 'border-[rgba(15,23,42,0.3)] hover:border-[#0891B2]'
          }`}
        >
          {done && <Check size={12} className="text-white" />}
        </button>

        <button
          onClick={hasInfo ? onOpen : onToggle}
          className={`flex-1 min-w-0 text-left font-sans text-sm leading-snug ${done ? 'text-[#94a3b8] line-through' : 'text-[#0F172A]'}`}
        >
          {node.title}
        </button>

        {learnSlug && (
          <button
            onClick={(e) => { e.stopPropagation(); navigate(`/roadmaps/${roadmapId}/learn/${learnSlug}`, { state: { contentKey, nodeId: node.id } }); }}
            className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-semibold text-[#0891B2] bg-[#0891B2]/10 hover:bg-[#0891B2]/20 transition-colors shrink-0"
          >
            <BookOpen size={12} /> Learn
          </button>
        )}
        {tierColor && <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: tierColor }} title={node.tier} />}
        {hasInfo && (
          <button onClick={onOpen} aria-label="Show notes" className="text-[#94a3b8] hover:text-[#0F172A] shrink-0">
            {open ? <ChevronDown size={14} /> : <StickyNote size={13} />}
          </button>
        )}
      </div>

      {open && hasInfo && (
        <div className="px-4 pb-3 pl-12 animate-in fade-in duration-150">
          {isLink ? (
            <a
              href={desc.trim()}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 font-sans text-xs font-semibold text-[#0891B2] hover:text-[#0F172A] transition-colors"
            >
              <ExternalLink size={13} /> {isNeetcode ? 'Solve on NeetCode' : 'Open link'}
            </a>
          ) : (
            <p className="font-sans text-xs text-[#475569] leading-relaxed">{desc}</p>
          )}
        </div>
      )}
    </div>
  );
}

export default RoadmapDetail;
