"""
Seed the dependency graph (prerequisite edges) for the "Python for SWE" roadmap.

The graph is authored as  title -> [prerequisite titles]  because node UUIDs are
regenerated every time seed_python_swe.py runs; the stable key within a roadmap is
the title. This script resolves titles to the CURRENT node IDs and writes edges to
roadmap_node_prerequisites. It does NOT touch roadmap_nodes, so it never cascades
into user_progress.

Idempotent: clears this roadmap's edges first, then re-inserts.
Run AFTER seed_python_swe.py:
    ./.venv/Scripts/python.exe seed_python_swe_prereqs.py
"""
import asyncio
import uuid
from sqlalchemy import text
from app.core.database import engine

ROADMAP_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")

# node title -> the titles that should be understood BEFORE it.
# Titles must match seed_python_swe.py exactly (verified by _check below).
PREREQS = {
    # --- Functions ---
    "*args and **kwargs": ["Defining functions and return values"],
    "Keyword-only and positional-only parameters": ["Defining functions and return values"],
    "LEGB rule: variable scope in Python": ["Defining functions and return values"],
    "Lambda functions and when to use them": ["Defining functions and return values"],
    "First-class functions: passing and returning functions": ["Defining functions and return values"],

    # --- Mutability / identity ---
    "Shallow copy vs deep copy in Python": ["Mutable vs immutable objects"],
    "Mutable default argument pitfall": ["Mutable vs immutable objects", "Defining functions and return values"],
    "is vs == : identity vs equality": ["Object identity: id() and memory references"],

    # --- Comprehensions ---
    "List comprehensions": ["for and while loops"],
    "Dictionary and set comprehensions": ["List comprehensions"],
    "Nested comprehensions": ["List comprehensions"],
    "Generator expressions vs list comprehensions": ["List comprehensions", "yield keyword and generator functions"],

    # --- Closures (the chain your design doc uses) ---
    "Lexical scope and free variables": ["LEGB rule: variable scope in Python", "First-class functions: passing and returning functions"],
    "Closure mechanics in Python": ["Lexical scope and free variables"],
    "Late binding closures gotcha": ["Closure mechanics in Python"],
    "Stateful functions using closures": ["Closure mechanics in Python"],

    # --- Decorators ---
    "Function decorators": ["Closure mechanics in Python", "First-class functions: passing and returning functions"],
    "functools.wraps and preserving metadata": ["Function decorators"],
    "Decorator factories with arguments": ["Function decorators", "Closure mechanics in Python"],
    "Stacking multiple decorators": ["Function decorators"],
    "Class decorators": ["Function decorators", "Class creation and instantiation"],

    # --- Iterables / iterators / generators ---
    "Iterator protocol and StopIteration": ["Iterable protocol in Python"],
    "Custom iterator class": ["Iterator protocol and StopIteration", "Class creation and instantiation"],
    "yield keyword and generator functions": ["Iterator protocol and StopIteration"],
    "Lazy evaluation and memory efficiency": ["yield keyword and generator functions"],
    "yield from and generator delegation": ["yield keyword and generator functions"],
    "Generator send() for two-way communication": ["yield keyword and generator functions"],

    # --- Dunders ---
    "__iter__ and __next__": ["Iterator protocol and StopIteration"],
    "__call__: making objects callable": ["Class creation and instantiation"],
    "Operator overloading: __add__, __eq__, __lt__": ["Class creation and instantiation"],

    # --- Classes & OOP ---
    "Instance variables vs class variables": ["Class creation and instantiation"],
    "Instance, class, and static methods": ["Class creation and instantiation"],
    "Property decorator: getter, setter, deleter": ["Class creation and instantiation", "Function decorators"],
    "__slots__ for memory optimization": ["Instance variables vs class variables"],
    "Single inheritance and super()": ["Class creation and instantiation"],
    "Multiple inheritance and the diamond problem": ["Single inheritance and super()"],
    "MRO: Method Resolution Order (C3 linearization)": ["Multiple inheritance and the diamond problem"],
    "Method overriding": ["Single inheritance and super()"],
    "Duck typing in Python": ["Method overriding"],
    "Structural subtyping with Protocols": ["Duck typing in Python"],
    "ABC module and abstract methods": ["Single inheritance and super()"],
    "Interface patterns in Python": ["ABC module and abstract methods"],

    # --- SOLID ---
    "Single Responsibility Principle": ["Class creation and instantiation"],
    "Open/Closed Principle": ["Single inheritance and super()"],
    "Liskov Substitution Principle": ["Single inheritance and super()"],
    "Interface Segregation Principle": ["ABC module and abstract methods"],
    "Dependency Inversion Principle": ["ABC module and abstract methods"],

    # --- Type hints ---
    "Optional and Union types": ["Basic annotations: int, str, list, dict"],
    "Generic types: List[T], Dict[K, V]": ["Basic annotations: int, str, list, dict"],
    "TypeVar and generic functions": ["Generic types: List[T], Dict[K, V]"],
    "Protocols for structural typing": ["Generic types: List[T], Dict[K, V]", "Structural subtyping with Protocols"],

    # --- Dataclasses ---
    "field() and default_factory": ["@dataclass basics"],
    "Frozen dataclasses": ["@dataclass basics"],
    "__post_init__ processing": ["@dataclass basics"],
    "Dataclasses vs Pydantic: when to use which": ["@dataclass basics"],

    # --- Context managers ---
    "__enter__ and __exit__": ["with statement and resource management", "Class creation and instantiation"],
    "contextlib.contextmanager decorator": ["with statement and resource management", "Function decorators", "yield keyword and generator functions"],
    "Async context managers": ["__enter__ and __exit__"],
}


async def main():
    async with engine.begin() as conn:
        rows = (
            await conn.execute(
                text("SELECT id, title FROM roadmap_nodes WHERE roadmap_id = :rid"),
                {"rid": str(ROADMAP_ID)},
            )
        ).all()
        id_by_title = {title: nid for nid, title in rows}
        if not id_by_title:
            print("No nodes found. Run seed_python_swe.py first.")
            return

        # Idempotent: clear this roadmap's edges before re-seeding.
        await conn.execute(
            text(
                "DELETE FROM roadmap_node_prerequisites WHERE node_id IN "
                "(SELECT id FROM roadmap_nodes WHERE roadmap_id = :rid)"
            ),
            {"rid": str(ROADMAP_ID)},
        )

        inserted = 0
        missing = set()
        for title, prereq_titles in PREREQS.items():
            nid = id_by_title.get(title)
            if nid is None:
                missing.add(title)
                continue
            for pt in prereq_titles:
                pid = id_by_title.get(pt)
                if pid is None:
                    missing.add(pt)
                    continue
                await conn.execute(
                    text(
                        "INSERT INTO roadmap_node_prerequisites (id, node_id, prerequisite_node_id) "
                        "VALUES (:id, :n, :p) ON CONFLICT (node_id, prerequisite_node_id) DO NOTHING"
                    ),
                    {"id": str(uuid.uuid4()), "n": str(nid), "p": str(pid)},
                )
                inserted += 1

    print(f"Seeded {inserted} prerequisite edges for 'Python for SWE'.")
    if missing:
        print(f"WARNING: {len(missing)} title(s) not found in the roadmap (typo vs seed?):")
        for t in sorted(missing):
            print(f"  - {t}")


if __name__ == "__main__":
    asyncio.run(main())
