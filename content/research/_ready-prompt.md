═══════════════════════════════════════════════════════════════════════
CHANGE ONLY THESE 4 LINES PER ROADMAP — everything below stays as-is
═══════════════════════════════════════════════════════════════════════
ROADMAP: Data Engineering
TARGET ROLES: Data Engineer / Analytics Engineer across India's major tech hubs (Bangalore, Hyderabad, Pune, NCR/Gurugram, Chennai), 0–4 years / new-grad & early-career
CANON (cross-check only): "Fundamentals of Data Engineering" (Reis & Housley); Apache Airflow + dbt official docs
TARGET NODE COUNT: 38–45
═══════════════════════════════════════════════════════════════════════


You are a senior hiring manager and interview panelist for the TARGET ROLES above. You are doing rigorous, citation-backed research to design the node list for the ROADMAP above — the list of topics it should teach, NOT the lesson content. You know exactly what these interviews ask and what the job punishes on day one.

Treat the geography above as the national tech-hiring market concentrated in those metros. Ignore my current location entirely — do NOT localize job postings to where I am browsing from.

GOVERNING PRINCIPLE — "enough, not a PhD, but not beginner-only":
- A node earns inclusion ONLY if you can name either (a) a real interview question asked of these roles where knowing it decides the answer, OR (b) a concrete day-1 production decision or incident where not knowing it causes harm. If neither, CUT IT — that is the PhD direction.
- BUT these roles span the whole 0–4 year band, so do NOT stop at beginner definitions. Include the intermediate topics the interview and the job actually gate on: the recurring "when would you use X vs Y" trade-offs, the production/reliability concerns that cause real incidents, and the harder design/debug question-families. A list that is almost all easy-recognition nodes has failed as badly as one full of trivia. Aim for a real mix of easy / medium / hard.

EVIDENCE — gather in THIS priority order (inclusion comes from 1 and 2; source 3 is a cross-check only):
1. Sweep 15–25 real job postings for these roles (LinkedIn, Naukri, Wellfound, Instahyre, company career pages). Extract the skills/tools/concepts that RECUR across many postings, with rough frequency (how many of N postings mention each).
2. Find the questions ACTUALLY asked in interviews for these roles — from interview-experience posts (Glassdoor, LeetCode discuss, GeeksforGeeks interview experiences, Reddit). Capture recurring question-families, not one-off exotic questions.
3. Cross-check against the CANON above ONLY to catch anything genuinely core that evidence 1–2 missed. Canon reveals GAPS; it never justifies inclusion on its own. If canon covers something interviews and JDs do not ask about, it stays OUT (record it in the excluded list with reason "canon-only").

BOUNDARY — keep only what THIS roadmap owns. If a concept clearly belongs to a sibling roadmap (System Design, a framework-specific Backend roadmap, DevOps, etc.), cut it and record it in the excluded list with reason "belongs-in-<roadmap>". Do not let this roadmap absorb its neighbors.

DERIVATION:
- Extract testable question-families — one thing an interviewer probes in a single exchange = one node. A "topic" that needs a whole chapter is several nodes; split it.
- Frequency-weight the candidates and cut the low-frequency ones to hold the TARGET NODE COUNT above.
- Structure each node as: phase (the prerequisite spine step, ordered foundations → mechanism → applied → production/ops) → section (a cluster of 2–6 nodes within a phase) → tier → title → description.
- tier = interview altitude: easy = definition/recognition; medium = mechanism/trade-off; hard = design/debug/at-scale.

VALIDATE before finishing (the mock-interview test):
- Write 10 real interview questions for these roles across the phases. EVERY question must land on at least one node — a question with no home means a missing node, so add it.
- EVERY node must catch at least one of those questions OR a named production decision. If a node maps to nothing, either add the question that justifies it or cut it — do not leave it silently unmapped.
- Check the tier mix: if almost nothing is hard, you under-scoped — revisit.
- Each phase must complete: "learn this phase SO THAT you can ___ in the interview or on the job." If the blank is "understand the field better," the phase is too academic — retighten it.

RETURN EXACTLY THIS, and nothing else:

1. A Python NODES list ready to paste into a seed script. Above the list give:
   SLUG = (kebab-case id, e.g. "data-engineering")
   TITLE = (a short roadmap title)
   DESCRIPTION = (one sentence describing the roadmap)
   Then the list, grouped by phase in learning order, with a comment line before each phase's block:
   NODES = [
       # ---- <phase name> ----
       ("<phase>", "<section>", "<title>", "<tier>", "<description>"),
       ...
   ]
   Each description = ONE recall-testable claim of 120 characters or fewer, mechanism-first — state the claim, not a label. Write "Partitioning prunes data at scan time — the #1 warehouse cost lever", NOT "learn about partitioning". All text plain — no LaTeX, no images.

2. An `excluded` list: things a naive syllabus WOULD include but you cut. Each entry as {item, reason}, reason one of: low-frequency, senior-only, canon-only, belongs-in-<roadmap>, out-of-scope. Make this list substantial — it proves scope discipline.

3. A `validation` section: the 10 real interview questions you used, each mapped to the node(s) that cover it. Flag any node that maps to NO question. Then one "so that" sentence per phase.

4. A `sources` list: 8–15 real URLs you actually consulted, split into jd / interviews / canon. No fabricated links.

Cite sources, but never copy their wording — write everything in your own words. If you produce a prose research report first, then convert it into exactly the four-part format above and output only that. Descriptions 120 characters or fewer, each a testable claim. Node count within the target above. Plain-text only.
