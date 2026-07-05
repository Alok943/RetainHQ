import React from 'react';
import { motion } from 'framer-motion';

// Colors adapted from ArrayViz
const C = {
  sorted: '#0F766E', write: '#7C3AED', merging: '#0891B2',
  left: '#0891B2', right: '#B45309', idle: '#cbd5e1', ink: '#0F172A', slate: '#64748B',
  pointer: '#B45309',
};

const FILL = {
  visited: C.merging,
  matched: C.sorted,
  path: C.pointer,
  invalid: '#E11D48',
  inserted: C.write,
};

function viewBoxFrom(nodes) {
  if (!nodes || nodes.length === 0) return '0 0 0 0';
  const xs = nodes.map(n => n.x);
  const ys = nodes.map(n => n.y);
  const minX = Math.min(...xs) - 40;
  const maxX = Math.max(...xs) + 40;
  const minY = Math.min(...ys) - 40;
  const maxY = Math.max(...ys) + 40;
  return `${minX} ${minY} ${maxX - minX} ${maxY - minY}`;
}

export default function TreeViz({ frame }) {
  const { tree, nodeTags = {}, nodeReturns = {}, cursor } = frame;
  if (!tree) return null;
  
  // Support both Map and plain object formats for safety
  const nodes = tree.nodes instanceof Map ? [...tree.nodes.values()] : Object.values(tree.nodes);
  const getNode = (id) => tree.nodes instanceof Map ? tree.nodes.get(id) : tree.nodes[id];

  return (
    <svg viewBox={viewBoxFrom(nodes)} className="w-full h-full max-h-[600px] select-none">
      {/* edges first (parent -> child lines) */}
      {nodes.flatMap(n => ['left', 'right'].filter(s => n[s] != null).map(s => {
        const c = getNode(n[s]);
        if (!c) return null;
        return (
          <line 
            key={`${n.id}-${s}`} 
            x1={n.x} 
            y1={n.y} 
            x2={c.x} 
            y2={c.y}
            stroke="#cbd5e1" 
            strokeWidth={2}
          />
        );
      }))}
      
      {/* nodes: circle + value; color by tag; ring on cursor */}
      {nodes.map(n => {
        const tag = nodeTags[n.id];
        const isFilled = !!tag;
        
        return (
          <g key={n.id} transform={`translate(${n.x},${n.y})`}>
            <motion.circle 
              r={18} 
              layout
              fill={FILL[tag] || '#fff'}
              stroke={n.id === cursor ? '#7C3AED' : '#94a3b8'}
              strokeWidth={n.id === cursor ? 3 : 1.5}
            />
            <text 
              textAnchor="middle" 
              dy="0.35em" 
              className="font-mono text-[13px] pointer-events-none"
              fill={isFilled ? '#fff' : C.ink}
            >
              {n.value}
            </text>
            {nodeReturns[n.id] != null && (
              <text 
                y={-26} 
                textAnchor="middle" 
                className="fill-[#0F766E] text-[11px] font-mono pointer-events-none"
              >
                ↑{nodeReturns[n.id]}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}
