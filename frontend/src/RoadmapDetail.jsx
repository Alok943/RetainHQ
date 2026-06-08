import React, { useEffect, useState, useCallback, useMemo, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { apiFetch } from './lib/api';
import { ArrowLeft, Check, ChevronDown, ChevronRight, StickyNote, X, MousePointerClick, ExternalLink, Download } from 'lucide-react';
import { jsPDF } from 'jspdf';
import { useAuth } from './lib/AuthContext';
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

  const [meta, setMeta] = useState(null);          // {title, description}
  const [rawNodes, setRawNodes] = useState([]);    // flat nodes from API
  const [statusMap, setStatusMap] = useState({});  // node_id -> status
  const [expanded, setExpanded] = useState(() => new Set());
  const [loading, setLoading] = useState(true);
  const [contextNode, setContextNode] = useState(null); // {raw, x, y}

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // Camera control
  const rfRef = useRef(null);
  const nodesRef = useRef([]);
  const [instanceReady, setInstanceReady] = useState(false);
  const didInitialFocus = useRef(false);
  useEffect(() => { nodesRef.current = nodes; }, [nodes]);

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
    if (!session) {
      setLoading(false);
      return;
    }
    async function load() {
      try {
        const data = await apiFetch(`/api/roadmaps/${id}`);
        setMeta({ title: data.title, description: data.description });
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
    if (next === 'done') focusNode(nodeId); // pan to the topic just completed
    try {
      await apiFetch(`/api/roadmaps/nodes/${nodeId}/progress`, {
        method: 'PUT',
        body: JSON.stringify({ status: next }),
      });
    } catch (err) {
      console.error('Failed to save progress:', err);
      setStatusMap((m) => ({ ...m, [nodeId]: cur })); // revert
    }
  }, [statusMap, focusNode]);

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

  if (loading) return <div className="p-8 text-center text-[#64748B]">Loading roadmap...</div>;
  if (!meta) return <div className="p-8 text-center text-[#ba1a1a]">Roadmap not found.</div>;

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
          <div>
            <h1 className="font-sans text-xl md:text-2xl font-semibold text-[#0F172A]">{meta.title}</h1>
            <p className="font-sans text-xs text-[#64748B] mt-0.5 max-w-2xl">{meta.description}</p>
          </div>
          <div className="flex items-center gap-3 shrink-0">
            <div className="w-40 h-2 bg-[rgba(15,23,42,0.06)] rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-[#0891B2] to-[#0F766E] transition-all duration-500" style={{ width: `${pct}%` }} />
            </div>
            <span className="font-mono text-sm font-semibold text-[#0F172A]">{pct}%</span>
            <span className="font-mono text-[11px] text-[#64748B]">{done}/{total}</span>
            <button
              onClick={downloadPdf}
              title="Download this roadmap as a PDF"
              className="flex items-center gap-1.5 text-xs font-semibold text-[#0891B2] border border-[#0891B2]/30 hover:bg-[#0891B2]/10 rounded px-2.5 py-1.5 transition-colors"
            >
              <Download size={14} /> PDF
            </button>
          </div>
        </div>
        {/* interaction hint */}
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-3 font-sans text-[11px] text-[#64748B]">
          <span className="flex items-center gap-1"><MousePointerClick size={12} /> Left-click: complete</span>
          <span className="flex items-center gap-1"><StickyNote size={12} /> Right-click: notes</span>
          <span className="flex items-center gap-1"><ChevronDown size={12} /> Double-click: subtopics</span>
        </div>
      </div>

      {/* Flow canvas */}
      <div className="flex-1 relative" style={{ minHeight: 0 }}>
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
    </div>
  );
}

export default RoadmapDetail;
