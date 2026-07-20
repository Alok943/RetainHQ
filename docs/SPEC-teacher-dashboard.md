# SPEC — Teacher-Facing Dashboard (Classrooms)

**Status:** DRAFT — design doc, nothing implemented. Written 2026-07-16.
**Why now:** the school pitch's core claim is "we pinpoint each student's exact gaps." The buyer is the school/teacher, and today there is zero teacher-facing surface — all analytics are self-serve per-student. This spec designs the classroom layer: per-student stats, class-wide gap visibility, and the supporting roster/join machinery.
**Companions:** `SYSTEM-OVERVIEW.md` (current state), `SPEC-test-runtime.md` (test attempts feed mastery), `school-b2b-research-findings.md` (pitch context).

---

## 1. Product shape

### Personas

- **Teacher** — owns one or more classrooms (e.g. "Class 9-A Physics"). Wants: who is behind, on exactly which concepts, and what to reteach. Checks weekly, before a test, and during parent meetings.
- **Student** — existing RetainHQ user (`audience='school'`). Joins a classroom with a code. Their normal app experience is unchanged; joining grants the teacher visibility into their *learning signals* (not their private notes — see §5 Privacy boundary).
- **Founder/admin** — unchanged (`get_admin_user`). NOT extended to see classrooms; teacher access is its own path.

### The three screens that carry the pitch

1. **Class Gap Map** — the money screen. Chapter × concept grid for the class: each node colored by the share of students weak on it. "Your class is solid on *Distance vs Displacement* but 60% are weak on *Equations of Motion* — and the prerequisite graph says the blocker is *Acceleration*." No competitor shows this.
2. **Roster** — one row per student: last active, reviews completed, recall rate, current streak, #weak concepts, at-risk flag. Sortable. This is "which 5 kids need me this week."
3. **Student drill-down** — one student's gap map + retention trend + test history. This is the parent-meeting / remediation screen, and it reuses the analytics endpoints that already exist (refactored to take a target user, §4.3).

### Explicit non-goals (v1)

- No school/organization entity, no multi-teacher classrooms, no admin hierarchy. One classroom = one teacher (its creator). A `school_name` text column keeps the door open.
- No teacher-driven content authoring or assignment engine (Phase 3 sketch only, §8).
- No separate teacher account type or signup flow. Any user can create a classroom and thereby *be* a teacher. Schools don't need gatekeeping here; visibility is gated by students consenting to join, not by who may create a class.
- No messaging/chat between teacher and student.
- Teachers do NOT get write access to anything student-owned. Read-only analytics, full stop.

---

## 2. Data model (3 new tables — all migrations MUST include `ENABLE ROW LEVEL SECURITY`, per convention)

```python
class Classroom(SQLModel, table=True):
    __tablename__ = "classrooms"
    id: uuid.UUID  # pk
    teacher_user_id: uuid.UUID          # indexed; the creator-owner
    name: str                           # "Class 9-A Physics" (max_length 120)
    school_name: Optional[str] = None   # free text for now (max_length 200)
    join_code: str                      # unique, indexed — 8 chars, unambiguous alphabet (no 0/O/1/I)
    archived_at: Optional[datetime] = None  # soft archive; hides from lists, keeps history
    created_at: datetime


class ClassroomMember(SQLModel, table=True):
    __tablename__ = "classroom_members"
    __table_args__ = (UniqueConstraint("classroom_id", "student_user_id", name="uq_class_student"),)
    id: uuid.UUID
    classroom_id: uuid.UUID   # FK classrooms.id, ondelete CASCADE
    student_user_id: uuid.UUID  # indexed
    # Roll-call name shown to the teacher. Captured at join (student types it, e.g.
    # "Priya Sharma, Roll 14") and editable by the teacher afterward. We do NOT
    # surface the student's Google account name/email to the teacher — see §5.
    display_name: str          # max_length 120
    joined_at: datetime


class ClassroomRoadmap(SQLModel, table=True):
    """Which catalog roadmaps (subjects/chapters) this classroom tracks. The gap
    map and all class aggregates are scoped to these — a teacher never sees
    signals from a student's personal/career roadmaps."""
    __tablename__ = "classroom_roadmaps"
    __table_args__ = (UniqueConstraint("classroom_id", "roadmap_id", name="uq_class_roadmap"),)
    id: uuid.UUID
    classroom_id: uuid.UUID  # FK classrooms.id, ondelete CASCADE
    roadmap_id: uuid.UUID    # FK roadmaps.id, ondelete CASCADE — catalog roadmaps only (user_id IS NULL)
```

