import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Presentation, Plus, Users, Copy, LogIn, X } from 'lucide-react';
import { apiFetch } from './lib/api';
import { useAuth } from './lib/AuthContext';
import { useToast } from './lib/ToastContext';

/**
 * Teach — /teach. Class list: classrooms the caller teaches (with a create
 * form) plus classrooms they've joined as a student (SPEC-teacher-dashboard.md
 * §7). "Teacher" isn't a role — any signed-in user can create a classroom
 * (spec §1/§2 notes) — so this page has no gate beyond being signed in.
 */
function Teach() {
  const { session, showAuthModal } = useAuth();
  const navigate = useNavigate();
  const toast = useToast();

  const [data, setData] = useState(null); // { teaching, enrolled }
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreate, setShowCreate] = useState(false);

  const load = () => {
    if (!session) { setLoading(false); return; }
    setLoading(true);
    apiFetch('/api/classrooms/mine')
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(load, [session]);

  const handleLeave = async (classroomId, name) => {
    if (!window.confirm(`Leave "${name}"? Your teacher loses visibility into your progress immediately — nothing else changes.`)) return;
    try {
      await apiFetch(`/api/classrooms/${classroomId}/membership`, { method: 'DELETE' });
      toast.success(`Left ${name}.`);
      load();
    } catch {
      // apiFetch already toasts server-side failures
    }
  };

  if (!session) {
    return (
      <div className="max-w-4xl mx-auto w-full p-4 md:p-8 pb-20 md:pb-8">
        <TeachHeader />
        <div className="kinetic-card bg-white p-8 flex flex-col items-center text-center gap-3 mt-6">
          <div className="w-11 h-11 rounded-full bg-[#0891B2]/10 flex items-center justify-center text-[#0891B2]">
            <LogIn size={20} />
          </div>
          <p className="font-sans text-sm text-[#64748B] max-w-sm">
            Sign in to create a classroom or see the ones you've joined.
          </p>
          <button onClick={showAuthModal} className="kinetic-btn kinetic-accent-gradient px-5 py-2 text-sm">
            Sign In
          </button>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto w-full p-4 md:p-8 pb-20 md:pb-8 flex flex-col gap-4">
        <div className="skeleton h-7 w-40" />
        <div className="skeleton h-4 w-72" />
        <div className="skeleton h-28 w-full rounded-xl mt-2" />
        <div className="skeleton h-28 w-full rounded-xl" />
      </div>
    );
  }

  const teaching = data?.teaching || [];
  const enrolled = data?.enrolled || [];

  return (
    <div className="max-w-4xl mx-auto w-full p-4 md:p-8 pb-20 md:pb-8 flex flex-col gap-8 animate-in fade-in duration-300">
      <div className="flex items-start justify-between gap-4">
        <TeachHeader />
        <button
          onClick={() => setShowCreate(true)}
          className="kinetic-btn kinetic-accent-gradient px-4 py-2.5 text-sm shrink-0"
        >
          <Plus size={16} /> New class
        </button>
      </div>

      {error && (
        <div className="kinetic-card bg-white text-[#ba1a1a] text-sm">Couldn't load your classes: {error}</div>
      )}

      <section>
        <h3 className="font-sans text-xs font-bold text-[#64748B] uppercase tracking-widest mb-3">
          Classes you teach
        </h3>
        {teaching.length === 0 ? (
          <div className="kinetic-card bg-white p-6 flex items-start gap-4">
            <div className="w-10 h-10 rounded-lg bg-[#0891B2]/10 flex items-center justify-center text-[#0891B2] shrink-0">
              <Presentation size={18} />
            </div>
            <div>
              <h4 className="font-sans text-sm font-semibold text-[#0F172A] mb-1">No classes yet</h4>
              <p className="font-sans text-xs text-[#64748B] leading-relaxed">
                Create one, assign a subject, then share the join code with your students — their gap map fills in as they study.
              </p>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {teaching.map((c) => (
              <TeachingCard key={c.id} classroom={c} onNavigate={() => navigate(`/teach/${c.id}`)} />
            ))}
          </div>
        )}
      </section>

      {enrolled.length > 0 && (
        <section>
          <h3 className="font-sans text-xs font-bold text-[#64748B] uppercase tracking-widest mb-3">
            Classes you're in
          </h3>
          <div className="flex flex-col gap-2">
            {enrolled.map((c) => (
              <div key={c.id} className="kinetic-card bg-white p-4 flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <p className="font-sans text-sm font-semibold text-[#0F172A] truncate">{c.name}</p>
                  <p className="font-sans text-xs text-[#64748B] mt-0.5 truncate">
                    {c.school_name || 'No school name set'} · joined as "{c.display_name}"
                  </p>
                </div>
                <button
                  onClick={() => handleLeave(c.id, c.name)}
                  className="shrink-0 text-xs font-semibold text-[#B91C1C] hover:text-[#ba1a1a] transition-colors"
                >
                  Leave
                </button>
              </div>
            ))}
          </div>
        </section>
      )}

      {showCreate && (
        <CreateClassroomModal
          onClose={() => setShowCreate(false)}
          onCreated={(c) => { setShowCreate(false); load(); navigate(`/teach/${c.id}`); }}
        />
      )}
    </div>
  );
}

function TeachHeader() {
  return (
    <header>
      <h2 className="font-sans text-2xl font-semibold text-[#0F172A] flex items-center gap-2">
        <Presentation size={24} className="text-[#0891B2]" /> Teach
      </h2>
      <p className="font-sans text-sm text-[#64748B] mt-1">
        Run a classroom — a live gap map and roster for every student who joins.
      </p>
    </header>
  );
}

function TeachingCard({ classroom, onNavigate }) {
  const toast = useToast();
  const copyCode = (e) => {
    e.stopPropagation();
    navigator.clipboard?.writeText(classroom.join_code);
    toast.success('Join code copied.');
  };
  return (
    <button
      onClick={onNavigate}
      className="kinetic-card bg-white p-5 text-left hover:border-[#0891B2]/40 hover:-translate-y-0.5 transition-all duration-150 flex flex-col gap-3"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="font-sans text-base font-semibold text-[#0F172A] truncate">{classroom.name}</p>
          {classroom.school_name && (
            <p className="font-sans text-xs text-[#64748B] mt-0.5 truncate">{classroom.school_name}</p>
          )}
        </div>
        <span className="shrink-0 flex items-center gap-1 font-sans text-xs font-semibold text-[#64748B]">
          <Users size={13} /> {classroom.member_count}
        </span>
      </div>
      <div
        onClick={copyCode}
        title="Copy join code"
        className="flex items-center gap-2 self-start px-2.5 py-1.5 rounded-lg bg-[rgba(15,23,42,0.04)] hover:bg-[rgba(15,23,42,0.07)] transition-colors"
      >
        <span className="font-mono text-xs font-semibold text-[#0F172A] tracking-wider">{classroom.join_code}</span>
        <Copy size={12} className="text-[#64748B]" />
      </div>
    </button>
  );
}

function CreateClassroomModal({ onClose, onCreated }) {
  const [name, setName] = useState('');
  const [schoolName, setSchoolName] = useState('');
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState(null);

  const submit = async (e) => {
    e.preventDefault();
    if (!name.trim() || saving) return;
    setSaving(true);
    setErr(null);
    try {
      const c = await apiFetch('/api/classrooms/', {
        method: 'POST',
        body: JSON.stringify({ name: name.trim(), school_name: schoolName.trim() || null }),
      });
      onCreated(c);
    } catch (e2) {
      setErr(e2.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] bg-[rgba(15,23,42,0.4)] flex items-center justify-center p-4" onClick={onClose}>
      <form
        onSubmit={submit}
        onClick={(e) => e.stopPropagation()}
        className="kinetic-card bg-white p-6 w-full max-w-sm flex flex-col gap-4"
      >
        <div className="flex items-center justify-between">
          <h3 className="font-sans text-base font-semibold text-[#0F172A]">New classroom</h3>
          <button type="button" onClick={onClose} className="text-[#64748B] hover:text-[#0F172A]">
            <X size={18} />
          </button>
        </div>

        <label className="flex flex-col gap-1.5">
          <span className="font-sans text-xs font-semibold text-[#64748B]">Class name</span>
          <input
            autoFocus
            value={name}
            onChange={(e) => setName(e.target.value)}
            maxLength={120}
            placeholder="Class 9-A Physics"
            className="px-3 py-2 rounded-lg border border-[rgba(15,23,42,0.12)] font-sans text-sm text-[#0F172A] focus:outline-none focus:border-[#0891B2] focus:ring-2 focus:ring-[#0891B2]/20"
          />
        </label>

        <label className="flex flex-col gap-1.5">
          <span className="font-sans text-xs font-semibold text-[#64748B]">School (optional)</span>
          <input
            value={schoolName}
            onChange={(e) => setSchoolName(e.target.value)}
            maxLength={200}
            placeholder="e.g. Springdale Public School"
            className="px-3 py-2 rounded-lg border border-[rgba(15,23,42,0.12)] font-sans text-sm text-[#0F172A] focus:outline-none focus:border-[#0891B2] focus:ring-2 focus:ring-[#0891B2]/20"
          />
        </label>

        {err && <p className="font-sans text-xs text-[#ba1a1a]">{err}</p>}

        <button
          type="submit"
          disabled={!name.trim() || saving}
          className="kinetic-btn kinetic-accent-gradient py-2.5 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {saving ? 'Creating…' : 'Create classroom'}
        </button>
      </form>
    </div>
  );
}

export default Teach;
