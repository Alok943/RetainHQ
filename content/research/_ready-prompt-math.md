═══════════════════════════════════════════════════════════════════════
CHANGE ONLY THESE 4 LINES PER ROADMAP — everything below stays as-is
(this is the PREREQUISITE-SUBJECT variant of the prompt — see the two starred rules)
═══════════════════════════════════════════════════════════════════════
ROADMAP: Math for ML (Probability & Statistics, Linear Algebra, Calculus for Optimization)
TARGET ROLES: aspiring ML Engineer / Data Scientist in India, 0–4 years / new-grad & early-career — i.e. the math that ML/DS INTERVIEWS test and that ML MODELS require, not a math degree
CANON (cross-check only): "Mathematics for Machine Learning" (Deisenroth, Faisal, Ong); 3Blue1Brown Essence of Linear Algebra + Essence of Calculus; the math sections of Andrew Ng's ML/DL courses
TARGET NODE COUNT: 32–40
═══════════════════════════════════════════════════════════════════════


You are a senior ML interviewer and a working ML engineer who mentors juniors. You are doing rigorous, citation-backed research to design the node list for the ROADMAP above — the list of topics it should teach, NOT the lesson content. You know exactly which math these interviews test and which math a practitioner actually needs to understand and debug models.

Treat the geography above as the national tech-hiring market concentrated in the major metros (Bangalore, Hyderabad, Pune, NCR/Gurugram, Chennai). Ignore my current location entirely — do NOT localize to where I am browsing from.

GOVERNING PRINCIPLE — "enough, not a PhD":
A node earns inclusion ONLY if you can name either (a) a real interview question asked of these roles where knowing this math decides the answer, OR (b) *** a specific ML/DS technique, model, or metric that a practitioner cannot understand, derive, or debug without this math *** (e.g. you cannot understand PCA without eigenvectors, regularization without vector norms, backprop without the chain rule, or logistic regression without the sigmoid + log-loss derivation). If you can name neither, CUT IT — that is the PhD direction.

*** ANTI-PROOF RULE (this roadmap's specific failure mode) ***: teach the APPLIED INTUITION and the ML CONNECTION, not the formal mathematics. For every node, INCLUDE: what the concept means geometrically/intuitively, and the ML method it unlocks. EXCLUDE: formal proofs, theorem-proving, epsilon-delta rigor, hand-derivation of results a library computes, and pure-math topics with no ML payoff (e.g. abstract group theory, measure-theoretic probability, manual matrix-inversion drills). A node that is a proof is wrong; a node that is "the intuition + the model it powers" is right. If a topic is mathematically important but no ML method or interview needs it, it goes in the excluded list as "canon-only".

EVIDENCE — gather in THIS priority order (inclusion comes from 1 and 2; source 3 is a cross-check only):
1. Sweep real ML Engineer / Data Scientist job postings and their stated math prerequisites, plus the math that recurs across ML course syllabi these roles are hired from (LinkedIn, Naukri, Wellfound, Instahyre, company career pages).
2. Find the MATH questions ACTUALLY asked in ML/DS interviews for these roles — from interview-experience posts (Glassdoor, LeetCode discuss, GeeksforGeeks interview experiences, Reddit r/MachineLearning, r/datascience). Capture the recurring question-families (bias-variance, why gradient descent converges, eigenvectors in PCA, probability brain-teasers, maximum likelihood, etc.).
3. Cross-check against the CANON above ONLY to catch anything genuinely core that evidence 1–2 missed. Canon reveals GAPS; it never justifies inclusion on its own. If canon covers something interviews and ML methods do not need, it stays OUT (record it in the excluded list with reason "canon-only").

BOUNDARY — keep only what THIS roadmap owns: the math prerequisites for ML. If a concept is actually an ML/DS TOPIC rather than the math under it (e.g. the full backpropagation algorithm, a specific model architecture, feature engineering), cut it and record it as "belongs-in-<ML/Deep-Learning/Data-Science roadmap>". This roadmap teaches the math a model rests on, not the model.

DERIVATION:
- Extract testable question-families — one concept an interviewer probes, or one piece of math a specific ML method requires = one node. A big topic that needs a whole chapter is several nodes; split it.
- Frequency-weight the candidates and cut the low-frequency / no-ML-payoff ones to hold the TARGET NODE COUNT above.
- Structure each node as: phase (the prerequisite spine step — group by the three subjects: Probability & Statistics, Linear Algebra, Calculus & Optimization, ordered so foundations come first) → section (a cluster of 2–6 nodes within a phase) → tier → title → description.
- tier = depth: easy = definition/recognition; medium = intuition/trade-off; hard = the harder derivation or the concept people most often get wrong in interviews.

VALIDATE before finishing (the mock-interview test):
- Write 10 real ML/DS interview questions (or "you can't understand method X without this" statements) across the three subjects. EVERY one must land on at least one node — one with no home means a missing node, so add it.
- EVERY node must catch at least one of those questions OR name the specific ML method it unlocks. If a node maps to nothing, either add the question/method that justifies it or cut it — do not leave it silently unmapped.
- Check the tier mix: if almost nothing is hard, you under-scoped; if it's full of proofs, you over-scoped — retighten toward applied intuition.
- Each phase must complete: "learn this phase SO THAT you can ___ (understand/derive/debug which ML method or answer which interview question)." If the blank is "understand the math better," the phase is too academic — retighten it.

RETURN EXACTLY THIS, and nothing else:

1. A Python NODES list ready to paste into a seed script. Above the list give:
   SLUG = "math-for-ml"
   TITLE = (a short roadmap title)
   DESCRIPTION = (one sentence describing the roadmap)
   Then the list, grouped by phase in learning order, with a comment line before each phase's block:
   NODES = [
       # ---- <phase name> ----
       ("<phase>", "<section>", "<title>", "<tier>", "<description>"),
       ...
   ]
   Each description = ONE recall-testable claim of 120 characters or fewer, mechanism-first, and where possible naming the ML method it unlocks — state the claim, not a label. Write "Eigenvectors point where a matrix only scales, not rotates — the axes PCA projects onto for max variance", NOT "learn about eigenvectors". All text plain — no LaTeX, no images; write math as plain text (e.g. O(n), x^2, sqrt, sum).

2. An `excluded` list: things a naive math syllabus WOULD include but you cut. Each entry as {item, reason}, reason one of: low-frequency, canon-only, no-ML-payoff, proof-only, belongs-in-<roadmap>, out-of-scope. Make this list substantial — it proves scope discipline.

3. A `validation` section: the 10 interview questions / "can't understand X without this" statements you used, each mapped to the node(s) that cover it. Flag any node that maps to nothing. Then one "so that" sentence per phase.

4. A `sources` list: 8–15 real URLs you actually consulted, split into jd / interviews / canon. No fabricated links.

Cite sources, but never copy their wording — write everything in your own words. If you produce a prose research report first, then convert it into exactly the four-part format above and output only that. Descriptions 120 characters or fewer, each a testable claim, plain-text math only. Node count within the target above.
