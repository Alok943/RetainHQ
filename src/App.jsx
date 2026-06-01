import React from 'react';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { Home as HomeIcon, CheckSquare, PlusSquare, Map, BarChart2 } from 'lucide-react';
import Home from './Home';
import Review from './Review';
import LogActivity from './LogActivity';
import Roadmaps from './Roadmaps';
import Analytics from './Analytics';
import RoadmapDetail from './RoadmapDetail';

function App() {
  const location = useLocation();
  const navigate = useNavigate();
  
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

  return (
    <div className="flex h-screen w-full bg-[#f9f9f6] overflow-hidden text-[#1a1c1b] font-sans">
      
      {/* LEFT SIDEBAR (Desktop / Tablet) */}
      <aside className="hidden md:flex flex-col w-[240px] border-r border-[rgba(15,23,42,0.08)] bg-[#f9f9f6] p-6 shrink-0 justify-between">
        <div>
          <div className="mb-10">
            <h1 className="font-sans font-semibold text-2xl tracking-tight text-[#0F172A] cursor-pointer" onClick={() => navigate('/')}>RetainHQ</h1>
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
        <div className="flex items-center gap-3 pt-6 border-t border-[rgba(15,23,42,0.08)]">
          <div className="h-8 w-8 bg-[#131b2e] rounded-full flex items-center justify-center text-xs font-mono font-medium text-white">
            AL
          </div>
          <span className="text-sm font-semibold text-[#0F172A]">Alok S.</span>
        </div>
      </aside>

      {/* MAIN CONTENT AREA */}
      <div className="flex-1 flex flex-col h-full relative overflow-hidden">
        
        {/* Mobile Header (Hidden on md+) */}
        <header className="md:hidden px-4 py-4 border-b border-[rgba(15,23,42,0.08)] bg-[#f9f9f6] sticky top-0 z-10 flex justify-between items-center">
          <h1 className="font-sans font-semibold text-xl tracking-tight text-[#0F172A]" onClick={() => navigate('/')}>RetainHQ</h1>
          <div className="h-8 w-8 bg-[#131b2e] rounded-full flex items-center justify-center text-xs font-mono font-medium text-white">
            AL
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
