import React, { useState } from 'react';
import { Puzzle, X } from 'lucide-react';
import { Link } from 'react-router-dom';

function CompanionInstallBanner() {
  return (
    <div className="fixed bottom-24 right-6 z-40 w-72 rounded-lg border border-[#0891B2]/25 bg-white p-4 flex items-start gap-3 shadow-xl">
      <div className="w-8 h-8 rounded-full bg-[#0891B2]/10 flex items-center justify-center text-[#0891B2] shrink-0">
        <Puzzle size={15} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-sans text-sm font-semibold text-[#0F172A]">
          Install Companion
        </p>
        <p className="font-sans text-xs text-[#64748B] mt-0.5 mb-2.5">
          Auto-tracks LeetCode, YouTube, and course time.
        </p>
        <Link
          to="/privacy/companion"
          className="font-sans text-xs font-semibold text-[#0891B2] hover:text-[#0e7490]"
        >
          Get the extension
        </Link>
      </div>
    </div>
  );
}

export default CompanionInstallBanner;
