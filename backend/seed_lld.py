"""
Seed script: Low-Level Design (LLD / OOD) roadmap for RetainHQ.
Idempotent — deletes and recreates the roadmap each run.
Run: ./.venv/Scripts/python.exe seed_lld.py
"""
import asyncio
import uuid
from sqlalchemy import text
from app.core.database import engine

ROADMAP_ID = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
TITLE = "Low-Level Design (LLD / OOD)"
DESCRIPTION = "From OOP fundamentals through SOLID, design patterns, and classic interview LLD problems (Parking Lot, Splitwise, Chess). Pairs with the System Design (HLD) roadmap."

# (phase, section, title, tier)
NODES = [
    # ---------------- Step 1: OOP Fundamentals ----------------
    ("Step 1: OOP Fundamentals", "Four Pillars", "Encapsulation — classes, access modifiers", "easy"),
    ("Step 1: OOP Fundamentals", "Four Pillars", "Abstraction — abstract classes & interfaces", "easy"),
    ("Step 1: OOP Fundamentals", "Four Pillars", "Inheritance — IS-A vs HAS-A", "easy"),
    ("Step 1: OOP Fundamentals", "Four Pillars", "Polymorphism — overloading & overriding", "easy"),
    ("Step 1: OOP Fundamentals", "Relationships", "Association, Aggregation & Composition", "medium"),
    ("Step 1: OOP Fundamentals", "Relationships", "Dependency Injection basics", "medium"),

    # ---------------- Step 2: SOLID Principles ----------------
    ("Step 2: SOLID Principles", "Principles", "S — Single Responsibility Principle", "easy"),
    ("Step 2: SOLID Principles", "Principles", "O — Open/Closed Principle", "medium"),
    ("Step 2: SOLID Principles", "Principles", "L — Liskov Substitution Principle", "medium"),
    ("Step 2: SOLID Principles", "Principles", "I — Interface Segregation Principle", "medium"),
    ("Step 2: SOLID Principles", "Principles", "D — Dependency Inversion Principle", "medium"),
    ("Step 2: SOLID Principles", "Principles", "SOLID violations — spotting & fixing", "hard"),

    # ---------------- Step 3: Creational Design Patterns ----------------
    ("Step 3: Design Patterns — Creational", "Patterns", "Singleton — thread-safe implementation", "easy"),
    ("Step 3: Design Patterns — Creational", "Patterns", "Factory Method & Abstract Factory", "medium"),
    ("Step 3: Design Patterns — Creational", "Patterns", "Builder pattern", "medium"),
    ("Step 3: Design Patterns — Creational", "Patterns", "Prototype pattern", "easy"),

    # ---------------- Step 4: Structural Design Patterns ----------------
    ("Step 4: Design Patterns — Structural", "Patterns", "Adapter — bridge incompatible interfaces", "medium"),
    ("Step 4: Design Patterns — Structural", "Patterns", "Decorator — add behaviour at runtime", "medium"),
    ("Step 4: Design Patterns — Structural", "Patterns", "Facade — simplify a subsystem", "easy"),
    ("Step 4: Design Patterns — Structural", "Patterns", "Proxy — access control & lazy loading", "medium"),
    ("Step 4: Design Patterns — Structural", "Patterns", "Composite — tree structures", "medium"),

    # ---------------- Step 5: Behavioural Design Patterns ----------------
    ("Step 5: Design Patterns — Behavioural", "Patterns", "Observer / Pub-Sub pattern", "medium"),
    ("Step 5: Design Patterns — Behavioural", "Patterns", "Strategy — swap algorithms at runtime", "medium"),
    ("Step 5: Design Patterns — Behavioural", "Patterns", "Command — encapsulate requests", "medium"),
    ("Step 5: Design Patterns — Behavioural", "Patterns", "Iterator pattern", "easy"),
    ("Step 5: Design Patterns — Behavioural", "Patterns", "State machine pattern", "hard"),
    ("Step 5: Design Patterns — Behavioural", "Patterns", "Template Method pattern", "medium"),

    # ---------------- Step 6: UML & Diagramming ----------------
    ("Step 6: UML & Diagramming", "Diagrams", "Class diagram — notation & relationships", "easy"),
    ("Step 6: UML & Diagramming", "Diagrams", "Sequence diagram — object interaction", "medium"),
    ("Step 6: UML & Diagramming", "Diagrams", "Use-case diagram & requirements mapping", "easy"),
    ("Step 6: UML & Diagramming", "Diagrams", "Read any LLD diagram in an interview", "medium"),

    # ---------------- Step 7: Classic LLD Interview Problems ----------------
    ("Step 7: Classic LLD Problems", "Easy–Medium", "Design a Parking Lot", "medium"),
    ("Step 7: Classic LLD Problems", "Easy–Medium", "Design a Library Management System", "medium"),
    ("Step 7: Classic LLD Problems", "Easy–Medium", "Design a Vending Machine", "medium"),
    ("Step 7: Classic LLD Problems", "Easy–Medium", "Design an ATM", "medium"),
    ("Step 7: Classic LLD Problems", "Easy–Medium", "Design a Logging Framework", "medium"),
    ("Step 7: Classic LLD Problems", "Medium–Hard", "Design Splitwise (expense sharing)", "hard"),
    ("Step 7: Classic LLD Problems", "Medium–Hard", "Design a Hotel Booking System", "hard"),
    ("Step 7: Classic LLD Problems", "Medium–Hard", "Design an Elevator System", "hard"),
    ("Step 7: Classic LLD Problems", "Medium–Hard", "Design Snake & Ladder / Chess", "hard"),
    ("Step 7: Classic LLD Problems", "Medium–Hard", "Design a Ride-Sharing App (Uber/Ola)", "hard"),

    # ---------------- Step 8: Interview Strategy ----------------
    ("Step 8: Interview Strategy", "Approach", "LLD interview framework — 4-step approach", "easy"),
    ("Step 8: Interview Strategy", "Approach", "Clarify requirements & identify actors/entities", "easy"),
    ("Step 8: Interview Strategy", "Approach", "Walk through design & justify pattern choices", "medium"),
    ("Step 8: Interview Strategy", "Approach", "Extensibility & edge-case discussion", "medium"),
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
