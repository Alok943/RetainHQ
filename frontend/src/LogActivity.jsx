import React, { useState } from 'react';
import { PlusSquare, Save, Tag, Target, Map, Activity, CheckSquare, Clock } from 'lucide-react';

function LogActivity() {
  const [confidence, setConfidence] = useState('developing');
  const [difficulty, setDifficulty] = useState(3);
  const [activityType, setActivityType] = useState('problem');
  const [neededHint, setNeededHint] = useState(false);

  return (
    <div className="flex flex-col gap-8 p-4 md:p-8 max-w-4xl mx-auto w-full pb-20 md:pb-8 animate-in fade-in duration-300">
      
      <header className="mb-2">
        <h2 className="font-sans text-2xl font-semibold text-[#0F172A] flex items-center gap-2">
          <PlusSquare size={24} className="text-[#0891B2]" /> Log Activity
        </h2>
        <p className="font-sans text-sm text-[#64748B] mt-1">Record a new learning session and initiate the spaced repetition sequence.</p>
      </header>

      <div className="kinetic-card flex flex-col gap-8 bg-white border-[rgba(15,23,42,0.12)]">
        
        {/* ROW 1: Title Input */}
        <div className="flex flex-col gap-2">
          <label className="font-sans text-[11px] font-bold text-[#64748B] uppercase tracking-widest">
            Topic / Resource Name
          </label>
          <input 
            type="text" 
            placeholder="e.g. Trees BFS, Fast.ai Chapter 4..." 
            className="w-full px-4 py-3 bg-[rgba(15,23,42,0.02)] border border-[rgba(15,23,42,0.12)] rounded font-sans text-sm text-[#0F172A] focus:outline-none focus:border-[#0891B2] transition-colors placeholder-[#94a3b8]"
          />
        </div>

        {/* ROW 2: Track, Roadmap, Activity Type */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Track */}
          <div className="flex-col gap-2 flex">
            <label className="font-sans text-[11px] font-bold text-[#64748B] uppercase tracking-widest">
              Track
            </label>
            <div className="relative">
              <Target size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#64748B]" />
              <select className="w-full pl-9 pr-4 py-3 bg-[rgba(15,23,42,0.02)] border border-[rgba(15,23,42,0.12)] rounded font-sans text-sm text-[#0F172A] focus:outline-none focus:border-[#0891B2] transition-colors appearance-none cursor-pointer">
                <option>Placement Prep 2026</option>
                <option>Personal Dev</option>
              </select>
            </div>
          </div>
          
          {/* Roadmap */}
          <div className="flex-col gap-2 flex">
            <label className="font-sans text-[11px] font-bold text-[#64748B] uppercase tracking-widest">
              Roadmap
            </label>
            <div className="relative">
              <Map size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#64748B]" />
              <select className="w-full pl-9 pr-4 py-3 bg-[rgba(15,23,42,0.02)] border border-[rgba(15,23,42,0.12)] rounded font-sans text-sm text-[#0F172A] focus:outline-none focus:border-[#0891B2] transition-colors appearance-none cursor-pointer">
                <option>NeetCode 150</option>
                <option>System Design Primer</option>
                <option>None</option>
              </select>
            </div>
          </div>

          {/* Activity Type */}
          <div className="flex-col gap-2 flex">
            <label className="font-sans text-[11px] font-bold text-[#64748B] uppercase tracking-widest">
              Activity Type
            </label>
            <div className="relative">
              <Activity size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#64748B]" />
              <select 
                value={activityType}
                onChange={(e) => setActivityType(e.target.value)}
                className="w-full pl-9 pr-4 py-3 bg-[rgba(15,23,42,0.02)] border border-[rgba(15,23,42,0.12)] rounded font-sans text-sm text-[#0F172A] focus:outline-none focus:border-[#0891B2] transition-colors appearance-none cursor-pointer"
              >
                <option value="problem">Problem Solving</option>
                <option value="reading">Reading</option>
                <option value="lecture">Lecture</option>
                <option value="revision">Revision</option>
                <option value="project">Project</option>
              </select>
            </div>
          </div>
        </div>

        {/* ROW 3: Key Memory */}
        <div className="flex flex-col gap-2 pt-6 border-t border-[rgba(15,23,42,0.08)]">
          <label className="font-sans text-[11px] font-bold text-[#0891B2] uppercase tracking-widest">
            Key Memory
          </label>
          <p className="font-sans text-xs text-[#64748B] mb-1">What is the single most important concept to retain from this session?</p>
          <textarea 
            rows="2"
            placeholder="Write a concise, testable statement..." 
            className="w-full px-4 py-3 bg-[rgba(15,23,42,0.02)] border border-[rgba(15,23,42,0.12)] rounded font-sans text-sm text-[#0F172A] focus:outline-none focus:border-[#0891B2] transition-colors resize-none placeholder-[#94a3b8]"
          ></textarea>
        </div>

        {/* ROW 4: Mistake Made & Hints */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="flex flex-col gap-2">
            <label className="font-sans text-[11px] font-bold text-[#64748B] uppercase tracking-widest flex items-center gap-2">
              Mistake Made 
              <span className="bg-[rgba(15,23,42,0.05)] text-[#64748B] px-1.5 py-0.5 rounded font-mono text-[9px] tracking-normal">OPTIONAL</span>
            </label>
            <textarea 
              rows="2"
              placeholder="What did you get wrong? (e.g. Confused BFS with DFS queue logic)" 
              className="w-full px-4 py-3 bg-[rgba(15,23,42,0.02)] border border-[rgba(15,23,42,0.12)] rounded font-sans text-sm text-[#0F172A] focus:outline-none focus:border-[#0891B2] transition-colors resize-none placeholder-[#94a3b8]"
            ></textarea>
          </div>

          <div className="flex flex-col gap-4 justify-center pl-0 md:pl-4">
            <div className="flex items-center gap-3">
              <input 
                type="checkbox" 
                id="neededHint" 
                checked={neededHint} 
                onChange={() => setNeededHint(!neededHint)}
                className="w-4 h-4 accent-[#0891B2] cursor-pointer" 
              />
              <label htmlFor="neededHint" className="font-sans text-sm font-semibold text-[#0F172A] cursor-pointer">
                I needed a hint to complete this
              </label>
            </div>
          </div>
        </div>

        {/* ROW 5: Difficulty & Retention Strength */}
        <div className="flex flex-col md:flex-row gap-8 pt-6 border-t border-[rgba(15,23,42,0.08)]">
          
          <div className="flex-1 flex flex-col gap-3">
            <label className="font-sans text-[11px] font-bold text-[#64748B] uppercase tracking-widest flex items-center gap-1.5">
              <Activity size={14} /> Session Difficulty (1-5)
            </label>
            <p className="font-sans text-xs text-[#64748B] mb-1">How hard was it to get through this material?</p>
            <div className="flex gap-2">
              {[1, 2, 3, 4, 5].map(num => (
                <button 
                  key={num}
                  onClick={() => setDifficulty(num)}
                  className={`w-10 h-10 rounded border font-mono text-sm transition-colors ${
                    difficulty === num 
                      ? 'bg-[#0F172A] border-[#0F172A] text-white' 
                      : 'bg-[rgba(15,23,42,0.02)] border-[rgba(15,23,42,0.12)] text-[#0F172A] hover:bg-white hover:border-[#0F172A]'
                  }`}
                >
                  {num}
                </button>
              ))}
            </div>
          </div>

          <div className="flex-1 flex flex-col gap-3">
            <label className="font-sans text-[11px] font-bold text-[#64748B] uppercase tracking-widest flex items-center gap-1.5">
              <CheckSquare size={14} /> Initial Retention Strength
            </label>
            <p className="font-sans text-xs text-[#64748B] mb-1">How well do you know it right now?</p>
            <div className="grid grid-cols-4 gap-2">
              <ConfidenceToggle label="Weak" color="#B91C1C" selected={confidence === 'weak'} onClick={() => setConfidence('weak')} />
              <ConfidenceToggle label="Developing" color="#B45309" selected={confidence === 'developing'} onClick={() => setConfidence('developing')} />
              <ConfidenceToggle label="Strong" color="#0891B2" selected={confidence === 'strong'} onClick={() => setConfidence('strong')} />
              <ConfidenceToggle label="Mastered" color="#0F766E" selected={confidence === 'mastered'} onClick={() => setConfidence('mastered')} />
            </div>
          </div>
        </div>

      </div>

      {/* ROW 6: Schedule Preview & CTA */}
      <div className="flex flex-col md:flex-row justify-between items-center gap-6 mt-2">
        <div className="flex items-center gap-3">
          <Clock size={16} className="text-[#64748B]" />
          <div>
            <div className="font-sans text-[10px] font-bold text-[#64748B] uppercase tracking-widest">Projected Review Schedule</div>
            <div className="font-mono text-sm font-semibold text-[#0F172A] mt-0.5">
              Day 3 · Day 7 · Day 14 · Day 30
            </div>
          </div>
        </div>

        <button className="kinetic-btn kinetic-accent-gradient w-full md:w-auto px-8 py-4 shadow-sm flex items-center justify-center gap-2">
          <Save size={18} />
          Log & Schedule Review
        </button>
      </div>

    </div>
  );
}

function TypePill({ label, selected, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`flex-1 py-1.5 text-xs font-semibold rounded transition-colors ${
        selected ? 'bg-white shadow-sm text-[#0F172A] border border-[rgba(15,23,42,0.08)]' : 'text-[#64748B] hover:text-[#0F172A]'
      }`}
    >
      {label}
    </button>
  );
}

function ConfidenceToggle({ label, color, selected, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`py-2 px-2 border rounded font-semibold text-xs transition-all group ${
        selected ? '' : 'bg-white'
      }`}
      style={{
        borderColor: selected ? color : 'rgba(15,23,42,0.12)',
        backgroundColor: selected ? color : 'white',
        color: selected ? '#fff' : color
      }}
    >
      {label}
    </button>
  );
}

export default LogActivity;
