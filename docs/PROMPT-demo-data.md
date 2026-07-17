# PROMPT — Pitch Demo Data (Priority 2)

**Status:** DRAFT session prompt, 2026-07-16. Nothing implemented.
**Goal:** every screen shown in the school pitch lights up with realistic data. Today all 5 analytics endpoints (and the future teacher gap map) have honest `enough_data` floors — a fresh account in front of a principal shows empty states everywhere, which undermines the exact "we pinpoint gaps" claim being pitched.
**Companions:** `SPEC-teacher-dashboard.md` §8 Phase-0 item 5 (this is that item, plus the student-side demo), `PROMPT-physics-pitch-chapter.md` (the content the demo runs on).

---

## 1. What the demo must show working

Student side (exists today — must light up):
- Home dashboard: due queue, streak, consistency window.
- Analytics page: review-metrics (retention band), heatmap (~3-week streak texture), source-retention, calibration, memory-strength, node-accuracy ("your weakest concepts").
- Review flow: a due queue of Class-9-Motion cards ready to be demoed live.
- Tests section: prior attempts on the `class-9-motion` bank so per-node weights and the score screen have history.

Teacher side (once SPEC-teacher-dashboard Phase 0 lands):
- "Class 9-A Physics" classroom, ~12 members, gap map with a visible weak-column story, roster with 2–3 at-risk students.

## 2. Account strategy — one real login + synthetic cohort

- **1 real demo student account** — a founder-controlled Google account (e.g. `retainhq.demo.student@gmail.com`), signed up through the normal OAuth flow, `audience='school'`. This is the account you actually log into and drive live in the pitch (do a review, take a test question). Its data is seeded by the script below. Keep credentials in the password manager, never in the repo.
- **11 synthetic students** — raw `user_id` UUIDs with NO `auth.users` rows. All app tables key on bare `user_id` (no FK to auth), so seeded activities/reviews/test_attempts aggregate fine. Verified consequences of having no auth row: reminders skip them (the `auth.users` email join finds nothing — good, no ghost emails); they can't log in (fine — only the teacher dashboard reads them); the admin funnel may count them (acceptable, or filter by the namespace below).
- **1 real demo teacher account** — second founder-controlled Google account, owns the classroom (needed to log in and present the teacher dashboard). Phase-0-of-teacher-dashboard dependency; the student-side seed does not block on it.

**Namespace convention:** all synthetic UUIDs are generated as `uuid5(DEMO_NAMESPACE, f"student-{i}")` with a fixed `DEMO_NAMESPACE` UUID constant — deterministic (idempotent re-runs hit the same ids), recognizable, and one `DELETE ... WHERE user_id = ANY(:demo_ids)` away from a clean teardown.

## 3. Personas (assign across the 12)

| Persona | Count | Signature in the data |
|---|---|---|
| **Strong** (e.g. "Ananya") | 3 | 90% recall, mostly `easy`/`medium` ratings, stability 10–30d, near-daily streak, test accuracy ≥0.85 everywhere, zero overdue |
| **Average** (e.g. "Rohan") | 6 | 65–75% recall, mixed ratings, stability 3–12d, reviews 4–5 days/week, weak on exactly 2–3 specific nodes (see §4), a few overdue |
| **Struggling / at-risk** (e.g. "Priya") | 3 | 40–50% recall, `hard` dominant, stability <5d, went inactive 8–10 days ago (trips the at-risk flag), test accuracy <0.5 on the weak-column nodes, 15+ overdue |

The **real demo student = one of the "average" personas** — average demos best live: some green, some red, a due queue that isn't demoralizing.

**The scripted story the data must encode** (this is what gets narrated in the room): the class is solid on *Distance vs Displacement*, split on *Velocity-Time Graphs*, and **weak as a group on the Equations-of-Motion cluster** — with the prerequisite edge pointing at *Acceleration* as the root cause. Choose actual node titles from the live `physics-9-10` roadmap (Class 9 · Motion phase) and the `_test/class-9-motion.json` bank at implementation time; the story shape is the requirement, the titles are looked up.

## 4. Data-realism requirements (the hard part — the seed must survive scrutiny of every aggregate)

The seed writes `activities`, `reviews`, `test_attempts`, `user_prefs`, `user_progress` for each persona over a **21-day window ending yesterday**. Every generated row must be internally consistent, because the analytics endpoints will cross-examine them:

