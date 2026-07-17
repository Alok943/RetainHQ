"""
Seed script: demo classroom for the school pitch (SPEC-teacher-dashboard.md §8
Phase 0 item 5, extended per PROMPT-demo-data.md) — "Class 9-A Physics", 12
students across 3 personas (strong/average/struggling), ~3 weeks of review +
test history against 6 real physics-9-10 nodes (Class 9 · Motion). This is the
artifact projected in the pitch room — retainhq.app itself never shows
fabricated numbers on a real account (spec §7 "Empty states matter for the
demo").

Card memory state is NOT hand-written: each persona's review history is
replayed through the real app.services.scheduler.apply_fsrs() in chronological
order, so stability/difficulty/next_review_at are exactly what the production
engine would have produced from that sequence of grades — not numbers that
merely look plausible.

--- Real accounts (optional; env vars, unset = fully synthetic) ---------------

DEMO_TEACHER_USER_ID: if set, this Supabase auth user owns the classroom, so
  the founder can log into a real account and present the Teach dashboard live.
  Unset -> a fixed fake UUID (no login possible; teacher-side reads still work
  since get_owned_classroom only matches teacher_user_id on the row, it never
  requires that id to have a live Supabase session).

DEMO_STUDENT_USER_ID: if set, this real Supabase auth user REPLACES the
  synthetic "Kabir Nair" slot (first "average" persona — demos best live per
  PROMPT-demo-data.md §3: some green, some red, a due queue that isn't
  demoralizing). The founder can then log into that account and drive the
  student-side Analytics/Review/Tests screens live. After seeding, the script
  self-verifies that every gated dashboard aggregate clears its enough_data
  floor for this account and aborts loudly if one doesn't.

Both env vars are checked against a freshness guard before writing: if the
given id already has activities/reviews/test_attempts older than the ~3-week
demo window, the script refuses to run rather than risk mixing fabricated
data into a real, already-in-use account.

IMPORTANT — switching a slot from synthetic to real: activity/review/
test_attempt row ids are keyed off a stable SLOT identity (the student's name,
or a fixed "real-student" marker for whichever slot DEMO_STUDENT_USER_ID
currently fills) — never off the live UUID itself — so a rerun with the same
config always upserts the SAME rows regardless of who happens to be logged in.
The first time you set DEMO_STUDENT_USER_ID, the "real-student" slot's rows
are brand new (never colliding with the old synthetic "Kabir Nair" rows,
which used the "Kabir-Nair" slot key). The classroom_members row DOES key on
(classroom_id, student_user_id) rather than on our own id, so switching
leaves BOTH a synthetic "Kabir Nair" member and a real one in the roster; the
script detects this and prints a warning with a cleanup statement.

Refreshing already-seeded demo data (e.g. after this script's persona/logic
changes) — a plain rerun deliberately does NOT overwrite existing rows'
data fields (ON CONFLICT DO NOTHING everywhere) so it can never clobber a
real student's own activity that happens to match a seeded node. To force a
clean refresh, set RESET_SYNTHETIC_DEMO=1: this deletes ONLY the rows owned
by this script's deterministic synthetic ids (activities — which cascades
their reviews —, test_attempts, classroom_members) before reseeding. It is
mathematically incapable of touching a real account: synthetic ids are uuid5
hashes of a fixed namespace, a real Supabase auth id can never collide with
one. DEMO_STUDENT_USER_ID / DEMO_TEACHER_USER_ID rows are never touched by
the reset even if set.

Idempotent, upsert-only (BACKLOG.md's progress-safe-seed rule — never
delete-then-reinsert): every row's id is a uuid5 hash of a stable business key
(resolved user id, node title, review/attempt index), so re-running this
script with the SAME env-var configuration computes the SAME ids every time.
Classroom/member rows use ON CONFLICT ... DO UPDATE (so a rerun can fix a
typo'd name); activity/review/test-attempt rows use a bare ON CONFLICT DO
NOTHING (activities also sit behind the real uq_activities_user_node partial
unique index, so a plain DO NOTHING — not one scoped to the id arbiter — is
required to swallow that constraint too). No row is ever deleted.

Depends on seed_physics_school.py having been run first (queries its real
RoadmapNode rows by title — node UUIDs are regenerated on every re-seed of
that script, per its own docstring, so we never hardcode them here).

Run: ./.venv/Scripts/python.exe seed_classroom_demo.py
Run (real accounts wired):
  DEMO_TEACHER_USER_ID=<uuid> DEMO_STUDENT_USER_ID=<uuid> ./.venv/Scripts/python.exe seed_classroom_demo.py
Re-run the day before any pitch — the ~3-week window is relative to run time,
and a heatmap whose last activity is weeks old reads as a dead account.
"""
import asyncio
import json
import os
import random
import uuid
from datetime import datetime, timedelta

