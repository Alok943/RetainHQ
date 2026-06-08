import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, get_optional_user
from app.core.security import SupabaseUser
from app.models.models import Roadmap, RoadmapNode, UserProgress
from app.schemas.roadmap import (
    RoadmapListItem,
    RoadmapDetailOut,
    RoadmapNodeOut,
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
            if user_id else False,
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
    if user_id:
        progress_rows = (
            await db.execute(
                select(UserProgress.node_id, UserProgress.status).where(
                    UserProgress.user_id == user_id,
                    UserProgress.node_id.in_([n.id for n in nodes]) if nodes else False,
                )
            )
        ).all()
        status_by_node = {nid: st for nid, st in progress_rows}

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
