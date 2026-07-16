"""
Teacher-facing classroom router (SPEC-teacher-dashboard.md §4). Roster/lifecycle
(§4.1) plus class analytics (§4.2), which are teacher-owner-only and scoped to
the classroom's assigned roadmaps + members — the privacy boundary (§4.2's
"Aggregation authorization rule", §5). Self-serve per-student aggregates are
reused via services/learner_stats.py (§4.3); the mastery model is
services/mastery.py (§3).
"""
import secrets
import uuid
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Date, bindparam, cast, delete, func, or_, select, text
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PG_UUID, insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.core.config import settings
from app.core.security import SupabaseUser
from app.models.models import (
    Activity,
    Classroom,
    ClassroomMember,
    ClassroomRoadmap,
    Review,
    Roadmap,
    RoadmapNode,
    RoadmapNodePrerequisite,
    TestAttempt,
)
from app.schemas.classroom import (
    ClassroomCreate,
    ClassroomOut,
    ClassroomOverviewOut,
    ClassroomPatch,
    ClassroomRoadmapsDetailOut,
    ClassroomRoadmapsIn,
    ClassroomRoadmapsOut,
    EnrolledClassroomOut,
    GapMapCellCounts,
    GapMapNodeOut,
    GapMapOut,
    JoinRequest,
    JoinResponse,
    MemberOut,
    MemberRename,
    MyClassroomsOut,
    RoadmapCoverageRow,
    RoadmapOptionOut,
    RosterOut,
    RosterRowOut,
    StudentDetailOut,
    StudentNodeMasteryOut,
    TeachingClassroomOut,
    WeeklyRecallBucket,
)
from app.services.mastery import (
    AT_RISK_RECALL_WINDOW,
    at_risk_flag,
    class_cell_status,
    compute_node_status,
    find_root_cause,
)
from app.services.learner_stats import (
    REVIEW_METRICS_MIN,
    get_heatmap as _get_learner_heatmap,
    get_node_accuracy as _get_learner_node_accuracy,
    get_review_metrics as _get_learner_review_metrics,
)

router = APIRouter()

# Unambiguous alphabet — no 0/O/1/I (spec §2). 8 digits + 24 letters = 32 symbols.
JOIN_CODE_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
JOIN_CODE_LENGTH = 8
_JOIN_CODE_GEN_ATTEMPTS = 5


def _generate_join_code() -> str:
    return "".join(secrets.choice(JOIN_CODE_ALPHABET) for _ in range(JOIN_CODE_LENGTH))


async def get_owned_classroom(
    classroom_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
) -> Classroom:
    """The IDOR wall: every teacher-scoped route depends on this. 404 (not 403)
    so a non-owner can't tell the classroom exists at all."""
    user_id = uuid.UUID(current_user.id)
    classroom = (
        await db.execute(
            select(Classroom).where(Classroom.id == classroom_id, Classroom.teacher_user_id == user_id)
        )
    ).scalar_one_or_none()
    if not classroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")
    return classroom


# --------------------------------------------------------------------------- #
# Roster / lifecycle (spec §4.1)
# --------------------------------------------------------------------------- #

@router.post("/", response_model=ClassroomOut, status_code=status.HTTP_201_CREATED)
async def create_classroom(
    body: ClassroomCreate,
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    user_id = uuid.UUID(current_user.id)

    active_count = (
        await db.execute(
            select(func.count())
            .select_from(Classroom)
            .where(Classroom.teacher_user_id == user_id, Classroom.archived_at.is_(None))
        )
    ).scalar_one()
    if active_count >= settings.MAX_CLASSROOMS_PER_TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You've reached the limit of {settings.MAX_CLASSROOMS_PER_TEACHER} classrooms — archive one to make room.",
        )

    school_name = (body.school_name or "").strip() or None
    classroom: Optional[Classroom] = None
    for _ in range(_JOIN_CODE_GEN_ATTEMPTS):
        candidate = Classroom(
            teacher_user_id=user_id,
            name=body.name.strip(),
            school_name=school_name,
            join_code=_generate_join_code(),
        )
        db.add(candidate)
        try:
            await db.flush()
            classroom = candidate
            break
        except IntegrityError:
            await db.rollback()
    if classroom is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not generate a unique join code — try again.",
        )

    await db.commit()
    await db.refresh(classroom)
    return classroom


