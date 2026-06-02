import React, { useEffect, useState } from 'react';
import { User, Mail, Shield, LogOut, Trash2 } from 'lucide-react';
import { supabase } from './lib/supabase';
import { useNavigate } from 'react-router-dom';

function Profile() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);

  useEffect(() => {
    supabase.auth.getUser().then(({ data: { user } }) => {
      setUser(user);
    });
  }, []);

  const handleSignOut = async () => {
    await supabase.auth.signOut();
    navigate('/');
  };

  if (!user) {
    return <div className="p-8 text-center text-[#64748B]">Loading profile...</div>;
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
            <div className="flex justify-between items-center py-2 border-b border-[rgba(15,23,42,0.05)]">
              <span className="font-sans text-xs text-[#64748B]">User ID</span>
              <span className="font-mono text-xs text-[#0F172A] bg-slate-100 px-2 py-1 rounded truncate max-w-[120px]">{user.id}</span>
            </div>

            {/* DEV TOOL — remove before production */}
            <div className="flex justify-between items-center py-2">
              <span className="font-sans text-xs text-[#64748B]">Dev: JWT Token</span>
              <button
                onClick={async () => {
                  const { data } = await supabase.auth.getSession();
                  await navigator.clipboard.writeText(data.session.access_token);
                  alert('JWT copied to clipboard!');
                }}
                className="font-mono text-xs text-[#0891B2] bg-[#0891B2]/10 px-2 py-1 rounded hover:bg-[#0891B2]/20 transition-colors"
              >
                Copy JWT
              </button>
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
