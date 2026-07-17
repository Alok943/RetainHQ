# School Maths (11th/12th) — runtime design + competitive frame

**Written:** 2026-07-12. Design doc for taking the school platform into Class 11/12
mathematics: what "visualize" means for maths, the two runtimes it needs, the pilot
chapter, and the competitive positioning it must serve. Companion to
`docs/PLAN-lesson-generation.md` (content priority) — this is the RUNTIME plan; content
generation starts only after the runtime contracts here are hardened.

---

## 1. Competitive frame (the honest version)

Three "competitors": the teacher + smartboard, the student's own LLM (ChatGPT/Claude),
and coaching apps (PW/Allen test series). The framing that survives scrutiny:

**Explanation is commoditized — never compete on it.** LLMs, 3Blue1Brown, GeoGebra and
a good teacher all explain limits better than we need to. Our layer-1 visuals are hooks,
not the moat.

**LLMs DO have memory now — do not build the pitch on "ChatGPT forgets you."**
ChatGPT memory / Claude Projects persist context and learning style across months. A
power user with a tutor skill file + persistent memory assembles a personal RetainHQ
(the founder literally does this for DSA). What actually remains defensible:

1. **Enforcement, not recall.** LLM memory *remembers*; it does not *initiate*. Nothing
   in an LLM runs a calibrated forgetting-curve scheduler, pings the student on day 6,
   caps the session, or refuses to reveal before a prediction. RetainHQ's loop is
   enforced by the product, not by the student's discipline. (LLM vendors are moving
   here — ChatGPT has study modes and scheduled tasks — so this edge erodes; see §7.)
2. **The assembly gap IS the product — especially rural/tier-3 schools.** What a power
   user builds with skills + memory + prompting patterns requires knowing those things
   exist. A Class-11 student in a rural school has: low prompting literacy, English as a
   barrier, a shared cheap Android, spotty data, and zero awareness of "memory,
   projects, skills". RetainHQ is those power-user defaults **packaged**: syllabus
   already structured, questions already scheduled, struggle already enforced, in plain
   language (the beginner overlay register). Distribution + defaults beat DIY.
3. **Verified memory state.** A school/parent will not trust "the chatbot says she's
   improving." They will trust a measured retention curve, per-topic decay, and test
   scores that correlate with it. LLM self-report is not a trust artifact; our
   analytics are. This is also the B2B wedge (see next).

**Vs the teacher: complete, don't compete.** The pitch positions RetainHQ as the
after-class layer the teacher lacks: teacher teaches → student captures → we schedule
the return visits → **the teacher gets a class-decay dashboard** ("trig identities are
decaying class-wide — reteach before the unit test"). No smartboard vendor or LLM gives
a teacher a forgetting-curve view of their class. The teacher becomes the champion, not
the competitor. The smartboard shows it once; we make sure it's still there in March.

**Vs the student's ChatGPT habit:** GPT's usage pattern defeats learning — ask when
stuck, get unblocked, feel competent, retain nothing. Our counter is behavioral, not
informational: predict-before-reveal as a hard gate (struggle is the price of the
answer), FSRS return visits the product initiates, and progress the student can show.
Marketing line: *"ChatGPT can do your homework. Nobody can do your remembering."*

**Applies to ALL roadmaps** (career + school): the stack is always
(1) domain interactive hook — varies per roadmap; (2) pedagogy — predict-before-reveal,
misconception banks, worked-example-first: constant; (3) moat — FSRS + measured memory
state + dashboards: constant, and it compounds with every subject added. Judge every
layer-1 runtime investment by how many roadmaps it feeds.

## 2. What 11th/12th maths actually is (two animals)

**A) Procedural maths — the majority of board/JEE marks.** Derivations, limits by
manipulation, integration technique, matrices/determinants, algebraic solving. Marks
die on stereotyped errors: sign slips, wrong formula variant, degrees-vs-radians,
forgot +C, squared-both-sides without checking extraneous roots, dropped domain
condition. The right "visualization" is NOT a picture — it is a **step-derivation
player** (§3): the expression transforms step by step and the student predicts the next
transformation before reveal.

