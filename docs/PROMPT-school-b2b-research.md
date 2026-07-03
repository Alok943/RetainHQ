# Deep-research prompt — India K-12 B2B edtech: survivors, corpses, and the gap

> Paste everything from "ROLE" down into Gemini Deep Research. One run. Output feeds a
> go/no-go + pitch-design decision for an interactive concept-learning product (details in
> CONTEXT), so optimize for **decision-grade evidence**, not an industry essay.
>
> **DO NOT add a city/region/locale to this prompt.** This is a NATIONAL industry + competitor
> analysis. A prior run that named "Gorakhpur" caused Deep Research to abandon the market
> questions and write a regional geography/history report instead. Local school-census research
> is a SEPARATE run — see `PROMPT-gorakhpur-school-census.md`. Keep the two apart.

---

## ⛔ SCOPE GUARD — read first
This is a **market and competitor analysis of the Indian K-12 EdTech INDUSTRY.** Your subject is
**companies, products, pricing, business models, and buyers** — named entities like *Educomp
Smartclass, BYJU'S, LEAD, Extramarks, Next Education, Toppr*. You must NOT profile any
geographic region: **no history, demographics, population, literacy stats, weather, tourism,
infrastructure, or expressways.** If you find yourself describing a place rather than a company or
a business model, you have drifted — stop and return to the companies. The deliverable is a
business decision doc, not a regional study.

---

## ROLE
You are a skeptical edtech market analyst doing citation-backed research on the **Indian private
K-12 B2B market** (CBSE/ICSE private schools buying digital teaching content). Your reader is a
solo founder deciding whether to pitch schools — they need pricing numbers, named failure causes,
and honest gap analysis. Be concrete and cite sources; where evidence is thin or claims come from
company PR, say so explicitly.

## WRITING RULES (knowledge extraction, not prose)
- Structured bullets and tables over paragraphs. No historical essay openers.
- Numbers with dates and sources ("₹X per student/year, 2024, source") — an undated price is noise.
- Distinguish **verified** (filings, credible reporting, multiple sources) from **reported/PR**
  (company claims, founder interviews). Label each.
- Every section ends with a `Confidence: high|medium|low — why` line.
- No company folklore or hype narration; failure causes must be *mechanisms*, not "mismanagement."

## CONTEXT (the product being pitched — for gap analysis, do not evaluate it)
An interactive concept-learning engine for Classes 6–12, starting with **Physics, Class 9–10**.
NOT videos: deterministic, code-driven simulations where the learner **predicts before the reveal**
(Predict-Observe-Explain). **Two usage motions on the SAME content, both paid by the school:**
1. **Classroom** — teacher projects and controls playback, prediction gates become class
   discussion pauses.
2. **Individual student** — each student opens the same concepts on their own phone (school-paid
   per-student license), completes prediction checkpoints themselves, and the concepts enter a
   **spaced-repetition review queue (FSRS)** they keep working through at home — retention as a
   product feature, not homework PDFs.
Differentiator claim to test: *interactive prediction + a genuine retention loop*, vs. incumbents'
video libraries + question banks. MVP = 2–3 polished lessons pitched directly to private schools.
Research BOTH motions with equal weight — the student-side (B2B2C) evidence matters as much as the
classroom side.

## RESEARCH QUESTIONS

### 1. The corpses — B2B K-12 failures and WHY (the most important section)
- **Educomp Smartclass**: the canonical smart-class collapse. Mechanism of failure: hardware
  bundling? receivables/school-financing model? content quality? What did schools actually stop
  paying for?
- **BYJU'S** (B2B school offerings + overall collapse as it affects school trust), **Toppr School
  OS**, **Meritnation**, **Curriculum Associates-style clones**, any smart-class vendors that
  quietly died (Pearson DigiClass? HCL Learning? Mexus?).
- For EACH: what was sold, to whom, at what price, and the specific failure mechanism
  (sales-driven receivables, hardware AMC burden, teacher non-adoption, content commoditization,
  free-alternative pressure, school churn after year 1).
- Synthesize a **failure-cause taxonomy**: rank the recurring causes by how often they killed
  companies. This taxonomy is the "what not to do" for the pitch.

