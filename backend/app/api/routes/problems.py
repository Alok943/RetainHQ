import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import case, delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, get_optional_user
from app.core.security import SupabaseUser
from app.models.models import Problem, ProblemAttempt, ProblemConcept, RoadmapNode, CareerGoal, NodeMastery, LearningEvent
from app.schemas.problems import ProblemMarkIn, ProblemOut, ProblemSearchOut
from datetime import datetime, timedelta, timezone

router = APIRouter()

_ROLE_ORDER = case((ProblemConcept.role == "primary", 0), (ProblemConcept.role == "supporting", 1), else_=2)
_DIFFICULTY_ORDER = case((Problem.difficulty == "easy", 0), (Problem.difficulty == "medium", 1), else_=2)

def _get_confidence_band(conf: Optional[float]) -> Optional[str]:
    if conf is None: return None
    if conf >= 0.85: return "high"
    if conf >= 0.55: return "medium"
    return "low"

@router.get("/search", response_model=List[ProblemSearchOut])
async def search_problems(
    q: str,
    limit: int = 8,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[SupabaseUser] = Depends(get_optional_user)
):
    """Typeahead search for problems. Returns ranked matches."""
    q = q.strip()
    if not q:
        return []
    
    # escape LIKE patterns
    q_like = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    
    is_digit = q.isdigit()
    
    query = select(
        Problem,
        ProblemConcept.node_id,
        ProblemConcept.confidence,
        RoadmapNode.title.label("node_title")
    ).outerjoin(
        ProblemConcept, (ProblemConcept.problem_id == Problem.id) & (ProblemConcept.role == 'primary')
    ).outerjoin(
        RoadmapNode, ProblemConcept.node_id == RoadmapNode.id
    )

    if is_digit:
        q_num = int(q)
        query = query.where(
            (Problem.external_id == q_num) | 
            (Problem.title.ilike(f"%{q_like}%", escape="\\"))
        )
    else:
        q_lower = q.lower()
        query = query.where(
            (Problem.title.ilike(f"%{q_like}%", escape="\\")) |
            (Problem.slug.ilike(f"%{q_like}%", escape="\\"))
        )
        
    rows = (await db.execute(query)).all()
    
    logged_problem_ids = set()
    active_goal_node_ids = set()
    weak_node_ids = set()
    exposed_nodes = set()
    recent_node_ids = set()
    
    if current_user:
        user_uuid = uuid.UUID(current_user.id)
        
        attempts = (await db.execute(select(ProblemAttempt.problem_id).where(ProblemAttempt.user_id == user_uuid))).scalars().all()
        logged_problem_ids = set(attempts)
        
        goal = (await db.execute(select(CareerGoal.roadmap_id).where(CareerGoal.user_id == user_uuid, CareerGoal.status == "active"))).scalar_one_or_none()
        if goal:
            goal_nodes = (await db.execute(select(RoadmapNode.id).where(RoadmapNode.roadmap_id == goal))).scalars().all()
            active_goal_node_ids = set(goal_nodes)
            
        masteries = (await db.execute(select(NodeMastery.node_id, NodeMastery.m_learned).where(NodeMastery.user_id == user_uuid))).all()
        weak_node_ids = {m.node_id for m in masteries if m.m_learned < 0.5}
        exposed_nodes = {m.node_id for m in masteries}
        
        seven_days_ago = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=7)
        recent_nodes = (await db.execute(select(LearningEvent.node_id).where(
            LearningEvent.user_id == user_uuid,
            LearningEvent.node_id.is_not(None),
            LearningEvent.occurred_at >= seven_days_ago
        ))).scalars().all()
        recent_node_ids = set(recent_nodes)

    results = []
    q_lower = q.lower()
    for row in rows:
        p = row.Problem
        node_id = row.node_id
        
        tier = 0
        if is_digit:
            if p.external_id == int(q):
                tier = 100
            elif str(p.external_id) in q or q in p.title.lower():
                tier = 60
        else:
            p_title_lower = p.title.lower()
            if p_title_lower == q_lower:
                tier = 100
            elif p_title_lower.startswith(q_lower):
                tier = 80
            elif any(word.startswith(q_lower) for word in p_title_lower.split()):
                tier = 70
            elif q_lower in p_title_lower:
                tier = 50
            elif q_lower in p.slug:
                tier = 40
                
        if tier == 0:
            continue
            
        boost = 0
        if current_user and node_id:
            if node_id in active_goal_node_ids:
                boost += 15
            if node_id in weak_node_ids or node_id not in exposed_nodes:
                boost += 10
            if node_id in recent_node_ids:
                boost += 8
                
        if p.id in logged_problem_ids:
            boost -= 20
            
        results.append({
            "tier": tier,
            "boost": boost,
            "external_id": p.external_id,
            "out": ProblemSearchOut(
                id=p.id,
                external_id=p.external_id,
                title=p.title,
                slug=p.slug,
                difficulty=p.difficulty,
                url=p.url,
                paid_only=p.paid_only,
                node_id=node_id,
                node_title=row.node_title,
                confidence_band=_get_confidence_band(row.confidence),
                already_logged=(p.id in logged_problem_ids)
            )
        })
        
    results.sort(key=lambda x: (-x["tier"], -x["boost"], x["external_id"]))
    return [r["out"] for r in results[:limit]]

