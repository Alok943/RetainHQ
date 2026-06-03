"""
Seed script: System Design as a RetainHQ roadmap.

HLD concepts (+ a short LLD/OOP track) — conceptually rich and excellent SR
material (CAP theorem, caching strategies, consistent hashing). Per the design
doc this is Phase-2 content; curated as crisp, recallable principles plus a few
classic case studies.

Sub-tracks rendered as the step spine via `phase`.
Idempotent. Run: ./.venv/Scripts/python.exe seed_system_design.py
"""
import asyncio
import uuid
from sqlalchemy import text
from app.core.database import engine

ROADMAP_ID = uuid.UUID("77777777-7777-7777-7777-777777777777")
TITLE = "System Design"
DESCRIPTION = "High-level design principles increasingly tested at SDE-1: scaling, storage, communication and reliability — plus LLD/OOP foundations and classic case studies."

# (phase = sub-track, section, title, tier, recall hint)
NODES = [
    ("Fundamentals", "Framing", "Functional vs non-functional requirements", "easy", "What it does vs how well (scale, latency, availability)."),
    ("Fundamentals", "Metrics", "Latency vs throughput", "easy", "Time per request vs requests served per second."),
    ("Fundamentals", "Metrics", "Availability, reliability, consistency", "medium", "Uptime; correctness over time; same data everywhere."),
    ("Fundamentals", "Theory", "CAP theorem", "hard", "Under a partition you choose Consistency or Availability."),
    ("Fundamentals", "Estimation", "Back-of-the-envelope estimation", "medium", "Rough QPS, storage and bandwidth math."),

    ("Scaling", "Scale Out", "Vertical vs horizontal scaling", "easy", "Bigger machine vs more machines."),
    ("Scaling", "Traffic", "Load balancing", "medium", "Distribute traffic; round robin, least connections."),
    ("Scaling", "Services", "Stateless vs stateful services", "medium", "Stateless services scale horizontally with ease."),
    ("Scaling", "Caching", "Caching strategies & CDN", "hard", "Cache-aside, write-through; LRU eviction; CDN at the edge."),
    ("Scaling", "Database", "Database replication", "medium", "Master-slave; read replicas; replication lag."),
    ("Scaling", "Database", "Sharding / partitioning", "hard", "Split data across nodes; choose a good shard key."),

    ("Data Storage", "Choices", "SQL vs NoSQL tradeoffs", "easy", "Relational/ACID vs key-value/document/wide-column."),
    ("Data Storage", "Performance", "Indexing", "medium", "Faster reads via B+ trees; costs writes."),
    ("Data Storage", "Consistency", "ACID vs BASE", "medium", "Strong consistency vs eventual consistency."),
    ("Data Storage", "Distribution", "Consistent hashing", "hard", "Minimise reshuffling when nodes join/leave."),
    ("Data Storage", "Files", "Blob / object storage", "easy", "Large files in S3-like stores, not the database."),

    ("Communication", "APIs", "REST vs RPC vs GraphQL", "medium", "Resource vs procedure vs query-shaped APIs."),
    ("Communication", "Async", "Message queues & async processing", "hard", "Decouple producer/consumer; Kafka, RabbitMQ."),
    ("Communication", "Async", "Pub/sub", "medium", "Publishers -> topics -> many subscribers."),
    ("Communication", "Realtime", "WebSockets vs polling", "medium", "Server push vs repeated client pull."),
    ("Communication", "Edge", "API gateway & rate limiting", "medium", "Single entry point; throttle abusive clients."),

    ("Reliability", "Resilience", "Redundancy & failover", "medium", "Standby replicas; no single point of failure."),
    ("Reliability", "Resilience", "Single point of failure", "easy", "Find and eliminate critical chokepoints."),
    ("Reliability", "Correctness", "Idempotency", "medium", "Same request twice = same effect; safe retries."),
    ("Reliability", "Patterns", "Circuit breaker", "hard", "Stop calling a failing dependency; fail fast."),
    ("Reliability", "Ops", "Monitoring, logging & alerting", "easy", "Metrics, logs, traces; alert on SLOs."),

    ("LLD / OOP", "Foundations", "OOP pillars", "easy", "Encapsulation, abstraction, inheritance, polymorphism."),
    ("LLD / OOP", "Principles", "SOLID principles", "hard", "SRP, OCP, LSP, ISP, DIP."),
    ("LLD / OOP", "Patterns", "Singleton / Factory / Observer / Strategy", "medium", "Reusable solutions to recurring design problems."),
    ("LLD / OOP", "Modelling", "UML class diagram basics", "easy", "Classes, associations, multiplicity."),

    ("Case Studies", "Practice", "Design a URL shortener", "medium", "Base62 hashing, redirect, read-heavy scaling."),
    ("Case Studies", "Practice", "Design a rate limiter", "medium", "Token bucket / sliding window."),
    ("Case Studies", "Practice", "Design a news feed", "hard", "Fan-out on write vs read; ranking."),
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
