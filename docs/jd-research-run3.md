# JD Research — Run 3: Role Transition Graph

**Scope:** 7 fresher roles (SDE · Backend Engineer · Data Analyst · Data Scientist · ML Engineer · GenAI/LLM Engineer · Data Engineer) — 10 transition edges, common/possible/rare-blocked + skill delta
**Population:** Indian B.Tech freshers, 0–3 yr experience, 2024–2026
**Run stats:** 17 agents · 650k tokens · 10 sources useful of 12 fetched

---

## Part 1 — Transition Table

| From | To | Status | Typical Timeline | Skill Delta (top 3–5) | Key Blocker | Conf | Sources |
|---|---|---|---|---|---|---|---|
| SDE | Backend Engineer | **common** | 1–3 months | System design depth, distributed systems, DB internals, API design patterns, observability | Almost none — roles overlap heavily; mostly a title clarification | **H** | Zinnov 2026, Sentpo 2026, Scaler 2026 |
| SDE | ML Engineer | **possible** | 6–12 months | Statistics/linear algebra, ML algorithms, Python ML stack (scikit-learn/PyTorch), model evaluation, MLOps basics | Math gap; no ML work at current company; DSA gatekeeping at product cos | **H** | Sentpo 2026, Scaler 2026, Medium/@bvvreddy, NASSCOM-Draup (5.5–10.5 mo range) |
| SDE | GenAI/LLM Engineer | **possible** | 6–12 months | Foundation model APIs, RAG/LangChain/LlamaIndex, vector DBs, prompt engineering, LLMOps (LangSmith/MLflow) | DSA round gatekeeping (Razorpay/Zomato/PhonePe filter before seeing AI work); portfolio must be deployed + original | **H** | GetPersonalisedCV.in (May 2026, most documented failure case), Zinnov 2026, ShiftToTech Dec 2025, Medium/SWE-to-AI-Eng 6-mo roadmap |
| Backend Engineer | GenAI/LLM Engineer | **common** | 6–12 months | Foundation model APIs, RAG pipelines, vector DBs, LangChain, prompt engineering | Same DSA gate as SDE; skills-test bar rising at GCCs | **H** | Zinnov 2026 ("largest single pathway in GCC AI hiring today"), ShiftToTech Dec 2025, TCS→GCC documented case (5 mo, ceiling not median) |
| Data Analyst | Data Scientist | **common** | 9–12 months (realistic for working professional) | Python beyond notebooks (OOP, packaging, unit tests), ML algorithms (scikit-learn/XGBoost), linear algebra, model evaluation (AUC/precision-recall), 3–5 GitHub projects | Weak portfolio; generic DA profile losing ground to specialized DS | **H** | Analytics Vidhya AV Hiring Report 2026, NASSCOM-Draup (3–7.5 mo), Scaler 2026, ShiftToTech Dec 2025 |
| Data Analyst | Data Engineer | **common** | 3–5 months (focused) / 6–12 months (hire-ready at product co) | Production Python ETL (version-controlled, tested), Apache Airflow, data warehouse modeling (star/snowflake), one cloud deep (S3/BigQuery/Redshift), dbt | SQL depth is first-round filter — production-query level, not textbook; Airflow/Docker skipped = fail technical screen | **H** | ShiftToTech June 2026 (DA→DE guide), Kalvium May 2026, AIM Research 2024, Medium/@browsejobsmarketing Apr 2026 |
| Data Scientist | ML Engineer | **common** | 2–4 months (focused; theory already held) | Production Python (packaged, tested, not notebooks), Docker/Kubernetes basics, CI/CD for models, cloud ML platforms (SageMaker/Vertex AI), model monitoring/retraining | Market has moved: basic ML + Python no longer differentiating; must show LLM integration or model-serving-at-scale | **H** | gauravkrvish/Medium May 2025 (28% of switching DSes go MLE), Sentpo Apr 2026, ShiftToTech Dec 2025, Zinnov Apr 2026 |
| ML Engineer | GenAI/LLM Engineer | **possible** | 3–6 months | LLM APIs (OpenAI/Anthropic/Groq), RAG system design, vector DBs, LangChain/orchestration, fine-tuning basics | Classical ML training skills differ from LLM integration skills; GCCs treat them as separate talent pools (Zinnov maps MLEs toward AI Bias Expert/Synthetic Data Engineer, not GenAI Dev) | **M** | Sentpo Apr 2026 (DS→GenAI fastest path = 3–6 mo, implies MLE even easier), ShiftToTech Dec 2025, Zinnov Apr 2026 (conflicting signal on pathway) |
| Data Engineer | ML Engineer | **possible** | 6–12 months | ML theory (supervised/unsupervised, model evaluation), statistics/probability, feature engineering, model training loops, project portfolio showing ML work | DE pigeonholed in infrastructure; no ML project portfolio = hard to pass DS/MLE screens | **M** | Search synthesis, gauravkrvish/Medium May 2025 (18% of switching DSes came from DE background — reverse direction, confirms structural feasibility), AIM Research 2024 |
| Data Engineer | Data Scientist | **possible** | 6–18 months | ML fundamentals, statistics depth, feature engineering, business framing of prediction problems, ambiguity tolerance | DE's engineering certainty mindset vs DS's research/ambiguity culture; DS roles under more market pressure than MLE | **M** | Search synthesis, gauravkrvish/Medium May 2025 |

