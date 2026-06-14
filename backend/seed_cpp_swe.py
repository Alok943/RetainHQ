"""
Seed script: C++ for SWE/CP roadmap for RetainHQ.
Idempotent — deletes and recreates the roadmap each run.
Run: ./.venv/Scripts/python.exe seed_cpp_swe.py
"""
import asyncio
import uuid
from sqlalchemy import text
from app.core.database import engine

ROADMAP_ID = uuid.UUID("10101010-1010-1010-1010-101010101010")
TITLE = "C++ for SWE / CP"
DESCRIPTION = "C++ from core language through STL, memory management, and competitive-programming patterns. Covers both SWE interviews and Codeforces/ICPC-style CP."

NODES = [
    # ---------------- Step 1: Core Language ----------------
    ("Step 1: Core Language", "Basics", "Data types, I/O (cin/cout) & fast I/O tricks", "easy"),
    ("Step 1: Core Language", "Basics", "References vs pointers — syntax & mental model", "medium"),
    ("Step 1: Core Language", "Basics", "Functions — pass by value, reference & pointer", "easy"),
    ("Step 1: Core Language", "Basics", "Arrays, strings & C-style vs std::string", "easy"),
    ("Step 1: Core Language", "Basics", "Preprocessor macros & #define for CP", "easy"),
    ("Step 1: Core Language", "Basics", "auto, range-for & structured bindings (C++17)", "easy"),

    # ---------------- Step 2: OOP in C++ ----------------
    ("Step 2: OOP in C++", "Classes", "Classes, constructors, destructors & this", "medium"),
    ("Step 2: OOP in C++", "Classes", "Operator overloading — common interview cases", "medium"),
    ("Step 2: OOP in C++", "Classes", "Inheritance & virtual functions / vtable", "hard"),
    ("Step 2: OOP in C++", "Classes", "Abstract classes & pure virtual functions", "medium"),
    ("Step 2: OOP in C++", "Classes", "Rule of 3 / 5 / 0 — copy, move, destructor", "hard"),

    # ---------------- Step 3: Memory Management ----------------
    ("Step 3: Memory Management", "Manual Memory", "Stack vs heap — new/delete & memory layout", "medium"),
    ("Step 3: Memory Management", "Manual Memory", "Memory leaks, dangling pointers & double free", "hard"),
    ("Step 3: Memory Management", "Smart Pointers", "unique_ptr, shared_ptr & weak_ptr", "hard"),
    ("Step 3: Memory Management", "Smart Pointers", "RAII — resource acquisition is initialization", "medium"),

    # ---------------- Step 4: STL ----------------
    ("Step 4: STL", "Sequence Containers", "vector — internals, push_back amortization", "easy"),
    ("Step 4: STL", "Sequence Containers", "deque, list & array", "easy"),
    ("Step 4: STL", "Associative Containers", "map & set — red-black tree, O(log n) ops", "medium"),
    ("Step 4: STL", "Associative Containers", "unordered_map & unordered_set — hash internals", "medium"),
    ("Step 4: STL", "Associative Containers", "multimap, multiset & priority_queue", "medium"),
    ("Step 4: STL", "Algorithms", "sort, binary_search, lower_bound & upper_bound", "easy"),
    ("Step 4: STL", "Algorithms", "next_permutation, rotate & reverse", "easy"),
    ("Step 4: STL", "Algorithms", "Custom comparators with lambda for sort/PQ", "medium"),
    ("Step 4: STL", "Algorithms", "accumulate, transform & common <algorithm> patterns", "medium"),

    # ---------------- Step 5: Modern C++ (11/14/17) ----------------
    ("Step 5: Modern C++", "Features", "Lambda expressions & closures", "medium"),
    ("Step 5: Modern C++", "Features", "Move semantics & rvalue references", "hard"),
    ("Step 5: Modern C++", "Features", "Templates — function & class templates", "hard"),
    ("Step 5: Modern C++", "Features", "constexpr & compile-time computation", "hard"),
    ("Step 5: Modern C++", "Features", "std::optional, std::variant & std::any", "medium"),

    # ---------------- Step 6: Competitive Programming Patterns ----------------
    ("Step 6: CP Patterns", "Fast I/O & Setup", "CP template — fast I/O, macros & type aliases", "easy"),
    ("Step 6: CP Patterns", "Number Theory", "Modular arithmetic & fast power", "medium"),
    ("Step 6: CP Patterns", "Number Theory", "Sieve of Eratosthenes & prime factorization", "medium"),
    ("Step 6: CP Patterns", "Number Theory", "GCD/LCM, Euler's totient, nCr mod p", "hard"),
    ("Step 6: CP Patterns", "Bit Tricks", "Bitmask DP & subset enumeration", "hard"),
    ("Step 6: CP Patterns", "Bit Tricks", "Bit manipulation tricks for CP", "medium"),
    ("Step 6: CP Patterns", "Advanced DS", "Segment tree — range query & point update", "hard"),
    ("Step 6: CP Patterns", "Advanced DS", "Fenwick tree (BIT) — prefix sums", "hard"),
    ("Step 6: CP Patterns", "Advanced DS", "Sparse table & RMQ", "hard"),
    ("Step 6: CP Patterns", "Advanced DS", "Disjoint Set Union (DSU) with path compression", "medium"),

    # ---------------- Step 7: Interview-Specific C++ ----------------
    ("Step 7: Interview C++", "Concepts", "vtable, vptr & dynamic dispatch overhead", "hard"),
    ("Step 7: Interview C++", "Concepts", "Copy elision & RVO/NRVO", "hard"),
    ("Step 7: Interview C++", "Concepts", "undefined behaviour — common traps", "hard"),
    ("Step 7: Interview C++", "Concepts", "Implement vector, stack & LRU cache from scratch", "hard"),
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
