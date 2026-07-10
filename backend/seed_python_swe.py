"""
Seed script: Python for SWE roadmap (comprehensive, 6-phase).

Fundamentals → Internals → OOP & Design → Professional Python →
Testing & Quality → Engineering Practices. Topic names are deliberately
specific so each is directly searchable.

Idempotent. Run: ./.venv/Scripts/python.exe seed_python_swe.py
"""
import asyncio
import uuid
from sqlalchemy import text
from app.core.database import engine

ROADMAP_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
TITLE = "Python for SWE"
SLUG = "python-swe"  # URL identifier; matches the content/ folder key
DESCRIPTION = "A comprehensive Python path for software engineers: fundamentals, language internals, OOP & design, professional tooling, testing, and engineering practices."

P1 = "Phase 1 — Python Fundamentals"
P2 = "Phase 2 — Python Internals"
P2H = "Phase 2.5 — Concurrency & Async"
P3 = "Phase 3 — OOP & Design"
P4 = "Phase 4 — Professional Python"
P5 = "Phase 5 — Testing & Quality"
P6 = "Phase 6 — Engineering Practices"

# (phase, section, title, tier)
NODES = [
    # ---------------- Phase 1 — Python Fundamentals ----------------
    (P1, "Variables & Types", "Primitive types: int, float, bool, str", "easy"),
    (P1, "Variables & Types", "Dynamic typing and type()", "easy"),
    (P1, "Variables & Types", "Mutable vs immutable objects", "medium"),
    (P1, "Variables & Types", "Object identity: id() and memory references", "medium"),
    (P1, "Variables & Types", "Type conversion: implicit vs explicit casting", "easy"),
    (P1, "Variables & Types", "Mutable default argument pitfall", "medium"),
    (P1, "Control Flow", "if/elif/else and Python truthiness", "easy"),
    (P1, "Control Flow", "match-case statement", "easy"),
    (P1, "Control Flow", "for and while loops", "easy"),
    (P1, "Control Flow", "break, continue, loop else clause", "medium"),
    (P1, "Control Flow", "Ternary expressions", "easy"),
    (P1, "Functions", "Defining functions and return values", "easy"),
    (P1, "Functions", "*args and **kwargs", "medium"),
    (P1, "Functions", "Keyword-only and positional-only parameters", "medium"),
    (P1, "Functions", "LEGB rule: variable scope in Python", "medium"),
    (P1, "Functions", "Lambda functions and when to use them", "easy"),
    (P1, "Functions", "First-class functions: passing and returning functions", "medium"),
    (P1, "Collections", "Lists: indexing, slicing, methods", "easy"),
    (P1, "Collections", "Tuples: immutability and use cases", "easy"),
    (P1, "Collections", "Dictionaries: operations and use cases", "easy"),
    (P1, "Collections", "Sets: operations and use cases", "easy"),
    (P1, "Collections", "Time Complexity of Collection Operations", "medium"),
    (P1, "Collections", "Shallow copy vs deep copy in Python", "medium"),
    (P1, "Comprehensions", "List comprehensions", "easy"),
    (P1, "Comprehensions", "Dictionary and set comprehensions", "easy"),
    (P1, "Comprehensions", "Nested comprehensions", "medium"),
    (P1, "Comprehensions", "Generator expressions vs list comprehensions", "medium"),
    (P1, "Error Handling", "try/except with specific exception types", "easy"),
    (P1, "Error Handling", "else and finally blocks", "easy"),
    (P1, "Error Handling", "Raising exceptions with raise", "easy"),
    (P1, "Error Handling", "Custom exception classes", "medium"),
    (P1, "Error Handling", "Exception chaining with raise from", "medium"),
    (P1, "File I/O & Serialization", "Reading and writing files with open()", "easy"),
    (P1, "File I/O & Serialization", "pathlib for filesystem paths", "easy"),
    (P1, "File I/O & Serialization", "JSON serialization with the json module", "easy"),
    (P1, "File I/O & Serialization", "CSV files with the csv module", "easy"),
    (P1, "Standard Library Power Tools", "collections.defaultdict", "medium"),
    (P1, "Standard Library Power Tools", "collections.Counter", "easy"),
    (P1, "Standard Library Power Tools", "collections.deque", "medium"),
    (P1, "Standard Library Power Tools", "itertools essentials", "medium"),
    (P1, "Standard Library Power Tools", "functools: lru_cache, partial, reduce", "medium"),
    (P1, "Standard Library Power Tools", "Regular expressions with re", "medium"),

    # ---------------- Phase 2 — Python Internals ----------------
    (P2, "Object Model", "Everything is an object in Python", "medium"),
    (P2, "Object Model", "is vs == : Identity vs Equality", "medium"),
    (P2, "Object Model", "Reference Counting in CPython", "medium"),
    (P2, "Object Model", "Garbage Collection and Cyclic References", "medium"),
    (P2, "Object Model", "Integer and String Interning", "hard"),
    (P2, "Dunder Methods", "__init__ and __new__", "medium"),
    (P2, "Dunder Methods", "__str__ vs __repr__", "easy"),
    (P2, "Dunder Methods", "__len__, __getitem__, __setitem__", "medium"),
    (P2, "Dunder Methods", "__iter__ and __next__", "medium"),
    (P2, "Dunder Methods", "__call__: Making Objects Callable", "medium"),
    (P2, "Dunder Methods", "Operator Overloading: __add__, __eq__, __lt__", "medium"),
    (P2, "Iterables & Iterators", "Iterable protocol in Python", "medium"),
    (P2, "Iterables & Iterators", "Iterator Protocol and StopIteration", "medium"),
    (P2, "Iterables & Iterators", "Custom Iterator Class", "medium"),
    (P2, "Iterables & Iterators", "iter() and next() builtins", "easy"),
    (P2, "Generators", "yield keyword and generator functions", "medium"),
    (P2, "Generators", "Lazy Evaluation and Memory Efficiency", "medium"),
    (P2, "Generators", "yield from and generator delegation", "hard"),
    (P2, "Generators", "Generator send() for Two-Way Communication", "hard"),
    (P2, "Closures", "Lexical Scope and Free Variables", "medium"),
    (P2, "Closures", "Closure mechanics in Python", "medium"),
    (P2, "Closures", "Late Binding Closures Gotcha", "hard"),
    (P2, "Closures", "Stateful Functions Using Closures", "medium"),
    (P2, "Decorators", "Function Decorators", "medium"),
    (P2, "Decorators", "functools.wraps and preserving metadata", "medium"),
    (P2, "Decorators", "Decorator Factories with Arguments", "hard"),
    (P2, "Decorators", "Stacking Multiple Decorators", "medium"),
    (P2, "Decorators", "Class decorators", "hard"),

    # ---------------- Phase 2.5 — Concurrency & Async ----------------
    (P2H, "Concurrency Model", "Concurrency vs Parallelism", "easy"),
    (P2H, "Concurrency Model", "The GIL (Global Interpreter Lock)", "medium"),
    (P2H, "Threads & Processes", "Threading for I/O-bound work", "medium"),
    (P2H, "Threads & Processes", "Threading vs Multiprocessing", "hard"),
    (P2H, "Threads & Processes", "Multiprocessing for CPU-bound work", "medium"),
    (P2H, "asyncio", "asyncio and the event loop", "medium"),
    (P2H, "asyncio", "Coroutines, async / await", "medium"),
    (P2H, "asyncio", "When async actually helps", "medium"),

    # ---------------- Phase 3 — OOP & Design ----------------
    (P3, "Classes & Objects", "Class Creation and Instantiation", "easy"),
    (P3, "Classes & Objects", "Instance variables vs class variables", "medium"),
    (P3, "Classes & Objects", "Instance, Class, and Static Methods", "medium"),
    (P3, "Classes & Objects", "Property decorator: getter, setter, deleter", "medium"),
    (P3, "Classes & Objects", "__slots__ for Memory Optimization", "hard"),
    (P3, "Inheritance", "Single inheritance and super()", "easy"),
    (P3, "Inheritance", "Multiple inheritance and the diamond problem", "hard"),
    (P3, "Inheritance", "MRO: Method Resolution Order (C3 linearization)", "hard"),
    (P3, "Polymorphism", "Method overriding", "easy"),
    (P3, "Polymorphism", "Duck typing in Python", "medium"),
    (P3, "Polymorphism", "Structural Subtyping with Protocols", "medium"),
    (P3, "Abstraction", "ABC Module and Abstract Methods", "medium"),
    (P3, "Abstraction", "Interface patterns in Python", "medium"),
    (P3, "SOLID Principles", "Single Responsibility Principle", "medium"),
    (P3, "SOLID Principles", "Open/Closed Principle", "medium"),
    (P3, "SOLID Principles", "Liskov Substitution Principle", "hard"),
    (P3, "SOLID Principles", "Interface Segregation Principle", "medium"),
    (P3, "SOLID Principles", "Dependency Inversion Principle", "hard"),

    # ---------------- Phase 4 — Professional Python ----------------
    (P4, "Type Hints", "Basic annotations: int, str, list, dict", "easy"),
    (P4, "Type Hints", "Optional and Union Types", "easy"),
    (P4, "Type Hints", "Generic types: List[T], Dict[K, V]", "medium"),
    (P4, "Type Hints", "TypeVar and Generic Functions", "hard"),
    (P4, "Type Hints", "Protocols for Structural Typing", "hard"),
    (P4, "Type Hints", "TYPE_CHECKING for Avoiding Circular Imports", "medium"),
    (P4, "Dataclasses", "@dataclass basics", "easy"),
    (P4, "Dataclasses", "field() and default_factory", "medium"),
    (P4, "Dataclasses", "Frozen Dataclasses", "easy"),
    (P4, "Dataclasses", "__post_init__ Processing", "medium"),
    (P4, "Dataclasses", "Dataclasses vs Pydantic: when to use which", "medium"),
    (P4, "Context Managers", "with statement and resource management", "easy"),
    (P4, "Context Managers", "__enter__ and __exit__", "medium"),
    (P4, "Context Managers", "contextlib.contextmanager decorator", "medium"),
    (P4, "Context Managers", "Async context managers", "medium"),
    (P4, "Logging", "Logging levels and basicConfig", "easy"),
    (P4, "Logging", "Loggers, handlers, formatters", "medium"),
    (P4, "Logging", "Structured logging with JSON output", "medium"),
    (P4, "Logging", "Log Rotation with RotatingFileHandler", "easy"),
    (P4, "Configuration & Deps", "os.environ and Environment Variables", "easy"),
    (P4, "Configuration & Deps", "python-dotenv for .env files", "easy"),
    (P4, "Configuration & Deps", "pyproject.toml and project metadata", "medium"),
    (P4, "Configuration & Deps", "Poetry: dependency management basics", "easy"),

    # ---------------- Phase 5 — Testing & Quality ----------------
    (P5, "pytest", "Test discovery and naming conventions", "easy"),
    (P5, "pytest", "Assertions and pytest.raises", "easy"),
    (P5, "pytest", "Fixtures and fixture scope", "medium"),
    (P5, "pytest", "@pytest.mark.parametrize", "medium"),
    (P5, "pytest", "conftest.py: shared fixtures", "medium"),
    (P5, "Mocking", "unittest.mock: Mock and MagicMock", "medium"),
    (P5, "Mocking", "patch as decorator and context manager", "medium"),
    (P5, "Mocking", "Dependency isolation strategies", "hard"),
    (P5, "Mocking", "Mocking external API calls", "hard"),
    (P5, "Code Quality", "Black: auto-formatting", "easy"),
    (P5, "Code Quality", "Ruff: linting and import sorting", "easy"),
    (P5, "Code Quality", "Mypy: static type checking", "medium"),
    (P5, "Code Quality", "Pre-commit hooks setup", "easy"),
    (P5, "Debugging", "pdb and breakpoint()", "easy"),
    (P5, "Debugging", "Reading stack traces", "easy"),
    (P5, "Debugging", "cProfile for performance profiling", "medium"),

    # ---------------- Phase 6 — Engineering Practices ----------------
    (P6, "Git", "Branching strategies: feature, main, release", "easy"),
    (P6, "Git", "Rebase vs merge", "medium"),
    (P6, "Git", "Pull request workflow", "easy"),
    (P6, "Git", "Conventional commits spec", "easy"),
    (P6, "Project Structure", "Package structure and __init__.py", "easy"),
    (P6, "Project Structure", "Layered architecture", "medium"),
    (P6, "Project Structure", "Service-repository pattern", "medium"),
    (P6, "Project Structure", "Modular design and separation of concerns", "medium"),
    (P6, "Design Patterns", "Singleton pattern", "medium"),
    (P6, "Design Patterns", "Factory pattern", "medium"),
    (P6, "Design Patterns", "Strategy pattern", "medium"),
    (P6, "Design Patterns", "Observer pattern", "medium"),
    (P6, "Design Patterns", "Provider abstraction pattern", "hard"),
]


