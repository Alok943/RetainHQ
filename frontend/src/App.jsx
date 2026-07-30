import React, { useState, useEffect, Suspense, lazy } from 'react';
import { Routes, Route, useNavigate, useLocation, Navigate, Link } from 'react-router-dom';
import { LayoutDashboard, Brain, GraduationCap, Library, TrendingUp, PlusSquare, LogOut, ShieldCheck, LogIn, Plus, Route as RouteIcon, MoreHorizontal, Presentation, Compass } from 'lucide-react';
import { supabase } from './lib/supabase';
import { useTheme } from './lib/theme';
import { AuthProvider, useAuth } from './lib/AuthContext';
import { ClassroomsProvider, useClassrooms } from './lib/ClassroomsContext';
import { ToastProvider } from './lib/ToastContext';
import { apiFetch } from './lib/api';
import { pageview, trackOnce, EVENTS } from './lib/analytics';

// Login is the public landing/LCP page — keep it eager so it paints without a
// chunk round-trip. Logo is tiny chrome used everywhere. Everything else is an
// authed route lazy-loaded on demand, which keeps the heavy libs (React Flow +
// dagre on roadmaps, jsPDF + html2canvas on roadmap detail) out of the initial
// bundle the landing page has to download.
import Login from './Login';
import Logo from './Logo';
import WelcomeModal from './WelcomeModal';
import JoinClassroom from './JoinClassroom';
import PrivacyCompanion from './PrivacyCompanion';

const Home = lazy(() => import('./Home'));
const Review = lazy(() => import('./Review'));
const LogActivity = lazy(() => import('./LogActivity'));
const Roadmaps = lazy(() => import('./Roadmaps'));
const SyllabusUpload = lazy(() => import('./SyllabusUpload'));
const CareerPaths = lazy(() => import('./CareerPaths'));
const CareerCoach = lazy(() => import('./CareerCoach')); // Career Coach Phase 2 (SPEC-career-coach-phase2.md)
const Analytics = lazy(() => import('./Analytics'));
const RoadmapDetail = lazy(() => import('./RoadmapDetail'));
const LessonView = lazy(() => import('./LessonView'));
const Profile = lazy(() => import('./Profile'));
const KnowledgeVault = lazy(() => import('./KnowledgeVault'));
const Admin = lazy(() => import('./Admin'));
const Evidence = lazy(() => import('./Evidence')); // Dev-only instrument (SPEC-career-coach-phase1 §7-8)
const DsaDev = lazy(() => import('./dsa/DsaDev')); // TEMP: DSA pilot harness (/dsa-dev)
const PhysicsNumericals = lazy(() => import('./PhysicsNumericals'));
const Tests = lazy(() => import('./Tests'));
const Teach = lazy(() => import('./Teach'));
const TeachClassroom = lazy(() => import('./TeachClassroom'));
const TeachStudentDetail = lazy(() => import('./TeachStudentDetail'));

const ADMIN_EMAIL = 'aloksingh98541@gmail.com';

function AppLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const { theme } = useTheme();
  const { session, showAuthModal } = useAuth();
  
  // Floating sidebar: an icon rail by default, expands to a labelled panel on
  // hover and floats over content (never reflows the page). Exception: on Home
  // it is OPEN by default — there the spacer widens too, so the expanded panel
  // is structural (content reflows beside it) instead of floating over it.
  const [hovered, setHovered] = useState(false);

  const [showMoreMenu, setShowMoreMenu] = useState(false);

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

  // "Teach" nav entry only shows once the caller actually teaches a class
  // (no role column — spec §2: "is a teacher" == "owns >=1 classroom"). Read
  // from the shared ClassroomsContext so we don't refetch /mine on every route
  // change; the context refreshes when a class is created or left.
  const { classrooms } = useClassrooms();
  const teachingCount = classrooms?.teaching?.length ?? 0;

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
    if (path.startsWith('/paths')) return 'paths';
    if (path.startsWith('/coach')) return 'coach';
    if (path.startsWith('/vault')) return 'vault';
    if (path.startsWith('/analytics')) return 'analytics';
    if (path.startsWith('/teach')) return 'teach';
    if (path.startsWith('/admin')) return 'admin';
    return 'dashboard';
  };

  const activeTab = getActiveTab();
  const isMoreActive = ['paths', 'coach', 'vault', 'analytics', 'teach', 'admin'].includes(activeTab);

  // Home shows the sidebar open; everywhere else it stays the hover-expand rail.
  const sidebarDefaultOpen = activeTab === 'dashboard';
  const isCollapsed = !hovered && !sidebarDefaultOpen;

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
      <div className={`hidden md:block shrink-0 transition-all duration-300 ease-out ${sidebarDefaultOpen ? 'w-[240px]' : 'w-[84px]'}`} aria-hidden="true" />
      <aside
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        className={`hidden md:flex flex-col border-r glass-nav justify-between transition-all duration-300 ease-out absolute inset-y-0 left-0 z-40 ${isCollapsed ? 'w-[84px] items-center p-6 px-4' : `w-[240px] p-6 ${sidebarDefaultOpen ? '' : 'shadow-2xl shadow-[rgba(15,23,42,0.18)]'}`}`}
      >
        <div className="w-full">
          <div className={`flex items-center mb-10 ${isCollapsed ? 'flex-col gap-4' : ''}`}>
            <Link to="/dashboard" className="flex items-center gap-2.5 cursor-pointer overflow-hidden">
              <Logo variant={logoVariant} className="h-7 w-auto shrink-0" />
              {!isCollapsed && <h1 className="font-sans font-semibold text-2xl tracking-tight text-[#0F172A] whitespace-nowrap">RetainHQ</h1>}
            </Link>
          </div>

          <nav className={`flex flex-col gap-2 ${isCollapsed ? 'items-center' : ''}`}>
            <SidebarItem isCollapsed={isCollapsed} icon={<LayoutDashboard size={20} />} label="Home" active={activeTab === 'dashboard'} to="/dashboard" />
            <SidebarItem isCollapsed={isCollapsed} icon={<Brain size={20} />} label="Reviews" active={activeTab === 'review'} to="/reviews" badge={dueCount} />
            <SidebarItem isCollapsed={isCollapsed} icon={<GraduationCap size={20} />} label="Learn" active={activeTab === 'roadmaps'} to="/roadmaps" />
            <SidebarItem isCollapsed={isCollapsed} icon={<RouteIcon size={20} />} label="Career Paths" active={activeTab === 'paths'} to="/paths" />
            <SidebarItem isCollapsed={isCollapsed} icon={<Compass size={20} />} label="Career Coach" active={activeTab === 'coach'} to="/coach" />
            <SidebarItem isCollapsed={isCollapsed} icon={<Library size={20} />} label="Vault" active={activeTab === 'vault'} to="/vault" />
            <SidebarItem isCollapsed={isCollapsed} icon={<TrendingUp size={20} />} label="Analytics" active={activeTab === 'analytics'} to="/analytics" />
            {teachingCount > 0 && <SidebarItem isCollapsed={isCollapsed} icon={<Presentation size={20} />} label="Teach" active={activeTab === 'teach'} to="/teach" />}
            {isAdmin && <SidebarItem isCollapsed={isCollapsed} icon={<ShieldCheck size={20} />} label="Admin" active={activeTab === 'admin'} to="/admin" />}
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
          <Link to="/dashboard" className="flex items-center gap-2">
            <Logo variant={logoVariant} className="h-6 w-auto" />
            <h1 className="font-sans font-semibold text-xl tracking-tight text-[#0F172A]">RetainHQ</h1>
          </Link>
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
          <Suspense fallback={
            <div className="max-w-4xl mx-auto w-full p-4 md:p-8 flex flex-col gap-4">
              <div className="skeleton h-6 w-48" />
              <div className="skeleton h-3 w-72" />
              <div className="skeleton h-32 w-full rounded-xl mt-2" />
              <div className="skeleton h-32 w-full rounded-xl" />
            </div>
          }>
          <Routes>
            <Route path="dashboard" element={<Home onStartReviews={() => navigate('/reviews')} />} />
            <Route path="reviews" element={<Review onBack={() => navigate('/dashboard')} />} />
            <Route path="log" element={<LogActivity />} />
            <Route path="roadmaps" element={<Roadmaps />} />
            <Route path="roadmaps/new" element={<SyllabusUpload />} />
            <Route path="roadmaps/:id" element={<RoadmapDetail />} />
            <Route path="roadmaps/:id/learn/:slug" element={<LessonView />} />
            <Route path="roadmaps/:roadmapSlug/numericals/:phaseSlug" element={<PhysicsNumericals />} />
            <Route path="roadmaps/:roadmapSlug/test/:phaseSlug" element={<Tests />} />
            <Route path="paths" element={<CareerPaths />} />
            <Route path="coach" element={<CareerCoach />} />
            <Route path="dsa-dev" element={<DsaDev />} />
            <Route path="vault" element={<KnowledgeVault />} />
            <Route path="analytics" element={<Analytics />} />
            <Route path="teach" element={<Teach />} />
            <Route path="teach/:id" element={<TeachClassroom />} />
            <Route path="teach/:id/students/:memberId" element={<TeachStudentDetail />} />
            <Route path="profile" element={<Profile />} />
            {isAdmin && <Route path="admin" element={<Admin />} />}
            {isAdmin && <Route path="evidence" element={<Evidence />} />}
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
        <nav className="md:hidden fixed inset-x-0 bottom-0 glass-nav border-t flex justify-around items-center px-2 py-3 z-30 pb-safe gap-1">
          <NavItem icon={<LayoutDashboard size={20} />} label="Home" active={activeTab === 'dashboard'} onClick={() => setShowMoreMenu(false)} to="/dashboard" />
          <NavItem icon={<Brain size={20} />} label="Review" active={activeTab === 'review'} onClick={() => setShowMoreMenu(false)} to="/reviews" badge={dueCount} />
          
          <button
            onClick={() => { setShowMoreMenu(false); navigate('/log'); }}
            className="flex flex-col items-center justify-center w-16 gap-1 transition-colors"
          >
            <div className={`h-10 w-10 flex items-center justify-center rounded-full ${activeTab === 'log' ? 'bg-[#0891B2] text-white' : 'bg-[rgba(8,145,178,0.1)] text-[#0891B2] hover:bg-[rgba(8,145,178,0.2)]'}`}>
              <Plus size={22} strokeWidth={2.5} />
            </div>
            <span className={`font-sans text-[10px] font-medium ${activeTab === 'log' ? 'text-[#0891B2]' : 'text-[#64748B]'}`}>Log</span>
          </button>
          
          <NavItem icon={<GraduationCap size={20} />} label="Learn" active={activeTab === 'roadmaps'} onClick={() => setShowMoreMenu(false)} to="/roadmaps" />
          
          <div className="relative flex flex-col items-center justify-center w-16">
            <NavItem 
              icon={<MoreHorizontal size={20} />} 
              label="More" 
              active={showMoreMenu || isMoreActive} 
              onClick={() => setShowMoreMenu(!showMoreMenu)} 
            />
            {showMoreMenu && (
              <>
                {/* Invisible backdrop to close the menu on outside click */}
                <div className="fixed inset-0 z-40" onClick={() => setShowMoreMenu(false)} />
                <div className="absolute bottom-[100%] right-0 mb-3 bg-white border border-[rgba(15,23,42,0.08)] shadow-lg rounded-xl flex flex-col w-48 overflow-hidden z-50 animate-in fade-in slide-in-from-bottom-2 duration-150">
                  <MenuButton icon={<RouteIcon size={16} />} label="Career Paths" active={activeTab === 'paths'} onClick={() => setShowMoreMenu(false)} to="/paths" />
                  <MenuButton icon={<Compass size={16} />} label="Career Coach" active={activeTab === 'coach'} onClick={() => setShowMoreMenu(false)} to="/coach" />
                  <MenuButton icon={<Library size={16} />} label="Vault" active={activeTab === 'vault'} onClick={() => setShowMoreMenu(false)} to="/vault" />
                  <MenuButton icon={<TrendingUp size={16} />} label="Analytics" active={activeTab === 'analytics'} onClick={() => setShowMoreMenu(false)} to="/analytics" />
                  {teachingCount > 0 && <MenuButton icon={<Presentation size={16} />} label="Teach" active={activeTab === 'teach'} onClick={() => setShowMoreMenu(false)} to="/teach" />}
                  {isAdmin && <MenuButton icon={<ShieldCheck size={16} />} label="Admin" active={activeTab === 'admin'} onClick={() => setShowMoreMenu(false)} to="/admin" />}
                </div>
              </>
            )}
          </div>
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

