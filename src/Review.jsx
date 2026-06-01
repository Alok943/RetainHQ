import React, { useState } from 'react';
import { ArrowLeft, CheckCircle2, AlertTriangle, Eye, ArrowRight } from 'lucide-react';

function Review({ onBack }) {
  const [isFlipped, setIsFlipped] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(1);
  const totalReviews = 4;

  const handleConfidence = (level) => {
    if (currentIndex < totalReviews) {
      setCurrentIndex(prev => prev + 1);
      setIsFlipped(false);
    } else {
      onBack(); // Done with reviews
    }
  };

  return (
    <div className="flex flex-col h-full w-full max-w-3xl mx-auto p-4 md:p-8 bg-[#f9f9f6]">
      
      {/* Header & Progress */}
      <header className="flex flex-col gap-4 mb-8">
        <div className="flex items-center justify-between">
          <button 
            onClick={onBack}
            className="flex items-center gap-2 text-[#64748B] hover:text-[#0F172A] font-sans text-sm font-medium transition-colors"
          >
            <ArrowLeft size={16} /> Back to Dashboard
          </button>
          <div className="font-mono text-xs font-semibold text-[#0F172A]">
            {currentIndex} / {totalReviews}
          </div>
        </div>
        
        {/* Progress Bar */}
        <div className="w-full h-1 bg-[rgba(15,23,42,0.08)] rounded-full overflow-hidden">
          <div 
            className="h-full bg-[#0891B2] transition-all duration-300"
            style={{ width: `${(currentIndex / totalReviews) * 100}%` }}
          />
        </div>
      </header>

      {/* Main Review Card */}
      <main className="flex-1 flex flex-col justify-center gap-8 mb-8">
        <div className="kinetic-card min-h-[300px] flex flex-col items-center justify-center text-center px-6 md:px-12 py-12 relative shadow-sm border-[rgba(15,23,42,0.12)]">
          <div className="font-sans text-[11px] font-bold text-[#64748B] uppercase tracking-widest absolute top-6 left-6">
            Data Structures · Trees
          </div>
          
          {/* Question */}
          <h2 className="font-sans text-2xl md:text-3xl font-semibold text-[#0F172A] leading-tight mt-6">
            Explain the difference between Breadth-First Search (BFS) and Depth-First Search (DFS).
          </h2>

          {/* Answer (Only visible if flipped) */}
          {isFlipped && (
            <div className="mt-8 pt-8 border-t border-[rgba(15,23,42,0.08)] w-full text-left animate-in fade-in slide-in-from-bottom-2 duration-300">
              <div className="font-sans text-[11px] font-bold text-[#0891B2] uppercase tracking-widest mb-3 flex items-center gap-1">
                <CheckCircle2 size={12} /> Key Memory
              </div>
              <p className="font-sans text-base text-[#1a1c1b] leading-relaxed mb-6">
                <strong className="text-[#0F172A]">BFS</strong> explores level-by-level and uses a <code className="font-mono text-sm bg-[rgba(15,23,42,0.05)] px-1 py-0.5 rounded text-[#0F172A]">Queue</code> (FIFO).<br/><br/>
                <strong className="text-[#0F172A]">DFS</strong> explores as deep as possible before backtracking and uses a <code className="font-mono text-sm bg-[rgba(15,23,42,0.05)] px-1 py-0.5 rounded text-[#0F172A]">Stack</code> (LIFO) or recursion.
              </p>
              
              {/* Previous Mistake Block */}
              <div className="bg-[#ba1a1a]/5 border border-[#ba1a1a]/20 rounded p-4">
                <div className="font-sans text-[11px] font-bold text-[#ba1a1a] uppercase tracking-widest mb-1.5 flex items-center gap-1">
                  <AlertTriangle size={12} /> Previous Mistake
                </div>
                <p className="font-sans text-sm text-[#0F172A] italic">
                  "Confused BFS data structure; tried to use a Stack instead of a Queue."
                </p>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Controls */}
      <footer className="w-full flex justify-center pb-8">
        {!isFlipped ? (
          <button 
            onClick={() => setIsFlipped(true)}
            className="kinetic-btn kinetic-accent-gradient w-full md:w-auto md:min-w-[300px] py-4 text-base shadow-sm group"
          >
            <Eye size={18} className="mr-2 group-hover:scale-110 transition-transform" /> Show Answer
          </button>
        ) : (
          <div className="w-full flex flex-col items-center animate-in fade-in slide-in-from-bottom-4 duration-300">
            <h3 className="font-sans text-xs font-semibold text-[#64748B] uppercase tracking-widest mb-4">How well did you know this?</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 w-full">
              <button 
                onClick={() => handleConfidence('weak')}
                className="kinetic-btn bg-white border border-[#B91C1C] text-[#B91C1C] hover:bg-[#B91C1C] hover:text-white py-3 font-semibold text-sm transition-all group"
              >
                Weak
                <span className="block font-mono text-[10px] mt-0.5 font-normal opacity-80 group-hover:text-white/80">Soon</span>
              </button>
              
              <button 
                onClick={() => handleConfidence('developing')}
                className="kinetic-btn bg-white border border-[#B45309] text-[#B45309] hover:bg-[#B45309] hover:text-white py-3 font-semibold text-sm transition-all group"
              >
                Developing
                <span className="block font-mono text-[10px] mt-0.5 font-normal opacity-80 group-hover:text-white/80">Tomorrow</span>
              </button>
              
              <button 
                onClick={() => handleConfidence('strong')}
                className="kinetic-btn bg-white border border-[#0891B2] text-[#0891B2] hover:bg-[#0891B2] hover:text-white py-3 font-semibold text-sm transition-all group"
              >
                Strong
                <span className="block font-mono text-[10px] mt-0.5 font-normal opacity-80 group-hover:text-white/80">3 Days</span>
              </button>
              
              <button 
                onClick={() => handleConfidence('mastered')}
                className="kinetic-btn bg-white border border-[#0F766E] text-[#0F766E] hover:bg-[#0F766E] hover:text-white py-3 font-semibold text-sm transition-all group"
              >
                Mastered
                <span className="block font-mono text-[10px] mt-0.5 font-normal opacity-80 group-hover:text-white/80">7 Days</span>
              </button>
            </div>
          </div>
        )}
      </footer>

    </div>
  );
}

export default Review;
