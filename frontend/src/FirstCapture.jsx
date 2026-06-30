import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, AlertTriangle, CalendarDays } from 'lucide-react';
import { apiFetch } from './lib/api';
import { useAuth } from './lib/AuthContext';
import RoadmapMini from './RoadmapMini';
import ReviewHeatmap from './ReviewHeatmap';

// Example topics for someone who blanks on the empty form. Clicking one drops it
// into Topic and moves the cursor to the memory — it's a prompt, not a prefill.
const EXAMPLES = ['Binary search', 'TCP handshake', 'SQL joins', 'Big-O of quicksort'];

// Full-screen first-capture gate. Shown instead of the dashboard when a signed-in
// user has zero activities — the post-login leak our funnel shows is right here, so
// we give them exactly one thing to do: capture a memory, then go straight into the
// one-time demo review (the actual aha moment). Because this gate only renders for a
// zero-activity user, the activity logged here is always their first — the backend
// schedules its review due now, so /reviews has a card waiting. (Second and later
// activities, logged from the normal Log page, defer their first review to tomorrow.)
export default function FirstCapture({ onSkip }) {
  const navigate = useNavigate();
  const { requireAuth } = useAuth();
  const memoryRef = useRef(null);

  const [topic, setTopic] = useState('');
  const [keyMemory, setKeyMemory] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [roadmaps, setRoadmaps] = useState([]);

  // A few roadmaps to explore — gives a brand-new user a path beyond the empty form.
  useEffect(() => {
    apiFetch('/api/roadmaps/', { optionalAuth: true })
      .then((d) => setRoadmaps(Array.isArray(d) ? d : []))
      .catch(() => {});
  }, []);

  const canSubmit = topic.trim().length > 0 && keyMemory.trim().length > 0 && !submitting;

  const pickExample = (ex) => {
    setTopic(ex);
    memoryRef.current?.focus();
  };

  const handleSubmit = async () => {
    if (!canSubmit) return;
    if (!requireAuth()) return;

    setSubmitting(true);
    setError(null);
    try {
      await apiFetch('/api/activities/', {
        method: 'POST',
        body: JSON.stringify({
          topic: topic.trim(),
          key_memory: keyMemory.trim(),
          difficulty: 3,
          needed_hint: false,
        }),
      });
      // First-ever activity: the backend scheduled its review due now. Drop them
      // straight into that one-time demo review — the activation aha moment.
      navigate('/reviews');
    } catch (err) {
      setError(err.message);
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-full flex flex-col items-center justify-start p-4 md:p-8 animate-in fade-in duration-300">
      <div className="w-full max-w-lg flex flex-col gap-6">
        <div>
          <h1 className="font-sans text-2xl md:text-3xl font-semibold text-[#0F172A] leading-tight">
            What's one thing you learned recently?
          </h1>
          <p className="font-sans text-sm text-[#64748B] mt-2 leading-relaxed">
            Capture it as a short memory. We'll test your recall right now, then bring it back
            for review just before you'd forget — so it actually sticks.
          </p>
        </div>

        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            <label className="font-sans text-sm font-medium text-[#0F172A]">Topic</label>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="What was it about?"
              className="w-full px-4 py-3 bg-white border border-[rgba(15,23,42,0.12)] rounded-lg font-sans text-sm text-[#0F172A] focus:outline-none focus:border-[#0891B2] transition-colors placeholder-[#94a3b8]"
              autoFocus
            />
            <div className="flex flex-wrap gap-2 mt-1">
              {EXAMPLES.map((ex) => (
                <button
                  key={ex}
                  type="button"
                  onClick={() => pickExample(ex)}
                  className="font-sans text-xs text-[#64748B] bg-[rgba(15,23,42,0.04)] hover:bg-[rgba(15,23,42,0.08)] hover:text-[#0F172A] px-3 py-1.5 rounded-full transition-colors"
                >
                  {ex}
                </button>
              ))}
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <label className="font-sans text-sm font-medium text-[#0F172A]">
              The one thing to remember
            </label>
            <textarea
              ref={memoryRef}
              rows="3"
              value={keyMemory}
              onChange={(e) => setKeyMemory(e.target.value)}
              placeholder="Write it in your own words — the thing you'd want to still know a month from now."
              className="w-full px-4 py-3 bg-white border border-[rgba(15,23,42,0.12)] rounded-lg font-sans text-sm text-[#0F172A] focus:outline-none focus:border-[#0891B2] transition-colors resize-none placeholder-[#94a3b8]"
            />
          </div>
        </div>

        {error && (
          <div className="flex items-center gap-2 text-[#ba1a1a] font-sans text-sm">
            <AlertTriangle size={16} /> {error}
          </div>
        )}

        <div className="flex flex-col gap-3">
          <button
            onClick={handleSubmit}
            disabled={!canSubmit}
            className="kinetic-btn kinetic-accent-gradient w-full py-3.5 flex items-center justify-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {submitting ? 'Saving…' : 'Capture & review it now'}
            {!submitting && <ArrowRight size={16} />}
          </button>
          <button
            onClick={onSkip}
            className="font-sans text-sm text-[#64748B] hover:text-[#0F172A] transition-colors self-center"
          >
            I'll look around first
          </button>
        </div>

        {/* Explore a roadmap — a path for a new user who isn't ready to capture yet. */}
        {roadmaps.length > 0 && (
          <div className="border-t border-[rgba(15,23,42,0.08)] pt-6 flex flex-col gap-3">
            <p className="font-sans text-sm font-semibold text-[#0F172A]">Or start with a roadmap</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {roadmaps.slice(0, 4).map((rm) => (
                <RoadmapMini key={rm.id} rm={rm} onClick={() => navigate(`/roadmaps/${rm.slug || rm.id}`)} />
              ))}
            </div>
          </div>
        )}

        {/* Review calendar — previews the retention loop (empty until reviews happen). */}
        <div className="border-t border-[rgba(15,23,42,0.08)] pt-6 flex flex-col gap-3">
          <p className="font-sans text-sm font-semibold text-[#0F172A] flex items-center gap-1.5">
            <CalendarDays size={15} className="text-[#0891B2]" /> Your review calendar
          </p>
          <ReviewHeatmap />
        </div>
      </div>
    </div>
  );
}