@router.get("/suggest", response_model=List[ProblemSearchOut])
async def suggest_problems(
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user)
):
    user_uuid = uuid.UUID(current_user.id)
    
    attempts = (await db.execute(select(ProblemAttempt.problem_id).where(ProblemAttempt.user_id == user_uuid))).scalars().all()
    logged_problem_ids = set(attempts)
    
    masteries = (await db.execute(select(NodeMastery.node_id, NodeMastery.m_learned).where(NodeMastery.user_id == user_uuid))).all()
    
    # rank nodes by weakness
    weakest_nodes = sorted(masteries, key=lambda m: m.m_learned)
    
    suggestions = []
    
    # helper to find an unlogged problem for a node
    async def get_problem_for_node(node_id: uuid.UUID, reason: str):
        query = select(
            Problem,
            ProblemConcept.node_id,
            ProblemConcept.confidence,
            RoadmapNode.title.label("node_title")
        ).join(
            ProblemConcept, (ProblemConcept.problem_id == Problem.id) & (ProblemConcept.role == 'primary')
        ).join(
            RoadmapNode, ProblemConcept.node_id == RoadmapNode.id
        ).where(
            ProblemConcept.node_id == node_id
        )
        if logged_problem_ids:
            query = query.where(Problem.id.not_in(logged_problem_ids))
        
        query = query.order_by(Problem.difficulty, Problem.external_id).limit(1)
        row = (await db.execute(query)).first()
        if row:
            p = row.Problem
            return ProblemSearchOut(
                id=p.id,
                external_id=p.external_id,
                title=p.title,
                slug=p.slug,
                difficulty=p.difficulty,
                url=p.url,
                paid_only=p.paid_only,
                node_id=row.node_id,
                node_title=row.node_title,
                confidence_band=_get_confidence_band(row.confidence),
                already_logged=False,
                reason=reason
            )
        return None

    for m in weakest_nodes:
        if len(suggestions) >= limit: break
        
        node = (await db.execute(select(RoadmapNode).where(RoadmapNode.id == m.node_id))).scalar_one_or_none()
        if not node: continue
        
        reason = f"Because {node.title} is your weakest mapped concept"
        suggestion = await get_problem_for_node(m.node_id, reason)
        if suggestion:
            suggestions.append(suggestion)
            
    # if we don't have enough suggestions, fill with canonical dsa problems
    if len(suggestions) < limit:
        from app.models.models import Roadmap
        dsa_roadmap_id = (await db.execute(select(Roadmap.id).where(Roadmap.slug == "dsa"))).scalar_one_or_none()
        if dsa_roadmap_id:
            query = select(
                Problem,
                ProblemConcept.node_id,
                ProblemConcept.confidence,
                RoadmapNode.title.label("node_title")
            ).join(
                ProblemConcept, (ProblemConcept.problem_id == Problem.id) & (ProblemConcept.role == 'primary')
            ).join(
                RoadmapNode, ProblemConcept.node_id == RoadmapNode.id
            ).where(
                RoadmapNode.roadmap_id == dsa_roadmap_id
            )
            if logged_problem_ids:
                query = query.where(Problem.id.not_in(logged_problem_ids))
                
            query = query.order_by(Problem.difficulty, Problem.external_id).limit(limit - len(suggestions))
            rows = (await db.execute(query)).all()
            for row in rows:
                p = row.Problem
                suggestions.append(ProblemSearchOut(
                    id=p.id,
                    external_id=p.external_id,
                    title=p.title,
                    slug=p.slug,
                    difficulty=p.difficulty,
                    url=p.url,
                    paid_only=p.paid_only,
                    node_id=row.node_id,
                    node_title=row.node_title,
                    confidence_band=_get_confidence_band(row.confidence),
                    already_logged=False,
                    reason="Recommended starting point"
                ))

    return suggestions


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
