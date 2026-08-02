import React, { useEffect, useState } from 'react';
import { ChevronRight, ScrollText, SlidersHorizontal } from 'lucide-react';
import { apiFetch } from './lib/api';

/**
 * "Why is this number what it is" — the evidence trail (SPEC-career-coach-phase1 §7).
 *
 * Was an admin-gated dev instrument until 2026-08-02, then un-gated for every
 * user WITHOUT a redesign, which made it the app's most confusing screen: raw
 * model variables as column headers (`m_learned` / `r` / `m` / `w`), a
 * JSON.stringify dump of the summary, a "POST /recompute" button, and 120+
 * never-touched nodes padding the list. The founder's review of it was, in
 * full, "wtf is this, how will a user understand??".
 *
 * Rewritten around the question a user actually has — *how well do I know this,
 * and why do you think that* — under three rules:
 *
 * 1. NOTHING IS HIDDEN, things are TRANSLATED. Every number the old page showed
 *    is still reachable; the raw ones moved behind an Advanced toggle instead of
 *    being deleted. This page's whole job is trust, and a page that quietly drops
 *    the number it can't explain has failed at that job.
 * 2. STATE THE NEGATIVE SPACE. Evidence that was removed, evidence that counted
 *    for zero, and activity that matched no topic all get said out loud. The old
 *    page marked deleted rows with `line-through` alone — invisible at a glance
 *    and, as the founder discovered, gone entirely on copy-paste, so a purged
 *    import read as live data scoring 0.000.
 * 3. NEVER INFLATE. Labels come from the same thresholds the scheduler uses
 *    (services/evidence.py), and low-confidence numbers say so next to the number.
 */

// --- translation layer -----------------------------------------------------
// The vocabulary here is the product decision. Every mapping mirrors a rule in
// services/evidence.py or evidence_weights.py — when those thresholds move,
// these labels must move with them or the page starts lying.

const STATE_COPY = {
  // Thresholds: evidence.node_state(). `interview_ready` additionally requires
  // an unassisted verified pass, which is why "on your own" is in its blurb.
  unexposed: { label: 'Not started', tone: 'text-[#64748B]', blurb: 'No evidence recorded yet.' },
  exposed: { label: 'Just started', tone: 'text-[#B45309]', blurb: 'Some exposure. Not enough to call this learned.' },
  practicing: { label: 'Practicing', tone: 'text-[#B45309]', blurb: 'Real evidence building up. Keep going.' },
  solid: { label: 'Solid', tone: 'text-[#0F766E]', blurb: 'Consistent evidence across your work.' },
  interview_ready: { label: 'Interview ready', tone: 'text-[#166534]', blurb: 'Solid, including at least one solve with no help.' },
};

const CONFIDENCE_COPY = {
  // evidence.confidence(): count + recency + how many kinds of evidence.
  high: 'Confident — several recent pieces, from more than one kind of evidence.',
  medium: 'Fairly confident — a few recent pieces.',
  low: 'Low confidence — very little evidence, or none of it recent.',
};

// Full prepositional PHRASES, not bare names. A name plus a hardcoded "from"
// produced "Recall review from a RetainHQ review"; the preposition belongs to
// the source, not to the sentence template.
const SOURCE_PHRASE = {
  leetcode: 'on LeetCode',
  neetcode: 'on NeetCode',
  github: 'on GitHub',
  manual: 'logged by hand',
  retainhq_review: 'in RetainHQ',
  retainhq_coach: 'with the RetainHQ coach',
  companion_desktop: 'tracked by the desktop companion',
  companion_android: 'tracked by the Android companion',
  companion_browser: 'tracked by the browser companion',
};

const ASSISTANCE_COPY = {
  none: 'on your own',
  hint: 'with a hint',
  llm_assisted: 'with AI help',
  solution_seen: 'after seeing the solution',
};

// Says what was OBSERVED, not how much it is trusted — "tier 1" means nothing
// to a user, and "verified" without saying by whom overclaims. Must stay
// event-type-agnostic: T3 covers both a NeetCode checkmark and a tracked study
// session, so wording like "marked complete" (an earlier draft) is nonsense on
// half the events that carry it.
const TIER_COPY = {
  T1_verified_external: 'Confirmed by a judged submission',
  T2_verified_internal: 'Graded inside RetainHQ',
  T3_observed: 'Observed, not verified',
  T4_claimed: 'Self-reported',
};

const article = (word) => (/^[aeiou]/i.test(word) ? 'an' : 'a');

