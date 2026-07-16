"""
Seed script: demo classroom for the school pitch (SPEC-teacher-dashboard.md §8
Phase 0 item 5) — "Class 9-A Physics", 12 students across 3 personas
(strong/average/struggling), ~3 weeks of review + test history against 6 real
physics-9-10 nodes (Class 9 · Motion). This is the artifact projected in the
pitch room — retainhq.app itself never shows fabricated numbers on a real
account (spec §7 "Empty states matter for the demo").

teacher_user_id is a fixed fake UUID with no real Supabase auth user behind
it. Nothing in the classroom read path requires the teacher to authenticate
to SEED data under their ownership — get_owned_classroom just matches
teacher_user_id on the classrooms row (app/api/routes/classrooms.py). Do not
try to log in as this UUID; it isn't a real account.

Idempotent, upsert-only (BACKLOG.md's progress-safe-seed rule — never
delete-then-reinsert): every row's id is a uuid5 hash of a stable business key
(student name, node title, review/attempt index), so re-running this script
computes the SAME ids every time. Classroom/member rows use
ON CONFLICT ... DO UPDATE (so a rerun can fix a typo'd name); activity/review/
test-attempt rows use a bare ON CONFLICT DO NOTHING (activities also sit
behind the real uq_activities_user_node partial unique index, so a plain
DO NOTHING — not one scoped to the id arbiter — is required to swallow that
constraint too). No row is ever deleted.

Depends on seed_physics_school.py having been run first (queries its real
RoadmapNode rows by title — node UUIDs are regenerated on every re-seed of
that script, per its own docstring, so we never hardcode them here).

Run: ./.venv/Scripts/python.exe seed_classroom_demo.py
"""
import asyncio
import json
import uuid
from datetime import datetime, timedelta

from sqlalchemy import text
from app.core.database import engine

SEED_NS = uuid.uuid5(uuid.NAMESPACE_URL, "retainhq.app/seed/classroom-demo")


def _id(key: str) -> uuid.UUID:
    return uuid.uuid5(SEED_NS, key)


PHYSICS_ROADMAP_ID = uuid.UUID("f1f1f1f1-f1f1-f1f1-f1f1-f1f1f1f1f1f1")  # seed_physics_school.py
PHYSICS_PHASE = "Class 9 · Motion"

TEACHER_USER_ID = _id("teacher")  # fake — no Supabase auth user; see docstring
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

# Per-persona review trajectory across the ~3-week history (oldest -> newest):
# (days_ago, recalled, rating, stability_after_days, quality, duration_ms).
PERSONA_REVIEWS = {
    "strong": [
        (21, False, "hard", 1.0, 2, 22000),
        (14, True, "medium", 4.0, 4, 14000),
        (7, True, "easy", 10.0, 5, 9000),
        (2, True, "easy", 21.0, 5, 8000),
    ],
    "average": [
        (21, False, "hard", 1.0, 2, 30000),
        (14, True, "medium", 3.0, 4, 20000),
        (7, False, "hard", 2.0, 2, 28000),
        (2, True, "medium", 5.0, 4, 18000),
    ],
    "struggling": [
        (21, False, "hard", 1.0, 1, 40000),
        (14, False, "hard", 1.0, 1, 38000),
        (7, True, "hard", 2.0, 3, 35000),
        (2, False, "hard", 1.0, 1, 42000),
    ],
}

PERSONA_CARD_DIFFICULTY = {"strong": 2, "average": 3, "struggling": 4}  # user's 1-5 self-rating
PERSONA_FSRS_DIFFICULTY = {"strong": 3.0, "average": 5.0, "struggling": 7.5}  # FSRS 1-10

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


def _display_name(first: str, last: str, roll: int) -> str:
    return f"{first} {last}, Roll {roll}"


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


