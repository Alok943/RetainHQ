import React, { useEffect, useState } from 'react';
import {
  ArrowRight, ArrowLeft, Loader2, Sparkles, Target, ClipboardList, TreePine, CheckCircle2,
  ChevronDown, ChevronRight, Trash2, RotateCcw, SkipForward,
} from 'lucide-react';
import { apiFetch } from './lib/api';
import AttachedRoadmaps from './AttachRoadmaps';

// Career Coach onboarding — SPEC-career-coach-phase2.md §8: four steps, aimed
// at under 5 minutes total. Step 3 (tree review) is where that budget is won
// or lost, so subjects collapse by default and counts surface up front —
// a wall of 60 nodes reads as "rubber-stamp this", which quietly kills the
// tree's ground-truth property (parent §6).

const STEPS = [
  { key: 'goal', label: 'Goal', icon: Target },
  { key: 'diagnostic', label: 'Diagnostic', icon: ClipboardList },
  { key: 'tree', label: 'Tree review', icon: TreePine },
  { key: 'confirm', label: 'Confirm', icon: CheckCircle2 },
];

function Stepper({ current }) {
  const idx = STEPS.findIndex((s) => s.key === current);
  return (
    <div className="flex items-center gap-2 mb-8">
      {STEPS.map((s, i) => {
        const Icon = s.icon;
        const done = i < idx;
        const active = i === idx;
        return (
          <React.Fragment key={s.key}>
            <div className="flex items-center gap-1.5">
              <div
                className={`h-7 w-7 rounded-full flex items-center justify-center border transition-colors ${
                  active ? 'bg-[#0891B2] border-[#0891B2] text-white'
                    : done ? 'bg-[#0891B2]/10 border-[#0891B2]/30 text-[#0891B2]'
                    : 'bg-transparent border-[rgba(15,23,42,0.15)] text-[#94A3B8]'
                }`}
              >
                <Icon size={14} />
              </div>
              <span className={`font-sans text-xs font-medium hidden sm:inline ${active ? 'text-[#0F172A]' : 'text-[#94A3B8]'}`}>
                {s.label}
              </span>
            </div>
            {i < STEPS.length - 1 && <div className="flex-1 h-px bg-[rgba(15,23,42,0.1)] min-w-[12px]" />}
          </React.Fragment>
        );
      })}
    </div>
  );
}

function ErrorBanner({ error }) {
  if (!error) return null;
  return (
    <div className="mb-4 px-4 py-3 rounded-xl bg-red-50 border border-red-200 font-sans text-sm text-red-700">
      {error}
    </div>
  );
}

function GoalStep({ templates, roleKey, setRoleKey, goalTitle, setGoalTitle, targetDate, setTargetDate, busy, error, onContinue }) {
  return (
    <div className="flex flex-col gap-6">
      <header>
        <h2 className="font-sans text-2xl font-semibold text-[#0F172A] flex items-center gap-2">
          <Sparkles size={22} className="text-[#0891B2]" /> What are you preparing for?
        </h2>
        <p className="font-sans text-sm text-[#64748B] mt-1">
          Pick a role. We'll adapt a curated tree to it — never invent one from scratch.
        </p>
      </header>

      <ErrorBanner error={error} />

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {templates.map((t) => (
          <button
            key={t.role_key}
            onClick={() => {
              setRoleKey(t.role_key);
              if (!goalTitle.trim()) setGoalTitle(t.title);
            }}
            className={`text-left bg-white border rounded-2xl p-4 transition-colors ${
              roleKey === t.role_key ? 'border-[#0891B2] ring-1 ring-[#0891B2]' : 'border-[rgba(15,23,42,0.08)] hover:border-[#0891B2]/50'
            }`}
          >
            <div className="font-sans text-sm font-semibold text-[#0F172A]">{t.title}</div>
            <div className="font-mono text-[11px] text-[#94A3B8] mt-1">{t.node_count} nodes · {t.version}</div>
          </button>
        ))}
        {templates.length === 0 && (
          <div className="col-span-full font-sans text-sm text-[#94A3B8]">Loading roles…</div>
        )}
      </div>

      <div className="bg-white border border-[rgba(15,23,42,0.08)] rounded-2xl shadow-sm p-4 md:p-5 flex flex-col gap-3">
        <label className="flex flex-col gap-1">
          <span className="font-sans text-xs font-semibold text-[#64748B] uppercase tracking-wide">Goal title</span>
          <input
            value={goalTitle}
            onChange={(e) => setGoalTitle(e.target.value)}
            placeholder="e.g. Backend SDE, Jan 2027 placements"
            className="font-sans text-sm text-[#0F172A] bg-transparent border-b border-[rgba(15,23,42,0.1)] focus:border-[#0891B2] focus:outline-none py-1"
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="font-sans text-xs font-semibold text-[#64748B] uppercase tracking-wide">Target date (optional)</span>
          <input
            type="date"
            value={targetDate}
            onChange={(e) => setTargetDate(e.target.value)}
            className="font-sans text-sm text-[#0F172A] bg-transparent border-b border-[rgba(15,23,42,0.1)] focus:border-[#0891B2] focus:outline-none py-1 w-48"
          />
        </label>
      </div>

      <button
        onClick={onContinue}
        disabled={busy || !roleKey || !goalTitle.trim()}
        className="self-end flex items-center gap-1.5 bg-[#0891B2] hover:bg-[#0E7490] text-white font-sans text-sm font-semibold px-4 py-2 rounded-xl transition-colors disabled:opacity-40"
      >
        {busy ? <><Loader2 size={15} className="animate-spin" /> Creating…</> : <>Continue <ArrowRight size={14} /></>}
      </button>
    </div>
  );
}

