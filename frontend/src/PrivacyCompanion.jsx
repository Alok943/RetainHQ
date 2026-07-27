import React from 'react';
import { Link } from 'react-router-dom';
import Logo from './Logo';
import { useSeo } from './lib/useSeo';

/**
 * Public privacy policy for the RetainHQ Companion browser extension —
 * required by AMO (IMPLEMENTATION-amo-submission.md §1) and linked from the
 * Firefox listing / install consent screen. Reachable signed-out, mounted
 * outside the authed AppLayout shell (App.jsx) so it renders standalone with
 * no sidebar and no session check, at a stable URL: /privacy/companion.
 *
 * Every claim below must stay defensible against the actual code — do not
 * soften or inflate. Sources: extension/src/content/llm_metadata.ts (titles
 * only, never chat content), extension/src/content/leetcode.ts (reflection
 * fields), extension/src/consent.ts (tier gating), backend/app/services/
 * llm_classifier.py (Gemini paid-tier — SYSTEM-OVERVIEW.md D-043 confirms
 * paid-tier prompts/responses are not used for training, unlike the free tier).
 */
function PrivacyCompanion() {
  useSeo(
    'Privacy Policy — RetainHQ Companion | RetainHQ',
    'What the RetainHQ Companion browser extension collects, what it never collects, where data goes, and how to delete it.'
  );

  return (
    <div className="min-h-screen bg-[#f9f9f6] text-[#1a1c1b] font-sans">
      <header className="border-b border-[rgba(15,23,42,0.08)] px-6 py-5">
        <div className="max-w-3xl mx-auto flex items-center gap-2.5">
          <Link to="/" className="flex items-center gap-2.5">
            <Logo variant="dark" className="h-6 w-auto" />
            <span className="font-semibold text-lg tracking-tight text-[#0F172A]">RetainHQ</span>
          </Link>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-12">
        <p className="text-xs font-semibold uppercase tracking-wide text-[#0891B2] mb-2">RetainHQ Companion</p>
        <h1 className="text-3xl font-semibold tracking-tight text-[#0F172A] mb-1">Privacy Policy</h1>
        <p className="text-sm text-[#64748B] mb-10">Last updated 2026-07-27</p>

        <Section title="What it does">
          <p>
            RetainHQ Companion is a browser extension that notices what you study — videos,
            courses, LeetCode problems — so your RetainHQ account can schedule spaced reviews
            before you forget it. It requires a RetainHQ account to do anything with what it
            observes.
          </p>
        </Section>

        <Section title="What we collect">
          <ul className="list-disc pl-5 space-y-1.5">
            <li>Page titles, domains, and how long a tab stayed open (YouTube, Coursera, and — if you turn it on — ChatGPT, Claude, or Gemini).</li>
            <li>LeetCode problem slugs and Accepted-submission events.</li>
            <li>Optional reflection you type after a LeetCode solve: a 1-5 confidence rating, whether you needed a hint, and an optional free-text note about your biggest mistake.</li>
            <li>PDF filenames and viewing durations.</li>
          </ul>
        </Section>

        <Section title="What we never collect">
          <ul className="list-disc pl-5 space-y-1.5">
            <li>The contents of any page you visit.</li>
            <li>The text of your AI chats, on any tier — the extension's ChatGPT/Claude/Gemini
              integration reads only <code className="text-[13px] bg-[rgba(15,23,42,0.05)] px-1 py-0.5 rounded">document.title</code>, never the conversation itself.</li>
          </ul>
        </Section>

        <Section title="Where it goes">
          <p>
            Everything above goes to your own RetainHQ account, via the RetainHQ API, into our
            Supabase database. Nothing is sold, shared with third parties, or used for
            advertising.
          </p>
          <p className="mt-3">
            If you turn on "Smart tracking," page titles from AI chat sites are classified by
            Google's Gemini API (paid tier) to distinguish studying from copy-pasting an answer.
            Only the title is sent — never chat content — and Google's paid-tier terms mean that
            data is not used to train models. "On-device AI" and "Titles only" send nothing to
            Gemini at all.
          </p>
        </Section>

        <Section title="Consent">
          <p>
            Access to ChatGPT, Claude, or Gemini tabs is an optional permission you grant
            explicitly, through a one-time choice screen in the extension popup. You can change
            it at any time from that same popup — switching tiers immediately grants or revokes
            the underlying browser permission.
          </p>
        </Section>

        <Section title="Deletion">
          <p>
            Every tracked session appears in your RetainHQ evidence log and can be deleted there,
            individually, at any time.
          </p>
        </Section>

        <Section title="Contact">
          <p>
            Questions about this policy: <a href="mailto:aloksingh98541@gmail.com" className="text-[#0891B2] hover:underline">aloksingh98541@gmail.com</a>.
          </p>
        </Section>
      </main>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <section className="mb-8">
      <h2 className="text-lg font-semibold text-[#0F172A] mb-2.5">{title}</h2>
      <div className="text-[15px] leading-relaxed text-[#334155]">{children}</div>
    </section>
  );
}

export default PrivacyCompanion;
