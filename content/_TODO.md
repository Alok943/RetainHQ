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
- [x] Type conversion: implicit vs explicit casting  →  `type-conversion`
- [x] Mutable default argument pitfall  →  `mutable-default-argument`

### Control Flow
- [x] if/elif/else and Python truthiness  →  `if-elif-else`
- [x] match-case statement  →  `match-case`
- [x] for and while loops  →  `loops`
- [x] break, continue, loop else clause  →  `break-continue-else`
- [x] Ternary expressions  →  `ternary-expressions`

### Functions
- [x] Defining functions and return values  →  `functions`
- [x] *args and **kwargs  →  `args-kwargs`
- [x] Keyword-only and positional-only parameters  →  `keyword-positional-params`
- [x] LEGB rule: variable scope in Python  →  `scope`
- [x] Lambda functions and when to use them  →  `lambda-functions`
- [x] First-class functions: passing and returning functions  →  `first-class-functions`

### Collections
- [x] Lists: indexing, slicing, methods  →  `lists`
- [x] Tuples: immutability and use cases  →  `tuples`
- [x] Dictionaries: operations and use cases  →  `dictionaries`
- [x] Sets: operations and use cases  →  `sets`
- [x] Time complexity of collection operations  →  `collection-complexity`
- [x] Shallow copy vs deep copy in Python  →  `shallow-vs-deep-copy`

### Comprehensions
- [x] List comprehensions  →  `list-comprehensions`
- [x] Dictionary and set comprehensions  →  `dict-set-comprehensions`
- [x] Nested comprehensions  →  `nested-comprehensions`
- [x] Generator expressions vs list comprehensions  →  `generator-expressions`

### Error Handling
- [x] try/except with specific exception types  →  `try-except`
- [x] else and finally blocks  →  `else-finally`
- [x] Raising exceptions with raise  →  `raising-exceptions`
- [x] Custom exception classes  →  `custom-exceptions`
- [x] Exception chaining with raise from  →  `exception-chaining`

**Phase 1 status: COMPLETE** ✅ — all 32 topics generated and `validate.py` passes.

---

## Phase 2 — Python Internals  (28 topics)

This is where RetainHQ's thesis ("understand execution, not syntax") pays off — these
topics are *all* about what Python does under the hood. Feed Phase 1 slugs into
`{{PREREQS}}` (esp. `scope`, `first-class-functions`, `mutable-vs-immutable`,
`object-identity`, `functions`). The hand-made `closures.json` is the quality bar.

### Object Model
- [x] Everything is an object in Python  →  `everything-is-an-object`
- [x] is vs == : identity vs equality  →  `is-vs-equals`  *(extends `object-identity`; keep focused on the operator semantics)*
- [x] Reference counting in CPython  →  `reference-counting`
- [x] Garbage collection and cyclic references  →  `garbage-collection`
- [x] Integer and string interning  →  `interning`

### Dunder Methods
- [x] __init__ and __new__  →  `init-vs-new`
- [x] __str__ vs __repr__  →  `str-vs-repr`
- [x] __len__, __getitem__, __setitem__  →  `len-getitem-setitem`
- [x] __iter__ and __next__  →  `iter-next-dunders`
- [x] __call__: making objects callable  →  `call-dunder`
- [x] Operator overloading: __add__, __eq__, __lt__  →  `operator-overloading`

### Iterables & Iterators
- [x] Iterable protocol in Python  →  `iterable-protocol`
- [x] Iterator protocol and StopIteration  →  `iterator-protocol`
- [x] Custom iterator class  →  `custom-iterator`
- [x] iter() and next() builtins  →  `iter-next-builtins`

### Generators
- [x] yield keyword and generator functions  →  `yield-generators`
- [x] Lazy evaluation and memory efficiency  →  `lazy-evaluation`
- [x] yield from and generator delegation  →  `yield-from`
- [x] Generator send() for two-way communication  →  `generator-send`

### Closures
- [x] (reference) closures  →  `closures`  ← golden hand-made example, the quality bar
- [x] Lexical scope and free variables  →  `lexical-scope`
- [x] Closure mechanics in Python  →  `closure-mechanics`
- [x] Late binding closures gotcha  →  `late-binding-closures`
- [x] Stateful functions using closures  →  `stateful-closures`

### Decorators
- [x] Function decorators  →  `decorators`
- [x] functools.wraps and preserving metadata  →  `functools-wraps`
- [x] Decorator factories with arguments  →  `decorator-factories`
- [x] Stacking multiple decorators  →  `stacking-decorators`
- [x] Class decorators  →  `class-decorators`

