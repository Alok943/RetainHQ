# SPEC — Review screen density pass

> Founder review finding (2026-07-12): **"the UI is very dense"** — specifically the
> REVIEW screen (`frontend/src/Review.jsx`), observed while running real 3-question
> sessions. This spec is the implementation handoff (Antigravity or a Sonnet session);
> Claude browser-verifies the result. **Do not change any grading/scheduling logic,
> API call, or analytics event — this is layout and disclosure only.**

## The problem, precisely

The screen stacks everything it knows at once. Worst at the **post-reveal** moment,
where the user sees simultaneously: the key-memory card, the per-question graded items
(question + user answer + correct/missed chip + note, ×3), the AI feedback sentence,
the revision note, related-subtopic suggestions, four outcome buttons, and keyboard
hints. That's 6+ competing blocks at the exact moment the user should be doing ONE
thing: judging "did I know this?" and picking an outcome.

Pre-reveal is milder but real: three question textareas render fully expanded at once,
plus the topic header, "why this card today" line, and the depth toggle.

## Information hierarchy (the design decision — build to this)

At any moment the screen has ONE primary action. Everything else is support and must
visually recede or collapse.

**Phase A — answering (pre-reveal).** Primary: the CURRENT question's textarea.
- Questions become a focused sequence: show question 1 expanded; questions 2–3 as
  collapsed rows (question text only) that expand on focus/advance. Answered ones
  collapse to a single-line row with a subtle "answered" tick. One textarea tall
  enough to think in beats three cramped ones.
- Topic title stays; the "why due" line and depth toggle drop to one quiet meta row.
- "I don't know" and "Reveal" remain always visible (bottom), unchanged behaviour.

**Phase B — judging (post-reveal).** Primary: the four outcome buttons.
- Outcome buttons move visually adjacent to the summary verdict — the user should not
  scroll past detail blocks to reach them.
- Keep expanded by default: key memory (it IS the answer) + the per-question
  correct/missed chips with the user's answer.
- Collapse by default (single-line disclosure rows, expand on tap):
  - the grader's per-question `note` text (chip stays visible; note expands),
  - `revision_note`,
  - `related_subtopics` (one row: "2 related topics to explore →").
- The AI feedback sentence stays visible but as one line attached to the suggested
  outcome, not a separate card.

**Spacing rhythm (both phases).** One consistent vertical unit between blocks —
today's mix of `mb-1/2/3/4` reads as clutter. Content column gets a comfortable
max-width; blocks separated by whitespace, not borders-inside-borders (prefer
removing inner borders over adding more).

## Boundaries

- Touch ONLY `frontend/src/Review.jsx` (+ `index.css` if a shared spacing utility is
  genuinely needed). No new dependencies, no new components outside this file.
- Do not alter: apiFetch calls, grading flows, FSRS completion payloads, analytics
  `track()` events, keyboard shortcuts (Ctrl/Cmd+Enter reveal; 1–4 outcomes), the
  depth toggle's behaviour, or the lesson-sourced question path.
- Dark mode: reuse existing color utility classes ONLY (the `html.dark` remap layer
  in `index.css` keys on them — see the recent Missed-label fix for why hardcoded
  one-offs break). No new hex values.
- Mobile (360px) must not regress — collapsed rows especially.
- Preserve the just-shipped Missed-label contrast fix (`darkColor`/`outcomeColor`).

## Acceptance criteria

1. Post-reveal, the outcome buttons are reachable without scrolling on a 1280×720
   viewport with a 3-question card.
2. At most THREE expanded content blocks visible in any phase; everything else is a
   one-line disclosure row.
3. Answering flows question-to-question without manual scrolling.
4. Zero changes to network requests or analytics events (verify by diffing the
   Network panel before/after on one full review).
5. `npm run build` green. No console errors.
6. Then STOP — Claude runs the browser pass (light + dark, desktop + 360px) before
   this is called done. Report file: `docs/REPORT-review-density.md`, one line per
   change + any FLAG where the spec fought reality.

## Explicitly out of scope (founder decisions, not this pass)

- Any redesign of the outcome buttons' shape/colors (pixel design is the founder's).
- Home-screen density (separate finding; not this file).
- Animations/transitions beyond what expanding/collapsing needs.
