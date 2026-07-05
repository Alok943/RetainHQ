# C++ lesson generation — PROMPT / design doc (Antigravity authoring contract)

> **North star (every roadmap):** *"Can the learner explain AND apply this in an interview 30 days
> later?"* For a **language** roadmap the five questions adapt to:
> 1. **Why does this feature/idiom exist?** (what problem in the language it solves; the naive/unsafe way)
> 2. **How do I picture what the compiler/runtime does?** (the mental model — memory, copies, dispatch)
> 3. **What is the exact rule / invariant?** (the precise semantics — not vibes; e.g. *when* a copy vs a move happens)
> 4. **Where does this bite in real code?** (the engineering situation — the bug it prevents or causes)
> 5. **How do I recognize when to reach for it?** (the idiom's trigger + the anti-pattern it replaces)

You author **one JSON per node** for the **`cpp-swe`** roadmap. Write to
`content/roadmaps/cpp-swe/<slug>.json` (filename = slug). Validate with `python content/validate.py`.

There is **no C++ runtime in the browser** (Pyodide is Python, PGlite is SQL). So C++ lessons are
**prose + hardcoded, annotated code examples** — the code is *read*, never executed. This is a
deliberate design choice, not a limitation to apologize for: the value is the *explanation of what the
code does and why*, which is exactly what an AI-assisted coder can't yet do for themselves.

---

## THE KIND DECISION — reuse `kind: "engineering"`

C++ concept lessons use **`kind: "engineering"`** (already in `validate.py`). No new validator or
renderer work — the `engineering` branch already requires teach-from-scratch prose **plus a
`code_snippets` list**, which is precisely the annotated-code-walkthrough shape we want, with a
`language` field that accepts `"cpp"`. (The kind name is historical — it was built for AI-Engineering
— but the field contract fits language lessons exactly. Roadmap and kind are independent: `roadmap`
= `"cpp-swe"`, `kind` = `"engineering"`.)

**Algorithmic nodes (CP patterns, LRU cache) — v1 rule:** author them as `engineering` too, with the
algorithm shown in `code_snippets`. Do **NOT** attempt a `viz`/execution-trace block. Several of them
(segment/Fenwick tree, DSU) need renderers that don't exist yet (DSA phases 12/14/16). A later
"trace-upgrade" pass will bolt DSA-style traces onto the nodes tagged **[trace-later]** below, once
those renderers land — same two-pass model we used for DSA phase-9 (prose first, viz after). Author
prose-complete now; nothing blocks on the visualizer.

---

## INFRA PREREQS (Claude owns these — done/tracked, listed so the contract is complete)
1. `seed_cpp_swe.py` must set a **`slug = "cpp-swe"`** on the roadmap row (older seed doesn't yet) so
   the content system keys `content/roadmaps/cpp-swe/` → the roadmap, and routes
   `/roadmaps/cpp-swe/learn/<slug>`. *(Backfill/`GET /api/roadmaps/{ref}` already resolves slug-or-UUID.)*
2. `content/roadmaps/cpp-swe/` folder (create on first lesson).
3. `node scripts/sync-content.mjs` copies to `frontend/public/content/` (runs on predev/prebuild).

---

## REQUIRED FIELDS (`engineering` branch — check `validate.py` ~L390)
- `slug`, `title`, `roadmap` (`"cpp-swe"`), `kind` (`"engineering"`), `tier` (`tier1|tier2|tier3`).
- `metadata`: `{difficulty (easy|medium|hard), estimated_minutes, importance (1–10),
  interview_frequency (low|medium|high), prerequisites [slug], unlocks [slug]}`.
- `mental_model` — object with a non-empty **`intuition`** one-liner (+ `description`).
- `explanation` (multi-paragraph string) **OR** `sections` (text-only `{body, recap?}`).
- **`code_snippets` — REQUIRED, and per your call: ≥2 examples.** Each
  `{title, language: "cpp", code, explanation}`. This is the heart of a language lesson.
- `common_mistakes` — ≥1 `{title, explanation}`.
- `recall_questions` — **≥3** `{q, answer, tier}`.
- `oa_questions` — **≥2** `{question, answer}` (+ optional `approach`, `company` honest-category).
- `sources` — non-empty list of real `http(s)` URLs (cppreference / ISO / Meyers / Stroustrup / quality blogs).
- Optional: `hook {scenario, question?}`, `key_points [{title, detail}]`, `glossary [{term, definition}]`.
  (Do NOT use `animation` here — it's an AI-Eng box-flow/vector-space construct, not for C++.)

### Language-content rules (the anti-hallucination guards — NON-NEGOTIABLE)
- **API fidelity:** only reference real, canonical STL/std methods and signatures. When unsure, don't
  invent — omit. The Sonnet critic's expert pass fact-checks every signature; a made-up method is a fail.
- **Version-tag every version-specific feature** in prose or the snippet comment: `auto`/lambdas/`nullptr`
  = C++11, `make_unique` = C++14, structured bindings/`optional`/`variant` = C++17, `constexpr` growth
  across 11/14/17/20. Getting the standard wrong is a correctness error.
- **Every `code_snippet` must be compilable-by-inspection** — self-contained enough that a reader (and
  the critic, reading as a compiler) can see it's valid. Prefer a full tiny `main`/class over a dangling
  fragment. Show *output* in the `explanation` when it teaches (e.g. what `2*x - min` prints).
- **≥2 snippets, and make them EARN their place:** typically (a) the naive/buggy way, then (b) the
  correct idiom — the contrast IS the lesson. Not two near-duplicates.
- **NEVER copy** prose from cppreference/SO/GfG — read, understand, write original. Cite in `sources`.

---

## BATCHING — generate one Step per packet, pilot Step 1 first (DO NOT generate the whole roadmap at once)

Long-horizon generation degrades: later nodes thin out, examples recycle, and — worst for a language —
APIs get fabricated. So:
- **One Step = one handoff packet** (6–10 lessons). 8 packets total (Steps 1–7 + the const/iterator
  additions fold into 1 & 4).
- **Pilot: author Step 1 ONLY first.** Run `validate.py` → **Sonnet** lesson critic
  (`content/PROMPT-lesson-critic.md`, run as a separate agent from the author) → fix → re-critic. Use
  what breaks on those ~7 lessons to tighten this contract *before* scaling to Steps 2–7. Cheap to fix
  the contract on 7 lessons, expensive on 45.
- Gate each packet: **`validate.py` green → Sonnet critic PASS → next Step.**

---

## PER-NODE MAP — the misconception each node must inoculate against
This is the anchor that stops hallucination: author the lesson AROUND this pitfall, don't invent one.
`[trace-later]` = algorithmic; author prose now, DSA-style viz in a future pass.

### Step 1: Core Language
| node | tier | the pitfall / focus to teach |
|---|---|---|
| Data types, I/O & fast I/O tricks | easy | `endl` flushes every call (slow); `'\n'` doesn't. `sync_with_stdio(false)` unties C/C++ streams. |
| References vs pointers | medium | A reference is not an object and can't be rebound or null; a pointer can. Don't return a ref to a local. |
| const correctness | medium | `const&` params avoid a copy AND promise no mutation; a `const` method can't modify members. `const` is a contract, not decoration. |
| Functions — value/ref/pointer | easy | Pass-by-value copies (expensive for containers); pass-by-`const&` is the default for big objects. |
| Arrays, C-style vs std::string | easy | C-strings are null-terminated char arrays with no bounds/length; `std::string` owns its buffer + knows its size. |
| Preprocessor macros & #define | easy | Macros are blind text substitution (no scope/type) — `#define SQ(x) x*x` breaks on `SQ(a+b)`. Parenthesize; prefer `constexpr`. |
| auto, range-for, structured bindings | easy (C++17) | `auto` drops references/const by default (`auto x = ref` copies); use `auto&`/`const auto&` in range-for to avoid per-element copies. |

### Step 2: OOP in C++
| node | tier | the pitfall / focus |
|---|---|---|
| Classes, ctors, dtors & this | medium | Member init order follows declaration order, NOT the init-list order. Use the init list, not assignment in the body. |
| Operator overloading | medium | Overload as free function for symmetry (`a + b` vs `b + a`); return by value, take `const&`. Don't overload to be cute. |
| Inheritance & virtual / vtable | hard | A non-`virtual` base method called through a base pointer does NOT dispatch to the override (static binding). |
| Abstract classes & pure virtual | medium | A class with a pure virtual (`= 0`) can't be instantiated; a **missing `virtual ~Base()`** leaks on `delete base`. |
| Rule of 3/5/0 | hard | If you manage a raw resource you need dtor + copy-ctor + copy-assign (and move pair in C++11), else a shallow copy → double-free. Prefer Rule of 0 (own nothing raw). |

### Step 3: Memory Management
| node | tier | the pitfall / focus |
|---|---|---|
| Stack vs heap — new/delete | medium | Stack objects die at scope end (automatic); heap objects live until `delete` — forget it and it leaks. `new[]` pairs with `delete[]`. |
| Leaks, dangling, double-free | hard | Using a pointer after `delete` (dangling) or deleting twice is UB. Set to `nullptr` after delete; better, don't use raw owning pointers. |
| unique_ptr / shared_ptr / weak_ptr | hard | `shared_ptr` cycles never free — break with `weak_ptr`. `unique_ptr` is move-only. Copying a `shared_ptr` bumps an atomic refcount (cost). |
| RAII | medium | Tie resource lifetime to object lifetime: acquire in ctor, release in dtor. This is why C++ rarely needs `finally`. |

### Step 4: STL
| node | tier | the pitfall / focus |
|---|---|---|
| vector internals & push_back amortization | easy | Growth reallocates and **invalidates all iterators/pointers**; amortized O(1) push, but a single push can be O(n). `reserve` to avoid churn. |
| deque, list & array | easy | `std::list` is a doubly-linked list (O(1) splice, bad cache); `std::array` is fixed-size stack storage; `deque` = block-indexed. |
| Iterator invalidation | hard (NEW) | Mutating a container mid-iteration invalidates iterators (vector: any realloc/erase; map: only the erased node). Erase with the `it = c.erase(it)` idiom. |
| map & set (RB tree) | medium | Ordered, O(log n), iterate in sorted order. `operator[]` on a `map` **inserts** a default if absent — use `.find`/`.count` to just check. |
| unordered_map / unordered_set | medium | Average O(1), worst O(n) on collisions; unordered iteration. Needs a hash for custom keys. Rehash invalidates iterators (not references). |
| multimap, multiset & priority_queue | medium | `priority_queue` is a **max-heap** by default; for min-heap pass `greater<>`. multi* allow duplicate keys. |
| sort, binary_search, lower/upper_bound | easy | `sort` needs a **strict-weak-ordering** comparator (`<`, not `<=`, or it's UB). `lower_bound` = first `>= x`, `upper_bound` = first `> x`. |
| next_permutation, rotate, reverse | easy | `next_permutation` needs a **sorted** start to enumerate all perms; returns false and wraps when it's the last. |
| Custom comparators with lambda | medium | For `priority_queue` the comparator returns true when a should come **below** b (inverted vs intuition). Capture-less lambda for `sort`. |
| accumulate, transform & <algorithm> | medium | `accumulate`'s init type drives the result type — `accumulate(v.begin(),v.end(),0)` truncates doubles. Pass `0.0`/`0LL`. |

### Step 5: Modern C++
| node | tier | the pitfall / focus |
|---|---|---|
| Lambdas & closures | medium | `[=]` copies captures, `[&]` captures by reference (dangling if the lambda outlives the scope). `mutable` to modify a by-value capture. |
| Move semantics & rvalue refs | hard | Move *steals* the source's guts, leaving it valid-but-unspecified. `std::move` is just a cast — it doesn't move anything by itself. Don't `move` a `const`. |
| Templates — function & class | hard | Templates are compiled per instantiation (code bloat + errors deferred to use). Definitions live in headers. |
| constexpr & compile-time | hard | `constexpr` = *may* run at compile time if inputs are constant; not a guarantee unless in a constant context. Version-sensitive (11→20). |
| optional / variant / any (C++17) | medium | `optional` models "maybe a value" without sentinels/null; deref-ing an empty `optional` is UB — check first. `variant` is a type-safe union. |

### Step 6: CP Patterns
| node | tier | the pitfall / focus |
|---|---|---|
| CP template — fast I/O, macros, aliases | easy | Same fast-I/O trap as Step 1; `#define int long long` overflow guard is a common (blunt) CP habit — know its cost. |
| Modular arithmetic & fast power | medium `[trace-later]` | Take mod at every step to avoid overflow; `(a*b)%m` can overflow before the mod — cast to `long long`. |
| Sieve of Eratosthenes & factorization | medium `[trace-later]` | Start marking at `i*i`, step `i`; sieve is O(n log log n), not O(n√n). |
| GCD/LCM, totient, nCr mod p | hard `[trace-later]` | `lcm(a,b) = a/gcd*b` (divide first to avoid overflow); nCr mod prime needs modular inverse (Fermat), not plain division. |
| Bitmask DP & subset enumeration | hard `[trace-later]` | Enumerate submasks with `for(s=m; s; s=(s-1)&m)`; state is `dp[mask]`. `1<<n` overflows int for n≥31 — use `1LL`. |
| Bit manipulation tricks | medium | `x & -x` isolates the lowest set bit; `x & (x-1)` clears it. Shifting by ≥ width is UB. |
| Segment tree — range query/point update | hard `[trace-later, needs tree renderer]` | Build 2n/4n array; a query splits into O(log n) canonical segments. Off-by-one on the node ranges is the classic bug. |
| Fenwick tree (BIT) — prefix sums | hard `[trace-later, needs array renderer]` | 1-indexed; `i += i & -i` to update, `i -= i & -i` to query. Answers prefix sums, not arbitrary ranges directly. |
| Sparse table & RMQ | hard `[trace-later]` | O(1) idempotent range queries (min/gcd) after O(n log n) build; only for **immutable** arrays and overlap-safe ops. |
| DSU with path compression | medium `[trace-later, needs forest renderer]` | Union by rank + path compression → near-O(1) amortized (inverse Ackermann). Forgetting compression makes it O(log n)+. |

### Step 7: Interview C++
| node | tier | the pitfall / focus |
|---|---|---|
| vtable, vptr & dynamic dispatch overhead | hard | Each polymorphic object carries a hidden vptr; virtual calls cost an indirection + defeat inlining. Not free — know when it matters. |
| Copy elision & RVO/NRVO | hard | Returning a local by value is elided (no copy) — mandatory for prvalues in C++17. Don't `std::move` a return value; it *pessimizes* by disabling NRVO. |
| Undefined behaviour — common traps | hard | Signed overflow, OOB access, use-after-free, uninitialized reads are UB — the compiler may assume they never happen and delete your checks. |
| Implement vector / stack / LRU cache | hard `[trace-later]` | LRU = hashmap(key→list-iterator) + doubly-linked list for O(1) move-to-front; the linkage between the two structures is the whole trick. |

---

## GOLD TEMPLATE — one filled `engineering`-kind C++ lesson (study before authoring)

```json
{
  "slug": "rule-of-3-5-0-copy-move-destructor",
  "title": "Rule of 3 / 5 / 0",
  "roadmap": "cpp-swe",
  "kind": "engineering",
  "tier": "tier3",
  "metadata": {
    "difficulty": "hard", "estimated_minutes": 20, "importance": 9,
    "interview_frequency": "high",
    "prerequisites": ["classes-constructors-destructors-and-this"],
    "unlocks": ["move-semantics-and-rvalue-references"]
  },
  "hook": {
    "scenario": "You write a class that holds a raw pointer, copy one object into another, and both destructors run at scope end. Your program crashes with 'double free'.",
    "question": "You never called delete twice — so who did?"
  },
  "mental_model": {
    "intuition": "The compiler silently writes a copy-constructor for you, and its copy is SHALLOW: it duplicates the pointer, not what it points to. Now two objects own the same memory — and both will free it.",
    "description": "If your class manages a raw resource (heap memory, a file handle, a socket), the compiler-generated copy operations do the wrong thing. The Rule of 3 says: if you need a custom destructor, you almost certainly need a custom copy-constructor and copy-assignment too. C++11 adds move-constructor and move-assignment (Rule of 5). The Rule of 0 is the escape hatch: own nothing raw (use std::vector / std::unique_ptr) and you need to write NONE of them."
  },
  "explanation": "A class that owns a raw pointer is a trap, because C++ gives every class a free copy-constructor and copy-assignment operator — and they copy member-by-member. For a pointer member that means copying the ADDRESS, so the original and the copy point at the same heap block. When both objects go out of scope, both destructors call delete on that one block: undefined behaviour, usually a crash.\n\nThe Rule of 3 (pre-C++11): if you define any one of destructor, copy-constructor, or copy-assignment, you need all three, because their presence signals you're managing a resource the defaults can't handle.\n\nC++11 adds move operations, making it the Rule of 5: destructor, copy-ctor, copy-assign, move-ctor, move-assign. A move transfers ownership (steal the pointer, null out the source) instead of duplicating — cheap, and correct for temporaries.\n\nThe modern answer is the Rule of 0: don't manage raw resources at all. Hold a std::vector or std::unique_ptr, whose own copy/move semantics are already correct, and let the compiler-generated special members just work. Reach for Rule of 5 only when you're writing the resource-owning wrapper itself.",
  "code_snippets": [
    {
      "title": "The bug: shallow copy → double free",
      "language": "cpp",
      "code": "struct Buf {\n  int* data;\n  Buf(int n) : data(new int[n]) {}\n  ~Buf() { delete[] data; }   // custom dtor, but NO custom copy\n};\n\nint main() {\n  Buf a(10);\n  Buf b = a;   // shallow copy: b.data == a.data\n}                // both dtors run -> delete[] the SAME pointer twice -> crash",
      "explanation": "Buf defines a destructor but relies on the compiler's shallow copy-constructor. `b = a` copies the pointer value, so a.data and b.data alias the same block. At the closing brace both are destroyed and delete[] is called twice on one address — a double free."
    },
    {
      "title": "The fix: Rule of 5 (deep copy + move)",
      "language": "cpp",
      "code": "struct Buf {\n  int* data; int n;\n  Buf(int n) : data(new int[n]), n(n) {}\n  ~Buf() { delete[] data; }\n  Buf(const Buf& o) : data(new int[o.n]), n(o.n) {      // copy: allocate + duplicate\n    std::copy(o.data, o.data + o.n, data);\n  }\n  Buf& operator=(Buf o) { std::swap(data, o.data); std::swap(n, o.n); return *this; } // copy-and-swap\n  Buf(Buf&& o) noexcept : data(o.data), n(o.n) { o.data = nullptr; o.n = 0; } // move: steal\n};",
      "explanation": "The copy-constructor allocates its OWN block and duplicates the contents (deep copy), so each object frees a distinct pointer. The move-constructor steals the pointer and nulls the source, so the moved-from object's delete[] is a harmless delete[] nullptr. The copy-and-swap assignment handles both cleanly and is self-assignment-safe."
    },
    {
      "title": "The best fix: Rule of 0",
      "language": "cpp",
      "code": "struct Buf {\n  std::vector<int> data;   // owns nothing raw\n  Buf(int n) : data(n) {}\n  // no dtor, no copy, no move — the compiler's defaults are already correct\n};",
      "explanation": "By delegating ownership to std::vector (whose copy/move are correct), Buf needs none of the five special members. This is the idiom to reach for by default — write the Rule of 5 only inside the resource wrapper itself."
    }
  ],
  "common_mistakes": [
    { "title": "Defining a destructor but not the copy operations", "explanation": "The most common source of double-free: a custom ~T() with the compiler's shallow copy still active. Either define all of Rule of 3/5, or =delete the copies, or use Rule of 0." },
    { "title": "Forgetting noexcept on the move constructor", "explanation": "std::vector only uses your move-ctor during reallocation if it's noexcept; otherwise it falls back to copying for exception safety. A non-noexcept move silently pessimizes performance." }
  ],
  "recall_questions": [
    { "q": "Why does a class with a raw owning pointer and only a custom destructor crash on copy?", "answer": "The compiler-generated copy is shallow: it duplicates the pointer, so two objects own one block and both destructors delete it — a double free.", "tier": "tier1" },
    { "q": "State the Rule of 3 and what C++11 added to make it the Rule of 5.", "answer": "Rule of 3: if you need a custom destructor, copy-constructor, or copy-assignment, you need all three. C++11 adds move-constructor and move-assignment (Rule of 5).", "tier": "tier1" },
    { "q": "What is the Rule of 0 and why prefer it?", "answer": "Own no raw resources — hold types like std::vector/std::unique_ptr whose special members are already correct — so you write none of the five. It's the least error-prone default.", "tier": "tier2" }
  ],
  "oa_questions": [
    { "question": "A candidate's String class double-frees on copy. What's missing and how do you fix it three ways?", "company": "SDE interview", "answer": "It has a destructor but relies on the shallow default copy. Fix: (1) define a deep copy-ctor + copy-assign (Rule of 3), (2) add move ops (Rule of 5), or (3) replace the raw char* with std::string (Rule of 0).", "approach": "Recognize the destructor-without-copy signature as the tell." },
    { "question": "Why should you NOT std::move a local variable in a return statement?", "company": "SDE interview", "answer": "It disables NRVO (named return value optimization): the compiler would elide the copy entirely, but an explicit std::move forces a move-construction instead, which is strictly worse.", "approach": "Ties Rule-of-5 knowledge to copy elision." }
  ],
  "key_points": [
    { "title": "The tell", "detail": "A custom destructor with the default (shallow) copy still enabled = latent double-free." },
    { "title": "Rule of 5", "detail": "dtor + copy-ctor + copy-assign + move-ctor + move-assign, as a set." },
    { "title": "Default to Rule of 0", "detail": "Own resources through std::vector/unique_ptr; write the five only in the wrapper itself." }
  ],
  "sources": [
    "https://en.cppreference.com/w/cpp/language/rule_of_three",
    "https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#Rc-five"
  ]
}
```

---

## QUALITY BAR (check before saving each node)
1. Could a learner answer all **FIVE questions** (language-adapted) from this lesson alone?
2. Do the **≥2 `code_snippets`** carry the lesson — ideally naive/buggy → correct idiom — and is each compilable-by-inspection?
3. **API fidelity:** every STL call/signature real; every version-specific feature standard-tagged.
4. **SELF-CONTAINMENT:** every recall/oa answer derivable from the body (`mental_model`/`explanation`/`code_snippets`/`key_points`) — no technique sprung only in an answer key.
5. **NO UNEXPLAINED JARGON:** any term an answer leans on (UB, RVO, strict-weak-ordering, refcount, dangling) is explained in the body.
6. `sources` = 2–5 real authoritative URLs (cppreference / ISO CppCoreGuidelines / Meyers / official). No fabricated links.
7. No `viz`, no `animation`, no `image`. (Trace upgrade is a later Claude pass on `[trace-later]` nodes only.)

## RUN
```
python content/validate.py            # must end "All content valid. [OK]"
cd frontend && node scripts/sync-content.mjs
```
Then the node renders at `/roadmaps/cpp-swe/learn/<slug>` (static page renders without the backend;
the roadmap-detail linkage needs `seed_cpp_swe.py` re-run on the DB with the `cpp-swe` slug set).

---

## PIPELINE (same standing flow as every roadmap)
author (Antigravity, one Step per packet) → `validate.py` (structure) → **Sonnet** lesson critic
(`content/PROMPT-lesson-critic.md`, separate agent) → author applies fix list → re-critic → done.
**Pilot Step 1, tighten this contract, then scale.** Java reuses this doc verbatim (kind `engineering`,
roadmap `java-swe`) with a Java-specific per-node map + gold template.
```