**Phase 2 status: COMPLETE** ✅ — all 28 topics generated and `validate.py` passes.

---

## Phase 3 — OOP & Design  (18 topics)

The interview-critical phase. Lean on Phase 1-2 slugs in `{{PREREQS}}` — esp.
`functions`, `scope`, `everything-is-an-object`, `is-vs-equals`, `init-vs-new`,
`operator-overloading`, `decorators`. MRO / diamond problem / SOLID are pure
execution-flow material — ideal for the step-through visualizer + aha-moments.

### Classes & Objects
- [x] Class creation and instantiation  →  `class-basics`
- [x] Instance variables vs class variables  →  `instance-vs-class-vars`
- [x] Instance, class, and static methods  →  `method-types`
- [x] Property decorator: getter, setter, deleter  →  `property-decorator`
- [x] __slots__ for memory optimization  →  `slots`

### Inheritance
- [x] Single inheritance and super()  →  `inheritance-super`
- [x] Multiple inheritance and the diamond problem  →  `multiple-inheritance`
- [x] MRO: Method Resolution Order (C3 linearization)  →  `mro`

### Polymorphism
- [x] Method overriding  →  `method-overriding`
- [x] Duck typing in Python  →  `duck-typing`
- [x] Structural subtyping with Protocols  →  `protocols`

### Abstraction
- [x] ABC module and abstract methods  →  `abc-abstract-methods`
- [x] Interface patterns in Python  →  `interface-patterns`

### SOLID Principles
- [x] Single Responsibility Principle  →  `srp`
- [x] Open/Closed Principle  →  `ocp`
- [x] Liskov Substitution Principle  →  `lsp`
- [x] Interface Segregation Principle  →  `isp`
- [x] Dependency Inversion Principle  →  `dip`

**Phase 3 status: COMPLETE** ✅ — all 18 topics generated and `validate.py` passes.

---

## Phase 4 — Professional Python  (23 topics)

The backend-relevance phase — maps directly onto the FastAPI/Pydantic stack.
Feed Phase 3 slugs into `{{PREREQS}}` (esp. `class-basics`, `property-decorator`,
`abc-abstract-methods`, `protocols`, `decorators`, `enter-exit`).

### Type Hints
- [x] Basic annotations: int, str, list, dict  →  `type-hints-basic`
- [x] Optional and Union types  →  `optional-union-types`
- [x] Generic types: List[T], Dict[K, V]  →  `generic-types`
- [x] TypeVar and generic functions  →  `typevar-generic-functions`
- [x] Protocols for structural typing  →  `type-hints-protocols`  *(extends Phase 3 `protocols`; angle on typing-module usage)*
- [x] TYPE_CHECKING for avoiding circular imports  →  `type-checking-imports`

### Dataclasses
- [x] @dataclass basics  →  `dataclass-basics`
- [x] field() and default_factory  →  `dataclass-field`
- [x] Frozen dataclasses  →  `frozen-dataclass`
- [x] __post_init__ processing  →  `post-init`
- [x] Dataclasses vs Pydantic: when to use which  →  `dataclass-vs-pydantic`

### Context Managers
- [x] with statement and resource management  →  `with-statement`
- [x] __enter__ and __exit__  →  `enter-exit`
- [x] contextlib.contextmanager decorator  →  `contextmanager-decorator`
- [x] Async context managers  →  `async-context-managers`

### Logging
- [x] Logging levels and basicConfig  →  `logging-basics`
- [x] Loggers, handlers, formatters  →  `loggers-handlers-formatters`
- [x] Structured logging with JSON output  →  `structured-logging`
- [x] Log rotation with RotatingFileHandler  →  `log-rotation`

### Configuration & Deps
- [x] os.environ and environment variables  →  `environment-variables`
- [x] python-dotenv for .env files  →  `dotenv`
- [x] pyproject.toml and project metadata  →  `pyproject-toml`
- [x] Poetry: dependency management basics  →  `poetry`

---

## Later phases (add when Phase 4 feels good)
Phase 5 Testing & Quality · Phase 6 Engineering Practices.
Pull the exact titles from `backend/seed_python_swe.py` the same way.

## Future roadmaps (separate base-language journeys, demand-pulled — not yet built)
Java for SWE · C++ for SWE — each its own `seed_*.py` + `content/roadmaps/<slug>/`,
mirroring how `python-swe` is the base under the AI-eng / REST-API path. Build only
when a real user / funnel signal asks for it.
