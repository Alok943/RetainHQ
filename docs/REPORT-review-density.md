# Review Density Change Report

> **Claude verification pass (2026-07-13), per D-013 — don't trust a self-report,
> verify against real behavior.** The Antigravity pass below shipped good pre-reveal
> work but never actually measured the spec's own acceptance criterion #1
> ("outcome buttons reachable without scrolling, 1280×720, 3-question card"). I
> measured it directly and it **failed** — the buttons sat 424px below the fold
> (needed ~647px of scroll). See "Claude's additional pass" at the bottom for the
> root cause, the fix, and verified-in-browser numbers. Original report kept below
> for the record.

## Changes Implemented (Antigravity)
- **Pre-reveal (Phase A) — Header**: Combined the "Why due" line and the "Revise" depth toggle into a single flex row beneath the topic title, separated by a pipe.
- **Pre-reveal (Phase A) — Questions Accordion**: Converted the `questionMode` list from three stacked textareas into a controlled accordion using a new `focusedQIndex` state. Unfocused questions collapse into a clickable single-line `<button>` row. If they contain text, a green `CheckCircle2` appears.
- **Post-reveal (Phase B) — Per-question Notes**: Wrapped the AI grader's per-question `item.note` inside a disclosure row ("View note..."), hiding the raw text behind the `expandedNotes` state map.
- **Post-reveal (Phase B) — AI Feedback**: Replaced the bulky "AI feedback" card with a streamlined one-line element directly attached above the outcome buttons, bringing the buttons visually adjacent to the summary.
- **Post-reveal (Phase B) — Revision Note**: Moved `aiResult.revision_note` into an expandable disclosure row directly below the AI Feedback line, controlled by `expandRevisionNote` state.
- **Post-reveal (Phase B) — Related Subtopics**: Converted the "Worth exploring next" card into a clickable, single-line disclosure row showing the count ("N related topics to explore") controlled by `expandSubtopics` state.

## Flags & Deviations
- **FLAG**: The spec said "The AI feedback sentence stays visible but as one line attached to the suggested outcome, not a separate card." To keep the DOM hierarchy sane and accessible, the feedback sentence is grouped *just above* the "How did it go?" section and outcome buttons row, rather than physically embedded into one of the outcome buttons.
- **FLAG**: For the questions accordion, React's `autoFocus` reliably shifts focus to the textarea when expanding a previously collapsed question because we conditionally swap the element from a `<button>` to a `<div>` containing the textarea, triggering a remount.
- **FLAG**: No new hex values were introduced; `bg-[rgba(...)]` opacities were used alongside existing theme colors. No external spacing utilities were strictly needed beyond standard Tailwind `gap`/`mt`/`mb`. Network requests and tracking code logic remained strictly untouched.

---

## Claude's additional pass (2026-07-13)

The Antigravity pass above is good pre-reveal work and was left in place. But
**acceptance criterion #1 from the spec — "outcome buttons reachable without
scrolling on a 1280×720 viewport with a 3-question card" — was never actually
measured**, and when I measured it, it failed: the "Missed it" button sat at
`top: 1144px` against a 720px viewport (the real scroll container — `<main
class="flex-1 overflow-y-auto">` in `App.jsx`, not `window` — had `scrollHeight:
1367`). Closing that gap required two further changes.

### 1. Collapse correctly-answered questions by default (post-reveal)

New `expandedCorrect` state. A question graded `correct: true` now renders as a
one-line row (`N. question text… [Got it] ›`) instead of the full
question+chip+answer block; click to re-expand. Wrong or ungraded items are
unaffected — full detail, always. This directly implements the founder's separate
finding #3 ("I should get focus on what I genuinely was wrong about") and is also
the largest single density win, since most review sessions have more right answers
than wrong ones.

### 2. Sticky bottom action bar — and the bug in my first attempt at it

Spacing trims alone (tighter padding/margins throughout `Review.jsx`, ~150px saved)
were not enough to guarantee reachability for every real content combination
(first-review sentence + a `mistake` note + 3 questions + both onboarding hints
still undismissed is a real, not contrived, worst case). The robust fix: pin the
"How did it go?" heading + outcome buttons to the bottom of the viewport via
`position: sticky; bottom: 0`, so they're reachable regardless of how tall the
detail content above grows (a longer key memory, `deep` mode's 5 questions, etc).

**First attempt failed.** I nested the sticky bar inside the existing `<div
className="... animate-in fade-in slide-in-from-bottom-4 ...">` reveal wrapper.
Measured result: completely inert — the button's position didn't move at all
between the unstuck and "should be stuck" states. Diagnosed via
`getComputedStyle` + walking the full ancestor chain: **`position: sticky` is
bounded by its own immediate parent's box**, not by the actual scrolling ancestor
further up the DOM. That wrapper div was sized to exactly fit its own children —
the sticky bar's natural bottom edge was already at the wrapper's bottom edge —
so there was no "room" within *that specific box* for it to visually travel,
regardless of how much the true scroll container (several levels further up,
owned by `App.jsx`) actually scrolled.

**Fix:** moved the sticky bar out of that wrapper entirely, making it a **direct
child of the root flex column** — a sibling of `<header>`, `<main>`, and the
(now separate) detail `<footer>` — so its containing block spans the full
~1000px+ content height and there's real room for it to pin.

### Verification (measured in-browser, not inferred from the diff)

No due reviews existed in the dev environment; I would not mutate prod Supabase
data to manufacture one. Instead: monkey-patched `window.fetch` client-side
(session-local, zero persisted writes) with a realistic worst-case mock — first
review, 3 questions (2 correct / 1 wrong), a `mistake`, 2 related subtopics — then
drove the real UI (`computer`/`form_input`: typed real answers into each question
via the focus/collapse flow, revealed, expanded/re-collapsed a "Got it" row) and
read actual computed geometry via `getBoundingClientRect()`.

| Check | Result |
|---|---|
| Buttons reachable w/o scroll, 1280×720, 3-question card | **PASS** — `top: 622, bottom: 708` vs 720px viewport (was `top: 1144`, ~647px short, before this pass) |
| ≤3 expanded content blocks post-reveal | **PASS** — "Your answers" (1 of 3 expanded), Key Memory, Previous Mistake |
| Question-to-question flow, no manual scrolling | **PASS** — clicked through Q1→Q2→Q3 focus/collapse, answers persisted on collapse |
| Console errors, full flow | **PASS** — zero, checked after every interaction |
| Dark mode | **PASS** — session was actually running in dark mode throughout; sticky bar background resolved to `rgb(14,17,23)`, the exact existing `#0E1117` remap of `bg-[#f9f9f6]` in `index.css` — no new hex values added |
| Mobile 360×740 | **PASS** — all 4 outcome buttons within viewport bounds, bottommost at `bottom: 728` |
| `vite build` | **PASS**, before and after |
| Network/analytics untouched | **PASS** — no `apiFetch` call sites, payload shapes, or `track()` events edited; only JSX structure/classNames and new local UI state (`expandedCorrect`) |

No FLAGs. The reachability guarantee required one structural fix (sticky-bar
placement) beyond what the spec anticipated in its own language, but it stays
inside the stated boundaries (layout/disclosure only — no logic, API, or schema
changes).
