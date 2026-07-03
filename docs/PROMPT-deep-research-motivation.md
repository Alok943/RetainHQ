# Deep Research Prompt — Non-Manipulative Motivation in Learning Interfaces

> Paste everything below the line into the deep-research tool as one prompt.

---

## Product context (read this first — every recommendation must fit this product)

**RetainHQ** is a learning-retention web app for developers: spaced repetition (FSRS) +
active recall, wrapped around interactive coding lessons. The core loop: the user logs
something they learned as one testable "key memory" → the system schedules reviews right
before predicted forgetting → at review time the user must type what they remember **before**
the answer is revealed (a commit-before-reveal retrieval gate) → they self-rate the outcome
(Missed / Hard / Good / Easy) → FSRS reschedules. An optional LLM grader gives advisory
feedback on the recall attempt; the user always makes the final call.

**Audience:** developers and CS students, mostly self-taught or "AI-assisted coders,"
preparing for interviews or leveling up. They are skeptical of hype, allergic to
gamification-as-manipulation, and use serious tools (terminals, IDEs, Linear, Stripe).

**Design philosophy (already decided — recommendations must be compatible):** the product is
a *calm precision instrument* — warm paper surfaces, one accent color, honest coaching copy
("Honest beats optimistic"), no invented statistics, no mascots, no confetti. Product thesis:
*"Track what you remember, not what you complete."*

**Anti-fatigue decisions already shipped:** daily review cap of 10 cards with overflow rolling
forward (no unbounded backlog), sessions framed as finishable ("Today's review · 6 cards ·
~4 min"), first review deferred to the next day with an explanation of why, due-review
indicators deliberately styled as calm invitations (action-colored) rather than red alarms,
a one-click "I don't know" so the failure path costs less than the success path.

**Explicitly rejected:** XP, levels, leaderboards, loss-framed streaks, variable-reward
mechanics, guilt copy, notification pressure. Do not recommend these. If evidence shows some
rejected mechanic genuinely outperforms alternatives for long-run retention, report that
honestly as a tension — but then propose the best *non-manipulative* implementation or
substitute rather than telling us to adopt it as-is.

## Role & objective

Act as a research team spanning learning science, motivation psychology (self-determination
theory), HCI, and behavioral design ethics. Your objective:

**How can an educational interface create sustained motivation, confidence, and long-term
engagement — over weeks and months of spaced-repetition practice — without relying on
manipulative gamification?**

This is a knowledge problem, not a design-execution problem. We have full design and
engineering capacity; what we need is *evidence*. Your job is to tell us what is actually
true, with what confidence, so our design decisions rest on findings instead of folklore.

## Research questions

1. **Sustained motivation.** What does the evidence (esp. self-determination theory:
   competence, autonomy, relatedness) say sustains voluntary practice over months? Which
   interface-expressible factors matter most? What kills intrinsic motivation
   (over-justification, controlling feedback, social comparison)?
2. **Anxiety and the failure experience.** Retrieval practice means frequent visible failure.
   What does research on test anxiety, error framing, productive failure, and
   mindset/attribution feedback say about how a *failed recall* should be framed so the user
   returns tomorrow instead of avoiding the app? Is there evidence on how *pre-session*
   anticipation (due counts, backlog framing) affects avoidance?
3. **Perceived progress in a slow domain.** Memory strength improves invisibly and
   non-monotonically. What forms of progress feedback are evidence-supported for sustaining
   effort when the underlying quantity is slow and abstract (goal-gradient effects, small-wins
   research, progress visualization, mastery framing vs completion framing)? What forms
   backfire (progress inflation, streak-loss aversion, metric fixation)?
4. **Streaks and consistency mechanics, specifically.** The evidence for and against. Is there
   a form of consistency feedback (e.g., non-punitive streaks, "practiced 4 of last 7 days"
   windows, freeze/repair mechanics) that keeps the habit-formation benefit without the
   loss-aversion manipulation and the abandonment cliff after a broken streak?
5. **Feedback that builds confidence.** For AI-graded or self-graded recall: what feedback
   characteristics (timing, specificity, praise type, normative vs self-referenced comparison)
   improve both learning and the learner's *calibration* (knowing what they actually know)
   without inflating or crushing confidence?
6. **The ethics line.** Where does the literature (persuasive-design ethics, dark-patterns
   research) actually draw the line between supporting a user's own goals and exploiting
   their psychology? Give us an operational test we can apply to any future feature.

## Evidence standards

- Prefer peer-reviewed studies and meta-analyses; name them (authors, year, venue). Blog
  posts and design folklore may be cited only as *claims to evaluate*, never as evidence.
- Grade every major finding: **Strong** (replicated / meta-analytic), **Moderate** (a few
  studies, plausible mechanism), **Weak/contested**, or **Folklore** (widely believed,
  unsupported or contradicted). Effect sizes where available.
- Explicitly hunt for findings that *contradict* our existing decisions (listed above). We
  want our philosophy stress-tested, not confirmed. If the evidence says our anti-streak or
  calm-due-badge stance costs retention, say so plainly.
- Note ecological validity: lab studies on undergraduates ≠ months-long self-directed app
  use. Flag where the evidence base is thin for our exact context (voluntary, long-horizon,
  adult, self-directed learning).

## Deliverables

1. **Evidence report** organized by the six research questions, every finding graded.
2. **Design implications for RetainHQ** — for each of these specific surfaces, state what the
   evidence recommends and at what confidence: (a) the due-review indicator and pre-session
   framing; (b) the failed-recall moment (copy, visual treatment, what happens next);
   (c) the session-complete moment; (d) progress/consistency display on the dashboard
   (currently: a review heatmap calendar + a "consistency N/7 days" stat); (e) AI feedback
   presentation; (f) long-gap re-entry (the user who returns after two weeks away).
3. **A folklore list** — the 10 most commonly repeated motivation-design claims that the
   evidence does not support.
4. **Contradictions & tensions** — anywhere the evidence disagrees with our stated philosophy
   or shipped decisions, with your recommended resolution.

Don't merely summarize existing knowledge. Synthesize it into positions. When experts
disagree, evaluate the evidence, explain the trade-offs, and make a recommendation with clear
reasoning. Write it as an internal evidence brief for a team that will act on it directly.