function describeEvent(e) {
  const where = SOURCE_PHRASE[e.source] ?? e.source;
  const how = e.assistance ? ` ${ASSISTANCE_COPY[e.assistance] ?? e.assistance}` : '';

  switch (e.event_type) {
    case 'PROBLEM_SOLVED': {
      const verb = e.outcome === 'pass' ? 'Solved' : e.outcome === 'partial' ? 'Partly solved' : 'Attempted';
      const noun = e.difficulty ? `${e.difficulty} problem` : 'problem';
      return `${verb} ${article(noun)} ${noun} ${where}${how}`;
    }
    case 'RECALL_GRADED':
      return `Recall review ${where}${e.grade != null ? ` — scored ${Math.round(e.grade * 100)}%` : ''}`;
    case 'CONCEPT_EXPLAINED':
      return `Explained this concept ${where}`;
    case 'ARTIFACT_BUILT':
      return `Built something using this ${where}`;
    case 'CONTENT_CONSUMED':
      return `Read or watched material on this ${where}`;
    case 'TIME_BLOCK':
      return `Study time ${where}`;
    default:
      return `${e.event_type} — ${where}`;
  }
}

const pct = (v) => `${Math.round((v ?? 0) * 100)}%`;

function fmtDate(iso) {
  if (!iso) return null;
  return new Date(iso).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' });
}

function relativeDays(iso) {
  if (!iso) return 'never';
  const days = Math.floor((Date.now() - new Date(iso).getTime()) / 86400000);
  if (days <= 0) return 'today';
  if (days === 1) return 'yesterday';
  if (days < 30) return `${days} days ago`;
  const months = Math.round(days / 30);
  if (days < 365) return `${months} month${months === 1 ? '' : 's'} ago`;
  const years = Math.round(days / 365);
  return `${years} year${years === 1 ? '' : 's'} ago`;
}

// --- pieces ----------------------------------------------------------------

function StrengthBar({ value, muted }) {
  return (
    <div className="w-full h-1.5 rounded-full bg-[rgba(15,23,42,0.06)] overflow-hidden">
      <div
        className="h-full rounded-full transition-all duration-700 ease-out"
        style={{ width: `${Math.max(value * 100, value > 0 ? 2 : 0)}%`, backgroundColor: muted ? '#94a3b8' : '#0891B2' }}
      />
    </div>
  );
}

function Stat({ label, value, sub }) {
  return (
    <div className="kinetic-card bg-white p-4">
      <div className="font-sans text-[10px] font-bold uppercase tracking-wider text-[#64748B]">{label}</div>
      <div className="font-mono text-2xl font-semibold text-[#0F172A] mt-1">{value}</div>
      {sub && <div className="font-sans text-xs text-[#64748B] mt-1 leading-snug">{sub}</div>}
    </div>
  );
}

function EventRow({ event, advanced }) {
  const removed = !!event.deleted_at;
  // Weight 0 with nothing deleted is real and currently invisible on every
  // other surface: a TIME_BLOCK, a T4 claim, or a failed attempt under the
  // minimum duration all legitimately contribute nothing. Saying "didn't count"
  // is the honest version of a row that silently changes no number.
  const didNothing = !removed && event.weight === 0;

  return (
    <li className={`flex gap-3 py-3 border-b border-[rgba(15,23,42,0.06)] last:border-0 ${removed ? 'opacity-50' : ''}`}>
      <div className="flex-1 min-w-0">
        <div className={`font-sans text-sm text-[#0F172A] ${removed ? 'line-through' : ''}`}>
          {describeEvent(event)}
        </div>
        <div className="font-sans text-xs text-[#64748B] mt-0.5 flex flex-wrap items-center gap-x-2 gap-y-1">
          <span className="font-mono">{fmtDate(event.occurred_at)}</span>
          <span aria-hidden="true">·</span>
          <span>{TIER_COPY[event.trust_tier] ?? event.trust_tier}</span>
          {removed && (
            // A badge, not just strikethrough. The old page's line-through was
            // invisible at a glance AND stripped on copy, so a fully purged
            // import read as live data that scored zero.
            <span className="font-sans text-[10px] font-bold uppercase tracking-wide px-1.5 py-0.5 rounded-full bg-[rgba(15,23,42,0.06)] text-[#ba1a1a]">
              Removed — not counted
            </span>
          )}
          {didNothing && (
            <span className="font-sans text-[10px] font-bold uppercase tracking-wide px-1.5 py-0.5 rounded-full bg-[rgba(15,23,42,0.06)] text-[#64748B]">
              Didn't change the number
            </span>
          )}
        </div>
      </div>

      <div className="text-right shrink-0">
        {!removed && event.weight > 0 && (
          <div className="font-mono text-sm text-[#0F766E]">+{event.weight.toFixed(2)}</div>
        )}
        {advanced && (
          <div className="font-mono text-[11px] text-[#64748B] mt-0.5">→ {event.m_learned_after.toFixed(3)}</div>
        )}
      </div>

      {advanced && !removed && (
        <button
          className="font-sans text-xs text-[#ba1a1a] underline self-start shrink-0"
          onClick={async () => {
            if (!confirm('Remove this piece of evidence? Your mastery numbers will be recalculated without it.')) return;
            await apiFetch(`/api/evidence/events/${event.id}`, { method: 'DELETE' });
            window.location.reload();
          }}
        >
          remove
        </button>
      )}
    </li>
  );
}

