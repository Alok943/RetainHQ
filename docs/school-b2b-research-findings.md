# School B2B research — findings & gaps (distilled 2026-07-02)

Distillation of four Deep Research reports (in `~/Downloads`). Read this instead of the ~240 KB of
raw reports. **Verdict: real, decision-grade market intel now exists (§D) — Educomp's failure
mechanism, current-vendor pricing, buyer psychology, and a precise Physics wedge — salvaged from
the one run that worked. The teacher-adoption report (§A) is strong product ammunition. Two runs
were drift-garbage (§B, §C). Net: enough to price a pilot and pick the MVP lesson; local school
census still needed.**

### Report scorecard
| Report | What it was meant to be | What it delivered |
|---|---|---|
| Teacher Tech Adoption | (its own prompt) | ✔ Useful — pedagogy + adoption principles (§A) |
| Gorakhpur Division Information Gathering | `PROMPT-school-b2b-research.md` run #1 | Drift — regional profile; salvage thin (§B) |
| START: Definitions, Programs… | (unknown) | ✘ Total garbage — researched the WORD "start" (§C) |
| Gorakhpur Division July 2026 Update | B2B market intel | ✔✔ **Buried goldmine — answers most questions (§D)** |

---

## A. Teacher-adoption report — HIGH VALUE (use for product design + pitch)

Caveat: it came back **hardware-centric** (smartboards/IWBs/projectors), not about a software
content product. But its *pedagogy + adoption* findings map straight onto our product, and several
are direct pitch weapons. All claims below are research-cited in the source.

### The five findings that matter
1. **The "glorified projector" death spiral.** Schools buy interactive hardware; teachers revert
   to projecting static PDFs/slides because *building* interactive lessons takes hours they don't
   have. Only ~4% of teachers ever use the interactive features. → **Our wedge: the lessons are
   PRE-BUILT. Zero authoring. This is the single strongest differentiator — we are the ready-made
   content that the SMART Exchange never had** (their example: math had 200k ready resources,
   social studies had 5).
2. **POE is research-validated.** Predict-Observe-Explain, with *productive confusion*, measurably
   improves understanding — our exact mechanic. But the report's warning is sharp: if the *tool*
   is confusing to operate, the student feels destructive frustration instead of productive
   confusion. → UI friction directly destroys our core pedagogy. Ruthless simplicity is not
   optional.
3. **Chalk beats slides on pacing** because information is revealed incrementally at
   thinking-speed (dual-coding, no split-attention). → Our step-through + predict-before-reveal
   *is* chalk pacing, digitized. Pitch it as "chalk-paced, not slide-dumped."
4. **Buyer-persona mismatch kills adoption.** Sold to admins for dashboards; teachers experience
   it as a compliance mandate and abandon it after the novelty fades. → The admin signs the
   cheque, but if the teacher doesn't *want* it, it's shelfware. Design and pitch for the teacher;
   frame to the admin as "avoids the glorified-projector graveyard you already paid for once."
5. **Reliability > features.** A failed demo teaches the teacher "this tech is a liability." Offline
   dependency, calibration, login friction, and boot latency are named abandonment causes. →
   Offline-first, instant-load, no-login-to-start are hard requirements, not polish.

### Teacher-adoption design principles (acceptance criteria for MVP lessons)
- **Zero prep** — a teacher opens a lesson cold and teaches; no asset-building, ever.
- **Zero-friction start** — no login to run a lesson; loads in ~1s; works with the internet down.
- **Incremental reveal** — never dump a full diagram; build it step-by-step (already our model).
- **Teacher-controlled pacing** — teacher drives; prediction gates are discussion pauses they
  trigger, not autoplay.
- **Big, obvious touch controls** — usable on a projector/low-end panel under classroom stress;
  next/back/pause must be unmissable.
- **Rock-solid demo path** — the 2-3 pitch lessons must never fail live; pre-cache everything.

---

## B. Gorakhpur report — FAILED RUN of the B2B prompt (Deep Research drifted)

