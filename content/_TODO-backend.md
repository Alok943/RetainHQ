# _TODO — python-backend lesson content (roadmap `python-backend`, UUID 88888888…)

Node list = `backend/seed_python_backend.py` (69 nodes). Derivation audit: `content/research/python-backend/nodes.md`.

**Three buckets:**
- `REUSE` — lesson already exists in `content/roadmaps/python-swe/<slug>.json`. Antigravity SKIPS these.
  (Wiring reuse into the python-backend folder is a Claude/runtime task, not content generation.)
- `concept` — NEW runnable Pyodide lesson. Author per the python-swe concept shape — copy the structure of
  `content/roadmaps/python-swe/decorators.json` (code_walkthrough + understanding_checks).
- `engineering` — NEW illustrative-code lesson (NOT executed in browser). Author per `content/PROMPT-backend.md`.

File target for new lessons: `content/roadmaps/python-backend/<slug>.json`. Validate: `python content/validate.py`.

## Phase 1 · Python Language Core (13) — 11 reuse, 2 new
| Node | Slug | Kind |
|---|---|---|
| Mutable vs immutable types | mutable-vs-immutable | REUSE |
| is vs == | is-vs-equals | REUSE |
| None & truthiness | none-and-truthiness | **concept (NEW)** |
| Variables as references | object-identity | REUSE |
| list vs tuple | tuples | REUSE |
| dict internals & ordering | dictionaries | REUSE |
| set & membership | sets | REUSE |
| Comprehensions | list-comprehensions | REUSE |
| Slicing | slicing | **concept (NEW)** |
| *args & **kwargs | args-kwargs | REUSE |
| Mutable default argument pitfall | mutable-default-argument | REUSE |
| Closures & LEGB scope | closures | REUSE |
| Positional vs keyword arguments | keyword-positional-params | REUSE |

## Phase 2 · Pythonic Constructs (8) — all reuse
iterator-protocol · yield-generators · generator-expressions · decorators · functools-wraps ·
with-statement · try-except · custom-exceptions — all REUSE.

## Phase 3 · OOP in Python (8) — all reuse
instance-vs-class-vars · method-types · property-decorator · operator-overloading (covers __eq__; note
__hash__ gap acceptable) · str-vs-repr · inheritance-super · duck-typing · dataclass-basics — all REUSE.

## Phase 4 · Concurrency, Memory & Performance (9) — 2 reuse, 7 new
| Node | Slug | Kind |
|---|---|---|
| [x] Concurrency vs parallelism | concurrency-vs-parallelism | **engineering (NEW)** |
| [x] The GIL | the-gil | **engineering (NEW)** |
| [x] Threading vs multiprocessing | threading-vs-multiprocessing | **engineering (NEW)** |
| Coroutines, async/await | coroutines-async-await | **concept (NEW)** — async runs in Pyodide |
| The event loop | the-event-loop | **concept (NEW)** |
| Tasks & gather | tasks-and-gather | **concept (NEW)** |
| [x] Blocking calls in async code | blocking-calls-in-async | **engineering (NEW)** — timing demo won't trace well |
| Reference counting & GC | reference-counting | REUSE |
| Shallow vs deep copy | shallow-vs-deep-copy | REUSE |

## Phase 5 · Web Framework & API (12) — all engineering (NEW)
[x] wsgi-vs-asgi · [x] path-and-query-parameters · [x] request-body-and-response-model · [x] routers-and-app-structure ·
[x] async-vs-def-endpoints · [x] dependency-injection-depends · [x] middleware-and-cors · [x] status-codes-and-openapi ·
[x] background-tasks · [x] pydantic-models-and-validators · [x] pydantic-settings · [x] configdict-from-attributes

## Phase 6 · Data Layer (7) — all engineering (NEW)
[x] sqlalchemy-sqlmodel-async · [x] sessions-and-expire-on-commit · [x] eager-loading-selectinload · [x] n-plus-1-queries ·
[x] alembic-migrations · [x] transactions-and-atomicity · [x] connection-pooling

## Phase 7 · Testing (6) — all engineering (NEW)
[x] pytest-basics-and-fixtures · [x] parametrized-tests · [x] mocking-and-patching · [x] async-tests ·
[x] api-tests-httpx-testclient · [x] coverage-and-ci

## Phase 8 · Production & Deployment (6) — all engineering (NEW)
[x] env-vars-and-secrets · [x] structured-logging-prod (python-swe has `structured-logging`; backend version is
JSON-logs-in-request-context — distinct skill, keep separate) · [x] httpexception-and-error-shape ·
[x] dockerfile-multi-stage · [x] uvicorn-gunicorn-workers · [x] hardening-health-rate-limit-jwt

## Totals
- REUSE: 29 (Antigravity skips)
- NEW concept: 6 (none-and-truthiness, slicing, coroutines-async-await, the-event-loop, tasks-and-gather + phase-1/4 above)
- NEW engineering: 34 → **Antigravity workload = 40 lessons**, engineering-kind first (higher value, no runnable dependency).

## Order of generation (for Antigravity)
1. Phase 6 Data Layer (7) — highest interview signal, ground truth in PROMPT-backend.md.
2. Phase 5 Web Framework (12).
3. Phase 7 Testing (6) + Phase 8 Production (6).
4. Phase 4 engineering trio + blocking-calls (4).
5. Concept-kind lessons (6) last — they need the Pyodide walkthrough shape.
