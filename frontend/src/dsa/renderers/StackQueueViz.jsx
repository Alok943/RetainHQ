import { motion, AnimatePresence } from 'framer-motion';

export default function StackQueueViz({ frame }) {
  if (!frame) return null;
  const { stack, queue } = frame;

  if (stack) {
    const view = [...stack].reverse(); // top of stack first
    return (
      <div className="select-none">
        <div className="font-sans text-[10px] font-bold uppercase tracking-wider text-[#64748B] mb-2">STACK</div>
        <div className="flex flex-col gap-1.5 min-h-[180px] justify-end pl-6">
          <AnimatePresence initial={false}>
            {view.map((item, idx) => {
              const originalIndex = stack.length - 1 - idx;
              const isTop = idx === 0;
              return (
                <motion.div
                  key={`${originalIndex}-${item}`}
                  layout
                  initial={{ opacity: 0, x: -12 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 12 }}
                  transition={{ type: 'spring', stiffness: 360, damping: 32 }}
                  className="rounded-md px-3 py-2 font-mono text-[12.5px] border relative flex items-center justify-center"
                  style={{
                    background: isTop ? 'rgba(124,58,237,0.10)' : 'rgba(15,23,42,0.03)',
                    borderColor: isTop ? '#7C3AED' : 'rgba(15,23,42,0.10)',
                    color: isTop ? '#7C3AED' : '#475569',
                    fontWeight: isTop ? 700 : 500,
                  }}
                >
                  {isTop && (
                    <span className="absolute -left-6 text-[9px] font-bold uppercase tracking-wider text-[#7C3AED]">
                      top
                    </span>
                  )}
                  {item}
                </motion.div>
              );
            })}
          </AnimatePresence>
          {view.length === 0 && (
            <div className="font-mono text-[12px] text-[#94a3b8] italic">— empty —</div>
          )}
        </div>
      </div>
    );
  }

  if (queue) {
    return (
      <div className="select-none">
        <div className="font-sans text-[10px] font-bold uppercase tracking-wider text-[#64748B] mb-2">QUEUE</div>
        <div className="flex items-center gap-1.5 min-h-[80px] overflow-x-auto py-5">
          <AnimatePresence initial={false}>
            {queue.map((item, idx) => {
              const isFront = idx === 0;
              const isBack = idx === queue.length - 1;
              return (
                <motion.div
                  key={`${idx}-${item}`}
                  layout
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                  transition={{ type: 'spring', stiffness: 360, damping: 32 }}
                  className="rounded-md px-3 py-2 font-mono text-[12.5px] border relative flex items-center justify-center min-w-[40px]"
                  style={{
                    background: 'rgba(15,23,42,0.03)',
                    borderColor: 'rgba(15,23,42,0.10)',
                    color: '#475569',
                    fontWeight: 500,
                  }}
                >
                  {item}
                  {isFront && <span className="absolute -left-1 -bottom-4 text-[9px] font-bold uppercase text-[#64748B]">front</span>}
                  {isBack && <span className="absolute -left-1 -top-4 text-[9px] font-bold uppercase text-[#64748B]">back</span>}
                </motion.div>
              );
            })}
          </AnimatePresence>
          {queue.length === 0 && (
            <div className="font-mono text-[12px] text-[#94a3b8] italic">— empty —</div>
          )}
        </div>
      </div>
    );
  }

  return null;
}
