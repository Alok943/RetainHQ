import React, { useState } from 'react';
import { GraduationCap, School } from 'lucide-react';
import { apiFetch } from './lib/api';

// One-time onboarding choice between the two catalogs. Shown on Home when
// GET /api/prefs returns is_set=false; also reused as the switcher body in
// Profile. Copy is deliberately identity-based ("where are you"), NOT
// goal-based ("placements") — 1st/2nd-years bounce off placement framing.
const OPTIONS = [
  {
    value: 'career',
    icon: GraduationCap,
    title: 'College — Coding & CS',
    desc: 'DSA, Python, SQL, core CS and more — from first-year fundamentals to final-year interviews.',
  },
  {
    value: 'school',
    icon: School,
    title: 'School — Class 9 & 10',
    desc: 'NCERT Physics concept-by-concept, so nothing you learn in August is forgotten by boards.',
  },
];

function AudiencePicker({ onDone }) {
  const [saving, setSaving] = useState(null);
  const [error, setError] = useState(null);

  const choose = async (value) => {
    setSaving(value);
    setError(null);
    try {
      const prefs = await apiFetch('/api/prefs/', {
        method: 'PUT',
        body: JSON.stringify({ audience: value }),
      });
      onDone(prefs.audience);
    } catch (err) {
      setError('Could not save your choice. Please try again.');
      setSaving(null);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#0F172A]/60 p-4">
      <div className="kinetic-card bg-white p-6 md:p-8 w-full max-w-lg rounded">
        <h2 className="font-sans text-lg font-semibold text-[#0F172A] mb-1">What are you learning for?</h2>
        <p className="font-sans text-xs text-[#64748B] mb-6">
          This picks which roadmaps you see. You can change it anytime from your Profile.
        </p>
        <div className="flex flex-col gap-3">
          {OPTIONS.map(({ value, icon: Icon, title, desc }) => (
            <button
              key={value}
              type="button"
              disabled={saving !== null}
              onClick={() => choose(value)}
              className="flex items-start gap-4 p-4 border border-slate-200 rounded text-left hover:border-[#0891B2] hover:bg-slate-50 transition-colors disabled:opacity-60"
            >
              <div className="w-9 h-9 shrink-0 rounded-full bg-[rgba(15,23,42,0.05)] flex items-center justify-center text-[#0891B2]">
                <Icon size={18} />
              </div>
              <div>
                <p className="font-sans text-sm font-semibold text-[#0F172A]">
                  {title}
                  {saving === value && <span className="ml-2 text-xs font-normal text-[#64748B]">Saving…</span>}
                </p>
                <p className="font-sans text-xs text-[#64748B] mt-0.5">{desc}</p>
              </div>
            </button>
          ))}
        </div>
        {error && <p className="font-sans text-xs text-[#B91C1C] mt-4">{error}</p>}
      </div>
    </div>
  );
}

export default AudiencePicker;
