import asyncio
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, func

from app.api import deps
from app.core.security import SupabaseUser
from app.models.models import LearningEvent, Roadmap, RoadmapNode
from app.schemas.companion import CompanionBatchIn
from app.services.evidence import record_event
from app.services.topic_mapping import candidate_nodes_for_user, top_k_suggested_nodes
from app.services.llm_classifier import classify_session, COMPANION_CLASSIFIER_MODEL, COMPANION_PROMPT_VERSION

router = APIRouter()

COMPANION_MAX_SESSIONS_PER_DAY = 50

@router.post("/sessions")
async def sync_sessions(
    body: CompanionBatchIn,
    db: AsyncSession = Depends(deps.get_db),
    current_user: SupabaseUser = Depends(deps.get_current_user),
):
    """
    Sync study sessions tracked by the browser extension.
    These events are ambient (TIME_BLOCK) and enter the evidence spine with 0 weight,
    acting as a T3_observed log without inflating mastery scores.
    """
    from app.models.models import UserPref
    import uuid
    pref_stmt = select(UserPref).where(UserPref.user_id == uuid.UUID(current_user.id))
    user_pref = (await db.execute(pref_stmt)).scalar_one_or_none()
    if user_pref and user_pref.audience == "school":
        raise HTTPException(
            status_code=403, 
            detail="Browser extension tracking is restricted for school audience accounts."
        )

    # Rate limiting: check how many sessions from companion_browser were recorded today
    today = datetime.now(timezone.utc).date()
    start_of_day = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)
    
    user_uuid = uuid.UUID(current_user.id)
    
    stmt = select(func.count(LearningEvent.id)).where(
        LearningEvent.user_id == user_uuid,
        LearningEvent.source == "companion_browser",
        LearningEvent.occurred_at >= start_of_day,
    )
    daily_count = (await db.execute(stmt)).scalar() or 0
    if daily_count + len(body.sessions) > COMPANION_MAX_SESSIONS_PER_DAY:
        raise HTTPException(
            status_code=429,
            detail=f"Daily limit of {COMPANION_MAX_SESSIONS_PER_DAY} tracked sessions reached."
        )

    synced = 0
    ignored = 0

    # Fetched once per request (not per session) — same candidate set applies
    # to every unmapped session in this batch, and the query touches every
    # roadmap node meta the user has, so doing it per-session was an N+1.
    candidates = None
    if any(session.node_id is None for session in body.sessions):
        candidates = await candidate_nodes_for_user(db, user_uuid)

    for session in body.sessions:
        if session.node_id:
            # Validate ownership of the node
            node_stmt = select(RoadmapNode.id, Roadmap.user_id).join(Roadmap).where(RoadmapNode.id == session.node_id)
            node_res = (await db.execute(node_stmt)).first()
            if not node_res:
                ignored += 1
                continue
            
            _, roadmap_user_id = node_res
            if roadmap_user_id is not None and roadmap_user_id != user_uuid:
                # User doesn't own this personal roadmap node
                ignored += 1
                continue
        
        # Record event
        payload = session.payload.model_dump(exclude_unset=True)
        
        # Classification Ladder
        if not session.node_id:
            title_sample = payload.get("title_sample", "")
            sources = session.payload.sources or []
            
            # Rung 1: Metadata rules (exact match skipped for now, rely on LLM for exact match if needed)

            # Rung 2: Embeddings. Calls out to Gemini synchronously (bounded
            # internally by embeddings._EMBED_TIMEOUT_SEC) — off the event
            # loop so a slow Gemini response doesn't stall other requests.
            shortlist = await asyncio.to_thread(top_k_suggested_nodes, title_sample, candidates, k=5)
            
            if shortlist:
                shortlist_dicts = [
                    {"node_id": s["node_id"], "title": s["title"], "description": s.get("description", "")}
                    for s in shortlist
                ]
                
                # Rung 3: LLM Classification
                # Using a dummy memory for now since we don't have recent topics yet
                classification = await classify_session(title_sample, sources, shortlist_dicts, memory=[])
                
                payload["classifier"] = COMPANION_CLASSIFIER_MODEL
                payload["prompt_version"] = COMPANION_PROMPT_VERSION
                payload["embedding_model"] = "gemini-embedding" # from config
                
                payload["confidence_band"] = classification.confidence_band
                payload["study_type"] = classification.study_type
                payload["assistance_level"] = classification.assistance_level
                payload["reason"] = classification.reason
                payload["candidates"] = [c.model_dump() for c in classification.candidates]
                
                if classification.confidence_band == "high" and classification.selected:
                    session.node_id = uuid.UUID(classification.selected)
                elif classification.confidence_band == "low":
                    # Drop silently
                    ignored += 1
                    continue
            else:
                # No candidates -> triage
                payload["confidence_band"] = "medium"
                payload["reason"] = "No candidate nodes found"

        # DB column is naive-UTC (CLAUDE.md convention); the extension sends
        # tz-aware ISO timestamps, so normalize before it reaches record_event.
        occurred_at = session.occurred_at
        if occurred_at.tzinfo is not None:
            occurred_at = occurred_at.astimezone(timezone.utc).replace(tzinfo=None)

        event = await record_event(
            db,
            user_uuid,
            event_type="TIME_BLOCK",
            trust_tier="T3_observed",
            source="companion_browser",
            node_id=session.node_id,
            duration_min=session.duration_min,
            entity_id=session.session_id,
            occurred_at=occurred_at,
            payload=payload,
        )
        if event is None:
            # Deduped
            ignored += 1
        else:
            synced += 1

    await db.commit()
    
    return {"status": "ok", "synced": synced, "ignored": ignored}
