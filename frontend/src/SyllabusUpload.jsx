import React, { useRef, useState } from 'react';
import {
  ArrowLeft, ArrowRight, FileUp, Loader2, Sparkles, Trash2, Plus,
  ChevronUp, ChevronDown, GraduationCap, Pencil, Check, ClipboardPaste,
} from 'lucide-react';
import { useNavigate, Link } from 'react-router-dom';
import { apiFetch } from './lib/api';
import { useSeo } from './lib/useSeo';

const MAX_PDF_MB = 10;
const MAX_TEXT_CHARS = 40000; // mirrors backend MAX_SYLLABUS_CHARS

// Phases: 'upload' → 'extracting' → 'review' → 'saving'
// The draft is NEVER auto-saved — the user reviews/edits, then commits explicitly.

const EXTRACT_STEPS = [
  'Reading your syllabus…',
  'Finding units and chapters…',
  'Breaking chapters into recallable topics…',
  'Assembling your roadmap…',
];

function ExtractingCard() {
  const [step, setStep] = useState(0);
  React.useEffect(() => {
    const t = setInterval(() => setStep((s) => Math.min(s + 1, EXTRACT_STEPS.length - 1)), 12000);
    return () => clearInterval(t);
  }, []);
  return (
    <div className="bg-white border border-[rgba(15,23,42,0.08)] rounded-3xl shadow-sm p-10 flex flex-col items-center text-center">
      <Loader2 size={32} className="text-[#0891B2] animate-spin mb-4" />
      <h3 className="font-sans text-lg font-semibold text-[#0F172A] mb-1">{EXTRACT_STEPS[step]}</h3>
      <p className="font-sans text-sm text-[#64748B] max-w-sm">
        This usually takes 30–60 seconds. We're decomposing each syllabus line into atomic,
        testable topics — the sharper the topics, the better your reviews.
      </p>
    </div>
  );
}

function TopicRow({ topic, onChange, onDelete }) {
  return (
    <div className="group flex items-start gap-2 py-1.5">
      <span className="mt-2.5 w-1.5 h-1.5 rounded-full bg-[#0891B2]/50 shrink-0" />
      <div className="flex-1 min-w-0">
        <input
          value={topic.title}
          onChange={(e) => onChange({ ...topic, title: e.target.value })}
          placeholder="Topic title"
          className="w-full font-sans text-sm text-[#0F172A] bg-transparent border-b border-transparent hover:border-[rgba(15,23,42,0.1)] focus:border-[#0891B2] focus:outline-none py-0.5"
        />
        <input
          value={topic.description}
          onChange={(e) => onChange({ ...topic, description: e.target.value })}
          placeholder="What should you be able to recall? (optional)"
          className="w-full font-sans text-xs text-[#64748B] bg-transparent border-b border-transparent hover:border-[rgba(15,23,42,0.1)] focus:border-[#0891B2] focus:outline-none py-0.5"
        />
      </div>
      <button
        onClick={onDelete}
        title="Remove topic"
        className="opacity-0 group-hover:opacity-100 text-[#94A3B8] hover:text-red-500 transition-all p-1 shrink-0"
      >
        <Trash2 size={14} />
      </button>
    </div>
  );
}

function UnitCard({ unit, index, count, onChange, onDelete, onMove }) {
  const setTopic = (i, t) => {
    const topics = unit.topics.slice();
    topics[i] = t;
    onChange({ ...unit, topics });
  };
  const deleteTopic = (i) => onChange({ ...unit, topics: unit.topics.filter((_, j) => j !== i) });
  const addTopic = () => onChange({ ...unit, topics: [...unit.topics, { title: '', description: '' }] });

  return (
    <div className="bg-white border border-[rgba(15,23,42,0.08)] rounded-2xl shadow-sm p-4 md:p-5">
      <div className="flex items-center gap-2 mb-2">
        <span className="font-mono text-[10px] font-semibold text-[#0891B2] bg-[#0891B2]/10 rounded px-1.5 py-0.5 shrink-0">
          UNIT {index + 1}
        </span>
        <input
          value={unit.title}
          onChange={(e) => onChange({ ...unit, title: e.target.value })}
          placeholder="Unit title"
          className="flex-1 min-w-0 font-sans text-sm font-semibold text-[#0F172A] bg-transparent border-b border-transparent hover:border-[rgba(15,23,42,0.1)] focus:border-[#0891B2] focus:outline-none py-0.5"
        />
        <div className="flex items-center gap-0.5 shrink-0">
          <button onClick={() => onMove(-1)} disabled={index === 0} title="Move up"
            className="p-1 text-[#94A3B8] hover:text-[#0F172A] disabled:opacity-30">
            <ChevronUp size={15} />
          </button>
          <button onClick={() => onMove(1)} disabled={index === count - 1} title="Move down"
            className="p-1 text-[#94A3B8] hover:text-[#0F172A] disabled:opacity-30">
            <ChevronDown size={15} />
          </button>
          <button onClick={onDelete} title="Remove unit" className="p-1 text-[#94A3B8] hover:text-red-500">
            <Trash2 size={15} />
          </button>
        </div>
      </div>

      <div className="pl-1 divide-y divide-[rgba(15,23,42,0.04)]">
        {unit.topics.map((t, i) => (
          <TopicRow key={i} topic={t} onChange={(nt) => setTopic(i, nt)} onDelete={() => deleteTopic(i)} />
        ))}
      </div>

      <button
        onClick={addTopic}
        className="mt-2 flex items-center gap-1.5 font-sans text-xs text-[#0891B2] hover:text-[#0F172A] transition-colors"
      >
        <Plus size={13} /> Add topic
      </button>
    </div>
  );
}