function DiagnosticStep({ probes, probesLoaded, answers, setAnswer, busy, error, onSubmit, onSkip }) {
  const answeredCount = probes.filter((p) => (answers[p.stable_key] || '').trim()).length;
  return (
    <div className="flex flex-col gap-6">
      <header>
        <h2 className="font-sans text-2xl font-semibold text-[#0F172A] flex items-center gap-2">
          <ClipboardList size={22} className="text-[#0891B2]" /> Quick diagnostic
        </h2>
        <p className="font-sans text-sm text-[#64748B] mt-1">
          A few questions from the highest-priority topics. Skip freely — an unanswered node just starts
          "unexposed," never guessed (parent design doc §6).
        </p>
      </header>

      <ErrorBanner error={error} />

      {!probesLoaded && (
        <div className="flex items-center gap-2 font-sans text-sm text-[#94A3B8]"><Loader2 size={15} className="animate-spin" /> Loading probes…</div>
      )}

      {probesLoaded && probes.length === 0 && (
        <div className="bg-white border border-[rgba(15,23,42,0.08)] rounded-2xl shadow-sm p-6 font-sans text-sm text-[#64748B]">
          Diagnostic isn't available right now — that's fine, every node just starts unexposed. Continue whenever you're ready.
        </div>
      )}

      <div className="flex flex-col gap-4">
        {probes.map((p) => (
          <div key={p.stable_key} className="bg-white border border-[rgba(15,23,42,0.08)] rounded-2xl shadow-sm p-4 md:p-5">
            <div className="font-sans text-xs font-semibold text-[#0891B2] mb-1">{p.node_title}</div>
            <div className="font-sans text-sm text-[#0F172A] mb-2">{p.probe}</div>
            <textarea
              value={answers[p.stable_key] || ''}
              onChange={(e) => setAnswer(p.stable_key, e.target.value)}
              placeholder="Your answer (leave blank to skip this one)"
              rows={2}
              className="w-full font-sans text-sm text-[#0F172A] bg-[rgba(15,23,42,0.02)] rounded-lg p-2 focus:outline-none focus:ring-1 focus:ring-[#0891B2]/50"
            />
          </div>
        ))}
      </div>

      <div className="flex items-center justify-between gap-3">
        <button
          onClick={onSkip}
          disabled={busy}
          className="flex items-center gap-1.5 font-sans text-sm text-[#64748B] hover:text-[#0F172A] transition-colors"
        >
          <SkipForward size={14} /> Skip diagnostic
        </button>
        <button
          onClick={onSubmit}
          disabled={busy || (probesLoaded && probes.length > 0 && answeredCount === 0)}
          className="flex items-center gap-1.5 bg-[#0891B2] hover:bg-[#0E7490] text-white font-sans text-sm font-semibold px-4 py-2 rounded-xl transition-colors disabled:opacity-40"
        >
          {busy ? <><Loader2 size={15} className="animate-spin" /> Grading…</> : <>Continue <ArrowRight size={14} /></>}
        </button>
      </div>
    </div>
  );
}

