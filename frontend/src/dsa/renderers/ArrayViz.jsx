import { motion } from 'framer-motion';

// Renders ONE compiled frame's array as bars. Bars are keyed by index, so a WRITE animates that
// position's height/colour (you watch values land during a merge). Colour encodes per-index state:
// sorted > active-write > region (merging/left/right) > default. Region brackets + the write pointer
// sit under/over the bars. Pure presentation — all data comes from the frame.
const C = {
  sorted: '#0F766E', write: '#7C3AED', merging: '#0891B2',
  left: '#0891B2', right: '#B45309', idle: '#cbd5e1', ink: '#0F172A', slate: '#64748B',
  pointer: '#B45309',
};

// Named pointers the renderer knows how to draw above a bar. `write` keeps its ▼;
// the two-pointer / array-family markers (lo/hi/i/j) draw as small labels.
const PTR_LABELS = { write: '▼', lo: 'lo', hi: 'hi', i: 'i', j: 'j', mid: 'mid', left: 'L', right: 'R', slow: 'S', fast: 'F' };

function regionOf(i, regions) {
  for (const r of regions || []) if (i >= r.lo && i <= r.hi) return r.label;
  return null;
}

export default function ArrayViz({ frame }) {
  if (!frame) return null;
  const { array, regions = [], sorted = [], pointers = {} } = frame;
  const sortedSet = new Set(sorted);
  // String/char traces render fixed-height cells (the letter), not value-scaled bars.
  const isNumeric = array.every((v) => typeof v === 'number');
  const maxVal = Math.max(1, ...(isNumeric ? array : [1]));

  // index -> the pointer labels sitting on it (e.g. ['lo'] or ['i'])
  const labelsAt = (i) =>
    Object.entries(pointers)
      .filter(([k, v]) => v === i && PTR_LABELS[k] && k !== 'write')
      .map(([k]) => PTR_LABELS[k]);

  const colorOf = (i) => {
    if (sortedSet.has(i)) return C.sorted;
    if (pointers.write === i || pointers.mid === i) return C.write; // active write / binary-search probe
    // active pointer cells (swap / two-pointer compare)
    if (pointers.i === i || pointers.j === i || pointers.lo === i || pointers.hi === i) return C.pointer;
    const reg = regionOf(i, regions);
    if (reg === 'merging') return C.merging;
    if (reg === 'left') return C.left;
    if (reg === 'right') return C.right;
    return C.idle;
  };

  // Cell pitch (bar width 34px + gap-1.5 = 6px = 40px) — shared by the backdrop and bracket layers
  // so they line up with the bars they annotate.
  const PITCH = 40;
  const regionColor = (label) => label === 'sorted' ? C.sorted : (label === 'merging' || label === 'sorting') ? C.merging
    : label === 'left' ? C.left : label === 'right' ? C.right : 'transparent';

  return (
    <div className="select-none">
      <div className="flex justify-center">
        <div className="relative">
          {/* active-window backdrop — sits behind the bars, one translucent rect per merging/sorting region */}
          <div className="absolute inset-y-0 left-0 right-0" style={{ zIndex: 0 }}>
            {regions.filter((r) => r.label === 'merging' || r.label === 'sorting').map((r, idx) => (
              <div key={idx} className="absolute inset-y-0" style={{
                left: r.lo * PITCH, width: (r.hi - r.lo + 1) * PITCH - 6,
                background: 'rgba(8,145,178,0.07)', borderRadius: 8,
              }} />
            ))}
          </div>
          <div className="relative z-10 flex items-end gap-1.5" style={{ height: 180 }}>
            {array.map((v, i) => (
              <div key={i} className="flex flex-col items-center justify-end" style={{ width: 34 }}>
                <span className="font-mono text-[11px] mb-1 h-[14px] flex items-center gap-0.5" style={{ color: pointers.write === i ? C.write : C.pointer }}>
                  {pointers.write === i ? '▼' : (labelsAt(i).join(' ') || '')}
                </span>
                <motion.div
                  className={`w-full ${isNumeric ? 'rounded-t-md flex items-start justify-center' : 'rounded-md flex items-center justify-center'}`}
                  animate={{ height: isNumeric ? 24 + (v / maxVal) * 130 : 40, backgroundColor: colorOf(i) }}
                  transition={{ type: 'spring', stiffness: 320, damping: 30 }}
                >
                  <span className={`font-mono text-[13px] font-bold text-white ${isNumeric ? 'mt-1' : ''}`}>{v}</span>
                </motion.div>
                <span className="font-mono text-[10px] text-[#94a3b8] mt-1">{i}</span>
              </div>
            ))}
          </div>
          {/* labeled region brackets — strip + label per region, positioned by the same pitch */}
          <div className="relative mt-1" style={{ height: 18 }}>
            {regions.map((r, idx) => {
              const col = regionColor(r.label);
              return (
                <span key={idx} className="absolute flex flex-col items-center" style={{ left: r.lo * PITCH, width: (r.hi - r.lo + 1) * PITCH - 6 }}>
                  <span className="block w-full" style={{ height: 3, backgroundColor: col, borderRadius: 2 }} />
                  <span className="font-sans text-[9px] font-semibold uppercase tracking-wide mt-0.5" style={{ color: col }}>{r.label}</span>
                </span>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
