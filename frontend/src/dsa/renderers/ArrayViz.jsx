import { motion } from 'framer-motion';

// Renders ONE compiled frame's array as bars. Bars are keyed by index, so a WRITE animates that
// position's height/colour (you watch values land during a merge). Colour encodes per-index state:
// sorted > active-write > region (merging/left/right) > default. Region brackets + the write pointer
// sit under/over the bars. Pure presentation — all data comes from the frame.
const C = {
  sorted: '#0F766E', write: '#7C3AED', merging: '#0891B2',
  left: '#0891B2', right: '#B45309', idle: '#cbd5e1', ink: '#0F172A', slate: '#64748B',
};

function regionOf(i, regions) {
  for (const r of regions || []) if (i >= r.lo && i <= r.hi) return r.label;
  return null;
}

export default function ArrayViz({ frame }) {
  if (!frame) return null;
  const { array, regions = [], sorted = [], pointers = {} } = frame;
  const sortedSet = new Set(sorted);
  const maxVal = Math.max(1, ...array);

  const colorOf = (i) => {
    if (sortedSet.has(i)) return C.sorted;
    if (pointers.write === i) return C.write;
    const reg = regionOf(i, regions);
    if (reg === 'merging') return C.merging;
    if (reg === 'left') return C.left;
    if (reg === 'right') return C.right;
    return C.idle;
  };

  return (
    <div className="select-none">
      <div className="flex items-end justify-center gap-1.5" style={{ height: 180 }}>
        {array.map((v, i) => (
          <div key={i} className="flex flex-col items-center justify-end" style={{ width: 34 }}>
            <span className="font-mono text-[11px] mb-1" style={{ color: pointers.write === i ? C.write : C.slate }}>
              {pointers.write === i ? '▼' : ''}
            </span>
            <motion.div
              className="w-full rounded-t-md flex items-start justify-center"
              animate={{ height: 24 + (v / maxVal) * 130, backgroundColor: colorOf(i) }}
              transition={{ type: 'spring', stiffness: 320, damping: 30 }}
            >
              <span className="font-mono text-[12px] font-bold text-white mt-1">{v}</span>
            </motion.div>
            <span className="font-mono text-[10px] text-[#94a3b8] mt-1">{i}</span>
          </div>
        ))}
      </div>
      {/* region brackets */}
      <div className="flex justify-center gap-1.5 mt-1">
        {array.map((_, i) => {
          const reg = regionOf(i, regions);
          const col = reg === 'sorted' ? C.sorted : reg === 'merging' ? C.merging : reg === 'left' ? C.left : reg === 'right' ? C.right : 'transparent';
          return <div key={i} style={{ width: 34, height: 3, backgroundColor: col, borderRadius: 2 }} />;
        })}
      </div>
    </div>
  );
}
