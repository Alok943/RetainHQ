import React, { useState, useEffect } from 'react';
import { Routes, Route, useNavigate, useLocation, Navigate } from 'react-router-dom';
import { Home as HomeIcon, CheckSquare, PlusSquare, Map, BarChart2, LogOut, Database, ShieldCheck, LogIn, PanelLeftClose, PanelLeftOpen, Plus } from 'lucide-react';
import { supabase } from './lib/supabase';
import { useTheme } from './lib/theme';
import { AuthProvider, useAuth } from './lib/AuthContext';
import { apiFetch } from './lib/api';

import Home from './Home';
import Review from './Review';
import LogActivity from './LogActivity';
import Roadmaps from './Roadmaps';
import Analytics from './Analytics';
import RoadmapDetail from './RoadmapDetail';
import Login from './Login';
import Profile from './Profile';
import KnowledgeVault from './KnowledgeVault';
import Admin from './Admin';
import Logo from './Logo';

const ADMIN_EMAIL = 'aloksingh98541@gmail.com';

function AppLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const { theme } = useTheme();
  const { session, showAuthModal } = useAuth();
  
  const [isCollapsed, setIsCollapsed] = useState(() => {
    return localStorage.getItem('sidebar_collapsed') === 'true' || location.pathname.startsWith('/roadmaps');
  });

  // Due-count badge on the Reviews nav item — the habit cue has to live in the
  // chrome, not just on Home. Re-fetched on route change so completing reviews
  // clears it without a hard refresh.
  const [dueCount, setDueCount] = useState(0);
  useEffect(() => {
    if (!session) {
      setDueCount(0);
      return;
    }
    apiFetch('/api/dashboard/')
      .then((d) => setDueCount(d?.due_count ?? 0))
      .catch(() => {});
  }, [session, location.pathname]);

  useEffect(() => {
    if (location.pathname.startsWith('/roadmaps')) {
      setIsCollapsed(true);
    }
  }, [location.pathname]);

  const toggleCollapse = () => {
    const newVal = !isCollapsed;
    setIsCollapsed(newVal);
    localStorage.setItem('sidebar_collapsed', newVal.toString());
  };

  const logoVariant = theme === 'dark' ? 'light' : 'dark';

  const handleSignOut = async () => {
    await supabase.auth.signOut();
    navigate('/');
  };
  
  const getActiveTab = () => {
    const path = location.pathname;
    if (path.startsWith('/reviews')) return 'review';
    if (path.startsWith('/log')) return 'log';
    if (path.startsWith('/roadmaps')) return 'roadmaps';
    if (path.startsWith('/vault')) return 'vault';
    if (path.startsWith('/analytics')) return 'analytics';
    if (path.startsWith('/admin')) return 'admin';
    return 'dashboard';
  };
  
  const activeTab = getActiveTab();

  const email = session?.user?.email || '';
  const initials = email ? email.substring(0, 2).toUpperCase() : '?';
  const isAdmin = email === ADMIN_EMAIL;

  return (
    <div className="flex h-screen w-full bg-[#f9f9f6] overflow-hidden text-[#1a1c1b] font-sans">
      {/* LEFT SIDEBAR (Desktop / Tablet) */}
      <aside className={`hidden md:flex flex-col border-r glass-nav shrink-0 justify-between transition-all duration-300 ${isCollapsed ? 'w-[84px] items-center p-6 px-4' : 'w-[240px] p-6'}`}>
        <div className="w-full">
          <div className={`flex items-center mb-10 ${isCollapsed ? 'flex-col gap-4' : 'justify-between'}`}>
            <div className="flex items-center gap-2.5 cursor-pointer overflow-hidden" onClick={() => navigate('/dashboard')}>
              <Logo variant={logoVariant} className="h-7 w-auto shrink-0" />
              {!isCollapsed && <h1 className="font-sans font-semibold text-2xl tracking-tight text-[#0F172A] whitespace-nowrap">RetainHQ</h1>}
            </div>
            <button onClick={toggleCollapse} className="text-[#64748B] hover:text-[#0F172A] transition-colors p-1.5 rounded hover:bg-[rgba(15,23,42,0.05)] shrink-0">
              {isCollapsed ? <PanelLeftOpen size={18} /> : <PanelLeftClose size={18} />}
            </button>
          </div>
          
          <nav className={`flex flex-col gap-2 ${isCollapsed ? 'items-center' : ''}`}>
            <SidebarItem isCollapsed={isCollapsed} icon={<HomeIcon size={20} />} label="Home" active={activeTab === 'dashboard'} onClick={() => navigate('/dashboard')} />
            <SidebarItem isCollapsed={isCollapsed} icon={<CheckSquare size={20} />} label="Reviews" active={activeTab === 'review'} onClick={() => navigate('/reviews')} badge={dueCount} />
            <SidebarItem isCollapsed={isCollapsed} icon={<Map size={20} />} label="Roadmaps" active={activeTab === 'roadmaps'} onClick={() => navigate('/roadmaps')} />
            <SidebarItem isCollapsed={isCollapsed} icon={<Database size={20} />} label="Vault" active={activeTab === 'vault'} onClick={() => navigate('/vault')} />
            <SidebarItem isCollapsed={isCollapsed} icon={<BarChart2 size={20} />} label="Analytics" active={activeTab === 'analytics'} onClick={() => navigate('/analytics')} />
            {isAdmin && <SidebarItem isCollapsed={isCollapsed} icon={<ShieldCheck size={20} />} label="Admin" active={activeTab === 'admin'} onClick={() => navigate('/admin')} />}
          </nav>
          
          <div className="mt-8">
            <button 
              onClick={() => navigate('/log')}
              title={isCollapsed ? 'Log Activity' : undefined}
              className={`kinetic-btn kinetic-accent-gradient w-full py-3 text-sm flex items-center justify-center gap-2 ${isCollapsed ? 'px-0' : ''}`}
            >
              <PlusSquare size={16} className="shrink-0" /> {!isCollapsed && <span className="whitespace-nowrap">Log Activity</span>}
            </button>
          </div>
        </div>

        {/* User Profile Area */}
        <div className={`w-full flex ${isCollapsed ? 'flex-col items-center' : 'flex-col'} gap-4 pt-6 border-t border-[rgba(15,23,42,0.08)]`}>
          {session ? (
            <>
              <div 
                onClick={() => navigate('/profile')}
                title={isCollapsed ? email : undefined}
                className={`flex items-center gap-3 cursor-pointer p-2 hover:bg-[rgba(15,23,42,0.03)] rounded transition-colors ${isCollapsed ? 'justify-center mx-0' : '-mx-2'}`}
              >
                <div className="h-8 w-8 bg-[#131b2e] rounded-full flex items-center justify-center text-xs font-mono font-medium text-white shrink-0">
                  {initials}
                </div>
                {!isCollapsed && <span className="text-sm font-semibold text-[#0F172A] truncate" title={email}>{email}</span>}
              </div>
              <button 
                onClick={handleSignOut}
                title={isCollapsed ? 'Sign Out' : undefined}
                className={`flex items-center gap-2 text-xs font-semibold text-[#64748B] hover:text-[#B91C1C] transition-colors ${isCollapsed ? 'justify-center p-2' : 'pl-2'}`}
              >
                <LogOut size={14} className="shrink-0" /> {!isCollapsed && 'Sign Out'}
              </button>
            </>
          ) : (
            <button 
              onClick={showAuthModal}
              title={isCollapsed ? 'Sign In to Save Data' : undefined}
              className={`flex items-center gap-2 text-sm font-semibold text-[#0891B2] hover:text-[#06B6D4] transition-colors ${isCollapsed ? 'justify-center p-2' : 'pl-2'}`}
            >
              <LogIn size={16} className="shrink-0" /> {!isCollapsed && 'Sign In'}
            </button>
          )}
        </div>
      </aside>

      {/* MAIN CONTENT AREA */}
      <div className="flex-1 flex flex-col h-full relative overflow-hidden">
        
        {/* Mobile Header (Hidden on md+) */}
        <header className="md:hidden px-4 py-4 border-b glass-nav sticky top-0 z-10 flex justify-between items-center">
          <div className="flex items-center gap-2" onClick={() => navigate('/dashboard')}>
            <Logo variant={logoVariant} className="h-6 w-auto" />
            <h1 className="font-sans font-semibold text-xl tracking-tight text-[#0F172A]">RetainHQ</h1>
          </div>
          <div className="flex items-center gap-3">
            {session ? (
              <>
                <button onClick={handleSignOut} className="text-[#64748B] hover:text-[#B91C1C]">
                  <LogOut size={18} />
                </button>
                <div 
                  onClick={() => navigate('/profile')}
                  className="h-8 w-8 bg-[#131b2e] rounded-full flex items-center justify-center text-xs font-mono font-medium text-white cursor-pointer"
                >
                  {initials}
                </div>
              </>
            ) : (
              <button onClick={showAuthModal} className="text-[#0891B2] text-sm font-semibold">
                Sign In
              </button>
            )}
          </div>
        </header>

        {/* Content Scrollable Area */}
        <main className="flex-1 overflow-y-auto w-full relative">
          <Routes>
            <Route path="dashboard" element={<Home onStartReviews={() => navigate('/reviews')} />} />
            <Route path="reviews" element={<Review onBack={() => navigate('/dashboard')} />} />
            <Route path="log" element={<LogActivity />} />
            <Route path="roadmaps" element={<Roadmaps />} />
            <Route path="roadmaps/:id" element={<RoadmapDetail />} />
            <Route path="vault" element={<KnowledgeVault />} />
            <Route path="analytics" element={<Analytics />} />
            <Route path="profile" element={<Profile />} />
            {isAdmin && <Route path="admin" element={<Admin />} />}
            {/* Fallback internal route — absolute path: a relative "dashboard" inside
                this splat route appends recursively (/dashboard/dashboard/...) into a loop. */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </main>

        {/* Mobile Bottom Navigation (Hidden on md+). `fixed` (not absolute) so it
            pins to the visible viewport bottom on real phones — an `absolute bottom-0`
            inside an h-screen/100vh container renders below the fold on mobile, where
            100vh is taller than the visible area (the classic mobile-100vh bug). Pages
            already reserve pb-20 for it. */}
        <nav className="md:hidden fixed inset-x-0 bottom-0 glass-nav border-t flex justify-around items-center px-2 py-3 z-30 pb-safe overflow-x-auto gap-1">
          <NavItem icon={<HomeIcon size={20} />} label="Home" active={activeTab === 'dashboard'} onClick={() => navigate('/dashboard')} />
          <NavItem icon={<CheckSquare size={20} />} label="Review" active={activeTab === 'review'} onClick={() => navigate('/reviews')} badge={dueCount} />
          <NavItem icon={<PlusSquare size={20} />} label="Log" active={activeTab === 'log'} onClick={() => navigate('/log')} />
          <NavItem icon={<Map size={20} />} label="Roadmaps" active={activeTab === 'roadmaps'} onClick={() => navigate('/roadmaps')} />
          <NavItem icon={<Database size={20} />} label="Vault" active={activeTab === 'vault'} onClick={() => navigate('/vault')} />
          <NavItem icon={<BarChart2 size={20} />} label="Analytics" active={activeTab === 'analytics'} onClick={() => navigate('/analytics')} />
          {isAdmin && <NavItem icon={<ShieldCheck size={20} />} label="Admin" active={activeTab === 'admin'} onClick={() => navigate('/admin')} />}
        </nav>

        {/* Floating Action Button — quick-log shortcut, desktop only (mobile has the Log tab in the bottom nav) */}
        <button
          aria-label="Log Activity"
          onClick={() => navigate('/log')}
          className="hidden md:flex fixed bottom-6 right-6 z-30 h-14 w-14 items-center justify-center rounded-full glass-nav border text-[#0891B2] shadow-lg hover:shadow-xl hover:-translate-y-0.5 active:translate-y-0 transition-all duration-150"
          style={{ boxShadow: '0 4px 20px -4px rgba(8,145,178,0.35), 0 2px 8px -2px rgba(15,23,42,0.15)' }}
        >
          <Plus size={24} strokeWidth={2.5} />
        </button>
      </div>
    </div>
  );
}

