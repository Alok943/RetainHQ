# Backlog — idea inbox

Raw, unprioritized capture. Mid-session "we should also…" ideas land here as **one line each**, and the session returns to its task. This is pre-triage: things graduate from here into `SYSTEM-OVERVIEW.md` §5 (plans) when actually prioritized — this file is never the roadmap.

Format: `- [ ] idea — one line of context (YYYY-MM-DD)`

## Product / features

- [ ] Node-mastery / per-node accuracy surfaced on the roadmap graph (color-coded), computed from Tests-section results — v1 deliberately computes this ad-hoc from `TestAttempt` scans instead of a dedicated table (SPEC-test-runtime.md non-goal) (2026-07-10)
- [ ] Tests-section score surfaced beyond the one-time completion screen (streaks/leaderboard/gamification) — `score`/`max_score` already computed and returned, just not displayed anywhere persistent (2026-07-10)
- [ ] School-audience nav: de-emphasize/hide the Log tab for `audience='school'` users — LogActivity's "source type: lecture/problem/course" framing doesn't fit a Class 9 student; their capture path is already "Add to reviews" on a lesson (2026-07-10)
- [ ] Make `key_memory` optional at log time — let the user log just the topic and have the LLM backfill the memory note, instead of requiring it upfront (explicit user ask, not built this session) (2026-07-05)
- [ ] Circuit and free-body 2D diagram renderers for physics lessons — `diagram.type: "circuit"/"free-body"` already has schema + membership-only validation, no renderer yet (2026-07-05)
- [ ] Retrofit `schematic`/`diagram3d` illustrations across the remaining ~120 physics lessons — only the 3-4 pitch-demo lessons got one; scoped as post-deal-only work (D-003) (2026-07-07)

## Tech debt / engineering

- [ ] (see also SYSTEM-OVERVIEW §5 for already-acknowledged debt: rate limiting, admin auth, feedback workflow)
- [ ] `Profile.jsx` calls raw `supabase.auth.getUser()` instead of `useAuth()`'s session — under `DEV_AUTH_BYPASS` (no real Supabase login happens) this never resolves, so the whole Profile page hangs on its loading skeleton forever in dev. Found verifying the audience-switcher redirect; not fixed, out of that session's scope (2026-07-10)
- [ ] Groq model upgrade path — currently `openai/gpt-oss-120b` (all 6 LLM endpoints); evaluate Kimi/GLM as alternatives. Raised by the founder, not evaluated (2026-07-05)
- [ ] Verify Railway builder (dashboard → service → Settings → Build, or build logs) — Dockerfile vs Nixpacks; if Dockerfile, one rebuild is needed for the new `.dockerignore` to purge old layers; also confirm no locally built image was ever pushed to a registry (closes/reopens the D-008 no-rotation call) (2026-07-10)
- [ ] Auth 401 responses echo JWT-library exception text (`detail=f"Could not validate credentials: {e}"`) — return a generic message, log the detail server-side (audit finding, deferred) (2026-07-10)
- [ ] `/health` doesn't touch the DB — Railway reports healthy while the pool is dead; add a cheap `SELECT 1` (audit finding, deferred) (2026-07-10)
- [ ] Security headers (CSP, HSTS, etc.) on the Vercel frontend via a `headers` block in `vercel.json` (audit finding, deferred) (2026-07-10)
- [ ] Move `alembic upgrade head` out of the container CMD into a separate release/pre-deploy step — concurrent replicas/redeploys race migrations; a failing migration crash-loops the API (audit finding, deferred post-pitch) (2026-07-10)
- [ ] Pin backend dependencies — `pyproject.toml` is all `>=` with no lockfile; `pip-compile` a pinned `requirements.txt` for the Docker build (audit finding, deferred post-pitch) (2026-07-10)
- [ ] `datetime.utcnow()` deprecation sweep → `datetime.now(datetime.UTC)` — 40 warnings in the test run; naive-UTC storage convention itself stays (audit finding, deferred) (2026-07-10)
- [ ] ~32 roadmap seeds still use the destructive `DELETE FROM roadmap_nodes … + re-INSERT with uuid.uuid4()` pattern — re-running any of them against a roadmap with live `user_progress` cascade-wipes it (ON DELETE CASCADE). Only `seed_python_swe.py` was converted to the progress-safe upsert (D-009); convert the rest — or at minimum any roadmap already in use — before ever re-running to add nodes (2026-07-10)
- [x] ~~DSA `valid-parentheses` generator array-input bug~~ — VERIFIED FIXED 2026-07-11: `generators/valid-parentheses.js:3` handles `Array.isArray(input)`, it's golden-tested in `stack-queue-family.golden.mjs`, registered in `registry.js`, and the lesson JSON has its `viz` block. The 2026-07-10 "still shows the bug" claim was itself a stale read (2026-07-11)
- [ ] Decide the semantics of the lesson `tier` field (tier1/2/3, shown as a colored badge in `LessonView`; no validator rule ties it to `difficulty`). It currently does NOT track `metadata.difficulty` — **189 of ~582 lessons diverge across every roadmap, including easy topics marked tier2/tier3** (`else-finally`, `slots`, `join-keys`…), so it reads as an independent "advanced-ness / importance" axis applied inconsistently, NOT a difficulty typo. Decide: (a) tier ≡ difficulty → mass-align all 189 + add a `validate.py` check; or (b) distinct axis → document it and leave values as authored. NOTE: this session pre-emptively forced 7 DSA lessons (backtracking ×5, lower/upper-bound) to tier=difficulty on the (b)-violating assumption — revert or keep pending this decision (2026-07-11)
- [ ] Browser-verify the `lower-bound`/`upper-bound` viz blocks added this session (validated + synced but never rendered; low risk — they reuse the already-golden-tested lower/upper-bound generators + `ArrayViz`) (2026-07-10)