from sqlalchemy import text
from app.core.database import engine
from app.models.models import Activity
from app.services.scheduler import apply_fsrs, fsrs_rating_from_outcome, quality_from_outcome
from app.services.learner_stats import REVIEW_METRICS_MIN, NODE_ACCURACY_MIN
from app.api.routes.dashboard import SOURCE_RETENTION_MIN

SEED_NS = uuid.uuid5(uuid.NAMESPACE_URL, "retainhq.app/seed/classroom-demo")


def _id(key: str) -> uuid.UUID:
    return uuid.uuid5(SEED_NS, key)


PHYSICS_ROADMAP_ID = uuid.UUID("f1f1f1f1-f1f1-f1f1-f1f1-f1f1f1f1f1f1")  # seed_physics_school.py
PHYSICS_PHASE = "Class 9 · Motion"

_FAKE_TEACHER_USER_ID = _id("teacher")  # default when DEMO_TEACHER_USER_ID unset
CLASSROOM_ID = _id("classroom")
CLASSROOM_ROADMAP_ID = _id("classroom-roadmap")
CLASSROOM_NAME = "Class 9-A Physics"
SCHOOL_NAME = "Demo School"
# Readable + alphabet-safe (no 0/O/1/I) per classrooms.py's JOIN_CODE_ALPHABET —
# real seed data, doesn't need to come out of _generate_join_code().
JOIN_CODE = "PHYS9ADM"

# Node titles must match seed_physics_school.py exactly (join key). The first
# two have a real roadmap_node_prerequisites edge (seed_physics_school_prereqs.py):
# "Define displacement" requires "Define distance" — that's the pair we seed
# weak for the struggling persona so the gap map's root-cause callout fires.
NODE_DISTANCE = "Define distance"
NODE_DISPLACEMENT = "Define displacement"
NODE_DIST_VS_DISP = "Distinguish distance from displacement"
NODE_AVG_SPEED = "Define average speed"
NODE_VELOCITY = "Define velocity"
NODE_ACCELERATION = "Define acceleration"

# key_memory text is the real recall_hint from seed_physics_school.py's NODES
# list — what "Add to reviews" would actually capture for these lessons.
NODE_KEY_MEMORY = {
    NODE_DISTANCE: "Distance is the actual path length covered by an object.",
    NODE_DISPLACEMENT: "Displacement is the shortest straight-line distance from initial to final position.",
    NODE_DIST_VS_DISP: "Distance = path length (scalar); displacement = shortest start->end vector; can be zero.",
    NODE_AVG_SPEED: "Average speed = total distance / total time.",
    NODE_VELOCITY: "Velocity is speed with a specific direction (displacement / time).",
    NODE_ACCELERATION: "Acceleration is the rate of change of velocity: a = (v-u)/t.",
}
NODE_TITLES = list(NODE_KEY_MEMORY)

# Realistic source_type split (feeds source-retention with 2 distinct groups,
# each well above SOURCE_RETENTION_MIN): the two numeric-type nodes read as
# "solved via a numerical problem", the rest as "captured from a lesson".
NODE_SOURCE_TYPE = {
    NODE_DISTANCE: "lesson",
    NODE_DISPLACEMENT: "lesson",
    NODE_DIST_VS_DISP: "lesson",
    NODE_AVG_SPEED: "problem",
    NODE_VELOCITY: "lesson",
    NODE_ACCELERATION: "problem",
}

