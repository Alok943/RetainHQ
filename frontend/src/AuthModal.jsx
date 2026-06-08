import React from 'react';
import { supabase } from './lib/supabase';
import { X, ArrowRight, Brain } from 'lucide-react';
import Logo from './Logo';

export default function AuthModal({ onClose }) {
  const handleGoogleLogin = async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: window.location.href },
    });
    if (error) console.error('Error logging in:', error.message);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#131b2e]/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-[#f9f9f6] rounded-2xl shadow-2xl w-full max-w-md overflow-hidden flex flex-col relative border border-[rgba(15,23,42,0.08)]">
        
        {/* Close button */}
        <button 
          onClick={onClose} 
          className="absolute top-4 right-4 text-[#64748B] hover:text-[#0F172A] transition-colors p-1"
          aria-label="Close"
        >
          <X size={20} />
        </button>

        <div className="p-8 pb-6 flex flex-col items-center text-center">
          <div className="w-14 h-14 bg-gradient-to-br from-[#0891B2] to-[#06B6D4] rounded-2xl flex items-center justify-center shadow-lg shadow-[#0891B2]/20 mb-6">
            <Logo variant="dark" className="h-8 w-auto" />
          </div>
          
          <h2 className="font-sans text-2xl font-bold text-[#0F172A] mb-3">
            Save your progress
          </h2>
          <p className="font-sans text-[15px] text-[#64748B] leading-relaxed mb-8 max-w-[280px]">
            Sign in to start logging topics, scheduling reviews, and building your knowledge vault.
          </p>

          <button
            onClick={handleGoogleLogin}
            className="w-full flex items-center justify-center gap-3 bg-white border border-[rgba(15,23,42,0.12)] hover:border-[rgba(15,23,42,0.2)] hover:bg-[rgba(15,23,42,0.02)] text-[#0F172A] font-semibold font-sans py-3.5 px-6 rounded-xl transition-all shadow-sm"
          >
            <svg viewBox="0 0 24 24" className="w-5 h-5">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
            </svg>
            Continue with Google
          </button>
        </div>

        <div className="bg-[rgba(15,23,42,0.03)] border-t border-[rgba(15,23,42,0.08)] px-8 py-5">
          <ul className="flex flex-col gap-3">
            <li className="flex items-center gap-3 font-sans text-sm text-[#64748B]">
              <div className="w-6 h-6 rounded-full bg-[#0891B2]/10 flex items-center justify-center text-[#0891B2]">
                <CheckCircle2 size={12} className="opacity-80" />
              </div>
              Adaptive spaced repetition
            </li>
            <li className="flex items-center gap-3 font-sans text-sm text-[#64748B]">
              <div className="w-6 h-6 rounded-full bg-[#0891B2]/10 flex items-center justify-center text-[#0891B2]">
                <CheckCircle2 size={12} className="opacity-80" />
              </div>
              AI-graded active recall
            </li>
            <li className="flex items-center gap-3 font-sans text-sm text-[#64748B]">
              <div className="w-6 h-6 rounded-full bg-[#0891B2]/10 flex items-center justify-center text-[#0891B2]">
                <CheckCircle2 size={12} className="opacity-80" />
              </div>
              Visual retention tracking
            </li>
          </ul>
        </div>

      </div>
    </div>
  );
}

// Dummy icon locally since we can't import all at once easily without cluttering
function CheckCircle2({ size, className }) {
  return <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="m9 11 3 3L22 4"/></svg>;
}
