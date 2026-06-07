import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { PlusSquare, Save, Activity, Clock, AlertTriangle, Layers, CheckCircle2 } from 'lucide-react';
import { apiFetch } from './lib/api';
import ComingSoon from './ComingSoon';

const SOURCE_TYPES = [
  { value: 'problem', label: 'Problem Solving' },
  { value: 'lecture', label: 'Lecture' },
  { value: 'video', label: 'Video' },
  { value: 'book', label: 'Book' },
  { value: 'article', label: 'Article' },
  { value: 'course', label: 'Course' },
  { value: 'project', label: 'Project' },
  { value: 'other', label: 'Other' },
];

function LogActivity() {
  const navigate = useNavigate();

  const [topic, setTopic] = useState('');
  const [sourceType, setSourceType] = useState('problem');
  const [keyMemory, setKeyMemory] = useState('');
  const [mistake, setMistake] = useState('');
  const [difficulty, setDifficulty] = useState(3);
  const [neededHint, setNeededHint] = useState(false);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [showFeedback, setShowFeedback] = useState(false);

  const canSubmit = topic.trim().length > 0 && keyMemory.trim().length > 0 && !submitting;

  const handleSubmit = async () => {
    if (!canSubmit) return;
    setSubmitting(true);
    setError(null);
    try {
      await apiFetch('/api/activities/', {
        method: 'POST',
        body: JSON.stringify({
          topic: topic.trim(),
          key_memory: keyMemory.trim(),
          mistake: mistake.trim() || null,
          difficulty,
          needed_hint: neededHint,
          source_type: sourceType,
        }),
      });
      navigate('/');
    } catch (err) {
      setError(err.message);
      setSubmitting(false);
    }
  };

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
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="e.g. Trees BFS, Fast.ai Chapter 4..."
            className="w-full px-4 py-3 bg-[rgba(15,23,42,0.02)] border border-[rgba(15,23,42,0.12)] rounded font-sans text-sm text-[#0F172A] focus:outline-none focus:border-[#0891B2] transition-colors placeholder-[#94a3b8]"
          />
        </div>

        {/* Source Type */}
        <div className="flex flex-col gap-2 max-w-xs">
          <label className="font-sans text-[11px] font-bold text-[#64748B] uppercase tracking-widest">
            Source Type
          </label>
          <div className="relative">
            <Layers size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#64748B]" />
            <select
              value={sourceType}
              onChange={(e) => setSourceType(e.target.value)}
              className="w-full pl-9 pr-4 py-3 bg-[rgba(15,23,42,0.02)] border border-[rgba(15,23,42,0.12)] rounded font-sans text-sm text-[#0F172A] focus:outline-none focus:border-[#0891B2] transition-colors appearance-none cursor-pointer"
            >
              {SOURCE_TYPES.map((s) => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
          </div>
        </div>

        {/* ROW 2: Key Memory */}
        <div className="flex flex-col gap-2 pt-6 border-t border-[rgba(15,23,42,0.08)]">
          <label className="font-sans text-[11px] font-bold text-[#0891B2] uppercase tracking-widest">
            Key Memory
          </label>
          <p className="font-sans text-xs text-[#64748B] mb-1">What is the single most important concept to retain from this session?</p>
          <textarea
            rows="2"
            value={keyMemory}
            onChange={(e) => setKeyMemory(e.target.value)}
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
              value={mistake}
              onChange={(e) => setMistake(e.target.value)}
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

        {/* ROW 4: Difficulty */}
        <div className="flex flex-col gap-3 pt-6 border-t border-[rgba(15,23,42,0.08)]">
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

      </div>

      {/* ROW 6: Schedule Preview & CTA */}
      <div className="flex flex-col md:flex-row justify-between items-center gap-6 mt-2">
        <div className="flex items-center gap-3">
          <Clock size={16} className="text-[#64748B]" />
          <div>
            <div className="font-sans text-[10px] font-bold text-[#64748B] uppercase tracking-widest">Projected Review Schedule</div>
            <div className="font-mono text-sm font-semibold text-[#0F172A] mt-0.5">
              Baseline review now, then spaced out as you recall it
            </div>
          </div>
        </div>

        <button
          onClick={handleSubmit}
          disabled={!canSubmit}
          className="kinetic-btn kinetic-accent-gradient w-full md:w-auto px-8 py-4 shadow-sm flex items-center justify-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <Save size={18} />
          {submitting ? 'Saving…' : 'Log & Schedule Review'}
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-2 text-[#ba1a1a] font-sans text-sm -mt-2">
          <AlertTriangle size={16} /> {error}
        </div>
      )}

      <ComingSoon
        id="log-track-roadmap"
        title="Track & Roadmap Linking"
        description="Link activities to learning tracks and roadmap nodes for structured progress."
        onFeedback={() => setShowFeedback(true)}
      />

      {showFeedback && <LogFeedbackModal onClose={() => setShowFeedback(false)} />}
    </div>
  );
}

function LogFeedbackModal({ onClose }) {
  const [msg, setMsg] = useState('');
  const [sending, setSending] = useState(false);
  const [done, setDone] = useState(false);

  const send = async () => {
    if (!msg.trim()) return;
    setSending(true);
    try {
      await apiFetch('/api/feedback/', {
        method: 'POST',
        body: JSON.stringify({ message: msg })
      });
      setDone(true);
      setTimeout(onClose, 2000);
    } catch (e) {
      alert("Failed to send feedback: " + e.message);
      setSending(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#131b2e]/40 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-[#f9f9f6] rounded-xl shadow-2xl w-full max-w-md overflow-hidden flex flex-col">
        <div className="p-4 border-b border-[rgba(15,23,42,0.08)] flex justify-between items-center bg-white">
          <h2 className="font-sans font-semibold text-[#0F172A]">Want this feature sooner?</h2>
          <button onClick={onClose} className="text-[#64748B] hover:text-[#0F172A] text-lg font-bold">✕</button>
        </div>
        <div className="p-4 bg-white flex flex-col gap-4">
          {done ? (
            <div className="text-center py-8 text-[#166534] font-medium flex flex-col items-center gap-2">
              <CheckCircle2 size={32} />
              Thanks for your feedback!
            </div>
          ) : (
            <>
              <textarea
                className="w-full border border-[rgba(15,23,42,0.12)] rounded p-3 text-sm focus:outline-none focus:border-[#0891B2] focus:ring-1 focus:ring-[#0891B2] min-h-[120px] resize-y font-sans text-[#0F172A]"
                placeholder="Tell us why this feature matters to you…"
                value={msg}
                onChange={e => setMsg(e.target.value)}
                autoFocus
              />
              <button
                onClick={send}
                disabled={sending || !msg.trim()}
                className="kinetic-btn kinetic-accent-gradient w-full py-2.5 disabled:opacity-50 flex items-center justify-center font-semibold"
              >
                {sending ? 'Sending...' : 'Send Feedback'}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default LogActivity;
