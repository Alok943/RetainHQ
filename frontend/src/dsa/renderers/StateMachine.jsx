import { motion, AnimatePresence } from 'framer-motion';

const PTR_ORDER = ['lo', 'hi', 'i', 'j', 'write'];

// Side panel for the execution-trace player. For recursive traces it renders the CALL STACK
// (the "aha" bars can't show). For array-family traces (two pointers, prefix sums) there is no
// call stack, so it falls back to a POINTERS readout of the current named indices.
export default function StateMachine({ frame }) {
  const stack = (frame?.callStack || []);
  const view = [...stack].reverse(); // top of stack first (visually on top)

  // No recursion in this trace → show the pointer state instead of an empty call stack.
  if (stack.length === 0) {
    const ptrs = PTR_ORDER
      .filter((k) => typeof frame?.pointers?.[k] === 'number')
      .map((k) => [k, frame.pointers[k]]);
    return (
      <div className="select-none">
        <div className="font-sans text-[10px] font-bold uppercase tracking-wider text-[#64748B] mb-2">Pointers</div>
        <div className="flex flex-col gap-1.5 min-h-[180px] justify-center">
          {ptrs.length === 0 ? (
            <div className="font-mono text-[12px] text-[#94a3b8] italic">—</div>
          ) : (
            ptrs.map(([k, v]) => (
              <div key={k} className="flex items-center justify-between rounded-md px-3 py-2 font-mono text-[13px] border" style={{ background: 'rgba(124,58,237,0.06)', borderColor: 'rgba(15,23,42,0.10)' }}>
                <span className="font-bold text-[#7C3AED]">{k}</span>
                <span className="text-[#475569]">{v}</span>
              </div>
            ))
          )}
        </div>
      </div>
    );
  }

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
