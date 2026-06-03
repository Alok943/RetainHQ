"""
Seed script: Aptitude as a RetainHQ roadmap (one roadmap, three sub-tracks).

Sub-tracks (rendered as the flowchart's step spine via `phase`):
  Quantitative Aptitude · Logical Reasoning · Verbal Ability

The filter for most on-campus mass-recruiter offers (TCS, Wipro, Cognizant).
Each node has a short recall hint in `description`.

Idempotent — deletes and recreates this roadmap each run.
Run: ./.venv/Scripts/python.exe seed_aptitude.py
"""
import asyncio
import uuid
from sqlalchemy import text
from app.core.database import engine

ROADMAP_ID = uuid.UUID("55555555-5555-5555-5555-555555555555")
TITLE = "Aptitude — Quant, Reasoning & Verbal"
DESCRIPTION = "The aptitude filter that gates 60%+ of on-campus offers. Quant, logical reasoning and verbal — short, high-frequency topics ideal for spaced practice."

# (phase = sub-track, section, title, tier, recall hint)
NODES = [
    # ================= Quantitative Aptitude =================
    ("Quantitative Aptitude", "Numbers", "Number system & divisibility", "easy", "Factors, multiples, divisibility rules, remainders."),
    ("Quantitative Aptitude", "Numbers", "HCF & LCM", "easy", "Product of two numbers = HCF × LCM."),
    ("Quantitative Aptitude", "Numbers", "Number & letter series", "medium", "Spot the pattern: AP/GP, squares, primes."),
    ("Quantitative Aptitude", "Arithmetic", "Percentages", "easy", "Fraction↔percent; successive % change."),
    ("Quantitative Aptitude", "Arithmetic", "Profit, loss & discount", "easy", "CP, SP, MP; profit% on CP."),
    ("Quantitative Aptitude", "Arithmetic", "Ratio & proportion", "easy", "Compound ratio; direct/inverse proportion."),
    ("Quantitative Aptitude", "Arithmetic", "Averages", "easy", "Sum / count; weighted average."),
    ("Quantitative Aptitude", "Arithmetic", "Problems on ages", "medium", "Set up linear equations from age relations."),
    ("Quantitative Aptitude", "Arithmetic", "Mixtures & alligation", "medium", "Alligation rule for ratio of quantities."),
    ("Quantitative Aptitude", "Arithmetic", "Simple & compound interest", "medium", "SI = PRT/100; CI compounds the principal."),
    ("Quantitative Aptitude", "Time & Distance", "Time & work", "medium", "Work rate = 1/time; LCM-of-days method."),
    ("Quantitative Aptitude", "Time & Distance", "Pipes & cisterns", "medium", "Same as time & work; outlets are negative."),
    ("Quantitative Aptitude", "Time & Distance", "Time, speed & distance", "medium", "Speed = distance/time; unit conversions."),
    ("Quantitative Aptitude", "Time & Distance", "Trains, boats & streams", "medium", "Relative speed; upstream/downstream."),
    ("Quantitative Aptitude", "Advanced", "Permutations & combinations", "hard", "nPr arranges, nCr selects."),
    ("Quantitative Aptitude", "Advanced", "Probability", "hard", "Favourable / total; addition & multiplication rules."),
    ("Quantitative Aptitude", "Advanced", "Mensuration", "medium", "Area, perimeter, surface area & volume formulas."),

    # ================= Logical Reasoning =================
    ("Logical Reasoning", "Verbal Reasoning", "Syllogisms", "medium", "Venn diagrams; all / some / no statements."),
    ("Logical Reasoning", "Verbal Reasoning", "Blood relations", "medium", "Draw a family tree; track generations."),
    ("Logical Reasoning", "Verbal Reasoning", "Coding–decoding", "easy", "Letter↔number shifts and substitutions."),
    ("Logical Reasoning", "Verbal Reasoning", "Analogy & classification", "easy", "Find the relationship / odd one out."),
    ("Logical Reasoning", "Verbal Reasoning", "Direction sense", "easy", "Track turns; net displacement."),
    ("Logical Reasoning", "Arrangements", "Linear & circular seating", "hard", "Fix one reference; facing in/out for circular."),
    ("Logical Reasoning", "Arrangements", "Puzzles (floors / boxes / scheduling)", "hard", "Build a grid; eliminate from clues."),
    ("Logical Reasoning", "Arrangements", "Clocks & calendars", "medium", "Angle = |30H − 5.5M|; odd days for calendars."),
    ("Logical Reasoning", "Analytical", "Number & letter series", "easy", "Difference / ratio pattern."),
    ("Logical Reasoning", "Analytical", "Statements: assumptions & conclusions", "medium", "What must be true vs what is implied."),
    ("Logical Reasoning", "Analytical", "Data sufficiency", "medium", "Is each statement alone / together enough?"),

    # ================= Verbal Ability =================
    ("Verbal Ability", "Reading & Grammar", "Reading comprehension", "medium", "Main idea, tone, inference, vocab in context."),
    ("Verbal Ability", "Reading & Grammar", "Sentence correction & grammar", "medium", "Subject–verb agreement, tenses, modifiers."),
    ("Verbal Ability", "Reading & Grammar", "Error spotting", "medium", "Find the grammatically wrong segment."),
    ("Verbal Ability", "Reading & Grammar", "Para jumbles", "medium", "Find opener; link pronouns & connectors."),
    ("Verbal Ability", "Vocabulary", "Synonyms & antonyms", "easy", "Build word lists; roots & prefixes."),
    ("Verbal Ability", "Vocabulary", "Idioms & phrases", "easy", "Learn common idiomatic meanings."),
    ("Verbal Ability", "Vocabulary", "Fill in the blanks", "easy", "Context + collocation + grammar."),
    ("Verbal Ability", "Reasoning", "Critical reasoning", "hard", "Assumption, strengthen/weaken, conclusion."),
]


async def main():
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM roadmap_nodes WHERE roadmap_id = :rid"), {"rid": str(ROADMAP_ID)})
        await conn.execute(text("DELETE FROM roadmaps WHERE id = :rid"), {"rid": str(ROADMAP_ID)})
        await conn.execute(
            text("INSERT INTO roadmaps (id, title, description, created_at) VALUES (:id, :title, :desc, now())"),
            {"id": str(ROADMAP_ID), "title": TITLE, "desc": DESCRIPTION},
        )
        for i, (phase, section, title, tier, desc) in enumerate(NODES):
            await conn.execute(
                text("INSERT INTO roadmap_nodes "
                     "(id, roadmap_id, phase, section, title, tier, order_index, description) "
                     "VALUES (:id, :rid, :phase, :section, :title, :tier, :idx, :desc)"),
                {"id": str(uuid.uuid4()), "rid": str(ROADMAP_ID), "phase": phase,
                 "section": section, "title": title, "tier": tier, "idx": i, "desc": desc},
            )
    print(f"Seeded '{TITLE}' with {len(NODES)} nodes.")


if __name__ == "__main__":
    asyncio.run(main())