async def main():
    """Progress-safe, additive upsert.

    Existing nodes are matched CASE-INSENSITIVELY by title and UPDATED in place
    (phase/section/tier/order_index only — never the title), so their id and every
    user_progress row that references it (ON DELETE CASCADE) survive untouched.
    Case-insensitive matching matters because live node titles may be Title-Cased
    while this file is sentence-cased; an exact match would miss them, insert
    duplicates, and orphan the originals.

    This seed NEVER DELETES a node — it only inserts new titles and updates existing
    ones. That guarantees no progress is ever cascaded away. Titles present in the
    DB but absent from NODES are reported, not removed. The roadmap row is upserted,
    never deleted, so we never cascade the whole tree.
    """
    async with engine.begin() as conn:
        await conn.execute(
            text("INSERT INTO roadmaps (id, slug, title, description, created_at) "
                 "VALUES (:id, :slug, :title, :desc, now()) "
                 "ON CONFLICT (id) DO UPDATE SET slug = :slug, title = :title, description = :desc"),
            {"id": str(ROADMAP_ID), "slug": SLUG, "title": TITLE, "desc": DESCRIPTION},
        )
        rows = (await conn.execute(
            text("SELECT id, title FROM roadmap_nodes WHERE roadmap_id = :rid"),
            {"rid": str(ROADMAP_ID)},
        )).fetchall()
        # key by lower(title) so casing differences update in place instead of duplicating
        existing = {r.title.lower(): (r.id, r.title) for r in rows}

        seen, inserted, updated = set(), 0, 0
        for i, (phase, section, title, tier) in enumerate(NODES):
            key = title.lower()
            seen.add(key)
            if key in existing:
                node_id, _db_title = existing[key]
                # Title is refreshed too (seed is authoritative) — safe because the
                # match key is lower(title), so correcting casing never re-keys the row.
                await conn.execute(
                    text("UPDATE roadmap_nodes SET title = :title, phase = :phase, "
                         "section = :section, tier = :tier, order_index = :idx WHERE id = :id"),
                    {"title": title, "phase": phase, "section": section, "tier": tier,
                     "idx": i, "id": str(node_id)},
                )
                updated += 1
            else:
                await conn.execute(
                    text("INSERT INTO roadmap_nodes "
                         "(id, roadmap_id, phase, section, title, tier, order_index) "
                         "VALUES (:id, :rid, :phase, :section, :title, :tier, :idx)"),
                    {"id": str(uuid.uuid4()), "rid": str(ROADMAP_ID), "phase": phase,
                     "section": section, "title": title, "tier": tier, "idx": i},
                )
                inserted += 1

        # Report (never delete) titles in the DB that this seed no longer lists.
        orphans = [db_title for key, (_id, db_title) in existing.items() if key not in seen]

    print(f"Seeded '{TITLE}': {len(NODES)} nodes "
          f"({inserted} inserted, {updated} updated, 0 removed).")
    if orphans:
        print(f"NOTE: {len(orphans)} DB node(s) not in this seed, left in place: {orphans}")


if __name__ == "__main__":
    asyncio.run(main())
