# Aptitude lesson generation — PROMPT (Quant)

> **North star:** *"Can the learner explain and solve this 30 days later?"* —
> **Understanding → Recall → Retention**, NOT Memorization → Practice → Forgetting.
> **Retention is an ENGINE problem, not a lesson problem.** So lessons are deliberately **THIN** —
> a sharp intuition + the rule + a trick + recall prompts. The spaced, mixed review queue does the
> retaining. Do NOT write like a coaching site (formula dump → 50 drills). Do NOT pad lessons.

You generate **one JSON per node** for the `aptitude` roadmap, `kind: "aptitude"`. Topics + slugs
are in `content/_TODO-aptitude.md` (Quant). Validate with `python content/validate.py` (aptitude
branch). Write to `content/roadmaps/aptitude/<slug>.json` (filename = slug).

---

## THE THIN TEMPLATE (field order = teaching order)
| # | Field | Required? | What it is |
|---|---|---|---|
| 1 | `hook` | **optional** | A real 2026 Indian-context scene (Swiggy/IPL/Zomato/dev-tasks). Include ONLY if it genuinely lands; skip if forced. |
| 2 | `mental_model` | **REQUIRED** | The one-line intuition every topic gets — even definitional ones. *"log = exponent tracker"; "permutation = arrange, combination = choose"; "work rate = speed."* This is the retention anchor. |
| 3 | `pattern_discovery` | **conditional** | Include ONLY when the rule is genuinely inducible from cases (percentages, successive change, series). OMIT for definitional/derived topics (P&C formula, clocks, log rules, mensuration) — forcing it manufactures fake discovery. `cases` = a list of **short observation STRINGS** (e.g. `"diffs: 3,5,7 → quadratic"`), never objects. |
| 4 | `formula` | **REQUIRED** | The formal rule. After discovery when discovery exists; right after `mental_model` when it doesn't. |
| 5 | `shortcuts` | **REQUIRED, ≥1** | The exam-speed trick vs the textbook way (10% base unit; successive %→one multiplier; time-work→LCM units; alligation cross). |
| 6 | `recall_questions` | **REQUIRED, ≥3** | The rule + applied numbers. tier1 = state it, tier2 = apply it. **These feed the review engine — the actual moat.** |
| 7 | `oa_questions` | **REQUIRED, ≥2** | Real OA-style questions with `company` + `approach` (the 10-second path, not just the answer). |
| — | `common_mistakes` | **REQUIRED, ≥1** | The tempting-but-wrong trap (predict→wrong→explain). |

**No `playground`, no `visual_model` field, no `understanding_checks`. V1 is text + recall.**
Interactive playgrounds are explicitly **deferred to V3** (see `_TODO-aptitude.md` priorities) — do
NOT emit them. A visual belongs *inside* `mental_model.description` as words if it helps, nothing more.

### The law (now conditional, not universal)
When `pattern_discovery` IS present, the **formula must come after it** — the learner discovers the
rule before it's named. When it's absent, lead with `mental_model` → `formula`. Never foreshadow the
formula inside `hook`/`mental_model`.

---