function NodeRow({ node, onChange, onDelete }) {
  return (
    <div className="group flex items-start gap-2 py-2 border-t border-[rgba(15,23,42,0.04)] first:border-t-0">
      <div className="flex-1 min-w-0">
        <input
          value={node.title}
          onChange={(e) => onChange({ title: e.target.value })}
          className="w-full font-sans text-sm text-[#0F172A] bg-transparent border-b border-transparent hover:border-[rgba(15,23,42,0.1)] focus:border-[#0891B2] focus:outline-none py-0.5"
        />
        {node.stable_key.startsWith('custom.') && (
          <span className="font-mono text-[9px] text-[#0F766E] bg-[#0F766E]/10 rounded px-1 py-0.5">new</span>
        )}
      </div>
      <select
        value={node.priority}
        onChange={(e) => onChange({ priority: Number(e.target.value) })}
        title="Priority"
        className="font-mono text-xs text-[#64748B] bg-transparent border border-[rgba(15,23,42,0.1)] rounded px-1 py-0.5 shrink-0"
      >
        {[1, 2, 3, 4, 5].map((p) => <option key={p} value={p}>P{p}</option>)}
      </select>
      <input
        type="number"
        min={5}
        value={node.est_effort_min}
        onChange={(e) => onChange({ est_effort_min: Math.max(5, Number(e.target.value) || 0) })}
        title="Estimated minutes"
        className="w-16 font-mono text-xs text-[#64748B] bg-transparent border border-[rgba(15,23,42,0.1)] rounded px-1 py-0.5 shrink-0"
      />
      <button onClick={onDelete} title="Remove node" className="opacity-0 group-hover:opacity-100 text-[#94A3B8] hover:text-red-500 transition-all p-1 shrink-0">
        <Trash2 size={13} />
      </button>
    </div>
  );
}

function SubjectGroup({ subject, expanded, onToggle, onChangeNode, onDeleteNode }) {
  const totalMin = subject.nodes.reduce((a, n) => a + (n.est_effort_min || 0), 0);
  return (
    <div className="bg-white border border-[rgba(15,23,42,0.08)] rounded-2xl shadow-sm overflow-hidden">
      <button onClick={onToggle} className="w-full flex items-center justify-between gap-2 px-4 py-3 hover:bg-[rgba(15,23,42,0.01)] transition-colors">
        <div className="flex items-center gap-2 min-w-0">
          {expanded ? <ChevronDown size={15} className="text-[#94A3B8] shrink-0" /> : <ChevronRight size={15} className="text-[#94A3B8] shrink-0" />}
          <span className="font-sans text-sm font-semibold text-[#0F172A] truncate">{subject.title}</span>
        </div>
        <span className="font-mono text-[11px] text-[#94A3B8] shrink-0">{subject.nodes.length} nodes · ~{Math.round(totalMin / 60)}h</span>
      </button>
      {expanded && (
        <div className="px-4 pb-3">
          {subject.nodes.map((n, ni) => (
            <NodeRow
              key={n.stable_key}
              node={n}
              onChange={(patch) => onChangeNode(ni, patch)}
              onDelete={() => onDeleteNode(ni)}
            />
          ))}
          {subject.nodes.length === 0 && <div className="font-sans text-xs text-[#94A3B8] py-2">No nodes left in this subject.</div>}
        </div>
      )}
    </div>
  );
}