function NodeTrail({ nodeId, advanced }) {
  const [events, setEvents] = useState(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let live = true;
    apiFetch(`/api/evidence/nodes/${nodeId}/events`)
      .then((data) => live && setEvents(data))
      .catch(() => live && setError(true));
    return () => { live = false; };
  }, [nodeId]);

  if (error) return <div className="font-sans text-sm text-[#64748B] py-3">Couldn't load this trail. Try again.</div>;
  if (!events) return <div className="font-sans text-sm text-[#64748B] py-3">Loading…</div>;
  if (events.length === 0) {
    return <div className="font-sans text-sm text-[#64748B] py-3">Nothing recorded against this topic yet.</div>;
  }

  return (
    <div className="pt-1">
      <div className="font-sans text-[10px] font-bold uppercase tracking-wider text-[#64748B] mb-1">
        What this is based on
      </div>
      <ul>
        {events.map((e) => <EventRow key={e.id} event={e} advanced={advanced} />)}
      </ul>
    </div>
  );
}

function NodeCard({ node, expanded, onToggle, advanced }) {
  const state = STATE_COPY[node.state] ?? STATE_COPY.unexposed;
  const untouched = node.evidence_count === 0;

  return (
    <div className="kinetic-card bg-white">
      <button
        className="w-full text-left p-4 flex items-start gap-3 hover:bg-[rgba(15,23,42,0.02)] transition-colors"
        onClick={onToggle}
        aria-expanded={expanded}
      >
        <ChevronRight
          size={16}
          className={`text-[#64748B] mt-1 shrink-0 transition-transform duration-200 ${expanded ? 'rotate-90' : ''}`}
        />
        <div className="flex-1 min-w-0">
          <div className="flex items-baseline justify-between gap-3">
            <span className="font-sans text-sm font-semibold text-[#0F172A] truncate">{node.title}</span>
            <span className={`font-sans text-xs font-semibold shrink-0 ${state.tone}`}>{state.label}</span>
          </div>

          <div className="mt-2 flex items-center gap-3">
            <StrengthBar value={node.m} muted={untouched} />
            <span className="font-mono text-xs text-[#64748B] w-10 text-right shrink-0">{pct(node.m)}</span>
          </div>

          <div className="font-sans text-xs text-[#64748B] mt-2">
            {untouched ? (
              state.blurb
            ) : (
              <>
                {node.evidence_count} {node.evidence_count === 1 ? 'piece' : 'pieces'} of evidence
                {' · '}last seen {relativeDays(node.last_event_at)}
                {/* Said next to the number, never instead of it — a number
                    the app isn't sure about must carry that doubt in the UI. */}
                {node.confidence !== 'high' && <> · {node.confidence} confidence</>}
              </>
            )}
          </div>

          {advanced && (
            <div className="font-mono text-[11px] text-[#64748B] mt-2">
              m_learned {node.m_learned.toFixed(3)} · retrievability {node.r.toFixed(3)} · shown {node.m.toFixed(3)}
            </div>
          )}
        </div>
      </button>

      {expanded && (
        <div className="px-4 pb-4 pl-11 border-t border-[rgba(15,23,42,0.06)]">
          <p className="font-sans text-xs text-[#64748B] pt-3">{CONFIDENCE_COPY[node.confidence]}</p>
          <NodeTrail nodeId={node.node_id} advanced={advanced} />
        </div>
      )}
    </div>
  );
}

// --- page ------------------------------------------------------------------

