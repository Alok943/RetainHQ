# Curation queue — Python for SWE (`python-swe`)

Source of truth for topics: `backend/seed_python_swe.py` (the `NODES` list).
Generate **one JSON per node** using the **exact title** below as `{{TOPIC}}`.
Tick a box once the JSON is saved **and** `python content/validate.py` passes.
Feed already-done titles into the next topic's `{{PREREQS}}`.

---

## Phase 1 — Python Fundamentals  (32 topics)

### Variables & Types
- [x] Primitive types: int, float, bool, str
- [x] Dynamic typing and type()
- [ ] Mutable vs immutable objects
- [ ] Object identity: id() and memory references
- [ ] Type conversion: implicit vs explicit casting
- [ ] Mutable default argument pitfall

### Control Flow
- [ ] if/elif/else and Python truthiness
- [ ] match-case statement
- [ ] for and while loops
- [ ] break, continue, loop else clause
- [ ] Ternary expressions

### Functions
- [ ] Defining functions and return values
- [ ] *args and **kwargs
- [ ] Keyword-only and positional-only parameters
- [ ] LEGB rule: variable scope in Python
- [ ] Lambda functions and when to use them
- [ ] First-class functions: passing and returning functions

### Collections
- [ ] Lists: indexing, slicing, methods
- [ ] Tuples: immutability and use cases
- [ ] Dictionaries: operations and use cases
- [ ] Sets: operations and use cases
- [ ] Time complexity of collection operations
- [ ] Shallow copy vs deep copy in Python

### Comprehensions
- [ ] List comprehensions
- [ ] Dictionary and set comprehensions
- [ ] Nested comprehensions
- [ ] Generator expressions vs list comprehensions

### Error Handling
- [ ] try/except with specific exception types
- [ ] else and finally blocks
- [ ] Raising exceptions with raise
- [ ] Custom exception classes
- [ ] Exception chaining with raise from

---

## Reference
- [x] closures  ← golden hand-made example (Phase 2), the quality bar to match

## Later phases (add when Phase 1 feels good)
Phase 2 Internals · Phase 3 OOP & Design · Phase 4 Professional Python ·
Phase 5 Testing & Quality · Phase 6 Engineering Practices.
Pull the exact titles from `backend/seed_python_swe.py` the same way.