**B) Geometric maths — the intuition layer.** Function graphs, conics, derivative as
sliding tangent, integral as accumulating area, vectors/3D. Interactive parameter-play
(§4) matters here, but honestly: GeoGebra/Desmos do this better and free. Our version
is deliberately lightweight and exists to SET UP a prediction, not to be a tool.
Vectors/3D reuse the existing physics R3F scene pipeline nearly verbatim.

Maths hands us one asset code lessons don't: **numeric/choice answers grade
deterministically** — the Tests runtime already grades numeric client-side. Maths recall
cards can be "solve this micro-step" at zero LLM cost. FSRS over solved micro-steps is
what coaching institutes sell as "test series + revision planner", minus the per-student
adaptivity we get for free.

## 3. Runtime 1 — step-derivation player (the priority build)

The DSA trace player's pattern applied to symbolic state instead of array state.
Claude-owned (runtime + schema + golden gates), same split as D-015: Antigravity fills
content against the contract; Claude builds the player once.

**Lesson-side schema (draft — to be hardened against the pilot chapter):**
```json
"derivation": {
  "goal": "\\int x e^x \\, dx",
  "steps": [
    {
      "expr": "u = x,\\; dv = e^x dx",
      "rule": "parts-choice",
      "why": "ILATE: pick the algebraic factor as u — it simplifies when differentiated.",
      "predict": {
        "question": "Which substitution should we choose?",
        "options": [
          { "expr": "u = x,\\; dv = e^x dx", "correct": true },
          { "expr": "u = e^x,\\; dv = x dx", "error": "reverse-ILATE",
            "feedback": "Differentiating e^x never simplifies — you'd loop forever." }
        ]
      }
    },
    { "expr": "x e^x - \\int e^x dx", "rule": "parts-formula", "why": "uv - \\int v\\,du" },
    { "expr": "x e^x - e^x + C", "rule": "standard-integral",
      "why": "\\int e^x dx = e^x; never drop the +C.", "predict": { "...": "..." } }
  ]
}
```
Design rules (the pedagogy is in the details):
- **`predict` on 30–60% of steps**, never step 1 (worked-example-first, beginner overlay
  B3). Options are 2–4 next-step candidates; **distractors come from the misconception
  bank** — the classic wrong move with per-error feedback. This converts the error
  taxonomy into interaction, deterministically graded, zero LLM.
- **`why` is the recall unit.** Each step's justification ("why is this step legal")
  becomes a recall card; the derivation is the context, the rule is the memory.
- Rendering needs **KaTeX** (new frontend dependency — small, self-contained, no CSP
  issues; decision flagged in §7).
- Player mechanics reuse the DSA player skeleton: step cursor, reveal gating,
  prediction scoring, "run to end" replay.

**Feeds:** 11/12 maths (most chapters), physics numericals (derivation-style solutions),
chemistry stoichiometry later, aptitude multi-step problems. Highest fan-out runtime
available — which is why it's the priority buy.

## 4. Runtime 2 — graph-play (a pedagogical instrument, not a hook and not a CAS)

Calibration (founder direction 2026-07-12): **rich enough that the visual itself teaches
— never so generic it becomes a tool.** The line between the two is a decision rule, not
a feature count: **a capability gets built only when a specific lesson's specific
prediction needs it.** GeoGebra is a lab bench; ours is an instrument pre-configured for
one experiment per lesson, with the prediction committed BEFORE the student may touch it.

Core (all modes): SVG/canvas plot of a fixed-grammar expression
(polynomial/trig/exp/log/abs/rational of one variable), parameter sliders, ghost trace
of the previous curve when a parameter changes (the "family" effect), constrained
zoom/pan, and a required `predict` block gating interaction.

**Chapter-driven modes** (this is where "not simple" lives — each exists because a
Class 11/12 chapter needs it to make a concept visible):
- `limit` — animate approach from left/right with a value readout table (x → 2⁻, 2⁺),
  open-circle hole markers, jump/asymptote rendering. *The* limits visual: shows
  "the value the function approaches ≠ the value at the point".
- `secant-tangent` — two points on the curve, drag h → 0, live slope readout; the
  secant visibly becomes the tangent. Derivative-as-limit made kinetic.
- `riemann` — under-curve rectangles with an n slider (4 → 100), signed-area shading;
  the sum readout converges on the integral value. (Class 12; built when that chapter
  starts, listed now so the schema reserves the mode.)