### 2. The survivors — who still sells to Indian private schools in 2025-26 and how
- **LEAD Group** (school-as-a-service), **Extramarks**, **Next Education**, **Teachmint**,
  **iDream Education**, **ConveGenius**, **Physics Wallah's school/offline push**, **Allen's
  school products**, plus any I'm missing.
- For EACH: what schools actually buy (content? LMS? hardware? integrated academics?), pricing
  model and real numbers (per-student/year vs per-school vs per-classroom), claimed school count
  (labeled PR vs verified), and what keeps renewal happening.
- Which are growing vs. treading water? Any recent pivots away from B2B K-12?

### 3. The buyer — how a private school actually buys
- Who decides (owner/trust vs principal vs academic coordinator), typical sales cycle length,
  pilot norms (free pilot? paid pilot? one section vs whole school?).
- Budget reality: what does a mid-tier private school (₹30k–₹1L annual fee) spend per year on
  digital content/tools? What line item does this come from?
- Churn drivers: why schools drop vendors after year 1-2.
- The **free-alternative pressure**: DIKSHA, NCERT official content, Khan Academy India, YouTube
  (Physics Wallah free content) — how do paid vendors position against free, and does it work?
- NEP 2020 / CBSE competency-based-education mandates: are they a real purchasing lever in
  2025-26 or just conference talk? Any evidence schools buy to satisfy them?

### 4. The gap check — does anything like the CONTEXT product exist?
- Interactive simulation products in Indian schools: **PhET usage in India** (is it actually used
  in classrooms? any Indian distribution/localization?), Labster-style sim vendors targeting K-12,
  any Indian startup doing prediction-based/POE-style interactive concepts (not videos).
- Do any incumbents (Extramarks/LEAD/Next) ship *interactive* sims vs. animated videos? How
  interactive, honestly?
- Spaced repetition / retention features in ANY Indian K-12 product (not test-series — actual
  scheduled review). Closest thing that exists?
- Verdict: is "interactive prediction + retention loop" a real white space in this market, or has
  someone tried and failed (if failed — why)?

### 5. The student side — school-paid individual student usage (B2B2C)
The classroom projector is only half the model; research the half where **each student uses the
product individually, licensed by the school**:
- **Who has tried school-paid student apps** — LEAD's student app, Extramarks student LMS,
  Toppr's school-distributed accounts, BYJU'S school partnerships, Teachmint student side,
  homework/practice products bundled into school fees. For each: activation and *sustained*
  usage reality (not licenses sold — actual weekly active students, if any evidence exists).
- **The engagement graveyard**: school-bought student licenses that students never opened —
  how common is this, what causes it (no teacher enforcement? clunky login? content = boring
  question banks? parents see no value?), and which vendors' student products actually get used.
- **What sustains home usage when it works**: teacher-assigned + teacher-visible (homework
  loop)? streaks/gamification? exam-prep utility close to test dates? parent visibility/reports?
  Rank by evidence.
- **Device + access reality** for mid-tier private school students (Classes 6-12): own phone vs
  parent's phone by class band, Android version/performance spread, data constraints — what a
  student-side product must technically tolerate.
- **Accountability plumbing schools expect** when they pay per-student: teacher dashboards,
  completion reports, parent reports — which of these are *deal requirements* vs nice-to-have.
- **Homework-replacement positioning**: any vendor that successfully replaced/augmented homework
  with in-app work (vs. being "extra" work students skip)? Did daily-review/retention framing
  ever get traded on — and did schools value measured *retention* over completion percentages?
- **Pricing split**: when schools pay per-student for a student-side product, what's the going
  rate vs classroom-content pricing? Are hybrid (classroom + student license) bundles priced as
  one line or two?

### 6. Physics 9-10 wedge validation
- Which CBSE Class 9-10 physics chapters are (a) highest board-exam weight, (b) most complained
  about by teachers/students as hard to teach/visualize (electricity, motion, light,
  work-energy?). Cite teacher forums, exam analyses, coaching content emphasis.
- Existing digital coverage of those chapters: where is quality already high (crowded) vs.
  genuinely weak (opening)?