function SidebarItem({ icon, label, active, onClick, isCollapsed, badge = 0 }) {
  return (
    <button
      onClick={onClick}
      title={isCollapsed ? label : undefined}
      className={`flex items-center gap-3 py-3 rounded text-sm font-medium transition-colors w-full ${
        isCollapsed ? 'justify-center px-0' : 'px-4 text-left'
      } ${
        active ? 'bg-[rgba(15,23,42,0.05)] text-[#0891B2]' : 'text-[#64748B] hover:bg-[rgba(15,23,42,0.02)] hover:text-[#0F172A]'
      }`}
    >
      <div className="shrink-0 relative">
        {icon}
        {badge > 0 && isCollapsed && (
          <span className="absolute -top-1.5 -right-1.5 min-w-[16px] h-4 px-1 rounded-full bg-[#ba1a1a] text-white font-mono text-[9px] font-bold flex items-center justify-center">
            {badge > 9 ? '9+' : badge}
          </span>
        )}
      </div>
      {!isCollapsed && <span className="truncate flex-1">{label}</span>}
      {!isCollapsed && badge > 0 && (
        <span className="min-w-[20px] h-5 px-1.5 rounded-full bg-[#ba1a1a] text-white font-mono text-[10px] font-bold flex items-center justify-center shrink-0">
          {badge > 9 ? '9+' : badge}
        </span>
      )}
    </button>
  );
}

function NavItem({ icon, label, active, onClick, badge = 0 }) {
  return (
    <button
      onClick={onClick}
      className={`flex flex-col items-center justify-center w-16 gap-1 ${
        active ? 'text-[#0891B2]' : 'text-[#64748B] hover:text-[#0F172A]'
      } transition-colors`}
    >
      <div className="relative">
        {icon}
        {badge > 0 && (
          <span className="absolute -top-1.5 -right-2 min-w-[16px] h-4 px-1 rounded-full bg-[#ba1a1a] text-white font-mono text-[9px] font-bold flex items-center justify-center">
            {badge > 9 ? '9+' : badge}
          </span>
        )}
      </div>
      <span className="font-sans text-[10px] font-medium">{label}</span>
    </button>
  );
}

function Root() {
  const { session, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <div className="min-h-screen bg-[#f9f9f6] flex items-center justify-center font-sans text-[#64748B]">Loading...</div>;
  }

  return (
    <Routes>
      <Route 
        path="/" 
        element={session ? <Navigate to="/dashboard" replace /> : <Login />} 
      />
      <Route path="/*" element={<AppLayout />} />
    </Routes>
  );
}

function App() {
  return (
    <AuthProvider>
      <Root />
    </AuthProvider>
  );
}

export default App;
