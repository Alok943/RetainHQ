import React from 'react';
import { supabase } from './lib/supabase';
import Logo from './Logo';

function Login() {
  const handleGoogleLogin = async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: window.location.origin
      }
    });

    if (error) {
      console.error('Error logging in:', error.message);
    }
  };

  return (
    <div className="min-h-screen w-full bg-[#131b2e] flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-md animate-in fade-in slide-in-from-bottom-4 duration-700">
        
        {/* Logo Section */}
        <div className="flex flex-col items-center text-center mb-10">
          <div className="w-16 h-16 bg-[#0891B2]/10 rounded-2xl flex items-center justify-center mb-6 border border-[#0891B2]/20 shadow-[0_0_40px_rgba(8,145,178,0.2)]">
            <Logo variant="light" className="h-8 w-auto" />
          </div>
          <h1 className="font-sans text-3xl font-bold text-white tracking-tight mb-3">RetainHQ</h1>
          <p className="font-sans text-[#7c839b] text-sm leading-relaxed max-w-xs">
            The intelligent command center for mastering engineering concepts.
          </p>
        </div>

        {/* Login Card */}
        <div className="kinetic-card bg-white p-8 border-t-4 border-t-[#0891B2] shadow-2xl flex flex-col gap-6">
          <h2 className="font-sans text-xl font-semibold text-[#0F172A] text-center">Welcome back</h2>
          
          <button 
            onClick={handleGoogleLogin}
            className="kinetic-btn w-full py-3.5 bg-white border border-[rgba(15,23,42,0.15)] text-[#0F172A] hover:bg-slate-50 flex items-center justify-center gap-3 font-semibold transition-all shadow-sm"
          >
            <svg viewBox="0 0 24 24" width="20" height="20" xmlns="http://www.w3.org/2000/svg">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
              <path d="M1 1h22v22H1z" fill="none"/>
            </svg>
            Continue with Google
          </button>

          <p className="font-sans text-xs text-center text-[#64748B]">
            By continuing, you agree to our Terms of Service and Privacy Policy.
          </p>
        </div>

      </div>
    </div>
  );
}

export default Login;
