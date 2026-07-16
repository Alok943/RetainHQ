import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { School, Eye, EyeOff, ArrowRight, CheckCircle2 } from 'lucide-react';
import { apiFetch } from './lib/api';
import { useAuth } from './lib/AuthContext';

/**
 * JoinClassroom — /join/:code. Fetches nothing until submit (spec §7): the
 * consent list (teacher_sees / teacher_never_sees) is static copy mirrored
 * from JoinResponse's defaults (schemas/classroom.py), not a pre-fetch, so a
 * student sees exactly what they're agreeing to before any account/network
 * activity happens. Reachable signed-out (App.jsx mounts it outside the authed
 * shell) since Class 9-10 students may follow the code before ever signing in.
 */
const TEACHER_SEES = [
  'The name you type below (not your Google name)',
  'When you log activities and complete reviews',
  'Your review counts and outcomes (recalled / missed)',
  'Computed mastery per topic, from your test scores and reviews',
  'Test scores and per-question outcomes',
  'Your current streak',
];

const TEACHER_NEVER_SEES = [
  'Your private notes, key memories, or mistake text',
  'Your free-recall answer text',
  'AI feedback text',
  'Your email or Google identity',
  'Anything from roadmaps not assigned to this class (your other subjects, career prep, etc.)',
];

function JoinClassroom() {
  const { code } = useParams();
  const navigate = useNavigate();
  const { session, showAuthModal } = useAuth();

  const [displayName, setDisplayName] = useState('');
  const [confirmed, setConfirmed] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null); // JoinResponse on success

  const submit = async (e) => {
    e.preventDefault();
    if (!session) { showAuthModal(); return; }
    if (!displayName.trim() || !confirmed || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      const res = await apiFetch('/api/classrooms/join', {
        method: 'POST',
        body: JSON.stringify({ code: code.trim(), display_name: displayName.trim() }),
      });
      setResult(res);
    } catch (e2) {
      setError(e2.status === 404 ? "That class code doesn't look right — check it with your teacher." : e2.message);
    } finally {
      setSubmitting(false);
    }
  };

  if (result) {
    return (
      <div className="min-h-screen bg-[#f9f9f6] flex items-center justify-center p-4">
        <div className="kinetic-card bg-white p-8 w-full max-w-md flex flex-col items-center text-center gap-4">
          <div className="w-14 h-14 rounded-full bg-[#0F766E]/10 flex items-center justify-center text-[#0F766E]">
            <CheckCircle2 size={28} />
          </div>
          <div>
            <h2 className="font-sans text-xl font-semibold text-[#0F172A]">You're in — {result.classroom_name}</h2>
            {result.school_name && <p className="font-sans text-sm text-[#64748B] mt-1">{result.school_name}</p>}
            <p className="font-sans text-sm text-[#64748B] mt-2">
              Joined as <span className="font-semibold text-[#0F172A]">"{result.display_name}"</span>. Keep using RetainHQ as normal —
              your teacher now sees your progress on this class's subjects.
            </p>
          </div>
          <button
            onClick={() => navigate('/dashboard')}
            className="kinetic-btn kinetic-accent-gradient px-5 py-2.5 text-sm w-full"
          >
            Go to your dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f9f9f6] flex items-center justify-center p-4 py-10">
      <div className="kinetic-card bg-white p-6 md:p-8 w-full max-w-lg flex flex-col gap-6">
        <header className="flex flex-col items-center text-center gap-2">
          <div className="w-12 h-12 rounded-full bg-[#0891B2]/10 flex items-center justify-center text-[#0891B2]">
            <School size={22} />
          </div>
          <h2 className="font-sans text-xl font-semibold text-[#0F172A]">Join a class</h2>
          <p className="font-mono text-sm font-semibold tracking-widest text-[#64748B]">{code?.toUpperCase()}</p>
        </header>

        {/* Consent — read before anything is sent (spec §5) */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <ConsentList
            icon={<Eye size={14} />}
            color="#0891B2"
            title="Your teacher WILL see"
            items={TEACHER_SEES}
          />
          <ConsentList
            icon={<EyeOff size={14} />}
            color="#B91C1C"
            title="Your teacher will NEVER see"
            items={TEACHER_NEVER_SEES}
          />
        </div>

        <form onSubmit={submit} className="flex flex-col gap-4">
          <label className="flex flex-col gap-1.5">
            <span className="font-sans text-xs font-semibold text-[#64748B]">Your name (as your teacher should see it)</span>
            <input
              autoFocus
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              maxLength={120}
              placeholder="e.g. Priya Sharma, Roll 14"
              className="px-3 py-2.5 rounded-lg border border-[rgba(15,23,42,0.12)] font-sans text-sm text-[#0F172A] focus:outline-none focus:border-[#0891B2] focus:ring-2 focus:ring-[#0891B2]/20"
            />
          </label>

          <label className="flex items-start gap-2.5 cursor-pointer">
            <input
              type="checkbox"
              checked={confirmed}
              onChange={(e) => setConfirmed(e.target.checked)}
              className="mt-0.5 w-4 h-4 accent-[#0891B2] shrink-0"
            />
            <span className="font-sans text-xs text-[#64748B] leading-relaxed">
              I understand what my teacher will and won't see, and I want to join this class. I can leave any time from my Profile.
            </span>
          </label>

          {error && <p className="font-sans text-xs text-[#ba1a1a]">{error}</p>}

          {!session ? (
            <button
              type="button"
              onClick={showAuthModal}
              className="kinetic-btn kinetic-accent-gradient py-2.5 text-sm"
            >
              Sign in to continue
            </button>
          ) : (
            <button
              type="submit"
              disabled={!displayName.trim() || !confirmed || submitting}
              className="kinetic-btn kinetic-accent-gradient py-2.5 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? 'Joining…' : <>Join class <ArrowRight size={15} /></>}
            </button>
          )}
        </form>
      </div>
    </div>
  );
}

function ConsentList({ icon, color, title, items }) {
  return (
    <div className="rounded-xl p-4 border" style={{ backgroundColor: `${color}0d`, borderColor: `${color}33` }}>
      <div className="flex items-center gap-1.5 mb-2.5" style={{ color }}>
        {icon}
        <span className="font-sans text-[11px] font-bold uppercase tracking-wide">{title}</span>
      </div>
      <ul className="flex flex-col gap-1.5">
        {items.map((item) => (
          <li key={item} className="font-sans text-xs text-[#0F172A] leading-snug flex gap-1.5">
            <span className="shrink-0" style={{ color }}>·</span> {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default JoinClassroom;