1. **FSRS coherence:** don't hand-write `stability`/`difficulty_fsrs` — replay history through `services/scheduler.apply_fsrs` (import it in the seed) so card state, `interval_days`, `next_review_at`, and the completed-review sequence are exactly what the real engine would produce. Hand-rolled numbers will contradict the memory-strength buckets.
2. **Review invariants:** the partial unique indexes (migration `e7f2a4c9b1d5`) allow at most one open `due` review per activity — end each card's replay with exactly one due row (or none). `completed_at` strictly after `scheduled_for` minus small jitter; `duration_ms` in a plausible 20s–4min band (feeds time-of-day avg-duration).
3. **Per-endpoint floors** (per persona, or the screen goes blank): ≥5 completed reviews (`review-metrics`, `calibration`, `time-of-day`); ≥3 completed reviews per `source_type` group with ≥2 groups (`source-retention` — give school students `lesson` + `other`); ≥5 activities with non-NULL stability (`memory-strength`); ≥2 test-question results per node for ≥4 nodes (`node-accuracy`).
4. **Calibration needs AI columns:** set `ai_recalled`/`ai_verdict` on ~70% of completed reviews, agreeing with `recalled` ~80% of the time for strong, ~60% for struggling (the "overconfident" cell should be non-zero for the struggling personas — it demos well).
5. **Timestamp texture:** reviews clustered 15:00–17:00 IST (09:30–11:30 UTC) on school days with jitter, so time-of-day shows a believable after-school peak; heatmap should show weekday density and the struggling personas' 8-day gap.
6. **Test attempts:** results arrays must use real `question_id`/`node_title`/`type` values from `content/roadmaps/physics-9-10/_test/class-9-motion.json`; outcomes per persona per §3; 2–3 attempts each, scores trending slightly up for average personas (growth demos well).
7. **`user_progress`:** mark done/in-progress consistent with which nodes each persona has cards+tests on.

## 5. Script mechanics & safety

- Lives at `backend/seed_demo_data.py` (matches the 33 existing seed scripts' home; it's a permanent pitch asset, not a scratch one-off).
- **Implemented as (as of 2026-07-16, `backend/seed_classroom_demo.py`):** idempotent upsert-by-default (`ON CONFLICT DO NOTHING`/`DO UPDATE`, never a bare delete) — row ids are `uuid5` hashes of a stable **slot** key (student name, or a fixed `"real-student"` marker for whichever slot `DEMO_STUDENT_USER_ID` currently fills), never of the live UUID itself, so switching a slot from synthetic to real can never collide with or silently skip the other's rows. Refreshing already-seeded rows (e.g. after a persona/logic change to this script) is an **opt-in** `RESET_SYNTHETIC_DEMO=1` env flag that deletes only the fixed set of synthetic ids (`activities` — cascades `reviews` via `ondelete=CASCADE` — + `test_attempts` + `classroom_members`); it is mathematically incapable of touching a real account, since a `uuid5` of the seed namespace can never collide with a real Supabase auth id. Real accounts are wired via `DEMO_STUDENT_USER_ID` / `DEMO_TEACHER_USER_ID` env vars — both go through a freshness guard (`_assert_fresh_account`) that refuses to run if the given id already has activity/review/test-attempt history older than the demo window + a safety margin.
- Targets prod via the pooler `DATABASE_URL` like other seeds; founder runs it manually. Prints a summary (rows inserted/already-present) and raises on any invariant violation.
- **Verification step implemented:** `_verify_demo_student()` queries the DB directly (not through the service layer — simpler, no FastAPI dependency wiring needed) for each gated aggregate's exact floor (`REVIEW_METRICS_MIN`, `SOURCE_RETENTION_MIN`, `NODE_ACCURACY_MIN`, imported from the real modules, never hand-duplicated) and raises if any Analytics card would render empty. Only runs when `DEMO_STUDENT_USER_ID` is set — the synthetic-only cohort has no login to verify against.
- **Refresh cadence:** data ages — a heatmap whose last activity is 3 weeks old looks dead. Re-run the seed the day before any pitch (the 21-day window is relative to run time; a plain rerun without `RESET_SYNTHETIC_DEMO` will NOT advance the `days_ago`-relative timestamps on already-seeded rows, so a true refresh needs the reset flag). Add one line to the pitch-prep checklist.

## 6. Ethics line (so it never gets crossed under demo pressure)

Seeded personas are **presented as a demo/simulation**, never as real students or real efficacy results. The pitch line is "this is what your class will look like," not "this is a class using it." Efficacy claims wait for real pilot data (Oct, per the sales timeline).

## 7. Acceptance checklist

- [ ] Logged in as the demo student on retainhq.app: all 5 Analytics cards render numbers, heatmap shows ~3 weeks of texture, due queue has 5–10 cards, Tests page shows attempt history.
- [ ] Node-accuracy top-weak list matches the scripted story (Equations-of-Motion cluster).
- [ ] Re-running the script twice produces identical row counts (idempotency).
- [ ] `DELETE`-scope audit: script log lists only demo-namespace user_ids.
- [ ] (After teacher dashboard Phase 0) gap map shows the weak column + root-cause callout; roster shows 3 at-risk with reasons.