NODE_QUESTION_TYPE = {
    NODE_DISTANCE: "fillup",
    NODE_DISPLACEMENT: "fillup",
    NODE_DIST_VS_DISP: "mcq",
    NODE_AVG_SPEED: "numeric",
    NODE_VELOCITY: "mcq",
    NODE_ACCELERATION: "numeric",
}
NODE_TRAP = {
    NODE_DISTANCE: False,
    NODE_DISPLACEMENT: True,
    NODE_DIST_VS_DISP: True,
    NODE_AVG_SPEED: False,
    NODE_VELOCITY: False,
    NODE_ACCELERATION: True,
}
NODE_MISCONCEPTION = {
    NODE_DISTANCE: "treats distance as a signed/directional quantity",
    NODE_DISPLACEMENT: "confuses displacement with total distance travelled",
    NODE_DIST_VS_DISP: "picks total path length when the question asks for displacement",
    NODE_AVG_SPEED: "divides by the number of intervals instead of total time",
    NODE_VELOCITY: "treats speed and velocity as identical",
    NODE_ACCELERATION: "assumes zero velocity at the highest point means zero acceleration",
}

# (persona, first, last, roll)
STUDENTS = [
    ("strong", "Priya", "Sharma", 3),
    ("strong", "Arjun", "Mehta", 7),
    ("strong", "Ananya", "Reddy", 12),
    ("strong", "Rohan", "Verma", 15),
    ("average", "Kabir", "Nair", 5),
    ("average", "Sneha", "Iyer", 9),
    ("average", "Vikram", "Rao", 18),
    ("average", "Meera", "Joshi", 21),
    ("struggling", "Aditya", "Kumar", 2),
    ("struggling", "Ishita", "Patel", 11),
    ("struggling", "Rahul", "Singh", 19),
    ("struggling", "Divya", "Menon", 24),
]

# The slot DEMO_STUDENT_USER_ID (if set) replaces — "average" demos best live
# per PROMPT-demo-data.md §3 (some green, some red, a non-demoralizing queue).
REAL_STUDENT_SLOT = ("average", "Kabir", "Nair", 5)

# Per-persona review trajectory across the ~3-week history (oldest -> newest):
# (days_ago, recalled, rating, duration_ms). Card memory state (stability,
# difficulty, next_review_at) is NOT specified here — it's derived by replaying
# these grades through the real apply_fsrs(), so it's exactly what the
# production engine would produce from this sequence, not a hand-tuned number.
PERSONA_REVIEWS = {
    "strong": [
        (21, False, "hard", 22000),
        (14, True, "medium", 14000),
        (7, True, "easy", 9000),
        (2, True, "easy", 8000),
    ],
    "average": [
        (21, False, "hard", 30000),
        (14, True, "medium", 20000),
        (7, False, "hard", 28000),
        (2, True, "medium", 18000),
    ],
    "struggling": [
        (21, False, "hard", 40000),
        (14, False, "hard", 38000),
        (7, True, "hard", 35000),
        (2, False, "hard", 42000),
    ],
}

PERSONA_CARD_DIFFICULTY = {"strong": 2, "average": 3, "struggling": 4}  # user's 1-5 self-rating

# AI recall-grader calibration (services/grader.py's ai_recalled/ai_verdict).
# AI_GRADE_COVERAGE = fraction of completed reviews the grader actually touched
# (grading is opt-in per review in the real app). PERSONA_AGREEMENT = how often
# the grader's verdict matches the student's own self-reported `recalled` —
# struggling students self-report generously ("I got it") more often than the
# grader agrees, which is exactly the "overconfident" story worth showing.
AI_GRADE_COVERAGE = 0.7
PERSONA_AGREEMENT = {"strong": 0.85, "average": 0.7, "struggling": 0.55}
AI_FEEDBACK_BY_VERDICT = {
    "correct": "Nailed the key idea.",
    "partial": "Got the gist, missed a precise detail.",
    "incorrect": "Missed the core idea here — worth a reread before the next review.",
}

