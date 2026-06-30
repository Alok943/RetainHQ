import React from 'react';
import { ArrowRight } from 'lucide-react';
import { getRoadmapStyle, RoadmapLogo } from './lib/roadmapVisuals';

// Compact roadmap card (logo + title + progress) used on Home's "Continue learning"
// row and on the new-user FirstCapture screen. Shared so both stay in sync.
export default function RoadmapMini({ rm, onClick }) {
  const { Icon, accent } = getRoadmapStyle(rm.title);
  const pct = rm.progress_pct ?? 0;
  return (
    <button
      onClick={onClick}
      className="kinetic-card bg-white p-4 flex items-center gap-3 text-left hover:-translate-y-0.5 transition-transform group"
    >
      <div
        className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
        style={{ backgroundColor: `${accent}14`, border: `1px solid ${accent}26` }}
      >
        <RoadmapLogo title={rm.title} Icon={Icon} accent={accent} size={20} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2">
          <h3 className="font-sans text-sm font-semibold text-[#0F172A] truncate">{rm.title}</h3>
          <span className="font-mono text-xs font-semibold shrink-0" style={{ color: accent }}>{pct}%</span>
        </div>
        <div className="w-full h-1.5 rounded-full bg-[rgba(15,23,42,0.06)] overflow-hidden mt-2">
          <div className="h-full rounded-full transition-all duration-700" style={{ width: `${pct}%`, backgroundColor: accent }} />
        </div>
      </div>
      <ArrowRight size={15} className="text-[#94a3b8] shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" />
    </button>
  );
}
