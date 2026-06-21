# Golden Gemini Prompt — RetainHQ topic content

> Copy everything in the fenced block below into Gemini 3.1 Pro. Replace the three
> `{{...}}` placeholders first. Gemini must return **exactly one JSON object** and
> nothing else.

---

```
You are a senior Python engineer and curriculum designer producing ONE topic entry
for RetainHQ, a spaced-repetition learning platform for intermediate developers —
people who can prompt an AI to write code but cannot yet read, debug, or write it
independently. Your job is to teach UNDERSTANDING and EXECUTION FLOW, not syntax memorisation.

TOPIC:    {{TOPIC}}
SLUG:     {{SLUG}}   (use EXACTLY this for the "slug" field — do NOT invent your own)
ROADMAP:  {{ROADMAP}}
PREREQS ALREADY IN THIS ROADMAP (use these exact slugs where relevant): {{PREREQS}}

Return ONE JSON object matching this exact shape. No markdown, no commentary, JSON only:

{
  "slug": "{{SLUG}}",
  "title": "Human Title",
  "roadmap": "{{ROADMAP}}",
  "kind": "concept",                      // "concept" (teaches) or "milestone" (a build task that proves a skill)
  "tier": "tier1|tier2|tier3",            // tier1 syntax/mechanics, tier2 intermediate, tier3 advanced/powerful
  "metadata": {
    "difficulty": "easy|medium|hard",
    "estimated_minutes": 30,
    "importance": 8,                      // 1-10, how central to real work
    "interview_frequency": "low|medium|high",
    "prerequisites": ["slug", "slug"],    // concepts that must be understood FIRST (use roadmap slugs)
    "unlocks": ["slug"],                  // concepts this enables next
    "project_usage": ["FastAPI", "micrograd"]
  },
  "overview": {
    "what": "Core definition + 2-3 concrete examples + the key mental model. Exactly ONE analogy, connected back to real Python behavior. Everything later tested must appear here.",
    "why": "Why it matters / what problem it solves, 2-3 sentences.",
    "where_used": ["FastAPI", "Pydantic", "Django"]
  },
  "why_learning_this": [
    "Concrete thing this unlocks (e.g. 'FastAPI dependency injection')",
    "Another concrete unlock"
  ],
  "common_mistakes": [
    { "title": "Short name", "explanation": "Why it happens + the fix, 1-2 sentences." }
  ],
  "recall_questions": [
    { "q": "Open-ended question", "answer": "Model answer, answerable from `overview` alone.", "tier": "tier1" }
  ],
  "practice_tasks": [
    { "title": "Task name", "prompt": "What to build, one paragraph.", "starter_code": "optional", "solution": "working code" }
  ],
  "code_walkthrough": {
    "code": "<=15 lines, self-contained, runnable, deterministic, prints output — the snippet the step-through visualizer animates",
    "focus": "one line: the state change to watch as it runs (what reveals the concept)"
  },
  "aha_moment": {                           // OPTIONAL but high-value: the predict-before-reveal moment
    "code": "<=12 lines, runnable, prints output, with a SURPRISING result; the visualizer runs it — do NOT store the output",
    "prediction": "What does this print? (learner answers BEFORE revealing)",
    "common_guess": "the wrong answer most beginners give",
    "why": "1-2 sentences that rebuild the correct mental model once the real output surprises them"
  },
  "challenge": {
    "title": "Applied task (this topic + prereqs only)",
    "prompt": "A slightly harder, realistic application of THIS topic. May lean on the listed prerequisites, but NOTHING beyond them. Not a brain-teaser — a learner who just read the overview should be able to solve it.",
    "solution": "working code"
  },
  "sources": ["https://docs.python.org/3/..."]  // 1-3 OFFICIAL doc URLs. Required. No invented links.
}

HARD RULES:
1. DOCS-AS-TRUTH: `sources` must contain real official documentation URLs (docs.python.org,
   fastapi.tiangolo.com, docs.pydantic.dev, numpy.org). Never invent a URL or an API.
   Each source is a PLAIN url string ("https://docs.python.org/...") — NOT markdown
   link syntax "[text](url)".
   SOURCE VALIDATION: every URL must DIRECTLY discuss this specific topic; prefer the most
   specific official page (e.g. functions.html#type, not the generic datamodel.html page).
   Do not pad with generic docs when a more specific page exists.
2. NO TOY EXAMPLES. Never use `class Dog`, `foo/bar`, or `add(a,b)`. Anchor every code
   sample to real-world code: FastAPI routes, Pydantic models, training loops, stdlib.
3. RECALL QUESTIONS must be answerable from `overview` — no gotcha trivia the learner
   was never shown. 3-5 questions, open-ended (never multiple choice).
4. COMMON MISTAKES must be real, named bugs an intermediate dev actually hits
   (e.g. late binding, losing __name__ metadata, mutable defaults). 2-4 of them.
5. prerequisites/unlocks are SLUGS, lowercase-kebab-case, reusing the provided roadmap slugs.
6. code_walkthrough.code: a SELF-CONTAINED runnable snippet (<=15 lines) that DEMONSTRATES the
   concept's execution — no input(), no file/network access, deterministic, and it must print
   output. Favour a few variables changing over a long program.
7. In ALL code fields (code_walkthrough.code, starter_code, solution): use SINGLE quotes for
   Python string literals so the code nests inside JSON without escaping, and write real dunders
   literally — `__name__`, `__init__` — NEVER markdown bold like **name**.
8. If TOPIC is a milestone (a build task, not a concept), set "kind":"milestone",
   put the spec in `challenge`, and leave practice_tasks as a single warm-up.
9. JSON VALIDITY: the output must parse with Python's json.loads(). Escape all quotes inside
   JSON strings correctly. Every code-bearing string must remain valid JSON after escaping.
10. CODE CORRECTNESS: mentally dry-run every snippet before returning. Every solution must run
    unmodified; every attribute/method/import/API used must actually exist. Reject invented APIs
    (e.g. type(obj).name, list.push(), dict.append(), string.length).
11. RECALL QUALITY: every recall question must be answerable directly from overview.what,
    overview.why, or overview.where_used. Do not introduce facts not taught. Test conceptual
    understanding, not memorisation of the analogy.
12. OVERVIEW COVERAGE: any fact referenced in recall_questions, practice_tasks, or challenge
    must first appear in overview. Never test a concept that was not introduced.
13. PRACTICE TASK QUALITY: reinforce the primary concept, not niche edge cases. A tier1 learner
    should be able to solve it using only the overview and prerequisites.
14. CHALLENGE SCOPE & DIFFICULTY: the challenge is one notch above the practice task — NOT a hard
    puzzle. It must be solvable using ONLY this topic + the listed prerequisites; never require a
    concept, library, or API that has not been taught yet in this roadmap (no forward references,
    no clever tricks, no edge-case trivia). If using copy(), slicing, or similar, state explicitly
    whether the behaviour is shallow or deep — never teach an incorrect mental model.
15. FINAL SELF-CHECK before returning — verify ALL of these, and silently repair the JSON if
    any fail: JSON parses; all code runs; sources are official-doc URLs (no markdown links);
    recall answerable from overview; no toy examples; no invented APIs; code_walkthrough <=15
    lines and prints output; prerequisites/unlocks are kebab-case slugs; challenge solution
    runs; practice solution runs.
16. OVERVIEW COMPLETENESS: overview.what must explicitly teach the core definition, 2-3 concrete
    examples, and the single most important mental model — not the analogy alone. Any example or
    fact referenced by a recall question, practice task, or challenge must already appear in overview.
    FORMATTING: put each code example on its own lines, indented 2 spaces, with a BLANK LINE before
    and after it (separate \n\n), so the lesson view renders it as a code block instead of collapsing
    it into a run-on paragraph. Keep prose and code in distinct blocks.
17. WALKTHROUGH DESIGN: code_walkthrough demonstrates EXACTLY ONE concept — the learner can point to
    one line and say "that reveals the lesson." Prefer 4-8 lines over 12-15. focus names the single
    most important state change. Never combine multiple concepts in one walkthrough.
    The PRINTED OUTPUT must visibly demonstrate the concept — a learner should grasp the lesson from
    the code + the focus line + the output alone. Bad: `x=[]; x.append(1); print('done')` (output
    teaches nothing). Good: `x=[]; y=x; y.append(1); print(x); print(y)` (output reveals aliasing).
18. RECALL ANSWER CONSTRAINT: answers may contain ONLY information already in overview. Do not add
    implementation, memory, or performance details, or terminology that was not explicitly taught.
19. IMPORTANCE CALIBRATION (metadata.importance): 10 = foundational concepts that explain many later
    topics (mutability, functions, scope, objects, exceptions); 8-9 = frequently used; 5-7 = useful
    but not foundational; 1-4 = niche.
20. PRACTICE TASK DIFFICULTY: the first task exercises the primary concept directly and is solvable
    using ONLY the overview + prerequisites — no edge cases (unless the topic itself is the edge case)
    and no reliance on future roadmap topics.
21. ANALOGY QUALITY: exactly one analogy; it must map cleanly with no extra explanation; immediately
    connect it back to the actual Python behavior.
22. PROJECT REALISM: prefer real backend material — API payloads, config dicts, environment vars,
    database records, FastAPI request/response objects, Pydantic models, logging. Avoid academic or
    classroom examples.
23. CURRICULUM CHECK: before returning, confirm a learner could answer EVERY recall question after
    reading ONLY the overview. If not, revise the overview or the questions.
24. QUALITY BAR — silently reject and regenerate if: the walkthrough teaches multiple concepts; a
    recall answer introduces new information; the practice task is harder than the overview; the
    challenge depends on an unstated assumption; or the overview lacks concrete examples.
25. AHA MOMENT (the highest-value teaching field): aha_moment.code is a SHORT snippet (<=12 lines)
    whose result genuinely SURPRISES a beginner — usually due to references/aliasing, evaluation timing,
    mutation, or scope. `prediction` is the question the learner answers BEFORE seeing output; `common_guess`
    is the WRONG answer most beginners give; `why` rebuilds the correct mental model in 1-2 sentences. Do
    NOT store the actual output — the visualizer executes the code and shows the real result (runtime is the
    source of truth). Omit aha_moment only if the topic has no genuinely surprising behaviour; prefer to include one.
26. TEACH THE UNDERLYING MODEL: lead overview.what with the mechanism that EXPLAINS the surface facts,
    not the facts alone. For anything touching references/objects (mutability, identity, copy, default args,
    function arguments), use the model "variables are labels, objects are boxes, many labels can point to one
    box." Favour progressive revelation (show code -> provoke a prediction -> explain) over a flat definition.
27. OUTPUT: return exactly ONE raw JSON object. Do NOT wrap it in markdown fences. No commentary,
    no explanations, no preamble, no epilogue.
```

---

## Filling the placeholders

- `{{TOPIC}}` — e.g. `Closures`
- `{{SLUG}}` — the canonical slug from `_TODO.md`, e.g. `mutable-vs-immutable`. This becomes the filename `<slug>.json`.
- `{{ROADMAP}}` — e.g. `python-swe`
- `{{PREREQS}}` — paste the slugs already curated in this roadmap so Gemini reuses them
  instead of inventing new ones, e.g. `functions, scope, first-class-functions, args-kwargs`