Notes:
- **No `user_prefs.role` column.** "Is a teacher" == "owns ≥1 classroom". The frontend shows the Teach nav entry if `GET /api/classrooms/mine` is non-empty (plus an entry point to create the first one). Avoids a role system we'd have to migrate away from later.
- **No per-(student, node) mastery table in v1.** Mastery is computed ad-hoc from `test_attempts` + node-linked `activities`/`reviews` scans, same deliberate call as SPEC-test-runtime.md. Scaling path if class sizes × content make this slow: a `node_mastery` rollup table refreshed on write. Don't build it speculatively.
- One migration, three tables, RLS enabled on all (zero policies — the PostgREST-blocking pattern).

## 3. Mastery model — the one algorithm in this feature

Per (student, node), combine the two existing signal sources:

| Signal | Source | Join |
|---|---|---|
| Test outcomes | `test_attempts.results` JSONB: `outcome ∈ got/missed/wrong` | `elem->>'node_title'` = `roadmap_nodes.title` (established convention) |
| Review recall + FSRS | node-linked `activities` (`node_id`) and their completed `reviews` (`recalled`), `activities.stability` | `activities.node_id` |

**Status per node** (server-computed, returned as an enum so the UI never re-derives it):

- `untouched` — no test results and no node-linked card. (Rendered grey; distinct from "weak" — absence of evidence.)
- `weak` — test accuracy < 0.5 over ≥2 results, OR last 2+ reviews on the node's card were misses.
- `developing` — accuracy 0.5–0.8, or recalled but stability < 7 days (knows it *today*, will forget by the exam).
- `strong` — accuracy ≥ 0.8 (≥2 results) or stability ≥ 7d with latest review recalled.