# Per persona, per node: two test-attempt outcomes (oldest -> newest). Struggling
# is 0/2 ("weak", accuracy < 0.5) on the two root-cause-linked nodes specifically,
# per the task spec, so the gap map's root-cause callout has real evidence.
PERSONA_NODE_OUTCOMES = {
    "strong": {
        NODE_DISTANCE: ["got", "got"],
        NODE_DISPLACEMENT: ["got", "got"],
        NODE_DIST_VS_DISP: ["missed", "got"],
        NODE_AVG_SPEED: ["got", "got"],
        NODE_VELOCITY: ["got", "got"],
        NODE_ACCELERATION: ["got", "got"],
    },
    "average": {
        NODE_DISTANCE: ["got", "missed"],
        NODE_DISPLACEMENT: ["missed", "got"],
        NODE_DIST_VS_DISP: ["got", "missed"],
        NODE_AVG_SPEED: ["missed", "got"],
        NODE_VELOCITY: ["got", "got"],
        NODE_ACCELERATION: ["missed", "got"],
    },
    "struggling": {
        NODE_DISTANCE: ["missed", "missed"],      # root-cause node — weak
        NODE_DISPLACEMENT: ["missed", "wrong"],    # root-cause node — weak
        NODE_DIST_VS_DISP: ["missed", "got"],
        NODE_AVG_SPEED: ["wrong", "got"],
        NODE_VELOCITY: ["missed", "got"],
        NODE_ACCELERATION: ["missed", "missed"],
    },
}

TEST_ATTEMPT_DAYS_AGO = [18, 4]  # two attempts within the 3-week window

# Freshness guard: refuse to seed onto an id whose real history predates this
# window by more than this margin — catches a fat-fingered real-user id before
# fabricated data gets mixed into it. Wider than the 21-day demo window itself
# so the script's OWN rows (max 21 days old) never trip the check on a rerun.
FRESHNESS_GUARD_DAYS = 25


def _display_name(first: str, last: str, roll: int) -> str:
    return f"{first} {last}, Roll {roll}"


def _env_uuid(name: str) -> uuid.UUID | None:
    raw = os.environ.get(name)
    if not raw:
        return None
    return uuid.UUID(raw)


async def _assert_fresh_account(conn, user_id: uuid.UUID, label: str) -> None:
    """Guard against seeding fabricated demo data onto a real, already-in-use
    account: if it has activity/review/test-attempt history older than the
    demo window (+ safety margin), this isn't a fresh demo login."""
    cutoff = datetime.utcnow() - timedelta(days=FRESHNESS_GUARD_DAYS)
    row = (
        await conn.execute(
            text(
                "SELECT min(created_at) AS oldest FROM ("
                "  SELECT created_at FROM activities WHERE user_id = :uid"
                "  UNION ALL SELECT created_at FROM reviews WHERE user_id = :uid"
                "  UNION ALL SELECT created_at FROM test_attempts WHERE user_id = :uid"
                ") x"
            ),
            {"uid": str(user_id)},
        )
    ).one()
    if row.oldest is not None and row.oldest < cutoff:
        raise RuntimeError(
            f"Refusing to seed onto {label} ({user_id}): it already has activity/review/"
            f"test-attempt history older than {cutoff.date()} — this looks like a real, "
            f"already-in-use account, not a fresh demo login. Use a dedicated demo "
            f"Google account, or unset the env var to fall back to a synthetic id."
        )


def _all_synthetic_ids() -> tuple[list[uuid.UUID], list[uuid.UUID]]:
    """Every id this script would EVER use for a fully-synthetic run — the
    fixed set that RESET_SYNTHETIC_DEMO is allowed to delete. Includes the
    real-student slot's synthetic fallback (so a stale "Kabir Nair" left over
    from a pre-DEMO_STUDENT_USER_ID run gets cleaned up too)."""
    student_ids = [_id(f"student:{first}-{last}") for _p, first, last, _r in STUDENTS]
    member_ids = [_id(f"member:{first}-{last}") for _p, first, last, _r in STUDENTS]
    return student_ids, member_ids


