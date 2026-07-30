# Implementation Plan — LeetCode capture in the Log Activity form

**For the implementer.** Written 2026-07-30. Not started — this is the doc only.
Parents: `SPEC-leetcode-retention.md` (§3 catalog, §4 capture tiers, §5 scheduling),
`IMPLEMENTATION-problem-capture.md` (§1 evidence boundary — **load-bearing, read it first**),
`ARCHITECTURE-learning-system.md` (D-038 evidence vs. inference), `docs/DECISIONS.md`.

Scope: add **LeetCode** to the Roadmap picker in `LogActivity.jsx`. Picking it turns the form
into a problem-capture form — typeahead over the 3,999-problem catalog (by number *or* title),
a language dropdown, and a card that reviews the **concept and the pattern**, not the syntax.

---

## 0. Prod state — verified 2026-07-30 via read-only Supabase MCP. Do not re-derive.

| Fact | Value | Consequence for this feature |
|---|---|---|
| `problems` | 3,999 | Small enough that server-side search needs **no index and no `pg_trgm`** (§5.2) |
| `problems.paid_only = true` | **0** | The "label the paywall" concern from `IMPLEMENTATION-problem-capture.md` §5 is currently moot. Still render the label — a re-import can flip it |
| `problem_concepts` | 5,084 (2,944 primary / 1,718 supporting / 422 alternative) | `role='primary'` is the node a logged solve resolves to |
| `role='out_of_scope'` rows | **0** | The spec's §3.2.0 bucket was never written. ~1,055 problems are simply **unmapped** instead. §4.3 handles them |
| `problem_concepts.reviewed_by='human'` | **0** | Machine-only. **Spot-checked 2026-07-30 — see §13. The 0.9 band is good enough to auto-fill; the tail is not.** |
| `confidence` on primary rows | banded 0.9 (2,120) / 0.6 (696) / 0.3 (128) | Ordinal, and **empirically well-calibrated** (§13). Use bands, never the float |
| Primaries on scaffold nodes | **66** (28 of them at conf 0.9) | Hard contract violation — `content/PROMPT-leetcode-mapping.md:120` bans 26 scaffold slugs as `primary`. Mechanically detectable; §6.1 |
| `concept_cards` | **0 rows** | **There is no card bank.** Anything in this plan that depended on it would not ship. §7 routes around it |
| `problem_attempts` | 0 rows | Table exists, RLS on, unused so far |
| Mapped roadmap | `dsa` (`dddddddd-…`), 126 nodes, **114 mapped** | See the trap below |
| RLS | on for `problems`, `problem_concepts`, `problem_attempts`, `activities`, `concept_cards` | Nothing to add for existing tables |

> **Trap — there are four DSA roadmaps in the picker.** `dsa` (126 nodes, *the mapped one*),
> `dsa-striver` (194), `neetcode-150` (150), `blind-75` (111). **Only `dsa` has any
> `problem_concepts` rows.** Resolve the roadmap by slug `'dsa'`, never by "the first roadmap
> whose title contains DSA", and never by hardcoding the UUID in the frontend.

---

## 1. The rule that governs everything here

`IMPLEMENTATION-problem-capture.md` §1 says a manual mark is a **completion checkbox, not
evidence** — no `learning_event`, no `node_mastery` movement. This feature adds a manual path
that *does* end in the review loop, so the boundary needs restating precisely, because getting
it wrong is how the mastery number stops being true:

> **The solve claim is not evidence. The recall performance is.**

| What the user does | What it writes | Reaches `node_mastery`? |
|---|---|---|
| Logs "I solved Two Sum in Python" | `problem_attempts` row + an `activities` card | **No** |
| Later *reviews* that card and answers the questions | `RECALL_GRADED`, `T2_verified_internal` (existing path, `reviews.py:161`) | **Yes** |
| Extension observes a real Accepted submission | `PROBLEM_SOLVED`, `T1_verified_external` | Yes |

This is coherent with both parent docs and it is the honest line: clicking a name in a dropdown
proves nothing, but answering "why does the hash-map trade space for the second pass?" three
days later proves something real. It also means the existing `reviews.py` evidence block needs
**zero changes** — it already fires on any card with `node_id` set.

**Do not** write a `PROBLEM_SOLVED` event from this path, at any trust tier, including `T4_claimed`.