function TreeStep({
  draft, generating, error, expandedSubjects, toggleSubject, updateNode, deleteNode,
  freeText, setFreeText, onRegenerate, onContinue,
}) {
  const totalNodes = draft ? draft.subjects.reduce((n, s) => n + s.nodes.length, 0) : 0;
  const totalHours = draft ? Math.round(draft.subjects.reduce((sum, s) => sum + s.nodes.reduce((a, n) => a + (n.est_effort_min || 0), 0), 0) / 60) : 0;

  return (
    <div className="flex flex-col gap-6">
      <header>
        <h2 className="font-sans text-2xl font-semibold text-[#0F172A] flex items-center gap-2">
          <TreePine size={22} className="text-[#0891B2]" /> Review your tree
        </h2>
        <p className="font-sans text-sm text-[#64748B] mt-1">
          This tree is what everything is measured against — rename, reprioritize, or remove anything
          that doesn't fit. {draft && <span className="font-semibold text-[#0F172A]">{totalNodes} nodes · ~{totalHours}h total.</span>}
        </p>
      </header>

      <ErrorBanner error={error} />

      {generating && (
        <div className="bg-white border border-[rgba(15,23,42,0.08)] rounded-3xl shadow-sm p-10 flex flex-col items-center text-center">
          <Loader2 size={28} className="text-[#0891B2] animate-spin mb-3" />
          <h3 className="font-sans text-sm font-semibold text-[#0F172A]">Adapting your tree…</h3>
          <p className="font-sans text-xs text-[#64748B] mt-1">Usually takes a few seconds.</p>
        </div>
      )}

      {!generating && draft && (
        <>
          <div className="flex flex-col gap-2">
            {draft.subjects.map((s, si) => (
              <SubjectGroup
                key={s.key}
                subject={s}
                expanded={!!expandedSubjects[s.key]}
                onToggle={() => toggleSubject(s.key)}
                onChangeNode={(ni, patch) => updateNode(si, ni, patch)}
                onDeleteNode={(ni) => deleteNode(si, ni)}
              />
            ))}
          </div>

          <div className="bg-white border border-[rgba(15,23,42,0.08)] rounded-2xl shadow-sm p-4 flex flex-col gap-2">
            <span className="font-sans text-xs font-semibold text-[#64748B] uppercase tracking-wide">Not quite right? Add context and regenerate</span>
            <textarea
              value={freeText}
              onChange={(e) => setFreeText(e.target.value)}
              placeholder="e.g. I've done 200 LeetCode problems, weak on DP"
              rows={2}
              className="w-full font-sans text-sm text-[#0F172A] bg-[rgba(15,23,42,0.02)] rounded-lg p-2 focus:outline-none focus:ring-1 focus:ring-[#0891B2]/50"
            />
            <button
              onClick={onRegenerate}
              className="self-start flex items-center gap-1.5 font-sans text-xs text-[#0891B2] hover:text-[#0F172A] transition-colors"
            >
              <RotateCcw size={13} /> Regenerate
            </button>
          </div>

          <AttachedRoadmaps />

          <button
            onClick={onContinue}
            disabled={totalNodes === 0}
            className="self-end flex items-center gap-1.5 bg-[#0891B2] hover:bg-[#0E7490] text-white font-sans text-sm font-semibold px-4 py-2 rounded-xl transition-colors disabled:opacity-40"
          >
            Continue <ArrowRight size={14} />
          </button>
        </>
      )}

      {/* The state that used to render NOTHING. The auto-generate effect is keyed
          on [step], so a failed first generation left this step permanently blank
          with no control to retry — the user's only escape was to navigate away
          and back. Always offer a way forward. */}
      {!generating && !draft && (
        <div className="bg-white border border-[rgba(15,23,42,0.08)] rounded-2xl shadow-sm p-6 flex flex-col items-center text-center gap-3">
          <p className="font-sans text-sm text-[#64748B]">
            {error ? "That didn't work." : 'No tree yet.'} You can try again — nothing has been saved.
          </p>
          <button
            onClick={onRegenerate}
            className="flex items-center gap-1.5 bg-[#0891B2] hover:bg-[#0E7490] text-white font-sans text-sm font-semibold px-4 py-2 rounded-xl transition-colors"
          >
            <RotateCcw size={14} /> Try again
          </button>
        </div>
      )}
    </div>
  );
}