function SyllabusUpload() {
  const navigate = useNavigate();
  const fileInput = useRef(null);
  const [phase, setPhase] = useState('upload');
  const [mode, setMode] = useState('paste'); // 'paste' (token-cheap default) | 'pdf'
  const [pasteText, setPasteText] = useState('');
  const [error, setError] = useState('');
  const [draft, setDraft] = useState(null);
  const [dragOver, setDragOver] = useState(false);

  useSeo(
    'Upload a Syllabus · Build Your Own Roadmap | RetainHQ',
    'Upload your university syllabus or curriculum PDF and get a topic-by-topic roadmap tracked with spaced repetition.'
  );

  const handleFile = async (file) => {
    setError('');
    if (!file) return;
    if (file.type !== 'application/pdf') {
      setError('Please upload a PDF file.');
      return;
    }
    if (file.size > MAX_PDF_MB * 1024 * 1024) {
      setError(`PDF is too large — the limit is ${MAX_PDF_MB} MB.`);
      return;
    }
    setPhase('extracting');
    try {
      const form = new FormData();
      form.append('file', file);
      const data = await apiFetch('/api/syllabus/extract', { method: 'POST', body: form });
      setDraft(data);
      setPhase('review');
    } catch (err) {
      setError(err.message || 'Extraction failed — try again.');
      setPhase('upload');
    }
  };

  const handleText = async () => {
    setError('');
    const text = pasteText.trim();
    if (!text) return;
    if (text.length > MAX_TEXT_CHARS) {
      setError(`That's a lot of text (${text.length.toLocaleString()} chars) — paste just the units/chapters (limit ${MAX_TEXT_CHARS.toLocaleString()}).`);
      return;
    }
    setPhase('extracting');
    try {
      const data = await apiFetch('/api/syllabus/extract-text', {
        method: 'POST',
        body: JSON.stringify({ text }),
      });
      setDraft(data);
      setPhase('review');
    } catch (err) {
      setError(err.message || 'Extraction failed — try again.');
      setPhase('upload');
    }
  };

  const totalTopics = draft
    ? draft.units.reduce((n, u) => n + u.topics.filter((t) => t.title.trim()).length, 0)
    : 0;

  const save = async () => {
    // Client-side prune: drop empty topics/units before commit.
    const units = draft.units
      .map((u) => ({
        title: u.title.trim(),
        topics: u.topics
          .filter((t) => t.title.trim())
          .map((t) => ({ title: t.title.trim(), description: (t.description || '').trim() })),
      }))
      .filter((u) => u.title && u.topics.length > 0);
    if (!draft.title.trim() || units.length === 0) {
      setError('Give the roadmap a title and keep at least one unit with topics.');
      return;
    }
    setError('');
    setPhase('saving');
    try {
      const res = await apiFetch('/api/syllabus/commit', {
        method: 'POST',
        body: JSON.stringify({
          title: draft.title.trim(),
          description: (draft.description || '').trim(),
          units,
        }),
      });
      navigate(`/roadmaps/${res.roadmap_id}`);
    } catch (err) {
      setError(err.message || 'Saving failed — try again.');
      setPhase('review');
    }
  };

  const setUnit = (i, u) => {
    const units = draft.units.slice();
    units[i] = u;
    setDraft({ ...draft, units });
  };
  const deleteUnit = (i) => setDraft({ ...draft, units: draft.units.filter((_, j) => j !== i) });
  const moveUnit = (i, dir) => {
    const j = i + dir;
    if (j < 0 || j >= draft.units.length) return;
    const units = draft.units.slice();
    [units[i], units[j]] = [units[j], units[i]];
    setDraft({ ...draft, units });
  };
  const addUnit = () =>
    setDraft({ ...draft, units: [...draft.units, { title: '', topics: [{ title: '', description: '' }] }] });

  return (
    <div className="relative max-w-3xl mx-auto w-full p-4 md:p-8 pb-20 md:pb-8 animate-in fade-in duration-300">
      <Link to="/roadmaps" className="inline-flex items-center gap-1.5 font-sans text-sm text-[#64748B] hover:text-[#0F172A] mb-6">
        <ArrowLeft size={15} /> Roadmaps
      </Link>

      <header className="mb-6">
        <h2 className="font-sans text-2xl font-semibold text-[#0F172A] flex items-center gap-2">
          <Sparkles size={22} className="text-[#0891B2]" /> Bring Your Own Path
        </h2>
        <p className="font-sans text-sm text-[#64748B] mt-1">
          Paste your syllabus (or upload the PDF) — we'll turn it into a topic-by-topic roadmap.
          You review and edit everything before it's saved; each topic becomes a trackable node
          you can log and review.
        </p>
      </header>

      {error && (
        <div className="mb-4 px-4 py-3 rounded-xl bg-red-50 border border-red-200 font-sans text-sm text-red-700">
          {error}
        </div>
      )}

      {phase === 'upload' && (
        <div className="flex flex-col gap-4">
          {/* Mode tabs — paste-text first: it's the token-cheap path */}
          <div className="flex items-center gap-1 bg-[rgba(15,23,42,0.04)] rounded-xl p-1 self-start">
            <button
              onClick={() => { setMode('paste'); setError(''); }}
              className={`flex items-center gap-1.5 font-sans text-sm px-3.5 py-1.5 rounded-lg transition-colors ${
                mode === 'paste' ? 'bg-white text-[#0F172A] font-semibold shadow-sm' : 'text-[#64748B] hover:text-[#0F172A]'
              }`}
            >
              <ClipboardPaste size={14} /> Paste text
            </button>
            <button
              onClick={() => { setMode('pdf'); setError(''); }}
              className={`flex items-center gap-1.5 font-sans text-sm px-3.5 py-1.5 rounded-lg transition-colors ${
                mode === 'pdf' ? 'bg-white text-[#0F172A] font-semibold shadow-sm' : 'text-[#64748B] hover:text-[#0F172A]'
              }`}
            >
              <FileUp size={14} /> Upload PDF
            </button>
          </div>

          {mode === 'paste' && (
            <div className="bg-white border border-[rgba(15,23,42,0.08)] rounded-3xl shadow-sm p-4 md:p-6">
              <textarea
                value={pasteText}
                onChange={(e) => setPasteText(e.target.value)}
                placeholder={'Paste the contents of the PDF here to save tokens.\n\nJust the units/chapters and their topics is enough — you can skip grading policy, textbook lists, and other admin pages.'}
                rows={12}
                className="w-full font-sans text-sm text-[#0F172A] bg-transparent resize-y focus:outline-none placeholder:text-[#94A3B8] min-h-[220px]"
              />
              <div className="flex items-center justify-between gap-3 mt-3 pt-3 border-t border-[rgba(15,23,42,0.06)]">
                <span className={`font-mono text-[11px] ${pasteText.length > MAX_TEXT_CHARS ? 'text-red-500' : 'text-[#94A3B8]'}`}>
                  {pasteText.length.toLocaleString()} / {MAX_TEXT_CHARS.toLocaleString()} chars
                </span>
                <button
                  onClick={handleText}
                  disabled={!pasteText.trim() || pasteText.trim().length > MAX_TEXT_CHARS}
                  className="flex items-center gap-1.5 bg-[#0891B2] hover:bg-[#0E7490] text-white font-sans text-sm font-semibold px-4 py-2 rounded-xl transition-colors disabled:opacity-40"
                >
                  <Sparkles size={15} /> Build roadmap <ArrowRight size={14} />
                </button>
              </div>
            </div>
          )}

          {mode === 'pdf' && (
            <div
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFile(e.dataTransfer.files?.[0]); }}
              onClick={() => fileInput.current?.click()}
              className={`bg-white rounded-3xl shadow-sm p-10 md:p-14 flex flex-col items-center text-center cursor-pointer transition-all border-2 border-dashed ${
                dragOver ? 'border-[#0891B2] bg-[#0891B2]/5' : 'border-[rgba(15,23,42,0.12)] hover:border-[#0891B2]/60'
              }`}
            >
              <input
                ref={fileInput}
                type="file"
                accept="application/pdf"
                className="hidden"
                onChange={(e) => handleFile(e.target.files?.[0])}
              />
              <div className="w-14 h-14 rounded-2xl bg-[#0891B2]/10 border border-[#0891B2]/20 flex items-center justify-center mb-4">
                <FileUp size={24} className="text-[#0891B2]" />
              </div>
              <h3 className="font-sans text-lg font-semibold text-[#0F172A] mb-1">Drop your syllabus PDF here</h3>
              <p className="font-sans text-sm text-[#64748B] mb-4">or click to browse — up to {MAX_PDF_MB} MB</p>
              <p className="font-mono text-[10px] text-[#94A3B8] uppercase tracking-wider">
                University syllabus · bootcamp schedule · exam curriculum
              </p>
            </div>
          )}
        </div>
      )}

      {phase === 'extracting' && <ExtractingCard />}

      {(phase === 'review' || phase === 'saving') && draft && (
        <div className="flex flex-col gap-4">
          <div className="bg-white border border-[rgba(15,23,42,0.08)] rounded-2xl shadow-sm p-4 md:p-5">
            <div className="flex items-center gap-2 mb-1">
              <GraduationCap size={16} className="text-[#0891B2] shrink-0" />
              <input
                value={draft.title}
                onChange={(e) => setDraft({ ...draft, title: e.target.value })}
                placeholder="Roadmap title"
                className="flex-1 font-sans text-lg font-semibold text-[#0F172A] bg-transparent border-b border-transparent hover:border-[rgba(15,23,42,0.1)] focus:border-[#0891B2] focus:outline-none py-0.5"
              />
            </div>
            <input
              value={draft.description || ''}
              onChange={(e) => setDraft({ ...draft, description: e.target.value })}
              placeholder="One-line description (optional)"
              className="w-full font-sans text-sm text-[#64748B] bg-transparent border-b border-transparent hover:border-[rgba(15,23,42,0.1)] focus:border-[#0891B2] focus:outline-none py-0.5"
            />
            <div className="flex items-center gap-2 mt-2">
              <Pencil size={12} className="text-[#94A3B8]" />
              <span className="font-sans text-xs text-[#64748B]">
                Everything below is editable — rename, remove, or add topics. Nothing is saved until you hit Save.
              </span>
            </div>
          </div>

          {draft.units.map((u, i) => (
            <UnitCard
              key={i}
              unit={u}
              index={i}
              count={draft.units.length}
              onChange={(nu) => setUnit(i, nu)}
              onDelete={() => deleteUnit(i)}
              onMove={(dir) => moveUnit(i, dir)}
            />
          ))}

          <button
            onClick={addUnit}
            className="flex items-center justify-center gap-1.5 font-sans text-sm text-[#0891B2] hover:text-[#0F172A] border-2 border-dashed border-[rgba(15,23,42,0.1)] hover:border-[#0891B2]/50 rounded-2xl py-3 transition-colors"
          >
            <Plus size={15} /> Add unit
          </button>

          {/* Sticky save bar */}
          <div className="sticky bottom-16 md:bottom-4 bg-[#0F172A] text-white rounded-2xl shadow-xl px-5 py-3.5 flex items-center justify-between gap-3">
            <span className="font-mono text-xs text-white/70">
              {draft.units.length} unit{draft.units.length !== 1 ? 's' : ''} · {totalTopics} topic{totalTopics !== 1 ? 's' : ''}
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => { setDraft(null); setPhase('upload'); }}
                disabled={phase === 'saving'}
                className="font-sans text-xs text-white/70 hover:text-white px-3 py-2 disabled:opacity-50"
              >
                Start over
              </button>
              <button
                onClick={save}
                disabled={phase === 'saving' || totalTopics === 0}
                className="flex items-center gap-1.5 bg-[#0891B2] hover:bg-[#0E7490] font-sans text-sm font-semibold px-4 py-2 rounded-xl transition-colors disabled:opacity-50"
              >
                {phase === 'saving'
                  ? <><Loader2 size={15} className="animate-spin" /> Saving…</>
                  : <><Check size={15} /> Save roadmap <ArrowRight size={14} /></>}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default SyllabusUpload;