- Recommend the **2-3 specific concepts** where an interactive predict-first demo would look most
  differentiated to a principal in a 10-minute pitch.

### 7. GTM lessons from those who cracked it
- How did LEAD/Extramarks/iDream actually get their first 50 schools? (direct founders' sales,
  channel/reseller networks, hardware partners, state relationships?)
- Pilot-to-paid conversion tactics that reportedly worked; pricing anchors for a new vendor with
  2-3 lessons (paid pilot? per-classroom license? annual per-student?).
- Solo-founder-relevant: any evidence of small content vendors succeeding via a niche wedge
  (single subject/grade) rather than full-curriculum? Or does the market punish narrow catalogs?

### 8. Teacher adoption & classroom behavior (critical — ends in design principles, not facts)
Research why teachers continue to prefer chalkboards/whiteboards even when interactive
whiteboards or smart classrooms are available and paid for. This section must end in **product
design implications**, not description.

- **Pedagogical reasons**: qualitative research, educational-psychology papers, teacher
  interviews, and classroom studies explaining why teachers *intentionally* prefer the board;
  teaching moves that are easier or more effective on a board than on digital tools.
- **Classroom usage patterns**: which lesson types, concepts, and classroom situations lead
  teachers to ignore an available smart board; which subjects benefit most and least from
  digital visualization.
- **Feature adoption**: which digital-tool features become part of teachers' *daily* workflow vs
  used only during onboarding/demos and then abandoned — evidence from teacher forums, case
  studies, product research.
- **EdTech abandonment**: why teachers stop using digital tools after the novelty phase —
  technical friction, usability, classroom-management problems, training burden, reliability,
  maintenance.
- **Workflow comparison** (chalkboard vs digital tool): lesson preparation time · classroom
  execution · ability to improvise · speed of explanation · troubleshooting effort · recovery
  from mistakes · classroom control · student engagement.
- **Cognitive load**: which aspects of digital tools genuinely reduce teacher workload, and which
  add cognitive or administrative burden.
- **Infrastructure tiers**: adoption differences across premium / mid-tier / budget private
  schools, government schools, urban vs rural.
- **PRODUCT DESIGN IMPLICATIONS (most important — the payoff of this section).** From the
  evidence above, derive concrete, evidence-cited design principles for a classroom teaching
  product. Answer at minimum:
  - What should a classroom visualization tool **never require a teacher to do**?
  - Which interactions feel natural during *live* teaching (vs. demo conditions)?
  - When should the technology disappear into the background?
  - What would make a teacher **voluntarily choose the product over picking up chalk** for a
    given concept?
  - How can the product *reduce* preparation time instead of adding to it?
  - Which features should be avoided because they consistently fail adoption?
  The goal is not to explain why teachers use chalkboards — it is evidence-based design
  principles that maximize long-term teacher adoption of the CONTEXT product.

## OUTPUT FORMAT
1. **One-page executive verdict first**: is there room for this product? Top 3 failure causes to
   avoid, price anchor recommendation, and the single strongest pitch angle vs. incumbents.
2. Then the eight sections above, bullets/tables, each with its Confidence line.
3. **Failure-cause taxonomy table** (cause → companies it killed → how the CONTEXT product
   avoids or is exposed to it).
4. **Survivor matrix table** (company → what's sold → pricing → verified traction → why schools
   renew).
5. End with **"Decision questions answered"**: (a) go/no-go signal for the 2-3 lesson pitch MVP,
   (b) recommended pilot structure + price, (c) the 2-3 physics concepts to build, (d) the three
   red flags most likely to kill this in a school pitch meeting, (e) **should the MVP pitch lead
   with the classroom motion, the student-retention motion, or the bundle** — based on what
   schools have actually paid for and what students have actually used, (f) the one design
   requirement most critical for the student side to avoid the engagement graveyard, (g) the
   **top 5 teacher-adoption design principles** (from section 8) the MVP lessons must satisfy —
   phrased as testable requirements, not advice.
6. Sources list: primary (filings, credible business press — Ken/Morning Context/ET/Inc42 with
   dates) vs secondary (blogs, PR). Flag paywalled claims you could not verify.
