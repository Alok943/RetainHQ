import uuid
from collections import deque
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func, case, false
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, get_optional_user
from app.core.security import SupabaseUser
from app.models.models import Roadmap, RoadmapNode, UserProgress, RoadmapNodePrerequisite
from app.schemas.roadmap import (
    RoadmapListItem,
    RoadmapDetailOut,
    RoadmapNodeOut,
    BlockerOut,
    BlockersOut,
    ProgressUpdate,
    ProgressResult,
)

router = APIRouter()


def _pct(done: int, total: int) -> int:
    return round((done / total) * 100) if total else 0


@router.get("/", response_model=List[RoadmapListItem])
async def list_roadmaps(
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser | None = Depends(get_optional_user),
):
    """List all roadmaps with the current user's real progress computed server-side."""
    user_id = uuid.UUID(current_user.id) if current_user else None

    done_node = case((UserProgress.status == "done", UserProgress.node_id))
    stmt = (
        select(
            Roadmap.id,
            Roadmap.title,
            Roadmap.description,
            func.count(func.distinct(RoadmapNode.id)).label("total_nodes"),
            func.count(func.distinct(done_node)).label("done_nodes"),
        )
        .outerjoin(RoadmapNode, RoadmapNode.roadmap_id == Roadmap.id)
        .outerjoin(
            UserProgress,
            (UserProgress.node_id == RoadmapNode.id)
            & (UserProgress.user_id == user_id)
            if user_id else false(),
        )
        .group_by(Roadmap.id, Roadmap.title, Roadmap.description)
        .order_by(Roadmap.created_at)
    )

    result = await db.execute(stmt)
    items = []
    for row in result.all():
        total, done = row.total_nodes or 0, row.done_nodes or 0
        items.append(
            RoadmapListItem(
                id=row.id,
                title=row.title,
                description=row.description,
                total_nodes=total,
                done_nodes=done,
                progress_pct=_pct(done, total),
            )
        )
    return items


@router.get("/{roadmap_id}", response_model=RoadmapDetailOut)
async def get_roadmap(
    roadmap_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser | None = Depends(get_optional_user),
):
    """Return a roadmap with all its nodes and the current user's progress per node."""
    user_id = uuid.UUID(current_user.id) if current_user else None

    roadmap = (
        await db.execute(select(Roadmap).where(Roadmap.id == roadmap_id))
    ).scalar_one_or_none()
    if not roadmap:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roadmap not found")

    # Nodes ordered as authored
    nodes = (
        (
            await db.execute(
                select(RoadmapNode)
                .where(RoadmapNode.roadmap_id == roadmap_id)
                .order_by(RoadmapNode.order_index)
            )
        )
        .scalars()
        .all()
    )

    # This user's progress for these nodes -> {node_id: status}
    status_by_node = {}
    if user_id and nodes:
        progress_rows = (
            await db.execute(
                select(UserProgress.node_id, UserProgress.status).where(
                    UserProgress.user_id == user_id,
                    UserProgress.node_id.in_([n.id for n in nodes]),
                )
            )
        ).all()
        status_by_node = {nid: st for nid, st in progress_rows}

    # Dependency edges among these nodes -> prerequisites + reverse (unlocks) per node.
    prereqs_by_node: dict = {}
    unlocks_by_node: dict = {}
    if nodes:
        edge_rows = (
            await db.execute(
                select(
                    RoadmapNodePrerequisite.node_id,
                    RoadmapNodePrerequisite.prerequisite_node_id,
                ).where(RoadmapNodePrerequisite.node_id.in_([n.id for n in nodes]))
            )
        ).all()
        for nid, pid in edge_rows:
            prereqs_by_node.setdefault(nid, []).append(pid)
            unlocks_by_node.setdefault(pid, []).append(nid)

    node_out = [
        RoadmapNodeOut(
            id=n.id,
            phase=n.phase,
            section=n.section,
            title=n.title,
            tier=n.tier,
            order_index=n.order_index,
            description=n.description,
            parent_id=n.parent_id,
            status=status_by_node.get(n.id, "not_started"),
            prerequisites=prereqs_by_node.get(n.id, []),
            unlocks=unlocks_by_node.get(n.id, []),
        )
        for n in nodes
    ]
    done = sum(1 for n in node_out if n.status == "done")
    total = len(node_out)

    return RoadmapDetailOut(
        id=roadmap.id,
        title=roadmap.title,
        description=roadmap.description,
        total_nodes=total,
        done_nodes=done,
        progress_pct=_pct(done, total),
        nodes=node_out,
    )