@router.get("/mine", response_model=MyClassroomsOut)
async def get_my_classrooms(
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    user_id = uuid.UUID(current_user.id)

    teaching_stmt = (
        select(Classroom, func.count(ClassroomMember.id).label("member_count"))
        .outerjoin(ClassroomMember, ClassroomMember.classroom_id == Classroom.id)
        .where(Classroom.teacher_user_id == user_id, Classroom.archived_at.is_(None))
        .group_by(Classroom.id)
        .order_by(Classroom.created_at.desc())
    )
    teaching_rows = (await db.execute(teaching_stmt)).all()
    teaching = [
        TeachingClassroomOut(
            id=c.id, name=c.name, school_name=c.school_name, join_code=c.join_code,
            archived_at=c.archived_at, created_at=c.created_at, member_count=cnt or 0,
        )
        for c, cnt in teaching_rows
    ]

    # Students see the class name only — no teacher identity (spec §4.1/§5).
    enrolled_stmt = (
        select(
            Classroom.id, Classroom.name, Classroom.school_name,
            ClassroomMember.display_name, ClassroomMember.joined_at,
        )
        .join(ClassroomMember, ClassroomMember.classroom_id == Classroom.id)
        .where(ClassroomMember.student_user_id == user_id, Classroom.archived_at.is_(None))
        .order_by(ClassroomMember.joined_at.desc())
    )
    enrolled_rows = (await db.execute(enrolled_stmt)).all()
    enrolled = [
        EnrolledClassroomOut(
            id=r.id, name=r.name, school_name=r.school_name,
            display_name=r.display_name, joined_at=r.joined_at,
        )
        for r in enrolled_rows
    ]

    return MyClassroomsOut(teaching=teaching, enrolled=enrolled)


@router.post("/join", response_model=JoinResponse)
async def join_classroom(
    body: JoinRequest,
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Resolve a join code -> upsert membership. 404 for unknown OR archived
    codes with the same shape (don't leak which). Idempotent re-join updates
    display_name rather than erroring (uq_class_student).

    NOTE: join-attempt throttling is deferred to Phase 1 (spec §6/§8) — not
    built here.
    """
    user_id = uuid.UUID(current_user.id)
    code = body.code.strip().upper()

    classroom = (
        await db.execute(
            select(Classroom).where(Classroom.join_code == code, Classroom.archived_at.is_(None))
        )
    ).scalar_one_or_none()
    if not classroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid class code")

    display_name = body.display_name.strip()
    stmt = (
        insert(ClassroomMember)
        .values(classroom_id=classroom.id, student_user_id=user_id, display_name=display_name)
        .on_conflict_do_update(
            index_elements=["classroom_id", "student_user_id"],
            set_={"display_name": display_name},
        )
        .returning(ClassroomMember.id, ClassroomMember.display_name)
    )
    row = (await db.execute(stmt)).one()
    await db.commit()

    return JoinResponse(
        classroom_id=classroom.id,
        classroom_name=classroom.name,
        school_name=classroom.school_name,
        member_id=row.id,
        display_name=row.display_name,
    )


@router.patch("/{classroom_id}", response_model=ClassroomOut)
async def update_classroom(
    classroom_id: uuid.UUID,
    body: ClassroomPatch,
    db: AsyncSession = Depends(get_db),
    classroom: Classroom = Depends(get_owned_classroom),
):
    if body.name is not None:
        classroom.name = body.name.strip()
    if body.school_name is not None:
        classroom.school_name = body.school_name.strip() or None
    if body.archived is True:
        classroom.archived_at = datetime.utcnow()
    elif body.archived is False:
        classroom.archived_at = None

    if body.regenerate_join_code:
        new_code = None
        for _ in range(_JOIN_CODE_GEN_ATTEMPTS):
            candidate = _generate_join_code()
            clash = (
                await db.execute(select(Classroom.id).where(Classroom.join_code == candidate))
            ).scalar_one_or_none()
            if not clash:
                new_code = candidate
                break
        if new_code is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not generate a unique join code — try again.",
            )
        classroom.join_code = new_code  # overwrite invalidates the old code

    db.add(classroom)
    await db.commit()
    await db.refresh(classroom)
    return classroom


@router.delete("/{classroom_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    classroom_id: uuid.UUID,
    member_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    classroom: Classroom = Depends(get_owned_classroom),
):
    result = await db.execute(
        delete(ClassroomMember).where(ClassroomMember.id == member_id, ClassroomMember.classroom_id == classroom.id)
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    await db.commit()


@router.delete("/{classroom_id}/membership", status_code=status.HTTP_204_NO_CONTENT)
async def leave_classroom(
    classroom_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Student-scoped, no ownership check — a member leaves their own row."""
    user_id = uuid.UUID(current_user.id)
    result = await db.execute(
        delete(ClassroomMember).where(
            ClassroomMember.classroom_id == classroom_id, ClassroomMember.student_user_id == user_id
        )
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")
    await db.commit()


@router.patch("/{classroom_id}/members/{member_id}", response_model=MemberOut)
async def rename_member(
    classroom_id: uuid.UUID,
    member_id: uuid.UUID,
    body: MemberRename,
    db: AsyncSession = Depends(get_db),
    classroom: Classroom = Depends(get_owned_classroom),
):
    member = (
        await db.execute(
            select(ClassroomMember).where(ClassroomMember.id == member_id, ClassroomMember.classroom_id == classroom.id)
        )
    ).scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    member.display_name = body.display_name.strip()
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member


@router.put("/{classroom_id}/roadmaps", response_model=ClassroomRoadmapsOut)
async def set_classroom_roadmaps(
    classroom_id: uuid.UUID,
    body: ClassroomRoadmapsIn,
    db: AsyncSession = Depends(get_db),
    classroom: Classroom = Depends(get_owned_classroom),
):
    ids = list(dict.fromkeys(body.roadmap_ids))  # de-dupe, preserve order
    if ids:
        valid_ids = set(
            (
                await db.execute(
                    select(Roadmap.id).where(
                        Roadmap.id.in_(ids), Roadmap.user_id.is_(None), Roadmap.audience == "school"
                    )
                )
            ).scalars().all()
        )
        invalid = [str(i) for i in ids if i not in valid_ids]
        if invalid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Not valid school-catalog roadmaps: {', '.join(invalid)}",
            )

    await db.execute(delete(ClassroomRoadmap).where(ClassroomRoadmap.classroom_id == classroom.id))
    for rid in ids:
        db.add(ClassroomRoadmap(classroom_id=classroom.id, roadmap_id=rid))
    await db.commit()
    return ClassroomRoadmapsOut(roadmap_ids=ids)


@router.get("/{classroom_id}/roadmaps", response_model=ClassroomRoadmapsDetailOut)
async def get_classroom_roadmaps(
    classroom_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    classroom: Classroom = Depends(get_owned_classroom),
):
    """GET counterpart to the PUT above — drives the frontend's assignment
    control (which roadmap_ids are already assigned, and what's assignable:
    catalog-only, audience='school', same validation the PUT enforces)."""
    assigned = await _assigned_roadmap_ids(db, classroom.id)
    available_rows = (
        await db.execute(
            select(Roadmap.id, Roadmap.title)
            .where(Roadmap.user_id.is_(None), Roadmap.audience == "school")
            .order_by(Roadmap.title)
        )
    ).all()
    return ClassroomRoadmapsDetailOut(
        roadmap_ids=assigned,
        available=[RoadmapOptionOut(id=r.id, title=r.title) for r in available_rows],
    )


# --------------------------------------------------------------------------- #
# Analytics helpers (spec §4.2 — the privacy boundary lives in these clauses)
# --------------------------------------------------------------------------- #

async def _member_rows(db: AsyncSession, classroom_id: uuid.UUID) -> list[ClassroomMember]:
    return list(
        (await db.execute(select(ClassroomMember).where(ClassroomMember.classroom_id == classroom_id)))
        .scalars()
        .all()
    )


async def _assigned_roadmap_ids(db: AsyncSession, classroom_id: uuid.UUID) -> list[uuid.UUID]:
    return list(
        (
            await db.execute(
                select(ClassroomRoadmap.roadmap_id).where(ClassroomRoadmap.classroom_id == classroom_id)
            )
        )
        .scalars()
        .all()
    )


async def _scoped_nodes(db: AsyncSession, roadmap_ids: list[uuid.UUID]) -> list[RoadmapNode]:
    if not roadmap_ids:
        return []
    return list(
        (
            await db.execute(
                select(RoadmapNode)
                .where(RoadmapNode.roadmap_id.in_(roadmap_ids))
                .order_by(RoadmapNode.phase, RoadmapNode.section, RoadmapNode.order_index)
            )
        )
        .scalars()
        .all()
    )


def _activity_scope_clause(roadmap_ids: list[uuid.UUID], node_ids: list[uuid.UUID]):
    """The privacy boundary made executable: an Activity/Review only counts
    toward classroom analytics if it's linked to one of the classroom's
    assigned roadmaps (directly, or via one of that roadmap's nodes). A
    student's career/personal-roadmap or free-form activity never matches."""
    return or_(Activity.roadmap_id.in_(roadmap_ids), Activity.node_id.in_(node_ids))


async def _last_active_map(
    db: AsyncSession, student_ids: list[uuid.UUID], activity_scope
) -> dict[uuid.UUID, datetime]:
    last_activity = dict(
        (
            await db.execute(
                select(Activity.user_id, func.max(Activity.created_at))
                .where(Activity.user_id.in_(student_ids), activity_scope)
                .group_by(Activity.user_id)
            )
        ).all()
    )
    last_review = dict(
        (
            await db.execute(
                select(Review.user_id, func.max(Review.completed_at))
                .select_from(Review)
                .join(Activity, Review.activity_id == Activity.id)
                .where(Review.user_id.in_(student_ids), Review.status == "completed", activity_scope)
                .group_by(Review.user_id)
            )
        ).all()
    )
    merged = dict(last_activity)
    for uid, ts in last_review.items():
        if ts is not None and (merged.get(uid) is None or ts > merged[uid]):
            merged[uid] = ts
    return merged


async def _overdue_map(
    db: AsyncSession, student_ids: list[uuid.UUID], activity_scope, now: datetime
) -> dict[uuid.UUID, int]:
    return dict(
        (
            await db.execute(
                select(Review.user_id, func.count(Review.id))
                .select_from(Review)
                .join(Activity, Review.activity_id == Activity.id)
                .where(
                    Review.user_id.in_(student_ids), Review.status == "due",
                    Review.scheduled_for < now, activity_scope,
                )
                .group_by(Review.user_id)
            )
        ).all()
    )


# Postgres-only (window function) — same untestable-on-SQLite boundary as
# learner_stats.py's node-accuracy SQL.
_RECALL_LAST_N_SQL = text("""
    select user_id, avg(case when recalled then 1.0 else 0.0 end) as recall_rate
    from (
        select r.user_id, r.recalled,
               row_number() over (partition by r.user_id order by r.completed_at desc) as rn
        from reviews r
        join activities a on a.id = r.activity_id
        where r.status = 'completed'
          and r.user_id = any(:student_ids)
          and (a.roadmap_id = any(:roadmap_ids) or a.node_id = any(:node_ids))
    ) sub
    where rn <= :window_size
    group by user_id
""").bindparams(
    bindparam("student_ids", type_=ARRAY(PG_UUID)),
    bindparam("roadmap_ids", type_=ARRAY(PG_UUID)),
    bindparam("node_ids", type_=ARRAY(PG_UUID)),
)


async def _recall_rate_last_n(
    db: AsyncSession, student_ids: list[uuid.UUID], roadmap_ids: list[uuid.UUID], node_ids: list[uuid.UUID]
) -> dict[uuid.UUID, float]:
    rows = (
        await db.execute(
            _RECALL_LAST_N_SQL,
            {
                "student_ids": student_ids,
                "roadmap_ids": roadmap_ids,
                "node_ids": node_ids,
                "window_size": AT_RISK_RECALL_WINDOW,
            },
        )
    ).all()
    return {r.user_id: round(r.recall_rate, 3) for r in rows}


async def _at_risk_map(
    db: AsyncSession,
    student_ids: list[uuid.UUID],
    roadmap_ids: list[uuid.UUID],
    node_ids: list[uuid.UUID],
    activity_scope,
    now: datetime,
) -> dict[uuid.UUID, tuple[bool, list[str]]]:
    last_active = await _last_active_map(db, student_ids, activity_scope)
    overdue = await _overdue_map(db, student_ids, activity_scope, now)
    recall10 = await _recall_rate_last_n(db, student_ids, roadmap_ids, node_ids)
    return {
        sid: at_risk_flag(last_active.get(sid), now, recall10.get(sid), overdue.get(sid, 0))
        for sid in student_ids
    }


def _current_streak(active_dates: set, now: datetime) -> int:
    today = now.date()
    yesterday = today - timedelta(days=1)
    if today in active_dates:
        anchor = today
    elif yesterday in active_dates:
        anchor = yesterday
    else:
        return 0
    streak = 0
    cursor = anchor
    while cursor in active_dates:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


# Postgres-only (jsonb_array_elements) — same convention as
# learner_stats.py's _NODE_ACCURACY_SQL, grouped per (student, roadmap, node
# title) instead of per-caller so it covers the whole class in one round trip.
_CLASS_NODE_TEST_SQL = text("""
    select
        ta.user_id, ta.roadmap_id,
        elem->>'node_title' as node_title,
        count(*) filter (where elem->>'outcome' = 'got') as got,
        count(*) filter (where elem->>'outcome' = 'missed') as missed,
        count(*) filter (where elem->>'outcome' = 'wrong') as wrong
    from test_attempts ta, jsonb_array_elements(ta.results) as elem
    where ta.user_id = any(:student_ids) and ta.roadmap_id = any(:roadmap_ids)
    group by ta.user_id, ta.roadmap_id, elem->>'node_title'
""").bindparams(
    bindparam("student_ids", type_=ARRAY(PG_UUID)),
    bindparam("roadmap_ids", type_=ARRAY(PG_UUID)),
)


async def _node_status_matrix(
    db: AsyncSession,
    student_ids: list[uuid.UUID],
    roadmap_ids: list[uuid.UUID],
    nodes: list[RoadmapNode],
) -> dict[tuple[uuid.UUID, uuid.UUID], str]:
    """{(node_id, student_id): status}, folding test_attempts + node-linked
    activity/review history through services/mastery.compute_node_status —
    two grouped queries for the whole class, never N+1 per student."""
    if not student_ids or not roadmap_ids or not nodes:
        return {}

    node_ids = [n.id for n in nodes]
    node_id_by_title_roadmap = {(n.roadmap_id, n.title): n.id for n in nodes}

    test_rows = (
        await db.execute(_CLASS_NODE_TEST_SQL, {"student_ids": student_ids, "roadmap_ids": roadmap_ids})
    ).all()
    test_by_student_node: dict[tuple, tuple[int, int, int]] = {}
    for row in test_rows:
        nid = node_id_by_title_roadmap.get((row.roadmap_id, row.node_title))
        if nid is None:
            continue
        test_by_student_node[(row.user_id, nid)] = (row.got, row.missed, row.wrong)

    review_rows = (
        await db.execute(
            select(Activity.user_id, Activity.node_id, Activity.stability, Review.recalled, Review.completed_at)
            .select_from(Activity)
            .join(Review, Review.activity_id == Activity.id)
            .where(
                Activity.user_id.in_(student_ids),
                Activity.node_id.in_(node_ids),
                Review.status == "completed",
            )
            .order_by(Activity.user_id, Activity.node_id, Review.completed_at)
        )
    ).all()
    history: dict[tuple, list[bool]] = defaultdict(list)
    stability_by: dict[tuple, float] = {}
    for uid, nid, stability, recalled, _completed_at in review_rows:
        history[(uid, nid)].append(bool(recalled))
        if stability is not None:
            stability_by[(uid, nid)] = stability

    status_by: dict[tuple, str] = {}
    for n in nodes:
        for sid in student_ids:
            got, missed, wrong = test_by_student_node.get((sid, n.id), (0, 0, 0))
            recalled_history = history.get((sid, n.id), [])
            stability = stability_by.get((sid, n.id))
            status_by[(n.id, sid)] = compute_node_status(got, missed, wrong, recalled_history, stability)
    return status_by


async def _weak_node_counts(
    db: AsyncSession, student_ids: list[uuid.UUID], roadmap_ids: list[uuid.UUID], nodes: list[RoadmapNode]
) -> dict[uuid.UUID, int]:
    status_by = await _node_status_matrix(db, student_ids, roadmap_ids, nodes)
    counts: dict[uuid.UUID, int] = defaultdict(int)
    for (_nid, sid), st in status_by.items():
        if st == "weak":
            counts[sid] += 1
    return counts


async def _roadmap_coverage(
    db: AsyncSession, roadmap_ids: list[uuid.UUID], student_ids: list[uuid.UUID], member_count: int
) -> list[RoadmapCoverageRow]:
    if not roadmap_ids or member_count == 0:
        return []
    roadmap_rows = (
        await db.execute(select(Roadmap.id, Roadmap.title).where(Roadmap.id.in_(roadmap_ids)))
    ).all()
    rows = []
    for rid, title in roadmap_rows:
        node_ids = [n.id for n in await _scoped_nodes(db, [rid])]
        scope = _activity_scope_clause([rid], node_ids)
        act_users = set(
            (
                await db.execute(
                    select(Activity.user_id).distinct().where(Activity.user_id.in_(student_ids), scope)
                )
            ).scalars().all()
        )
        test_users = set(
            (
                await db.execute(
                    select(TestAttempt.user_id)
                    .distinct()
                    .where(TestAttempt.user_id.in_(student_ids), TestAttempt.roadmap_id == rid)
                )
            ).scalars().all()
        )
        covered = len(act_users | test_users)
        rows.append(RoadmapCoverageRow(roadmap_id=rid, title=title, coverage_pct=round(covered / member_count * 100)))
    return rows


def _bucket_heatmap_into_weeks(days: list, weeks: int = 8) -> list[WeeklyRecallBucket]:
    """Buckets learner_stats.get_heatmap's daily days[] into `weeks` Monday-
    aligned weekly buckets ending at the current week (server-side, per spec
    §4.2's student drill-down)."""
    today = datetime.utcnow().date()
    this_monday = today - timedelta(days=today.weekday())
    week_starts = [this_monday - timedelta(weeks=w) for w in range(weeks - 1, -1, -1)]
    buckets = {ws: {"count": 0, "recalled": 0} for ws in week_starts}
    earliest = week_starts[0]

    for day in days:
        d = date.fromisoformat(day.date)
        if d < earliest:
            continue
        week_start = d - timedelta(days=d.weekday())
        if week_start in buckets:
            buckets[week_start]["count"] += day.count
            buckets[week_start]["recalled"] += day.recalled

    result = []
    for ws in week_starts:
        b = buckets[ws]
        rate = round(b["recalled"] / b["count"], 3) if b["count"] else None
        result.append(
            WeeklyRecallBucket(week_start=ws.isoformat(), count=b["count"], recalled=b["recalled"], recall_rate=rate)
        )
    return result


# --------------------------------------------------------------------------- #
# Class analytics endpoints (spec §4.2)
# --------------------------------------------------------------------------- #

@router.get("/{classroom_id}/overview", response_model=ClassroomOverviewOut)
async def get_classroom_overview(
    classroom_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    classroom: Classroom = Depends(get_owned_classroom),
):
    members = await _member_rows(db, classroom.id)
    member_count = len(members)
    if member_count == 0:
        return ClassroomOverviewOut(member_count=0, active_last_7d=0, reviews_completed_7d=0, at_risk_count=0)
    student_ids = [m.student_user_id for m in members]

    roadmap_ids = await _assigned_roadmap_ids(db, classroom.id)
    if not roadmap_ids:
        return ClassroomOverviewOut(
            member_count=member_count, active_last_7d=0, reviews_completed_7d=0, at_risk_count=0
        )

    nodes = await _scoped_nodes(db, roadmap_ids)
    node_ids = [n.id for n in nodes]
    activity_scope = _activity_scope_clause(roadmap_ids, node_ids)
    now = datetime.utcnow()
    seven_days_ago = now - timedelta(days=7)

    active_from_activities = set(
        (
            await db.execute(
                select(Activity.user_id)
                .distinct()
                .where(Activity.user_id.in_(student_ids), Activity.created_at >= seven_days_ago, activity_scope)
            )
        ).scalars().all()
    )

    review_stmt = (
        select(
            Review.user_id,
            func.count(Review.id).label("completed"),
            func.count(Review.id).filter(Review.recalled == True).label("recalled"),
        )
        .select_from(Review)
        .join(Activity, Review.activity_id == Activity.id)
        .where(
            Review.user_id.in_(student_ids), Review.status == "completed",
            Review.completed_at >= seven_days_ago, activity_scope,
        )
        .group_by(Review.user_id)
    )
    review_rows = (await db.execute(review_stmt)).all()
    active_last_7d = len(active_from_activities | {r.user_id for r in review_rows})

    reviews_completed_7d = sum(r.completed for r in review_rows)
    total_recalled = sum(r.recalled for r in review_rows)
    class_recall_rate = round(total_recalled / reviews_completed_7d, 3) if reviews_completed_7d else None

    at_risk_map = await _at_risk_map(db, student_ids, roadmap_ids, node_ids, activity_scope, now)
    at_risk_count = sum(1 for is_at_risk, _reasons in at_risk_map.values() if is_at_risk)

    coverage = await _roadmap_coverage(db, roadmap_ids, student_ids, member_count)

    return ClassroomOverviewOut(
        member_count=member_count,
        active_last_7d=active_last_7d,
        reviews_completed_7d=reviews_completed_7d,
        class_recall_rate_7d=class_recall_rate,
        enough_data_for_recall_rate=reviews_completed_7d >= REVIEW_METRICS_MIN,
        at_risk_count=at_risk_count,
        roadmap_coverage=coverage,
    )


@router.get("/{classroom_id}/gap-map", response_model=GapMapOut)
async def get_gap_map(
    classroom_id: uuid.UUID,
    roadmap_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    classroom: Classroom = Depends(get_owned_classroom),
):
    assigned = await _assigned_roadmap_ids(db, classroom.id)
    if roadmap_id not in assigned:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Roadmap is not assigned to this classroom"
        )

    members = await _member_rows(db, classroom.id)
    if not members:
        return GapMapOut(roadmap_id=roadmap_id, nodes=[])
    student_ids = [m.student_user_id for m in members]
    member_id_by_student = {m.student_user_id: m.id for m in members}

    nodes = await _scoped_nodes(db, [roadmap_id])
    if not nodes:
        return GapMapOut(roadmap_id=roadmap_id, nodes=[])

    status_by = await _node_status_matrix(db, student_ids, [roadmap_id], nodes)

    node_ids = [n.id for n in nodes]
    prereq_rows = (
        await db.execute(
            select(RoadmapNodePrerequisite.node_id, RoadmapNodePrerequisite.prerequisite_node_id).where(
                RoadmapNodePrerequisite.node_id.in_(node_ids)
            )
        )
    ).all()
    prereqs_by_node: dict[uuid.UUID, list[uuid.UUID]] = defaultdict(list)
    for nid, pid in prereq_rows:
        prereqs_by_node[nid].append(pid)

    # Reshape for find_root_cause's {prereq_node_id: {student_id: status}} contract.
    status_by_node: dict[uuid.UUID, dict[uuid.UUID, str]] = defaultdict(dict)
    for (nid, sid), st in status_by.items():
        status_by_node[nid][sid] = st

    total_students = len(student_ids)
    out_nodes = []
    for n in nodes:
        counts = GapMapCellCounts()
        weak_student_ids: set = set()
        for sid in student_ids:
            st = status_by.get((n.id, sid), "untouched")
            setattr(counts, st, getattr(counts, st) + 1)
            if st == "weak":
                weak_student_ids.add(sid)

        cell_status = class_cell_status(counts.model_dump(), total_students)
        root_cause = find_root_cause(n.id, weak_student_ids, prereqs_by_node.get(n.id, []), status_by_node)
        out_nodes.append(
            GapMapNodeOut(
                node_id=n.id, title=n.title, phase=n.phase, section=n.section,
                status=cell_status, counts=counts,
                weak_students=[member_id_by_student[sid] for sid in weak_student_ids],
                root_cause_node_id=root_cause,
            )
        )
    return GapMapOut(roadmap_id=roadmap_id, nodes=out_nodes)


@router.get("/{classroom_id}/students", response_model=RosterOut)
async def get_roster(
    classroom_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    classroom: Classroom = Depends(get_owned_classroom),
):
    members = await _member_rows(db, classroom.id)
    if not members:
        return RosterOut(students=[])
    student_ids = [m.student_user_id for m in members]
    now = datetime.utcnow()

    roadmap_ids = await _assigned_roadmap_ids(db, classroom.id)
    if not roadmap_ids:
        return RosterOut(students=[RosterRowOut(member_id=m.id, display_name=m.display_name) for m in members])

    nodes = await _scoped_nodes(db, roadmap_ids)
    node_ids = [n.id for n in nodes]
    activity_scope = _activity_scope_clause(roadmap_ids, node_ids)
    seven_days_ago = now - timedelta(days=7)

    last_active = await _last_active_map(db, student_ids, activity_scope)
    overdue = await _overdue_map(db, student_ids, activity_scope, now)
    recall10 = await _recall_rate_last_n(db, student_ids, roadmap_ids, node_ids)

    review_7d_rows = (
        await db.execute(
            select(
                Review.user_id,
                func.count(Review.id).label("completed"),
                func.count(Review.id).filter(Review.recalled == True).label("recalled"),
            )
            .select_from(Review)
            .join(Activity, Review.activity_id == Activity.id)
            .where(
                Review.user_id.in_(student_ids), Review.status == "completed",
                Review.completed_at >= seven_days_ago, activity_scope,
            )
            .group_by(Review.user_id)
        )
    ).all()
    review_7d_by_student = {r.user_id: r for r in review_7d_rows}

    streak_day_rows = (
        await db.execute(
            select(Review.user_id, cast(Review.completed_at, Date))
            .select_from(Review)
            .join(Activity, Review.activity_id == Activity.id)
            .where(Review.user_id.in_(student_ids), Review.status == "completed", activity_scope)
            .distinct()
        )
    ).all()
    active_dates_by_student: dict[uuid.UUID, set] = defaultdict(set)
    for uid, day in streak_day_rows:
        active_dates_by_student[uid].add(day)

    weak_counts = await _weak_node_counts(db, student_ids, roadmap_ids, nodes)

    students = []
    for m in members:
        sid = m.student_user_id
        r7 = review_7d_by_student.get(sid)
        completed_7d = r7.completed if r7 else 0
        recalled_7d = r7.recalled if r7 else 0
        recall_rate = round(recalled_7d / completed_7d, 3) if completed_7d else None
        overdue_count = overdue.get(sid, 0)
        is_at_risk, reasons = at_risk_flag(last_active.get(sid), now, recall10.get(sid), overdue_count)
        students.append(
            RosterRowOut(
                member_id=m.id,
                display_name=m.display_name,
                last_active_at=last_active.get(sid),
                reviews_completed_7d=completed_7d,
                recall_rate=recall_rate,
                current_streak=_current_streak(active_dates_by_student.get(sid, set()), now),
                weak_node_count=weak_counts.get(sid, 0),
                overdue_count=overdue_count,
                at_risk=is_at_risk,
                at_risk_reasons=reasons,
            )
        )
    return RosterOut(students=students)


@router.get("/{classroom_id}/students/{member_id}", response_model=StudentDetailOut)
async def get_student_detail(
    classroom_id: uuid.UUID,
    member_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    classroom: Classroom = Depends(get_owned_classroom),
):
    """Drill-down: verifies the member belongs to THIS classroom, then calls
    the shared learner_stats functions scoped to the member's student_user_id +
    this classroom's assigned roadmaps — never unscoped (that would leak the
    student's non-classroom life, spec §4.2/§5)."""
    member = (
        await db.execute(
            select(ClassroomMember).where(ClassroomMember.id == member_id, ClassroomMember.classroom_id == classroom.id)
        )
    ).scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found in this classroom")

    roadmap_ids = await _assigned_roadmap_ids(db, classroom.id)  # [] is valid — scopes to nothing, not "unscoped"
    student_id = member.student_user_id

    review_metrics = await _get_learner_review_metrics(db, student_id, roadmap_ids)
    heatmap = await _get_learner_heatmap(db, student_id, roadmap_ids)
    node_accuracy = await _get_learner_node_accuracy(db, student_id, roadmap_ids)

    nodes = await _scoped_nodes(db, roadmap_ids)
    node_mastery = []
    if nodes:
        status_by = await _node_status_matrix(db, [student_id], roadmap_ids, nodes)
        node_mastery = [
            StudentNodeMasteryOut(
                node_id=n.id, title=n.title, phase=n.phase, section=n.section,
                status=status_by.get((n.id, student_id), "untouched"),
            )
            for n in nodes
        ]

    weekly_trend = _bucket_heatmap_into_weeks(heatmap.days, weeks=8)

    return StudentDetailOut(
        member_id=member.id,
        display_name=member.display_name,
        joined_at=member.joined_at,
        review_metrics=review_metrics.model_dump(),
        node_accuracy=node_accuracy.model_dump(),
        node_mastery=node_mastery,
        weekly_recall_trend=weekly_trend,
    )
