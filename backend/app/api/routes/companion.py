import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, func

from app.api import deps
from app.core.security import SupabaseUser
from app.models.models import LearningEvent, MetricEvent, Roadmap, RoadmapNode, UserPref
from app.schemas.companion import CompanionBatchIn, CompanionSessionIn, ChapterWatch
from app.services.evidence import record_event
from app.services.metrics import get_latest_consent_tier, record_metric_event
from app.services.topic_mapping import candidate_nodes_for_user, top_k_suggested_nodes
from app.services.llm_classifier import classify_session, COMPANION_CLASSIFIER_MODEL, COMPANION_PROMPT_VERSION
from app.services.topic_segmentation import segment_session_topics, SessionTopic

router = APIRouter()

COMPANION_MAX_SESSIONS_PER_DAY = 50

# Cost/latency guard (IMPLEMENTATION-companion-chat-content.md §4): segmenting
# every content-bearing session in a batch would mean up to
# SEND_CHUNK_SIZE(20) x (1 segmentation + up to 5 classify) sequential Gemini
# calls inside one request — this bounds it to a handful.
MAX_CONTENT_SESSIONS_PER_BATCH = 3
# Short sessions are rarely multi-topic; not worth a segmentation call.
MIN_SEGMENTATION_DURATION_MIN = 5
_LLM_ORIGIN_SUFFIXES = ("chatgpt.com", "claude.ai", "gemini.google.com")

# YouTube chapter fan-out needs no Gemini segmentation call (the video's own
# chapter markers ARE the topic boundaries), but each chapter still runs the
# classify_session ladder — so the same per-request cost bound as chat
# content applies, via its own counter/cap so the two don't compete for the
# same budget. A long tutorial can have 100+ chapters (freeCodeCamp checked
# 2026-07-27: 135-142); a session spanning more than MAX_CHAPTERS_PER_SESSION
# falls back to the single-event whole-video path rather than firing that
# many classify calls from one sync.
MAX_CHAPTER_SESSIONS_PER_BATCH = 3
MAX_CHAPTERS_PER_SESSION = 15


def _has_llm_source(sources: list[str]) -> bool:
    return any(src.endswith(_LLM_ORIGIN_SUFFIXES) for src in sources)


def _fanout_entity_id(kind: str, session_id: uuid.UUID, index: int) -> uuid.UUID:
    """Deterministic per-(session, leg) id — same inputs always produce the
    same UUID, so a retried sync of the same batch hits uq_learning_event_dedupe
    instead of double-inserting. `kind` ("topic" vs "chapter") keeps the two
    fan-out sources namespaced apart even though a session only ever produces
    one or the other, never both."""
    return uuid.uuid5(uuid.NAMESPACE_URL, f"retainhq://companion-{kind}/{session_id}/{index}")


