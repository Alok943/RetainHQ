import React from 'react';
import { Routes, Route, useNavigate, useLocation, Navigate } from 'react-router-dom';
import { Home as HomeIcon, CheckSquare, PlusSquare, Map, BarChart2, LogOut, Database, ShieldCheck, LogIn } from 'lucide-react';
import { supabase } from './lib/supabase';
import { useTheme } from './lib/theme';
import { AuthProvider, useAuth } from './lib/AuthContext';

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
      <aside className="hidden md:flex flex-col w-[240px] border-r border-[rgba(15,23,42,0.08)] bg-[#f9f9f6] p-6 shrink-0 justify-between">
        <div>
          <div className="mb-10">
            <div className="flex items-center gap-2.5 cursor-pointer w-max" onClick={() => navigate('/dashboard')}>
              <Logo variant={logoVariant} className="h-7 w-auto" />
              <h1 className="font-sans font-semibold text-2xl tracking-tight text-[#0F172A]">RetainHQ</h1>
            </div>
          </div>
          
          <nav className="flex flex-col gap-2">
            <SidebarItem icon={<HomeIcon size={20} />} label="Home" active={activeTab === 'dashboard'} onClick={() => navigate('/dashboard')} />
            <SidebarItem icon={<CheckSquare size={20} />} label="Reviews" active={activeTab === 'review'} onClick={() => navigate('/reviews')} />
            <SidebarItem icon={<Map size={20} />} label="Roadmaps" active={activeTab === 'roadmaps'} onClick={() => navigate('/roadmaps')} />
            <SidebarItem icon={<Database size={20} />} label="Vault" active={activeTab === 'vault'} onClick={() => navigate('/vault')} />
            <SidebarItem icon={<BarChart2 size={20} />} label="Analytics" active={activeTab === 'analytics'} onClick={() => navigate('/analytics')} />
            {isAdmin && <SidebarItem icon={<ShieldCheck size={20} />} label="Admin" active={activeTab === 'admin'} onClick={() => navigate('/admin')} />}
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
          {session ? (
            <>
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
            </>
          ) : (
            <button 
              onClick={showAuthModal}
              className="flex items-center gap-2 text-sm font-semibold text-[#0891B2] hover:text-[#06B6D4] transition-colors pl-2"
            >
              <LogIn size={16} /> Sign In to Save Data
            </button>
          )}
        </div>
      </aside>

      {/* MAIN CONTENT AREA */}
      <div className="flex-1 flex flex-col h-full relative overflow-hidden">
        
        {/* Mobile Header (Hidden on md+) */}
        <header className="md:hidden px-4 py-4 border-b border-[rgba(15,23,42,0.08)] bg-[#f9f9f6] sticky top-0 z-10 flex justify-between items-center">
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
            {/* Fallback internal route */}
            <Route path="*" element={<Navigate to="dashboard" replace />} />
          </Routes>
        </main>

        {/* Mobile Bottom Navigation (Hidden on md+) */}
        <nav className="md:hidden absolute bottom-0 w-full bg-[#f9f9f6] border-t border-[rgba(15,23,42,0.08)] flex justify-around items-center px-2 py-3 z-20 pb-safe overflow-x-auto gap-1">
          <NavItem icon={<HomeIcon size={20} />} label="Home" active={activeTab === 'dashboard'} onClick={() => navigate('/dashboard')} />
          <NavItem icon={<CheckSquare size={20} />} label="Review" active={activeTab === 'review'} onClick={() => navigate('/reviews')} />
          <NavItem icon={<PlusSquare size={20} />} label="Log" active={activeTab === 'log'} onClick={() => navigate('/log')} />
          <NavItem icon={<Map size={20} />} label="Roadmaps" active={activeTab === 'roadmaps'} onClick={() => navigate('/roadmaps')} />
          <NavItem icon={<Database size={20} />} label="Vault" active={activeTab === 'vault'} onClick={() => navigate('/vault')} />
          <NavItem icon={<BarChart2 size={20} />} label="Analytics" active={activeTab === 'analytics'} onClick={() => navigate('/analytics')} />
          {isAdmin && <NavItem icon={<ShieldCheck size={20} />} label="Admin" active={activeTab === 'admin'} onClick={() => navigate('/admin')} />}
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