---

## 2. UX flow

**Roadmap picker gains one option, pinned above the groups:**

```
Roadmap  [OPTIONAL]
  ├─ 🟠 LeetCode problem        ← new, first
  ├─ No roadmap
  ├─ In progress …
  └─ All roadmaps …
```

Selecting it (`value="__leetcode__"`) switches the form into LeetCode mode:

1. **Topic / Resource Name** is replaced by a **problem combobox** (§5). Type `1` → *1. Two Sum*.
   Type `two sum` → same. Type `trapping` → *42. Trapping Rain Water*.
2. On select, an inline **resolved-concept chip** appears: `Hash Tables · high confidence` with
   a **Change** affordance (§6). This is the single most important element on the screen — it is
   what the user will be quizzed on, so it must be visible *before* submit, never after.
3. A **Language** dropdown appears (§4.2). Defaults to the user's last used.
4. `source_type` is forced to `problem` and the select is disabled with a hint
   ("set by LeetCode mode"). Do not leave it editable and silently ignore it.
5. **Key Memory stays required.** This is the product thesis; a LeetCode log with no takeaway is
   a completion checkbox, and we already have a table for those. The existing
   "Stuck? Suggest key points" assist becomes node-grounded here and is genuinely good — wire it
   to pass the resolved node.
6. Difficulty / Needed hint / Mistake are unchanged and still map to the FSRS + weight inputs.

Switching *away* from LeetCode restores the plain topic input and keeps whatever text was there.
The `localStorage` draft must round-trip the new fields (`problemId`, `language`) — it already
persists `roadmapId`, so a half-restored LeetCode draft is the obvious regression.

---

## 3. Two axes: the pattern is language-neutral, the implementation is not

"Language independent" applies to the **catalog and the pattern**, not to the questions. The
language dropdown exists precisely so the review *can* ask language-specific questions, because
those test real understanding.

| Axis | Language | Example question |
|---|---|---|
| **Pattern / concept** | neutral | "Why does the window stay valid when you shrink from the left?" |
| **Implementation** | specific | "You wrote this in Python — why is `deque.popleft()` the right call here and `list.pop(0)` a trap?" |

The second axis is not trivia. It is where most real bugs and most interview stumbles live, and
it is invisible to every language-agnostic DSA resource:

- **Python** — `heapq` is min-only (negate for max); `list.pop(0)` is O(n) vs `deque.popleft()` O(1); default recursion limit kills naive DFS on 10⁴ nodes.
- **Java** — `HashMap` O(1) vs `TreeMap` O(log n); `PriorityQueue` is a min-heap; `Integer` cache makes `==` work up to 127 and silently break after.
- **C++** — `unordered_map` degrades to O(n) under adversarial hashes (a real Codeforces hack); `vector::push_back` invalidates iterators; `std::sort` is not stable.
- **Go** — a slice sharing a backing array after `append`; no heap without implementing `container/heap`.
- **JavaScript** — `Array.prototype.sort` is lexicographic by default; no native priority queue.

**The one guardrail that survives:** ask about **semantics and complexity, never syntax lookup.**
"What does `heappush` cost, and why can't it give you a max-heap?" is understanding. "What's the
import line for heapq?" is a thing you look up in two seconds and should never occupy a review.

**Consequence for the schema (§4.2):** the language is now an input to question generation, so it
must be **immutable per card**. It cannot live only on `problem_attempts`, whose
`(user_id, problem_id)` upsert would silently rewrite an existing card's language on a re-solve.

**Consequence for the product:** language becomes a review dimension. Switching Python → Go for
interview prep should keep every concept card intact and regenerate only the implementation
questions. That is a genuinely differentiated feature and it falls out of this design for free —
worth a BACKLOG line, not this build.

---

## 4. Schema — two nullable columns, one migration

`down_revision` = current head. **Run `alembic history` — do not assume.** Note there is an
uncommitted migration in the tree (`a3f8c1d92b47_drop_attached_roadmap_node_meta.py`); rebase on
whatever is actually head at implementation time.

### 4.1 `activities.problem_id`

```python
problem_id: Optional[uuid.UUID] = Field(default=None, foreign_key="problems.id")
```

Mirrors the existing `node_id` / `concept_card_id` nullable-FK pattern. This is the link that
makes problem-aware question generation possible; without it the card knows its concept but not
which problem produced it, and the pattern questions in §7 lose their anchor.

