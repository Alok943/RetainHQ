import React, { useEffect, useState } from 'react';
import { User, Mail, Shield, LogOut, Trash2, Sun, Moon, GraduationCap, School, Bell, BellOff, Presentation, ChevronRight } from 'lucide-react';
import { supabase } from './lib/supabase';
import { useNavigate } from 'react-router-dom';
import { useTheme } from './lib/theme';
import { apiFetch } from './lib/api';
import { useToast } from './lib/ToastContext';
import { getPushState, subscribePush, unsubscribePush, isPushSupported } from './lib/push';
import { track, EVENTS } from './lib/analytics';

function Profile() {
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';
  const [user, setUser] = useState(null);
  const [audience, setAudience] = useState(null);
  const [savingAudience, setSavingAudience] = useState(false);
  const [pushState, setPushState] = useState(null); // null = loading
  const [pushBusy, setPushBusy] = useState(false);
  const [classrooms, setClassrooms] = useState(null); // { teaching, enrolled }
  const toast = useToast();

  const loadClassrooms = () => {
    apiFetch('/api/classrooms/mine').then(setClassrooms).catch(() => {});
  };

  useEffect(() => {
    supabase.auth.getUser().then(({ data: { user } }) => {
      setUser(user);
    });
    apiFetch('/api/prefs/').then((p) => setAudience(p.audience)).catch(() => {});
    getPushState().then(setPushState);
    loadClassrooms();
  }, []);

  const handleLeaveClassroom = async (classroomId, name) => {
    if (!window.confirm(`Leave "${name}"? Your teacher loses visibility into your progress immediately — nothing else changes.`)) return;
    try {
      await apiFetch(`/api/classrooms/${classroomId}/membership`, { method: 'DELETE' });
      toast.success(`Left ${name}.`);
      loadClassrooms();
    } catch {
      // apiFetch already toasts server-side failures
    }
  };

  const togglePush = async () => {
    if (pushBusy) return;
    setPushBusy(true);
    try {
      if (pushState === 'subscribed') {
        await unsubscribePush();
        track(EVENTS.PUSH_UNSUBSCRIBED);
        setPushState('prompt');
      } else {
        await subscribePush();
        track(EVENTS.PUSH_SUBSCRIBED);
        setPushState('subscribed');
      }
    } catch (e) {
      // Notification.requestPermission resolving 'denied' throws from
      // pushManager.subscribe — reflect the real browser state, don't guess.
      const state = await getPushState();
      setPushState(state);
      if (state === 'denied') {
        toast.error("Notifications are blocked for RetainHQ — enable them in your browser's site settings to turn this on.");
      } else {
        toast.error("Couldn't turn on notifications — try again.");
      }
    } finally {
      setPushBusy(false);
    }
  };

  const switchAudience = async (value) => {
    if (value === audience || savingAudience) return;
    setSavingAudience(true);
    try {
      const p = await apiFetch('/api/prefs/', {
        method: 'PUT',
        body: JSON.stringify({ audience: value }),
      });
      setAudience(p.audience);
      // The whole point of switching catalogs is to go look at the new one —
      // land the user on Learn instead of leaving them on the settings page.
      navigate('/roadmaps');
    } catch {
      // keep the old selection on failure
    } finally {
      setSavingAudience(false);
    }
  };

  const handleSignOut = async () => {
    await supabase.auth.signOut();
    navigate('/');
  };

  if (!user) {
    return (
      <div className="flex flex-col gap-8 p-4 md:p-8 max-w-4xl mx-auto w-full pb-20 md:pb-8">
        <header className="mb-2">
          <h2 className="font-sans text-2xl font-semibold text-[#0F172A] flex items-center gap-2">
            <User size={24} className="text-[#0891B2]" /> Account Profile
          </h2>
          <p className="font-sans text-sm text-[#64748B] mt-1">Manage your identity and account settings.</p>
        </header>

        <div className="kinetic-card bg-[#131b2e] border-[#131b2e] p-8 flex flex-col md:flex-row items-center md:items-start gap-6 border-l-4 border-l-[#0891B2]">
          <div className="skeleton w-24 h-24 rounded-full shrink-0" />
          <div className="flex flex-col items-center md:items-start gap-2 pt-2 w-full">
            <div className="skeleton h-6 w-48" />
            <div className="skeleton h-4 w-40" />
            <div className="skeleton h-5 w-36 rounded-full mt-2" />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="kinetic-card bg-white p-6">
            <div className="skeleton h-3 w-32 mb-4" />
            <div className="flex flex-col gap-4">
              <div className="flex justify-between items-center py-2 border-b border-[rgba(15,23,42,0.05)]">
                <div className="skeleton h-3 w-24" />
                <div className="skeleton h-4 w-28" />
              </div>
              <div className="flex justify-between items-center py-2">
                <div className="skeleton h-3 w-16" />
                <div className="skeleton h-4 w-24" />
              </div>
            </div>
          </div>
          <div className="kinetic-card bg-white p-6 flex flex-col justify-between gap-6">
            <div>
              <div className="skeleton h-3 w-20 mb-3" />
              <div className="skeleton h-3 w-full mb-1.5" />
              <div className="skeleton h-3 w-2/3" />
            </div>
            <div className="skeleton h-10 w-full rounded" />
          </div>
        </div>

        <div className="kinetic-card bg-white p-6">
          <div className="skeleton h-3 w-24 mb-4" />
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="skeleton w-9 h-9 rounded-full" />
              <div>
                <div className="skeleton h-3.5 w-24 mb-1.5" />
                <div className="skeleton h-3 w-32" />
              </div>
            </div>
            <div className="skeleton h-7 w-12 rounded-full" />
          </div>
        </div>
      </div>
    );
  }

  const initials = user.email ? user.email.substring(0, 2).toUpperCase() : 'US';
  const joinedDate = new Date(user.created_at).toLocaleDateString('en-US', {
    month: 'long',
    year: 'numeric'
  });

  return (
    <div className="flex flex-col gap-8 p-4 md:p-8 max-w-4xl mx-auto w-full pb-20 md:pb-8 animate-in fade-in duration-300">
      
      <header className="mb-2">
        <h2 className="font-sans text-2xl font-semibold text-[#0F172A] flex items-center gap-2">
          <User size={24} className="text-[#0891B2]" /> Account Profile
        </h2>
        <p className="font-sans text-sm text-[#64748B] mt-1">Manage your identity and account settings.</p>
      </header>

      {/* Hero Profile Card */}
      <div className="kinetic-card bg-[#131b2e] border-[#131b2e] p-8 flex flex-col md:flex-row items-center md:items-start gap-6 border-l-4 border-l-[#0891B2]">
        <div className="w-24 h-24 bg-[#0F172A] rounded-full flex items-center justify-center text-3xl font-mono font-medium text-white shadow-xl shrink-0 border border-[rgba(255,255,255,0.1)]">
          {initials}
        </div>
        
        <div className="flex flex-col text-center md:text-left pt-2">
          <h3 className="font-sans text-2xl font-bold text-white mb-1 truncate max-w-full">
            {user.user_metadata?.full_name || user.email}
          </h3>
          <div className="flex items-center justify-center md:justify-start gap-2 text-[#7c839b] font-mono text-sm mb-4">
            <Mail size={14} /> {user.email}
          </div>
          <span className="font-sans text-[11px] font-bold text-[#0891B2] bg-[#0891B2]/20 px-2.5 py-1 rounded-full flex items-center gap-1.5 tracking-normal border border-[#0891B2]/30 uppercase w-max mx-auto md:mx-0">
            <Shield size={12} /> Google Authenticated
          </span>
        </div>
      </div>

      {/* Details Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        <div className="kinetic-card bg-white p-6">
          <h3 className="font-sans text-sm font-semibold text-[#0F172A] mb-4 uppercase tracking-widest">Account Details</h3>
          
          <div className="flex flex-col gap-4">
            <div className="flex justify-between items-center py-2 border-b border-[rgba(15,23,42,0.05)]">
              <span className="font-sans text-xs text-[#64748B]">Member Since</span>
              <span className="font-mono text-sm text-[#0F172A] font-medium">{joinedDate}</span>
            </div>
            <div className="flex justify-between items-center py-2">
              <span className="font-sans text-xs text-[#64748B]">User ID</span>
              <span className="font-mono text-xs text-[#0F172A] bg-slate-100 px-2 py-1 rounded truncate max-w-[120px]">{user.id}</span>
            </div>
          </div>
        </div>

        <div className="kinetic-card bg-white p-6 flex flex-col justify-between">
          <div>
            <h3 className="font-sans text-sm font-semibold text-[#0F172A] mb-2 uppercase tracking-widest">Session</h3>
            <p className="font-sans text-xs text-[#64748B] mb-6">
              You are securely signed in. Sign out of this device to clear your active session.
            </p>
          </div>
          
          <button 
            onClick={handleSignOut}
            className="w-full flex items-center justify-center gap-2 py-2.5 border border-[#0F172A] text-[#0F172A] hover:bg-slate-50 font-medium text-sm rounded transition-colors"
          >
            <LogOut size={16} /> Sign Out
          </button>
        </div>
      </div>

      {/* Appearance */}
      <div className="kinetic-card bg-white p-6">
        <h3 className="font-sans text-sm font-semibold text-[#0F172A] mb-4 uppercase tracking-widest">Appearance</h3>
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-[rgba(15,23,42,0.05)] flex items-center justify-center text-[#0891B2]">
              {isDark ? <Moon size={16} /> : <Sun size={16} />}
            </div>
            <div>
              <p className="font-sans text-sm font-semibold text-[#0F172A]">Dark Mode</p>
              <p className="font-sans text-xs text-[#64748B]">
                {isDark ? 'Dark theme is on.' : 'Switch to a low-light theme.'}
              </p>
            </div>
          </div>

          <button
            type="button"
            role="switch"
            aria-checked={isDark}
            aria-label="Toggle dark mode"
            onClick={toggleTheme}
            className={`relative inline-flex h-7 w-12 shrink-0 items-center rounded-full transition-colors duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#0891B2] focus-visible:ring-offset-2 ${
              isDark ? 'bg-[#0891B2]' : 'bg-slate-200'
            }`}
          >
            <span
              style={{ backgroundColor: '#ffffff' }}
              className={`inline-block h-5 w-5 transform rounded-full shadow transition-transform duration-200 ${
                isDark ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
      </div>

      {/* Push notifications */}
      <div className="kinetic-card bg-white p-6">
        <h3 className="font-sans text-sm font-semibold text-[#0F172A] mb-4 uppercase tracking-widest">Notifications</h3>
        {!isPushSupported() ? (
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-[rgba(15,23,42,0.05)] flex items-center justify-center text-[#64748B]">
              <BellOff size={16} />
            </div>
            <div>
              <p className="font-sans text-sm font-semibold text-[#0F172A]">Daily reminder notifications</p>
              <p className="font-sans text-xs text-[#64748B] mt-0.5">
                Not supported in this browser. On iPhone, add RetainHQ to your Home Screen first (Share → Add to Home Screen), then enable notifications from there.
              </p>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-full bg-[rgba(15,23,42,0.05)] flex items-center justify-center text-[#0891B2]">
                {pushState === 'subscribed' ? <Bell size={16} /> : <BellOff size={16} />}
              </div>
              <div>
                <p className="font-sans text-sm font-semibold text-[#0F172A]">Daily reminder notifications</p>
                <p className="font-sans text-xs text-[#64748B] mt-0.5">
                  {pushState === 'denied'
                    ? 'Blocked — enable in your browser\'s site settings for retainhq.app.'
                    : pushState === 'subscribed'
                      ? 'On. Mirrors your daily reminder email.'
                      : 'Get a notification when reviews are due, same content as the daily email.'}
                </p>
              </div>
            </div>

            <button
              type="button"
              role="switch"
              aria-checked={pushState === 'subscribed'}
              aria-label="Toggle push notifications"
              onClick={togglePush}
              disabled={pushState === null || pushState === 'denied' || pushBusy}
              className={`relative inline-flex h-7 w-12 shrink-0 items-center rounded-full transition-colors duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#0891B2] focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed ${
                pushState === 'subscribed' ? 'bg-[#0891B2]' : 'bg-slate-200'
              }`}
            >
              <span
                style={{ backgroundColor: '#ffffff' }}
                className={`inline-block h-5 w-5 transform rounded-full shadow transition-transform duration-200 ${
                  pushState === 'subscribed' ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        )}
      </div>

      {/* Learning catalog (career vs school) */}
      <div className="kinetic-card bg-white p-6">
        <h3 className="font-sans text-sm font-semibold text-[#0F172A] mb-1 uppercase tracking-widest">Learning Catalog</h3>
        <p className="font-sans text-xs text-[#64748B] mb-4">
          Pick what you're studying — this decides which roadmaps you see. Your progress in the other catalog is kept.
        </p>
        <div className="flex flex-col sm:flex-row gap-3">
          {[
            { value: 'career', icon: GraduationCap, title: 'College — Coding & CS', desc: 'DSA, Python, SQL, core CS & interviews.' },
            { value: 'school', icon: School, title: 'School — Class 9 & 10', desc: 'NCERT Physics, concept by concept.' },
          ].map(({ value, icon: Icon, title, desc }) => (
            <button
              key={value}
              type="button"
              disabled={savingAudience || audience === null}
              onClick={() => switchAudience(value)}
              aria-pressed={audience === value}
              className={`flex-1 flex items-start gap-3 p-4 border rounded text-left transition-colors disabled:opacity-60 ${
                audience === value
                  ? 'border-[#0891B2] bg-[#0891B2]/5'
                  : 'border-slate-200 hover:border-[#0891B2] hover:bg-slate-50'
              }`}
            >
              <div className="w-9 h-9 shrink-0 rounded-full bg-[rgba(15,23,42,0.05)] flex items-center justify-center text-[#0891B2]">
                <Icon size={16} />
              </div>
              <div>
                <p className="font-sans text-sm font-semibold text-[#0F172A]">{title}</p>
                <p className="font-sans text-xs text-[#64748B] mt-0.5">{desc}</p>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Teach entry point — discoverable before the nav item appears (which only
          shows once GET /api/classrooms/mine.teaching is non-empty) */}
      <div className="kinetic-card bg-white p-6 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-[rgba(15,23,42,0.05)] flex items-center justify-center text-[#0891B2] shrink-0">
            <Presentation size={16} />
          </div>
          <div>
            <p className="font-sans text-sm font-semibold text-[#0F172A]">Set up your class</p>
            <p className="font-sans text-xs text-[#64748B] mt-0.5">
              {classrooms?.teaching?.length
                ? `You teach ${classrooms.teaching.length} class${classrooms.teaching.length === 1 ? '' : 'es'}.`
                : 'Run a live gap map and roster for a class of students.'}
            </p>
          </div>
        </div>
        <button
          onClick={() => navigate('/teach')}
          className="shrink-0 flex items-center gap-1 font-sans text-sm font-semibold text-[#0891B2] hover:text-[#06B6D4] transition-colors"
        >
          {classrooms?.teaching?.length ? 'Manage' : 'Get started'} <ChevronRight size={15} />
        </button>
      </div>

      {/* My Class — school-audience students see the classroom(s) they've joined */}
      {audience === 'school' && classrooms?.enrolled?.length > 0 && (
        <div className="kinetic-card bg-white p-6">
          <h3 className="font-sans text-sm font-semibold text-[#0F172A] mb-1 uppercase tracking-widest">My Class</h3>
          <p className="font-sans text-xs text-[#64748B] mb-4">
            Classes you've joined — your teacher sees your activity, review outcomes, and mastery on these subjects only.
          </p>
          <div className="flex flex-col gap-2">
            {classrooms.enrolled.map((c) => (
              <div key={c.id} className="flex items-center justify-between gap-3 py-2.5 border-b border-[rgba(15,23,42,0.05)] last:border-b-0">
                <div className="min-w-0">
                  <p className="font-sans text-sm font-semibold text-[#0F172A] truncate">{c.name}</p>
                  <p className="font-sans text-xs text-[#64748B] mt-0.5 truncate">
                    {c.school_name || 'No school name set'} · joined as "{c.display_name}"
                  </p>
                </div>
                <button
                  onClick={() => handleLeaveClassroom(c.id, c.name)}
                  className="shrink-0 text-xs font-semibold text-[#B91C1C] hover:text-[#ba1a1a] transition-colors"
                >
                  Leave
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Danger Zone */}
      <div className="mt-4 p-6 border border-[#B91C1C]/20 bg-[#B91C1C]/5 rounded">
        <h3 className="font-sans text-sm font-semibold text-[#B91C1C] mb-2 uppercase tracking-widest flex items-center gap-2">
          <Trash2 size={16} /> Danger Zone
        </h3>
        <p className="font-sans text-xs text-[#64748B] mb-4">
          Deleting your account is permanent. All associated roadmap progress, review history, and stats will be wiped from our servers immediately.
        </p>
        <button 
          disabled
          className="px-4 py-2 bg-[#B91C1C]/10 text-[#B91C1C] font-semibold text-xs rounded opacity-50 cursor-not-allowed"
        >
          Delete Account (Coming Soon)
        </button>
      </div>

    </div>
  );
}

export default Profile;