---

## Part 2 — Blocked Transition Notes

### "3 Years Experience Required" Title Inflation (cross-cutting blocker)

**What it looks like:** JDs from large Indian product companies and GCCs routinely post GenAI/LLM Engineer roles demanding 3–5 years of experience in technology that has existed for less than 3 years (ChatGPT launched November 2022). The inflation mechanism is threefold: (1) copy-paste of old Senior Data Scientist JDs with GenAI buzzwords bolted on; (2) C-suite anxiety producing inflated filters; (3) experience requirements used as proxy for "knows the plumbing, not just a ChatGPT user."

**Who gets hit hardest:** Candidates from service companies (TCS/Infosys/Wipro) where internal GenAI or ML work rarely exists in functioning form. Also non-BTech candidates (BCA/BSc) who face a compounded barrier — degree bias and experience inflation together.

**Workaround:** The posted bar and the actual hiring bar diverge. GCCs assessed 31% of entry-level hires via skills tests in 2024 (up from 19% in 2022), and 45% plan to drop degree requirements. Freshers with deployed, original portfolio projects (not tutorial copies) routinely land ₹8–15 LPA GCC/product-company roles. The path around the JD wall is: referrals (60–70% conversion vs 5–10% cold), skills-test screening, and "Associate AI Engineer" / "SWE — Backend AI Team" title targeting rather than "ML Engineer" or "LLM Engineer" directly.

---

### DSA Gatekeeping (SDE/Backend → GenAI/LLM Engineer) — the most documented blocker

**Source:** GetPersonalisedCV.in (May 2026) — the single most concrete failure account in the dataset. Candidate with 16 months of genuine AI agent work (LangGraph, Pinecone, multi-agent systems, FastAPI) remained unplaced because every product-company pipeline (Razorpay, Flipkart, Zomato, PhonePe) runs a mandatory DSA round before evaluating AI skills.

**Mechanism:** First round is a LeetCode-medium/hard filter, designed for SDE hiring pipelines. Companies never updated the pipeline for AI/GenAI lateral hires. The AI portfolio never gets seen if DSA round fails.

**Who is exempt:** Service companies (TCS/Tech Mahindra/LTIMindtree) skip the DSA gate but cap salary at ₹4–5 LPA. GCCs increasingly use skills tests instead of pure DSA (31% of GCC entry-level hires, 2024 data), making GCC applications the structurally better route for AI-portfolio-rich but DSA-weak candidates.