## Content / roadmaps

- [ ] (roadmap-seed candidates are tracked in CLAUDE-ARCHIVE-2026-07.md "Roadmap backlog" + SYSTEM-OVERVIEW plans)
- [ ] python-swe: 40 of 148 nodes still have no lesson (108 now link). Gaps are almost all **Phase 5 Testing** (pytest, unittest.mock, black, ruff, mypy, pre-commit, pdb, cProfile) and **Phase 6 Engineering Practices** (git, project structure, design patterns) — never authored — plus a few Phase 3/4 nodes whose lesson exists under divergent wording (duck typing, multiple inheritance, property decorator, dataclasses-vs-pydantic, with-statement). Needs authoring/title-mapping, not a mechanical fix — Antigravity content pass candidate (2026-07-10)
- [ ] Apply the fix lists for the ~26-29 python-swe lessons still flagged NEEDS-WORK by the lesson-critic pass (duplicate recall/understanding-check questions, a fabricated `__req__` dunder in `operator-overloading.json`, missing variance discussion in `generic-types.json`, etc.) — found and reported but never actually applied (D-013) (2026-07-10)
- [ ] `shallow-vs-deep-copy.json` has 2 recall_questions truncated mid-sentence (cut off right at an em-dash, no continuation or `?`) — a botched prior fix for a mojibake-encoding defect that swapped one bug for a worse one; needs the questions properly completed (2026-07-10)
- [ ] Run the format-upgrade pass (bullets/backticks/edge-case flags, D-011/D-012) on the other 8 roadmaps — only `python-swe` got the pilot pass; rollout order + per-roadmap edge-flag guidance already specified in `content/PROMPT-format-upgrade.md` (2026-07-10)
- [ ] Run the lesson-critic sweep on the remaining major roadmaps — core-cs (61), aptitude (40), dsa (**51** — folder grew past the quoted 37); python-swe/sql/ai-engineering were swept + fixes applied per D-013. NOTE (2026-07-11 audit): the only report artifact on disk is `content/CRITIC-REPORT-dsa.md` — none exist for the three claimed-swept roadmaps, so "swept" rests on D-013's session record, not artifacts; and the dsa report suggests a partial dsa run already happened. Reconcile before re-running. Via Gemini-in-Antigravity (`content/RUN-lesson-critic-antigravity.md`, D-016) (2026-07-10)
- [ ] Java (`java-swe`) roadmap: add `equals()/hashCode()` contract + autoboxing/Integer-cache seed nodes (placement-critical, currently only implicit) before authoring; then generate the Step-1 pilot per `content/PROMPT-cpp.md` (D-014). C++ Step-1 pilot also not yet generated (only the gold exemplar `rule-of-3-5-0-...json` exists) (2026-07-10)

## Marketing / growth

- [ ] Reverse-engineer the school-pilot sales timeline into a dated plan: launch pilot Jul/Aug → pull mid-term efficacy data Oct → pitch the School Management Committee Dec, landing inside the Nov–Feb CBSE procurement window (from the deep-research pilot playbook; not yet turned into calendar dates) (2026-07-05)