@router.get("/{roadmap_id}/blockers", response_model=BlockersOut)
async def get_roadmap_blockers(
    roadmap_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser | None = Depends(get_optional_user),
):
    """"Why am I stuck?" — diagnose the dependency graph against the user's progress.

    Returns the *ready frontier*: incomplete topics whose prerequisites are already
    done (so they can be started now), ranked by how many still-incomplete topics
    they transitively unblock. The biggest unlocks are the fastest way forward.
    Works for guests too (no progress -> everything incomplete -> the roadmap roots
    surface as the natural starting points).
    """
    user_id = uuid.UUID(current_user.id) if current_user else None

    exists = (
        await db.execute(select(Roadmap.id).where(Roadmap.id == roadmap_id))
    ).scalar_one_or_none()
    if not exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roadmap not found")

    node_rows = (
        await db.execute(
            select(RoadmapNode.id, RoadmapNode.title, RoadmapNode.section).where(
                RoadmapNode.roadmap_id == roadmap_id
            )
        )
    ).all()
    if not node_rows:
        return BlockersOut(roadmap_id=roadmap_id, total_incomplete=0, blockers=[])

    node_ids = [r.id for r in node_rows]
    title_by = {r.id: r.title for r in node_rows}
    section_by = {r.id: r.section for r in node_rows}

    status_by = {}
    if user_id:
        prog = (
            await db.execute(
                select(UserProgress.node_id, UserProgress.status).where(
                    UserProgress.user_id == user_id,
                    UserProgress.node_id.in_(node_ids),
                )
            )
        ).all()
        status_by = {nid: st for nid, st in prog}
    incomplete = {nid for nid in node_ids if status_by.get(nid) != "done"}

    edges = (
        await db.execute(
            select(
                RoadmapNodePrerequisite.node_id,
                RoadmapNodePrerequisite.prerequisite_node_id,
            ).where(RoadmapNodePrerequisite.node_id.in_(node_ids))
        )
    ).all()
    prereqs_of: dict = {}
    dependents_of: dict = {}
    for nid, pid in edges:
        prereqs_of.setdefault(nid, []).append(pid)
        dependents_of.setdefault(pid, []).append(nid)

    def downstream_incomplete(start: uuid.UUID) -> list:
        # BFS over dependents (graph is a DAG); collect still-incomplete descendants.
        seen: set = set()
        q = deque(dependents_of.get(start, []))
        while q:
            x = q.popleft()
            if x in seen:
                continue
            seen.add(x)
            q.extend(dependents_of.get(x, []))
        return [x for x in seen if x in incomplete]

    ranked = []
    for nid in incomplete:
        # "ready" = every prerequisite is already done.
        if all(p not in incomplete for p in prereqs_of.get(nid, [])):
            ds = downstream_incomplete(nid)
            if ds:
                ranked.append((nid, ds))
    ranked.sort(key=lambda t: (-len(t[1]), title_by[t[0]]))

    blockers = [
        BlockerOut(
            node_id=nid,
            title=title_by[nid],
            section=section_by[nid],
            unlocks_count=len(ds),
            unlocks_sample=[title_by[x] for x in ds[:3]],
        )
        for nid, ds in ranked[:6]
    ]
    return BlockersOut(roadmap_id=roadmap_id, total_incomplete=len(incomplete), blockers=blockers)


@router.put("/nodes/{node_id}/progress", response_model=ProgressResult)
async def set_node_progress(
    node_id: uuid.UUID,
    body: ProgressUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Mark a node done/not_started for the current user (idempotent upsert)."""
    user_id = uuid.UUID(current_user.id)

    if body.status not in ("done", "not_started"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="status must be 'done' or 'not_started'",
        )

    # Node must exist (avoids dangling progress rows)
    node = (
        await db.execute(select(RoadmapNode).where(RoadmapNode.id == node_id))
    ).scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")

    from sqlalchemy.dialects.postgresql import insert
    
    stmt = insert(UserProgress).values(
        user_id=user_id,
        node_id=node_id,
        status=body.status,
        updated_at=datetime.utcnow()
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=['user_id', 'node_id'],
        set_={"status": body.status, "updated_at": datetime.utcnow()}
    )
    
    await db.execute(stmt)
    await db.commit()
    
    return ProgressResult(node_id=node_id, status=body.status)