function Evidence() {
  const [nodes, setNodes] = useState(null);
  const [summary, setSummary] = useState(null);
  const [expanded, setExpanded] = useState(null);
  const [advanced, setAdvanced] = useState(false);
  const [showUntouched, setShowUntouched] = useState(false);
  const [recomputing, setRecomputing] = useState(false);

  const load = () => {
    apiFetch('/api/evidence/nodes').then(setNodes).catch(() => setNodes([]));
    apiFetch('/api/evidence/summary').then(setSummary).catch(() => setSummary(null));
  };
  useEffect(load, []);

  const recompute = async () => {
    setRecomputing(true);
    try {
      await apiFetch('/api/evidence/recompute', { method: 'POST' });
      load();
    } finally {
      setRecomputing(false);
    }
  };

  const withEvidence = (nodes ?? []).filter((n) => n.evidence_count > 0);
  const untouched = (nodes ?? []).filter((n) => n.evidence_count === 0);
  // Strongest first: the list answers "what do I actually have" before "what's
  // missing", and 120+ never-touched nodes are collapsed rather than padding it.
  const visible = [...withEvidence].sort((a, b) => b.m - a.m);

  return (
    <div className="p-4 md:p-8 max-w-4xl mx-auto w-full">
      <header className="mb-6">
        <h1 className="font-sans text-xl font-bold text-[#0F172A] flex items-center gap-2">
          <ScrollText size={20} className="text-[#0891B2]" /> Your evidence
        </h1>
        <p className="font-sans text-sm text-[#64748B] mt-1 max-w-2xl">
          Every strength number in RetainHQ traces back to something you actually did. This is that
          trail — open any topic to see exactly what it's built on.
        </p>
      </header>

      {summary && (
        <section className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-6">
          <Stat label="Topics with evidence" value={summary.nodes_with_evidence} />
          <Stat label="Things recorded" value={summary.total_events} />
          {/* Surfaced deliberately. These are real captures — imported solves and
              tracked sessions — that matched no topic, so they move nothing and
              appear nowhere else in the app. Hiding the count would make the
              evidence trail look complete when it isn't. */}
          <Stat
            label="Not yet matched"
            value={summary.unmapped_events}
            sub={summary.unmapped_events > 0 ? "Recorded, but we couldn't tie these to a topic yet — they don't count toward anything." : 'Everything recorded found a topic.'}
          />
        </section>
      )}

      <div className="flex items-center justify-between gap-3 mb-3">
        <h2 className="font-sans text-sm font-semibold text-[#1a1c1b] uppercase tracking-wider">
          Topics
        </h2>
        <button
          onClick={() => setAdvanced((v) => !v)}
          className="font-sans text-xs text-[#64748B] hover:text-[#0F172A] flex items-center gap-1.5"
        >
          <SlidersHorizontal size={13} /> {advanced ? 'Hide' : 'Show'} raw numbers
        </button>
      </div>

      {advanced && (
        <div className="kinetic-card bg-gray-50 p-4 mb-3">
          <p className="font-sans text-xs text-[#64748B] leading-relaxed">
            <strong className="text-[#0F172A]">m_learned</strong> is what your evidence adds up to.{' '}
            <strong className="text-[#0F172A]">retrievability</strong> is how much of it you'd still
            recall right now, given how long it's been. <strong className="text-[#0F172A]">shown</strong>{' '}
            is the two multiplied — the number on the bar. Each piece of evidence is worth a fixed
            amount by difficulty and how much help you had.
          </p>
          <div className="flex flex-wrap items-center gap-3 mt-3">
            <button
              onClick={recompute}
              disabled={recomputing}
              className="kinetic-btn font-sans text-xs px-3 py-1.5 rounded-lg border border-[rgba(15,23,42,0.12)] disabled:opacity-50"
            >
              {recomputing ? 'Recalculating…' : 'Recalculate from scratch'}
            </button>
            {summary && (
              <span className="font-mono text-[11px] text-[#64748B]">
                weights {summary.weights_version}
              </span>
            )}
          </div>
        </div>
      )}

      {!nodes ? (
        <div className="space-y-2">
          {[0, 1, 2].map((i) => <div key={i} className="kinetic-card bg-white h-[90px] skeleton" />)}
        </div>
      ) : visible.length === 0 ? (
        <div className="kinetic-card bg-white p-6 text-center">
          <p className="font-sans text-sm text-[#0F172A] font-semibold">No evidence yet</p>
          <p className="font-sans text-sm text-[#64748B] mt-1">
            Complete a review, log an activity, or import your solved problems from the browser
            companion — anything you do shows up here.
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {visible.map((n) => (
            <NodeCard
              key={n.node_id}
              node={n}
              advanced={advanced}
              expanded={expanded === n.node_id}
              onToggle={() => setExpanded(expanded === n.node_id ? null : n.node_id)}
            />
          ))}
        </div>
      )}

      {untouched.length > 0 && (
        <div className="mt-6">
          <button
            onClick={() => setShowUntouched((v) => !v)}
            className="font-sans text-xs text-[#64748B] hover:text-[#0F172A]"
          >
            {showUntouched ? 'Hide' : 'Show'} {untouched.length} topics with nothing recorded yet
          </button>
          {showUntouched && (
            <div className="space-y-2 mt-3">
              {untouched.map((n) => (
                <NodeCard
                  key={n.node_id}
                  node={n}
                  advanced={advanced}
                  expanded={expanded === n.node_id}
                  onToggle={() => setExpanded(expanded === n.node_id ? null : n.node_id)}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default Evidence;