**Workaround:** 250–300 curated LeetCode problems (medium-hard) alongside the AI portfolio, not instead of it. Estimated 3–4 additional months of parallel prep. Target GCC applications preferentially — the skills-test path bypasses the LeetCode gate.

---

### No ML Work at Current Company (SDE → ML Engineer)

**What it looks like:** Internal SDE-to-ML transfers require organizational support. Zero documented accounts of 0–3 year SDEs at Indian companies making a successful internal team transfer to ML without the company being explicitly a "polyglot org with rapid experimentation" (Zahiruddin Tavargere's explicit condition, though he had 15+ years and was not a 0–3 yr fresher).

**Who gets hit:** SDEs at IT services (TCS/Infosys/Wipro) — these companies have no functioning internal ML pipelines for fresh engineers to transfer into. Internal L&D programs exist but produce theory knowledge, not production ML experience, and don't translate to external hire-readiness.

**Workaround:** External company switch is the de facto path. Services engineers overwhelmingly need to exit to a product company or GCC to access real ML work. Salary data reinforces this: a direct company switch from IT services to product/GCC delivers +60–150% compensation — the market has priced the company-change as the standard escape route.

---

### Service Company Trap (Data Engineer)

**What it looks like:** "Data Engineer" titles at TCS/Infosys/Wipro typically involve legacy ETL tooling (SSIS, Informatica, OBIEE) that does not map to product company or GCC expectations (Airflow, dbt, Spark, Snowflake/BigQuery). A resume showing DE experience at a services firm passes neither the ATS filter nor the technical screen at a product company.

**Workaround:** ShiftToTech's documented recommendation — take the services role for 12–18 months to get the "data engineer" title on the resume, build side projects in Airflow/dbt/Spark on real messy data (not tutorial datasets), then exit to product company/GCC for a doubled salary (₹12–18 LPA). The side project must demonstrate ownership of pipeline reliability ("daily 6 a.m. delivery"), not just query-writing.

---

## Part 3 — Mobility Graph Summary (per starting role)

### Starting as SDE
Most natural first move: Backend Engineer (common, 1–3 months, nearly friction-free — mostly a title and depth clarification). From there or directly, GenAI/LLM Engineer is the most in-demand lateral pivot (possible, 6–12 months) — Backend SDEs are explicitly the largest feeder population into GenAI Developer roles at GCCs, because production tooling (Docker, CI/CD, system design, REST APIs) transfers directly and is the gap that ML-specialists don't have. ML Engineer path is also open (possible, 6–12 months) but requires a harder math lift and carries the same DSA gatekeeping problem. The one hard blocker that cuts across both is the DSA round at product companies — 16 months of real AI portfolio work can still lose to a LeetCode failure at Razorpay or PhonePe. GCC applications bypass this most reliably.

### Starting as Backend Engineer
GenAI/LLM Engineer is now the primary high-ROI move (common at GCCs, 6–12 months). Existing production skills (APIs, Docker, system design) are the explicit advantage over data-science candidates for these roles. Zinnov calls this "the largest single pathway in GCC AI hiring today." Skill delta is narrower than for data-side candidates — adding model APIs, RAG pipelines, and vector DBs onto an already production-capable foundation. DSA gating and portfolio originality are the same barriers as for SDEs.

### Starting as Data Analyst
Two strong paths. Data Scientist is the most-trodden (common, 9–12 months realistic): SQL and business intuition transfer; Python-to-production and ML algorithms are the main climb. Data Engineer is increasingly the higher-ROI move (common, 3–5 months to focused hire-readiness): SQL is the biggest asset entering DE interviews, and DE compensation has risen faster than DA since 2023. The single hardest filter on both paths is SQL depth — not textbook SQL but reading and writing 200-line production queries under interview conditions. DA→Data Scientist is under more competition (generic DS profiles losing ground); DA→Data Engineer benefits from a structural talent shortage (230,000+ open positions projected by 2026).

### Starting as Data Scientist
The market is actively pushing toward ML Engineer (common, 2–4 months if Python and ML theory already held). 28% of switching Indian data scientists are going this direction. The gap is purely engineering depth — Docker, CI/CD, model serving, cloud ML platforms — not additional ML theory. GenAI/LLM Engineer is possible (3–6 months) but Zinnov's GCC mapping shows this path is less clean: GCCs prefer Backend/SDE engineers for GenAI Dev roles and route Data Scientists toward AI Bias Expert or Synthetic Data Engineer instead. A move to Data Engineer is also possible (possible, 6–18 months) and offers more stable demand and better work-life balance but is seen internally as lateral-to-down rather than up.

### Starting as ML Engineer
GenAI/LLM Engineer is the adjacent move (possible, 3–6 months): add LLM APIs, RAG patterns, vector DBs, LangChain. The nuance is that GCCs treat classical ML skills and LLM integration skills as different talent pools — an MLE resume doesn't auto-qualify for GenAI Dev roles at GCCs even though the underlying engineering is similar. The path is real but requires explicit LLM project work in portfolio, not just ML credentials.

### Starting as Data Engineer
The most structurally efficient unrecognized path is DE→ML Engineer (possible, 6–12 months). DEs already hold production Python, cloud platforms, Docker/Kubernetes awareness, and pipeline orchestration — the entire engineering depth that most MLEs lack. Adding ML theory and model training on top produces a very competitive MLE profile. DE→Data Scientist is also possible but harder because DS roles involve research ambiguity that contrasts with DE's engineering certainty, and the DS market is under more GenAI disruption pressure than MLE. Primary blocker on any DE→ML/DS move is absence of ML project portfolio — the resume gets screened out without it.

---

## Part 4 — Coverage Gaps & Evidence Quality Notes

### SDE → Backend Engineer
Near-zero research evidence needed or found because the boundary between these roles is blurry in the Indian market. "Backend Engineer" is essentially a seniority/specialization label applied to SDEs who go deeper on distributed systems and API infrastructure. No independent transition literature exists because companies treat it as a same-track progression, not a domain switch. Confidence is high that it is common, but the "typical timeline" number (1–3 months) is an inference, not a measured datum.

### ML Engineer → GenAI/LLM Engineer
Conflicting signals. Sentpo (Apr 2026) implies this is one of the fastest transitions (DS→GenAI in 3–6 months, MLE should be even shorter). Zinnov (Apr 2026) maps MLEs toward AI Bias Expert and Synthetic Data Engineer in GCCs, explicitly not toward GenAI Developer — which is sourced from Backend/SDE populations. These sources point in different directions. No first-person Indian MLE-to-LLM-Engineer transition account was found. Confidence is medium; the true answer likely depends on whether the target is a GCC (Zinnov's mapping applies) or a startup/product company (Sentpo's framing applies).

### Data Engineer → ML Engineer / Data Scientist
The reverse direction (18% of switching DSes came from DE backgrounds per gauravkrvish/Medium) is documented. The forward direction (DE explicitly targeting MLE or DS) has thin first-person India evidence. The structural argument is strong (DE has the engineering half, needs the ML theory half) but no concrete Indian fresher account was found. Confidence medium.

### Data Scientist → GenAI/LLM Engineer (direct)
Sentpo calls this "fastest and highest-ROI upskilling path" (3–6 months). Zinnov contradicts, mapping DSes away from GenAI Developer roles. Reddit and Blind — the highest-signal community sources — were inaccessible to web crawlers throughout all four searches, which is the single biggest evidence gap in this entire dataset. All community-sourced data points came indirectly through third-party aggregators or practitioner blogs. The GenAI job market is also moving at 18–24 month skill-cycle speeds, meaning any source older than mid-2025 may already be stale on specifics.

### Non-BTech background (BCA/BSc IT)
The GetPersonalisedCV.in case study (May 2026) is the only documented account and it describes a blocked state after 16 months. No successful 0–3 yr BCA/BSc→product-company AI Engineer transition was found in the public record. The degree-bias compounding effect (non-BTech + no experience + DSA gate) is real and underdocumented — this is an active gap.

---

## Salary Reference Table (India, 2025–2026)

| Role | Entry (0–2 yr) | Mid (3–5 yr) | Senior (6+ yr) |
|---|---|---|---|
| Data Analyst | ₹5–9 LPA | ₹9–18 LPA | ₹18–30 LPA |
| Data Scientist | ₹10–15 LPA | ₹15–28 LPA | ₹28–50 LPA+ |
| Data Engineer | ₹6–14 LPA (product/GCC) | ₹16–32 LPA | ₹35–65 LPA |
| ML Engineer | ₹14–20 LPA | ₹20–35 LPA | ₹35–65 LPA+ |
| GenAI/LLM Engineer | ₹8–15 LPA (fresher, GCC) | ₹18–40 LPA | ₹40–90 LPA |
| SDE | ₹8–20 LPA | ₹20–40 LPA | ₹40–80 LPA |
| Backend Engineer | ₹8–22 LPA | ₹22–45 LPA | ₹45–85 LPA |

---

## Sources Fetched

| URL | Useful | Type | Date |
|---|---|---|---|
| getpersonalisedcv.in/blog/ai-ml-learning-dsa-rejection-india-2026 | Yes | Blog | May 2026 |
| linkedin.com/posts/neha-jain… | No | LinkedIn | 2024 |
| linkedin.com/pulse/how-i-transitioned-ai-engineer-zahiruddin-tavargere | Yes | LinkedIn | Feb 2024 |
| sentpo.com/ai-and-ml-careers-in-india-2026 | Yes | Blog | Apr 2026 |
| shifttotech.co.in/blog/ai-ml-jobs-india-2025-complete-guide | Yes | Blog | Dec 2025 |
| kalvium.com/blog/data-engineer-career-india | Yes | Blog | May 2026 |
| gauravkrvish.medium.com/why-80-of-indian-data-scientists-are-switching | Yes | Medium | May 2025 |
| shifttotech.co.in/blog/how-to-become-data-engineer-india | Yes | Blog | Jun 2026 |
| medium.com/@browsejobsmarketing/how-to-break-into-data-engineering-in-india | Yes | Medium | Apr 2026 |
| scaler.com/topics/career-transition-to-data-science | Yes | Blog | 2026 |
| medium.com/@dedeepyayarlagadda/the-great-ai-paradox | No | Medium | Feb 2026 |
| zinnov.com/centers-of-excellence/8-new-ai-jobs-in-gccs | Yes | Blog | Apr 2026 |

---

## Key Cross-Run Findings (for roadmap metadata)

From all 3 runs combined:

1. **DSA is a gatekeeping round for ALL roles including GenAI** — not just SDE. Confirmed across 3+ sources in Run 1, again in Run 3. Even 16 months of real LLM engineering work loses to a bad LeetCode round at a product company.

2. **Backend Engineer → GenAI is the single highest-ROI transition in 2026** — Zinnov explicitly calls it "the largest single pathway in GCC AI hiring today." B.E.s have the production infra skills that data-side candidates don't.

3. **DA → DE is underrated**: faster than DA→DS (3–5 months vs 9–12), more in-demand (230k+ open roles), better salary trajectory. SQL is already the biggest DE interview filter and it's a DA's natural strength.

4. **ML Engineer → GenAI is structurally ambiguous**: GCCs route MLEs toward AI Bias Expert / Synthetic Data Engineer, NOT GenAI Developer. Startups/product companies treat it as the adjacent move. Target matters.

5. **Service company trap is real**: Internal titles (TCS/Infosys DE, SDE) don't map to product company or GCC job requirements. The de facto path is: get title for 12–18 months → build side projects in the real stack → external company switch for +60–150% compensation.