Weights when both sources exist: **test evidence wins** (it's objective; review `recalled` is self-reported). Thresholds are constants in one place (`services/mastery.py`) — expect to tune them; do not scatter.

**Honest-floor convention carries over:** a node with a single data point stays `untouched` visually annotated as "1 attempt" rather than pretending precision. Class-level cells with <30% of students having any data render as "insufficient data", exactly like the existing `enough_data` pattern. This honesty is a *pitch feature* — schools are numb to dashboards that invent numbers.

Prerequisite edges (`roadmap_node_prerequisites`) upgrade the gap map from descriptive to diagnostic: for each weak node, if a prerequisite node is also weak for the same students, surface it as the **likely root cause** ("weak on Equations of Motion; blocker: Acceleration"). This reuses the existing "Why am I stuck?" data with zero new schema — and it's the most differentiated sentence in the demo.

## 4. API surface (new router `classrooms.py`, mounted at `/api/classrooms`)

### 4.1 Roster / lifecycle

| Endpoint | Auth | Behavior |
|---|---|---|
| `POST /api/classrooms/` | user | Create; server generates `join_code`; caller becomes teacher. Cap: `MAX_CLASSROOMS_PER_TEACHER = 20` (abuse bound, same spirit as the syllabus cap). |
| `GET /api/classrooms/mine` | user | Two lists: `teaching: [...]` (owned, with member counts) and `enrolled: [...]` (memberships, with classroom + teacher-name-less summary — students see class name only). |
| `PATCH /api/classrooms/{id}` | teacher-owner | Rename, set `school_name`, archive/unarchive, **regenerate join_code** (invalidates the old one — the "code leaked on the class WhatsApp group" recovery). |
| `POST /api/classrooms/join` | user | Body `{code, display_name}`. Resolves code → membership upsert. 404 on bad code (don't distinguish wrong vs archived). Rate-limit note in §6. Returns what the teacher will now see — the consent screen renders from this response (§5). |
| `DELETE /api/classrooms/{id}/members/{member_id}` | teacher-owner | Remove a student. |
| `DELETE /api/classrooms/{id}/membership` | student | Leave. Visibility ends immediately; nothing is deleted from the student's own account. |
| `PATCH /api/classrooms/{id}/members/{member_id}` | teacher-owner | Edit `display_name` (fix roll-call names). |
| `PUT /api/classrooms/{id}/roadmaps` | teacher-owner | Replace the assigned-roadmap set. Validates: catalog only (`user_id IS NULL`), `audience='school'`. |

**Ownership dependency:** a `get_owned_classroom(classroom_id, current_user)` dependency does the `WHERE id=:id AND teacher_user_id=:uid` fetch once and 404s otherwise (404, not 403 — don't confirm existence). Every teacher-scoped route goes through it; this is the IDOR wall and gets its own tests in `test_ownership.py` style.

### 4.2 Class analytics (teacher-owner only, scoped to assigned roadmaps + members)

| Endpoint | Returns |
|---|---|
| `GET /{id}/overview` | Headline stats: member count, active-last-7d, reviews completed (7d), class recall rate (7d), at-risk count, per-assigned-roadmap coverage % (students with any activity). One grouped query per stat family — GROUP BY `student_user_id`, never N+1 per student. |
| `GET /{id}/gap-map?roadmap_id=` | Per node (ordered by phase/section/order_index): `{node_id, title, phase, section, counts: {untouched, weak, developing, strong}, weak_students: [member_id...], root_cause_node_id?}`. One pass: pull all members' test results + node-linked review state for the roadmap in two grouped queries, fold in Python via `services/mastery.py`. |
| `GET /{id}/students` | Roster rows: `{member_id, display_name, last_active_at, reviews_completed_7d, recall_rate, current_streak, weak_node_count, overdue_count, at_risk: bool, at_risk_reasons: [...]}`. |
| `GET /{id}/students/{member_id}` | Drill-down: the student's per-node mastery for assigned roadmaps + retention trend (weekly recall rate, last 8 weeks) + test attempt history (scores per phase) + review heatmap (counts only). |

**At-risk flag** (deterministic, reasons always attached — teachers distrust unexplained flags): any of — no activity in 7 days; recall rate < 0.5 over the last 10 completed reviews; overdue reviews > 15. Constants live with the mastery thresholds.

**Aggregation authorization rule:** every analytics query's inner scope is `user_id IN (SELECT student_user_id FROM classroom_members WHERE classroom_id = :cid)` **AND** content scoped to the classroom's assigned roadmaps (`activities.node_id`/`roadmap_id` ∈ assigned, `test_attempts.roadmap_id` ∈ assigned). A teacher must never receive a number computed from a student's non-classroom life (career roadmaps, personal syllabus roadmaps, free-form cards). This rule is the privacy boundary made executable — test it explicitly.

### 4.3 Refactor, don't duplicate

`dashboard.py`'s aggregate bodies (`review-metrics`, `heatmap`, `node-accuracy` internals) get extracted into `services/learner_stats.py` functions taking `(db, user_id, roadmap_scope: list[uuid] | None)`. The existing self-serve endpoints call them with `current_user.id, None`; the teacher drill-down calls them with the member's id + assigned-roadmap scope. One implementation, two authorization paths. (The Postgres-only raw-SQL blocks move along and keep their SQLite-boundary comments.)

## 5. Privacy boundary & DPDP posture (students are minors — this section is load-bearing for the pitch)

**What the teacher sees:** display_name (student-typed), activity timing, review counts/outcomes, FSRS-derived mastery, test scores and per-question outcomes, streaks.

**What the teacher NEVER sees:** the student's `key_memory`/notes/mistake text (their private notebook), free-recall answer text, AI feedback text, email or Google identity, anything from non-assigned roadmaps, career-side activity. Enforced server-side by field selection + the scope rule in §4.2 — not by frontend omission.

**Consent moment:** the join screen (`/join/{code}`) lists, in plain language, exactly what the teacher will see and not see, and requires an explicit confirm. The student can leave at any time from their Profile (visibility ends immediately). This screen doubles as the DPDP good-faith artifact; the fuller compliance story (parental consent capture, data-processing disclosure covering Groq/PostHog/Resend) is the separate pre-pilot one-pager already on the watch-list — not this spec's scope, but this spec must not make it harder.

**Data on leave/remove:** membership row deleted; no analytics are retained about the pairing. Student data was never copied — teacher views were live queries — so there's nothing else to delete.

## 6. Security notes

- **Join-code brute force:** 8 chars over a 32-symbol alphabet ≈ 1.1e12 — fine *if* guessing is throttled. The repo has no rate limiting (SYSTEM-OVERVIEW §4 risk #1). Minimum viable here without solving the general problem: a per-user counter on join attempts (10/hour, in-DB or in-memory like the syllabus daily cap) + 404 on miss. When slowapi lands globally, this endpoint is in the first batch.
- **IDOR:** all teacher routes behind `get_owned_classroom`; member-scoped routes additionally verify the member belongs to that classroom. Extend `test_ownership.py` with: teacher A cannot read teacher B's class; a student cannot call teacher endpoints on a class they merely belong to; a removed student's stats stop resolving.
- **Enumeration:** `join` returns 404 for unknown codes with no timing/shape difference from archived ones.
- **Input bounds:** `max_length` on name/school_name/display_name per the existing convention.

## 7. Frontend (`/teach`)

- **Routes:** `/teach` (class list + create), `/teach/:id` (tabs: **Gap Map** · **Students** · **Overview**), `/teach/:id/students/:memberId` (drill-down), `/join/:code` (student consent + join; also reachable by typing the code on the Profile page).
- **Nav:** "Teach" appears in the shell when `GET /api/classrooms/mine.teaching` is non-empty; a "Set up your class" entry lives on Profile for discovery. School-audience students see "My Class" on Profile (enrolled list + leave).
- **Gap Map rendering:** CSS-grid heatmap grouped by phase → section; cell color = dominant status weighted weak > developing > strong, grey for untouched/insufficient; cell click → side panel with the student list per status + the root-cause prerequisite callout. Desktop-first (teachers on laptops/projectors — same call as DSA). Reuses existing color utility classes so dark mode is free; `ReviewHeatmap.jsx` is prior art for the grid, `SchoolRoadmaps.jsx` for phase parsing ("Class 9 · Motion").
- **Empty states matter for the demo:** a classroom with no data yet shows the seeded-demo screenshot… no. It shows honest zero-states with a "here's what this will look like" illustration. The *pitch* uses the seeded demo classroom (§9), never fake numbers in real accounts.

## 8. Phasing

**Phase 0 — pitch-demo blocking (build first):**
1. Migration (3 tables) + `classrooms.py` router: create/mine/join/roadmaps + gap-map + students + overview.
2. `services/mastery.py` + `services/learner_stats.py` refactor.
3. `/teach` UI: class list, Gap Map tab, Students tab; `/join/:code` consent flow.
4. Ownership/IDOR tests + mastery unit tests (pure function → easy goldens).
5. **Seed script: demo classroom** — "Class 9-A Physics", ~12 members with 3 personas (strong/average/struggling) × realistic 3-week review+test history against `physics-9-10`. This is the artifact projected in the pitch room. (Seed must use the progress-safe upsert pattern, not the destructive delete-reinsert — see BACKLOG's seed warning.)

**Phase 1 — pilot-ready (before real students):**
6. ~~Student drill-down page + retention trend; at-risk reasons UI; member remove/rename; code regeneration UI.~~ **Done 2026-07-17** — `TeachStudentDetail.jsx` + wired the 3 endpoints (rename/remove/regen) that Phase 0 built but never surfaced. At-risk reasons UI was already done in Phase 0.
7. Join-attempt throttle; extend the DPDP one-pager with the classroom visibility model. **Not started** — `classrooms.py`'s `join_classroom` still carries the explicit deferral comment.
8. Weekly teacher email digest (reuse `mailer.py`/`reminders.py` claim pattern): "3 students went inactive, class weak-spot: Equations of Motion." **Not started.**

**Phase 2 — post-pilot:**
9. CSV/PDF export of the gap map + roster (SMC/parent-meeting artifact).
10. "Assign a test" — teacher points the class at an existing `_test` bank for a phase, dashboard tracks completion (no new content machinery; it's a filter + nudge).
11. School entity + multi-teacher + transfer-ownership, when a second real teacher exists.

Per the no-MVP rule: Phase 1–2 items are sequenced, not cut — nothing here is "maybe never."

## 9. Open questions for the founder

1. **Student identity in a real pilot:** join-code flow assumes students self-sign-up with Google accounts on their own devices. Class 9-10 reality may be shared devices / no Gmail. If the pilot school can't do Google-per-student, teacher-provisioned accounts become a Phase 1 requirement (bigger auth change — Supabase email+password or magic links; also flips the HIBP advisor from moot to real). **Recommendation:** ask the school in the pitch meeting; don't build speculatively.
2. **Does the teacher see per-question test detail** (which option a student picked, misconception tags) in drill-down, or only per-node outcomes? Misconception tags (`trap`/`misconception` already in `test_attempts.results`) would be genuinely useful for reteaching — leaning yes, Phase 1.
3. **Gap-map default granularity:** node-level grids for a 100+-node roadmap overwhelm; likely default to section-level rollup with node-level on expand. Decide against real content dimensions when building the UI.

## 10. Doc-routing obligations when implemented

Same-commit updates per CLAUDE.md: SYSTEM-OVERVIEW §1 (router, services, frontend routes) + §2 (tables, migration) + §4 (new teacher authorization path, privacy boundary) + Changelog; DECISIONS.md entries for (a) no-role-column "teacher = classroom owner" and (b) the teacher-never-sees-private-content boundary; migration includes RLS.
