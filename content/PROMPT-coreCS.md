# Core CS lesson generation — PROMPT (theory: OS / DBMS / Networks)

> **North star (same as the rest):** *"Can the learner explain this in an interview 30 days later?"*
> Core CS is **conceptual** — no code to run, no formula to drill. The lesson teaches **understanding
> via analogy + a plain explanation**, then locks it in with recall. Retention is the engine's job;
> lessons stay tight. Do NOT write a textbook chapter — write the version that makes it *click*.

You generate **one JSON per node** for the `core-cs` roadmap, `kind: "theory"`. Topics + slugs are
in `content/_TODO-coreCS.md`. Validate with `python content/validate.py` (theory branch). Write to
`content/roadmaps/core-cs/<slug>.json` (filename = slug).

---

## THE TEMPLATE (field order = teaching order)
| # | Field | Required? | What it is |
|---|---|---|---|
| 1 | `hook` | optional | A concrete scene where this concept bites (a server thrashing, an app deadlocking). Skip if forced. |
| 2 | `mental_model` | **REQUIRED** | The **analogy** that makes it click. *"A deadlock is 4 cars at a 4-way stop, each waiting for the one to its right." "A semaphore is a bowl of restaurant buzzers." "An index is a book's index — jump, don't scan."* `intuition` = the one-liner; `description` = expand the analogy. |
| 3 | `explanation` | **REQUIRED** | The concept, explained plainly — what it is, how it works, why it exists. A few short paragraphs (blank-line separated). This is the meat. Precise but not a textbook dump. |
| 4 | `key_points` | optional | The component breakdown as `[{title, detail}]` — e.g. ACID → 4 points; TCP handshake → SYN / SYN-ACK / ACK; deadlock → the 4 necessary conditions. Use when the concept HAS discrete parts. |
| — | `common_mistakes` | **REQUIRED, ≥1** | The classic **misconception** (e.g. "mutex == semaphore"; "paging == segmentation"; "TCP is faster than UDP"). |
| 5 | `recall_questions` | **REQUIRED, ≥3** | The kind an interviewer asks. tier1 = state it, tier2 = apply/compare. Feeds the review engine. |
| 6 | `oa_questions` | **REQUIRED, ≥2** | Real interview/OA questions ("What happens when you type a URL?", "Difference between process and thread?") with `company` + an `approach`/`answer` outline. |

**No `code_walkthrough`, no `formula`, no `method`, no `pattern_discovery`, no `playground`.**
A diagram-in-words belongs inside `explanation` or `mental_model.description`.

---

## JSON shape (emit exactly these fields, in order)
```json
{
  "slug": "deadlock-conditions",
  "title": "Deadlock & the 4 Necessary Conditions",
  "roadmap": "core-cs",
  "kind": "theory",
  "tier": "tier1",
  "metadata": {
    "difficulty": "medium",
    "estimated_minutes": 12,
    "importance": 8,
    "interview_frequency": "high",
    "prerequisites": ["process-vs-program"],
    "unlocks": ["deadlock-prevention"],
    "appears_in": ["Core CS OA", "SDE interview"]
  },
  "hook": {
    "scenario": "Two threads each grab one lock, then each waits forever for the lock the other holds. The program just... stops.",
    "question": "What exactly has to be true for this freeze to be possible — and which one condition is easiest to break?"
  },
  "mental_model": {
    "intuition": "A deadlock is four cars at a 4-way stop, each waiting for the car on its right to go first.",
    "description": "Nobody is broken; everyone is just politely waiting on someone who is also waiting. The system is alive but frozen. Break any single link in the waiting cycle and traffic flows again."
  },
  "explanation": "A deadlock is a state where a set of processes are each blocked waiting for a resource held by another process in the same set, so none can ever proceed.\n\nIt can only arise if FOUR conditions hold simultaneously (Coffman conditions). Remove any one and deadlock becomes impossible — which is exactly how prevention works.",
  "key_points": [
    { "title": "Mutual exclusion", "detail": "At least one resource is held in a non-shareable mode — only one process can use it at a time." },
    { "title": "Hold and wait", "detail": "A process holding at least one resource is waiting to acquire more held by others." },
    { "title": "No preemption", "detail": "A resource can't be forcibly taken; it's released only voluntarily." },
    { "title": "Circular wait", "detail": "A closed chain of processes exists, each waiting for a resource the next one holds." }
  ],
  "common_mistakes": [
    { "title": "Confusing deadlock with starvation", "explanation": "Deadlock = a cycle where everyone is stuck forever. Starvation = one process keeps getting passed over but the system as a whole progresses." },
    { "title": "Thinking all four conditions are independent", "explanation": "They must hold AT ONCE. Prevention works by making just ONE impossible (usually circular wait, via resource ordering)." }
  ],
  "recall_questions": [
    { "q": "Name the four necessary conditions for deadlock.", "answer": "Mutual exclusion, hold-and-wait, no preemption, circular wait.", "tier": "tier1" },
    { "q": "Why does breaking circular wait prevent deadlock?", "answer": "Imposing a global ordering on resource acquisition makes a closed waiting cycle impossible, so the 4th condition can never hold.", "tier": "tier2" },
    { "q": "Deadlock vs starvation — one-line difference?", "answer": "Deadlock freezes a whole set forever; starvation indefinitely delays one process while others proceed.", "tier": "tier1" }
  ],
  "oa_questions": [
    { "question": "How would you prevent deadlock in a system with multiple locks?", "company": "SDE interview", "answer": "Impose a global lock-acquisition order (break circular wait), or use lock-free structures / try-lock with backoff.", "approach": "Tie the answer to breaking ONE Coffman condition — ordering kills circular wait; that's the cleanest, most common real-world fix." }
  ],
  "sources": ["https://www.geeksforgeeks.org/introduction-of-deadlock-in-operating-system/"]
}
```

## Topic notes
- **DBMS — SKIP the SQL-overlap nodes** (joins, GROUP BY/HAVING, subqueries, normalization drills,
  keys, indexing mechanics): those are taught with a real runtime in the `sql` roadmap — don't make
  inferior no-runtime copies. Build only the genuine theory (3-schema, ER model, relational algebra,
  ACID, serializability, 2PL, recovery, B-tree structure). The TODO marks which to skip.
- **OS / Networks** — lean hard on `mental_model` analogies; these are where understanding beats
  memorization (scheduling, paging, TCP handshake, subnetting).
- **`company` tags = honest categories** (Core CS OA / SDE interview / service-co OA), never fabricated.

## Quality bar
- Does `mental_model` make the concept feel **obvious**? If the analogy is generic ("it's like a
  manager"), sharpen it.
- Is `explanation` **tight** (a few paragraphs), not a textbook section?
- Are `recall_questions` what an **interviewer** actually asks?
- Blank-line-separate paragraphs in `explanation`; single quotes inside strings so they nest in JSON.
