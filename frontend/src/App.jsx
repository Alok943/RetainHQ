import React, { useState, useEffect, Suspense, lazy } from 'react';
import { Routes, Route, useNavigate, useLocation, Navigate } from 'react-router-dom';
import { LayoutDashboard, Brain, GraduationCap, Library, TrendingUp, PlusSquare, LogOut, ShieldCheck, LogIn, Plus } from 'lucide-react';
import { supabase } from './lib/supabase';
import { useTheme } from './lib/theme';
import { AuthProvider, useAuth } from './lib/AuthContext';
import { apiFetch } from './lib/api';
import { pageview } from './lib/analytics';

// Login is the public landing/LCP page — keep it eager so it paints without a
// chunk round-trip. Logo is tiny chrome used everywhere. Everything else is an
// authed route lazy-loaded on demand, which keeps the heavy libs (React Flow +
// dagre on roadmaps, jsPDF + html2canvas on roadmap detail) out of the initial
// bundle the landing page has to download.
import Login from './Login';
import Logo from './Logo';
import WelcomeModal from './WelcomeModal';

const Home = lazy(() => import('./Home'));
const Review = lazy(() => import('./Review'));
const LogActivity = lazy(() => import('./LogActivity'));
const Roadmaps = lazy(() => import('./Roadmaps'));
const Analytics = lazy(() => import('./Analytics'));
const RoadmapDetail = lazy(() => import('./RoadmapDetail'));
const LessonView = lazy(() => import('./LessonView'));
const Profile = lazy(() => import('./Profile'));
const KnowledgeVault = lazy(() => import('./KnowledgeVault'));
const Admin = lazy(() => import('./Admin'));
const DsaDev = lazy(() => import('./dsa/DsaDev')); // TEMP: DSA pilot harness (/dsa-dev)

const ADMIN_EMAIL = 'aloksingh98541@gmail.com';

function AppLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const { theme } = useTheme();
  const { session, showAuthModal } = useAuth();
  
  // Floating sidebar: an icon rail by default, expands to a labelled panel on
  // hover and floats over content (never reflows the page).
  const [hovered, setHovered] = useState(false);
  const isCollapsed = !hovered;

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
    <div className="relative flex h-screen w-full bg-[#f9f9f6] overflow-hidden text-[#1a1c1b] font-sans">
      {/* First-visit explainer for guests — shown on the Home page only (the landing
          page no longer renders it; there it covered the hero). Logged-in first-runs
          use FirstCapture instead. Shown once per browser via a shared localStorage flag. */}
      {!session && activeTab === 'dashboard' && <WelcomeModal />}

      {/* LEFT SIDEBAR (Desktop / Tablet) — floating icon rail that expands on hover.
          The spacer holds the collapsed footprint so content never sits under the rail;
          the aside is absolutely positioned and floats over content while expanded. */}
      <div className="hidden md:block w-[84px] shrink-0" aria-hidden="true" />
      <aside
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        className={`hidden md:flex flex-col border-r glass-nav justify-between transition-all duration-300 ease-out absolute inset-y-0 left-0 z-40 ${isCollapsed ? 'w-[84px] items-center p-6 px-4' : 'w-[240px] p-6 shadow-2xl shadow-[rgba(15,23,42,0.18)]'}`}
      >
        <div className="w-full">
          <div className={`flex items-center mb-10 ${isCollapsed ? 'flex-col gap-4' : ''}`}>
            <div className="flex items-center gap-2.5 cursor-pointer overflow-hidden" onClick={() => navigate('/dashboard')}>
              <Logo variant={logoVariant} className="h-7 w-auto shrink-0" />
              {!isCollapsed && <h1 className="font-sans font-semibold text-2xl tracking-tight text-[#0F172A] whitespace-nowrap">RetainHQ</h1>}
            </div>
          </div>

          <nav className={`flex flex-col gap-2 ${isCollapsed ? 'items-center' : ''}`}>
            <SidebarItem isCollapsed={isCollapsed} icon={<LayoutDashboard size={20} />} label="Home" active={activeTab === 'dashboard'} onClick={() => navigate('/dashboard')} />
            <SidebarItem isCollapsed={isCollapsed} icon={<Brain size={20} />} label="Reviews" active={activeTab === 'review'} onClick={() => navigate('/reviews')} badge={dueCount} />
            <SidebarItem isCollapsed={isCollapsed} icon={<GraduationCap size={20} />} label="Learn" active={activeTab === 'roadmaps'} onClick={() => navigate('/roadmaps')} />
            <SidebarItem isCollapsed={isCollapsed} icon={<Library size={20} />} label="Vault" active={activeTab === 'vault'} onClick={() => navigate('/vault')} />
            <SidebarItem isCollapsed={isCollapsed} icon={<TrendingUp size={20} />} label="Analytics" active={activeTab === 'analytics'} onClick={() => navigate('/analytics')} />
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
          <Suspense fallback={<div className="w-full py-24 flex items-center justify-center font-sans text-sm text-[#64748B]">Loading…</div>}>
          <Routes>
            <Route path="dashboard" element={<Home onStartReviews={() => navigate('/reviews')} />} />
            <Route path="reviews" element={<Review onBack={() => navigate('/dashboard')} />} />
            <Route path="log" element={<LogActivity />} />
            <Route path="roadmaps" element={<Roadmaps />} />
            <Route path="roadmaps/:id" element={<RoadmapDetail />} />
            <Route path="roadmaps/:id/learn/:slug" element={<LessonView />} />
            <Route path="dsa-dev" element={<DsaDev />} />
            <Route path="vault" element={<KnowledgeVault />} />
            <Route path="analytics" element={<Analytics />} />
            <Route path="profile" element={<Profile />} />
            {isAdmin && <Route path="admin" element={<Admin />} />}
            {/* Fallback internal route — absolute path: a relative "dashboard" inside
                this splat route appends recursively (/dashboard/dashboard/...) into a loop. */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
          </Suspense>
        </main>

        {/* Mobile Bottom Navigation (Hidden on md+). `fixed` (not absolute) so it
            pins to the visible viewport bottom on real phones — an `absolute bottom-0`
            inside an h-screen/100vh container renders below the fold on mobile, where
            100vh is taller than the visible area (the classic mobile-100vh bug). Pages
            already reserve pb-20 for it. */}
        <nav className="md:hidden fixed inset-x-0 bottom-0 glass-nav border-t flex justify-around items-center px-2 py-3 z-30 pb-safe overflow-x-auto gap-1">
          <NavItem icon={<LayoutDashboard size={20} />} label="Home" active={activeTab === 'dashboard'} onClick={() => navigate('/dashboard')} />
          <NavItem icon={<Brain size={20} />} label="Review" active={activeTab === 'review'} onClick={() => navigate('/reviews')} badge={dueCount} />
          <NavItem icon={<PlusSquare size={20} />} label="Log" active={activeTab === 'log'} onClick={() => navigate('/log')} />
          <NavItem icon={<GraduationCap size={20} />} label="Learn" active={activeTab === 'roadmaps'} onClick={() => navigate('/roadmaps')} />
          <NavItem icon={<Library size={20} />} label="Vault" active={activeTab === 'vault'} onClick={() => navigate('/vault')} />
          <NavItem icon={<TrendingUp size={20} />} label="Analytics" active={activeTab === 'analytics'} onClick={() => navigate('/analytics')} />
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

  // SPA pageviews (autocapture is off) — fire on every path change.
  useEffect(() => {
    pageview(location.pathname);
  }, [location.pathname]);

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
