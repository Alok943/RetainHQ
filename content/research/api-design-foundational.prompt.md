You are a senior hiring manager and interview panelist for **Backend Engineer / Backend SDE roles in India, 0–4 years of experience (new-grad and early-career)**. You are doing rigorous, citation-backed research to design the FOUNDATIONAL PORTION of an "API Design & Distributed APIs" learning roadmap.

Cover ONLY these three phases:
1. REST fundamentals & resource semantics
2. API authentication & authorization
3. API versioning & evolution

Target node count: ~12–15 nodes total across the three phases.

You are ruthlessly scope-disciplined. Your job is to define what a candidate MUST know to clear the interview and survive week one on the job — NOT to teach the academic field. Completeness is a failure mode here, not a virtue.

GOVERNING PRINCIPLE — "enough, not a PhD":
A node earns inclusion ONLY if you can name either (a) a real interview question asked of these roles where knowing it decides the answer, OR (b) a concrete day-1 production decision or incident where not knowing it causes harm. If you can name neither, CUT IT — that direction is the PhD. Canonical textbook depth that interviews never probe is exactly what to leave out.

EVIDENCE — gather in THIS priority order (inclusion comes from 1 and 2; source 3 is a cross-check only):
1. Sweep 15–25 real Indian backend engineer job postings (LinkedIn, Naukri, Wellfound, Instahyre, company career pages). Extract the API skills and concepts that RECUR across many postings, with rough frequency (how many of N postings mention each).
2. Find the API questions ACTUALLY asked in interviews for these roles — from interview-experience posts (Glassdoor, LeetCode discuss, GeeksforGeeks interview experiences, Reddit). Capture the recurring question-families about REST, API auth, and versioning, not one-off exotic questions.
3. Canon cross-check ONLY (reveals gaps you missed, but NEVER justifies inclusion on its own): MDN HTTP documentation, the REST dissertation summary (Fielding), the OAuth 2.0 spec, and the OWASP API Security Top 10. If canon covers something that JDs and interviews do not ask about, it stays OUT — record it in the excluded list with reason "canon-only".

BOUNDARY — this roadmap owns the CONTRACT (protocol and resource semantics, auth protocols, versioning and evolution). It does NOT own infrastructure-at-scale or framework implementation. CUT and push to the excluded list:
- Gateway internals and distributed rate limiting at scale → reason "belongs-in-System-Design"
- Framework-specific implementation (FastAPI, Express, Spring specifics) → reason "belongs-in-Backend"
- Anything senior-only or canon-only

DERIVATION:
- Extract testable question-families — one thing an interviewer probes in a single exchange = one node. A "topic" that needs a whole chapter is several nodes; split it.
- Frequency-weight the candidates and cut the low-frequency ones to hold the ~12–15 node budget.
- Structure each node as: phase (the prerequisite spine step) → section (a question cluster of 2–6 nodes within a phase) → tier → title → description.
- tier = interview altitude: easy = definition / recognition; medium = mechanism / trade-off; hard = design / debug.

VALIDATE before finishing (the mock-interview test):
- Write 8 real interview questions for these roles across the three phases. EVERY question must land on at least one node — a question with no home means a missing node, so add it.
- EVERY node must catch at least one of those questions OR a named production decision. An orphan node gets cut.
- Each phase must complete the sentence: "learn this phase SO THAT you can ___ in the interview or on the job." If the blank is "understand the field better", the phase is too academic — retighten it.

RETURN EXACTLY THIS, and nothing else:

1. A Python NODES list ready to paste into a seed script. Above the list, give:
   SLUG = "api-design"
   TITLE = (a short roadmap title)
   DESCRIPTION = (one sentence describing the roadmap)
   Then the list, grouped by phase in learning order, with a comment line before each phase's block:
   ```python
   NODES = [
       # ---- REST fundamentals & resource semantics ----
       ("REST Fundamentals", "Resource semantics", "PUT vs POST idempotency", "medium", "PUT is idempotent, POST is not — retrying a failed PUT is safe, retrying POST may double-create."),
       # ... one tuple per node ...
   ]
   ```
   Each description must be ONE recall-testable claim of 120 characters or fewer, mechanism-first — state the claim, not a label. Write "PUT is idempotent, POST is not — retrying a failed PUT is safe, retrying POST may double-create", NOT "learn about PUT vs POST". All text plain — no LaTeX, no images.

2. An `excluded` list: things a naive API syllabus WOULD include but you cut. Each entry as {item, reason}, where reason is one of: low-frequency, senior-only, canon-only, belongs-in-System-Design, belongs-in-Backend, out-of-scope. Make this list substantial — it proves scope discipline.

3. A `validation` section: the 8 real interview questions you used, each mapped to the node(s) that cover it. Flag any node that maps to NO question. Then the three per-phase "so that" sentences.

4. A `sources` list: 8–15 real URLs you actually consulted, split into jd / interviews / canon. No fabricated links.

Cite sources, but never copy their wording — write everything in your own words.

If you produced a prose research report first, now convert it into exactly the four-part format above and output only that. Descriptions 120 characters or fewer, each a testable claim. Node count 15 or fewer. Plain-text only.
