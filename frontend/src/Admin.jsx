import React, { useState, useEffect } from 'react';
import { ShieldCheck, AlertCircle, Users, Activity, CheckCircle2, RefreshCw, MessageSquare } from 'lucide-react';
import { apiFetch } from './lib/api';

function fmtDate(d) {
  return d ? new Date(d).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—';
}

function FunnelStat({ label, value, sub, accent }) {
  return (
    <div className="kinetic-card bg-white p-4 flex flex-col gap-1">
      <span className="font-sans text-[11px] font-bold text-[#64748B] uppercase tracking-widest">{label}</span>
      <span className="font-mono text-2xl font-semibold" style={{ color: accent || '#0F172A' }}>{value}</span>
      {sub && <span className="font-mono text-[11px] text-[#64748B]">{sub}</span>}
    </div>
  );
}

function Admin() {
  const [data, setData] = useState(null);
  const [feedbacks, setFeedbacks] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('funnel');

  const loadFunnel = () => {
    setLoading(true);
    setError(null);
    apiFetch('/api/admin/funnel')
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  const loadFeedback = () => {
    setLoading(true);
    setError(null);
    apiFetch('/api/admin/feedback')
      .then(setFeedbacks)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  const load = () => {
    if (activeTab === 'funnel') loadFunnel();
    else loadFeedback();
  };

  useEffect(() => { load(); }, [activeTab]);

  return (
    <div className="flex flex-col gap-8 p-4 md:p-8 max-w-5xl mx-auto w-full pb-20 md:pb-8 animate-in fade-in duration-300">

      <header className="flex flex-col md:flex-row md:items-start justify-between gap-4">
        <div>
          <h2 className="font-sans text-2xl font-semibold text-[#0F172A] flex items-center gap-2">
            <ShieldCheck size={24} className="text-[#0891B2]" /> Admin Dashboard
          </h2>
          <p className="font-sans text-sm text-[#64748B] mt-1">Founder-only analytics and feedback.</p>
        </div>
        <button
          onClick={load}
          className="kinetic-btn bg-white border border-[rgba(15,23,42,0.12)] text-[#0F172A] px-4 py-2 text-sm flex items-center gap-2 hover:bg-gray-50"
        >
          <RefreshCw size={14} /> Refresh
        </button>
      </header>

      {/* Tabs */}
      <div className="flex gap-6 border-b border-[rgba(15,23,42,0.08)]">
        <button 
          onClick={() => setActiveTab('funnel')}
          className={`pb-2 text-sm font-semibold transition-colors border-b-2 flex items-center gap-2 ${activeTab === 'funnel' ? 'border-[#0891B2] text-[#0891B2]' : 'border-transparent text-[#64748B] hover:text-[#0F172A]'}`}
        >
          <Activity size={16} /> Activation Funnel
        </button>
        <button 
          onClick={() => setActiveTab('feedback')}
          className={`pb-2 text-sm font-semibold transition-colors border-b-2 flex items-center gap-2 ${activeTab === 'feedback' ? 'border-[#0891B2] text-[#0891B2]' : 'border-transparent text-[#64748B] hover:text-[#0F172A]'}`}
        >
          <MessageSquare size={16} /> User Feedback
        </button>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="kinetic-card bg-white p-4 flex flex-col gap-2">
              <div className="skeleton h-3 w-20" />
              <div className="skeleton h-7 w-14" />
              <div className="skeleton h-3 w-24" />
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="kinetic-card flex items-center gap-3 text-[#ba1a1a]">
          <AlertCircle size={20} />
          <p className="font-sans text-sm">{error === 'Admin access required' ? "You don't have admin access." : `Failed to load: ${error}`}</p>
        </div>
      ) : (
        <>
          {activeTab === 'funnel' && data && (
            <>
              {/* Funnel summary */}
              <section className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <FunnelStat label="Signups" value={data.summary.signups} sub="total accounts" />
                <FunnelStat label="Activated" value={`${data.summary.pct_activated}%`} sub={`${data.summary.logged_activity} logged an activity`} accent="#0891B2" />
                <FunnelStat label="Reviewed" value={`${data.summary.pct_reviewed}%`} sub={`${data.summary.completed_review} completed a review`} accent="#0F766E" />
                <FunnelStat label="Retained" value={`${data.summary.pct_retained}%`} sub={`${data.summary.returned_later_day} returned a later day`} accent="#7C3AED" />
              </section>

              {/* Per-user breakdown */}
              <section>
                <h3 className="font-sans text-sm font-semibold text-[#1a1c1b] uppercase tracking-wider flex items-center gap-1.5 mb-3">
                  <Users size={16} className="text-[#0F172A]" /> Per user
                </h3>
                <div className="kinetic-card bg-white p-0 overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left font-sans text-[11px] font-bold text-[#64748B] uppercase tracking-widest border-b border-[rgba(15,23,42,0.08)]">
                        <th className="px-4 py-3">Email</th>
                        <th className="px-4 py-3">Signed up</th>
                        <th className="px-4 py-3 text-right">Activities</th>
                        <th className="px-4 py-3 text-right">Reviews</th>
                        <th className="px-4 py-3">Last active</th>
                      </tr>
                    </thead>
                    <tbody className="font-sans text-[#0F172A]">
                      {data.users.map((u, i) => (
                        <tr key={i} className={`border-b border-[rgba(15,23,42,0.05)] ${u.activities === 0 ? 'opacity-60' : ''}`}>
                          <td className="px-4 py-3 truncate max-w-[220px]" title={u.email}>{u.email}</td>
                          <td className="px-4 py-3 font-mono text-xs text-[#64748B]">{fmtDate(u.signed_up)}</td>
                          <td className="px-4 py-3 text-right font-mono">{u.activities}</td>
                          <td className="px-4 py-3 text-right font-mono">{u.reviews_done}</td>
                          <td className="px-4 py-3 font-mono text-xs text-[#64748B]">{fmtDate(u.last_active)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>

              {/* Captures by source */}
              <section>
                <h3 className="font-sans text-sm font-semibold text-[#1a1c1b] uppercase tracking-wider flex items-center gap-1.5 mb-3">
                  <Activity size={16} className="text-[#0F172A]" /> Captures by source
                </h3>
                <div className="kinetic-card bg-white flex flex-col gap-2">
                  {data.by_source.length === 0 ? (
                    <p className="font-sans text-sm text-[#64748B]">No activities yet.</p>
                  ) : (
                    data.by_source.map((s) => (
                      <div key={s.source_type} className="flex items-center justify-between font-sans text-sm">
                        <span className="capitalize text-[#0F172A]">{s.source_type}</span>
                        <span className="font-mono text-[#64748B]">{s.activities}</span>
                      </div>
                    ))
                  )}
                </div>
              </section>
            </>
          )}

          {activeTab === 'feedback' && feedbacks && (
            <section className="flex flex-col gap-4">
              {feedbacks.length === 0 ? (
                <div className="kinetic-card bg-white py-12 flex flex-col items-center justify-center text-center">
                  <MessageSquare size={32} className="text-[#cbd5e1] mb-2" />
                  <p className="font-sans text-sm font-semibold text-[#0F172A]">No feedback yet</p>
                  <p className="font-sans text-sm text-[#64748B]">When users submit feedback, it will appear here.</p>
                </div>
              ) : (
                feedbacks.map(f => (
                  <div key={f.id} className="kinetic-card bg-white p-5 flex flex-col gap-3">
                    <div className="flex justify-between items-start gap-4">
                      <div>
                        <span className="font-sans text-sm font-semibold text-[#0F172A]">{f.email || 'Unknown User'}</span>
                        <span className="font-mono text-xs text-[#64748B] ml-3">{fmtDate(f.created_at)}</span>
                      </div>
                      <span className={`font-sans text-[10px] font-bold uppercase tracking-widest px-2 py-1 rounded-sm ${f.status === 'new' ? 'bg-[#0891B2]/10 text-[#0891B2]' : 'bg-slate-100 text-slate-500'}`}>
                        {f.status}
                      </span>
                    </div>
                    <p className="font-sans text-sm text-[#334155] whitespace-pre-wrap">{f.message}</p>
                  </div>
                ))
              )}
            </section>
          )}
        </>
      )}
    </div>
  );
}

export default Admin;
