# HANDOFF — python-swe gap-fill, beginner-first (P0 #3)

> Paste the block below into Antigravity (repo access required). Saved here so the
> mission survives session resets — point a fresh session at this file to resume.
> Status: NOT started.
>
> Context (verified 2026-07-12): the seed defines 148 nodes; 120 lessons exist; the 40
> node titles listed below resolve to NO lesson via the frontend's matching (exact
> manifest title, else slugified title). Several of the first ~12 likely DO have a
> lesson under a variant title (the manifest has case-duplicate keys like
> `Duck typing` vs `Duck typing in Python`) — hence Part A below. Do not skip Part A.

---

You are filling the lesson gap in RetainHQ's `python-swe` roadmap, beginner-first.
Work inside this repo. The job has two parts — classification first, then authoring.

## Read these files FIRST, fully, in this order — they are the contract
1. `content/PROMPT.md` — the base authoring contract (`kind: "concept"`). Note the
   AUDIENCE & OVERLAYS block at the top.
2. `content/PROMPT-beginner-overlay.md` — the beginner overlay. **Where it conflicts
   with the base contract, the OVERLAY WINS** (it names the base rules it overrides).
   Read the Terminology guard twice: schema `tier:` = item difficulty; the "tier-3
   college" audience must NOT push you toward `tier3` (advanced) items.
3. Two existing lessons as register references:
   `content/roadmaps/python-swe/mutable-default-argument-pitfall.json` (shape) and any
   Phase-5-adjacent lesson you can find (depth).

## The 40 target nodes (title → slug to use for a NEW file)
Phase 2/3/4 stragglers — CHECK FOR AN EXISTING LESSON FIRST (Part A):
- Shallow copy vs deep copy in Python → shallow-copy-vs-deep-copy-in-python
- Iterable protocol in Python → iterable-protocol-in-python
- Closure mechanics in Python → closure-mechanics-in-python
- Property decorator: getter, setter, deleter → property-decorator-getter-setter-deleter
- Multiple inheritance and the diamond problem → multiple-inheritance-and-the-diamond-problem
- Duck typing in Python → duck-typing-in-python
- Basic annotations: int, str, list, dict → basic-annotations-int-str-list-dict
- Generic types: List[T], Dict[K, V] → generic-types-list-t-dict-k-v
- Dataclasses vs Pydantic: when to use which → dataclasses-vs-pydantic-when-to-use-which
- with statement and resource management → with-statement-and-resource-management
- Structured logging with JSON output → structured-logging-with-json-output

Phase 5 — Testing & Quality (most are genuinely net-new):
- Test discovery and naming conventions → test-discovery-and-naming-conventions
- Assertions and pytest.raises → assertions-and-pytest-raises
- Fixtures and fixture scope → fixtures-and-fixture-scope
- @pytest.mark.parametrize → pytest-mark-parametrize
- conftest.py: shared fixtures → conftest-py-shared-fixtures
- unittest.mock: Mock and MagicMock → unittest-mock-mock-and-magicmock
- patch as decorator and context manager → patch-as-decorator-and-context-manager
- Dependency isolation strategies → dependency-isolation-strategies
- Mocking external API calls → mocking-external-api-calls
- Black: auto-formatting → black-auto-formatting
- Ruff: linting and import sorting → ruff-linting-and-import-sorting
- Mypy: static type checking → mypy-static-type-checking
- Pre-commit hooks setup → pre-commit-hooks-setup
- pdb and breakpoint() → pdb-and-breakpoint
- Reading stack traces → reading-stack-traces
- cProfile for performance profiling → cprofile-for-performance-profiling

Phase 6 — Engineering Practices (net-new):
- Branching strategies: feature, main, release → branching-strategies-feature-main-release
- Rebase vs merge → rebase-vs-merge
- Pull request workflow → pull-request-workflow
- Conventional commits spec → conventional-commits-spec
- Package structure and __init__.py → package-structure-and-init-py
- Layered architecture → layered-architecture
- Service-repository pattern → service-repository-pattern
- Modular design and separation of concerns → modular-design-and-separation-of-concerns
- Singleton pattern → singleton-pattern
- Factory pattern → factory-pattern
- Strategy pattern → strategy-pattern
- Observer pattern → observer-pattern
- Provider abstraction pattern → provider-abstraction-pattern

## Part A — classification (do this for ALL 40 before authoring anything)
For each node above, search `content/roadmaps/python-swe/` for an existing lesson that
already teaches it under a variant title (search by concept keywords in `title` and
`slug`, e.g. "shallow", "duck", "closure", "property", "diamond", "context manager").
Classify each node in `content/REPORT-python-swe-gap-fill.md`:
- `MAPPED <node title> -> <existing slug>` — an existing lesson covers it. Do NOT author
  a duplicate, do NOT rename anything (titles are cross-roadmap join keys; the founder
  fixes mappings separately).
- `NET-NEW <node title> -> <new slug>` — nothing covers it; you will author it in Part B.
Also list in the report any pairs of existing lessons whose titles differ only by case
or wording variant (the manifest currently has 9 case-duplicate keys) — report only.

## Part B — author every NET-NEW lesson
- One JSON per node at `content/roadmaps/python-swe/<slug>.json`, using the slug from
  the list above. `kind: "concept"`, full base schema from `PROMPT.md`, overlay rules
  B1–B11 on top (overlay wins; no invented JSON fields — the validator ignores them and
  the renderer never shows them).
- The lesson `title` must EXACTLY equal the node title from the list (it is the join key).
- Domain note (overlay §per-P0): these are tooling/practice topics. Code under test or
  discussion is code this learner already wrote in this roadmap (an average-marks
  function, a dedupe function) — NOT FastAPI services. Framework versions appear only
  as a labeled bridge at the end.
- Tooling topics that can't run in the browser (git, black, pre-commit): the
  `code_walkthrough` may be a pure-Python analogue, or lean on prose + config examples —
  never fake runnable output for a CLI tool.
- `prerequisites`/`unlocks` reuse existing python-swe slugs (browse the folder; do not
  invent slugs).

## Workflow (per batch of 5–6 lessons)
1. Author the batch.
2. Run `python content/validate.py` — every file must stay green. Fix before moving on.
3. Append one line per lesson to `content/REPORT-python-swe-gap-fill.md`:
   `<slug> — authored | checks: <n> | prediction rung: yes`.
4. Continue until every NET-NEW node is done.

## Boundaries
- You are the AUTHOR. Do NOT critique your own output — the critic pass runs later on a
  different model (`content/PROMPT-lesson-critic.md`, beginner-batch checks included).
- Do NOT commit, push, rename existing files, or touch anything outside
  `content/roadmaps/python-swe/` and the report file.
- If a topic resists the beginner register without losing correctness, do your best pass
  and add `FLAG: <one-line why>` to its report line.
