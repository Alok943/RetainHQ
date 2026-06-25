# Reasoning + Verbal lesson generation — PROMPT (Aptitude Phase 2)

> **North star (same as quant):** *"Can the learner solve this problem TYPE 30 days later?"*
> Retention is an ENGINE problem — lessons stay **THIN**. The difference from quant: reasoning has
> **no formula and nothing to discover.** It's a repeatable **METHOD** you apply to a problem type
> (blood relations → draw the tree; seating → fix a reference, build a grid; syllogisms → Venn).
> So the lesson = a sharp intuition + the method's steps + **one worked example** showing the method
> in action. Do NOT pad. Do NOT write a coaching-site wall of 20 solved problems.

You generate **one JSON per node** for the `aptitude` roadmap, `kind: "reasoning"` (Logical Reasoning
+ Verbal Ability — Phase 2). Topics + slugs are in `content/_TODO-reasoning.md`. Validate with
`python content/validate.py` (reasoning branch). Write to `content/roadmaps/aptitude/<slug>.json`
(filename = slug). All these lessons live in the **same `aptitude` folder** as the quant lessons —
only the `kind` differs.

---

## THE TEMPLATE (field order = teaching order)
| # | Field | Required? | What it is |
|---|---|---|---|
| 1 | `hook` | **optional** | A real 2026 context (TCS/Infosys reasoning section, an OA puzzle, an interview). Skip if forced. |
| 2 | `mental_model` | **REQUIRED** | The one-line idea that makes the type clickable. *"Blood relations: don't track relations, draw the family tree." "Seating: fix one person, everything else is relative." "Syllogism: draw the Venn, don't argue in words."* |
| 3 | `method` | **REQUIRED, ≥2 steps** | The ordered procedure to attack ANY problem of this type. A list of short step strings. This is the spine — it's what transfers to a new problem. |
| 4 | `worked_example` | **REQUIRED** | ONE concrete problem solved by walking the method step by step. Object: `{ problem, steps[], answer }`. The `steps` mirror the `method` applied to THIS problem. |
| 5 | `shortcuts` | optional | Speed tricks if the type has them (e.g. clocks: angle = |30H − 5.5M|; calendars: odd-days). Omit if none. |
| — | `common_mistakes` | **REQUIRED, ≥1** | The classic trap (assuming gender in blood relations; mixing facing-in/out in circular seating). |
| 6 | `recall_questions` | **REQUIRED, ≥3** | About the METHOD, not trivia. "What's the first thing you draw for a seating problem?" Feeds the review engine. |
| 7 | `oa_questions` | **REQUIRED, ≥2** | Real OA-style problems with `company` + `approach` (which method-steps crack it fast). |

**No `formula`, no `pattern_discovery`, no `playground`, no `understanding_checks`.** The method
REPLACES the formula. The worked_example REPLACES discovery.

---

## JSON shape (emit exactly these fields, in order)
```json
{
  "slug": "blood-relations",
  "title": "Blood Relations",
  "roadmap": "aptitude",
  "kind": "reasoning",
  "tier": "tier1",
  "metadata": {
    "difficulty": "medium",
    "estimated_minutes": 12,
    "importance": 8,
    "interview_frequency": "high",
    "prerequisites": [],
    "unlocks": [],
    "appears_in": ["TCS NQT", "Infosys", "Service-co OA"]
  },
  "hook": {
    "scenario": "Every TCS/Infosys reasoning section throws a 'Pointing to a photo, X said...' puzzle.",
    "question": "Do you solve it in your head and second-guess, or in 15 seconds on paper?"
  },
  "mental_model": {
    "intuition": "Don't track relationships in words — draw the family TREE.",
    "description": "Generations stack top-to-bottom; a couple sits side by side. Once it's a diagram, the answer is just reading the path between two boxes."
  },
  "method": [
    "Spot the two people and the link word (son, sister, maternal uncle, father-in-law).",
    "Anchor the speaker/reference person as a box; draw generations top (elder) to bottom (younger).",
    "Mark gender (+ male, - female) and couples (= ), parent-child with a vertical line.",
    "Read the path between the two target boxes to name the relation."
  ],
  "worked_example": {
    "problem": "Pointing at a man, Riya says: 'He is the son of my grandfather's only son.' How is the man related to Riya?",
    "steps": [
      "'Grandfather's only son' = Riya's father (he's the single son).",
      "The man is the son of Riya's father.",
      "Son of Riya's father = Riya's brother."
    ],
    "answer": "He is Riya's brother."
  },
  "common_mistakes": [
    { "title": "Assuming gender from the name", "explanation": "'The son of X's child' — the child's gender may be unstated. Only use gender the puzzle gives you." },
    { "title": "Reading words instead of drawing", "explanation": "Chains like 'father-in-law of the brother of...' are unsolvable in the head. Draw the tree; the error rate drops to near zero." }
  ],
  "recall_questions": [
    { "q": "First move on any blood-relations puzzle?", "answer": "Draw the family tree — anchor the reference person and stack generations top to bottom.", "tier": "tier1" },
    { "q": "How do you handle 'my grandfather's only son'?", "answer": "'Only son' of the grandfather = the speaker's father (collapse it to one box).", "tier": "tier2" },
    { "q": "Why is solving these in your head error-prone?", "answer": "Multi-hop relations exceed working memory; the diagram externalizes them so you just read a path.", "tier": "tier1" }
  ],
  "oa_questions": [
    { "question": "A is B's sister. C is B's mother. D is C's father. How is A related to D?", "company": "Service-co OA", "answer": "Granddaughter.", "approach": "Tree: D -> C -> (A, B). A is female (sister) and two generations below D = granddaughter." }
  ],
  "sources": ["https://www.indiabix.com/logical-reasoning/blood-relation-test/"]
}
```

---

## Topic notes
- **Logical Reasoning** (syllogisms, seating, puzzles, direction, coding-decoding, clocks-calendars,
  series-reasoning, assumptions-conclusions, data-sufficiency) — pure method + worked example. The
  method is the product; make it transferable.
- **Verbal-strategy** (reading-comprehension, sentence-correction, error-spotting, para-jumbles,
  critical-reasoning) — `method` = the reading/attack strategy; `worked_example` = applying it to one
  passage/sentence. Keep passages short.
- **Vocabulary** (synonyms-antonyms, idioms-phrases, fill-in-the-blanks) — these are recall-heavy.
  `method` = the *learning* strategy (group by root/prefix; learn in context, not lists);
  `worked_example` = decoding one word from its root in context; lean on `recall_questions` as the
  actual payload (these will become the strongest review cards once the engine bridge lands).

## Quality bar
- Could a learner apply the `method` to a DIFFERENT problem of this type? If it only fits the worked
  example, it's not a method — generalize it.
- Do `worked_example.steps` visibly follow the `method` order?
- Are `recall_questions` about the METHOD (transferable), not one-off trivia?
- `company` tags = honest exam CATEGORIES (TCS NQT / AMCAT-style / service-co OA), never a fabricated
  "X company asked this exact question."
- Single quotes + literal characters in strings so they nest in JSON.
