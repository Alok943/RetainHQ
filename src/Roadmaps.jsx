import React, { useEffect, useState } from 'react';
import { Map, Plus, ListChecks } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { supabase } from './lib/supabase';

function Roadmaps() {
  const navigate = useNavigate();
  const [roadmaps, setRoadmaps] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchRoadmaps() {
      // In a real app we'd also fetch progress to calculate the %
      const { data, error } = await supabase
        .from('roadmaps')
        .select('*')
        .order('created_at', { ascending: false });

      if (data) {
        setRoadmaps(data);
      } else {
        console.error(error);
      }
      setLoading(false);
    }
    fetchRoadmaps();
  }, []);

  return (
    <div className="flex flex-col lg:flex-row gap-8 p-4 md:p-8 max-w-6xl mx-auto w-full pb-20 md:pb-8 animate-in fade-in duration-300">
      
      {/* MAIN CONTENT AREA */}
      <div className="flex-1 flex flex-col gap-8 min-w-0">
        
        <header className="mb-2">
          <h2 className="font-sans text-2xl font-semibold text-[#0F172A] flex items-center gap-2">
            <Map size={24} className="text-[#0891B2]" /> Learning Roadmaps
          </h2>
          <p className="font-sans text-sm text-[#64748B] mt-1">Structured learning paths tracking your completion and retention.</p>
        </header>

        {/* ROADMAPS LIST */}
        <section>
          <div className="flex justify-between items-end mb-4">
            <h2 className="font-sans text-sm font-semibold text-[#1a1c1b] uppercase tracking-wider flex items-center gap-1.5">
              <ListChecks size={16} className="text-[#0F172A]" /> All Roadmaps
            </h2>
            <button className="text-xs font-semibold text-[#0891B2] hover:text-[#0F766E] uppercase tracking-widest flex items-center gap-1">
              <Plus size={12} /> New Roadmap
            </button>
          </div>
          
          {loading ? (
            <div className="p-8 text-center text-[#64748B]">Loading roadmaps...</div>
          ) : roadmaps.length === 0 ? (
            <div className="p-8 text-center text-[#64748B] bg-white rounded border border-[rgba(15,23,42,0.1)]">No roadmaps found.</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {roadmaps.map(rm => (
                <div 
                  key={rm.id} 
                  onClick={() => navigate(`/roadmaps/${rm.id}`)}
                  className="kinetic-card bg-white p-5 cursor-pointer hover:border-[rgba(15,23,42,0.2)] transition-colors group"
                >
                  <div className="flex justify-between items-start mb-3">
                    <h3 className="font-sans text-lg font-semibold text-[#0F172A] line-clamp-1">{rm.title}</h3>
                    {/* Placeholder for actual progress % since we don't have agg query here yet */}
                    <span className="font-mono text-sm font-semibold text-[#0F172A]">0%</span>
                  </div>
                  <p className="font-sans text-xs text-[#64748B] mb-4 line-clamp-2 min-h-[32px]">{rm.description}</p>
                  <div className="w-full h-1.5 bg-[rgba(15,23,42,0.05)] rounded-full overflow-hidden mb-4">
                    <div className="h-full bg-[#0F172A]" style={{ width: '0%' }} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* EXPLORE TEMPLATES */}
        <section className="mt-8">
          <div className="flex justify-between items-end mb-4">
            <h2 className="font-sans text-sm font-semibold text-[#1a1c1b] uppercase tracking-wider flex items-center gap-1.5">
              <Map size={16} className="text-[#0F172A]" /> Explore Templates
            </h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <TemplateCard title="Machine Learning Ops" topics="42 Topics" />
            <TemplateCard title="AWS Solutions Architect" topics="89 Topics" />
            <TemplateCard title="React Patterns" topics="24 Topics" />
          </div>
        </section>

      </div>

      {/* RIGHT RAIL */}
      <aside className="hidden lg:flex flex-col w-[320px] shrink-0 gap-6">
        <div className="kinetic-card bg-[#f9f9f6] border-dashed border-2 flex flex-col items-center justify-center text-center p-8 min-h-[300px]">
          <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center border border-[rgba(15,23,42,0.1)] mb-4">
            <Plus size={24} className="text-[#64748B]" />
          </div>
          <h3 className="font-sans font-semibold text-[#0F172A] mb-2">Import Roadmap</h3>
          <p className="font-sans text-xs text-[#64748B] leading-relaxed mb-6">
            Paste a link from GitHub, Notion, or text to instantly generate a tracked curriculum.
          </p>
          <button className="kinetic-btn bg-white border border-[#0F172A] text-[#0F172A] hover:bg-slate-50 w-full">
            Paste Link
          </button>
        </div>
      </aside>

    </div>
  );
}

function TemplateCard({ title, topics }) {
  return (
    <div className="kinetic-card bg-[#f9f9f6] p-4 cursor-pointer hover:bg-white hover:shadow-sm transition-all border border-transparent hover:border-[rgba(15,23,42,0.08)]">
      <h4 className="font-sans text-sm font-semibold text-[#0F172A] mb-1">{title}</h4>
      <div className="font-mono text-[10px] text-[#64748B]">{topics}</div>
    </div>
  );
}

export default Roadmaps;
