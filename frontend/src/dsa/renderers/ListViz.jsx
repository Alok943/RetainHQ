import { motion } from 'framer-motion';

const C = {
  visited: '#7C3AED', matched: '#0F766E', path: '#0891B2',
  idle: '#cbd5e1', pointer: '#B45309',
};

const PTR_LABELS = { slow: 'S', fast: 'F', prev: 'prev', curr: 'curr', head: 'head', next: 'next', dummy: 'dummy' };

export default function ListViz({ frame }) {
  if (!frame) return null;
  const { list, listPtrs = {}, nodeTags = {} } = frame;
  if (!list || !list.nodes) return null;

  const PITCH = 80;
  
  return (
    <div className="flex justify-center select-none p-4">
      <svg viewBox={`0 0 ${list.nodes.length * PITCH + 20} 140`} className="w-full max-w-2xl overflow-visible">
        <defs>
          <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#94a3b8" />
          </marker>
        </defs>
        
        {/* Edges */}
        {list.nodes.map((n, i) => {
          if (n.next == null) return null;
          const nextIdx = list.nodes.findIndex(x => x.id === n.next);
          if (nextIdx === -1) return null;
          
          const fromX = i * PITCH + 40;
          const fromY = 70;
          const toX = nextIdx * PITCH;
          const toY = 70;
          
          if (nextIdx === i + 1) {
            return (
              <motion.line key={`${n.id}-${n.next}`} x1={fromX} y1={fromY} x2={toX - 2} y2={toY} 
                stroke="#cbd5e1" strokeWidth={2} markerEnd="url(#arrow)" layout />
            );
          }
          
          const dx = toX - fromX;
          const isBackEdge = nextIdx < i;
          const cy = isBackEdge ? 20 : 120;
          
          return (
            <motion.path key={`${n.id}-${n.next}`}
              d={`M ${fromX} ${fromY} Q ${fromX + dx/2} ${cy} ${toX} ${toY + (isBackEdge ? -15 : 15)}`}
              stroke="#cbd5e1" strokeWidth={2} fill="none" markerEnd="url(#arrow)" layout />
          );
        })}
        
        {/* Nodes */}
        {list.nodes.map((n, i) => {
          const x = i * PITCH;
          const y = 70;
          const labels = Object.entries(listPtrs).filter(([k,v]) => v === n.id).map(([k]) => PTR_LABELS[k] || k);
          
          return (
            <g key={n.id} transform={`translate(${x}, ${y})`}>
              {labels.length > 0 && (
                <text y={-25} x={20} textAnchor="middle" className="font-mono text-[11px] fill-[#B45309]">
                  {labels.join(' ')}
                </text>
              )}
              <motion.rect x={0} y={-15} width={40} height={30} rx={4}
                fill={nodeTags[n.id] ? C[nodeTags[n.id]] || '#fff' : '#fff'}
                stroke="#94a3b8" strokeWidth={1.5} layout />
              <text x={20} y={4} textAnchor="middle" className="font-mono text-[13px] font-bold">
                {n.value}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
