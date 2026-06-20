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
ROADMAP:  {{ROADMAP}}
PREREQS ALREADY IN THIS ROADMAP (use these exact slugs where relevant): {{PREREQS}}

Return ONE JSON object matching this exact shape. No markdown, no commentary, JSON only:

{
  "slug": "kebab-case-id",
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
    "what": "Plain-language definition in 2-4 sentences. Use ONE analogy.",
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
  "challenge": {
    "title": "Production-flavoured task",
    "prompt": "A realistic task that combines this topic with its prerequisites.",
    "solution": "working code"
  },
  "sources": ["https://docs.python.org/3/..."]  // 1-3 OFFICIAL doc URLs. Required. No invented links.
}

HARD RULES:
1. DOCS-AS-TRUTH: `sources` must contain real official documentation URLs (docs.python.org,
   fastapi.tiangolo.com, docs.pydantic.dev, numpy.org). Never invent a URL or an API.
   Each source is a PLAIN url string ("https://docs.python.org/...") — NOT markdown
   link syntax "[text](url)".
2. NO TOY EXAMPLES. Never use `class Dog`, `foo/bar`, or `add(a,b)`. Anchor every code
   sample to real-world code: FastAPI routes, Pydantic models, training loops, stdlib.
3. RECALL QUESTIONS must be answerable from `overview` — no gotcha trivia the learner
   was never shown. 3-5 questions, open-ended (never multiple choice).
4. COMMON MISTAKES must be real, named bugs an intermediate dev actually hits
   (e.g. late binding, losing __name__ metadata, mutable defaults). 2-4 of them.
5. prerequisites/unlocks are SLUGS, lowercase-kebab-case, reusing the provided roadmap slugs.
6. code_walkthrough.code: a SELF-CONTAINED runnable snippet (<=15 lines) that DEMONSTRATES the
   concept's execution — no input(), no file/network access, deterministic, and it must print
   output. This is what the step-through visualizer animates, so favour a few variables changing
   over a long program.
7. If TOPIC is a milestone (a build task, not a concept), set "kind":"milestone",
   put the spec in `challenge`, and leave practice_tasks as a single warm-up.
8. Output ONLY the JSON object. No ```json fences, no prose before or after.
```

---

## Filling the placeholders

- `{{TOPIC}}` — e.g. `Closures`
- `{{ROADMAP}}` — e.g. `python-swe`
- `{{PREREQS}}` — paste the slugs already curated in this roadmap so Gemini reuses them
  instead of inventing new ones, e.g. `functions, scope, first-class-functions, args-kwargs`
