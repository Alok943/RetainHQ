import React from 'react';
import { motion } from 'framer-motion';

// Color theme aligned with ArrayViz
const C = {
  idle: '#cbd5e1',     // slate-300
  ink: '#0F172A',      // slate-900
  write: '#7C3AED',    // violet-600
  queen: '#7C3AED',    // violet-600
  attacked: 'rgba(239, 68, 68, 0.15)', // translucent red for shaded ray squares
  path: '#0891B2',     // cyan-600
  max: '#0F766E',      // teal-700
  read: '#B45309',     // amber-700
};

export default function GridViz({ frame }) {
  if (!frame || !frame.grid) return null;
  const { grid, cellTags = {}, readCells = [] } = frame;
  const { rows, cols, cells, labels } = grid;

  const isRead = (r, c) => {
    const key = `${r},${c}`;
    if (readCells instanceof Set) return readCells.has(key);
    return Array.isArray(readCells) ? readCells.includes(key) : false;
  };

  const getTag = (r, c) => {
    const key = `${r},${c}`;
    if (cellTags instanceof Map) return cellTags.get(key);
    return cellTags[key];
  };

  const getBgColor = (tag) => {
    if (tag === 'queen') return C.queen;
    if (tag === 'attacked') return C.attacked;
    if (tag === 'path') return C.path;
    if (tag === 'max') return C.max;
    return '#ffffff';
  };

  const getBorderColor = (r, c, tag) => {
    if (isRead(r, c)) return C.read;
    if (tag === 'queen' || tag === 'path' || tag === 'max') return getBgColor(tag);
    return C.idle;
  };
  
  const getTextColor = (tag) => {
    if (tag === 'queen' || tag === 'path' || tag === 'max') return '#ffffff';
    return C.ink;
  };

  const CELL_SIZE = 44;
  const GAP = 4;

  const hasColLabels = labels?.col?.length > 0;
  const hasRowLabels = labels?.row?.length > 0;
  
  const gridRows = hasColLabels ? rows + 1 : rows;
  const gridCols = hasRowLabels ? cols + 1 : cols;

  return (
    <div className="flex flex-col items-center justify-center select-none overflow-auto w-full py-4 h-full">
      <div 
        className="grid"
        style={{ 
          gap: GAP,
          gridTemplateRows: `repeat(${gridRows}, ${CELL_SIZE}px)`,
          gridTemplateColumns: `repeat(${gridCols}, ${CELL_SIZE}px)` 
        }}
      >
        {/* Top-left empty cell if both labels exist */}
        {hasRowLabels && hasColLabels && <div />}
        
        {/* Column labels */}
        {hasColLabels && labels.col.map((lbl, c) => (
          <div key={`col-lbl-${c}`} className="flex items-center justify-center font-mono text-[13px] font-semibold text-[#94a3b8]">
            {lbl}
          </div>
        ))}

        {/* Rows */}
        {cells.map((row, r) => (
          <React.Fragment key={`row-${r}`}>
            {/* Row label */}
            {hasRowLabels && (
              <div className="flex items-center justify-center font-mono text-[13px] font-semibold text-[#94a3b8]">
                {labels.row[r]}
              </div>
            )}
            
            {/* Row cells */}
            {row.map((val, c) => {
              const tag = getTag(r, c);
              const read = isRead(r, c);
              const isQueen = tag === 'queen';
              const displayVal = isQueen ? '♛' : (val !== null && val !== undefined ? val : '');
              
              return (
                <div
                  key={`${r},${c}`}
                  className={`flex items-center justify-center font-mono text-[14px] font-bold rounded-md
                    ${read ? 'border-2 border-dashed' : 'border border-solid'}
                  `}
                  style={{
                    backgroundColor: getBgColor(tag),
                    borderColor: getBorderColor(r, c, tag),
                    color: getTextColor(tag),
                    width: CELL_SIZE,
                    height: CELL_SIZE,
                    transition: 'background-color 0.2s, border-color 0.2s',
                  }}
                >
                  <motion.span
                    key={`${displayVal}`}
                    initial={{ opacity: 0, scale: 0.5 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ type: 'spring', stiffness: 400, damping: 25 }}
                  >
                    {displayVal}
                  </motion.span>
                </div>
              );
            })}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
}
