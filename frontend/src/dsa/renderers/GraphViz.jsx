import { useMemo } from 'react';
import { motion } from 'framer-motion';

const FILL = {
  visited: '#0F766E', // teal
  frontier: '#0891B2', // cyan
  current: '#7C3AED', // purple
  invalid: '#B45309', // amber
  matched: '#0F766E',
  path: '#7C3AED',    // purple
};

export default function GraphViz({ frame }) {
  if (!frame) return null;
  const { graph, nodeTags = {}, edges = [] } = frame;
  if (!graph) return null;

  const rawNodes = Array.isArray(graph.nodes) ? graph.nodes : (graph.nodes ? [...graph.nodes.values()] : []);
  const rawEdges = Array.isArray(edges) && edges.length > 0 ? edges : (Array.isArray(graph.edges) ? graph.edges : []);

  const { nodes, nodeMap, minX, maxX, minY, maxY } = useMemo(() => {
    const hasCoords = rawNodes.every(n => typeof n.x === 'number' && typeof n.y === 'number');
    
    const computedNodes = rawNodes.map((n, i) => {
      if (hasCoords) return { ...n };
      // Fallback to circular layout
      const radius = Math.max(100, rawNodes.length * 15);
      const angle = (i / rawNodes.length) * 2 * Math.PI - Math.PI / 2;
      return {
        ...n,
        x: radius * Math.cos(angle),
        y: radius * Math.sin(angle)
      };
    });

    const nm = new Map(computedNodes.map(n => [n.id, n]));
    
    let mnX = Infinity, mxX = -Infinity, mnY = Infinity, mxY = -Infinity;
    for (const n of computedNodes) {
      if (n.x < mnX) mnX = n.x;
      if (n.x > mxX) mxX = n.x;
      if (n.y < mnY) mnY = n.y;
      if (n.y > mxY) mxY = n.y;
    }
    
    if (computedNodes.length === 0) {
      mnX = 0; mxX = 100; mnY = 0; mxY = 100;
    }
    
    // Add padding to fit node radius (18) + some margin
    mnX -= 40; mxX += 40;
    mnY -= 50; mxY += 50;
    
    return { nodes: computedNodes, nodeMap: nm, minX: mnX, maxX: mxX, minY: mnY, maxY: mxY };
  }, [rawNodes]);

  return (
    <svg viewBox={`${minX} ${minY} ${maxX - minX} ${maxY - minY}`} className="w-full select-none">
      <defs>
        <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="28" refY="3.5" orient="auto">
          <polygon points="0 0, 10 3.5, 0 7" fill="#cbd5e1" />
        </marker>
        <marker id="arrowhead-highlight" markerWidth="10" markerHeight="7" refX="28" refY="3.5" orient="auto">
          <polygon points="0 0, 10 3.5, 0 7" fill="#7C3AED" />
        </marker>
      </defs>
      
      {/* Edges layer */}
      {rawEdges.map((e, idx) => {
        const u = nodeMap.get(e.u);
        const v = nodeMap.get(e.v);
        if (!u || !v) return null;
        
        const isHighlighted = e.tag === 'tree' || e.tag === 'MST' || e.tag === 'path';
        const stroke = isHighlighted ? '#7C3AED' : '#cbd5e1';
        const strokeWidth = isHighlighted ? 3 : 2;
        
        const mx = (u.x + v.x) / 2;
        const my = (u.y + v.y) / 2;
        
        return (
          <g key={`${e.u}-${e.v}-${idx}`}>
            <line
              x1={u.x} y1={u.y} x2={v.x} y2={v.y}
              stroke={stroke}
              strokeWidth={strokeWidth}
              markerEnd={e.directed ? (isHighlighted ? 'url(#arrowhead-highlight)' : 'url(#arrowhead)') : undefined}
            />
            {e.w != null && (
              <text x={mx} y={my - 6} textAnchor="middle" className="text-[12px] font-mono font-semibold"
                    fill="#475569" paintOrder="stroke" stroke="#fff" strokeWidth="4" strokeLinejoin="round">
                {e.w}
              </text>
            )}
          </g>
        );
      })}
      
      {/* Nodes layer */}
      {nodes.map(n => {
        const tag = nodeTags[n.id];
        const isCursor = n.id === frame.cursor || tag === 'current';
        const textColor = FILL[tag] ? '#ffffff' : '#0F172A';
        
        return (
          <g key={n.id} transform={`translate(${n.x},${n.y})`}>
            <motion.circle r={18} layout
              fill={FILL[tag] || '#ffffff'}
              stroke={isCursor ? '#7C3AED' : '#94a3b8'}
              strokeWidth={isCursor ? 3 : 1.5}
            />
            <text textAnchor="middle" dy="0.35em" className="font-mono text-[13px]" fill={textColor}>
              {n.value !== undefined ? n.value : n.id}
            </text>
            {n.dist != null && (
              <text y={-26} textAnchor="middle" className="font-mono text-[11px] font-semibold" fill="#0F766E">
                {n.dist}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}
