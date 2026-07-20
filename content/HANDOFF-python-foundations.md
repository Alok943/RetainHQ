# Antigravity handoff — Python Foundations (Phase 0 for DSA)

**Why:** a beginner opening the DSA roadmap has never seen Python syntax — they hit `arr[::-1]`,
`enumerate()`, `sorted(key=...)` in the first arrays lessons and have to leave the app to search.
The fix is NOT a new beginner roadmap: python-swe already teaches the fundamentals
(`primitive-types` → `loops` → `lists` → `dictionaries` …). The fix is (a) **4 gap lessons**
python-swe is missing, and (b) a curated **"Before you start" foundations list** on the DSA
roadmap that links to the python-swe lessons in order.

> **Plumbing reality check (verified 2026-07-19, Claude).** `roadmap_node_prerequisites` can
> technically store cross-roadmap edges (FK is generic), but the API silently ignores them:
> `GET /{id}/blockers` builds its `incomplete` set from the current roadmap's nodes only
> (`roadmaps.py:245`), so a foreign prerequisite always counts as "done", and `RoadmapDetail.jsx`
> never renders per-node `prerequisites` IDs at all. **Decision (D-036): foundations are a
> content-side manifest + a UI section, NOT prereq edges.** Never-locking also matches the product
> thesis — foundations are a recommendation, not a gate.

Three passes:
- **Pass 0 — WIRING (Claude, before Pass 2 lands):**
  1. `content/validate.py`: skip `_foundations.json` from the lesson-schema walk
     (`ROOT.glob("*/*.json")` at `validate.py:301` currently catches every JSON in a roadmap dir)
     and add a dedicated shape check for it (fields below; every `{roadmap, slug}` pair must
     resolve to an existing lesson file).
  2. `RoadmapDetail.jsx`: fetch `/content/roadmaps/<key>/_foundations.json` (404 → no section);
     render a collapsible **"Before you start"** card above Phase 1 linking each item to
     `/roadmaps/<lesson.roadmap>/learn/<lesson.slug>`. v1 is links-only (no cross-roadmap
     progress state; follow-up if wanted). `sync-content.mjs` already copies every JSON in
     `content/roadmaps/` to `frontend/public/`, so no sync change needed.
  3. `seed_python_swe.py`: add the 4 new nodes (section/phase = wherever `lists` / `loops` live,
     ordered per the table). Reseed is a **prod action → user runs it**, per working agreement.
- **Pass 1 — 4 GAP LESSONS (Antigravity, THIS packet):** author the lessons below. Normal
  python-swe lessons — no dependency on Pass 0.
- **Pass 2 — FOUNDATIONS MANIFEST (Antigravity, after Pass 0 item 1):** author
  `content/roadmaps/dsa/_foundations.json` exactly per the spec below.

**Gate for passes 1–2: `python content/validate.py` — zero errors. Do NOT run the frontend.
Do NOT commit.**

---

## Pass 1 — the 4 gap lessons (`content/roadmaps/python-swe/<slug>.json`)

Contract: **`kind: "concept"`**, same schema as every python-swe lesson (see `lists.json` /
`loops.json` as shape references; `content/PROMPT-engineering.md` is the contract). `tier1` all four.
Audience: someone who has done the Phase-0 lessons before this one and nothing else — **assume they
can read `if`/`for`/`def`/lists, nothing more.** Examples should lean DSA-flavored (arrays, strings,
pairs) since that's where these lessons send you next.