- `transform` — multi-parameter families (a·f(bx+c)+d) with ghost traces; teaches
  shift/stretch/flip as *motions*, not rules.

**Step-derivation player, same calibration** (§3 additions): (a) **sub-expression
diff highlighting** — the part of the expression that changed this step glows; the
student's eye lands where the rule applied; (b) **wrong-path branches** — choosing a
misconception distractor optionally plays 1–2 steps down the WRONG path until the
contradiction/mess appears, then rewinds. Watching the error unravel teaches more than
"incorrect, try again" ever will. Both are player features, zero extra content cost
(the branch steps come from the misconception bank).

Hard boundaries (the "not overkill" side — these hold until a lesson proves a need):
no general CAS, no free-form expression input by students, no symbolic manipulation
in graph-play, no GeoGebra-style construction tools, no user-saved states. Evaluation
via a tiny safe parser — **no eval(); mathjs only if the grammar genuinely fights back**
(§7). 3D/vector visuals do NOT use this runtime — they go through the existing physics
R3F pipeline.

## 5. Pilot: one chapter end-to-end before any syllabus sweep

**Limits & Derivatives (Class 11, NCERT ch. 13)** — procedural + geometric + feared,
and it forward-feeds all of Class 12 calculus:
- ~15 nodes: limit intuition (graph-play), algebra of limits, standard limits
  (sin x/x — derivation + graph), limits at infinity, derivative as slope (graph-play,
  sliding secant→tangent), first-principles derivatives (step-derivation, the
  centerpiece), rules (sum/product/quotient/chain preview), polynomial + trig
  derivatives (step-derivation with error-bank distractors).
- Misconception bank first — **Gemini web Deep Research** (Antigravity can't deep-
  research; self-contained paste prompt: `content/PROMPT-maths-research.md`, output
  saved to `content/research/maths-limits-derivatives.json`; first batch delivered as
  `class11deepresearch.md`, nodes 1–3) — then runtime + validator branch + 3 golden
  lessons built by **Antigravity from the Claude spec** `content/HANDOFF-maths-runtime.md`
  (D-015 pattern; browser verification stays a Claude gate), then bulk generation
  (Antigravity, beginner overlay applies — this IS the tier-3 audience), then critic sweep.
- Exit test for the pilot: a student who finished the chapter answers its recall cards
  at ≥85% a week later (FSRS data tells us), and the pitch demo shows: predict → step
  player → wrong-move feedback → scheduled return → teacher decay view.

Per the no-MVP rule: full 11th+12th coverage remains the scope; one chapter first is
dependency sequencing (the runtime contract needs a real chapter to harden against),
not scope-cutting.

## 6. Teacher dashboard (the B2B wedge — schedule after pilot content proves)

Class-level aggregation of what already exists per-user: per-topic retention/decay,
due-backlog, misconception frequency ("14 of 40 students picked the reverse-ILATE
distractor"). Reuses metric/event data; needs class/cohort modeling (school → class →
students) — a schema decision for its own doc when the pilot lands. Named here because
the smartboard/LLM positioning depends on it existing.

## 7. Open decisions (founder)

1. **KaTeX dependency** for expression rendering — assumed yes; alternative (MathML/
   images) is worse on cheap Android.
2. **Graph-play parser**: tiny custom grammar vs mathjs. Start custom; adopt mathjs
   only if the grammar fights back.
3. **Board alignment**: NCERT/CBSE first (assumed — matches Physics 9-10 pitch); state
   boards later via the syllabus-upload path (a rural school's state-board syllabus
   pastes into the existing extractor TODAY — that's the stopgap story while authored
   chapters grow).
4. **Where the erosion clock ticks**: LLM vendors will productize study loops
   (ChatGPT study mode exists). Our durable positions are enforcement UX, packaged
   defaults for low-literacy users, class-level verified analytics, and B2B school
   distribution. Revisit this frame every quarter — the "LLMs don't schedule" line has
   a shelf life.
5. **Sequencing vs P0 content** (`PLAN-lesson-generation.md`): the step-derivation
   runtime is a Claude build and doesn't block Antigravity's P0 batches — they run in
   parallel. Confirm.