async def main():
    async with engine.begin() as conn:
        # ---- Classroom + assigned roadmap --------------------------------
        await conn.execute(
            text(
                "INSERT INTO classrooms (id, teacher_user_id, name, school_name, join_code, created_at) "
                "VALUES (:id, :teacher_id, :name, :school, :code, now()) "
                "ON CONFLICT (id) DO UPDATE SET name = :name, school_name = :school"
            ),
            {
                "id": str(CLASSROOM_ID), "teacher_id": str(TEACHER_USER_ID),
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

        for persona, first, last, roll in STUDENTS:
            student_key = f"{first}-{last}"
            student_id = _id(f"student:{student_key}")
            member_id = _id(f"member:{student_key}")
            display_name = _display_name(first, last, roll)

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

            review_plan = PERSONA_REVIEWS[persona]
            card_difficulty = PERSONA_CARD_DIFFICULTY[persona]
            fsrs_difficulty = PERSONA_FSRS_DIFFICULTY[persona]
            needed_hint = persona == "struggling"

            for node_title in NODE_TITLES:
                node_id = node_id_by_title[node_title]
                activity_id = _id(f"activity:{student_key}:{node_title}")
                created_at = now - timedelta(days=21)
                last_days_ago, _recalled, _rating, last_stability, _q, _d = review_plan[-1]
                last_reviewed_at = now - timedelta(days=last_days_ago)
                next_review_at = last_reviewed_at + timedelta(days=round(last_stability))

                activities_seen += 1
                result = await conn.execute(
                    text(
                        "INSERT INTO activities (id, user_id, roadmap_id, node_id, topic, difficulty, "
                        "needed_hint, key_memory, source_type, created_at, stability, difficulty_fsrs, "
                        "last_reviewed_at, next_review_at) "
                        "VALUES (:id, :uid, :rid, :nid, :topic, :diff, :hint, :mem, 'lesson', :created, "
                        ":stability, :fsrs_diff, :last_rev, :next_rev) "
                        "ON CONFLICT DO NOTHING"
                    ),
                    {
                        "id": str(activity_id), "uid": str(student_id), "rid": str(PHYSICS_ROADMAP_ID),
                        "nid": str(node_id), "topic": node_title, "diff": card_difficulty,
                        "hint": needed_hint, "mem": NODE_KEY_MEMORY[node_title], "created": created_at,
                        "stability": last_stability, "fsrs_diff": fsrs_difficulty,
                        "last_rev": last_reviewed_at, "next_rev": next_review_at,
                    },
                )
                if result.rowcount:
                    activities_inserted += 1

                for i, (days_ago, recalled, rating, stab_after, quality, duration_ms) in enumerate(review_plan):
                    review_id = _id(f"review:{student_key}:{node_title}:{i}")
                    completed_at = now - timedelta(days=days_ago)
                    reviews_seen += 1
                    result = await conn.execute(
                        text(
                            "INSERT INTO reviews (id, user_id, activity_id, status, scheduled_for, "
                            "completed_at, rating, recalled, quality, duration_ms, created_at) "
                            "VALUES (:id, :uid, :aid, 'completed', :sched, :completed, :rating, "
                            ":recalled, :quality, :duration, :created) "
                            "ON CONFLICT DO NOTHING"
                        ),
                        {
                            "id": str(review_id), "uid": str(student_id), "aid": str(activity_id),
                            "sched": completed_at, "completed": completed_at, "rating": rating,
                            "recalled": recalled, "quality": quality, "duration": duration_ms,
                            "created": completed_at,
                        },
                    )
                    if result.rowcount:
                        reviews_inserted += 1

                # The one open "due" review every activity carries in production
                # (reviews.uq_reviews_one_open_per_activity) — next_review_at
                # above mirrors this row per the Activity docstring.
                due_review_id = _id(f"review:{student_key}:{node_title}:due")
                reviews_seen += 1
                result = await conn.execute(
                    text(
                        "INSERT INTO reviews (id, user_id, activity_id, status, scheduled_for, created_at) "
                        "VALUES (:id, :uid, :aid, 'due', :sched, :created) "
                        "ON CONFLICT DO NOTHING"
                    ),
                    {
                        "id": str(due_review_id), "uid": str(student_id), "aid": str(activity_id),
                        "sched": next_review_at, "created": last_reviewed_at,
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

                attempt_id = _id(f"attempt:{student_key}:{attempt_i}")
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
        f"Seeded classroom '{CLASSROOM_NAME}' (join code {JOIN_CODE}, teacher_user_id {TEACHER_USER_ID}):\n"
        f"  members touched: {members_touched}/{len(STUDENTS)}\n"
        f"  activities: {activities_inserted} inserted, {activities_seen - activities_inserted} already present\n"
        f"  reviews: {reviews_inserted} inserted, {reviews_seen - reviews_inserted} already present\n"
        f"  test attempts: {attempts_inserted} inserted, {attempts_seen - attempts_inserted} already present\n"
        f"All inserts are ON CONFLICT DO NOTHING/UPDATE — safe to re-run, nothing is ever deleted."
    )


if __name__ == "__main__":
    asyncio.run(main())
