import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { supabase } from './lib/supabase';
import { ArrowLeft, ChevronDown, ChevronRight, CheckCircle2, Circle } from 'lucide-react';
import NodeDrawer from './NodeDrawer';

function RoadmapDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [roadmap, setRoadmap] = useState(null);
  const [nodes, setNodes] = useState([]);
  const [progress, setProgress] = useState([]); // Array of { node_id, status }
  const [loading, setLoading] = useState(true);
  
  // State for drawer
  const [selectedNode, setSelectedNode] = useState(null);
  
  // State for collapsed phases
  const [collapsedPhases, setCollapsedPhases] = useState({});

  useEffect(() => {
    async function fetchData() {
      // Fetch roadmap info
      const { data: rmData } = await supabase
        .from('roadmaps')
        .select('*')
        .eq('id', id)
        .single();
      if (rmData) setRoadmap(rmData);

      // Fetch nodes
      const { data: nodesData } = await supabase
        .from('roadmap_nodes')
        .select('*')
        .eq('roadmap_id', id)
        .order('order_index', { ascending: true });
      if (nodesData) setNodes(nodesData);

      // Fetch user progress (if auth is set up)
      const { data: userData } = await supabase.auth.getUser();
      if (userData?.user) {
        const { data: progData } = await supabase
          .from('user_progress')
          .select('*')
          .in('node_id', nodesData?.map(n => n.id) || []);
        if (progData) setProgress(progData);
      } else {
        // Fallback for local testing if no auth
        console.warn("No authenticated user, progress will not persist.");
      }
      setLoading(false);
    }
    fetchData();
  }, [id]);

  const togglePhase = (phase) => {
    setCollapsedPhases(prev => ({ ...prev, [phase]: !prev[phase] }));
  };

  const toggleNodeProgress = async (nodeId, currentStatus) => {
    const newStatus = currentStatus === 'done' ? 'not_started' : 'done';
    
    // Optimistic update
    const existing = progress.find(p => p.node_id === nodeId);
    if (existing) {
      setProgress(progress.map(p => p.node_id === nodeId ? { ...p, status: newStatus } : p));
    } else {
      setProgress([...progress, { node_id: nodeId, status: newStatus }]);
    }

    // Persist to Supabase
    const { data: userData } = await supabase.auth.getUser();
    if (userData?.user) {
      const { error } = await supabase
        .from('user_progress')
        .upsert({ user_id: userData.user.id, node_id: nodeId, status: newStatus, updated_at: new Date() }, { onConflict: 'user_id,node_id' });
      if (error) console.error("Error saving progress:", error);
    }
  };

  if (loading) return <div className="p-8 text-center text-[#64748B]">Loading roadmap...</div>;
  if (!roadmap) return <div className="p-8 text-center text-[#ba1a1a]">Roadmap not found.</div>;

  // Compute progress
  const totalNodes = nodes.length;
  const completedNodes = progress.filter(p => p.status === 'done').length;
  const percentComplete = totalNodes === 0 ? 0 : Math.round((completedNodes / totalNodes) * 100);

  // Group nodes by phase and section
  const groupedNodes = {};
  nodes.forEach(node => {
    if (!groupedNodes[node.phase]) groupedNodes[node.phase] = {};
    if (!groupedNodes[node.phase][node.section]) groupedNodes[node.phase][node.section] = [];
    groupedNodes[node.phase][node.section].push(node);
  });

  return (
    <div className="flex h-full relative">
      <div className="flex-1 overflow-y-auto pb-20 md:pb-8 p-4 md:p-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <button 
            onClick={() => navigate('/roadmaps')}
            className="flex items-center gap-2 text-[#64748B] hover:text-[#0F172A] font-sans text-sm font-medium mb-6 transition-colors"
          >
            <ArrowLeft size={16} /> Back to Roadmaps
          </button>

          <header className="mb-8">
            <h1 className="font-sans text-3xl font-semibold text-[#0F172A] mb-2">{roadmap.title}</h1>
            <p className="font-sans text-sm text-[#64748B]">{roadmap.description}</p>
            
            {/* Overall Progress */}
            <div className="mt-6">
              <div className="flex justify-between items-end mb-2">
                <span className="font-sans text-[11px] font-bold text-[#0891B2] uppercase tracking-widest">Progress</span>
                <span className="font-mono text-sm font-semibold text-[#0F172A]">{percentComplete}%</span>
              </div>
              <div className="w-full h-2 bg-[rgba(15,23,42,0.05)] rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-[#0891B2] to-[#0F766E] transition-all duration-500"
                  style={{ width: `${percentComplete}%` }}
                />
              </div>
            </div>
          </header>

          {/* Phases & Sections */}
          <div className="flex flex-col gap-6">
            {Object.keys(groupedNodes).map((phaseName) => {
              const isCollapsed = collapsedPhases[phaseName];
              const sections = groupedNodes[phaseName];

              return (
                <div key={phaseName} className="kinetic-card bg-white p-0 overflow-hidden">
                  {/* Phase Header */}
                  <div 
                    onClick={() => togglePhase(phaseName)}
                    className="p-4 md:p-6 bg-[rgba(15,23,42,0.02)] border-b border-[rgba(15,23,42,0.08)] cursor-pointer flex justify-between items-center hover:bg-[rgba(15,23,42,0.04)] transition-colors"
                  >
                    <h2 className="font-sans text-lg font-semibold text-[#0F172A]">{phaseName}</h2>
                    {isCollapsed ? <ChevronRight size={20} className="text-[#64748B]" /> : <ChevronDown size={20} className="text-[#64748B]" />}
                  </div>

                  {/* Sections */}
                  {!isCollapsed && (
                    <div className="p-4 md:p-6 flex flex-col gap-8">
                      {Object.keys(sections).map((sectionName) => (
                        <div key={sectionName}>
                          <h3 className="font-sans text-xs font-bold text-[#64748B] uppercase tracking-widest mb-3 border-l-2 border-l-[#0891B2] pl-2">
                            {sectionName}
                          </h3>
                          <div className="flex flex-col gap-1">
                            {sections[sectionName].map(node => {
                              const pStat = progress.find(p => p.node_id === node.id);
                              const isDone = pStat && pStat.status === 'done';
                              
                              return (
                                <div key={node.id} className="flex items-center gap-3 p-2 hover:bg-[rgba(15,23,42,0.02)] rounded group transition-colors">
                                  <button onClick={() => toggleNodeProgress(node.id, pStat?.status)} className="shrink-0">
                                    {isDone ? (
                                      <CheckCircle2 size={20} className="text-[#0F766E]" />
                                    ) : (
                                      <Circle size={20} className="text-[#94a3b8] group-hover:text-[#64748B]" />
                                    )}
                                  </button>
                                  
                                  <div 
                                    className={`flex-1 font-sans text-sm font-medium cursor-pointer ${isDone ? 'text-[#64748B] line-through decoration-[#cbd5e1]' : 'text-[#0F172A]'}`}
                                    onClick={() => setSelectedNode({ ...node, status: pStat?.status || 'not_started' })}
                                  >
                                    {node.title}
                                  </div>
                                  
                                  <div className="shrink-0">
                                    <TierBadge tier={node.tier} />
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Drawer */}
      <NodeDrawer 
        node={selectedNode} 
        onClose={() => setSelectedNode(null)} 
        onToggleStatus={() => {
          if (selectedNode) toggleNodeProgress(selectedNode.id, selectedNode.status);
          setSelectedNode(prev => prev ? { ...prev, status: prev.status === 'done' ? 'not_started' : 'done' } : null);
        }}
      />
    </div>
  );
}

function TierBadge({ tier }) {
  const styles = {
    't1': 'bg-[#B91C1C]/10 text-[#B91C1C] border-[#B91C1C]/20',
    't2': 'bg-[#B45309]/10 text-[#B45309] border-[#B45309]/20',
    't3': 'bg-[#0891B2]/10 text-[#0891B2] border-[#0891B2]/20',
    'dsa': 'bg-[#0F172A]/10 text-[#0F172A] border-[#0F172A]/20',
  };
  
  return (
    <span className={`font-mono text-[9px] font-bold uppercase tracking-widest px-1.5 py-0.5 rounded border ${styles[tier] || styles['t3']}`}>
      {tier}
    </span>
  );
}

export default RoadmapDetail;
