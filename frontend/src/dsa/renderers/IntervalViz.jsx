import { motion } from 'framer-motion';

const C = {
  selected: '#7C3AED', merged: '#0F766E', skipped: '#cbd5e1', idle: '#38bdf8'
};

export default function IntervalViz({ frame }) {
  if (!frame) return null;
  const { intervals = [], intervalTags = {} } = frame;
  
  if (intervals.length === 0) return null;
  
  const minStart = Math.min(...intervals.map(i => i.start));
  const maxEnd = Math.max(...intervals.map(i => i.end));
  const range = Math.max(1, maxEnd - minStart);
  
  const ROW_HEIGHT = 40;
  
  const scaleX = (val) => `${((val - minStart) / range) * 100}%`;
  const widthX = (start, end) => `${((end - start) / range) * 100}%`;

  return (
    <div className="flex flex-col select-none p-4 w-full">
      <div className="relative w-full border-l-2 border-[#e2e8f0] pl-2" style={{ height: intervals.length * ROW_HEIGHT }}>
        {intervals.map((inv, i) => {
          const tag = intervalTags[inv.id];
          const color = tag ? C[tag] || C.idle : C.idle;
          
          return (
            <motion.div 
              key={inv.id}
              className="absolute h-6 rounded-md flex items-center justify-center text-[11px] font-mono font-bold text-white shadow-sm overflow-hidden"
              style={{
                left: scaleX(inv.start),
                width: widthX(inv.start, inv.end),
                top: i * ROW_HEIGHT
              }}
              animate={{ backgroundColor: color }}
              layout
            >
              <span>[{inv.start},{inv.end}]</span>
            </motion.div>
          );
        })}
      </div>
      
      {/* Basic axis markers */}
      <div className="relative w-full h-4 mt-2 border-t-2 border-[#e2e8f0]">
        <span className="absolute left-0 top-1 text-[10px] font-mono text-[#94a3b8] -translate-x-1/2">{minStart}</span>
        <span className="absolute right-0 top-1 text-[10px] font-mono text-[#94a3b8] translate-x-1/2">{maxEnd}</span>
      </div>
    </div>
  );
}