async def _reset_synthetic_demo_data(conn) -> None:
    student_ids, member_ids = _all_synthetic_ids()
    student_id_strs = [str(u) for u in student_ids]
    member_id_strs = [str(u) for u in member_ids]

    deleted_attempts = (
        await conn.execute(
            text("DELETE FROM test_attempts WHERE user_id = ANY(:ids)"),
            {"ids": student_id_strs},
        )
    ).rowcount
    # ondelete=CASCADE on reviews.activity_id takes the review history with it.
    deleted_activities = (
        await conn.execute(
            text("DELETE FROM activities WHERE user_id = ANY(:ids)"),
            {"ids": student_id_strs},
        )
    ).rowcount
    deleted_members = (
        await conn.execute(
            text("DELETE FROM classroom_members WHERE id = ANY(:ids)"),
            {"ids": member_id_strs},
        )
    ).rowcount
    print(
        f"RESET_SYNTHETIC_DEMO: cleared {deleted_activities} activities (+ cascaded reviews), "
        f"{deleted_attempts} test attempts, {deleted_members} classroom members "
        f"— all scoped to this script's fixed synthetic ids.\n"
    )


async def _fetch_node_ids(conn) -> dict:
    rows = (
        await conn.execute(
            text("SELECT id, title FROM roadmap_nodes WHERE roadmap_id = :rid"),
            {"rid": str(PHYSICS_ROADMAP_ID)},
        )
    ).fetchall()
    by_title = {r.title: r.id for r in rows}
    missing = [t for t in NODE_TITLES if t not in by_title]
    if missing:
        raise RuntimeError(
            f"Missing physics-9-10 nodes (run seed_physics_school.py first): {missing}"
        )
    return by_title


def _replay_fsrs(review_plan: list[tuple], node_id: uuid.UUID, student_id: uuid.UUID) -> Activity:
    """Replay a persona's review history through the real FSRS engine in
    chronological order, mutating a throwaway (never-persisted-via-ORM) card.
    The card's state afterward — stability/difficulty/next_review_at — is
    exactly what production would have produced from this grade sequence."""
    card = Activity(
        user_id=student_id,
        roadmap_id=PHYSICS_ROADMAP_ID,
        node_id=node_id,
        topic="",
        difficulty=1,
        key_memory="",
    )
    for days_ago, recalled, rating, _duration_ms in review_plan:
        completed_at = datetime.utcnow() - timedelta(days=days_ago)
        grade = fsrs_rating_from_outcome(rating, recalled)
        apply_fsrs(card, grade, now=completed_at)
    return card


def _ai_grade(review_id: uuid.UUID, persona: str, recalled: bool, rating: str):
    """Deterministic (seeded by review_id) AI-grader calibration fields —
    ai_recalled/ai_verdict/ai_feedback, or (None, None, None) when this review
    wasn't graded at all (grading is opt-in per review in the real app)."""
    rng = random.Random(review_id.int & 0xFFFFFFFF)
    if rng.random() >= AI_GRADE_COVERAGE:
        return None, None, None
    agree = rng.random() < PERSONA_AGREEMENT[persona]
    ai_recalled = recalled if agree else (not recalled)
    if ai_recalled:
        verdict = "correct" if rating != "hard" else "partial"
    else:
        verdict = "incorrect"
    return ai_recalled, verdict, AI_FEEDBACK_BY_VERDICT[verdict]


