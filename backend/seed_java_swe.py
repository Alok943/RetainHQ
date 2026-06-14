"""
Seed script: Java for SWE roadmap for RetainHQ.
Idempotent — deletes and recreates the roadmap each run.
Run: ./.venv/Scripts/python.exe seed_java_swe.py
"""
import asyncio
import uuid
from sqlalchemy import text
from app.core.database import engine

ROADMAP_ID = uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")
TITLE = "Java for SWE"
DESCRIPTION = "Java from ground up for software engineering interviews and backend roles — OOP, Collections, Concurrency, JVM internals, and placement-critical patterns."

NODES = [
    # ---------------- Step 1: Language Basics ----------------
    ("Step 1: Language Basics", "Fundamentals", "JDK vs JRE vs JVM — how Java runs", "easy"),
    ("Step 1: Language Basics", "Fundamentals", "Data types, variables & type casting", "easy"),
    ("Step 1: Language Basics", "Fundamentals", "Operators, control flow & loops", "easy"),
    ("Step 1: Language Basics", "Fundamentals", "Methods — overloading, varargs & recursion", "easy"),
    ("Step 1: Language Basics", "Fundamentals", "Arrays — 1D, 2D & Arrays utility class", "easy"),
    ("Step 1: Language Basics", "Fundamentals", "Strings — immutability, StringBuilder & common methods", "easy"),

    # ---------------- Step 2: OOP in Java ----------------
    ("Step 2: OOP in Java", "Core OOP", "Classes, objects, constructors & this keyword", "easy"),
    ("Step 2: OOP in Java", "Core OOP", "Inheritance — extends, super & method overriding", "easy"),
    ("Step 2: OOP in Java", "Core OOP", "Abstract classes vs interfaces", "medium"),
    ("Step 2: OOP in Java", "Core OOP", "Polymorphism — compile-time & runtime", "medium"),
    ("Step 2: OOP in Java", "Core OOP", "static, final & access modifiers", "easy"),
    ("Step 2: OOP in Java", "Core OOP", "Inner classes & anonymous classes", "medium"),
    ("Step 2: OOP in Java", "Core OOP", "Enums & records (Java 16+)", "easy"),

    # ---------------- Step 3: Collections Framework ----------------
    ("Step 3: Collections Framework", "Interfaces", "Iterable, Collection, List, Set, Map hierarchy", "medium"),
    ("Step 3: Collections Framework", "Implementations", "ArrayList vs LinkedList — when to use each", "medium"),
    ("Step 3: Collections Framework", "Implementations", "HashMap internals — hashing, buckets, load factor", "hard"),
    ("Step 3: Collections Framework", "Implementations", "LinkedHashMap & TreeMap — ordering guarantees", "medium"),
    ("Step 3: Collections Framework", "Implementations", "HashSet, LinkedHashSet & TreeSet", "medium"),
    ("Step 3: Collections Framework", "Implementations", "PriorityQueue — min/max heap & custom comparator", "medium"),
    ("Step 3: Collections Framework", "Implementations", "ArrayDeque — stack & queue operations", "easy"),
    ("Step 3: Collections Framework", "Utility", "Collections & Arrays utility methods", "easy"),
    ("Step 3: Collections Framework", "Utility", "Comparable vs Comparator", "medium"),

    # ---------------- Step 4: Generics & Functional Java ----------------
    ("Step 4: Generics & Functional Java", "Generics", "Generic classes, methods & bounded wildcards", "medium"),
    ("Step 4: Generics & Functional Java", "Lambdas & Streams", "Lambda expressions & functional interfaces", "medium"),
    ("Step 4: Generics & Functional Java", "Lambdas & Streams", "Stream API — filter, map, reduce, collect", "medium"),
    ("Step 4: Generics & Functional Java", "Lambdas & Streams", "Optional — avoid NullPointerException", "medium"),
    ("Step 4: Generics & Functional Java", "Lambdas & Streams", "Method references & common functional interfaces", "medium"),

    # ---------------- Step 5: Exception Handling & I/O ----------------
    ("Step 5: Exception Handling & I/O", "Exceptions", "Checked vs unchecked exceptions", "easy"),
    ("Step 5: Exception Handling & I/O", "Exceptions", "try-catch-finally & try-with-resources", "easy"),
    ("Step 5: Exception Handling & I/O", "Exceptions", "Custom exceptions & exception chaining", "medium"),
    ("Step 5: Exception Handling & I/O", "I/O", "BufferedReader/Writer for fast competitive I/O", "easy"),
    ("Step 5: Exception Handling & I/O", "I/O", "File I/O & NIO.2 basics", "medium"),

    # ---------------- Step 6: Concurrency ----------------
    ("Step 6: Concurrency", "Threads", "Thread lifecycle — create via Thread & Runnable", "medium"),
    ("Step 6: Concurrency", "Threads", "synchronized, volatile & memory visibility", "hard"),
    ("Step 6: Concurrency", "Threads", "wait / notify & producer-consumer pattern", "hard"),
    ("Step 6: Concurrency", "ExecutorService", "ThreadPoolExecutor & Executors factory", "medium"),
    ("Step 6: Concurrency", "ExecutorService", "Future, Callable & CompletableFuture", "hard"),
    ("Step 6: Concurrency", "Concurrency Utils", "Lock, ReentrantLock & ReadWriteLock", "hard"),
    ("Step 6: Concurrency", "Concurrency Utils", "ConcurrentHashMap, CopyOnWriteArrayList", "medium"),
    ("Step 6: Concurrency", "Concurrency Utils", "Deadlock — detection, prevention & avoidance", "hard"),

    # ---------------- Step 7: JVM Internals ----------------
    ("Step 7: JVM Internals", "Memory", "Heap vs Stack vs Metaspace", "medium"),
    ("Step 7: JVM Internals", "Memory", "Garbage collection — GC roots, mark-sweep, G1 GC", "hard"),
    ("Step 7: JVM Internals", "Memory", "Memory leaks — common causes in Java", "hard"),
    ("Step 7: JVM Internals", "Performance", "JIT compilation & HotSpot basics", "hard"),
    ("Step 7: JVM Internals", "Performance", "Profiling with jstack, jmap & VisualVM", "hard"),

    # ---------------- Step 8: Interview & Placement Patterns ----------------
    ("Step 8: Interview Patterns", "Coding", "DSA in Java — idiomatic patterns (PQ, maps, deque)", "medium"),
    ("Step 8: Interview Patterns", "Coding", "String manipulation interview problems", "medium"),
    ("Step 8: Interview Patterns", "Design", "Implement LRU cache in Java", "hard"),
    ("Step 8: Interview Patterns", "Design", "Thread-safe singleton & double-checked locking", "hard"),
    ("Step 8: Interview Patterns", "Design", "Producer-consumer with BlockingQueue", "hard"),
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
            text("INSERT INTO roadmaps (id, title, description, created_at) VALUES (:id, :title, :desc, now())"),
            {"id": str(ROADMAP_ID), "title": TITLE, "desc": DESCRIPTION},
        )
        for i, (phase, section, title, tier) in enumerate(NODES):
            await conn.execute(
                text("INSERT INTO roadmap_nodes (id, roadmap_id, phase, section, title, tier, order_index) "
                     "VALUES (:id, :rid, :phase, :section, :title, :tier, :idx)"),
                {"id": str(uuid.uuid4()), "rid": str(ROADMAP_ID), "phase": phase,
                 "section": section, "title": title, "tier": tier, "idx": i},
            )
    print(f"Seeded '{TITLE}' with {len(NODES)} nodes.")


if __name__ == "__main__":
    asyncio.run(main())
