import React, { useEffect, useState } from 'react';
import { Map, ListChecks } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { apiFetch } from './lib/api';

function Roadmaps() {
  const navigate = useNavigate();
  const [roadmaps, setRoadmaps] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchRoadmaps() {
      try {
        // Backend returns each roadmap with real progress computed server-side
        const data = await apiFetch('/api/roadmaps/');
        setRoadmaps(data);
      } catch (err) {
        console.error('Failed to load roadmaps:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchRoadmaps();
  }, []);

  return (
    <div className="flex flex-col gap-8 p-4 md:p-8 max-w-5xl mx-auto w-full pb-20 md:pb-8 animate-in fade-in duration-300">

      <header className="mb-2">
        <h2 className="font-sans text-2xl font-semibold text-[#0F172A] flex items-center gap-2">
          <Map size={24} className="text-[#0891B2]" /> Learning Roadmaps
        </h2>
        <p className="font-sans text-sm text-[#64748B] mt-1">Structured learning paths tracking your completion and retention.</p>
      </header>

      <section>
        <h2 className="font-sans text-sm font-semibold text-[#1a1c1b] uppercase tracking-wider flex items-center gap-1.5 mb-4">
          <ListChecks size={16} className="text-[#0F172A]" /> All Roadmaps
        </h2>

        {loading ? (
          <div className="p-8 text-center text-[#64748B]">Loading roadmaps...</div>
        ) : roadmaps.length === 0 ? (
          <div className="p-8 text-center text-[#64748B] bg-white rounded border border-[rgba(15,23,42,0.1)]">No roadmaps found.</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {roadmaps.map((rm) => (
              <div
                key={rm.id}
                onClick={() => navigate(`/roadmaps/${rm.id}`)}
                className="kinetic-card bg-white p-5 cursor-pointer hover:border-[rgba(15,23,42,0.2)] transition-colors group"
              >
                <div className="flex justify-between items-start mb-3">
                  <h3 className="font-sans text-lg font-semibold text-[#0F172A] line-clamp-1">{rm.title}</h3>
                  <span className="font-mono text-sm font-semibold text-[#0F172A]">{rm.progress_pct}%</span>
                </div>
                <p className="font-sans text-xs text-[#64748B] mb-4 line-clamp-2 min-h-[32px]">{rm.description}</p>
                <div className="w-full h-1.5 bg-[rgba(15,23,42,0.05)] rounded-full overflow-hidden mb-3">
                  <div className="h-full bg-gradient-to-r from-[#0891B2] to-[#0F766E] transition-all duration-500" style={{ width: `${rm.progress_pct}%` }} />
                </div>
                <div className="font-mono text-[10px] text-[#64748B]">{rm.done_nodes} / {rm.total_nodes} topics complete</div>
              </div>
            ))}
          </div>
        )}
      </section>

    </div>
  );
}

export default Roadmaps;