function ConfirmStep({ draft, busy, error, onBack, onConfirm }) {
  const totalNodes = draft.subjects.reduce((n, s) => n + s.nodes.length, 0);
  const totalHours = Math.round(draft.subjects.reduce((sum, s) => sum + s.nodes.reduce((a, n) => a + (n.est_effort_min || 0), 0), 0) / 60);
  return (
    <div className="flex flex-col gap-6">
      <header>
        <h2 className="font-sans text-2xl font-semibold text-[#0F172A] flex items-center gap-2">
          <CheckCircle2 size={22} className="text-[#0891B2]" /> Confirm your tree
        </h2>
        <p className="font-sans text-sm text-[#64748B] mt-1">
          Every node starts <span className="font-semibold">unexposed</span> unless the diagnostic already graded it.
          Nothing is guessed.
        </p>
      </header>

      <ErrorBanner error={error} />

      <div className="bg-white border border-[rgba(15,23,42,0.08)] rounded-2xl shadow-sm p-5 flex flex-col gap-3">
        <div className="font-sans text-lg font-semibold text-[#0F172A]">{draft.title}</div>
        <div className="flex flex-wrap gap-4 font-mono text-xs text-[#64748B]">
          <span>{draft.subjects.length} subjects</span>
          <span>{totalNodes} nodes</span>
          <span>~{totalHours}h estimated</span>
        </div>
        <div className="flex flex-wrap gap-1.5 mt-1">
          {draft.subjects.map((s) => (
            <span key={s.key} className="font-sans text-[11px] text-[#475569] bg-[rgba(15,23,42,0.04)] border border-[rgba(15,23,42,0.06)] rounded px-2 py-0.5">
              {s.title} · {s.nodes.length}
            </span>
          ))}
        </div>
      </div>

      <div className="flex items-center justify-between gap-3">
        <button onClick={onBack} disabled={busy} className="flex items-center gap-1.5 font-sans text-sm text-[#64748B] hover:text-[#0F172A] transition-colors">
          <ArrowLeft size={14} /> Back to tree
        </button>
        <button
          onClick={onConfirm}
          disabled={busy}
          className="flex items-center gap-1.5 bg-[#0891B2] hover:bg-[#0E7490] text-white font-sans text-sm font-semibold px-5 py-2.5 rounded-xl transition-colors disabled:opacity-40"
        >
          {busy ? <><Loader2 size={15} className="animate-spin" /> Saving…</> : <>Confirm & start tracking <ArrowRight size={14} /></>}
        </button>
      </div>
    </div>
  );
}