async def main():
    demo_teacher_id = _env_uuid("DEMO_TEACHER_USER_ID")
    demo_student_id = _env_uuid("DEMO_STUDENT_USER_ID")
    teacher_id = demo_teacher_id or _FAKE_TEACHER_USER_ID
    reset_synthetic = os.environ.get("RESET_SYNTHETIC_DEMO", "").lower() in ("1", "true", "yes")

    if reset_synthetic:
        async with engine.begin() as conn:
            await _reset_synthetic_demo_data(conn)

    async with engine.begin() as conn:
        if demo_teacher_id is not None:
            await _assert_fresh_account(conn, demo_teacher_id, "DEMO_TEACHER_USER_ID")
        if demo_student_id is not None:
            await _assert_fresh_account(conn, demo_student_id, "DEMO_STUDENT_USER_ID")

        # ---- Classroom + assigned roadmap --------------------------------
        await conn.execute(
            text(
                "INSERT INTO classrooms (id, teacher_user_id, name, school_name, join_code, created_at) "
                "VALUES (:id, :teacher_id, :name, :school, :code, now()) "
                "ON CONFLICT (id) DO UPDATE SET name = :name, school_name = :school, teacher_user_id = :teacher_id"
            ),
            {
                "id": str(CLASSROOM_ID), "teacher_id": str(teacher_id),
                "name": CLASSROOM_NAME, "school": SCHOOL_NAME, "code": JOIN_CODE,
            },
        )
        await conn.execute(
            text(
                "INSERT INTO classroom_roadmaps (id, classroom_id, roadmap_id) "
                "VALUES (:id, :cid, :rid) ON CONFLICT (classroom_id, roadmap_id) DO NOTHING"
            ),
            {"id": str(CLASSROOM_ROADMAP_ID), "cid": str(CLASSROOM_ID), "rid": str(PHYSICS_ROADMAP_ID)},
        )

        node_id_by_title = await _fetch_node_ids(conn)
        now = datetime.utcnow()

        members_touched = 0
        activities_inserted = reviews_inserted = attempts_inserted = 0
        activities_seen = reviews_seen = attempts_seen = 0
        stale_synthetic_warning = None

        for persona, first, last, roll in STUDENTS:
            student_key = f"{first}-{last}"
            is_real_slot = (persona, first, last, roll) == REAL_STUDENT_SLOT and demo_student_id is not None
            student_id = demo_student_id if is_real_slot else _id(f"student:{student_key}")
            display_name = _display_name(first, last, roll)
            # Row-identity key: stable per SLOT (name, or a fixed marker for
            # whichever slot is currently "the real account"), never derived
            # from the live UUID — so a rerun with unchanged config always
            # upserts the same rows, and switching synthetic<->real never
            # collides with the other's rows (incl. the member row's PRIMARY
            # KEY — its ON CONFLICT target is (classroom_id, student_user_id),
            # which would NOT catch an id collision against the old synthetic
            # row, so member_id must be key_slot-based too). See module docstring.
            key_slot = "real-student" if is_real_slot else student_key
            member_id = _id(f"member:{key_slot}")

            await conn.execute(
                text(
                    "INSERT INTO classroom_members (id, classroom_id, student_user_id, display_name, joined_at) "
                    "VALUES (:id, :cid, :sid, :name, :joined_at) "
                    "ON CONFLICT (classroom_id, student_user_id) DO UPDATE SET display_name = :name"
                ),
                {
                    "id": str(member_id), "cid": str(CLASSROOM_ID), "sid": str(student_id),
                    "name": display_name, "joined_at": now - timedelta(days=21),
                },
            )
            members_touched += 1

            if is_real_slot:
                # If a prior synthetic-only run already seeded this slot under
                # its deterministic fake id, that row is a DIFFERENT
                # (classroom_id, student_user_id) tuple and won't be touched by
                # the upsert above — it'll sit alongside the real one. Detect
                # and flag it (never auto-delete, per convention).
                stale_id = _id(f"student:{student_key}")
                stale = (
                    await conn.execute(
                        text(
                            "SELECT id FROM classroom_members "
                            "WHERE classroom_id = :cid AND student_user_id = :sid"
                        ),
                        {"cid": str(CLASSROOM_ID), "sid": str(stale_id)},
                    )
                ).first()
                if stale is not None:
                    stale_synthetic_warning = (
                        f"A synthetic '{display_name}' member row still exists from a prior "
                        f"run without DEMO_STUDENT_USER_ID set. Clean it up manually:\n"
                        f"  DELETE FROM classroom_members WHERE id = '{stale.id}';"
                    )

            review_plan = PERSONA_REVIEWS[persona]
            card_difficulty = PERSONA_CARD_DIFFICULTY[persona]
            needed_hint = persona == "struggling"

            for node_title in NODE_TITLES:
                node_id = node_id_by_title[node_title]
                source_type = NODE_SOURCE_TYPE[node_title]
                activity_id = _id(f"activity:{key_slot}:{node_title}")

                card = _replay_fsrs(review_plan, node_id, student_id)
                created_at = now - timedelta(days=21)

                activities_seen += 1
                result = await conn.execute(
                    text(
                        "INSERT INTO activities (id, user_id, roadmap_id, node_id, topic, difficulty, "
                        "needed_hint, key_memory, source_type, created_at, stability, difficulty_fsrs, "
                        "last_reviewed_at, next_review_at) "
                        "VALUES (:id, :uid, :rid, :nid, :topic, :diff, :hint, :mem, :source, :created, "
                        ":stability, :fsrs_diff, :last_rev, :next_rev) "
                        "ON CONFLICT DO NOTHING"
                    ),
                    {
                        "id": str(activity_id), "uid": str(student_id), "rid": str(PHYSICS_ROADMAP_ID),
                        "nid": str(node_id), "topic": node_title, "diff": card_difficulty,
                        "hint": needed_hint, "mem": NODE_KEY_MEMORY[node_title], "source": source_type,
                        "created": created_at, "stability": card.stability, "fsrs_diff": card.difficulty_fsrs,
                        "last_rev": card.last_reviewed_at, "next_rev": card.next_review_at,
                    },
                )
                if result.rowcount:
                    activities_inserted += 1

                for i, (days_ago, recalled, rating, duration_ms) in enumerate(review_plan):
                    review_id = _id(f"review:{key_slot}:{node_title}:{i}")
                    completed_at = now - timedelta(days=days_ago)
                    quality = quality_from_outcome(rating, recalled)
                    ai_recalled, ai_verdict, ai_feedback = _ai_grade(review_id, persona, recalled, rating)
                    reviews_seen += 1
                    result = await conn.execute(
                        text(
                            "INSERT INTO reviews (id, user_id, activity_id, status, scheduled_for, "
                            "completed_at, rating, recalled, quality, duration_ms, ai_recalled, "
                            "ai_verdict, ai_feedback, created_at) "
                            "VALUES (:id, :uid, :aid, 'completed', :sched, :completed, :rating, "
                            ":recalled, :quality, :duration, :ai_recalled, :ai_verdict, :ai_feedback, :created) "
                            "ON CONFLICT DO NOTHING"
                        ),
                        {
                            "id": str(review_id), "uid": str(student_id), "aid": str(activity_id),
                            "sched": completed_at, "completed": completed_at, "rating": rating,
                            "recalled": recalled, "quality": quality, "duration": duration_ms,
                            "ai_recalled": ai_recalled, "ai_verdict": ai_verdict, "ai_feedback": ai_feedback,
                            "created": completed_at,
                        },
                    )
                    if result.rowcount:
                        reviews_inserted += 1

                # The one open "due" review every activity carries in production
                # (reviews.uq_reviews_one_open_per_activity) — card.next_review_at
                # is exactly what apply_fsrs computed from the final replayed grade.
                due_review_id = _id(f"review:{key_slot}:{node_title}:due")
                reviews_seen += 1
                result = await conn.execute(
                    text(
                        "INSERT INTO reviews (id, user_id, activity_id, status, scheduled_for, created_at) "
                        "VALUES (:id, :uid, :aid, 'due', :sched, :created) "
                        "ON CONFLICT DO NOTHING"
                    ),
                    {
                        "id": str(due_review_id), "uid": str(student_id), "aid": str(activity_id),
                        "sched": card.next_review_at, "created": card.last_reviewed_at,
                    },
                )
                if result.rowcount:
                    reviews_inserted += 1

            for attempt_i, days_ago in enumerate(TEST_ATTEMPT_DAYS_AGO):
                results = []
                got_count = 0
                for n, node_title in enumerate(NODE_TITLES, start=1):
                    outcome = PERSONA_NODE_OUTCOMES[persona][node_title][attempt_i]
                    if outcome == "got":
                        got_count += 1
                    item = {
                        "question_id": f"cd-{attempt_i}-{n}",
                        "node_title": node_title,
                        "type": NODE_QUESTION_TYPE[node_title],
                        "outcome": outcome,
                        "trap": NODE_TRAP[node_title],
                    }
                    if outcome != "got":
                        item["misconception"] = NODE_MISCONCEPTION[node_title]
                    results.append(item)

                attempt_id = _id(f"attempt:{key_slot}:{attempt_i}")
                attempts_seen += 1
                result = await conn.execute(
                    text(
                        "INSERT INTO test_attempts (id, user_id, roadmap_id, phase, score, max_score, "
                        "results, created_at) "
                        "VALUES (:id, :uid, :rid, :phase, :score, :max, CAST(:results AS jsonb), :created) "
                        "ON CONFLICT DO NOTHING"
                    ),
                    {
                        "id": str(attempt_id), "uid": str(student_id), "rid": str(PHYSICS_ROADMAP_ID),
                        "phase": PHYSICS_PHASE, "score": got_count, "max": len(NODE_TITLES),
                        "results": json.dumps(results), "created": now - timedelta(days=days_ago),
                    },
                )
                if result.rowcount:
                    attempts_inserted += 1

    print(
        f"Seeded classroom '{CLASSROOM_NAME}' (join code {JOIN_CODE}, teacher_user_id {teacher_id}"
        f"{' [REAL]' if demo_teacher_id else ' [fake, no login]'}):\n"
        f"  members touched: {members_touched}/{len(STUDENTS)}\n"
        f"  activities: {activities_inserted} inserted, {activities_seen - activities_inserted} already present\n"
        f"  reviews: {reviews_inserted} inserted, {reviews_seen - reviews_inserted} already present\n"
        f"  test attempts: {attempts_inserted} inserted, {attempts_seen - attempts_inserted} already present\n"
        f"All inserts are ON CONFLICT DO NOTHING/UPDATE — safe to re-run, nothing is ever deleted."
    )
    if stale_synthetic_warning:
        print(f"\nWARNING: {stale_synthetic_warning}")

    if demo_student_id is not None:
        await _verify_demo_student(demo_student_id)


