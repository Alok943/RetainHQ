# RetainHQ — Hardening Plan (pre/post first-users)

Triage of the 22-point review, re-prioritized for the actual goal: **deploy to ~20 known users, validate the loop.** Numbers in brackets map to the original review. Each item: file → fix sketch → note.

Guiding cut: *security holes and deploy-config block launch; data-integrity races are cheap so do them; most scalability items are genuinely premature at 20 users and are deferred on purpose.*

---

## Tier 0 — Block deploy (security + must-work-in-prod)

- [ ] **[1] Remove `HS256` from the JWT allowlist** — `core/security.py:42`. Change `["ES256","RS256","HS256"]` → `["ES256"]` (Supabase JWKS issues ES256; add `RS256` only if a token actually needs it). **Confirmed live vuln**: the verify key is the JWKS *public* key, so HS256 enables an algorithm-confusion forgery. Also directly contradicts CLAUDE.md ("never use HS256"). One-line, highest priority.
- [ ] **[2] `echo=True` → off in prod** — `core/database.py:12`. Add `DEBUG: bool = False` to `config.py`, set `echo=settings.DEBUG`. Currently every SQL statement **+ params** (key_memory text, emails, user ids) streams to Render/Railway logs.
- [ ] **[7] Env-driven CORS allow-list** — `main.py:10`. Read a comma-separated `CORS_ORIGINS` from env; include the Vercel domain. Without this the deployed frontend can't call the API. **Deploy is broken until done.**
- [ ] **[4] Input length limits (DoS)** — `schemas/activity.py` (`ActivityCreate`) and `schemas/feedback.py` (`FeedbackCreate`). Add `Field(max_length=...)`: topic ~300, key_memory ~2000, notes ~5000, mistake ~2000, feedback message ~5000. Cheap, closes a 10 MB-per-row vector.
- [ ] **[3] Require `ADMIN_EMAIL` via env** — `config.py`. Drop the hardcoded default so it must come from env. (Note: the value is already in git history + CLAUDE.md + live data, so this only helps going forward — still worth it. Set it as a deploy env var.)

---

## Tier 1 — Cheap correctness (do around deploy)

- [ ] **[8] Double-completion race on reviews** — `api/routes/reviews.py` `complete_review`. The read-then-write `if review.status=="completed"` can let two concurrent requests both insert a next review (breaks "exactly one open `due` review/activity"). Fix: make it an atomic `UPDATE reviews SET status='completed', ... WHERE id=:id AND user_id=:uid AND status='due'` and check `rowcount`; only run `apply_sm2` + schedule-next when rowcount==1, else 400. (Or `SELECT ... FOR UPDATE` before the check.) Low real-world odds at this scale, but cheap and annoying to debug later.
- [ ] **[9]+[16] `user_progress` UNIQUE + indexes (one migration)** — add `CREATE UNIQUE INDEX ... ON user_progress(user_id, node_id)` and switch `set_node_progress` to `ON CONFLICT (user_id,node_id) DO UPDATE`. Same migration, add the two hot-path indexes: `reviews(user_id,status,scheduled_for)` and `activities(user_id,created_at DESC)`. The unique index is a real correctness fix (concurrent toggles double-count progress); the other two are cheap insurance.
- [ ] **[15] Cap `/reviews/due`** — `api/routes/reviews.py`. Add a `LIMIT` (e.g. 20) + return an "N more overdue" count. This is a real *single-user* scenario (3-week break → 200 overdue), not just scale.
- [ ] **[6] `source_type` → `Optional[Literal[...]]`** — `schemas/activity.py`. Constrain to the 8 known values. *(Reversing my earlier "plain string for flexibility" call — a Literal needs no migration to extend either, and unconstrained strings will pollute the by-source analytics with casing/typos. The frontend already sends a fixed set; enforce it server-side.)*
- [ ] **[17] Connection pool config** — `core/database.py`. Add `pool_size`, `max_overflow`, `pool_timeout` sized to your worker count so multiple Render workers don't exhaust the Supabase pooler. Set when you decide worker count at deploy.

---

## Tier 2 — Schema hygiene + cleanup (one migration + small edits)

- [ ] **[18]+[19] CHECK constraints** — Alembic migration: `reviews.status IN ('due','completed')`, `user_progress.status IN ('done','not_started')`, `activities.rating IN ('easy','medium','hard') OR NULL`, `feedbacks.status IN ('new','reviewed','resolved')`, `activities.ease_factor >= 1.3`. Defends the state machines against direct DB writes.
- [ ] **[12] Cap SM-2 interval** — `services/scheduler.py` `apply_sm2`: `interval_days = min(365, round(interval * ease_factor))`. Prevents 2-year intervals; decide later whether dormant cards leave rotation.
- [ ] **[11] Remove dead `daily_progress`** — `api/routes/dashboard.py` (~line 57): the first `daily_progress = sum(...)` is overwritten immediately. Delete it. Trivial.
- [ ] **[22] (optional) `public.user_summary` view** — wrap `auth.users` in a public view and have `admin.py` query that instead of crossing into the `auth` schema. Hardens against Supabase changing auth-schema perms; also limits exposed columns.

---

## Tier 3 — Deliberately deferred (premature for ~20 users)

Revisit when going public / scaling past the first cohort. The reviewer flags several of these as "invisible at low user count" — agreed.

- **[5] Rate limiting (slowapi)** — adds a dependency; the first cohort is ~20 known people. Defer until public signup.
- **[13] Pagination on `/api/activities/`** — fine until lists get long (hundreds of rows). Defer; the Vault loads instantly at this size.
- **[14] Dashboard 7-query → CTE** — pure optimization, invisible at low concurrency. Defer.
- **[10] `next_review_at` desync reconciliation** — theoretical (can't happen with current transactions). Note it; no job needed yet.
- **[21] `tier` CHECK in migration but not model** — cosmetic divergence; harmless because we always migrate via Alembic (never `create_all`). Low priority.

---

## Corrections / cautions (where the review needs nuance)

- **[20] `datetime.utcnow()` → DO NOT do a naive find-replace.** The whole codebase + DB columns are **consistently naive-UTC** (CLAUDE.md). Swapping some calls to `datetime.now(timezone.utc)` makes them *aware*, which then throws `can't compare offset-naive and offset-aware datetimes` against existing naive values. It's a **deprecation warning, not an error** today. Either (a) stay naive-UTC (fine for now), or (b) migrate *everything* — code + DB columns to `timestamptz` — in one deliberate pass. Don't half-do it. Defer; not deploy-blocking.
- **[16] "seq scans hurt first, at very low counts"** — slightly overstated; on tiny tables seq scans are fine. Still add the indexes (cheap), but treat as insurance, not urgent.
- **[3] admin email "now in git history"** — true, but it's already in git + CLAUDE.md + the live DB, so removing the default doesn't un-leak the current value; it just enforces env going forward.

---

## Suggested order

1. Tier 0 items 1, 2, 4 (one short PR — pure wins, no infra). 
2. Tier 0 items 3, 7 + Tier 1 [17] **together with the actual deploy** (they're env/deploy-coupled).
3. Tier 1 [8], [9]+[16], [15], [6] (correctness + one migration).
4. Tier 2 as a "schema hygiene" migration once the loop is validated.
5. Tier 3 only when scaling past the first cohort.
