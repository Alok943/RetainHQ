import React from 'react';
import { Puzzle } from 'lucide-react';
import { Link } from 'react-router-dom';

function CompanionInstallBanner() {
  return (
    <div className="rounded-lg border border-[#0891B2]/25 bg-[#0891B2]/[0.05] p-4 flex items-center gap-3">
      <div className="w-8 h-8 rounded-full bg-[#0891B2]/10 flex items-center justify-center text-[#0891B2] shrink-0">
        <Puzzle size={15} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-sans text-sm font-semibold text-[#0F172A]">
          Install Companion
        </p>
        <p className="font-sans text-xs text-[#64748B] mt-0.5">
          Auto-tracks LeetCode, YouTube, and course time.
        </p>
      </div>
      <Link
        to="/privacy/companion"
        className="shrink-0 font-sans text-xs font-semibold text-[#0891B2] hover:text-[#0e7490] whitespace-nowrap"
      >
        Get the extension
      </Link>
    </div>
  );
}

export default CompanionInstallBanner;
