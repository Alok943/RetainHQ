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
 * soften or inflate. Sources: extension/src/content/chat_extract.ts (Smart
 * tracking tier reads chat TEXT, not just titles, as of 2026-07-27 —
 * IMPLEMENTATION-companion-chat-content.md), extension/src/content/
 * llm_metadata.ts (Titles only tier — document.title alone), extension/src/
 * content/leetcode.ts (reflection fields), extension/src/consent.ts (tier
 * gating + copy-version re-consent), backend/app/services/topic_segmentation.py
 * (what the chat text is used for and what's kept), backend/app/services/
 * llm_classifier.py (Gemini paid-tier — SYSTEM-OVERVIEW.md D-043 confirms
 * paid-tier prompts/responses are not used for training, unlike the free tier).
 *
 * The "paid tier" claim below was CONFIRMED by the owner on 2026-07-27:
 * GEMINI_API_KEY is on a billed Google Cloud project. That is what makes the
 * not-used-for-training sentence true, and it now covers chat text, not just
 * page titles (D-047). If billing on that project ever lapses, this page
 * becomes false the moment it does — treat the billing status as part of the
 * policy, not as infrastructure.
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

        <Section title="Two ways to track AI chats">
          <p>
            "Smart tracking" and "Titles only" are genuinely different, not just a privacy
            slider on the same behavior:
          </p>
          <ul className="list-disc pl-5 space-y-1.5 mt-2">
            <li><strong>Smart tracking</strong> reads the text of what you and the AI wrote in
              ChatGPT, Claude, or Gemini — so a single conversation covering several topics
              (e.g. a database question, then a React bug) can be split and credited correctly,
              instead of the whole session being attributed to whatever the chat happened to be
              titled after.</li>
            <li><strong>Titles only</strong> reads nothing but the browser tab's title. It never
              sees the conversation.</li>
          </ul>
        </Section>

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
            <li>Page titles, domains, and how long a tab stayed open (YouTube, Coursera, Notion, and — if you turn it on — ChatGPT, Claude, or Gemini).</li>
            <li>On YouTube videos that have chapters: which chapters you watched and for how long,
              read from the chapter markers the video's uploader added — the same list every
              viewer already sees under the video. Not the video's captions or audio; just the
              chapter titles and your watched time per chapter, so a single long video covering
              several topics can be credited accurately instead of as one block.</li>
            <li>On the "Smart tracking" tier only: the text of your AI chat conversations, sent to
              our server and to Google Gemini so the topics you covered can be identified. Assistant
              replies are truncated before they're read; only what you typed is kept in full.</li>
            <li>LeetCode problem slugs and Accepted-submission events.</li>
            <li>Optional reflection you type after a LeetCode solve: a 1-5 confidence rating, whether you needed a hint, and an optional free-text note about your biggest mistake.</li>
            <li>PDF filenames and viewing durations.</li>
          </ul>
        </Section>

        <Section title="What we never collect">
          <ul className="list-disc pl-5 space-y-1.5">
            <li>The contents of any page you visit outside a supported study surface.</li>
            <li>The raw text of your AI chats on the "Titles only" tier — that tier's ChatGPT/
              Claude/Gemini integration reads only <code className="text-[13px] bg-[rgba(15,23,42,0.05)] px-1 py-0.5 rounded">document.title</code>, never the conversation.</li>
            <li>Even on "Smart tracking": the conversation text itself is never stored. Only a
              short, AI-written topic label survives — never a copy-pasted excerpt of what you
              or the assistant wrote.</li>
            <li>Your video's captions, transcript, or audio, on any tier — only the chapter
              titles the uploader already made public, never anything spoken in the video.</li>
          </ul>
        </Section>

        <Section title="Where it goes">
          <p>
            Everything above goes to your own RetainHQ account, via the RetainHQ API, into our
            Supabase database. Nothing is sold, shared with third parties, or used for
            advertising.
          </p>
          <p className="mt-3">
            On "Smart tracking," page titles and — for AI chat sites — conversation text are sent
            to Google's Gemini API (paid tier) to identify what you were studying and split one
            chat covering several topics into its parts. Google's paid-tier terms mean that data
            is not used to train models. "Titles only" sends nothing but a page title to Gemini,
            ever.
          </p>
        </Section>

        <Section title="Consent">
          <p>
            Access to ChatGPT, Claude, or Gemini tabs — and to their conversation text on the
            "Smart tracking" tier — is an optional permission you grant explicitly, through a
            choice screen in the extension popup. You can change it at any time from that same
            popup — switching tiers immediately grants or revokes the underlying browser
            permission. If what a tier does changes enough that this description would no
            longer be accurate, the extension re-asks rather than carrying an old choice forward.
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
            Questions about this policy: <a href="mailto:privacy@retainhq.app" className="text-[#0891B2] hover:underline">privacy@retainhq.app</a>.
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
