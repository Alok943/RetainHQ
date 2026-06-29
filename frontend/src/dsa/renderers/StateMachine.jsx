import { motion, AnimatePresence } from 'framer-motion';

// Renders the recursion CALL STACK from a frame — the "aha" for recursion that bars can't show.
// Newest call on top (highlighted = currently executing). Push/pop animate via AnimatePresence.
// Driven entirely by frame.callStack ([{lo, hi}], bottom→top).
export default function StateMachine({ frame }) {
  const stack = (frame?.callStack || []);
  const view = [...stack].reverse(); // top of stack first (visually on top)

  return (
    <div className="select-none">
      <div className="font-sans text-[10px] font-bold uppercase tracking-wider text-[#64748B] mb-2">Call stack</div>
      <div className="flex flex-col gap-1.5 min-h-[180px] justify-end">
        <AnimatePresence initial={false}>
          {view.map((f, idx) => {
            const isTop = idx === 0;
            return (
              <motion.div
                key={`${f.lo}-${f.hi}`}
                layout
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 12 }}
                transition={{ type: 'spring', stiffness: 360, damping: 32 }}
                className="rounded-md px-3 py-2 font-mono text-[12.5px] border"
                style={{
                  background: isTop ? 'rgba(124,58,237,0.10)' : 'rgba(15,23,42,0.03)',
                  borderColor: isTop ? '#7C3AED' : 'rgba(15,23,42,0.10)',
                  color: isTop ? '#7C3AED' : '#475569',
                  fontWeight: isTop ? 700 : 500,
                }}
              >
                mergeSort([{f.lo}..{f.hi}])
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