async def _classify_and_record(
    db: AsyncSession,
    user_uuid: uuid.UUID,
    *,
    node_id: Optional[uuid.UUID],
    title_sample: str,
    sources: list[str],
    duration_min: int,
    entity_id: uuid.UUID,
    occurred_at: datetime,
    base_payload: dict,
    candidates: Optional[list[dict]],
    consent_tier: Optional[str],
) -> bool:
    """Runs the classification ladder (when node_id isn't already known) and
    records one LearningEvent. Shared by the single-event path and each leg
    of a multi-topic fan-out — same rungs, same record_event call, just a
    different title_sample/duration/entity_id per caller. Returns True if a
    row was actually written (False = dropped as low-confidence, or deduped)."""
    payload = dict(base_payload)
    resolved_node_id = node_id

    if resolved_node_id is None:
        shortlist = await asyncio.to_thread(top_k_suggested_nodes, title_sample, candidates, k=5)

        if shortlist:
            shortlist_dicts = [
                {"node_id": s["node_id"], "title": s["title"], "description": s.get("description", "")}
                for s in shortlist
            ]
            classification = await classify_session(
                title_sample, sources, shortlist_dicts, memory=[], consent_tier=consent_tier,
            )

            payload["classifier"] = COMPANION_CLASSIFIER_MODEL
            payload["prompt_version"] = COMPANION_PROMPT_VERSION
            payload["embedding_model"] = "gemini-embedding"
            payload["confidence_band"] = classification.confidence_band
            payload["study_type"] = classification.study_type
            payload["assistance_level"] = classification.assistance_level
            payload["reason"] = classification.reason
            payload["candidates"] = [c.model_dump() for c in classification.candidates]

            if classification.confidence_band == "high" and classification.selected:
                resolved_node_id = uuid.UUID(classification.selected)
            elif classification.confidence_band == "low":
                return False
        else:
            payload["confidence_band"] = "medium"
            payload["reason"] = "No candidate nodes found"

    event = await record_event(
        db,
        user_uuid,
        event_type="TIME_BLOCK",
        trust_tier="T3_observed",
        source="companion_browser",
        node_id=resolved_node_id,
        duration_min=duration_min,
        entity_id=entity_id,
        occurred_at=occurred_at,
        payload=payload,
    )
    return event is not None


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

    A session may be split into several LearningEvents — one per topic —
    instead of one, from two independent sources: `content` (chat text, cloud
    tier only, LLM-segmented) or `chapters` (YouTube's own chapter markers,
    any tier, no LLM segmentation needed — the video already provides the
    topic boundaries). Either way this never changes trust_tier/event_type:
    every row is still T3_observed/TIME_BLOCK, weight 0 regardless of how many
    legs it split into (evidence_weights.TIME_BLOCK_WEIGHT is unconditionally
    0.0) — watching or reading is not evidence of learning, only of exposure;
    finer attribution must never mean higher mastery.
    """
    user_uuid = uuid.UUID(current_user.id)

    pref_stmt = select(UserPref).where(UserPref.user_id == user_uuid)
    user_pref = (await db.execute(pref_stmt)).scalar_one_or_none()
    if user_pref and user_pref.audience == "school":
        raise HTTPException(
            status_code=403,
            detail="Browser extension tracking is restricted for school audience accounts."
        )

    # Rate limiting: counts sessions SUBMITTED, via a dedicated metric event —
    # not LearningEvent rows. Content-bearing sessions can fan out into
    # several rows each, so counting rows would silently divide the real cap
    # by however many topics a session happened to split into.
    today = datetime.now(timezone.utc).date()
    start_of_day = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)

    stmt = select(func.count(MetricEvent.id)).where(
        MetricEvent.user_id == user_uuid,
        MetricEvent.event_type == "companion_session_tracked",
        MetricEvent.created_at >= start_of_day,
    )
    daily_count = (await db.execute(stmt)).scalar() or 0
    if daily_count + len(body.sessions) > COMPANION_MAX_SESSIONS_PER_DAY:
        raise HTTPException(
            status_code=429,
            detail=f"Daily limit of {COMPANION_MAX_SESSIONS_PER_DAY} tracked sessions reached."
        )

    synced = 0
    ignored = 0
    content_sessions_processed = 0
    chapter_sessions_processed = 0

    # Fetched once per request (not per session) — same candidate set applies
    # to every unmapped session in this batch, and the query touches every
    # roadmap node meta the user has, so doing it per-session was an N+1.
    candidates = None
    consent_tier = None
    if any(session.node_id is None for session in body.sessions):
        candidates = await candidate_nodes_for_user(db, user_uuid)
        consent_tier = await get_latest_consent_tier(db, user_uuid)

    for session in body.sessions:
        if session.node_id:
            node_stmt = select(RoadmapNode.id, Roadmap.user_id).join(Roadmap).where(RoadmapNode.id == session.node_id)
            node_res = (await db.execute(node_stmt)).first()
            if not node_res:
                ignored += 1
                continue

            _, roadmap_user_id = node_res
            if roadmap_user_id is not None and roadmap_user_id != user_uuid:
                ignored += 1
                continue

        payload = session.payload.model_dump(exclude_unset=True)

        # AI-attribution fields are only ever legitimately set by the
        # classification step — a client must never forge
        # confidence_band/classifier/reason etc. and have them stored as if
        # the server had verified them.
        for _ai_field in ("classifier", "prompt_version", "embedding_model", "confidence_band", "candidates", "reason", "study_type", "assistance_level"):
            payload.pop(_ai_field, None)
        payload["session_id"] = str(session.session_id)

        occurred_at = session.occurred_at
        if occurred_at.tzinfo is not None:
            occurred_at = occurred_at.astimezone(timezone.utc).replace(tzinfo=None)

        title_sample = payload.get("title_sample", "")
        sources = session.payload.sources or []

        # Two independent, mutually exclusive fan-out sources feed the same
        # `legs` shape below: chat-derived topics (LLM-segmented, share of
        # total duration) and YouTube chapters (video-provided boundaries,
        # actual watched seconds). Both need node_id is None — an explicit
        # node_id means attribution for the whole session was already
        # decided, which either fan-out would only contradict.
        topics: list[SessionTopic] = []
        if (
            session.node_id is None
            and session.content
            and consent_tier == "cloud"
            and session.duration_min >= MIN_SEGMENTATION_DURATION_MIN
            and content_sessions_processed < MAX_CONTENT_SESSIONS_PER_BATCH
            and _has_llm_source(sources)
        ):
            content_sessions_processed += 1
            topics = await segment_session_topics(session.content, sources)
            await record_metric_event(
                db, user_uuid, "companion_topic_segmentation",
                entity_id=session.session_id,
                payload={
                    "duration_min": session.duration_min,
                    "topic_count": len(topics),
                    "split": len(topics) > 1,
                },
            )

        chapters: list[ChapterWatch] = []
        if (
            session.node_id is None
            and not topics  # chat topics, if present, already claimed this session
            and session.chapters
            and 1 < len(session.chapters) <= MAX_CHAPTERS_PER_SESSION
            and sources == ["youtube.com"]  # never fan out a mixed-tab session
            and chapter_sessions_processed < MAX_CHAPTER_SESSIONS_PER_BATCH
        ):
            chapter_sessions_processed += 1
            chapters = [c for c in session.chapters if c.seconds > 0]

        legs: list[dict] = []
        if topics:
            for idx, topic in enumerate(topics):
                topic_duration = round(session.duration_min * topic.share)
                if topic_duration <= 0:
                    continue
                legs.append({
                    "kind": "topic",
                    "index": idx,
                    "label": topic.label,
                    "duration_min": topic_duration,
                    "extra_payload": {
                        "study_type": topic.study_type,
                        "assistance_level": topic.assistance_level,
                        "topic_index": idx,
                        "topic_count": len(topics),
                    },
                })
        elif chapters:
            for idx, chapter in enumerate(chapters):
                chapter_duration = round(chapter.seconds / 60)
                if chapter_duration <= 0:
                    continue
                legs.append({
                    "kind": "chapter",
                    "index": idx,
                    "label": chapter.title,
                    "duration_min": chapter_duration,
                    "extra_payload": {
                        "chapter_index": idx,
                        "chapter_count": len(chapters),
                    },
                })

        session_synced_any = False

        if legs:
            for leg in legs:
                wrote = await _classify_and_record(
                    db, user_uuid,
                    node_id=None,
                    title_sample=leg["label"],
                    sources=sources,
                    duration_min=leg["duration_min"],
                    entity_id=_fanout_entity_id(leg["kind"], session.session_id, leg["index"]),
                    occurred_at=occurred_at,
                    base_payload={
                        **payload,
                        "title_sample": leg["label"],
                        **leg["extra_payload"],
                    },
                    candidates=candidates,
                    consent_tier=consent_tier,
                )
                if wrote:
                    synced += 1
                    session_synced_any = True
                else:
                    ignored += 1
        else:
            wrote = await _classify_and_record(
                db, user_uuid,
                node_id=session.node_id,
                title_sample=title_sample,
                sources=sources,
                duration_min=session.duration_min,
                entity_id=session.session_id,
                occurred_at=occurred_at,
                base_payload=payload,
                candidates=candidates,
                consent_tier=consent_tier,
            )
            if wrote:
                synced += 1
                session_synced_any = True
            else:
                ignored += 1

        if session_synced_any:
            # One row per submitted session regardless of fan-out — what the
            # daily-cap query above counts. Not itself dedupe-guarded against
            # a client retrying an already-synced batch (record_event's own
            # dedupe already prevents duplicate LearningEvent rows either
            # way; this only means a retry can over-count the pre-check by a
            # small margin, same class of imprecision the old row-counting
            # version had).
            await record_metric_event(
                db, user_uuid, "companion_session_tracked", entity_id=session.session_id,
            )

    await db.commit()

    return {"status": "ok", "synced": synced, "ignored": ignored}
