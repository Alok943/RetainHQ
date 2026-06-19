import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { PlusSquare, Save, Activity, Clock, AlertTriangle, Layers, CheckCircle2, Sparkles, Plus, Map } from 'lucide-react';
import { apiFetch } from './lib/api';
import { useAuth } from './lib/AuthContext';

const KEY_MEMORY_MAX = 500; // ~6 lines: one testable claim, not a paragraph dump

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
  const location = useLocation();

  const [topic, setTopic] = useState('');
  const [sourceType, setSourceType] = useState('problem');
  const [keyMemory, setKeyMemory] = useState('');
  const [mistake, setMistake] = useState('');
  const [difficulty, setDifficulty] = useState(3);
  const [neededHint, setNeededHint] = useState(false);
  const [roadmapId, setRoadmapId] = useState('');
  const [roadmaps, setRoadmaps] = useState([]);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [logged, setLogged] = useState(false);
  // Capture-assist (gated): suggested key points the user can recognize + insert.
  const [suggestions, setSuggestions] = useState([]);
  const [suggesting, setSuggesting] = useState(false);
  const [suggestError, setSuggestError] = useState(null);
  const [assistUnavailable, setAssistUnavailable] = useState(false); // 404 = grader off
  const { requireAuth } = useAuth();

  // Persist draft to localStorage so it survives an OAuth redirect
  useEffect(() => {
    const draft = localStorage.getItem('retainhq_log_draft');
    if (draft) {
      try {
        const parsed = JSON.parse(draft);
        if (parsed.topic) setTopic(parsed.topic);
        if (parsed.sourceType) setSourceType(parsed.sourceType);
        if (parsed.keyMemory) setKeyMemory(parsed.keyMemory);
        if (parsed.mistake) setMistake(parsed.mistake);
        if (parsed.difficulty) setDifficulty(parsed.difficulty);
        if (parsed.neededHint !== undefined) setNeededHint(parsed.neededHint);
        if (parsed.roadmapId) setRoadmapId(parsed.roadmapId);
      } catch (e) {}
    }
    // Arriving from a roadmap node ("Log what you learned") pre-fills the topic
    // (and roadmap, if the link passes one). Applied after the draft so an explicit
    // hand-off wins over a stale draft.
    const params = new URLSearchParams(location.search);
    const topicParam = params.get('topic');
    if (topicParam) setTopic(topicParam);
    const roadmapParam = params.get('roadmap_id');
    if (roadmapParam) setRoadmapId(roadmapParam);
  }, []);

  // Load roadmaps for the picker, in-progress ones first (less search friction).
  // optionalAuth so guests exploring the form still see the list. Failure is silent
  // — the picker just stays empty (it's an optional field).
  useEffect(() => {
    apiFetch('/api/roadmaps/', { optionalAuth: true })
      .then((data) => {
        const sorted = [...(data || [])].sort(
          (a, b) => (b.progress_pct || 0) - (a.progress_pct || 0)
        );
        setRoadmaps(sorted);
      })
      .catch(() => {});
  }, []);

  const startedRoadmaps = roadmaps.filter((r) => (r.progress_pct || 0) > 0);
  const otherRoadmaps = roadmaps.filter((r) => (r.progress_pct || 0) === 0);

  useEffect(() => {
    const draft = { topic, sourceType, keyMemory, mistake, difficulty, neededHint, roadmapId };
    localStorage.setItem('retainhq_log_draft', JSON.stringify(draft));
  }, [topic, sourceType, keyMemory, mistake, difficulty, neededHint, roadmapId]);

  const canSubmit = topic.trim().length > 0 && keyMemory.trim().length > 0 && !submitting;

  const resetForm = () => {
    setTopic('');
    setSourceType('problem');
    setKeyMemory('');
    setMistake('');
    setDifficulty(3);
    setNeededHint(false);
    setRoadmapId('');
    setError(null);
    setLogged(false);
    setSuggestions([]);
    setSuggestError(null);
  };

  // On-demand capture aid: ask the LLM for the core points under this topic. Fires
  // only when the user clicks (no cost/latency on every log). Suggestions are
  // recognition prompts — the user inserts what they actually learned, nothing is
  // auto-applied. Silently disables itself if the grader is off (404).
  const handleSuggest = async () => {
    if (!topic.trim() || suggesting) return;
    if (!requireAuth()) return; // guests get the sign-in modal, not a vague error
    setSuggesting(true);
    setSuggestError(null);
    try {
      const res = await apiFetch('/api/activities/suggest-key-points', {
        method: 'POST',
        body: JSON.stringify({ topic: topic.trim(), draft: keyMemory.trim() || null }),
      });
      setSuggestions(res?.points || []);
    } catch (err) {
      if (err.status === 404) setAssistUnavailable(true); // grader disabled
      else setSuggestError("Couldn't get suggestions — try again.");
    } finally {
      setSuggesting(false);
    }
  };

  // Append a recognized point as its own line, respecting the char cap, then drop
  // it from the list. The user stays the author — they choose what goes in.
  const insertPoint = (point) => {
    setKeyMemory((prev) => {
      const line = `• ${point}`;
      const next = prev.trim() ? `${prev.replace(/\s+$/, '')}\n${line}` : line;
      return next.length <= KEY_MEMORY_MAX ? next : prev; // skip if it wouldn't fit
    });
    setSuggestions((prev) => prev.filter((p) => p !== point));
  };

  const handleSubmit = async () => {
    if (!canSubmit) return;
    
    // Protect action: pops modal if not logged in
    const isAuthed = requireAuth();
    if (!isAuthed) return;

    setSubmitting(true);
    setError(null);
    try {
      const res = await apiFetch('/api/activities/', {
        method: 'POST',
        body: JSON.stringify({
          topic: topic.trim(),
          key_memory: keyMemory.trim(),
          mistake: mistake.trim() || null,
          difficulty,
          needed_hint: neededHint,
          source_type: sourceType,
          roadmap_id: roadmapId || null,
        }),
      });
      localStorage.removeItem('retainhq_log_draft');
      // A user's first-ever activity gets a demo review due now — send them
      // straight into it so they see the recall loop. Every later activity's
      // first review waits until tomorrow (recall after a delay builds memory),
      // so we confirm instead of dropping them into an empty queue.
      if (res?.review_due_now) {
        navigate('/reviews');
        return;
      }
      setLogged(true);
      setSubmitting(false);
    } catch (err) {
      setError(err.message);
      setSubmitting(false);
    }
  };

  if (logged) {
    return (
      <div className="flex flex-col items-center justify-center gap-5 p-8 max-w-md mx-auto w-full text-center min-h-[60vh] animate-in fade-in duration-300">
        <CheckCircle2 size={44} className="text-[#0F766E]" />
        <h2 className="font-sans text-2xl font-semibold text-[#0F172A]">Captured</h2>
        <p className="font-sans text-sm text-[#64748B] leading-relaxed">
          Your first review lands <span className="font-semibold text-[#0F172A]">tomorrow</span>.
          Recalling it after a day is what actually builds memory — quizzing you right now
          would only test short-term recall.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 w-full justify-center mt-2">
          <button
            onClick={resetForm}
            className="kinetic-btn bg-white border border-[rgba(15,23,42,0.15)] text-[#0F172A] px-6 py-3 text-sm font-medium"
          >
            Log another
          </button>
          <button
            onClick={() => navigate('/')}
            className="kinetic-btn kinetic-accent-gradient px-6 py-3 text-sm"
          >
            Back to home
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8 p-4 md:p-8 max-w-4xl mx-auto w-full pb-20 md:pb-8 animate-in fade-in duration-300">
      
      <header className="mb-2">
        <h2 className="font-sans text-2xl font-semibold text-[#0F172A] flex items-center gap-2">
          <PlusSquare size={24} className="text-[#0891B2]" /> Log Activity
        </h2>
        <p className="font-sans text-sm text-[#64748B] mt-1">Just learned something? Capture the one thing worth keeping — we'll test you on it later.</p>
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

        {/* Source Type + Roadmap (both optional metadata) */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="flex flex-col gap-2">
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

          {/* Roadmap link — in-progress roadmaps surfaced first to cut search friction */}
          <div className="flex flex-col gap-2">
            <label className="font-sans text-[11px] font-bold text-[#64748B] uppercase tracking-widest flex items-center gap-2">
              Roadmap
              <span className="bg-[rgba(15,23,42,0.05)] text-[#64748B] px-1.5 py-0.5 rounded font-mono text-[9px] tracking-normal">OPTIONAL</span>
            </label>
            <div className="relative">
              <Map size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#64748B]" />
              <select
                value={roadmapId}
                onChange={(e) => setRoadmapId(e.target.value)}
                className="w-full pl-9 pr-4 py-3 bg-[rgba(15,23,42,0.02)] border border-[rgba(15,23,42,0.12)] rounded font-sans text-sm text-[#0F172A] focus:outline-none focus:border-[#0891B2] transition-colors appearance-none cursor-pointer"
              >
                <option value="">No roadmap</option>
                {startedRoadmaps.length > 0 && (
                  <optgroup label="In progress">
                    {startedRoadmaps.map((r) => (
                      <option key={r.id} value={r.id}>{r.title} · {r.progress_pct}%</option>
                    ))}
                  </optgroup>
                )}
                <optgroup label={startedRoadmaps.length > 0 ? 'All roadmaps' : 'Roadmaps'}>
                  {otherRoadmaps.map((r) => (
                    <option key={r.id} value={r.id}>{r.title}</option>
                  ))}
                </optgroup>
              </select>
            </div>
          </div>
        </div>

        {/* ROW 2: Key Memory */}
        <div className="flex flex-col gap-2 pt-6 border-t border-[rgba(15,23,42,0.08)]">
          <label className="font-sans text-[11px] font-bold text-[#0891B2] uppercase tracking-widest">
            Key Memory
          </label>
          <p className="font-sans text-xs text-[#64748B] mb-1">The one thing you want to still remember a month from now.</p>
          <textarea
            rows="2"
            value={keyMemory}
            maxLength={KEY_MEMORY_MAX}
            onChange={(e) => setKeyMemory(e.target.value)}
            placeholder="Write a concise, testable statement..."
            className="w-full px-4 py-3 bg-[rgba(15,23,42,0.02)] border border-[rgba(15,23,42,0.12)] rounded font-sans text-sm text-[#0F172A] focus:outline-none focus:border-[#0891B2] transition-colors resize-none placeholder-[#94a3b8]"
          ></textarea>

          {/* Char counter + on-demand "suggest key points" assist (hidden if grader off) */}
          <div className="flex items-center justify-between gap-3 flex-wrap">
            {!assistUnavailable ? (
              <button
                type="button"
                onClick={handleSuggest}
                disabled={!topic.trim() || suggesting}
                title={!topic.trim() ? 'Add a topic first' : 'Suggest the core points under this topic'}
                className="flex items-center gap-1.5 font-sans text-xs font-semibold text-[#8B5CF6] hover:text-[#7c3aed] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                <Sparkles size={13} /> {suggesting ? 'Thinking…' : "Stuck? Suggest key points"}
              </button>
            ) : <span />}
            <span className={`font-mono text-[11px] ${keyMemory.length >= KEY_MEMORY_MAX ? 'text-[#B45309]' : 'text-[#94a3b8]'}`}>
              {keyMemory.length}/{KEY_MEMORY_MAX}
            </span>
          </div>

          {suggestError && (
            <p className="font-sans text-xs text-[#B45309]">{suggestError}</p>
          )}

          {/* Recognition, not instruction: keep what you actually learned, ignore the rest. */}
          {suggestions.length > 0 && (
            <div className="mt-1 rounded-lg border border-[#8B5CF6]/25 bg-[#8B5CF6]/[0.05] p-3 flex flex-col gap-2">
              <p className="font-sans text-[11px] text-[#64748B]">
                Key points often under this topic — tap to add the ones <span className="italic">you</span> learned, ignore the rest.
              </p>
              <div className="flex flex-wrap gap-2">
                {suggestions.map((p, i) => (
                  <button
                    key={i}
                    type="button"
                    onClick={() => insertPoint(p)}
                    className="group flex items-start gap-1.5 text-left rounded-md border border-[#8B5CF6]/30 bg-white px-2.5 py-1.5 font-sans text-xs text-[#0F172A] hover:border-[#8B5CF6] hover:bg-[#8B5CF6]/[0.06] transition-colors"
                  >
                    <Plus size={12} className="mt-0.5 shrink-0 text-[#8B5CF6]" />
                    <span>{p}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
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
              First review tomorrow, then spaced out as you recall it
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
    </div>
  );
}

export default LogActivity;
