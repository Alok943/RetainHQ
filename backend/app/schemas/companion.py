from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class CompanionSessionPayload(BaseModel):
    """
    Metadata about the session classification.
    extra='forbid' is a critical security invariant (SPEC-companion-phase1 §6):
    It prevents any raw chat content or unbounded text fields from being accidentally
    persisted to the database.
    """
    model_config = ConfigDict(extra="forbid")

    sources: List[str] = Field(description="List of domains or app surfaces e.g. ['leetcode.com', 'claude.ai']")
    study_type: Optional[str] = None
    assistance_level: Optional[str] = None
    confidence_band: Optional[str] = None
    candidates: Optional[List[dict]] = None
    reason: Optional[str] = None
    title_sample: Optional[str] = Field(None, max_length=500, description="Capped sample of window titles")
    classifier: Optional[str] = None
    prompt_version: Optional[str] = None
    embedding_model: Optional[str] = None


class ChapterWatch(BaseModel):
    """One YouTube chapter and how many seconds of it were actively watched,
    from the video's OWN uploader-added chapter markers — public metadata
    YouTube shows every viewer, not user-authored or AI-derived text. Unlike
    `content` below this needs no consent-tier gating and carries no privacy
    weight; it's capped defensively (an uploader-controlled string) rather
    than for any exposure reason."""
    title: str = Field(max_length=300)
    seconds: int = Field(ge=0)


class CompanionSessionIn(BaseModel):
    """
    One completed study session from the browser extension.
    """
    session_id: UUID = Field(description="Idempotency key for deduplication")
    node_id: Optional[UUID] = Field(None, description="Matched roadmap node; None means it goes to triage")
    duration_min: int = Field(..., ge=0)
    occurred_at: datetime = Field(description="When the session ended (stitcher's `end`), not when it synced — sessions sync in batches after offline gaps")
    payload: CompanionSessionPayload
    # Transport only — a SIBLING of `payload`, never nested inside it.
    # `payload` keeps `extra="forbid"` and no content field precisely so raw
    # chat text can never land there even by accident; `content` lives here
    # instead, is consumed by topic_segmentation.py, and must never be copied
    # into anything that gets persisted (IMPLEMENTATION-companion-chat-content
    # §3.1). `exclude=True` means a bare `.model_dump()` of this model drops
    # it by default — defense in depth against a future refactor that stores
    # the whole object.
    content: Optional[str] = Field(
        None, max_length=16_000, exclude=True,
        description="Flattened chat turns, cloud-tier only. Transport-only — never persisted.",
    )
    # Same transport-only shape as `content`, for the same reason: consumed to
    # build per-chapter LearningEvents, then discarded — each resulting event
    # already stores its own chapter title as `title_sample`, so keeping the
    # raw list around too would just be redundant storage.
    chapters: Optional[list[ChapterWatch]] = Field(
        None, max_length=200, exclude=True,
        description="Per-chapter watched seconds, from YouTube's chapter markers. Transport-only.",
    )


class CompanionBatchIn(BaseModel):
    """
    Batch of sessions to sync.
    """
    sessions: List[CompanionSessionIn]