async def _verify_demo_student(student_id: uuid.UUID) -> None:
    """Self-verification (PROMPT-demo-data.md §5): the seed isn't done until
    every gated Analytics card is proven to clear its enough_data floor for
    the real demo student account. Raises loudly on any failure rather than
    leaving the founder to discover an empty card live in the pitch."""
    async with engine.begin() as conn:
        completed = (
            await conn.execute(
                text("SELECT count(*) FROM reviews WHERE user_id = :uid AND status = 'completed'"),
                {"uid": str(student_id)},
            )
        ).scalar_one()
        graded = (
            await conn.execute(
                text("SELECT count(*) FROM reviews WHERE user_id = :uid AND ai_recalled IS NOT NULL"),
                {"uid": str(student_id)},
            )
        ).scalar_one()
        with_stability = (
            await conn.execute(
                text("SELECT count(*) FROM activities WHERE user_id = :uid AND stability IS NOT NULL"),
                {"uid": str(student_id)},
            )
        ).scalar_one()
        best_source_group = (
            await conn.execute(
                text(
                    "SELECT coalesce(max(cnt), 0) FROM ("
                    "  SELECT count(*) AS cnt FROM reviews r JOIN activities a ON a.id = r.activity_id "
                    "  WHERE r.user_id = :uid AND r.status = 'completed' "
                    "  GROUP BY coalesce(a.source_type, 'other')"
                    ") x"
                ),
                {"uid": str(student_id)},
            )
        ).scalar_one()
        best_node_group = (
            await conn.execute(
                text(
                    "SELECT coalesce(max(cnt), 0) FROM ("
                    "  SELECT count(*) AS cnt FROM test_attempts ta, jsonb_array_elements(ta.results) e "
                    "  WHERE ta.user_id = :uid GROUP BY e->>'node_title'"
                    ") x"
                ),
                {"uid": str(student_id)},
            )
        ).scalar_one()

    checks = [
        ("review-metrics / heatmap / time-of-day", completed, REVIEW_METRICS_MIN),
        ("calibration", graded, REVIEW_METRICS_MIN),
        ("memory-strength", with_stability, REVIEW_METRICS_MIN),
        ("source-retention (best group)", best_source_group, SOURCE_RETENTION_MIN),
        ("node-accuracy (best node)", best_node_group, NODE_ACCURACY_MIN),
    ]
    print(f"\nSelf-verification for the real demo student account ({student_id}):")
    all_ok = True
    for label, value, floor in checks:
        ok = value >= floor
        all_ok = all_ok and ok
        print(f"  [{'OK' if ok else 'FAIL'}] {label}: {value} >= {floor}")
    if not all_ok:
        raise RuntimeError(
            "Demo student account will show an empty state on at least one Analytics "
            "card in the pitch — see FAIL line(s) above."
        )


if __name__ == "__main__":
    asyncio.run(main())
