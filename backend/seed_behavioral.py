"""
Seed script: Behavioral + HR Interview roadmap for RetainHQ.
Idempotent — deletes and recreates the roadmap each run.
Run: ./.venv/Scripts/python.exe seed_behavioral.py
"""
import asyncio
import uuid
from sqlalchemy import text
from app.core.database import engine

ROADMAP_ID = uuid.UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee")
TITLE = "Behavioral + HR Interview"
DESCRIPTION = "STAR stories, culture-fit questions, salary negotiation, and the non-technical side of cracking any interview — SWE, product, or data roles."

# (phase, section, title, tier)
NODES = [
    # ---------------- Step 1: Foundations ----------------
    ("Step 1: Foundations", "Mindset & Method", "Why behavioral rounds matter & how they're scored", "easy"),
    ("Step 1: Foundations", "Mindset & Method", "The STAR method — Situation, Task, Action, Result", "easy"),
    ("Step 1: Foundations", "Mindset & Method", "Building your story bank — 8 versatile stories", "medium"),
    ("Step 1: Foundations", "Mindset & Method", "Quantify everything — impact over activity", "easy"),
    ("Step 1: Foundations", "Mindset & Method", "Anti-patterns: rambling, vague, negative stories", "easy"),

    # ---------------- Step 2: Core Questions ----------------
    ("Step 2: Core Questions", "Must-Know", "Tell me about yourself — 90-second pitch", "easy"),
    ("Step 2: Core Questions", "Must-Know", "Why this company / why this role?", "easy"),
    ("Step 2: Core Questions", "Must-Know", "Strengths — pick ones that are evidenced, not generic", "easy"),
    ("Step 2: Core Questions", "Must-Know", "Weaknesses — real ones + what you're doing about them", "medium"),
    ("Step 2: Core Questions", "Must-Know", "Where do you see yourself in 5 years?", "easy"),
    ("Step 2: Core Questions", "Must-Know", "Tell me about a failure / mistake", "medium"),
    ("Step 2: Core Questions", "Must-Know", "Tell me about a time you handled conflict", "medium"),

    # ---------------- Step 3: Leadership & Impact ----------------
    ("Step 3: Leadership & Impact", "Stories", "Led a project or initiative (with or without authority)", "medium"),
    ("Step 3: Leadership & Impact", "Stories", "Influenced without authority — got buy-in", "medium"),
    ("Step 3: Leadership & Impact", "Stories", "Mentored or helped a teammate grow", "easy"),
    ("Step 3: Leadership & Impact", "Stories", "Took ownership beyond your role", "medium"),
    ("Step 3: Leadership & Impact", "Stories", "Made a decision under uncertainty / ambiguity", "medium"),
    ("Step 3: Leadership & Impact", "Stories", "Dealt with a difficult stakeholder or manager", "hard"),

    # ---------------- Step 4: Problem-Solving & Execution ----------------
    ("Step 4: Problem-Solving & Execution", "Stories", "Most challenging technical problem you solved", "medium"),
    ("Step 4: Problem-Solving & Execution", "Stories", "Shipped something under a tight deadline", "medium"),
    ("Step 4: Problem-Solving & Execution", "Stories", "Prioritised when everything was P0", "medium"),
    ("Step 4: Problem-Solving & Execution", "Stories", "Pushed back on requirements — and were right", "hard"),
    ("Step 4: Problem-Solving & Execution", "Stories", "Learned a new skill fast to solve a problem", "easy"),
    ("Step 4: Problem-Solving & Execution", "Stories", "Data-driven decision — how you used data to change direction", "medium"),

    # ---------------- Step 5: Teamwork & Culture Fit ----------------
    ("Step 5: Teamwork & Culture Fit", "Stories", "Best team you worked on — what made it great", "easy"),
    ("Step 5: Teamwork & Culture Fit", "Stories", "Disagreed with the team — how you handled it", "medium"),
    ("Step 5: Teamwork & Culture Fit", "Stories", "Gave difficult feedback to a peer", "hard"),
    ("Step 5: Teamwork & Culture Fit", "Stories", "Adapted your communication for a different audience", "medium"),
    ("Step 5: Teamwork & Culture Fit", "Research", "Research company values & match your stories to them", "medium"),
    ("Step 5: Teamwork & Culture Fit", "Research", "Amazon Leadership Principles deep-dive (if applying there)", "medium"),

    # ---------------- Step 6: Questions to Ask ----------------
    ("Step 6: Questions to Ask", "Strategy", "Why your questions matter (it's an eval signal)", "easy"),
    ("Step 6: Questions to Ask", "Strategy", "Questions about the team & day-to-day work", "easy"),
    ("Step 6: Questions to Ask", "Strategy", "Questions about growth, feedback & promotion", "easy"),
    ("Step 6: Questions to Ask", "Strategy", "Questions that reveal company health / red flags", "medium"),
    ("Step 6: Questions to Ask", "Strategy", "Questions to avoid", "easy"),

    # ---------------- Step 7: Offer & Negotiation ----------------
    ("Step 7: Offer & Negotiation", "Negotiation", "Never accept on the spot — always ask for time", "easy"),
    ("Step 7: Offer & Negotiation", "Negotiation", "Research market range — levels.fyi, Glassdoor, blind", "easy"),
    ("Step 7: Offer & Negotiation", "Negotiation", "Negotiate base, stock & signing separately", "medium"),
    ("Step 7: Offer & Negotiation", "Negotiation", "Counter-offer script — word-for-word", "medium"),
    ("Step 7: Offer & Negotiation", "Negotiation", "Competing offers — how to use them ethically", "hard"),
    ("Step 7: Offer & Negotiation", "Negotiation", "Evaluating an offer — comp, growth, team, mission", "medium"),
]


async def main():
    async with engine.begin() as conn:
        await conn.execute(
            text("DELETE FROM roadmap_nodes WHERE roadmap_id = :rid"), {"rid": str(ROADMAP_ID)}
        )
        await conn.execute(
            text("DELETE FROM roadmaps WHERE id = :rid"), {"rid": str(ROADMAP_ID)}
        )

        await conn.execute(
            text("INSERT INTO roadmaps (id, title, description, created_at) "
                 "VALUES (:id, :title, :desc, now())"),
            {"id": str(ROADMAP_ID), "title": TITLE, "desc": DESCRIPTION},
        )

        for i, (phase, section, title, tier) in enumerate(NODES):
            await conn.execute(
                text("INSERT INTO roadmap_nodes "
                     "(id, roadmap_id, phase, section, title, tier, order_index) "
                     "VALUES (:id, :rid, :phase, :section, :title, :tier, :idx)"),
                {
                    "id": str(uuid.uuid4()),
                    "rid": str(ROADMAP_ID),
                    "phase": phase,
                    "section": section,
                    "title": title,
                    "tier": tier,
                    "idx": i,
                },
            )

    print(f"Seeded '{TITLE}' with {len(NODES)} nodes.")


if __name__ == "__main__":
    asyncio.run(main())