function CareerOnboarding({ existingGoal, onCommitted }) {
  const [step, setStep] = useState(existingGoal ? 'diagnostic' : 'goal');
  const [templates, setTemplates] = useState([]);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  // Step 1 — Goal
  const [roleKey, setRoleKey] = useState(existingGoal?.role_key || '');
  const [goalTitle, setGoalTitle] = useState(existingGoal?.title || '');
  const [targetDate, setTargetDate] = useState(existingGoal?.target_date || '');
  const [goal, setGoal] = useState(existingGoal || null);

  // Step 2 — Diagnostic
  const [probes, setProbes] = useState([]);
  const [probesLoaded, setProbesLoaded] = useState(false);
  const [answers, setAnswers] = useState({});
  const [diagnosticResults, setDiagnosticResults] = useState([]);

  // Step 3 — Tree review
  const [draft, setDraft] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [freeText, setFreeText] = useState('');
  const [expandedSubjects, setExpandedSubjects] = useState({});

  useEffect(() => {
    apiFetch('/api/career/templates').then(setTemplates).catch(() => setTemplates([]));
  }, []);

  useEffect(() => {
    if (step !== 'diagnostic' || !goal) return;
    setProbesLoaded(false);
    apiFetch('/api/career/diagnostic')
      .then((p) => setProbes(p))
      .catch((err) => { if (err.status !== 404) setError(err.message); setProbes([]); })
      .finally(() => setProbesLoaded(true));
  }, [step, goal]);

  const generateTree = async (extraFreeText) => {
    setGenerating(true);
    setError('');
    try {
      const d = await apiFetch('/api/career/tree/generate', {
        method: 'POST',
        body: JSON.stringify({
          role_key: goal.role_key,
          goal_title: goal.title,
          target_date: goal.target_date || undefined,
          diagnostic_results: diagnosticResults.length ? diagnosticResults : undefined,
          free_text: (extraFreeText ?? freeText).trim() || undefined,
        }),
      });
      setDraft(d);
      // Every subject starts collapsed — a wall of nodes reads as "rubber-stamp this."
      setExpandedSubjects({});
    } catch (err) {
      setError(err.message);
    }
    setGenerating(false);
  };

  useEffect(() => {
    if (step === 'tree' && !draft && !generating) generateTree('');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step]);

  // Deliberately does NOT clear the draft first. `generating` already drives the
  // loading card, and clearing it meant a failed regenerate left
  // draft=null + generating=false — a state NO render branch matched, so the
  // tree, the context box and Continue all vanished at once with no way back
  // (this effect is keyed on [step], so it never re-fires to recover).
  const regenerateTree = () => generateTree(freeText);

  const createGoal = async () => {
    setBusy(true);
    setError('');
    try {
      const g = await apiFetch('/api/career/goals/', {
        method: 'POST',
        body: JSON.stringify({ role_key: roleKey, title: goalTitle.trim(), target_date: targetDate || null }),
      });
      setGoal(g);
      setStep('diagnostic');
    } catch (err) {
      setError(err.message);
    }
    setBusy(false);
  };

  const submitDiagnostic = async () => {
    const answered = probes.filter((p) => (answers[p.stable_key] || '').trim());
    if (answered.length === 0) {
      setStep('tree');
      return;
    }
    setBusy(true);
    setError('');
    try {
      const body = answered.map((p) => ({ stable_key: p.stable_key, answer: answers[p.stable_key] }));
      const results = await apiFetch('/api/career/diagnostic/submit', { method: 'POST', body: JSON.stringify(body) });
      setDiagnosticResults(results);
      setStep('tree');
    } catch (err) {
      if (err.status === 404) setStep('tree'); // grader disabled mid-flow — never block onboarding
      else setError(err.message);
    }
    setBusy(false);
  };

  const updateNode = (si, ni, patch) => {
    setDraft((d) => ({
      ...d,
      subjects: d.subjects.map((s, i) => (i !== si ? s : { ...s, nodes: s.nodes.map((n, j) => (j !== ni ? n : { ...n, ...patch })) })),
    }));
  };
  const deleteNode = (si, ni) => {
    setDraft((d) => ({
      ...d,
      subjects: d.subjects.map((s, i) => (i !== si ? s : { ...s, nodes: s.nodes.filter((_, j) => j !== ni) })),
    }));
  };
  const toggleSubject = (key) => setExpandedSubjects((e) => ({ ...e, [key]: !e[key] }));

  const commitTree = async () => {
    setBusy(true);
    setError('');
    try {
      const body = {
        ...draft,
        diagnostic_results: diagnosticResults.length
          ? diagnosticResults.map((r) => ({ stable_key: r.stable_key, grade: r.grade, recalled: r.recalled }))
          : undefined,
      };
      const committedGoal = await apiFetch('/api/career/tree/commit', { method: 'POST', body: JSON.stringify(body) });
      onCommitted(committedGoal);
    } catch (err) {
      setError(err.message);
    }
    setBusy(false);
  };

  return (
    <div className="max-w-3xl mx-auto w-full p-4 md:p-8 pb-20 md:pb-8 animate-in fade-in duration-300">
      <Stepper current={step} />

      {step === 'goal' && (
        <GoalStep
          templates={templates}
          roleKey={roleKey} setRoleKey={setRoleKey}
          goalTitle={goalTitle} setGoalTitle={setGoalTitle}
          targetDate={targetDate} setTargetDate={setTargetDate}
          busy={busy} error={error}
          onContinue={createGoal}
        />
      )}

      {step === 'diagnostic' && (
        <DiagnosticStep
          probes={probes} probesLoaded={probesLoaded}
          answers={answers} setAnswer={(k, v) => setAnswers((a) => ({ ...a, [k]: v }))}
          busy={busy} error={error}
          onSubmit={submitDiagnostic}
          onSkip={() => setStep('tree')}
        />
      )}

      {step === 'tree' && (
        <TreeStep
          draft={draft} generating={generating} error={error}
          expandedSubjects={expandedSubjects} toggleSubject={toggleSubject}
          updateNode={updateNode} deleteNode={deleteNode}
          freeText={freeText} setFreeText={setFreeText}
          onRegenerate={regenerateTree}
          onContinue={() => setStep('confirm')}
        />
      )}

      {step === 'confirm' && draft && (
        <ConfirmStep draft={draft} busy={busy} error={error} onBack={() => setStep('tree')} onConfirm={commitTree} />
      )}
    </div>
  );
}

export default CareerOnboarding;