## JSON shape (emit exactly these fields, in order)
```json
{
  "slug": "percentages",
  "title": "Percentages",
  "roadmap": "aptitude",
  "kind": "aptitude",
  "tier": "tier1",
  "metadata": {
    "difficulty": "easy",
    "estimated_minutes": 12,
    "importance": 9,
    "interview_frequency": "high",
    "prerequisites": [],
    "unlocks": ["profit-loss", "interest"],
    "appears_in": ["TCS NQT", "Swiggy DA OA", "Deloitte OA"]
  },
  "hook": {
    "scenario": "Flipkart shows '20% off, then extra 10% off'. Your friend says 'so 30% off'.",
    "question": "Is it 30% off? And does the order of the two discounts matter?"
  },
  "mental_model": {
    "intuition": "A percentage is a multiplier, not an amount.",
    "description": "+20% means ×1.2, −20% means ×0.8. Once you see every % as a multiplier, chains of changes (discounts, interest, growth) become one multiplication — and you stop adding them."
  },
  "pattern_discovery": {
    "setup": "Apply two discounts back to back and watch the total.",
    "cases": [
      "₹100, 20% off then 10% off → ₹72 (not ₹70)",
      "₹100, 10% off then 20% off → ₹72 (same)",
      "₹100, 50% off then 50% off → ₹25 (not ₹0)"
    ],
    "prompt": "Why is it never the simple sum? What is the second % taken OF?",
    "rule": "Each discount applies to what's LEFT, so changes MULTIPLY: 0.8×0.9 = 0.72 → 28% off, never 30%. Order doesn't matter (multiplication commutes)."
  },
  "formula": {
    "statement": "Final = Original × ∏(1 ± rᵢ). Successive a% then b% ⇒ net = a + b + ab/100.",
    "explain": "The single idea behind discounts, SI/CI, growth and depreciation: a % change is a multiplier; chain them by multiplying."
  },
  "shortcuts": [
    { "title": "10% is your base unit", "trick": "Find 10% (move the decimal), then build any %.", "example": "35% of 260 → 26+26+26 + 13 = 91." },
    { "title": "Successive % in one step", "trick": "a% then b% ⇒ net = a + b + ab/100.", "example": "20% then 10% ⇒ −20−10+(200/100)= −28% ⇒ ×0.72." }
  ],
  "common_mistakes": [
    { "title": "Adding successive percentages", "explanation": "20% then 10% is NOT 30% — the second % is of the reduced amount. It's 28%." },
    { "title": "% of the wrong base", "explanation": "Profit% is on COST, discount% is on MARKED price. Same number, different whole." }
  ],
  "recall_questions": [
    { "q": "Is a 20% then 10% discount the same as 30% off?", "answer": "No — 28% (×0.8×0.9=0.72). Successive % multiply, not add.", "tier": "tier1" },
    { "q": "Does the order of two successive discounts change the final price?", "answer": "No — multiplication commutes (0.8×0.9 = 0.9×0.8).", "tier": "tier1" },
    { "q": "Fast: 35% of 260 with the 10% base unit.", "answer": "10%=26 → 30%=78, +5%(13) = 91.", "tier": "tier2" }
  ],
  "oa_questions": [
    { "question": "A shopkeeper marks up 20% then gives 20% discount. Profit or loss %?", "company": "TCS NQT", "answer": "4% loss.", "approach": "×1.2×0.8 = 0.96 ⇒ 4% below cost. Markup base (cost) ≠ discount base (marked), so they don't cancel." }
  ],
  "sources": ["https://www.geeksforgeeks.org/percentages/"]
}
```
*(This example HAS discovery because percentages support it. For `permutations-combinations` or
`geometry`, OMIT `pattern_discovery` and go `mental_model` → `formula`.)*

---

## Mental-model seeds (every topic gets a one-liner — required)
- **Percentages** — "a % is a multiplier, not an amount." Amazon/Swiggy discounts; 10% = base unit.
- **Logarithms** — "log = the exponent tracker" (log₂8 asks 'two to the what is eight?').
- **P&C** — "permutation = arrange (order matters), combination = choose (order doesn't)."
- **Time & Work** — "work rate = speed; add rates, not times."
- **Probability** — "favourable branches ÷ all branches." Cricket/IPL/cards/dice, never red/blue balls.
- **Ratio** — "parts of a recipe; scale all parts together."
- **Data Interpretation** — frame as **"reading a business dashboard"** (Zomato orders, startup
  revenue, IPL/stock charts): extract the insight, don't just compute.
- **Time & Distance** — devs/commutes, not generic trains where avoidable.
- **Geometry** — name the relationship the figure encodes; discovery before the formula where natural.

## Quality bar (self-check before saving)
- Does `mental_model.intuition` make the topic feel **obvious**, not memorized?
- If `pattern_discovery` is present, could a learner **guess the rule** from the cases alone, and is
  the formula genuinely **after** it? If discovery is forced, **delete it**.
- Is the lesson **thin** — no padding, no playground, no invented sections?
- Do `oa_questions[].approach` give the **10-second path**?
- Single quotes + literal numbers in code/formula strings so they nest in JSON.
