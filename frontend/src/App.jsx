import React, { useEffect, useState } from 'react';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { Home as HomeIcon, CheckSquare, PlusSquare, Map, BarChart2, LogOut } from 'lucide-react';
import { supabase } from './lib/supabase';
import { useTheme } from './lib/theme';

import Home from './Home';
import Review from './Review';
import LogActivity from './LogActivity';
import Roadmaps from './Roadmaps';
import Analytics from './Analytics';
import RoadmapDetail from './RoadmapDetail';
import Login from './Login';
import Profile from './Profile';
import Logo from './Logo';

function App() {
  const location = useLocation();
  const navigate = useNavigate();
  const { theme } = useTheme();
  // Navy mark on light surfaces, white mark on dark.
  const logoVariant = theme === 'dark' ? 'light' : 'dark';
  const [session, setSession] = useState(null);
  const [isInitializing, setIsInitializing] = useState(true);

  // Authentication Listener
  useEffect(() => {
    console.log('[Auth] App loaded with URL:', window.location.href);
    
    // Actively fetch the session on load (crucial for parsing the ?code= param in PKCE flow)
    supabase.auth.getSession().then(({ data: { session }, error }) => {
      console.log('[Auth] getSession finished. Session:', session, 'Error:', error);
      if (error) console.error('Error fetching session:', error);
      setSession(session);
      setIsInitializing(false);
      
      // Clean up URL if PKCE code is present
      if (session && window.location.search.includes('code=')) {
        window.history.replaceState(null, '', window.location.pathname);
      }
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event, session) => {
      console.log('[Auth] onAuthStateChange:', event, session);

      setSession(session);
      setIsInitializing(false);
      
      // Also clean up on SIGNED_IN event just in case
      if (event === 'SIGNED_IN' && window.location.search.includes('code=')) {
        window.history.replaceState(null, '', window.location.pathname);
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  const handleSignOut = async () => {
    await supabase.auth.signOut();
    navigate('/');
  };
  
  // Helper to determine active tab based on path
  const getActiveTab = () => {
    const path = location.pathname;
    if (path.startsWith('/reviews')) return 'review';
    if (path.startsWith('/log')) return 'log';
    if (path.startsWith('/roadmaps')) return 'roadmaps';
    if (path.startsWith('/analytics')) return 'analytics';
    return 'home';
  };
  
  const activeTab = getActiveTab();

  if (isInitializing) {
    return <div className="min-h-screen bg-[#f9f9f6] flex items-center justify-center font-sans text-[#64748B]">Loading...</div>;
  }

  // If not logged in, render the Login screen full-screen
  if (!session) {
    return <Login />;
  }

  // Get user initials for avatar
  const email = session.user.email || '';
  const initials = email ? email.substring(0, 2).toUpperCase() : 'US';

  return (
    <div className="flex h-screen w-full bg-[#f9f9f6] overflow-hidden text-[#1a1c1b] font-sans">
      
      {/* LEFT SIDEBAR (Desktop / Tablet) */}
      <aside className="hidden md:flex flex-col w-[240px] border-r border-[rgba(15,23,42,0.08)] bg-[#f9f9f6] p-6 shrink-0 justify-between">
        <div>
          <div className="mb-10">
            <div className="flex items-center gap-2.5 cursor-pointer w-max" onClick={() => navigate('/')}>
              <Logo variant={logoVariant} className="h-7 w-auto" />
              <h1 className="font-sans font-semibold text-2xl tracking-tight text-[#0F172A]">RetainHQ</h1>
            </div>
          </div>
          
          <nav className="flex flex-col gap-2">
            <SidebarItem icon={<HomeIcon size={20} />} label="Home" active={activeTab === 'home'} onClick={() => navigate('/')} />
            <SidebarItem icon={<CheckSquare size={20} />} label="Reviews" active={activeTab === 'review'} onClick={() => navigate('/reviews')} />
            <SidebarItem icon={<Map size={20} />} label="Roadmaps" active={activeTab === 'roadmaps'} onClick={() => navigate('/roadmaps')} />
            <SidebarItem icon={<BarChart2 size={20} />} label="Analytics" active={activeTab === 'analytics'} onClick={() => navigate('/analytics')} />
          </nav>
          
          <div className="mt-8">
            <button 
              onClick={() => navigate('/log')}
              className="kinetic-btn kinetic-accent-gradient w-full py-3 text-sm flex items-center justify-center gap-2"
            >
              <PlusSquare size={16} /> Log Activity
            </button>
          </div>
        </div>

        {/* User Profile Area */}
        <div className="flex flex-col gap-4 pt-6 border-t border-[rgba(15,23,42,0.08)]">
          <div 
            onClick={() => navigate('/profile')}
            className="flex items-center gap-3 cursor-pointer p-2 -mx-2 hover:bg-[rgba(15,23,42,0.03)] rounded transition-colors"
          >
            <div className="h-8 w-8 bg-[#131b2e] rounded-full flex items-center justify-center text-xs font-mono font-medium text-white shrink-0">
              {initials}
            </div>
            <span className="text-sm font-semibold text-[#0F172A] truncate" title={email}>{email}</span>
          </div>
          
          <button 
            onClick={handleSignOut}
            className="flex items-center gap-2 text-xs font-semibold text-[#64748B] hover:text-[#B91C1C] transition-colors pl-2"
          >
            <LogOut size={14} /> Sign Out
          </button>
        </div>
      </aside>

      {/* MAIN CONTENT AREA */}
      <div className="flex-1 flex flex-col h-full relative overflow-hidden">
        
        {/* Mobile Header (Hidden on md+) */}
        <header className="md:hidden px-4 py-4 border-b border-[rgba(15,23,42,0.08)] bg-[#f9f9f6] sticky top-0 z-10 flex justify-between items-center">
          <div className="flex items-center gap-2" onClick={() => navigate('/')}>
            <Logo variant={logoVariant} className="h-6 w-auto" />
            <h1 className="font-sans font-semibold text-xl tracking-tight text-[#0F172A]">RetainHQ</h1>
          </div>
          <div className="flex items-center gap-3">
            <button onClick={handleSignOut} className="text-[#64748B] hover:text-[#B91C1C]">
              <LogOut size={18} />
            </button>
            <div 
              onClick={() => navigate('/profile')}
              className="h-8 w-8 bg-[#131b2e] rounded-full flex items-center justify-center text-xs font-mono font-medium text-white cursor-pointer"
            >
              {initials}
            </div>
          </div>
        </header>

        {/* Content Scrollable Area */}
        <main className="flex-1 overflow-y-auto w-full relative">
          <Routes>
            <Route path="/" element={<Home onStartReviews={() => navigate('/reviews')} />} />
            <Route path="/reviews" element={<Review onBack={() => navigate('/')} />} />
            <Route path="/log" element={<LogActivity />} />
            <Route path="/roadmaps" element={<Roadmaps />} />
            <Route path="/roadmaps/:id" element={<RoadmapDetail />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/profile" element={<Profile />} />
          </Routes>
        </main>

        {/* Mobile Bottom Navigation (Hidden on md+) */}
        <nav className="md:hidden absolute bottom-0 w-full bg-[#f9f9f6] border-t border-[rgba(15,23,42,0.08)] flex justify-around items-center px-2 py-3 z-20 pb-safe">
          <NavItem icon={<HomeIcon size={20} />} label="Home" active={activeTab === 'home'} onClick={() => navigate('/')} />
          <NavItem icon={<CheckSquare size={20} />} label="Review" active={activeTab === 'review'} onClick={() => navigate('/reviews')} />
          <NavItem icon={<PlusSquare size={20} />} label="Log" active={activeTab === 'log'} onClick={() => navigate('/log')} />
          <NavItem icon={<Map size={20} />} label="Roadmaps" active={activeTab === 'roadmaps'} onClick={() => navigate('/roadmaps')} />
          <NavItem icon={<BarChart2 size={20} />} label="Analytics" active={activeTab === 'analytics'} onClick={() => navigate('/analytics')} />
        </nav>
      </div>
    </div>
  );
}

function SidebarItem({ icon, label, active, onClick }) {
  return (
    <button 
      onClick={onClick}
      className={`flex items-center gap-3 px-4 py-3 rounded text-sm font-medium transition-colors w-full text-left ${
        active ? 'bg-[rgba(15,23,42,0.05)] text-[#0891B2]' : 'text-[#64748B] hover:bg-[rgba(15,23,42,0.02)] hover:text-[#0F172A]'
      }`}
    >
      {icon}
      <span>{label}</span>
    </button>
  );
}

function NavItem({ icon, label, active, onClick }) {
  return (
    <button 
      onClick={onClick}
      className={`flex flex-col items-center justify-center w-16 gap-1 ${
        active ? 'text-[#0891B2]' : 'text-[#64748B] hover:text-[#0F172A]'
      } transition-colors`}
    >
      {icon}
      <span className="font-sans text-[10px] font-medium">{label}</span>
    </button>
  );
}

export default App;