| slug | title | core content | must cover |
|---|---|---|---|
| `strings-and-string-methods` | Strings & string methods | Strings as immutable sequences | indexing `s[0]`/`s[-1]`, immutability (`s[0]='x'` → TypeError, build a new string instead), iteration, `len`, `in`, `.lower()/.upper()`, `.strip()`, `.split()/.join()`, comparison, f-strings for output. DSA hooks: palindrome check, anagram counting (`.count()` vs a dict). |
| `slicing` | Slicing lists & strings | `seq[start:stop:step]` mental model (fence-post: stop is EXCLUSIVE) | `a[1:]`, `a[:n]`, `a[i:j]`, negative indices, `a[::-1]` reversal, step slices, slice = **copy** (vs alias — cross-link `shallow-vs-deep-copy`), works identically on `str`/`list`/`tuple`. DSA hooks: prefix/suffix, reversing, matrix row copy. |
| `enumerate-zip-range` | Loop idioms: `range`, `enumerate`, `zip` | The three ways DSA code walks a sequence | `range(n)`/`range(start,stop,step)` incl. reverse ranges (`range(n-1,-1,-1)`), `enumerate(a)` for index+value (vs the C-style `range(len(a))` — show both, name when each is right), `zip(a,b)` for pairwise walks, unpacking in the for-header. DSA hooks: two arrays in lockstep, index math in binary search. |
| `sorted-and-sort-key` | Sorting with `sorted` and `key=` | Sorting as a black box you steer with `key` | `sorted(a)` vs `a.sort()` (new list vs in-place), `reverse=True`, `key=len`, `key=lambda x: x[1]` for tuples/pairs, sorting dict items, stability (equal keys keep order — matters for interval problems). Cross-link `lambda-functions`. DSA hooks: sort intervals by start, sort pairs by second element. |

Build order = table order (slicing references strings; idioms reference both; sorting references
lambda). Each lesson cross-links its neighbors in `metadata.prerequisites`/`unlocks` by slug.

---

## Pass 2 — `content/roadmaps/dsa/_foundations.json`

```json
{
  "roadmap": "dsa",
  "title": "Before you start: the Python you need",
  "description": "DSA lessons are written in Python. If you can read these 15 lessons, no syntax in this roadmap will surprise you. This is a recommendation, not a lock — skip anything you already know.",
  "lessons": [
    { "roadmap": "python-swe", "slug": "primitive-types",             "why": "int, float, str, bool — the values every trace shows" },
    { "roadmap": "python-swe", "slug": "type-conversion",             "why": "int('5'), str(5) — input parsing in every problem" },
    { "roadmap": "python-swe", "slug": "if-elif-else",                "why": "every algorithm branches" },
    { "roadmap": "python-swe", "slug": "loops",                       "why": "for/while — the body of every algorithm" },
    { "roadmap": "python-swe", "slug": "break-continue-else",         "why": "early exit — how searches stop" },
    { "roadmap": "python-swe", "slug": "functions",                   "why": "every solution is a function taking inputs" },
    { "roadmap": "python-swe", "slug": "lists",                       "why": "THE array — the most used structure in DSA" },
    { "roadmap": "python-swe", "slug": "strings-and-string-methods",  "why": "immutable sequences — half of easy problems are strings" },
    { "roadmap": "python-swe", "slug": "slicing",                     "why": "arr[1:], arr[::-1] — you'll see these in lesson one" },
    { "roadmap": "python-swe", "slug": "tuples",                      "why": "fixed pairs — coordinates, (key, value) items" },
    { "roadmap": "python-swe", "slug": "dictionaries",                "why": "the hash map — the #1 interview data structure" },
    { "roadmap": "python-swe", "slug": "sets",                        "why": "O(1) membership — dedupe and seen-tracking" },
    { "roadmap": "python-swe", "slug": "enumerate-zip-range",         "why": "the loop idioms all DSA code is written in" },
    { "roadmap": "python-swe", "slug": "sorted-and-sort-key",         "why": "sort by a key — intervals, pairs, custom order" },
    { "roadmap": "python-swe", "slug": "list-comprehensions",         "why": "one-line transforms — you'll read them constantly" }
  ]
}
```

Rules: `lessons[].slug` must be an existing file under `content/roadmaps/<roadmap>/`; order is the
study order; `why` ≤ 12 words, concrete, DSA-flavored. The 4 Pass-1 slugs must exist first.

**Same pattern later (do NOT build yet):** `sql` foundations before data-eng, python foundations
before ai-engineering — one `_foundations.json` per roadmap, same shape.
