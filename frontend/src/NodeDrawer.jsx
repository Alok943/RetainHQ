import React from 'react';
import { X, Play, Plus, BookOpen } from 'lucide-react';

function NodeDrawer({ node, onClose, onToggleStatus }) {
  if (!node) return null;

  const isDone = node.status === 'done';

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-[#131b2e]/20 backdrop-blur-sm z-40 transition-opacity"
        onClick={onClose}
      />
      
      {/* Drawer */}
      <div className="fixed top-0 right-0 h-full w-full sm:w-[400px] bg-white border-l border-[rgba(15,23,42,0.08)] shadow-2xl z-50 transform transition-transform duration-300 flex flex-col animate-in slide-in-from-right">
        
        {/* Header */}
        <div className="flex justify-between items-start p-6 border-b border-[rgba(15,23,42,0.08)] bg-[#f9f9f6]">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="font-mono text-[10px] font-bold uppercase tracking-widest px-1.5 py-0.5 rounded border bg-[#0F172A]/10 text-[#0F172A] border-[#0F172A]/20">
                {node.tier}
              </span>
              <span className={`font-sans text-xs font-semibold ${isDone ? 'text-[#0F766E]' : 'text-[#64748B]'}`}>
                {isDone ? 'COMPLETED' : 'PENDING'}
              </span>
            </div>
            <h2 className="font-sans text-xl font-semibold text-[#0F172A] leading-tight">
              {node.title}
            </h2>
          </div>
          <button 
            onClick={onClose}
            className="p-1 hover:bg-[rgba(15,23,42,0.05)] rounded transition-colors text-[#64748B]"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content Scrollable Area */}
        <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-8">
          
          <section>
            <h3 className="font-sans text-xs font-bold text-[#64748B] uppercase tracking-widest mb-2 flex items-center gap-1.5">
              <BookOpen size={14} className="text-[#0891B2]" /> Description
            </h3>
            <p className="font-sans text-sm text-[#0F172A] leading-relaxed">
              This is a placeholder description for {node.title}. In a fully fleshed out system, this would contain the core concepts, common interview questions, and key takeaways associated with this topic.
            </p>
          </section>

          <section>
            <h3 className="font-sans text-xs font-bold text-[#64748B] uppercase tracking-widest mb-2">
              What to Know
            </h3>
            <ul className="list-disc pl-4 flex flex-col gap-1 font-sans text-sm text-[#0F172A]">
              <li>Core syntax and usage patterns</li>
              <li>Time and space complexity</li>
              <li>Common edge cases to watch for</li>
              <li>Real-world production examples</li>
            </ul>
          </section>

        </div>

        {/* Footer Actions */}
        <div className="p-6 border-t border-[rgba(15,23,42,0.08)] bg-[#f9f9f6] flex flex-col gap-3">
          <button 
            className="kinetic-btn kinetic-accent-gradient w-full py-3 text-sm flex items-center justify-center gap-2 font-medium"
          >
            <Play size={16} /> Start Review Session
          </button>
          
          <div className="flex gap-3">
            <button 
              onClick={onToggleStatus}
              className={`flex-1 border text-sm font-medium py-2.5 rounded transition-colors flex justify-center items-center gap-2 ${
                isDone 
                  ? 'border-[rgba(15,23,42,0.1)] text-[#64748B] hover:bg-white' 
                  : 'bg-white border-[#0F172A] text-[#0F172A] hover:bg-slate-50'
              }`}
            >
              {isDone ? 'Mark as Pending' : 'Mark as Completed'}
            </button>
            <button className="px-4 border border-[rgba(15,23,42,0.1)] text-[#64748B] rounded hover:bg-white transition-colors flex justify-center items-center bg-transparent">
              <Plus size={18} />
            </button>
          </div>
        </div>

      </div>
    </>
  );
}

export default NodeDrawer;
