import { motion } from 'framer-motion';

const C = {
  active: '#7C3AED', result: '#0F766E', idle: '#f1f5f9', text: '#0F172A'
};

export default function BitsViz({ frame }) {
  if (!frame) return null;
  const { bits = [], activeCol, bitTags = {} } = frame;
  
  if (bits.length === 0) return null;
  
  const maxVal = Math.max(...bits.map(b => b.value));
  const numBits = Math.max(4, maxVal.toString(2).length);
  
  return (
    <div className="flex flex-col items-center select-none p-4 gap-2">
      {bits.map((b) => {
        const binStr = b.value.toString(2).padStart(numBits, '0');
        const tag = bitTags[b.id];
        const rowColor = tag === 'result' ? C.result : C.active;
        
        return (
          <div key={b.id} className="flex items-center gap-4">
            {b.label && <span className="w-16 text-right font-mono text-[12px] text-[#64748B]">{b.label}</span>}
            <div className="flex gap-1">
              {binStr.split('').map((bit, j) => {
                const colIdx = numBits - 1 - j; // 0 is LSB
                const isActive = activeCol === colIdx;
                
                return (
                  <motion.div 
                    key={j}
                    className="w-8 h-8 flex items-center justify-center rounded-sm font-mono text-[14px]"
                    animate={{
                      backgroundColor: isActive ? rowColor : C.idle,
                      color: isActive ? '#fff' : C.text
                    }}
                    layout
                  >
                    {bit}
                  </motion.div>
                );
              })}
            </div>
            <span className="w-12 font-mono text-[12px] font-bold text-left">{b.value}</span>
          </div>
        );
      })}
    </div>
  );
}