function SidebarItem({ icon, label, active, onClick, to, isCollapsed, badge = 0 }) {
  const Component = to ? Link : 'button';
  return (
    <Component
      onClick={onClick}
      to={to}
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
    </Component>
  );
}

function NavItem({ icon, label, active, onClick, to, badge = 0 }) {
  const Component = to ? Link : 'button';
  return (
    <Component
      onClick={onClick}
      to={to}
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
    </Component>
  );
}

function MenuButton({ icon, label, active, onClick, to }) {
  const Component = to ? Link : 'button';
  return (
    <Component
      onClick={onClick}
      to={to}
      className={`flex items-center gap-3 px-4 py-3 text-sm font-medium transition-colors ${
        active ? 'bg-[rgba(15,23,42,0.05)] text-[#0891B2]' : 'text-[#64748B] hover:bg-[rgba(15,23,42,0.02)] hover:text-[#0F172A]'
      }`}
    >
      <div className="shrink-0">{icon}</div>
      <span className="truncate flex-1 text-left">{label}</span>
    </Component>
  );
}

function Root() {
  const { session, loading } = useAuth();
  const location = useLocation();

  // SPA pageviews (autocapture is off) — fire on every path change.
  useEffect(() => {
    pageview(location.pathname);
  }, [location.pathname]);

  // Reminder-email attribution: a visit carrying ?src=reminder is an email click.
  // Pairs with the server's reminder_sent to give email CTR. Once per load.
  useEffect(() => {
    if (new URLSearchParams(location.search).get('src') === 'reminder') {
      trackOnce('reminder_clicked', EVENTS.REMINDER_CLICKED);
    }
  }, []);

  // Warm the core-loop route chunks in priority order once idle, so the first
  // real navigation after login doesn't pay a chunk round-trip. Same import()
  // specifiers as the lazy() calls above, so Vite serves these from cache
  // instead of double-fetching.
  useEffect(() => {
    if (!session) return;
    const prefetch = [
      () => import('./Home'),
      () => import('./Review'),
      () => import('./Roadmaps'),
      () => import('./Profile'),
    ];
    let cancelled = false;
    const schedule = window.requestIdleCallback || ((cb) => setTimeout(cb, 200));
    function next(i) {
      if (cancelled || i >= prefetch.length) return;
      schedule(() => prefetch[i]().finally(() => next(i + 1)));
    }
    next(0);
    return () => { cancelled = true; };
  }, [session]);

  if (loading) {
    return <div className="min-h-screen bg-[#f9f9f6] flex items-center justify-center font-sans text-[#64748B]">Loading...</div>;
  }

  return (
    <Routes>
      <Route
        path="/"
        element={session ? <Navigate to="/dashboard" replace /> : <Login />}
      />
      {/* Top-level (outside AppLayout) — a student may follow a join code before
          ever signing in, so this can't sit behind the authed shell's routing. */}
      <Route path="/join/:code" element={<JoinClassroom />} />
      {/* Public AMO/reviewer-facing policy page — no session check, no app shell
          (IMPLEMENTATION-amo-submission.md §1: must be reachable without logging in). */}
      <Route path="/privacy/companion" element={<PrivacyCompanion />} />
      <Route path="/*" element={<AppLayout />} />
    </Routes>
  );
}

function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <ClassroomsProvider>
          <Root />
        </ClassroomsProvider>
      </AuthProvider>
    </ToastProvider>
  );
}

export default App;
