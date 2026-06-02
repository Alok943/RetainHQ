import React from 'react';
import { BarChart2, TrendingUp, Calendar, Zap, BrainCircuit, CheckSquare, Target } from 'lucide-react';

function Analytics() {
  return (
    <div className="flex flex-col lg:flex-row gap-8 p-4 md:p-8 max-w-6xl mx-auto w-full pb-20 md:pb-8 animate-in fade-in duration-300">
      
      {/* MAIN CONTENT AREA */}
      <div className="flex-1 flex flex-col gap-8 min-w-0">
        
        <header className="mb-2">
          <h2 className="font-sans text-2xl font-semibold text-[#0F172A] flex items-center gap-2">
            <BarChart2 size={24} className="text-[#0891B2]" /> Analytics & Retention
          </h2>
          <p className="font-sans text-sm text-[#64748B] mt-1">Visualize your knowledge health and review compliance over time.</p>
        </header>

        {/* HERO: LEARNING MOMENTUM */}
        <section>
          <div className="kinetic-card border-l-4 border-l-[#0891B2] flex flex-col md:flex-row justify-between md:items-center gap-6 bg-[#131b2e] border-[#131b2e] p-8">
            <div className="flex flex-col gap-4">
              <div className="flex justify-between items-start">
                <h3 className="font-sans text-sm font-semibold text-[#7c839b] uppercase tracking-widest">Learning Momentum</h3>
              </div>
              
              <div className="flex items-center gap-6">
                <div className="font-mono text-7xl font-medium text-white tracking-tighter">
                  82
                </div>
                <div className="flex flex-col gap-2">
                  <span className="font-sans text-xs font-bold text-[#0891B2] bg-[#0891B2]/20 px-2.5 py-1 rounded-full flex items-center gap-1 tracking-normal border border-[#0891B2]/30 uppercase w-max">
                    <TrendingUp size={12} /> Healthy
                  </span>
                  <div className="font-mono text-sm text-[#0891B2] flex items-center gap-1 font-semibold">
                    +6 This Week
                  </div>
                </div>
              </div>
            </div>
            
            {/* Context Stats inside Hero */}
            <div className="flex flex-col gap-4 w-full md:w-auto border-t md:border-t-0 md:border-l border-[rgba(255,255,255,0.1)] pt-6 md:pt-0 md:pl-8">
              <div className="flex justify-between items-center gap-12">
                <span className="font-sans text-xs font-semibold text-[#7c839b] uppercase tracking-widest">Consistency</span>
                <span className="font-mono text-lg text-white">6 / 7</span>
              </div>
              <div className="flex justify-between items-center gap-12">
                <span className="font-sans text-xs font-semibold text-[#7c839b] uppercase tracking-widest">Compliance</span>
                <span className="font-mono text-lg text-white">94%</span>
              </div>
            </div>
          </div>
        </section>

        {/* TOP STATS */}
        <div className="grid grid-cols-2 gap-4">
          <StatCard title="Knowledge Health" value="Strong" icon={<BrainCircuit size={16} />} color="#0F766E" sub="124 Retained" />
          <StatCard title="Total Reviews" value="1,402" icon={<Zap size={16} />} color="#B45309" sub="All Time" />
        </div>

        {/* CHARTS AREA 1 */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
          
          <div className="kinetic-card bg-white h-72 flex flex-col">
            <h3 className="font-sans text-sm font-semibold text-[#0F172A] mb-4">Retention Strength</h3>
            <div className="flex-1 flex items-end gap-4 p-4 border-b border-l border-[rgba(15,23,42,0.08)]">
              {/* Fake chart bars */}
              <div className="w-1/4 bg-[#B91C1C] h-[10%] rounded-t opacity-90 relative group hover:opacity-100 transition-opacity cursor-pointer">
                <span className="absolute -top-6 left-1/2 -translate-x-1/2 text-xs font-mono text-[#0F172A] opacity-0 group-hover:opacity-100 transition-opacity">12</span>
              </div>
              <div className="w-1/4 bg-[#B45309] h-[35%] rounded-t opacity-90 relative group hover:opacity-100 transition-opacity cursor-pointer">
                <span className="absolute -top-6 left-1/2 -translate-x-1/2 text-xs font-mono text-[#0F172A] opacity-0 group-hover:opacity-100 transition-opacity">45</span>
              </div>
              <div className="w-1/4 bg-[#0891B2] h-[80%] rounded-t opacity-90 relative group hover:opacity-100 transition-opacity cursor-pointer">
                <span className="absolute -top-6 left-1/2 -translate-x-1/2 text-xs font-mono text-[#0F172A] opacity-0 group-hover:opacity-100 transition-opacity">110</span>
              </div>
              <div className="w-1/4 bg-[#0F766E] h-[60%] rounded-t opacity-90 relative group hover:opacity-100 transition-opacity cursor-pointer">
                <span className="absolute -top-6 left-1/2 -translate-x-1/2 text-xs font-mono text-[#0F172A] opacity-0 group-hover:opacity-100 transition-opacity">84</span>
              </div>
            </div>
            <div className="flex justify-between mt-3 px-2 font-mono text-[10px] text-[#64748B] uppercase">
              <span>Weak</span>
              <span>Dev</span>
              <span>Strong</span>
              <span>Mastered</span>
            </div>
          </div>

          <div className="kinetic-card bg-white h-72 flex flex-col">
            <h3 className="font-sans text-sm font-semibold text-[#0F172A] mb-4">Daily Activity</h3>
            <div className="flex-1 flex items-end gap-2 p-4 border-b border-l border-[rgba(15,23,42,0.08)]">
              {/* Fake chart bars */}
              {[40, 20, 60, 80, 50, 90, 70].map((h, i) => (
                <div key={i} className="flex-1 bg-[rgba(15,23,42,0.1)] hover:bg-[#0F172A] rounded-t transition-colors cursor-pointer" style={{ height: `${h}%` }}></div>
              ))}
            </div>
            <div className="flex justify-between mt-3 px-2 font-mono text-[10px] text-[#64748B] uppercase">
              <span>Mon</span>
              <span>Sun</span>
            </div>
          </div>

        </section>

        {/* CHARTS AREA 2: Track Balance */}
        <section>
          <div className="kinetic-card bg-white flex flex-col">
            <div className="flex justify-between items-center mb-6">
              <h3 className="font-sans text-sm font-semibold text-[#0F172A] flex items-center gap-2">
                <Target size={16} className="text-[#0891B2]" /> Track Balance
              </h3>
              <span className="font-sans text-xs font-medium text-[#64748B]">Last 30 Days</span>
            </div>
            
            <div className="w-full h-4 rounded-full overflow-hidden flex bg-[rgba(15,23,42,0.05)] mb-6">
              <div className="h-full bg-[#0F172A]" style={{ width: '60%' }} title="Placement Prep 2026: 60%" />
              <div className="h-full bg-[#0891B2]" style={{ width: '30%' }} title="Personal Dev: 30%" />
              <div className="h-full bg-[#B45309]" style={{ width: '10%' }} title="Misc: 10%" />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 rounded-full bg-[#0F172A]"></div>
                <div className="flex flex-col">
                  <span className="font-sans text-sm font-semibold text-[#0F172A]">Placement Prep 2026</span>
                  <span className="font-mono text-xs text-[#64748B]">60% (84 Topics)</span>
                </div>
              </div>
              
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 rounded-full bg-[#0891B2]"></div>
                <div className="flex flex-col">
                  <span className="font-sans text-sm font-semibold text-[#0F172A]">Personal Dev</span>
                  <span className="font-mono text-xs text-[#64748B]">30% (42 Topics)</span>
                </div>
              </div>
              
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 rounded-full bg-[#B45309]"></div>
                <div className="flex flex-col">
                  <span className="font-sans text-sm font-semibold text-[#0F172A]">Uncategorized</span>
                  <span className="font-mono text-xs text-[#64748B]">10% (14 Topics)</span>
                </div>
              </div>
            </div>
          </div>
        </section>

      </div>

    </div>
  );
}

function StatCard({ title, value, sub, icon, color }) {
  return (
    <div className="kinetic-card bg-white p-4 border-t-2" style={{ borderTopColor: color }}>
      <div className="flex justify-between items-start mb-2">
        <h3 className="font-sans text-[10px] font-bold text-[#64748B] uppercase tracking-widest">{title}</h3>
        <div style={{ color }}>{icon}</div>
      </div>
      <div className="font-mono text-2xl md:text-3xl font-semibold text-[#0F172A]">{value}</div>
      <div className="font-sans text-xs text-[#64748B] mt-1">{sub}</div>
    </div>
  );
}

export default Analytics;
