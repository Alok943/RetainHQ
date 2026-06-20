# Curation queue — Python for SWE (`python-swe`)

Source of truth for topics: `backend/seed_python_swe.py` (the `NODES` list).
Generate **one JSON per node** using the **exact title** below as `{{TOPIC}}`.
Tick a box once the JSON is saved **and** `python content/validate.py` passes.
Feed already-done titles into the next topic's `{{PREREQS}}`.

---

## Phase 1 — Python Fundamentals  (32 topics)

Format: `- [ ] <exact title>  →  <slug>` (slug = filename `<slug>.json` AND the `slug`
field inside). Slugs are canonical — reuse them in other topics' prerequisites/unlocks.

### Variables & Types
- [x] Primitive types: int, float, bool, str  →  `primitive-types`
- [x] Dynamic typing and type()  →  `dynamic-typing`
- [x] Mutable vs immutable objects  →  `mutable-vs-immutable`
- [x] Object identity: id() and memory references  →  `object-identity`
- [ ] Type conversion: implicit vs explicit casting  →  `type-conversion`
- [x] Mutable default argument pitfall  →  `mutable-default-argument`

### Control Flow
- [x] if/elif/else and Python truthiness  →  `if-elif-else`
- [x] match-case statement  →  `match-case`
- [x] for and while loops  →  `loops`
- [x] break, continue, loop else clause  →  `break-continue-else`
- [x] Ternary expressions  →  `ternary-expressions`

### Functions
- [ ] Defining functions and return values  →  `functions`
- [ ] *args and **kwargs  →  `args-kwargs`
- [ ] Keyword-only and positional-only parameters  →  `keyword-positional-params`
- [ ] LEGB rule: variable scope in Python  →  `scope`
- [ ] Lambda functions and when to use them  →  `lambda-functions`
- [ ] First-class functions: passing and returning functions  →  `first-class-functions`

### Collections
- [ ] Lists: indexing, slicing, methods  →  `lists`
- [ ] Tuples: immutability and use cases  →  `tuples`
- [ ] Dictionaries: operations and use cases  →  `dictionaries`
- [ ] Sets: operations and use cases  →  `sets`
- [ ] Time complexity of collection operations  →  `collection-complexity`
- [ ] Shallow copy vs deep copy in Python  →  `shallow-vs-deep-copy`

### Comprehensions
- [ ] List comprehensions  →  `list-comprehensions`
- [ ] Dictionary and set comprehensions  →  `dict-set-comprehensions`
- [ ] Nested comprehensions  →  `nested-comprehensions`
- [ ] Generator expressions vs list comprehensions  →  `generator-expressions`

### Error Handling
- [ ] try/except with specific exception types  →  `try-except`
- [ ] else and finally blocks  →  `else-finally`
- [ ] Raising exceptions with raise  →  `raising-exceptions`
- [ ] Custom exception classes  →  `custom-exceptions`
- [ ] Exception chaining with raise from  →  `exception-chaining`

---

## Reference
- [x] closures  ← golden hand-made example (Phase 2), the quality bar to match

## Later phases (add when Phase 1 feels good)
Phase 2 Internals · Phase 3 OOP & Design · Phase 4 Professional Python ·
Phase 5 Testing & Quality · Phase 6 Engineering Practices.
Pull the exact titles from `backend/seed_python_swe.py` the same way.