**This report IS what came back when `PROMPT-school-b2b-research.md` was run with "Gorakhpur" as
the target.** Deep Research anchored on the place name + the word "information," reframed the
analytical market task as "gather general info about Gorakhpur Division," and — finding little
school-market data — filled the report with abundant regional facts (history, expressways,
Buddhist tourism, monsoon weather). **The market questions were never answered.** Root causes:
(1) a locale name over-anchors Deep Research on an analytical prompt; (2) the prompt fused two
different retrieval modes (national industry analysis + local enumeration) and the model took the
broader/easier one. **Fix applied:** scope-guard added to the B2B prompt (no locale, "do not
profile a region"), and a separate `PROMPT-gorakhpur-school-census.md` created as a pure
enumeration task with hard regional-exclusions. Re-run both separately.

The only usable facts salvaged from the drifted report:
- **Literacy:** district 70.83% overall; male 81.8% vs female 59.36% (big gender gap).
- **Scale:** Gorakhpur district ~4.44M people (division well over 13M); 90.3% Hindu, 9.1% Muslim.
- **Govt school system is active** (June 2026 secondary-teacher transfer notification) — but govt
  schools are not our buyer.
- Cross-report note: private schools adopt edtech faster than public (fewer bureaucratic hurdles).

**What it did NOT provide (and what we actually need for a Gorakhpur pitch):** a census of local
private CBSE/ICSE schools (names, count, fee tiers), existing smart-class penetration locally,
who decides (owner/principal), and per-student digital spend. This needs a **narrow re-run**
targeted at "private schools in Gorakhpur city," not the division's history.

---

## C. START report — TOTAL GARBAGE (ignore)

`START: Definitions, Programs, and Strategies` — Deep Research read the literal word **"START"**
as the topic and wrote an encyclopedia of "initialization" across nuclear treaties (New START),
medical triage (START triage), UART start bits, and habit-formation books. Zero relevance. Delete
it. (Confirms the drift pattern: a salient word/proper-noun hijacks the whole run.)

## D. MARKET INTELLIGENCE — salvaged from the July-update run (HIGH VALUE)

All cited in the source report (Tracxn, GetLatka, NextOS, iDream, court docs via Indian Kanoon).
**Confidence: medium — single-synthesis, spot-verify the pricing before betting on it.** But it
directly answers the questions the B2B prompt was built for.

### Failure taxonomy (why the legacy players died)
- **Educomp Smartclass / Pearson DigiClass** (early 2010s): bundled proprietary content + expensive
  hardware on **5-year lock-in contracts**; ₹75–150 per-child/month. Educomp used future fee
  receivables as **loan collateral** (Axis/SBI via 'Edu Smart'). Collapse mechanism: hardware
  degradation, no timely on-site support, content obsolescence → smart classes sat **non-functional
  for long stretches** → **parent revolts + withheld fees** → receivables imploded → **SFIO probe
  into fund diversion**, insolvency. *The killer was the financing/receivables model + hardware
  dependency, not the content.*
- **BYJU'S / Toppr School OS**: B2C giant's B2B pivot; now insolvent, $1B debt, lenders (Glas
  Trust) seizing ~30% of Aakash. School-facing products in limbo → **regional admins now distrust
  big-brand lock-in.**

### Survivor pricing matrix (the anchors for our pilot price)
| Vendor | Model | Numbers |
|---|---|---|
| **LEAD Group** | "Managed School" (takes over operations) | 100% net retention; cut burn 65% FY24; ₹370 Cr revenue |
| **Next Education** | Cloud ERP + LMS + content | **₹7–155 / student / month**; ERP ₹60k–2L/yr; 12M students |
| **Extramarks** | B2B smart-class subscriptions | K-12 from **₹1,820/month**; Live Class Packs ₹3,999/yr |
| **iDream Education (iPrep)** | Plug-and-play, **offline-capable**, Tier-2/3 focus | Closest direct competitor to our model — study it |
- Regional smart-class hardware for reference: 65" board ₹80k–1L, 75" ₹1.2–1.5L, +audio/UPS.

### Buyer psychology (THE most actionable finding)
Procurement is **bifurcated**: **Trustees/owners** think ₹-per-student, ROI, and *parental
optics* — there's an **"invisible ceiling": they won't pay >~$4/student/year for backend software
parents can't see.** **Principals** care about pedagogy + ease-of-use and act as influencers.
→ **Implication for us: the product MUST have parent-visible value** (retention scores, exam-prep
outcomes, progress reports) or it dies at the trustee's ceiling. Sell outcomes parents brag about,
not "an engine."

### Physics wedge — ANSWERED (this is the MVP lesson)
The report names the exact chapter where chalkboards fail and a step-through visual wins: **CBSE
Class 10 Physics — Light (Reflection & Refraction), ray diagrams for spherical mirrors & lenses.**
Rote-memorized ray diagrams → poor exam performance because students can't visualize the geometric
intersection of focal rays. It even lists the deterministic ray protocols (concave/convex
mirror/lens) — **exactly an event-driven, deterministic visualization our engine produces.**
→ **MVP lesson = Light: Reflection & Refraction (ray-diagram builder), Class 10.** (Class 10, not
9-10 — the wedge is specifically Class 10.)

### Competitive warning (don't ignore)
The report states emerging platforms are **already integrating FSRS + AI adaptive learning** for
retention (JEE/NEET prep framing). Our retention loop is **validated but no longer unique** in the
abstract — the moat has to be *execution*: the predict-before-reveal visual quality + how tightly
the loop closes, not "we have spaced repetition."

## Next actions (in order)
1. **Pick MVP lesson = Class 10 Light: Reflection & Refraction** (ray-diagram builder). The wedge
   is answered; no more research needed to start speccing it.
2. **Run `PROMPT-gorakhpur-school-census.md`** — the ONE thing still genuinely missing: the local
   target-school list (names, tiers, decision-makers). Enumeration task, hard-guarded.
3. **Spot-verify the §D pricing** (Next Education ₹7-155/student/mo, Extramarks ₹1,820/mo, the $4
   trustee ceiling) before using them in a pitch — single-source synthesis.
4. `PROMPT-school-b2b-research.md` is now **largely answered by §D** — only re-run if you want the
   student-side B2B2C engagement-graveyard detail, which §D didn't cover.
5. Bake §A (teacher adoption) + §D (parent-visible value, offline-first, trustee $4 ceiling) into
   the MVP lesson + pitch spec.

## Tooling lesson (reusable)
Gemini Deep Research drifts when given (a) a proper-noun locale inside an analytical prompt, or
(b) two different retrieval modes in one run. Guard analytical prompts with an explicit "do NOT
profile a region / stay on companies" block, keep enumeration tasks in their own run, and front-
load named entities so browsing anchors on the right subject.
