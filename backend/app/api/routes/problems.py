import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import case, delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, get_optional_user
from app.core.security import SupabaseUser
from app.models.models import Problem, ProblemAttempt, ProblemConcept
from app.schemas.problems import ProblemMarkIn, ProblemOut

router = APIRouter()

_ROLE_ORDER = case((ProblemConcept.role == "primary", 0), (ProblemConcept.role == "supporting", 1), else_=2)
_DIFFICULTY_ORDER = case((Problem.difficulty == "easy", 0), (Problem.difficulty == "medium", 1), else_=2)


@router.get("/by-node/{node_id}", response_model=List[ProblemOut])
async def get_problems_by_node(
    node_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[SupabaseUser] = Depends(get_optional_user),
):
    """Problems mapped to a concept, grouped by role, with the caller's marks.
    `problems`/`problem_concepts` are a shared catalog with no owner to check —
    a node with zero mapped problems is a legitimate empty result, not a 404
    (114 of 126 DSA nodes have at least one; §2)."""
    rows = (
        await db.execute(
            select(Problem, ProblemConcept.role)
            .join(ProblemConcept, ProblemConcept.problem_id == Problem.id)
            .where(ProblemConcept.node_id == node_id)
            .order_by(_ROLE_ORDER, _DIFFICULTY_ORDER, Problem.external_id)
        )
    ).all()

    marked_by_problem_id = {}
    if current_user and rows:
        problem_ids = [row.Problem.id for row in rows]
        marked_rows = (
            await db.execute(
                select(ProblemAttempt.problem_id, ProblemAttempt.status).where(
                    ProblemAttempt.user_id == uuid.UUID(current_user.id),
                    ProblemAttempt.problem_id.in_(problem_ids),
                )
            )
        ).all()
        marked_by_problem_id = {m.problem_id: m.status for m in marked_rows}

    return [
        ProblemOut(
            id=row.Problem.id,
            external_id=row.Problem.external_id,
            slug=row.Problem.slug,
            title=row.Problem.title,
            difficulty=row.Problem.difficulty,
            url=row.Problem.url,
            paid_only=row.Problem.paid_only,
            role=row.role,
            marked_status=marked_by_problem_id.get(row.Problem.id),
        )
        for row in rows
    ]


@router.post("/{problem_id}/mark", status_code=status.HTTP_204_NO_CONTENT)
async def mark_problem(
    problem_id: uuid.UUID,
    body: ProblemMarkIn,
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Completion checkbox only — see models.ProblemAttempt and
    IMPLEMENTATION-problem-capture.md §1. Never touches learning_events or
    node_mastery. Upsert, so re-marking the same problem is one row."""
    if body.status not in ("solved", "attempted"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="status must be 'solved' or 'attempted'")

    user_id = uuid.UUID(current_user.id)

    problem_exists = (
        await db.execute(select(Problem.id).where(Problem.id == problem_id))
    ).scalar_one_or_none()
    if problem_exists is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")

    stmt = insert(ProblemAttempt).values(user_id=user_id, problem_id=problem_id, status=body.status)
    stmt = stmt.on_conflict_do_update(
        index_elements=["user_id", "problem_id"],
        set_={"status": body.status},
    )
    await db.execute(stmt)
    await db.commit()


@router.delete("/{problem_id}/mark", status_code=status.HTTP_204_NO_CONTENT)
async def unmark_problem(
    problem_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    user_id = uuid.UUID(current_user.id)
    await db.execute(
        delete(ProblemAttempt).where(ProblemAttempt.user_id == user_id, ProblemAttempt.problem_id == problem_id)
    )
    await db.commit()