> `activities` → `problems` is a user-data → bulk-rebuildable-catalog FK, the exact shape that
> caused **D-039**. Use `ondelete="SET NULL"`, **not** CASCADE: a catalog re-import must never be
> able to delete a user's card. Add a BACKLOG line to confirm `activities` is covered by the
> `no_truncate_*` guard set.

### 4.2 `activities.language` (+ `problem_attempts.language`)

```python
# activities — the language THIS card was captured in. Immutable. Feeds question generation.
language: Optional[str] = None   # 'python' | 'java' | 'cpp' | … ; NULL = not stated
# problem_attempts — the language last used for this problem. Overwritten on re-solve.
language: Optional[str] = None
```

Both, and the duplication is deliberate: they answer different questions. `activities.language`
is *"what these questions were written against"* and must never change under an existing card
(§3). `problem_attempts.language` is *"what I'd reach for now"* and is exactly the thing that
should be overwritten by the `(user_id, problem_id)` upsert.

If only one ships, it must be `activities.language` — question generation depends on it.

Stored as a slug from a closed list — free text produces `C++` / `cpp` / `Cpp` / `c plus plus`
within a week, the same landfill argument as `SPEC-leetcode-retention.md` §2:

```
python java cpp c javascript typescript go rust csharp kotlin swift ruby scala php
```

Validate server-side against the list; unknown value → 400, not silent NULL.

No RLS work: both tables already have it (§0).

---

## 5. Search — routes and ranking

### 5.1 Routes (`api/routes/problems.py`, existing router)

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/problems/search?q=&limit=8` | Typeahead. Returns ranked matches with the resolved concept |
| `GET` | `/api/problems/suggest?limit=5` | **Empty-box recommendations** (§5.3) |

Response row:

```json
{ "id": "…", "external_id": 1, "title": "Two Sum", "slug": "two-sum",
  "difficulty": "easy", "url": "…", "paid_only": false,
  "node_id": "…", "node_title": "Hash Tables", "confidence_band": "high",
  "already_logged": false }
```

`node_id` / `node_title` come from the `role='primary'` mapping; **null when unmapped** (§4.3
below). `already_logged` is the caller's `problem_attempts` row — user-scoped, so `search` needs
`get_current_user`, while the catalog half is a shared read. `suggest` is auth-required.

Both are read-only over a shared catalog; there is nothing to own-check on `problems`. The IDOR
surface is `already_logged` and `suggest` — **test that B's suggestions never reflect A's marks.**

### 5.2 Ranking — deterministic tiers, personalization strictly inside a tier

LeetCode's own box does number-first, then title. Match that:

```
q is all digits           → tier 100  exact external_id
                            tier 60   title contains the digits (e.g. "3sum" for q=3)
otherwise (case-insens.)  → tier 100  title equals q
                            tier 80   title starts with q
                            tier 70   any title word starts with q
                            tier 50   title contains q
                            tier 40   slug contains q
```

Sort by `(tier DESC, personal_boost DESC, external_id ASC)`.

**The boost may only reorder within a tier — never across.** A "smart" search that pushes a
substring hit above the exact number you typed is broken, and it is the failure users notice
first. `external_id ASC` as the final tie-break puts the older, canonical problems first, which
is almost always what someone typing a partial title means.

Personal boost signals (each additive, all cheap):

| Signal | Boost |
|---|---|
| primary node is in the user's active career-goal tree | +15 |
| primary node's `node_mastery` is low / unexposed | +10 |
| primary node touched in `learning_events` in the last 7 days | +8 |
| already has a `problem_attempts` row | **−20**, and still shown, labelled *Logged* |

Never *filter* on any of these. Hiding a problem the user explicitly typed the name of is worse
than ranking it fifth.

**Performance:** 3,999 rows. A sequential scan with `ILIKE` is ~1–2 ms. **Ship no index and do
not install `pg_trgm`** (it is not currently installed — verified §0). Revisit only when a real
typo miss is observed in use; a trigram index on a 4k-row table is premature, and a Supabase
extension migration is real risk for no measured gain. Escape `%` and `_` in `q` before
interpolating into the `LIKE` pattern.

**Client:** 150 ms debounce, abort the in-flight request on each keystroke (`AbortController`),
minimum 1 char for digits / 2 for text, cap at 8 rows. Keyboard: ↑ ↓ Enter Esc, and proper
`role="combobox"` / `aria-activedescendant` — this is a form control, not a div soup.

### 5.3 The empty box is where the recommendation actually lives

"Predict what the user is trying to input" is mostly *not* a string-matching problem. Before a
single character is typed, we already know a lot: what their career goal is, which DSA nodes are
weak, what they studied this week. So on focus-with-empty-query, show 5 suggestions:

> **Because Sliding Window is your weakest mapped concept** — 3. Longest Substring Without
> Repeating Characters · Medium

Each suggestion carries its *reason string*. A recommendation the user can't audit is a
recommendation they won't trust, and the reason is free — it is the boost rule that produced it.
Fall back to the `dsa` roadmap's canonical easy problems for a cold user.

---

## 6. Trusting the mapping — banded, per the §13 measurement

The concern in the first draft of this doc ("nobody has looked at the mapping") is **discharged
by the §13 spot-check**. Classification is not the hard part; the existing tail is the artifact of
a weak model, and the confidence bands turn out to track quality closely. So:

| Band | Rows | Measured | UI behaviour |
|---|---|---|---|
| **0.9** | 2,120 (72%) | ~12/14 clearly right, 0 wrong | **Auto-fill, no gate.** Overridable, but no confirmation tap |
| **0.6** | 696 (24%) | ~6/10 right, 2 wrong | Auto-fill, **require an explicit confirm tap** on the chip |
| **0.3** | 128 (4%) | ~2/8 right — noise, as labelled | **Do not auto-fill.** Show candidates, user picks |

The correction path stays, but as a **quality ratchet, not a gate**: the resolved-concept chip is
editable, and an override writes the corrected row with `reviewed_by='human'` + a bumped
`mapping_version` (`SPEC-leetcode-retention.md` §3.2.1 — "why did mastery move?" must stay
answerable). It no longer blocks anything.

> **One user's override edits a shared catalog table.** Fine at n=1, wrong at n=100. Ship the
> shared write now; BACKLOG line: *before the second user, corrections become proposals the owner
> promotes.* Do not discover this in production.

### 6.1 Fix the 66 scaffold primaries first — it is a SQL check, not a curation project

`content/PROMPT-leetcode-mapping.md:120` lists 26 **teaching-scaffold** slugs that are illegal as
`primary` ("Choosing one is always wrong; if nothing else fits, the answer is `out_of_scope`").
**66 primary rows violate it**, 28 at confidence 0.9 — i.e. inside the band this doc just decided
to auto-fill without a gate. Worst offenders: *String traversal* (26), *Arrays & memory* (18),
*Brute force first* (6), *In-place operations* (5).

This is why #418 Sentence Screen Fitting maps to "String traversal" and #326 Power of Three maps
to "Base case" — the model dumped implementation-heavy problems onto scaffold nodes, exactly the
failure `content/HANDOFF-leetcode-mapping-run.md` predicted and banned.

Two things, both cheap:

1. **Re-classify those 66** against the legal 98-slug vocabulary (or mark them unmapped). ~66 items.
2. **Add the check as an import gate** in `backend/scripts/import_leetcode_catalog.py` and as a
   backend test: *zero `role='primary'` rows may point at a scaffold node.* A contract the prompt
   states but nothing enforces will be violated again on the next run.

### 6.2 The tail — correcting an earlier claim in this doc

An earlier revision of this section said the tail was the artifact of a weak model
(gemini-3.5-flash-lite) and that a re-run on a stronger one would fix it. **That was wrong, and
it came from reading the handoff narrative instead of the artifact.** `mapping.v1.json` records
`"model": "gemini-3.1-pro"`. The flash-lite figure in `HANDOFF-leetcode-mapping-run.md` refers to
an earlier *diagnostic* run that was explicitly discarded.

What the §13 audit actually shows is that v1's confidence labels are **well calibrated** — the
model knew which rows it had got right. So the tail is not misclassification waiting to be fixed
by a better model; a straight re-run is likely to reproduce it. The residual causes are
structural:

- problems with no legal `primary` at all (implementation/simulation — 26 of the 66 scaffold
  violations were exactly this, §6.1);
- problems with two genuinely co-equal approaches, where the one-`primary` rule is the binding
  constraint (`SPEC-leetcode-retention.md` §10 lists this as open);
- thin input — v1 classified from title + tags only.

`content/HANDOFF-leetcode-mapping-rerun.md` is written accordingly: a **stricter protocol** over
the 797 medium/low rows, and it treats "agreement with v1 is high" as a valid result that should
stop the work rather than a failure to paper over.

**Status 2026-07-30: measured.** Pass 2 was rejected — it was a passthrough of v1 with the golden
answers hardcoded, and it fooled every structural check
(`content/leetcode-catalog/REJECTED-mapping.v2-tail.md`). Pass 3 re-ran it against a blinded work
set (`tail-work-set.blind.json`, no prior assignment included) and was verified independently
before acceptance — 0% reason-copying from v1, 53.5% agreement with the withheld v1 mapping
(not the ~99% a passthrough would show), 68.8% on a withheld golden subset with 5 genuine
disagreements (not the 100% a lookup table would show). Result:
**the tail was mostly misclassified, not genuinely ambiguous.**

One known gap, accepted deliberately: 37 of 797 rows (the newest/highest-ID problems) hit a
rushed end-of-batch fallback rather than real judgment, and were left `out_of_scope` at `low`
confidence rather than re-run — the safe direction (unmapped, not wrongly mapped). Full detail
and the exact ID list: `content/leetcode-catalog/mapping.v3-tail.NOTES.md`.

**Not yet wired in:** `backend/scripts/import_leetcode_catalog.py` still reads
`mapping.v1.json` only. Importing `mapping.v3-tail.json`'s corrections is a follow-up.

None of this blocks the build. The high band alone covers 2,121 mapped problems (73%) and is what
the UI ships against.

### 4.3 (referenced above) Unmapped problems

~1,055 catalog problems have no `problem_concepts` row — the JS/pandas study-plan sets and
long-tail. They still appear in search (they are real problems the user may have solved), with
`node_id: null`. On select: no concept chip, and an honest line — *"No concept mapped yet — this
will be logged, but reviewed as a plain note."* The card is created with `node_id = NULL`, which
means the existing `reviews.py` path records `evidence_unmapped` and moves no mastery. That is
already built and already correct; do not special-case it.

---

## 7. The questions — concept and pattern, without a card bank

`concept_cards` has **0 rows**, so nothing here may depend on it. It doesn't need to: the
existing `generate_question_items()` in `services/grader.py` already takes
`node_title` + `node_description` and generates **topic-grounded** questions, and `reviews.py:343`
already calls it that way whenever `activity.node_id` is set.

**So the concept half works the day `node_id` is populated.** That is the whole architectural
payoff of §1 — one FK, and the review loop starts asking about Hash Tables instead of about
whatever the user typed.

The **pattern** half needs one small, additive grader change: a new optional block passed only
for problem-linked cards.

```python
# generate_question_items(..., problem_context: Optional[ProblemContext] = None)
ProblemContext = { problem_title, primary_node_title, alternative_node_titles: [str], language: str|None }
```

`alternative_node_titles` comes free from the 422 existing `role='alternative'` rows — these are
the genuinely multi-approach problems, and per `SPEC-leetcode-retention.md` §3.2.-1 they are the
best transfer-question material in the system.

Prompt contract additions (`_QGEN_SET_SYSTEM_PROMPT`, or a sibling constant — do not silently
change the shared one and regress non-LeetCode cards):

1. **Never restate, quote, or paraphrase the problem statement.** We hold title and number only,
   by design (`SPEC-leetcode-retention.md` §1 — copyright, and we are not a problem browser).
   The title is a *label*, not content to quiz on.
2. **Language questions are about semantics and complexity, never syntax lookup** (§3). If the
   answer is a one-line docs lookup, it is not a question.
3. Only emit a language question when `language` is set. `NULL` → fall back to an extra
   complexity/transfer question. Never guess the language.

Question mix:

| Depth | Questions |
|---|---|
| `main` (3) | 1 **concept** (why the pattern works) · 1 **trigger** (what in a problem signals this pattern) · 1 **implementation**, in the card's language |
| `deep` (5) | + 1 **complexity/transfer** (the `alternative` approaches) · 1 **edge case or discriminating** question vs. a confusable concept |

Two of these are things no other DSA resource asks. The **trigger** question is the one that
decides interview performance — recognising the pattern is the whole game, and it is unanswerable
from a node description alone, which is what makes `problem_context` worth the change. The
**implementation** question is the axis every language-agnostic course drops (§3), and per the
review-dimension note there, it is also what makes a language switch a first-class feature later.

Cost: unchanged — two LLM calls per question set, already amortized by `QuestionSet` persistence.
If `GRADER_ENABLED` is false the card degrades to the plain key-memory review, exactly as today.

---

## 8. Frontend notes (`LogActivity.jsx`)

- Reuse existing color classes → dark mode is free (`CLAUDE.md`). No new palette.
- Track **fetch failure separately from emptiness** (the post-2026-07-24 `Home.jsx` pattern):
  "Couldn't reach the catalog" and "no problem matches *xyzzy*" are different screens, and the
  second one needs a "log it as a plain topic instead" escape hatch.
- The combobox must be usable with the keyboard alone, and the dropdown must not trap focus.
- Guests: the form is explorable today via `optionalAuth`. Search can stay `optionalAuth`
  (catalog is public) but `suggest` and `already_logged` require auth — degrade, don't error.

---

## 9. Tests

Backend (`tests/test_problems_search.py`):

- `q="1"` ranks *1. Two Sum* first; `q="two sum"` ranks it first; `q="trapping"` finds 42.
- Tier dominance: a personal boost never lifts a tier-50 hit above a tier-100 hit.
- `%`/`_` in `q` are escaped, not treated as wildcards.
- Unmapped problem returns `node_id: null` and is still returned.
- IDOR: B's `already_logged` and `suggest` never reflect A's `problem_attempts`.
- Invalid `language` → 400.

The two load-bearing ones:

- **Logging a LeetCode activity creates NO `learning_event` and moves NO `node_mastery`** (§1).
- **Completing the review of that card DOES create a `RECALL_GRADED` / `T2_verified_internal`
  event on the resolved node** — the other half of §1, and the thing that makes the feature
  worth building.

Plus: a low-band (0.3) problem does not auto-fill a concept; an override writes
`reviewed_by='human'`.

Baseline is 355 backend tests (`IMPLEMENTATION-problem-capture.md`). Do not finish with fewer.

---

## 10. Build order

0. **Scaffold-primary fix (§6.1)** — re-map the 66 illegal rows + add the import gate and the test. Independent of everything below, and 28 of them sit in the band step 5 auto-fills unattended.
1. Migration: `activities.problem_id` (SET NULL), `activities.language`, `problem_attempts.language`. `alembic history` first. **Do not upgrade prod.**
2. `GET /api/problems/search` + ranking + tests. Ship this alone and exercise it via `/docs` — the ranking is the part most likely to feel wrong, and it is cheapest to fix before any UI exists.
3. `POST /api/activities/` accepts `problem_id` + `language`; resolves primary node → `node_id`; upserts `problem_attempts`. Tests §9.
4. `GET /api/problems/suggest` (§5.3).
5. `LogActivity.jsx`: mode switch, combobox, language, concept chip. Live browser check, console clean.
6. Concept-override write path (§6).
7. `pattern_context` in the grader (§7) — last, because everything above is useful without it.
8. Docs in the same commit: SYSTEM-OVERVIEW (§1 routes, §2 the new columns, changelog), DECISIONS (**D-0xx — the solve claim is not evidence, the recall is; why not `T4_claimed`**), BACKLOG (shared-mapping override at n>1; `activities` truncate-guard coverage; **language-switch regenerates implementation questions only, §3**).

**Do not push.**

---

## 11. Pushback and open questions

1. ~~The mapping is machine-generated and nobody has looked at it.~~ **Discharged — measured, see
   §13.** The 0.9 band (72% of rows) is trustworthy; the residual work is the 66 scaffold
   violations (§6.1) and an ~800-row re-run of the tail (§6.2). Neither blocks the build.
2. **Four DSA roadmaps, one mapped** (§0). Worth deciding separately whether `dsa-striver` /
   `neetcode-150` / `blind-75` nodes should share the `dsa` mappings, or whether having four
   parallel DSA trees is itself the problem. Not this doc's call, but this feature makes the
   inconsistency user-visible for the first time.
3. **Difficulty means two things.** The form's 1–5 "Session Difficulty" is the FSRS input;
   LeetCode's easy/medium/hard is a property of the problem. Showing both on one screen without
   distinct labels will produce garbage self-ratings. Label the form field
   *"How hard was it **for you**?"* in LeetCode mode.
4. Should logging a problem the user has already logged offer to *update* the existing card
   rather than create a second one? The lesson-card path already solved this shape
   (`_find_lesson_card`, one card per `(user, node)`). Probably yes, keyed on
   `(user, problem_id)` — but re-solving a problem months later is genuinely new evidence, so
   this is a product call, not the implementer's.
5. `problem_attempts` was speced (`IMPLEMENTATION-problem-capture.md`) as the *manual mark in the
   roadmap view*, and this feature writes it from a second place. Confirm the roadmap checkbox and
   the log form stay consistent — logging here should tick the box there.

---

## 12. Adjacent bug found while reading (not part of this change)

`LogActivity.jsx:12` offers **`self_learn`** ("Self Learning (sites / LLMs / RetainHQ)") in the
Source Type dropdown, but `backend/app/schemas/activity.py:6`
`VALID_SOURCES = Literal["problem","lecture","video","book","article","course","project","lesson","other"]`
does **not** include it. Selecting that option and submitting should 422.

Prod `activities.source_type` is `lecture` ×1 and `NULL` ×1 — nobody has hit it yet, which is why
it is still there. One-line fix (add `self_learn` to the Literal), but it wants its own commit and
a test, not a smuggled ride on this feature.

---

## 13. Appendix — the mapping spot-check (2026-07-30)

**Method.** 32 `role='primary'` mappings pulled from prod, stratified across the three confidence
bands, sampled deterministically (`ORDER BY md5(id)`) so the draw is not cherry-picked. Each judged
against the problem title + LeetCode's own tags, asking *"is this the concept a teacher would say
this problem is for?"* — not *"is it defensible?"*.

**Caveat, stated because it matters:** this is one frontier model auditing another's output, n=32,
by me and not by the owner. It is a smoke test that shifts a decision, not a validation run. The
owner-reviewed `content/leetcode-catalog/golden.json` remains the only real ground truth, and the
§6.2 re-run should be graded against it, never self-graded (`HANDOFF-leetcode-mapping-run.md`
rule 3).

| Band | n | Clearly right | Defensible | Wrong |
|---|---|---|---|---|
| 0.9 | 14 | 12 | 2 | **0** |
| 0.6 | 10 | 6 | 2 | 2 |
| 0.3 | 8 | ~2 | 2 | ~4 |

**Findings**

- **The bands are well calibrated.** That is the load-bearing result: the classifier knew what it
  didn't know. 0.9 can drive the UI unattended.
- 0.9 hits are strong and often non-obvious — #3768 *Minimum Inversion Count* → Fenwick tree,
  #3430 → Monotonic stack, #3376 → Bitmask DP, #992 → Sliding window (variable). This is not
  tag-echoing; #3768 is tagged `segment-tree` and the mapping picked BIT anyway.
- The two 0.9 "defensible" calls are #1361 *Validate Binary Tree Nodes* → Union-Find (LeetCode
  tags it, but the canonical solve is indegree + traversal) and #2981 → Binary search on the
  answer (counting is more canonical). Both are legitimate approaches, neither is the teaching
  choice — a distinction worth nothing to a learner and everything to a curator.
- The 0.6/0.3 failures are the interesting ones because they are all the *same* failure: reaching
  for a heavyweight technique on a light problem (#1967, a trivial substring check, → Pattern
  matching (KMP)), or dumping onto scaffold (#326 *Power of Three* → Base case, #418 → String
  traversal). Both modes are detectable without human review — the second one entirely by SQL
  (§6.1).

**Conclusion.** DSA classification is not the hard problem — the high band proves that. But the
tail is **not** explained away by model weakness: v1 was `gemini-3.1-pro` (§6.2 corrects an
earlier claim in this doc that said otherwise). Well-calibrated confidence plus a bad tail means
the residue is structurally hard — homeless problems and genuine two-answer cases — not
mislabelled. Ship against the high band; the 66 scaffold rows are fixed; treat the 797 as a
measurement (`HANDOFF-leetcode-mapping-rerun.md`), not a defect queue.
